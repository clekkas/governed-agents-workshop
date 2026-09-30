# Capability-Host Reuse and Cost — guidance for Kaiser Permanente

> Answers the workshop's most-raised question: *when Foundry provisions Azure AI Search,
> Cosmos DB, and Storage for an agent project, can our app teams reuse those, or must they
> stand up their own?* — and what to tell app teams about cost.
>
> Grounded in Microsoft Learn: **Set up standard agent resources for Foundry Agent Service**
> (`/azure/foundry/agents/concepts/standard-agent-setup`) and **Configure agent capability
> settings** (`/azure/foundry/agents/how-to/configure-capability-settings`). Verify RU/container
> specifics against Learn at delivery time — the service evolves.

## The one-line answer

Foundry Agent Service **standard setup is Bring-Your-Own (BYO)**: at project/account creation you
can **create new resources or pass the resource IDs of existing ones**. So reuse is not only
allowed, it is a first-class path — but reuse **couples the resource's lifecycle to the Foundry
project** (capability-settings connections are immutable and can't be changed without deleting and
recreating the project). Reuse to save cost **only** with logical isolation, RBAC, capacity
headroom, and eyes-open lifecycle coupling.

## What Foundry actually provisions (standard setup)

Standard setup uses **customer-managed, single-tenant** resources in your subscription (this is
Matt's "single-tenant per project" point — confirmed). Three data stores plus Key Vault:

| Resource | What the agent stores in it | Footprint it creates |
| --- | --- | --- |
| **Azure AI Search** (BYO Search) | Vector stores the agent creates | Indexes for agent vector stores |
| **Azure Cosmos DB for NoSQL** (BYO Thread Storage) | Messages, conversation history, agent metadata | Database `enterprise_memory`; New runtime uses containers `agent-definitions-v1` + `run-state-v1`; needs **≥ 3000 RU/s** total (5 containers × 1000 RU/s in standard setup; Provisioned or Serverless) |
| **Azure Storage** (BYO File Storage) | Uploaded files + intermediate data (chunks, embeddings) | 2 blob containers: `<workspaceId>-azureml-blobstore`, `<workspaceId>-azureml-agent` |
| **Azure Key Vault** | Secrets/connection strings for the agent infra | — |

**Project-level data isolation is on by default** — dedicated containers per project. So sharing a
*service/account* across an app and its agent does **not** break the isolation the agent relies on;
the agent keeps its own containers/indexes.

## The two reuse directions

1. **App has existing resources → BYO into Foundry.** Point the project's capability settings at an
   existing Search/Cosmos/Storage by resource ID. Cleanest when the team already runs a governed
   Search. This is the supported, documented path.
2. **Foundry provisioned resources → app reuses them for its own workloads.** The stores are your
   own Azure resources, so the app *can* add its own index/database/containers alongside the
   agent's — with the guardrails below.

## Per-resource guidance (what to tell app teams)

| Resource | Reuse verdict | Do | Watch |
| --- | --- | --- | --- |
| **Azure AI Search** | ✅ Best cost win | Host the app's own RAG indexes on the **same** Search service to avoid a **second always-on base charge**. Isolate per index + RBAC (`Search Index Data Reader` for app query path). | SKU capacity: index count, replicas/partitions, and noisy-neighbor between agent vector stores and app indexes. If the app needs its own SLA/scaling, use dedicated. |
| **Cosmos DB** | ✅ Allowed, small $ win | Put app data in a **separate database/containers** (never the agent's `enterprise_memory`). | ≥ 3000 RU/s floor is for the agent; app RU is additive. Serverless vs provisioned; RU contention. Consumption model means little base-cost saving. |
| **Storage** | ✅ Allowed, small $ win | App blobs in **separate containers** (not the `azureml-*` ones). | Consumption-priced, so sharing saves little; benefit is fewer resources, not lower cost. |

**Where the real cost saving is: Azure AI Search.** Cosmos and Storage are consumption-priced, so
sharing them mostly reduces resource sprawl, not spend. Search carries an always-on base rate per
service, so reusing one Search service for both the agent's vector stores and the app's RAG indexes
is the material cost-optimization move — *if* the SKU has capacity headroom.

## The lifecycle-coupling caveat (say this out loud)

Capability-settings connections are **immutable while in use**, and you **cannot update capability
settings on an existing project** — changing which resources a project uses requires **deleting and
recreating the project**. Implication for reuse:

- Sharing the **service/account** (app adds its own separate index/db/container) is low-risk — the
  app's objects are independent of the agent's connection.
- **Do not** build the app on the agent's *own* containers/indexes (`enterprise_memory`,
  `agent-definitions-v1`, `run-state-v1`, `<workspaceId>-azureml-*`) — those are managed by the
  runtime and tied to the project's immutable connection.

## Decision rule (the slide)

Reuse the project's capability-host resource for app workloads **only when all are true**:
1. **Capacity headroom** exists (esp. Search index/replica/partition limits).
2. **Logical isolation** is enforced (separate index / database / container).
3. **RBAC** scopes the app's access (least privilege, distinct from the project managed identity's
   `Search Index Data Contributor` / `Cosmos DB Built-in Data Contributor` / `Storage Blob Data
   Owner`).
4. The team **accepts lifecycle coupling** to the Foundry project.

Otherwise provision a dedicated resource. When an app needs independent SLA, scaling, compliance
scope, or lifecycle, dedicated wins over the cost saving.

## RBAC note (roles were renamed)

Foundry RBAC roles were renamed: **Foundry User / Foundry Owner / Foundry Account Owner / Foundry
Project Manager** (previously Azure AI User / Owner / Account Owner / Project Manager). Role IDs and
permissions are unchanged; you may still see old names mid-rollout. Developers who create/edit
agents need **Foundry User** on the project.

## Workshop mapping

- Our deployed infra (`infra/terraform/`) uses one AI Search (`srch-…`) and a Storage account with a
  RAG container — a concrete instance of the "one Search, app + agent indexes" pattern to show live.
- Tie this to `docs/rag-guidance-gpt-rag.md` Pattern 1 (Foundry IQ vs AI Search direct) and the
  `searchIndex` source kind (bring your existing index) for the existing-vs-Foundry Search question.

## References (public)

- Standard agent setup: `/azure/foundry/agents/concepts/standard-agent-setup`
- Configure agent capability settings: `/azure/foundry/agents/how-to/configure-capability-settings`
- Foundry IQ knowledge sources: `/azure/foundry/agents/concepts/what-is-foundry-iq`
