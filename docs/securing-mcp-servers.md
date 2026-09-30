# Securing MCP Servers — guidance for Kaiser Permanente

> Answers the workshop's named "core question": *what is Microsoft's recommended standard for
> securing MCP servers?* Covers transport, authentication, authorization/least privilege,
> credential management, human approval of tool calls, and audit — across the SDLC.
>
> Grounded in Microsoft Learn: **Connect agents to MCP server endpoints**
> (`/azure/foundry/agents/how-to/tools/model-context-protocol`), **Foundry Toolboxes**
> (`/azure/foundry/agents/how-to/tools/toolbox`), and **Agent tools with network isolation**
> (`/azure/foundry/agents/how-to/configure-private-link`). Verify specifics at delivery time.

## The one-line answer

Put the MCP server behind **(1) a private network boundary**, **(2) an identity-based auth type via
a Foundry project connection** (managed identity / agentic identity / Entra token — not static
keys), **(3) least-privilege tool scoping with per-tool contracts**, **(4) centralized credentials
and policy via a Toolbox**, and **(5) human approval on sensitive tool calls** — then **(6) audit
every call**. Security is layered; no single control is sufficient.

## Layer 1 — Network / transport boundary

Agent Service supports **public** and **private** MCP endpoints:

| Endpoint | When | Requirement |
| --- | --- | --- |
| **Public** | Trusted external MCP (e.g. GitHub, Microsoft Learn) | Works with basic + standard setup; still authenticate. |
| **Private** (recommended for KP-owned tools over PHI-adjacent data) | Your own MCP server, no public exposure | **Private networking + a dedicated MCP subnet** in your VNet. Deploy the MCP server on **Azure Container Apps with internal-only ingress** on a subnet delegated to `Microsoft.App/environments`. |

KP guidance: any MCP server that touches member-adjacent or regulated data should be **private**,
internal-ingress only, on its own delegated subnet — never a public endpoint. Microsoft ships Bicep
samples (`infrastructure-setup-bicep/19-private-network-agent-tools`) that provision the MCP subnet.

## Layer 2 — Authentication (via a Foundry project connection)

Never bake credentials into the agent. Create a **project connection** with the auth type that fits,
then reference it from the tool/toolbox. Auth types, best → weakest for enterprise use:

| `--auth-type` | Use for | Notes |
| --- | --- | --- |
| `project-managed-identity` | KP-owned Azure-hosted MCP (e.g. Cognitive Services) | Project's system-assigned MI; no secrets to manage. **Prefer this.** |
| `agentic-identity` | Per-agent identity to a resource | The agent's own per-project identity; finest-grained attribution. |
| `user-entra-token` | Per-user delegated access (e.g. Fabric, M365) | Passes the **user's** Entra token → permission-trimmed to what that user may see (OBO-style). Pair with the RAG OBO pattern. |
| `oauth2` | Third-party or your own IdP | Foundry-managed OAuth app **or** BYO app registration (`authorization-url`, `token-url`, `client-id/secret`, `scopes`). |
| `custom-keys` | Header/PAT-only servers | Static secret in the connection — **last resort**; store/rotate carefully; never in code. |
| `none` | Public, non-sensitive MCP only | No auth; only for read-only public servers. |

KP guidance: default to **`project-managed-identity`** or **`agentic-identity`** for KP-owned
servers; **`user-entra-token`** whenever the tool reaches per-user data (matches the RAG OBO rule in
`docs/rag-guidance-gpt-rag.md` — separate caller identity from service identity, test allowed AND
denied users). Treat `custom-keys` as a temporary bridge, not a standard.

## Layer 3 — Authorization / least privilege

- **RBAC**: `Foundry User` to use agents/tools; `Foundry Project Manager` to create the connection.
  (Roles were renamed from Azure AI User / Project Manager — IDs unchanged.)
- **Tool scoping**: expose only the tools a use case needs; each tool declares a **contract**
  (argument schema + required scope). Validate arguments against the contract and reject drift.
- **Data minimization at the tool boundary**: tools return redacted/aggregated results by default
  (PHI-minimization), not raw records.

## Layer 4 — Centralize credentials & policy with a Toolbox

A **Foundry Toolbox** bundles tools (MCP servers, Azure AI Search, OpenAPI, Code Interpreter, A2A,
etc.) into **one MCP-compatible endpoint**, centralizing **credential management, versioning, and
policy enforcement**. Point agents at the toolbox `server_url`/`server_label`; add/remove/reconfigure
tools without touching agent code. Any MCP-capable runtime (Foundry, Agent Framework, LangGraph,
Copilot SDK) can consume it. **This is the recommended way to run MCP at scale** — one governed
endpoint instead of per-agent credential sprawl.

## Layer 5 — Human approval of tool calls

Agent Service supports **review-and-approve on MCP tool calls**. Require approval for any tool that
writes, mutates, or triggers a downstream action (e.g. `task.create`). This is the same
human-in-the-loop principle the workshop implements with the Durable Task Scheduler gate — keep a
human between the agent and any consequential action.

## Layer 6 — Audit everything

Emit an audit event per tool call (name, scope, decision allow/redact/deny, latency, correlation
ID). A recorded event doesn't prove correct behavior and missing telemetry doesn't prove an action
didn't happen — so make audit **always-on** and fail closed. Ties to the telemetry taxonomy in
`docs/governance-security-observability.md`.

## SDLC checklist (what to tell app teams)

1. **Design**: choose public vs private; pick the identity-based auth type; list the minimum tools.
2. **Build**: define per-tool contracts + scopes; wire the project connection (no secrets in code).
3. **Deploy**: private MCP on ACA internal ingress + dedicated subnet; front tools with a Toolbox.
4. **Operate**: RBAC least privilege; approval on write tools; always-on audit; rotate any keys.
5. **Govern**: review data movement/region per tool; test allowed AND denied users for user-scoped tools.

## Workshop mapping

- `mcp-server/tool-contracts/*.schema.json` + `mcp-server/validate-contracts.js` are the per-tool
  contract + drift-rejection control (Layer 3). `Module02` lists the discharge-transition tool
  boundary (`patient.get` redact, `task.create` human-approved, `audit.write` always-on).
- Our deployed Container Apps environment (`cae-…`) is the substrate for an internal-ingress private
  MCP server on a delegated subnet (Layer 1) — a concrete "make it private" demo.
- `task.create` → the Durable Task Scheduler HITL gate is Layer 5 in action.

## References (public)

- Connect agents to MCP servers: `/azure/foundry/agents/how-to/tools/model-context-protocol`
- Foundry Toolboxes: `/azure/foundry/agents/how-to/tools/toolbox`
- Agent tools with network isolation: `/azure/foundry/agents/how-to/configure-private-link`
- Private network agent-tools Bicep: `github.com/microsoft-foundry/foundry-samples` → `infrastructure-setup-bicep/19-private-network-agent-tools`
