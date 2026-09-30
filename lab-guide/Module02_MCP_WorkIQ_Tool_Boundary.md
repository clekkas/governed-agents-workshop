# Module 02: MCP Server and Work IQ Tool Boundary

## Objective

Design a governed tool boundary for patient context, protocol lookup, utilization history, HITL task creation, and audit logging.

## Tools

| Tool | Purpose | Required control |
| --- | --- | --- |
| `patient.get` | Retrieve redacted case summary | Patient-context scope |
| `notes.get` | Retrieve relevant note excerpts | PHI minimization |
| `protocol.search` | Retrieve approved protocol evidence | Citation metadata |
| `utilization.history` | Retrieve prior encounter summary | Aggregation by default |
| `task.create` | Create HITL review task | Human approval required |
| `audit.write` | Record material workflow events | Always on |

## Work IQ pattern

**Work IQ is Microsoft's governed workplace-intelligence layer over Microsoft 365** — a shipping,
consumable service (not a server you build) that an agent reaches via **MCP, A2A, or REST**. It
reasons over mail, Teams, files, people, calendar, Planner, and enterprise search, and runs on
**Microsoft Entra delegated / on-behalf-of identity only**: the agent sees only what the signed-in
user can, with sensitivity labels, DLP, and an OPA policy engine enforced on every call.

In this workshop's trust model, keep two lanes clean:

- **Clinical / PHI → our own governed MCP tools** (the table above), with PHI minimization.
- **M365 work context → Work IQ**, on the user's identity — surrounding, non-clinical collaboration
  context (Teams threads, meeting summaries, SharePoint SOPs). We consume Microsoft's governed
  server; we do not build or secure it.

The agent must never bypass user permissions or tool authorization. Work IQ is usage-billed via
Copilot Credits, independent of Copilot licensing. Full brief: **`docs/work-iq-overview.md`**.

## Securing the MCP server (core question)

See **`docs/securing-mcp-servers.md`** for the full, source-grounded standard. The six layers:

1. **Network** — private MCP on Azure Container Apps internal ingress + a dedicated MCP subnet; public endpoints only for trusted read-only servers.
2. **Authentication** — via a Foundry project connection; prefer `project-managed-identity` / `agentic-identity`, and `user-entra-token` for per-user data. Treat static `custom-keys` as a last resort.
3. **Authorization** — RBAC (`Foundry User` to use, `Foundry Project Manager` to create connections); per-tool contracts + least-privilege scopes.
4. **Centralize** — front tools with a **Foundry Toolbox** (one MCP-compatible endpoint; centralized credentials, versioning, policy).
5. **Human approval** — require approval on write/mutating tool calls (e.g. `task.create`).
6. **Audit** — always-on tool-call audit events.

## Output

Tool contracts, scopes, auth model, network posture, and audit requirements.

