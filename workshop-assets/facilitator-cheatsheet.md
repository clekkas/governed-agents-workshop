# Facilitator Cheat-Sheet — KP attendees → who wants what → which brief answers it

> Fast reference for the on-site Microsoft team (Shivang, David, Eran, Chris). Derived from the 9/29
> planning call. Use it to steer answers to the right person and open the right doc live.

## Attendees & what each one is really asking for

| Person | Role | What they want | Lead with | Backup brief |
| --- | --- | --- | --- | --- |
| **Sarita Krishnakumar** | Program/product lead (Foundry enablement) | Adoption, **cost not duplicated**, secure MCP, content-safety confidence, agenda coverage | Cost + reuse story; secure-MCP standard | `capability-host-reuse-and-cost.md`, `securing-mcp-servers.md`, `healthcare-content-safety.md` |
| **Matt Heitzenroder** | Platform architect (sharp, SDLC lens) | **Capability-host reuse + cost** to advise app teams; **hosted-vs-prompt tipping factor**; SharePoint/O365 RAG | Capability-host reuse; agent-type decision | `capability-host-reuse-and-cost.md`, `agent-type-decision.md`, `sharepoint-o365-rag-ingest.md` |
| **Joshua Viray** | Platform engineer (hands-on RAG, cautious on ops) | **Existing vs Foundry Search**; verify current RAG pattern; SRE-agent caution | Existing-vs-Foundry Search; RAG patterns | `existing-vs-foundry-search.md`, `rag-guidance-gpt-rag.md` |
| **Lee Schuenemeyer** | MSFT SE — LAW/observability (Day 2) | Dedicated cluster + CMK + AMPLS for PHI logs; cost | Day-2 observability posture | `observability-dedicated-cluster-cmk-ampls.md` |

## Question → brief lookup (open this doc when you hear…)

| If they ask… | Open |
| --- | --- |
| "Can our app teams reuse the Search/Cosmos/Storage Foundry creates, or pay for their own?" | `docs/capability-host-reuse-and-cost.md` |
| "How do we secure the MCP server? What's the standard?" | `docs/securing-mcp-servers.md` |
| "Is the Search Foundry spins up the same as our existing one?" | `docs/existing-vs-foundry-search.md` |
| "When do we use a hosted agent vs a prompt agent vs our own code?" | `docs/agent-type-decision.md` |
| "The content filter blocks legitimate medical questions (Tylenol)." | `docs/healthcare-content-safety.md` |
| "We want to RAG over SharePoint PDFs/PPT/Word/Excel." | `docs/sharepoint-o365-rag-ingest.md` |
| "Foundry logs may hold PHI — how do we protect them?" | `docs/observability-dedicated-cluster-cmk-ampls.md` |
| "What are the RAG best practices / how do we measure retrieval?" | `docs/rag-guidance-gpt-rag.md`, `docs/rag-development-patterns.md` |
| "What's the governance/RBAC model?" | `docs/governance-security-observability.md`, `governance/` |

## The three highest-value answers (memorize these)

1. **Capability-host reuse (Sarita/Matt, "critical"):** Standard setup is **BYO** — reuse existing or
   let Foundry provision. The cost win is **Azure AI Search** (one always-on service for both agent
   vector stores and app RAG indexes, with capacity headroom + RBAC). Cosmos/Storage are
   consumption-priced (little saving). **Caveat:** capability connections are immutable — build on
   *separate* indexes/DBs/containers, never the agent's own; changing a project's resources means
   recreating the project.
2. **Secure MCP (Sarita, "core question"):** six layers — private network + dedicated MCP subnet;
   identity-based auth via project connections (managed/agentic identity; user-Entra-token for
   per-user data; custom-keys last); least-privilege tool contracts + RBAC; **Toolbox** as one
   governed endpoint; human approval on write tools; always-on audit.
3. **Hosted vs prompt (Matt, "tipping factor"):** default to **prompt agent**; graduate to **hosted
   agent** the moment you need custom orchestration, multi-agent handoffs, an existing framework, or
   your own code — which is exactly why the discharge use case is hosted.

## Reordered agenda reminder (per 9/29)

Day 1 AM leads with **MCP + Toolboxes → Foundry IQ/RAG**; PM = **Guardrails → Hosted Agents (demoted)**.
Day 2 = **LAW/App Insights (+ CMK/AMPLS)** → **HITL/DTS** → **governance Q&A + roadmap**.
See `workshop-assets/agenda-2-day.md` and `run-of-show.md`.

## Out of scope / futures (set expectations)

- **BYO Registry** — Matt can't pre-stage; we show a sample end-to-end demo only.
- **BYO AKS for hosted agents** — roadmap/futures (product-team session); not GA.
- **SRE agent** — Joshua interested but "down the line" (Nexus OS integration unknowns).
