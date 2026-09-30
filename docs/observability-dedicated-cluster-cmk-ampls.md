# Dedicated LAW Cluster + CMK + AMPLS — guidance for Kaiser Permanente

> Day-2 observability foundation. Why Foundry changes the logging posture, and how to protect
> request/response telemetry that may contain PHI: **dedicated Log Analytics cluster + customer-
> managed keys (CMK) + Azure Monitor Private Link (AMPLS)**. Led by Lee Schuenemeyer.
>
> Grounded in Microsoft Learn: **Customer-managed keys** (`/azure/azure-monitor/logs/customer-
> managed-keys`), **Log Analytics dedicated clusters** (`/azure/azure-monitor/logs/logs-dedicated-
> clusters`), **Azure Monitor Private Link Scope** (`/azure/azure-monitor/logs/private-link-security`).
> Verify commitment tiers and limits at delivery time.

## Why Foundry changes the logging posture

Before Foundry, LAW/App Insights held mostly **telemetry** (metrics, traces, IDs). With Foundry
agents, App Insights can capture **prompt/response content, retrieved source excerpts, and tool
arguments** — which in a care setting may contain **PHI**. That reclassifies the log store from
"operational telemetry" to "regulated data at rest," which drives three controls:

| Concern | Control |
| --- | --- |
| Encrypt logs with keys KP controls (revoke/rotate) | **Customer-managed keys (CMK)** |
| CMK is only available on… | a **dedicated Log Analytics cluster** |
| Keep ingestion/query off the public internet | **AMPLS** (Azure Monitor Private Link) |

KP context: today KP uses standard (non-dedicated) LAW on **public endpoints**. The move is to a
dedicated cluster with CMK + AMPLS specifically for the Foundry workloads. (Current LAW spend
~$130K/mo already sits well above the dedicated-cluster commitment floor — see cost below.)

## Control 1 — Dedicated Log Analytics cluster

- CMK, Lockbox, availability zones, and double encryption require a **dedicated cluster** — you
  cannot apply CMK to a pay-as-you-go workspace.
- **Pricing is a commitment-tier model of at least 100 GB/day.** Workspaces link to the cluster and
  inherit its capabilities; billing is at the cluster level.
- **Double encryption**: data on a dedicated cluster is encrypted twice — service level (MMK or CMK)
  and infrastructure level (a second algorithm + key).
- Start slow: link only the **Foundry** workspace(s) to the cluster first; migrate other workspaces
  later. KP's stated approach is "start with Foundry, expand after."

## Control 2 — Customer-managed keys (CMK)

- After CMK is set, **new data ingested to linked workspaces is encrypted with your Key Vault key**
  (Key Vault or Managed HSM). You own the key lifecycle and can **revoke access** to make data
  inaccessible.
- The **cluster** holds a **managed identity** (system- or user-assigned) that authenticates to your
  Key Vault via Entra ID; the cluster is the intermediary between Key Vault and the workspaces.
- Key Vault must have **soft-delete + purge protection**; grant the cluster identity key
  get/wrap/unwrap.
- **Hot cache** (last ~14 days / recently queried) is infra-encrypted regardless, but access is
  still governed by CMK state — revoke the key and hot-cache data is deleted and inaccessible.
- CMK protects **at rest**; it is not a substitute for minimizing what you log (see below).

## Control 3 — AMPLS (Azure Monitor Private Link)

- AMPLS binds Azure Monitor resources (the LAW workspace(s) and the Foundry App Insights) to your
  **VNet via a private endpoint**, so **ingestion and query traffic avoid the public internet** —
  closing the "logs on a public endpoint" gap.
- Choose the access mode deliberately: **Private Only** (block public network access to the scoped
  resources) vs **Open**; plan **private DNS** for the Azure Monitor endpoints.
- Ensure the agents/apps emitting telemetry and the analysts querying it are on networks that route
  through the AMPLS private endpoints.

## Don't skip the cheap control: minimize what you log

CMK/AMPLS protect the store; they don't reduce exposure. Pair them with the telemetry discipline
from `docs/rag-guidance-gpt-rag.md` (Pattern 6) and `docs/governance-security-observability.md`:

- **Operational metadata** (IDs, durations, tool names, status codes) — permitted; still minimize.
- **Sensitive content** (prompts, responses, source excerpts, tool args) — **off by default**;
  enable only after need + privacy review + retention + cost review.
- **Prohibited** (tokens, keys, secrets) — never captured; redact before telemetry leaves the process.
- **Pseudonymize actors** (HMAC of identity, key in Key Vault) instead of raw user IDs.

The layered result: minimize sensitive content at the source, then CMK-encrypt what remains, and
keep it all on the private network.

## Cost framing (for the "is this affordable?" question)

- Dedicated cluster = commitment tier (≥100 GB/day). At KP's current volume this is generally a
  **cost-neutral-to-favorable** move vs. pay-as-you-go, because commitment tiers are discounted
  against per-GB ingestion — the reason the earlier cost analysis showed a saving, not a surcharge.
- Model: (commitment-tier price at chosen GB/day) + Key Vault + private endpoints, vs. current
  pay-as-you-go ingestion. Bring the real numbers to the Day-2 session with Lee.

## Sequencing (Day-2 with Lee)

1. Create Key Vault (soft-delete + purge protection); create/import the CMK.
2. Create the dedicated cluster; assign its managed identity; grant it Key Vault access; set CMK.
3. Link the Foundry LAW workspace to the cluster; confirm CMK on new ingestion.
4. Create AMPLS; add the workspace + Foundry App Insights; set access mode; wire private DNS.
5. Validate: ingest a Foundry run, query by `correlationId` over the private path, confirm
   encryption + private-only access; test key revocation in a non-prod scope.

## Workshop mapping

- Extends `Module05` and `observability/` (taxonomy, KQL, dashboards) with the data-protection layer.
- The App Insights we deploy (`appi-…`) becomes the workspace-based resource that lands in the
  CMK-encrypted, AMPLS-scoped LAW — so Foundry traces inherit the posture.

## References (public)

- Customer-managed keys: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/customer-managed-keys
- Dedicated clusters: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-dedicated-clusters
- Azure Monitor Private Link: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/private-link-security
- Encryption at rest / double encryption: https://learn.microsoft.com/en-us/azure/security/fundamentals/encryption-atrest
