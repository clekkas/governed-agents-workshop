# SharePoint / Office 365 Docs as a RAG Source (for Kaiser Permanente)

> Matt's ask: two KP teams want to take **SharePoint objects — PDFs, PowerPoint, Word, Excel** —
> and **tokenize/vectorize** them so an agent can use them as a RAG source. This walks the two
> supported patterns, the ingest pipeline, ACL/identity, licensing, and how to choose.
>
> Grounded in Microsoft Learn: **SharePoint tool for Foundry Agent Service**
> (`/azure/foundry/agents/how-to/tools/sharepoint`), **Foundry IQ knowledge sources**
> (`/azure/foundry/agents/concepts/what-is-foundry-iq`), **Azure AI Search integrated
> vectorization** (`/azure/search/vector-search-integrated-vectorization`), and **Document
> Intelligence** (`/azure/ai-services/document-intelligence/`). Verify preview status at delivery.

## Two patterns — pick per use case

| | **A. Live SharePoint tool** (Copilot Retrieval API) | **B. Indexed pipeline** (you tokenize → Azure AI Search) |
| --- | --- | --- |
| How it grounds | Foundry SharePoint tool retrieves from the site/folder at query time | You extract, chunk, embed, and index the docs; agent retrieves from your index via Foundry IQ |
| Identity / ACL | **Per-user OBO** — SharePoint permissions applied every request | **App-only** — you must carry/enforce ACLs yourself (or restrict to non-sensitive corpora) |
| Who tokenizes | Microsoft (managed) — **no pipeline to build** | **You** — full control of chunking, metadata, embeddings |
| Licensing | **M365 Copilot license or pay-as-you-go** retrieval | Azure AI Search + embedding model cost only |
| Constraints | Same Entra tenant; user identity only (no service principal); **one SharePoint tool per agent**; not available when published to Teams; preview | You own refresh, ACL trimming, and index lifecycle |
| Best when | Per-user access must be honored automatically; you want zero ingestion code | You need custom chunking/metadata, non-Copilot-licensed access, or corpus you already govern |

KP guidance: if the two use cases need **per-user permission trimming** and the org has (or will buy)
M365 Copilot / PAYG retrieval, **start with Pattern A** — it honors SharePoint ACLs with no pipeline.
Choose **Pattern B** when you need control over tokenization/metadata, or the corpus is broadly
readable (e.g. approved clinical protocols) and you want a cost-predictable indexed store.

## Pattern A — Live SharePoint tool (fastest, ACL-honoring)

1. **License**: developers + end users have an M365 Copilot license, or enable the pay-as-you-go
   retrieval model.
2. **RBAC**: `Foundry User` on the project; each user has at least `READ` on the SharePoint site.
3. **Same tenant**: SharePoint site and Foundry project in the same Entra tenant (no cross-tenant).
4. **Connect**: create a SharePoint project connection (`SHAREPOINT_PROJECT_CONNECTION_ID`); point at
   the site/folder (e.g. `contoso.sharepoint.com/sites/policies`).
5. **Run as the user**: the tool uses **delegated (OBO) identity** — run the agent with the signed-in
   user's token so SharePoint applies that user's site/folder/document permissions.
6. **Limits to plan for**: one SharePoint tool per agent; not available when the agent is published to
   Teams; start with a small, simple folder structure.

Result: the agent retrieves only what **that user** may see — the permission-trimming rule from
`docs/rag-guidance-gpt-rag.md` Pattern 4, enforced by Microsoft.

## Pattern B — Indexed pipeline (tokenize → vectorize → ground)

This is the "tokenize the PDFs/PPT/Word/Excel" path Matt described. Five steps:

1. **Extract (crack the binaries).** Office formats (Word/PPT/Excel) and digital PDFs: use Azure AI
   Search's built-in document cracking. Scanned/image PDFs or complex layouts/tables: pre-process
   with **Azure AI Document Intelligence** (layout/OCR) to get clean text + structure.
2. **Chunk.** Split into passages with overlap; preserve section/heading context. Keep chunks small
   enough for precise citations (the "recover a precise claim" test in
   `docs/rag-development-patterns.md`).
3. **Embed (vectorize).** Generate vectors with an embedding model. **Integrated vectorization** in
   Azure AI Search can run chunking + embedding as an indexer skillset, so ingestion is repeatable
   and refreshable rather than a one-off script.
4. **Index.** Write vectors + text + **metadata** (source, SharePoint URL, owner, effective date,
   sensitivity, citation URI, and — if you enforce security — ACL/group claims) into an Azure AI
   Search index.
5. **Ground.** Expose the index to the agent as a Foundry IQ **`searchIndex`** (or `indexedSharePoint`)
   knowledge source; the agent retrieves, builds an evidence packet, and cites. Missing/conflicting
   evidence → escalate, never guess.

### ACL/security for Pattern B (say this out loud)

Indexed/app-only ingestion **does not** automatically honor SharePoint per-user permissions. Options,
in order of safety:
- **Restrict the corpus** to broadly-readable, approved content (e.g. clinical protocols) — simplest.
- **Carry ACLs into the index** (group/security claims per document) and **security-trim at query
  time** with the user's identity — more work, honors permissions.
- If neither fits and per-user trimming is required → use **Pattern A** instead.

Test allowed **and** denied users; a service-identity test does not prove user isolation.

## Governance gate (both patterns)

Run the source-governance checklist before connecting anything (`docs/rag-guidance-gpt-rag.md`
Pattern 5): provenance, right-to-use, classification, scope minimization, retention/deletion, review
access (allowed + denied), and data-movement review. Do **not** connect a real KP SharePoint site in
the workshop — use synthetic docs and treat this as the pilot gate.

## Decision one-liner

Need per-user ACLs honored automatically and have Copilot/PAYG licensing → **Pattern A (live tool)**.
Need custom tokenization/metadata, cost-predictable indexing, or a broadly-readable corpus →
**Pattern B (indexed)**. Either way: cite everything, escalate on missing evidence, govern the source.

## Workshop mapping

- Our `data/rag-docs/` synthetic corpus + local `KnowledgeBase` stands in for the indexed pipeline;
  the retrieval harness in `agent-service/eval/` is the "measure retrieval before tuning" step.
- Demo: show Pattern A conceptually (OBO trimming), then run Pattern B end-to-end on a synthetic
  Office doc (crack → chunk → embed → index → cited answer).

## References (public)

- SharePoint tool: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/sharepoint
- Copilot Retrieval API: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api-reference/retrieval-api-overview
- Foundry IQ knowledge sources: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-foundry-iq
- Integrated vectorization: https://learn.microsoft.com/en-us/azure/search/vector-search-integrated-vectorization
- Document Intelligence: https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview
