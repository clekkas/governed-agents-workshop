# RAG Guidance for Kaiser Permanente — patterns from the Azure GPT-RAG accelerator

Source reviewed: **Azure GPT-RAG Solution Accelerator** (`https://azure.github.io/GPT-RAG/`) —
an enterprise-grade, Microsoft-maintained reference for building agentic RAG assistants on
Microsoft Foundry. This document synthesizes its best practices into guidance KP can adopt, and
maps each pattern to this workshop's implementation. It is not a copy of the accelerator; treat
the accelerator as the authoritative source and this as an adoption guide.

## The one-line takeaway

Ground answers through **one managed retrieval endpoint (Foundry IQ Knowledge Base)** that fans
out to trusted sources with **permission trimming**, keep the model on top of **retrieved evidence
with citations**, and **measure retrieval quality before tuning prompts**. Governance, access, and
provenance are part of the RAG design, not an afterthought.

## Pattern 1 — Choose the grounding approach deliberately

The accelerator supports two backends; pick one per request (you cannot mix in a single call):

| Approach | Use when | Notes |
| --- | --- | --- |
| **A. Foundry IQ Knowledge Base** (default, recommended) | New builds; you need multiple/enterprise sources | One endpoint fans out to Blob, Azure AI Search index, Work IQ, Fabric, SharePoint (live or indexed), OneLake, Web, MCP — with permission trimming built in. |
| **B. Azure AI Search direct** | Existing single-index pipeline; rollback/compat path | You build multi-source blending and permission trimming yourself. |

KP guidance: **start on Approach A (Foundry IQ)** so Microsoft 365 (Work IQ), SharePoint, and
Fabric can be added later without re-architecting. Keep Approach B in mind as the rollback path.

Workshop mapping: our `docs/solution-architecture-overview.md` already targets Foundry IQ / Azure
AI Search as the knowledge backing; the local `KnowledgeBase` (`agent-service/.../knowledge.py`) is
the stand-in that speaks the same retrieve-then-cite contract.

## Pattern 2 — One Knowledge Base, many Knowledge Sources

A Knowledge Base points to one or more Knowledge Sources, each with its own `kind`, security
model, and cost profile. Foundry IQ blends and permission-trims results in a single call.

| Source kind | Grounds on |
| --- | --- |
| `azureBlob` | Files in a Blob container (default for new deployments) |
| `searchIndex` | An existing Azure AI Search index (keep your ingestion pipeline) |
| `workIQ` | Microsoft 365 context for the signed-in user (needs M365 Copilot licensing) |
| `fabricOntology` / `fabricDataAgent` | Fabric business ontology / curated Data Agent |
| `remoteSharePoint` / `indexedSharePoint` | SharePoint live (per-user ACL) or indexed (app-only) |
| `indexedOneLake` | Fabric OneLake lakehouse content |
| `web` | Public web, scoped by allow/block lists |
| `mcpServer` | Live tool-backed data from a trusted remote MCP server |

KP guidance: enable the **minimum** set of sources the use case needs; each source is a separate
security and cost decision. For the discharge-transition use case, start with approved protocol
documents (Blob/searchIndex); add SharePoint/Work IQ only with governance sign-off.

## Pattern 3 — Retrieval-then-ground, always cite

The orchestrator never sends the raw question to the model. It **retrieves** grounding content
first, includes it in the prompt, and the answer is built on that material so it **cites real
sources instead of guessing**. Missing or conflicting evidence should surface, not be papered over.

Workshop mapping: the Evidence Retrieval Agent builds an **evidence packet** with claim-level
citations; missing specialty protocol drives **escalation** rather than a fabricated answer.

## Pattern 4 — Document-level security via delegated identity (OBO)

For per-user grounding, the accelerator forwards the **user's** delegated token (On-Behalf-Of
exchange) so retrieval is permission-trimmed to what that user may see:

- The UI signs the user in and sends a token for the orchestrator API.
- The orchestrator validates it and performs an **OBO exchange** to get a token whose audience is
  the search/knowledge service.
- Azure AI Search enforces document-level ACL/RBAC using
  `x-ms-query-source-authorization` (the user token), separate from the calling service identity.

Critical rule: **keep the caller (user) identity separate from the service identity.** A
service-identity-only test is not proof that different end users are isolated. Always test with
allowed **and denied** users.

KP guidance: for any source with per-user permissions (SharePoint, Work IQ), require OBO and test
denied users. `ALLOW_ANONYMOUS` must not silently fall back to local-only answers for
permission-sensitive sources.

## Pattern 5 — Govern the source before you connect it

Run this checklist before wiring any grounding source (indexed or queried at request time):

1. **Provenance** — system of record, data owner, ingestion/query path, refresh cadence, permission model.
2. **Right-to-use** — record that the org is authorized to process the source for these users and purpose.
3. **Classify** — apply KP's classification for personal/confidential/regulated content.
4. **Minimize scope** — only the sites, containers, indexes, fields, date ranges, and tools the use case needs.
5. **Retention & deletion** — how source data, indexes, history, caches, and backups are removed; test it.
6. **Review access** — source permissions + managed identity + delegated access + retrieval trimming; test allowed/denied.
7. **Review data movement** — region, service, public-internet, and cross-boundary behavior per source.

KP guidance: this maps to `governance/agent-governance-plan.md`. Do not connect a real KP source in
the workshop; use synthetic data and treat this checklist as the pilot gate.

## Pattern 6 — Treat telemetry as three data classes

| Class | Examples | Posture |
| --- | --- | --- |
| Operational metadata | event/correlation IDs, service/version, status/reason codes, durations, tool names, source kinds, opaque source refs | Permitted; still classify/minimize (identifiers can be sensitive) |
| Sensitive content | prompts, responses, source excerpts, tool arguments/results | **Off by default**; enable only after need + privacy review + access design + retention + cost review |
| Prohibited data | tokens, API keys, auth headers, cookies, connection strings, secrets | **Never** capture/export; redact before telemetry leaves the process; fail closed |

Additional accelerator practices worth adopting:
- **Pseudonymize actors** (HMAC-SHA256 of the identity, key in Key Vault, rotate the key) instead of
  logging raw user identifiers.
- **Redaction metadata** lists *which* fields were omitted, never the omitted values, and a redaction
  flag does not prove all sensitive data was found — use allowlisted fields and bounded enums.
- **A citation does not prove correctness; a recorded event does not prove correct behavior;
  missing telemetry does not prove an action did not occur.**

Workshop mapping: our observability plan already uses a bounded custom-event taxonomy and
correlation IDs; adopt the actor-pseudonymization and redaction-metadata rules when wiring App
Insights for real data.

## Pattern 7 — Measure retrieval before you tune prompts

The accelerator's retrieval-optimization method is the highest-value RAG-dev practice for a team:

1. **Freeze the experiment** — fixed corpus snapshot, fixed questions, fixed identity/permissions,
   one strategy, one model/prompt/temperature, one document limit, comparable load.
2. **Split questions** into a **tuning set** and a **held-out set**; only open held-out after picking a candidate.
3. **Build qrels** (relevance judgments) with a shared rubric:

   | Label | Meaning |
   | --- | --- |
   | 4 | Directly and fully answers |
   | 3 | Strongly relevant |
   | 2 | Partially relevant |
   | 1 | Weakly related |
   | 0 | Not relevant |

4. **Measure each backend on its own identifiers/qrels** — never compare raw backend scores; compare
   normalized ranking + answer-quality metrics.
5. **Treat a completed run as immutable**; record corpus/manifest versions and image digests for reproducibility.
6. Remember: **config changes require an orchestrator restart** (settings are cached at startup).

Workshop mapping: implemented locally in `agent-service/eval/` — `qrels.jsonl` (labeled judgments
over our synthetic corpus) and `evaluate_retrieval.py` (precision@k, recall@k, MRR). This is the
"measure retrieval before tuning" pattern in miniature, ready to graduate to the accelerator's
full method against Foundry IQ.

## Pattern 8 — Modular runtime services

The accelerator separates concerns into services KP can mirror:

| Service | Responsibility |
| --- | --- |
| Orchestrator | Agentic workflow (Microsoft Agent Framework) + Foundry IQ retrieval |
| Data Ingestion | Extract, chunk, index enterprise data for retrieval |
| MCP Server | Optional tool hosting / business-logic integration |
| Web UI | Chat interface with streaming |

It is **Zero-Trust and IaC-first**: network isolation, private endpoints, Key Vault, managed
identity, and Bicep/Terraform from the ground up.

Workshop mapping: our repo mirrors this shape — `agent-service/` (orchestrator + agents),
`mcp-server/` (tool contracts), `app/` (UI), `backend/` (gateway), `infra/terraform/` (IaC).
Ingestion is represented by `data/rag-docs/` + the local `KnowledgeBase`.

## What to say to KP in the workshop

- Use **Foundry IQ** as the one governed retrieval endpoint; add sources incrementally with sign-off.
- **Permission-trim with delegated identity (OBO)**; never rely on a service-identity test for user isolation.
- **Cite everything; escalate on missing evidence.**
- **Measure retrieval with qrels** before touching prompts or models.
- **Govern the source and the telemetry** — provenance, minimization, retention, and the three data classes.

## References (public)

- GPT-RAG accelerator: https://azure.github.io/GPT-RAG/
- Grounding sources overview: https://azure.github.io/GPT-RAG/howto_grounding_overview/
- Governance and responsible operation: https://azure.github.io/GPT-RAG/governance_overview/
- Retrieval optimization: https://azure.github.io/GPT-RAG/howto_retrieval_optimization/
- Authentication and document-level security: https://azure.github.io/GPT-RAG/howto_authentication/
- Microsoft Learn: What is Foundry IQ (`/azure/foundry/agents/concepts/what-is-foundry-iq`)
