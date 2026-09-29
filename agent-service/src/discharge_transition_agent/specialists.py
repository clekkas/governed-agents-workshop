"""Specialist agents and the shared run context.

Each specialist is a small, independently testable agent with a narrow responsibility.
They record their tool calls and a handoff so the workflow is observable. This mirrors
the multi-agent design in agents/multi-agent-orchestration.md.

The specialists use deterministic reasoning by default so the service runs locally with
no cloud dependency. When a Foundry model client is provided, the drafting and summary
steps can be delegated to the model (see foundry.py); the safety boundary is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from . import tools
from .demo import is_break
from .tools import ToolResult


@dataclass
class Context:
    """Shared state passed between specialists during one workflow run."""

    case: dict[str, Any]
    correlation_id: str
    knowledge: Any = None
    tool_calls: list[ToolResult] = field(default_factory=list)
    handoffs: list[dict[str, Any]] = field(default_factory=list)
    # Working outputs accumulated by specialists.
    approved_risk_score: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    evidence_blocked: bool = False
    transition_gaps: list[str] = field(default_factory=list)
    draft_packet: list[str] = field(default_factory=list)

    def record(self, agent_name: str, role: str, status: str, summary: str, handoff_to: Optional[str] = None) -> None:
        self.handoffs.append(
            {
                "agent_name": agent_name,
                "role": role,
                "status": status,
                "summary": summary,
                "handoff_to": handoff_to,
            }
        )

    def call(self, result: ToolResult) -> ToolResult:
        self.tool_calls.append(result)
        return result


class Specialist:
    name = "Specialist"
    role = "Specialist"

    def run(self, ctx: Context) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class CaseContextAgent(Specialist):
    name = "Case Context Agent"
    role = "Context"

    def run(self, ctx: Context) -> None:
        ctx.call(tools.patient_get(ctx.case))
        ctx.call(tools.utilization_history(ctx.case))
        ctx.record(self.name, self.role, "completed", "Returned redacted case summary and utilization signals.", "Risk Score Agent")


class RiskScoreAgent(Specialist):
    name = "Risk Score Agent"
    role = "Approved score"

    def run(self, ctx: Context) -> None:
        result = ctx.call(tools.risk_score_get(ctx.case))
        ctx.approved_risk_score = result.result
        if is_break("risk_score"):  # workshop demo fault only (EVAL_DEMO_BREAK); off by default
            ctx.approved_risk_score = {**result.result, "score": 0.10, "tier": "Low", "provenance": "agent-recalculated"}
        ctx.record(self.name, self.role, "completed", "Returned approved score, provenance, timestamp, and driver codes.", "Evidence Retrieval Agent")


class EvidenceRetrievalAgent(Specialist):
    name = "Evidence Retrieval Agent"
    role = "RAG"

    def run(self, ctx: Context) -> None:
        result = ctx.call(tools.protocol_search(ctx.case, kb=ctx.knowledge))
        ctx.evidence = result.result.get("evidence", [])
        ctx.evidence_blocked = result.decision == "review_required"
        if ctx.evidence_blocked:
            ctx.record(self.name, self.role, "blocked", "Could not find the requested approved transition protocol source.", "Transition Exception Agent")
        else:
            ctx.record(self.name, self.role, "completed", f"Built evidence packet with {len(ctx.evidence)} citation(s).", "Transition Exception Agent")


class TransitionExceptionAgent(Specialist):
    name = "Transition Exception Agent"
    role = "Gap detection"

    def run(self, ctx: Context) -> None:
        ctx.transition_gaps = list(ctx.case.get("transition_gaps", []))
        status = "needs-review" if ctx.transition_gaps else "completed"
        ctx.record(self.name, self.role, status, f"Identified {len(ctx.transition_gaps)} transition gap(s).", "Care Plan Drafting Agent")


class CarePlanDraftingAgent(Specialist):
    name = "Care Plan Drafting Agent"
    role = "Drafting"

    # Owner/due-time drafts per facility. Draft only; never executed.
    _OWNERS = {
        "Metro General": [
            "Owner: pharmacist pool - due today 2:00 PM - verify medication reconciliation status.",
            "Owner: scheduling team - due today 3:00 PM - confirm follow-up appointment options.",
            "Owner: social work queue - due today 3:30 PM - review transportation support need.",
        ],
        "Riverside Health": [
            "Owner: scheduling team - due tomorrow 10:30 AM - confirm appointment options.",
            "Owner: care manager - due tomorrow noon - review and edit exception packet.",
        ],
        "Community Medical": [
            "Do not use exception packet operationally.",
            "Owner: ADT nurse - due now - assign pending-result owner before discharge workflow proceeds.",
            "Retrieve missing protocol or escalate to human reviewer.",
        ],
    }

    def run(self, ctx: Context, foundry: Any = None) -> None:
        facility = ctx.case["facility"]
        ctx.draft_packet = list(self._OWNERS.get(facility, ["Owner: care manager - review transition gaps."]))
        # Optional model-assisted phrasing; safety boundary unchanged.
        if foundry is not None and foundry.enabled:
            ctx.draft_packet = foundry.refine_draft(ctx.case, ctx.draft_packet, ctx.evidence)
        if is_break("prohibited_claim"):  # workshop demo fault only (EVAL_DEMO_BREAK); off by default
            ctx.draft_packet = [*ctx.draft_packet, "Patient is safe to discharge."]
        ctx.record(self.name, self.role, "completed", "Prepared draft exception packet with proposed owners and due times.", "Policy Guardrail Agent")


class PolicyGuardrailAgent(Specialist):
    name = "Policy Guardrail Agent"
    role = "Safety"

    def run(self, ctx: Context) -> str:
        decision = "allow"
        if ctx.evidence_blocked or ctx.case["context"].get("specialty_protocol") == "missing":
            decision = "escalate"
        elif ctx.transition_gaps:
            decision = "review_required"
        status = "blocked" if decision == "escalate" else "needs-review"
        summary = (
            "Blocked operational draft until missing evidence is resolved."
            if decision == "escalate"
            else "Allowed exception packet creation but required HITL before operational use."
        )
        ctx.record(self.name, self.role, status, summary, "Human Review Agent")
        return decision


class HumanReviewAgent(Specialist):
    name = "Human Review Agent"
    role = "HITL"

    def run(self, ctx: Context) -> None:
        ctx.call(tools.task_create(ctx.case))
        ctx.call(tools.audit_write(ctx.case, "exception_packet_drafted"))
        ctx.record(self.name, self.role, "needs-review", "Created pending human review task and wrote audit event.")
