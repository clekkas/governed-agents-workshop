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

Use Work IQ as a permission-aware enterprise context pattern where appropriate. The agent should not bypass user permissions or tool authorization.

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

