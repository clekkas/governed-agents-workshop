# Existing AI Search vs Foundry Capability-Host Search (for Kaiser Permanente)

> Clarifies Joshua's question: teams already run Azure AI Search for RAG; Foundry *also* spins up an
> AI Search per project. Are they the same? Which do you use? This resolves the two instances and
> when each applies. Pairs with `docs/capability-host-reuse-and-cost.md` (reuse + cost).

## There can be two different Search instances in play

| Instance | Who creates it | What it holds | Lifecycle |
| --- | --- | --- | --- |
| **A. Capability-host Search** | Foundry Agent Service (standard setup), per **project** | The **agent's vector stores** (thread/file vector data the runtime manages) | Tied to the project via an **immutable capability connection** — single-tenant to that project |
| **B. Your existing Search** | Your team, independently | Your **application RAG indexes** (protocol docs, etc.), on your own ingestion pipeline | You own it; independent of any Foundry project |

They are **independent Azure resources**. The one Foundry provisions for agent vector stores is not
automatically your app's RAG index, and your existing Search index is not automatically visible to
an agent — you connect it deliberately.

## How they connect (two clean patterns)

1. **Bring your existing Search as the capability host (BYO).** Standard setup lets you pass the
   **resource ID of an existing** AI Search instead of creating a new one — so instance A *is* your
   existing service. Cleanest when you already run a governed Search.
2. **Ground on your existing index via Foundry IQ.** Add your existing index as a `searchIndex`
   **Knowledge Source** on a Foundry IQ Knowledge Base — the agent retrieves from your index
   (keeping your ingestion pipeline) while Foundry IQ handles blending, citations, and permission
   trimming. See `docs/rag-guidance-gpt-rag.md` Pattern 1–2.

## Which do I use?

| Goal | Use |
| --- | --- |
| Store the agent's own vector data (threads/files) | Capability-host Search (A) — required by the runtime |
| Ground answers on your curated protocol/RAG corpus | Your index via **Foundry IQ `searchIndex` source** (B) |
| Avoid a second always-on Search base charge | **Reuse one service** for both — add app indexes alongside the agent's, with capacity headroom + RBAC (see capability-host-reuse-and-cost.md) |
| New build, multiple/enterprise sources | **Foundry IQ** as the one retrieval endpoint (fans out to Blob, searchIndex, SharePoint, Work IQ, Fabric, MCP) |
| Existing single-index pipeline, rollback/compat | **Azure AI Search direct** (you build blending + permission trimming) |

## Cost note (the real question underneath)

Azure AI Search has an **always-on base rate per service**, so the money question is *"do we need a
second Search service?"* — usually **no**: reuse one service for the agent's vector stores **and**
your app's RAG indexes when the SKU has index/replica/partition headroom. Cosmos/Storage are
consumption-priced, so their reuse saves little. Full guidance + the lifecycle caveat:
`docs/capability-host-reuse-and-cost.md`.

## One-slide summary

- Two Search instances *can* exist: the agent's (capability host) and yours (app RAG). They're
  independent unless you connect them.
- Prefer **one Search service** reused for both (cost) **or** BYO your existing Search as the
  capability host — don't reflexively stand up a third.
- Ground on your corpus through **Foundry IQ (`searchIndex` source)**; keep your ingestion pipeline.

## References (public)

- Foundry IQ knowledge sources: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-foundry-iq
- Standard agent setup (BYO Search): https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/standard-agent-setup
- Local: `docs/capability-host-reuse-and-cost.md`, `docs/rag-guidance-gpt-rag.md`
