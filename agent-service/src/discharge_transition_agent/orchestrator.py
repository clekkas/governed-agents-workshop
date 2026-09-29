"""Discharge Transition Orchestrator.

Coordinates the specialist agents through mock MCP tools, preserves the correlation ID,
and assembles the final exception packet. Produces the exact InvokeResult contract shared
with the Node backend and the React UI.

Safety boundary enforced by construction:
- the risk score is consumed from a tool, never generated;
- the draft packet always requires human review;
- missing or blocked evidence escalates instead of guessing.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from .foundry import FoundryClient
from .knowledge import KnowledgeBase
from .models import (
    AgentHandoff,
    ApprovedRiskScore,
    Evidence,
    InvokeResult,
    ToolCall,
)
from .specialists import (
    CarePlanDraftingAgent,
    CaseContextAgent,
    Context,
    EvidenceRetrievalAgent,
    HumanReviewAgent,
    PolicyGuardrailAgent,
    RiskScoreAgent,
    TransitionExceptionAgent,
)


class DischargeTransitionOrchestrator:
    def __init__(self, foundry: Optional[FoundryClient] = None, knowledge: Optional[KnowledgeBase] = None) -> None:
        self.foundry = foundry or FoundryClient()
        self.knowledge = knowledge or KnowledgeBase()

    def run(self, case: dict[str, Any], correlation_id: Optional[str] = None) -> InvokeResult:
        cid = correlation_id or f"trace-{uuid.uuid4()}"
        ctx = Context(case=case, correlation_id=cid, knowledge=self.knowledge)

        # 1. Orchestrator opens the correlated workflow.
        ctx.record(
            "Discharge Transition Orchestrator",
            "Coordinator",
            "completed",
            "Started discharge-transition exception workflow and assembled specialist outputs.",
            "Case Context Agent",
        )

        # 2-8. Specialists in sequence.
        CaseContextAgent().run(ctx)
        RiskScoreAgent().run(ctx)
        EvidenceRetrievalAgent().run(ctx)
        TransitionExceptionAgent().run(ctx)
        CarePlanDraftingAgent().run(ctx, foundry=self.foundry)
        policy_decision = PolicyGuardrailAgent().run(ctx)
        HumanReviewAgent().run(ctx)

        return InvokeResult(
            correlation_id=cid,
            case_id=case["id"],
            summary=case["summary"],
            approved_risk_score=ApprovedRiskScore(
                tier=ctx.approved_risk_score["tier"],
                score=ctx.approved_risk_score["score"],
                provenance=ctx.approved_risk_score["provenance"],
            ),
            transition_gaps=ctx.transition_gaps,
            missing_information=list(case.get("missing_information", [])),
            evidence=[
                Evidence(
                    source=e["source"],
                    citation=e["citation"],
                    claim=e["claim"],
                    confidence=e.get("confidence", "Medium"),
                )
                for e in ctx.evidence
            ],
            draft_exception_packet=ctx.draft_packet,
            tool_calls=[ToolCall(name=t.name, decision=t.decision, latency_ms=t.latency_ms) for t in ctx.tool_calls],
            agent_handoffs=[
                AgentHandoff(
                    agent_name=h["agent_name"],
                    role=h["role"],
                    status=h["status"],
                    summary=h["summary"],
                    handoff_to=h["handoff_to"],
                )
                for h in ctx.handoffs
            ],
            policy_decision=policy_decision,
            requires_human_review=True,
        )
