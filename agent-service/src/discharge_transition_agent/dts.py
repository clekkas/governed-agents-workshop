"""Durable Task Scheduler (DTS) approval gate — the durable graduation of the local HITL store.

This is the real Durable Task Scheduler implementation the workshop's local ``hitl.TaskStore``
graduates to, hosted on **Azure Container Apps** (not Azure Functions) via the portable
``durabletask`` + ``durabletask-azuremanaged`` SDK.

Design (faithful to orchestrations/function_app.py and hitl.py):

  * The multi-agent workflow (foundry/local mode) has ALREADY drafted the exception packet and
    computed the policy decision. This orchestration is purely the **human-in-the-loop approval
    gate** — it takes that result as input, records ``PendingReview``, then pauses on the
    ``ReviewDecision`` external event raced against a durable SLA timer.
  * While paused it consumes no compute and no model tokens — the timer is durable, so a review
    can safely take hours or days.
  * States mirror the local store exactly: PendingReview -> Approved | NeedsRework | Rejected;
    timer -> Escalated; a policy-escalate decision creates the run already Escalated.
  * The human-only guard (approve/reject require a real reviewer) is enforced in the orchestration.
  * Every transition appends an immutable audit record; the running history is published via the
    orchestration's custom status so the API can show it before completion.

Two roles share this module:
  * the **worker** (``run_worker``) hosts the orchestration + activities — a separate Container App;
  * the **client** (``DtsGate``) schedules runs and raises decisions — used by the FastAPI service.

Auth: endpoint + taskhub + DefaultAzureCredential (user-assigned MI on Container Apps). Against the
local emulator the endpoint is http://localhost:8080 with an insecure channel and no credential.
"""

from __future__ import annotations

import os
from datetime import timedelta
from typing import Any, Optional

# ---- shared state vocabulary (must match hitl.py) ----
PENDING = "PendingReview"
APPROVED = "Approved"
NEEDS_REWORK = "NeedsRework"
REJECTED = "Rejected"
ESCALATED = "Escalated"
TERMINAL_STATES = {APPROVED, REJECTED, ESCALATED}

_ACTION_TO_STATE = {"approve": APPROVED, "request_changes": NEEDS_REWORK, "reject": REJECTED}
_HUMAN_ONLY = {"approve", "reject"}
_AGENT_ACTORS = {"agent", "orchestrator", "system", ""}

ORCHESTRATION_NAME = "discharge_exception_approval"
REVIEW_EVENT = "ReviewDecision"


# ---------------------------------------------------------------------------
# Connection settings
# ---------------------------------------------------------------------------
def _endpoint() -> str:
    return os.environ.get("DTS_ENDPOINT", os.environ.get("ENDPOINT", "http://localhost:8080")).strip()


def _taskhub() -> str:
    return os.environ.get("DTS_TASKHUB", os.environ.get("TASKHUB", "default")).strip()


def _sla_seconds() -> int:
    return int(os.environ.get("HITL_SLA_SECONDS", "86400"))


def _credential():
    """DefaultAzureCredential for secure (cloud) endpoints; None for the insecure emulator."""
    if not _endpoint().startswith("https://"):
        return None
    from azure.identity import DefaultAzureCredential

    client_id = os.environ.get("AZURE_MANAGED_IDENTITY_CLIENT_ID", os.environ.get("AZURE_CLIENT_ID", "")).strip()
    return DefaultAzureCredential(managed_identity_client_id=client_id) if client_id else DefaultAzureCredential()


# ---------------------------------------------------------------------------
# Orchestration + activities (hosted by the worker)
# ---------------------------------------------------------------------------
def _audit(ctx, history: list, src: Optional[str], dst: str, action: str, actor: str, note: str) -> None:
    """Append an audit record (deterministic — uses the orchestration clock) and publish it."""
    history.append(
        {
            "timestamp": ctx.current_utc_datetime.isoformat().replace("+00:00", "Z"),
            "from": src,
            "to": dst,
            "action": action,
            "actor": actor or "orchestrator",
            "note": note or "",
        }
    )
    ctx.set_custom_status({"status": dst, "history": list(history)})


def discharge_exception_approval(ctx, case_result: dict):
    """The durable HITL approval gate. `case_result` is the invoke result + optional slaSeconds."""
    result = case_result or {}
    correlation_id = result.get("correlationId")
    policy_decision = result.get("policyDecision")
    sla_seconds = int(result.get("slaSeconds") or _sla_seconds())
    history: list[dict] = []

    # Policy escalation never waits for a routine reviewer — straight to a specialist.
    if policy_decision == "escalate":
        _audit(ctx, history, None, ESCALATED, "escalate", "orchestrator",
               "Policy escalation on run — routed to specialist reviewer.")
        return {"correlationId": correlation_id, "status": ESCALATED, "history": history}

    # Draft already exists (produced by the agent workflow). Record PendingReview and notify.
    _audit(ctx, history, None, PENDING, "create", "orchestrator",
           "Draft exception packet created; awaiting care-manager review.")
    yield ctx.call_activity(notify_care_manager, input={"correlationId": correlation_id, "caseId": result.get("caseId")})

    # Pause on the care-manager decision, raced against the durable SLA timer.
    decision_task = ctx.wait_for_external_event(REVIEW_EVENT)
    timeout_task = ctx.create_timer(ctx.current_utc_datetime + timedelta(seconds=sla_seconds))

    from durabletask import task as _dtask

    winner = yield _dtask.when_any([decision_task, timeout_task])

    if winner == timeout_task:
        _audit(ctx, history, PENDING, ESCALATED, "escalate", "system",
               "Review SLA elapsed with no decision; auto-escalated to a human reviewer.")
        return {"correlationId": correlation_id, "status": ESCALATED, "history": history}

    decision = decision_task.get_result() or {}
    action = str(decision.get("action") or "").strip().lower()
    actor = str(decision.get("actor") or "").strip()
    note = str(decision.get("note") or "")

    # Human-only guard: agents cannot approve or reject.
    if action in _HUMAN_ONLY and actor.lower() in _AGENT_ACTORS:
        _audit(ctx, history, PENDING, PENDING, "rejected_transition", "system",
               f"Action '{action}' requires a human reviewer; ignored.")
        return {"correlationId": correlation_id, "status": PENDING, "history": history,
                "error": "approve/reject require a human reviewer"}

    destination = _ACTION_TO_STATE.get(action)
    if destination is None:
        _audit(ctx, history, PENDING, PENDING, "rejected_transition", "system",
               f"Unknown review action '{action}'.")
        return {"correlationId": correlation_id, "status": PENDING, "history": history,
                "error": f"unknown review action '{action}'"}

    _audit(ctx, history, PENDING, destination, action, actor or "care-manager", note)
    if destination == APPROVED:
        yield ctx.call_activity(finalize_exception_packet, input={"correlationId": correlation_id})
    return {"correlationId": correlation_id, "status": destination, "history": history}


def notify_care_manager(ctx, payload: dict) -> str:
    """Side effect: notify the reviewer (Teams/queue/email). Stub for the workshop."""
    return "notified"


def finalize_exception_packet(ctx, payload: dict) -> str:
    """Side effect: task.create (draft only) downstream. Never approves on the patient's behalf."""
    return "finalized"


# ---------------------------------------------------------------------------
# Worker host (separate Container App)
# ---------------------------------------------------------------------------
def run_worker() -> None:
    from durabletask.azuremanaged.worker import DurableTaskSchedulerWorker

    endpoint, taskhub = _endpoint(), _taskhub()
    secure = endpoint.startswith("https://")
    print(f"[dts-worker] connecting endpoint={endpoint} taskhub={taskhub} secure={secure}", flush=True)
    with DurableTaskSchedulerWorker(
        host_address=endpoint,
        secure_channel=secure,
        taskhub=taskhub,
        token_credential=_credential(),
    ) as worker:
        worker.add_orchestrator(discharge_exception_approval)
        worker.add_activity(notify_care_manager)
        worker.add_activity(finalize_exception_packet)
        worker.start()
        print("[dts-worker] started; awaiting work items", flush=True)
        # Keep the process alive; the worker streams work items in background threads.
        import threading

        threading.Event().wait()


# ---------------------------------------------------------------------------
# Client gate (used by the FastAPI service when HITL_MODE=dts)
# ---------------------------------------------------------------------------
class DtsGate:
    """Thin client over the DTS scheduler for the approval gate."""

    def __init__(self) -> None:
        self.endpoint = _endpoint()
        self.taskhub = _taskhub()
        self._client = None

    def _connect(self):
        if self._client is None:
            from durabletask.azuremanaged.client import DurableTaskSchedulerClient

            self._client = DurableTaskSchedulerClient(
                host_address=self.endpoint,
                secure_channel=self.endpoint.startswith("https://"),
                taskhub=self.taskhub,
                token_credential=_credential(),
            )
        return self._client

    def schedule(self, result: dict) -> str:
        """Start the approval-gate orchestration; instance id == correlationId for direct mapping."""
        client = self._connect()
        instance_id = result.get("correlationId")
        client.schedule_new_orchestration(ORCHESTRATION_NAME, input=result, instance_id=instance_id)
        return instance_id

    def raise_decision(self, instance_id: str, action: str, actor: str = "", note: str = "") -> None:
        client = self._connect()
        client.raise_orchestration_event(
            instance_id, REVIEW_EVENT, data={"action": action, "actor": actor, "note": note}
        )

    def get_status(self, instance_id: str) -> Optional[dict]:
        """Return {status, history, runtimeStatus} from custom status/output, or None if unknown."""
        client = self._connect()
        state = client.get_orchestration_state(instance_id)
        if state is None:
            return None
        payload: dict[str, Any] = {"instanceId": instance_id, "runtimeStatus": str(getattr(state, "runtime_status", ""))}
        # Prefer the final output; fall back to the live custom status while still pending.
        import json

        raw = getattr(state, "serialized_output", None) or getattr(state, "serialized_custom_status", None)
        if raw:
            try:
                payload.update(json.loads(raw))
            except (json.JSONDecodeError, TypeError):
                pass
        return payload


if __name__ == "__main__":
    run_worker()
