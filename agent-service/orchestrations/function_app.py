# =============================================================================
# Discharge Transition approval — Durable Task Scheduler reference orchestration
# =============================================================================
#
# REFERENCE / TEACHING CODE — not wired into the local demo. This is the target
# the local durable HITL store (agent-service/src/discharge_transition_agent/hitl.py)
# graduates to. It runs on Azure Functions with the Microsoft Agent Framework
# Durable Extension, backed by the Durable Task Scheduler ("Data Task Scheduler").
#
# Why it is not run in the workshop laptop path:
#   * requires the Azure Functions host + a Durable Task Scheduler backend (or its
#     local emulator) and the pre-release agent-framework packages, which do not
#     build on Windows ARM64 today.
#   * the local store reproduces the SAME state machine, audit contract, and
#     timeout->escalate branch so the demo stays runnable offline.
#
# Install (on a supported host):
#   pip install azure-identity agent-framework-azurefunctions --pre azure-functions-durable
#
# Pattern source: Microsoft Learn — "Durable Extension" (Agent Framework hosting on
# Azure Functions), Human-in-the-loop orchestrations section.
# =============================================================================

from __future__ import annotations

import os
from datetime import timedelta

import azure.durable_functions as df
from agent_framework.azure import AgentFunctionApp
from agent_framework.openai import OpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential

# ---- 1. Register the agent(s) that draft the exception packet ----------------
# In the workshop, the multi-agent orchestrator (7 specialists) drafts the packet.
# Here we register the single drafting agent for brevity; add the others the same way.
drafting_agent = OpenAIChatCompletionClient(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    model=os.getenv("AZURE_OPENAI_CHAT_COMPLETION_MODEL", "gpt-5-mini"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    credential=DefaultAzureCredential(),
).as_agent(
    instructions=(
        "You draft a discharge-transition exception packet from an APPROVED risk score and "
        "retrieved protocol evidence. You never generate or override a risk score, never state a "
        "patient is safe to discharge, and never make a clinical determination. Draft only."
    ),
    name="CarePlanDraftingAgent",
)

app = AgentFunctionApp(agents=[drafting_agent])

# The review SLA. On the Durable Task Scheduler the orchestration consumes NO compute and NO model
# tokens while it waits — the timer is durable, so this can safely be hours or days.
REVIEW_SLA = timedelta(seconds=int(os.getenv("HITL_SLA_SECONDS", "86400")))


# ---- 2. The human-in-the-loop orchestration ---------------------------------
@app.orchestration_trigger(context_name="context")
def discharge_exception_approval(context: df.DurableOrchestrationContext):
    """Draft an exception packet, then pause on the care-manager approval gate.

    States mirror the local store exactly:
      PendingReview -> Approved | NeedsRework | Rejected ; timeout -> Escalated.
    Every branch calls an audit activity so the record is identical to the local mirror.
    """
    case = context.get_input()

    # Policy escalation (e.g. missing specialty protocol) never waits for a routine reviewer —
    # it goes straight to a specialist, exactly like the local store's Escalated-on-create path.
    if case.get("policyDecision") == "escalate":
        yield context.call_activity("audit_transition", _audit(case, None, "Escalated", "escalate", "orchestrator"))
        return yield_result(context, "Escalated", case)

    # --- draft the packet (durably checkpointed) ---
    drafting = app.get_agent(context, "CarePlanDraftingAgent")
    draft = yield drafting.run(messages=f"Draft an exception packet for case {case['caseId']}.")
    yield context.call_activity("audit_transition", _audit(case, None, "PendingReview", "create", "orchestrator"))

    # --- notify the care manager and pause on the external decision event ---
    yield context.call_activity("notify_care_manager", {"case": case, "draft": draft})

    decision_event = context.wait_for_external_event("ReviewDecision")
    timeout = context.create_timer(context.current_utc_datetime + REVIEW_SLA)
    winner = yield context.task_any([decision_event, timeout])

    if winner == timeout:
        # Timer -> escalate branch (compute was zero the entire wait).
        yield context.call_activity("audit_transition", _audit(case, "PendingReview", "Escalated", "escalate", "system"))
        return yield_result(context, "Escalated", case)

    timeout.cancel()
    decision = decision_event.result or {}
    action = (decision.get("action") or "").lower()
    actor = decision.get("actor") or "care-manager"

    # Human-only guard: agents cannot approve or reject (state-machine rule 1).
    if action in {"approve", "reject"} and actor.lower() in {"agent", "orchestrator", "system", ""}:
        raise ValueError("approve/reject require a human reviewer")

    mapping = {"approve": "Approved", "request_changes": "NeedsRework", "reject": "Rejected"}
    destination = mapping.get(action)
    if destination is None:
        raise ValueError(f"unknown review action '{action}'")

    yield context.call_activity("audit_transition", _audit(case, "PendingReview", destination, action, actor))
    if destination == "Approved":
        yield context.call_activity("finalize_exception_packet", {"case": case, "draft": draft})
    return yield_result(context, destination, case)


# ---- 3. Activities (side effects live here, never in the orchestrator body) --
@app.activity_trigger(input_name="payload")
def notify_care_manager(payload: dict) -> str:
    # Post to Teams / queue / email. Kept as a stub in the reference.
    return "notified"


@app.activity_trigger(input_name="record")
def audit_transition(record: dict) -> str:
    # Append-only audit sink (Log Analytics / append blob / table). Same fields as the local store.
    return "audited"


@app.activity_trigger(input_name="payload")
def finalize_exception_packet(payload: dict) -> str:
    # task.create (draft only) downstream — still cannot approve on the patient's behalf.
    return "finalized"


# ---- helpers -----------------------------------------------------------------
def _audit(case: dict, src, dst: str, action: str, actor: str) -> dict:
    return {
        "correlationId": case.get("correlationId"),
        "caseId": case.get("caseId"),
        "from": src,
        "to": dst,
        "action": action,
        "actor": actor,
    }


def yield_result(context, status: str, case: dict) -> dict:
    return {"correlationId": case.get("correlationId"), "status": status}
