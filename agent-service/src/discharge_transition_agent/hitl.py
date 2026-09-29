"""Durable human-in-the-loop task store — the local mirror of the Durable Task Scheduler
human-approval gate.

The Microsoft Agent Framework Durable Extension (hosted on the Durable Task Scheduler) lets an
agent orchestration draft a result and then *pause on an external event* — a human decision —
while compute scales to zero, resuming only when the decision arrives or a timer fires. This module
reproduces those semantics locally so the workshop is runnable offline:

  * a run registers a durable review task (persisted to JSON, so it survives a process restart);
  * the task waits in ``PendingReview`` for an external decision event (approve / rework / reject);
  * an unattended task past its due time escalates on ``sweep`` — the timer -> escalate branch;
  * a policy escalation (e.g. missing specialty protocol) creates the task already ``Escalated``;
  * every transition appends an immutable audit record (actor, from, to, note, timestamp).

The state machine and audit rules match ``hitl/state-machine.md`` and ``hitl/task-schema.json``.
Graduate to the real Durable Task Scheduler by swapping this store for the durable orchestration in
``orchestrations/`` — the states, actions, and audit contract are identical.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Canonical review states (match the UI ReviewStatus enum plus Escalated).
PENDING = "PendingReview"
IN_REVIEW = "InReview"
APPROVED = "Approved"
NEEDS_REWORK = "NeedsRework"
REJECTED = "Rejected"
ESCALATED = "Escalated"

TERMINAL_STATES = {APPROVED, REJECTED, ESCALATED}

# Legal transitions keyed by action. Each maps allowed source states -> destination state.
_TRANSITIONS: dict[str, dict[str, str]] = {
    "claim": {PENDING: IN_REVIEW},
    "approve": {PENDING: APPROVED, IN_REVIEW: APPROVED},
    "request_changes": {PENDING: NEEDS_REWORK, IN_REVIEW: NEEDS_REWORK},
    "reject": {PENDING: REJECTED, IN_REVIEW: REJECTED},
    "escalate": {PENDING: ESCALATED, IN_REVIEW: ESCALATED, NEEDS_REWORK: ESCALATED},
    "rework": {NEEDS_REWORK: PENDING},
}

# Actions that only a human reviewer may take (state-machine rule 1).
_HUMAN_ONLY = {"approve", "reject"}
_AGENT_ACTORS = {"agent", "orchestrator", "system", ""}

_DEFAULT_SLA_SECONDS = int(os.getenv("HITL_SLA_SECONDS", "86400"))


class HitlError(Exception):
    """Raised for illegal transitions or unknown tasks. ``status`` carries an HTTP hint."""

    def __init__(self, message: str, status: int = 409):
        super().__init__(message)
        self.status = status


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_review_task(result: dict, case: Optional[dict], sla_seconds: int, now: Optional[datetime] = None) -> dict:
    """Construct a durable review-task dict from an invoke result.

    Single source of truth for the task shape, shared by the local ``TaskStore`` and the
    Durable Task Scheduler adapter (``hitl_dts.DtsTaskStore``). Escalating policy decisions
    yield a task already ``Escalated`` — a run a human cannot clear on the spot goes straight
    to a specialist, never through silent approval.
    """
    case = case or {}
    now = now or _now()
    task_id = result["correlationId"]
    escalate = result.get("policyDecision") == "escalate"
    status = ESCALATED if escalate else PENDING
    task = {
        "taskId": task_id,
        "correlationId": task_id,
        "caseId": result.get("caseId"),
        "patientLabel": case.get("patientLabel"),
        "facility": case.get("facility"),
        "diagnosis": case.get("diagnosis"),
        "riskTier": (result.get("approvedRiskScore") or {}).get("tier"),
        "status": status,
        "assignedRole": None,
        "policyDecision": result.get("policyDecision"),
        "transitionGaps": result.get("transitionGaps", []),
        "missingInformation": result.get("missingInformation", []),
        "draftPlan": result.get("draftExceptionPacket", []),
        "evidence": result.get("evidence", []),
        "createdAt": _iso(now),
        "updatedAt": _iso(now),
        "dueAt": _iso(now + timedelta(seconds=sla_seconds)),
        "history": [],
    }
    note = (
        "Policy escalation on run — routed to specialist reviewer."
        if escalate
        else "Draft exception packet created; awaiting care-manager review."
    )
    task["history"].append(
        {
            "timestamp": _iso(now),
            "from": None,
            "to": status,
            "action": "escalate" if escalate else "create",
            "actor": "orchestrator",
            "note": note,
        }
    )
    return task


class TaskStore:
    """Thread-safe, file-backed durable review-task store."""

    def __init__(self, path: Optional[Path] = None, sla_seconds: int = _DEFAULT_SLA_SECONDS):
        env_path = os.getenv("HITL_STORE_PATH")
        self.path = Path(path or env_path or (Path(__file__).resolve().parents[2] / ".hitl-store.json"))
        self.sla_seconds = sla_seconds
        self._lock = threading.RLock()
        self._tasks: dict[str, dict] = {}
        self._load()

    # ---- persistence -----------------------------------------------------
    def _load(self) -> None:
        if self.path.exists():
            try:
                self._tasks = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._tasks = {}

    def _persist(self) -> None:
        try:
            self.path.write_text(json.dumps(self._tasks, indent=2), encoding="utf-8")
        except OSError:
            pass  # best-effort durability; the in-memory store stays authoritative

    # ---- registration ----------------------------------------------------
    def register_from_result(self, result: dict, case: Optional[dict] = None) -> dict:
        """Create (or refresh) a durable review task from an invoke result.

        Escalating policy decisions create the task already ``Escalated`` — a run that a human
        cannot clear on the spot goes straight to a specialist, never through silent approval.
        """
        task = build_review_task(result, case, self.sla_seconds)
        task_id = task["taskId"]
        with self._lock:
            self._tasks[task_id] = task
            self._persist()
        return task

    # ---- queries ---------------------------------------------------------
    def list_tasks(self) -> list[dict]:
        with self._lock:
            self._sweep_locked()
            return sorted(self._tasks.values(), key=lambda t: t["createdAt"], reverse=True)

    def get_task(self, task_id: str) -> dict:
        with self._lock:
            self._sweep_locked()
            task = self._tasks.get(task_id)
            if task is None:
                raise HitlError(f"No review task for correlation id '{task_id}'.", status=404)
            return task

    def get_audit(self, task_id: str) -> list[dict]:
        return self.get_task(task_id)["history"]

    # ---- transitions -----------------------------------------------------
    def apply_action(self, task_id: str, action: str, actor: str = "", note: str = "") -> dict:
        action = (action or "").strip().lower()
        if action not in _TRANSITIONS:
            raise HitlError(
                f"Unknown action '{action}'. Valid: {', '.join(sorted(_TRANSITIONS))}.", status=400
            )
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise HitlError(f"No review task for correlation id '{task_id}'.", status=404)

            current = task["status"]
            if current in TERMINAL_STATES:
                raise HitlError(
                    f"Task is already {current}; no further transitions are allowed.", status=409
                )
            allowed = _TRANSITIONS[action]
            if current not in allowed:
                raise HitlError(
                    f"Action '{action}' is not valid from state '{current}'.", status=409
                )
            if action in _HUMAN_ONLY and (actor or "").strip().lower() in _AGENT_ACTORS:
                raise HitlError(
                    f"Action '{action}' requires a human reviewer; supply an 'actor'.", status=403
                )

            destination = allowed[current]
            self._transition_locked(task, action, current, destination, actor, note)
            return task

    def sweep(self) -> list[dict]:
        """Escalate any non-terminal task past its due time. The timer -> escalate branch."""
        with self._lock:
            return self._sweep_locked()

    # ---- internals -------------------------------------------------------
    def _transition_locked(
        self, task: dict, action: str, src: str, dst: str, actor: str, note: str
    ) -> None:
        now = _now()
        task["status"] = dst
        task["updatedAt"] = _iso(now)
        if action == "claim":
            task["assignedRole"] = actor or task.get("assignedRole")
        task["history"].append(
            {
                "timestamp": _iso(now),
                "from": src,
                "to": dst,
                "action": action,
                "actor": actor or "orchestrator",
                "note": note or "",
            }
        )
        self._persist()

    def _sweep_locked(self) -> list[dict]:
        now = _now()
        escalated: list[dict] = []
        for task in self._tasks.values():
            if task["status"] in TERMINAL_STATES:
                continue
            due = task.get("dueAt")
            if due and _parse(due) <= now:
                self._transition_locked(
                    task,
                    "escalate",
                    task["status"],
                    ESCALATED,
                    "system",
                    "Review SLA elapsed with no decision; auto-escalated to a human reviewer.",
                )
                escalated.append(task)
        return escalated


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
