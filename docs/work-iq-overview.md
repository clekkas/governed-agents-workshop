# Work IQ — governed Microsoft 365 work context for agents

Source-grounded brief for the discharge-transition workshop. Explains what Work IQ is, how the agent
would consume it, its governance model, and how it fits our trust boundary. Grounded on current
Microsoft Learn (verified 2026-09-29).

## What it is

Work IQ is **Microsoft's workplace intelligence layer** that lets agents access and reason over
Microsoft 365 organizational and business data — with **built-in, permission-aware governance**. It
continuously builds a semantic understanding across Microsoft 365 (and external systems like
Dynamics 365 and Power Platform) and packages four capabilities: **Chat, Context, Tools, and
Workspaces**.

It reasons over:

- Email and calendar / meetings
- OneDrive and SharePoint documents
- Microsoft Teams messages
- People and organizational context
- Microsoft Planner plans
- Enterprise search results
- Business/workflow data from Dynamics 365 and Power Platform

## How an agent consumes it (this is the key upgrade)

Work IQ is a **shipping, consumable service — not a server you build**. It exposes three protocols so
you pick what fits your architecture:

| Protocol | Use when | Caller |
| --- | --- | --- |
| **A2A** (Agent-to-Agent) | Another agent delegates a task to Work IQ and gets results back | Another agent |
| **REST** | Your app/backend calls Work IQ programmatically | Your service/orchestrator |
| **MCP** (remote + local) | An LLM client invokes Work IQ as a tool for the user | An LLM-based client |

The **Work IQ MCP** collapses hundreds of Microsoft 365 operations into **~10 generic tools** —
simple verbs (`fetch`, `create`, `update`) where the **resource path** defines what's being acted on
(mail, calendar, files, people, chat, sites). Agents can **discover data structure at runtime**
instead of relying on predefined models. Local MCP is available via the `workiq` CLI:

```json
{
  "workiq": { "type": "stdio", "command": "workiq", "args": ["mcp"] }
}
```

A2A endpoint example: `POST https://workiq.svc.cloud.microsoft/a2a/` (JSON-RPC envelope; `A2A-Version`
header selects v1.0 `SendMessage` vs v0.3; multi-turn via `contextId`).

## Governance model (why it's safe)

- **Microsoft Entra ID delegated authentication only.** Every request runs in the **signed-in user's
  context**; **on-behalf-of (OBO)** is supported; **application-only auth is not supported**.
- **User-scoped access** — the agent only sees what that user is allowed to see or do.
- **Permissions, sensitivity labels, and compliance policies are enforced automatically.**
- A **Rego-based policy engine (Open Policy Agent)** evaluates resource path, request method, user
  identity, and **data content** on every request — a small set of broad permissions replaces
  hundreds of static OAuth scopes, with fine-grained policy on top.
- **Every tool invocation is logged and evaluated** — auditability, usage analytics, rate limiting,
  and real-time compliance.
- **Workspaces** use **SharePoint Embedded** working storage inside the tenant boundary for
  long-running agent state.

Multitenant caveat: in parent/child orgs the access token issuer (`iss`) must match the **user's home
tenant**; register the app as multitenant and sign users in through their home authority, or the
request fails with `400 AuthenticationError`.

## Access and cost

- Work IQ API access is **independent of Microsoft 365 Copilot licensing** and billed via a
  **usage-based model using Copilot Credits**.
- Copilot-licensed users get Work IQ across Copilot experiences; **custom / third-party agents incur
  usage billing**. Users without a Copilot license are billed based on usage.
- Cost is variable and **managed in the Microsoft 365 admin center**.

## How it fits our discharge-transition trust boundary

Keep two lanes clean:

- **Clinical / PHI lane → our own governed MCP tools** (`patient.get`, `notes.get`,
  `protocol.search`, `utilization.history`, `task.create`, `audit.write`) with PHI minimization. This
  is where regulated patient data flows and where our contracts + scopes live.
- **M365 work-context lane → Work IQ** — the surrounding, non-clinical collaboration context a care
  manager legitimately touches (a coordination Teams thread, a discharge-planning meeting summary, an
  SOP in SharePoint), reached **on the user's identity** with labels, DLP, and OPA policy enforced.

Both lanes share the same identity-first rule (Entra / OBO). Work IQ means we **don't build or secure
an M365-context server ourselves** — we consume Microsoft's governed one.

> One-liner: "Work IQ is Microsoft's governed workplace-intelligence layer — a permission-aware
> MCP/A2A/REST service over Microsoft 365 that runs on the user's identity with labels, DLP, and an
> OPA policy engine on every call. Clinical data stays on our MCP tools; Work IQ safely reaches the
> surrounding M365 work context."

## References

- Work IQ overview — https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/work-iq/
- Work IQ API overview — https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/work-iq/api-overview
- Work IQ MCP (Copilot Studio) — https://learn.microsoft.com/en-us/microsoft-copilot-studio/use-work-iq
- Microsoft 365 Copilot extensibility — https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/
- Work IQ licensing — https://aka.ms/WorkIQ/licensing
