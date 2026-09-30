"""Discharge-transition MCP server (real, runnable).

A governed Model Context Protocol server that exposes the seven clinical tools of the
discharge-transition trust boundary over stdio. It is the graduation target for the in-process
"mock" tools in ``agent-service``: same tool names, same JSON contracts, same governed decisions —
now reachable by any MCP-capable client (a Foundry agent, an IDE, the ``workiq``-style CLI pattern).

Run it directly:

    pip install -r mcp-server/requirements.txt
    python mcp-server/server.py            # speaks MCP over stdio

Or wire it into an MCP client config (see ``mcp-server/connections/clinical.mcp.json``).

Governance note: every tool validates its arguments against the published JSON contract before
running, enforces its policy decision (redact / allow / review_required) in code, and returns a
structured result. All data is synthetic — never point this at real PHI.
"""

from __future__ import annotations

from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - clear message when the SDK isn't installed
    raise SystemExit(
        "The 'mcp' package is required to run the server. Install it with:\n"
        "    pip install -r mcp-server/requirements.txt"
    ) from exc

import governed_tools as gt

mcp = FastMCP("discharge-transition-clinical-tools")


@mcp.tool(name="patient.get", description="Redacted, minimum-necessary case context for a patient.")
def patient_get(patientId: str, correlationId: str, purpose: str = "care-review", expandedScope: bool = False) -> dict[str, Any]:
    return gt.patient_get(patientId, correlationId, purpose, expandedScope).to_dict()


@mcp.tool(name="utilization.history", description="Aggregate prior-encounter summary (aggregate-only by default).")
def utilization_history(patientId: str, correlationId: str, lookbackDays: int = 365, aggregateOnly: bool = True) -> dict[str, Any]:
    return gt.utilization_history(patientId, correlationId, lookbackDays, aggregateOnly).to_dict()


@mcp.tool(name="risk_score.get", description="Read-only approved risk score. Never generated or overridden.")
def risk_score_get(patientId: str, encounterId: str, correlationId: str, includeDriverCodes: bool = True) -> dict[str, Any]:
    return gt.risk_score_get(patientId, encounterId, correlationId, includeDriverCodes).to_dict()


@mcp.tool(name="protocol.search", description="Retrieve approved, cited protocol evidence; escalates when a required specialty protocol is missing.")
def protocol_search(query: str, correlationId: str, facility: str | None = None, topK: int = 5, specialtyRequired: bool = False, specialtyFound: bool = True) -> dict[str, Any]:
    return gt.protocol_search(query, correlationId, facility, topK, specialtyRequired, specialtyFound).to_dict()


@mcp.tool(name="task.create", description="Draft a human-review task only. Cannot approve.")
def task_create(patientId: str, correlationId: str, draftPlan: str, evidence: list[dict[str, Any]], assignedRole: str = "Care Manager") -> dict[str, Any]:
    return gt.task_create(patientId, correlationId, draftPlan, evidence, assignedRole).to_dict()


@mcp.tool(name="audit.write", description="Always-on compliance audit record.")
def audit_write(correlationId: str, eventType: str, actor: str, timestamp: str) -> dict[str, Any]:
    return gt.audit_write(correlationId, eventType, actor, timestamp).to_dict()


@mcp.tool(name="notes.get", description="Redacted clinical note excerpts (minimum necessary).")
def notes_get(patientId: str, encounterId: str, correlationId: str, redactedOnly: bool = True) -> dict[str, Any]:
    return gt.notes_get(patientId, encounterId, correlationId, redactedOnly).to_dict()


if __name__ == "__main__":
    mcp.run()
