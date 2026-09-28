# Mode 1 — Pre-Workshop Validation Runbook

Goal: build, deploy, and validate the **complete** solution on Azure + Microsoft Foundry, then
freeze it as a known-good git tag so Mode 2 delivery is deterministic.

Run this **before** the workshop, with Scout coordinating and a human approving cloud actions.
Nothing here should run on stage during the event.

## Prerequisites

- Azure subscription with rights to create the resources below.
- Microsoft Foundry project access (`Foundry Project Manager` at project scope to deploy agents).
- Azure CLI (`az`) and Azure Developer CLI (`azd`) signed in: `az login`, `azd auth login`.
- Docker Desktop (for hosted-agent container builds) or use source-based deploy.
- Node.js 20+, Python 3.11+, PowerShell 7+.
- Synthetic data only. No PHI. No secrets in the repo.

## Target resources (workshop-scale)

| Resource | Purpose |
| --- | --- |
| Microsoft Foundry project + model deployment | Hosted agent + specialist agents. |
| Azure Container Registry (BYO) | Hosted-agent image (or source-based deploy). |
| Azure AI Search (Foundry IQ knowledge base) | RAG over `data/rag-docs/`. |
| Application Insights + Log Analytics | Traces, custom events, dashboards. |
| Azure Container Apps or App Service | Backend API + static UI. |
| Key Vault | Secrets/connection strings. |
| Microsoft Entra ID | Agent identity + RBAC. |

## Phase 0 — Local full-solution validation

Prove everything works locally before touching cloud.

```powershell
./scripts/validate-solution.ps1
```

This runs repo validation, the frontend production build, and a backend smoke test
(`/api/health`, `/api/v1/cases`, an invoke, and the P0310 escalate case).

Gate: all green, or stop and fix.

## Phase 1 — Provision Azure + Foundry

1. Create/confirm the Foundry project and deploy an agent-compatible model.
2. Provision Search, App Insights, Log Analytics, ACR, Key Vault (Bicep/azd or portal).
3. Connect Application Insights to the Foundry project (enables server-side tracing).
4. Create the Foundry IQ knowledge base over the synthetic protocol docs.

Delegate the implementation to Copilot via backlog item WI-08 (scaffold) plus infra work,
but **the human runs the actual deployment commands** and approves each cloud step.

## Phase 2 — Deploy the solution

1. Deploy/host the specialist agents (hosted agent fulfilling the `/api/v1/agent/invoke` contract).
2. Deploy the backend API + built UI to Container Apps/App Service.
3. Wire the backend to the hosted agent endpoint (swap the local orchestrator for the Foundry path).
4. Confirm identity/RBAC and Key Vault wiring; no secrets on disk.

## Phase 3 — Cloud smoke test + evaluation

1. Hit the deployed `/api/health` and `/api/v1/agent/invoke` for each synthetic case.
2. Confirm traces appear in Application Insights; run a KQL sample from `fabric/kql/`.
3. Run the evaluation harness (WI-07) against the deployed URL:
   - golden cases pass (cited, escalates when evidence missing),
   - adversarial risk-score-override case **fails closed** (agent refuses).
4. Confirm the hard safety boundary holds end to end.

Gate: all pass, or roll back and fix.

## Phase 4 — Tag and commit

Only after Phases 0–3 pass.

```powershell
# Ensure working tree is clean and validation is green
git status
./scripts/validate-solution.ps1

# Commit any final config
git add -A
git commit -m "Mode 1: validated full solution on Azure + Foundry"

# Cut the validated release tag (date-stamped, immutable)
$stamp = Get-Date -Format 'yyyyMMdd'
git tag -a "solution-validated-$stamp" -m "Full solution validated on Azure + Foundry $stamp"

# Also cut/refresh the local baseline tag
git tag -a "solution-local-$stamp" -m "Full solution validated locally $stamp"

# Push commit + tags
git push
git push --tags
```

## Phase 5 — Cut chapter checkpoints for Mode 2

Create the chapter tags in order (each after its work item is done and validated):

```powershell
# Example — repeat per chapter tag from docs/workshop-modes.md
./scripts/validate-solution.ps1
git tag -a "chapter-02-mcp-validate" -m "Chapter 2 checkpoint: MCP tool validation"
git push --tags
```

## Rollback

- Revert to the last good release: `git checkout solution-validated-<date>`.
- Tear down cloud resources by resource group when validation is complete and captured.
- Keep screenshots/exports of successful cloud runs as Mode 2 fallback evidence.

## Exit criteria (Mode 1 complete)

- [ ] Local full-solution validation passes.
- [ ] Solution deployed to Azure + Foundry.
- [ ] Cloud smoke test + evaluation pass; adversarial case fails closed.
- [ ] `solution-validated-<date>` tag pushed.
- [ ] All chapter checkpoint tags cut and pushed.
- [ ] Fallback screenshots captured.
