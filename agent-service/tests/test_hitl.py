"""Contract tests for the durable HITL task store (Data Task Scheduler local mirror).

Run: .\\.venv\\Scripts\\python.exe tests\\test_hitl.py
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
    REJECTED,
    HitlError,
    TaskStore,
)


def _result(correlation_id: str, policy: str = "review_required") -> dict:
    return {
        "correlationId": correlation_id,
        "caseId": "P0147",
        "policyDecision": policy,
        "approvedRiskScore": {"tier": "High", "score": 0.82, "provenance": "risk_score.get"},
        "transitionGaps": ["No 48h follow-up scheduled"],
        "missingInformation": [],
        "draftExceptionPacket": ["Schedule cardiology follow-up within 48h."],
        "evidence": [{"source": "protocol.search", "citation": "rag-docs/x.md", "claim": "c", "confidence": "High"}],
    }


def _store() -> TaskStore:
    tmp = Path(tempfile.mkdtemp()) / "hitl.json"
    return TaskStore(path=tmp, sla_seconds=86400)


def test_register_creates_pending_task_with_audit():
    store = _store()
    task = store.register_from_result(_result("trace-1"), case={"patientLabel": "Patient A", "diagnosis": "CHF"})
    assert task["status"] == PENDING
    assert task["patientLabel"] == "Patient A"
    assert task["dueAt"] > task["createdAt"]
    assert task["history"][0]["action"] == "create"
    assert task["history"][0]["to"] == PENDING


def test_policy_escalation_creates_escalated_task():
    store = _store()
    task = store.register_from_result(_result("trace-2", policy="escalate"))
    assert task["status"] == ESCALATED
    assert task["history"][0]["action"] == "escalate"


def test_human_approval_transition():
    store = _store()
    store.register_from_result(_result("trace-3"))
    task = store.apply_action("trace-3", "approve", actor="care-manager", note="Looks complete")
    assert task["status"] == APPROVED
    assert task["history"][-1]["actor"] == "care-manager"


def test_approve_requires_human_actor():
    store = _store()
    store.register_from_result(_result("trace-4"))
    try:
        store.apply_action("trace-4", "approve", actor="agent")
        raise AssertionError("agent should not be able to approve")
    except HitlError as exc:
        assert exc.status == 403


def test_no_transition_from_terminal_state():
    store = _store()
    store.register_from_result(_result("trace-5"))
    store.apply_action("trace-5", "reject", actor="care-manager")
    try:
        store.apply_action("trace-5", "approve", actor="care-manager")
        raise AssertionError("must not transition out of a terminal state")
    except HitlError as exc:
        assert exc.status == 409
    assert store.get_task("trace-5")["status"] == REJECTED


def test_rework_loops_back_to_pending():
    store = _store()
    store.register_from_result(_result("trace-6"))
    assert store.apply_action("trace-6", "request_changes", actor="care-manager")["status"] == NEEDS_REWORK
    assert store.apply_action("trace-6", "rework", actor="orchestrator")["status"] == PENDING


def test_sweep_escalates_overdue_tasks():
    tmp = Path(tempfile.mkdtemp()) / "hitl.json"
    store = TaskStore(path=tmp, sla_seconds=-1)  # already overdue on creation
    store.register_from_result(_result("trace-7"))
    escalated = store.sweep()
    assert [t["taskId"] for t in escalated] == ["trace-7"]
    assert store.get_task("trace-7")["status"] == ESCALATED
    assert store.get_task("trace-7")["history"][-1]["actor"] == "system"


def test_store_persists_across_reload():
    tmp = Path(tempfile.mkdtemp()) / "hitl.json"
    store = TaskStore(path=tmp, sla_seconds=86400)
    store.register_from_result(_result("trace-8"))
    store.apply_action("trace-8", "approve", actor="care-manager")
    reloaded = TaskStore(path=tmp, sla_seconds=86400)
    assert reloaded.get_task("trace-8")["status"] == APPROVED


if __name__ == "__main__":
    for fn in [
        test_register_creates_pending_task_with_audit,
        test_policy_escalation_creates_escalated_task,
        test_human_approval_transition,
        test_approve_requires_human_actor,
        test_no_transition_from_terminal_state,
        test_rework_loops_back_to_pending,
        test_sweep_escalates_overdue_tasks,
        test_store_persists_across_reload,
    ]:
        fn()
        print(f"ok  {fn.__name__}")
    print("all hitl tests passed")
