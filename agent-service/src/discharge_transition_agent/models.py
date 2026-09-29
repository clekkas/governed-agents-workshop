"""Pydantic models for the agent invoke contract.

JSON is camelCase to match the Node backend and the React UI. Python fields are
snake_case; an alias generator maps them to camelCase on serialization.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

RiskTier = Literal["Critical", "High", "Medium", "Low"]
PolicyDecision = Literal["allow", "redact", "review_required", "deny", "escalate"]
AgentStatus = Literal["completed", "needs-review", "blocked"]


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class InvokeRequest(CamelModel):
    case_id: str
    actor_role: Optional[str] = "care-manager"


class ApprovedRiskScore(CamelModel):
    tier: RiskTier
    score: float
    provenance: str


class Evidence(CamelModel):
    source: str
    citation: str
    claim: str
    confidence: str = "Medium"


class ToolCall(CamelModel):
    name: str
    decision: PolicyDecision
    latency_ms: int


class AgentHandoff(CamelModel):
    agent_name: str
    role: str
    status: AgentStatus
    summary: str
    handoff_to: Optional[str] = None


class InvokeResult(CamelModel):
    correlation_id: str
    case_id: str
    summary: str
    approved_risk_score: ApprovedRiskScore
    transition_gaps: list[str]
    missing_information: list[str]
    evidence: list[Evidence]
    draft_exception_packet: list[str]
    tool_calls: list[ToolCall]
    agent_handoffs: list[AgentHandoff]
    policy_decision: PolicyDecision
    requires_human_review: bool


class CaseSummary(CamelModel):
    id: str
    patient_label: str
    facility: str
    diagnosis: str
    risk_tier: RiskTier
    summary: str
