"""External MCP routing seam for the discharge-transition agent.

By default the agent calls its governed tools **in-process** (``tools.py``) — identical contracts and
policy decisions, zero extra moving parts, and it keeps the evaluation gate hermetic. This module is
the **graduation seam**: when ``USE_EXTERNAL_MCP=1`` is set, tool calls can be routed to the real
governed MCP server (``mcp-server/server.py``) instead, and Work IQ can be attached as a *separate*
connection for M365 work context.

The switch is intentionally **off by default**. The live path lazy-imports the MCP client SDK only
when enabled, so neither CI nor the eval gate depends on it. See
``mcp-server/connections/README.md`` for the connection design.
"""

from __future__ import annotations

import os
from typing import Any

# MCP tool name -> the kwargs the agent sends. Mirrors mcp-server/validate-contracts.js so the
# in-process and over-MCP invocations are provably the same shape.
def case_to_args(tool: str, case: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    pid = case.get("id") or case.get("patientId")
    enc = case.get("context", {}).get("encounter_id", "E1")
    if tool == "patient.get":
        return {"patientId": pid, "correlationId": correlation_id, "purpose": "care-review"}
    if tool == "notes.get":
        return {"patientId": pid, "encounterId": enc, "correlationId": correlation_id, "redactedOnly": True}
    if tool == "utilization.history":
        return {"patientId": pid, "correlationId": correlation_id, "lookbackDays": 365, "aggregateOnly": True}
    if tool == "risk_score.get":
        return {"patientId": pid, "encounterId": enc, "correlationId": correlation_id, "includeDriverCodes": True}
    if tool == "protocol.search":
        return {"query": f"{case.get('diagnosis', '')} discharge follow-up", "correlationId": correlation_id, "topK": 5}
    if tool == "task.create":
        return {"patientId": pid, "correlationId": correlation_id, "draftPlan": "Confirm follow-up appointment within 48h.",
                "evidence": [{"source": "Discharge Protocol", "claim": "Follow-up within 48-72h."}], "assignedRole": "Care Manager"}
    if tool == "audit.write":
        return {"correlationId": correlation_id, "eventType": "task.created", "actor": "orchestrator",
                "timestamp": "2026-09-28T22:00:00Z"}
    raise KeyError(f"no arg mapping for tool '{tool}'")


def use_external_mcp() -> bool:
    """True when the agent should route tool calls through the external MCP server."""
    return os.environ.get("USE_EXTERNAL_MCP", "").strip() in ("1", "true", "True")


def mcp_server_url() -> str:
    """Internal URL of the hosted MCP server, if deployed (empty for stdio-only)."""
    return os.environ.get("MCP_SERVER_URL", "").strip()


def clinical_server_command() -> list[str]:
    """The stdio command that launches the governed clinical MCP server (local transport)."""
    return ["python", "mcp-server/server.py"]


async def call_external(tool: str, args: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover - live path
    """Route one governed tool call through the external MCP server.

    Two transports, chosen automatically:
    - **HTTP (hosted):** when ``MCP_SERVER_URL`` is set (the deployed internal Container App), use the
      streamable-http transport.
    - **stdio (local):** otherwise launch ``server.py`` as a subprocess.

    Lazy-imports the MCP client SDK so the default (in-process) path never requires it. Enabled only
    when ``USE_EXTERNAL_MCP=1``.
    """
    from mcp import ClientSession

    url = mcp_server_url()
    if url:
        from mcp.client.streamable_http import streamablehttp_client

        async with streamablehttp_client(url.rstrip("/") + "/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool, arguments=args)
                return {"content": [c.text for c in result.content if getattr(c, "type", "") == "text"]}

    from mcp import StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=clinical_server_command()[0], args=clinical_server_command()[1:])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, arguments=args)
            return {"content": [c.text for c in result.content if getattr(c, "type", "") == "text"]}
