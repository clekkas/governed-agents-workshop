"""Contract tests for the DTS-backed HITL store (hitl_dts.DtsTaskStore).

Uses a fake DtsGate so the adapter logic is exercised without a live Durable Task Scheduler or
the durabletask SDK: schedule/raise_decision are recorded, and get_status is driven by a small
in-memory state the fake flips on decisions.

Run: .\\.venv-dts\\Scripts\\python.exe -m pytest tests/test_hitl_dts.py -q
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discharge_transition_agent.hitl import (  # noqa: E402
    APPROVED,
    ESCALATED,
    NEEDS_REWORK,
    PENDING,
    HitlError,
)
from discharge_transition_agent.hitl_dts import DtsTaskStore  # noqa: E402


def _result(correlation_id: str, policy: str = "review_required") -> dict:
    return {
        "correlationId": correlation_id,
        "caseId": "P0147",
        "policyDecision": policy,
        "approvedRiskScore": {"tier": "High", "score": 0.82},
        "transitionGaps": ["No 48h follow-up scheduled"],
        "missingInformation": [],
        "draftExceptionPacket": ["Schedule cardiology follow-up within 48h."],
        "evidence": [{"source": "protocol.search", "citation": "x.md", "claim": "c", "confidence": "High"}],
    }


class FakeGate:
    """Minimal DtsGate stand-in that models the orchestration's status vocabulary."""

    _DECISION_TO_STATUS = {"approve": APPROVED, "request_changes": NEEDS_REWORK, "reject": "Rejected"}

    def __init__(self) -> None:
        self.scheduled: list[dict] = []
        self.decisions: list[tuple] = []
        self._status: dict[str, str] = {}
        self._history: dict[str, list] = {}

    def schedule(self, result: dict) -> str:
        cid = result["correlationId"]
        self.scheduled.append(result)
        status = ESCALATED if result.get("policyDecision") == "escalate" else PENDING
        self._status[cid] = status
        self._history[cid] = [{"from": None, "to": status, "action": "create", "actor": "orchestrator", "note": ""}]
        return cid

    def raise_decision(self, instance_id: str, action: str, actor: str = "", note: str = "") -> None:
        self.decisions.append((instance_id, action, actor, note))
        dst = self._DECISION_TO_STATUS[action]
        self._status[instance_id] = dst
        self._history[instance_id].append({"from": PENDING, "to": dst, "action": action, "actor": actor, "note": note})

    def get_status(self, instance_id: str):
        if instance_id not in self._status:
            return None
        return {"instanceId": instance_id, "status": self._status[instance_id], "history": self._history[instance_id]}


def _store() -> tuple[DtsTaskStore, FakeGate]:
    tmp = Path(tempfile.mkdtemp()) / "dts-index.json"
    store = DtsTaskStore(path=tmp, sla_seconds=86400)
    gate = FakeGate()
    store._gate = gate
    return store, gate


def test_register_schedules_and_returns_pending_task():
    store, gate = _store()
    task = store.register_from_result(_result("trace-1"), case={"patientLabel": "Patient A", "diagnosis": "CHF"})
    assert task["status"] == PENDING
    assert task["patientLabel"] == "Patient A"
    assert len(gate.scheduled) == 1
    assert gate.scheduled[0]["correlationId"] == "trace-1"
    assert gate.scheduled[0]["slaSeconds"] == 86400


def test_policy_escalation_schedules_escalated():
    store, gate = _store()
    task = store.register_from_result(_result("trace-2", policy="escalate"))
    assert task["status"] == ESCALATED
    assert store.get_task("trace-2")["status"] == ESCALATED


def test_get_task_overlays_live_status():
    store, gate = _store()
    store.register_from_result(_result("trace-3"))
    gate._status["trace-3"] = APPROVED  # simulate an out-of-band durable transition
    assert store.get_task("trace-3")["status"] == APPROVED


def test_human_approval_raises_decision_and_reflects_status():
    store, gate = _store()
    store.register_from_result(_result("trace-4"))
    task = store.apply_action("trace-4", "approve", actor="care-manager", note="ok")
    assert task["status"] == APPROVED
    assert gate.decisions == [("trace-4", "approve", "care-manager", "ok")]


def test_approve_requires_human_actor():
    store, _ = _store()
    store.register_from_result(_result("trace-5"))
    try:
        store.apply_action("trace-5", "approve", actor="agent")
        assert False, "expected HitlError"
    except HitlError as exc:
        assert exc.status == 403


def test_claim_is_local_only():
    store, gate = _store()
    store.register_from_result(_result("trace-6"))
    task = store.apply_action("trace-6", "claim", actor="nurse-joy")
    assert task["assignedRole"] == "nurse-joy"
    assert task["status"] == PENDING
    assert gate.decisions == []  # no durable event for a claim


def test_rework_and_manual_escalate_unsupported():
    store, _ = _store()
    store.register_from_result(_result("trace-7"))
    for action in ("rework", "escalate"):
        try:
            store.apply_action("trace-7", action, actor="care-manager")
            assert False, f"expected HitlError for {action}"
        except HitlError as exc:
            assert exc.status == 400


def test_terminal_state_blocks_further_actions():
    store, gate = _store()
    store.register_from_result(_result("trace-8"))
    store.apply_action("trace-8", "reject", actor="care-manager")
    try:
        store.apply_action("trace-8", "approve", actor="care-manager")
        assert False, "expected HitlError"
    except HitlError as exc:
        assert exc.status == 409


def test_unknown_task_is_404():
    store, _ = _store()
    try:
        store.get_task("nope")
        assert False, "expected HitlError"
    except HitlError as exc:
        assert exc.status == 404


def test_sweep_is_noop():
    store, _ = _store()
    store.register_from_result(_result("trace-9"))
    assert store.sweep() == []
