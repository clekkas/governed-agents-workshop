"""Mock MCP tools.

Stand-ins for the governed MCP tool boundary the specialist agents call. Each returns
a ToolResult with a policy decision, latency, and payload. In a later step these are
replaced by a real MCP server; the agent-facing contract stays the same.

Safety-relevant tools enforce their own rules here (not just in prompts):
- risk_score.get is read-only and deterministic; it cannot generate or override a score.
- task.create drafts a review task only; it cannot approve.
- audit.write runs for every material action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_LATENCY = {
    "patient.get": 118,
    "utilization.history": 164,
    "risk_score.get": 74,
    "protocol.search": 242,
    "task.create": 96,
    "audit.write": 55,
}


@dataclass
class ToolResult:
    name: str
    decision: str
    latency_ms: int
    result: dict[str, Any] = field(default_factory=dict)


def _timed(name: str, decision: str, result: dict[str, Any]) -> ToolResult:
    return ToolResult(name=name, decision=decision, latency_ms=_LATENCY.get(name, 120), result=result)


def patient_get(case: dict[str, Any]) -> ToolResult:
    """Redacted, minimum-necessary case context only."""
    return _timed(
        "patient.get",
        "redact",
        {
            "patient_label": case["patient_label"],
            "facility": case["facility"],
            "diagnosis": case["diagnosis"],
            "encounters": case["context"].get("encounters"),
        },
    )


def utilization_history(case: dict[str, Any]) -> ToolResult:
    """Aggregate only; never event-level by default."""
    return _timed(
        "utilization.history",
        "allow",
        {"aggregate": True, "driver_codes": case["approved_risk_score"]["driver_codes"]},
    )


def risk_score_get(case: dict[str, Any]) -> ToolResult:
    """Deterministic approved score with provenance. Never generated or overridden."""
    score = dict(case["approved_risk_score"])
    return _timed("risk_score.get", "allow", score)


def protocol_search(case: dict[str, Any], kb: Any = None) -> ToolResult:
    """Retrieve approved protocol evidence via the knowledge base (RAG).

    Builds a query from the case, retrieves cited evidence from data/rag-docs, and reports
    a decision. If the case requires a diagnosis-specific ("specialty") protocol and the
    corpus has no matching document, the decision is review_required so the workflow escalates
    instead of proceeding on general guidance.
    """
    diagnosis = case.get("diagnosis", "")
    query = f"{diagnosis} discharge transition follow-up medication reconciliation appointment transportation escalation"
    evidence = kb.retrieve(query, diagnosis=diagnosis) if kb is not None else list(case.get("evidence", []))

    requires_specialty = case["context"].get("specialty_protocol") == "missing"
    specialty_found = kb.has_protocol_for(diagnosis) if kb is not None else False
    decision = "review_required" if (requires_specialty and not specialty_found) else "allow"
    return _timed("protocol.search", decision, {"evidence": evidence})


def task_create(case: dict[str, Any]) -> ToolResult:
    """Creates a draft HITL review task only; cannot approve it."""
    return _timed(
        "task.create",
        "review_required",
        {"task_id": f"task-{case['id']}", "status": "PendingReview", "assigned_role": "Care Manager"},
    )


def audit_write(case: dict[str, Any], event_type: str) -> ToolResult:
    """Always-on compliance record."""
    return _timed("audit.write", "allow", {"event_type": event_type, "case_id": case["id"]})
