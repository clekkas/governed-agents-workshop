"""Hosted-agent execution mode: drive the published Foundry agents.

This is the DEFAULT execution path (AGENT_EXECUTION_MODE=foundry). It drives the persistent
Foundry agents created by scripts/publish_hosted_agents.py — the orchestrator plus the seven
specialists — so their runs are visible in the Foundry portal and traces.

Safety boundary is IDENTICAL to local mode and enforced in Python, not by the model:

  * the approved risk score is read from the governed `risk_score.get` tool — never generated;
  * evidence comes from the approved-source retrieval tool — never invented;
  * transition gaps, the policy decision, and the HITL task are computed by governed Python;
  * the operational draft packet (owners / due times) stays deterministic.

The hosted agents contribute grounded, in-role NARRATIVE only (the handoff summaries). They are
given the governed facts and asked to describe their step; they cannot change the facts. On any
Foundry error the caller falls back to the local deterministic orchestrator, so the response
contract is always the same.
"""

from __future__ import annotations

import os
import time
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
    ORCHESTRATOR_NAME,
    PolicyGuardrailAgent,
    RiskScoreAgent,
    TransitionExceptionAgent,
    manifest_id,
)

_TERMINAL_OK = {"completed"}
_TERMINAL_BAD = {"failed", "cancelled", "expired"}


def _run_state(run: Any) -> str:
    """Normalize a ThreadRun status to a lowercase string.

    RunStatus is a str-enum whose str() is 'RunStatus.COMPLETED'; its .value is 'completed'.
    Comparing str(status) would never match the terminal sets, so use the value.
    """
    status = getattr(run, "status", None)
    return str(getattr(status, "value", status) or "").lower()


class FoundryAgentsUnavailable(RuntimeError):
    """Raised when the hosted-agent path cannot be used; the caller should fall back to local."""


class FoundryAgentOrchestrator:
    """Runs the workflow with governed Python facts + hosted-agent narrative."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        knowledge: Optional[KnowledgeBase] = None,
        per_agent_timeout: Optional[float] = None,
    ) -> None:
        # Reuse FoundryClient only to resolve the project endpoint + model deployment.
        resolver = FoundryClient()
        self.endpoint = (endpoint or resolver.endpoint or "").strip()
        self.model = (model or resolver.deployment or os.environ.get("FOUNDRY_MODEL_DEPLOYMENT", "gpt-4o")).strip()
        self.knowledge = knowledge or KnowledgeBase()
        self.per_agent_timeout = per_agent_timeout or float(os.environ.get("FOUNDRY_AGENT_TIMEOUT", "30"))
        # Narration can be disabled (facts-only) to prove routing cheaply: FOUNDRY_NARRATE=0.
        self.narrate = os.environ.get("FOUNDRY_NARRATE", "1").strip().lower() not in {"0", "false", "no"}
        self._client = None
        self._agents_by_name: dict[str, str] = {}
        self.available = bool(self.endpoint)

    # ---- connection ----

    def _connect(self) -> None:
        if self._client is not None:
            return
        if not self.endpoint:
            raise FoundryAgentsUnavailable("no project endpoint (set AZURE_AI_PROJECT_ENDPOINT)")
        try:
            from azure.ai.agents import AgentsClient
            from azure.identity import DefaultAzureCredential

            client = AgentsClient(endpoint=self.endpoint, credential=DefaultAzureCredential())
            agents: dict[str, str] = {}
            for a in client.list_agents():
                if a.name:
                    agents[a.name] = a.id
        except Exception as exc:  # noqa: BLE001
            raise FoundryAgentsUnavailable(f"cannot connect to Foundry Agents: {exc}") from exc
        if not agents:
            raise FoundryAgentsUnavailable("no hosted agents found; run publish_hosted_agents.py")
        self._client = client
        self._agents_by_name = agents

    def _agent_id(self, agent_name: str) -> Optional[str]:
        # Orchestrator display name maps to the orchestrator manifest id.
        if agent_name == ORCHESTRATOR_NAME:
            return self._agents_by_name.get("discharge-transition-orchestrator")
        return self._agents_by_name.get(manifest_id(agent_name))

    # ---- one hosted-agent turn (grounded narrative only) ----

    def _narrate(self, thread_id: str, agent_name: str, grounding: str, deterministic: str) -> str:
        """Ask the hosted agent for an in-role summary grounded on governed facts.

        Returns the hosted agent's text, or the deterministic summary on any problem, so a slow
        or failed run never breaks the response.
        """
        agent_id = self._agent_id(agent_name)
        if not agent_id:
            return deterministic
        from azure.ai.agents.models import MessageRole

        prompt = (
            f"Governed facts for this discharge-transition case (authoritative — do not change, "
            f"recalculate, or add to them):\n{grounding}\n\n"
            f"In one or two sentences, summarize what you (the {agent_name}) did for this step, "
            f"consistent with your guardrails. Do not invent facts, do not approve anything, and "
            f"do not declare the patient safe to discharge."
        )
        try:
            self._client.messages.create(thread_id=thread_id, role="user", content=prompt)
            run = self._client.runs.create(thread_id=thread_id, agent_id=agent_id)
            deadline = time.time() + self.per_agent_timeout
            while _run_state(run) not in _TERMINAL_OK | _TERMINAL_BAD:
                if time.time() > deadline:
                    try:
                        self._client.runs.cancel(thread_id=thread_id, run_id=run.id)
                    except Exception:  # noqa: BLE001
                        pass
                    return deterministic
                time.sleep(1)
                run = self._client.runs.get(thread_id=thread_id, run_id=run.id)
            if _run_state(run) not in _TERMINAL_OK:
                return deterministic
            msg = self._client.messages.get_last_message_text_by_role(thread_id, MessageRole.AGENT)
            text = getattr(getattr(msg, "text", None), "value", "") if msg else ""
            return text.strip() or deterministic
        except Exception:  # noqa: BLE001
            return deterministic

    # ---- public API (same contract as DischargeTransitionOrchestrator.run) ----

    def run(self, case: dict[str, Any], correlation_id: Optional[str] = None) -> InvokeResult:
        self._connect()  # raises FoundryAgentsUnavailable -> caller falls back to local
        cid = correlation_id or f"trace-{uuid.uuid4()}"

        # 1. Compute the governed FACTS with the same deterministic specialists as local mode.
        ctx = Context(case=case, correlation_id=cid, knowledge=self.knowledge)
        ctx.record(
            ORCHESTRATOR_NAME,
            "Coordinator",
            "completed",
            "Started discharge-transition exception workflow and assembled specialist outputs.",
            "Case Context Agent",
        )
        CaseContextAgent().run(ctx)
        RiskScoreAgent().run(ctx)
        EvidenceRetrievalAgent().run(ctx)
        TransitionExceptionAgent().run(ctx)
        CarePlanDraftingAgent().run(ctx)  # deterministic operational draft (owners/due times)
        policy_decision = PolicyGuardrailAgent().run(ctx)
        HumanReviewAgent().run(ctx)

        # 2. Drive the hosted agents to produce grounded narrative for each handoff.
        if self.narrate:
            grounding = self._grounding(case, ctx)
            try:
                thread = self._client.threads.create()
                thread_id = thread.id
            except Exception:  # noqa: BLE001
                thread_id = None
            if thread_id:
                for h in ctx.handoffs:
                    h["summary"] = self._narrate(thread_id, h["agent_name"], grounding, h["summary"])
                try:
                    self._client.threads.delete(thread_id)
                except Exception:  # noqa: BLE001
                    pass

        # 3. Assemble the identical InvokeResult contract.
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

    @staticmethod
    def _grounding(case: dict[str, Any], ctx: Context) -> str:
        risk = ctx.approved_risk_score or {}
        lines = [
            f"case_id: {case.get('id')}",
            f"facility: {case.get('facility')}",
            f"summary: {case.get('summary')}",
            f"approved_risk_score: tier={risk.get('tier')} score={risk.get('score')} provenance={risk.get('provenance')}",
            f"transition_gaps: {', '.join(ctx.transition_gaps) or 'none'}",
            f"evidence_citations: {', '.join(e.get('citation', '') for e in ctx.evidence) or 'none'}",
            f"evidence_blocked: {ctx.evidence_blocked}",
        ]
        return "\n".join(lines)
