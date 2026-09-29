# Infrastructure — Azure + Microsoft Foundry (Terraform)

Deploys the Discharge Transition Exception Coordinator to Azure and Microsoft Foundry as
infrastructure-as-code. Aimed at the DevOps / infrastructure track of the workshop.

Synthetic data only. This is a reference deployment, not a production clinical system.

## Execution model — staged hybrid

This infra follows a **local → GitHub Actions** rollout (see `DEPLOYMENT.md` for the full guide):

| Stage | Runs where | State | Auth |
| --- | --- | --- | --- |
| 1. Prove it | Local `terraform apply` (`scripts/deploy.ps1`) | local file | `az login` |
| 2. Bootstrap | `scripts/bootstrap-remote-state.ps1` + `scripts/setup-github-oidc.ps1` | → Azure blob | `az login` |
| 3. Steady state | `.github/workflows/terraform-{plan,apply}.yml` | remote | OIDC (keyless) |

Stage 1 uses local state for a friction-free first run. Stage 2 (one-time) creates the remote state
backend and the GitHub→Azure OIDC federation. Stage 3 runs `plan` on PRs and a human-gated `apply`
on merge — no credentials stored.

## What gets deployed

```
Resource group
├── Log Analytics workspace + Application Insights      (observability: LAW / App Insights)
├── Azure Container Registry (admin disabled)           (BYO registry theme)
├── Key Vault (RBAC authorization)                       (secrets)
├── Storage account + container                          (RAG source docs)
├── Azure AI Search (system-assigned identity)           (Foundry IQ / RAG backing)
├── User-assigned managed identity + RBAC                (least-privilege access)
├── Container Apps environment + app                     (backend API + built UI, one image)
│     └── agent sidecar container                        (Python multi-agent service on :8081)
└── Microsoft Foundry (AI Services account)
    ├── Foundry project                                  (agent runtime)
    ├── Model deployment (gpt-4o-mini by default)
    └── Application Insights connection                  (server-side agent tracing)
```

Governance/access wired in: the app runs as a user-assigned managed identity with least-privilege
role assignments (AcrPull, Key Vault Secrets User, Storage Blob Data Reader, Search Index Data
Reader, Cognitive Services User). No admin keys; Search uses managed identity; secrets stay in
Key Vault.

## Prerequisites

- Azure CLI (`az`) logged in to the target subscription.
- Terraform >= 1.6.
- Permission to create the resources above and to assign roles (Owner or User Access Administrator
  on the target scope).
- Registered providers: `Microsoft.CognitiveServices`, `Microsoft.App`, `Microsoft.Search`,
  `Microsoft.OperationalInsights`, `Microsoft.ContainerRegistry`, `Microsoft.KeyVault`,
  `Microsoft.Storage`.

## Quick start

```powershell
cd infra\scripts
.\preflight.ps1          # verify tooling + login + providers
.\deploy.ps1             # provision, build/push image, roll real image
```

`deploy.ps1` runs three phases:
1. `terraform init` + `apply` (provisions infra with public placeholder images).
2. `az acr build` x2 (builds the repo `Dockerfile` for the app and `agent-service/Dockerfile`
   for the agent sidecar, pushing both to the new ACR).
3. `terraform apply -var container_image=<app> -var container_image_agent=<agent>` (rolls the
   real images).

The Container App runs two containers: the backend+UI (`:8080`, public ingress) and the Python
agent service (`:8081`, sidecar). The backend delegates `/api/v1/agent/invoke` to the agent over
`localhost:8081` (via `AGENT_SERVICE_URL`), and the agent calls the Foundry model using the app's
managed identity.

When it finishes it prints the app URL, Foundry endpoint, model deployment, and search endpoint.

## Manual Terraform (alternative)

```powershell
cd infra\terraform
copy terraform.tfvars.example terraform.tfvars   # edit as needed
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

Then build/push the image and re-apply with the real image reference:

```powershell
$acr = terraform output -raw acr_name
$login = terraform output -raw acr_login_server
az acr build --registry $acr --image discharge-transition:latest --file ..\..\Dockerfile ..\..
terraform apply -var "container_image=$login/discharge-transition:latest"
```

## Teardown

```powershell
cd infra\scripts
.\destroy.ps1
```

## Notes and adjustables

- **Model / region / capacity**: set in `terraform.tfvars` (`model_name`, `location`,
  `model_sku`, `model_capacity`). Confirm the model + SKU are available in your region and you
  have quota.
- **Foundry API versions**: `foundry.tf` uses `azapi` for the project and the App Insights
  connection with a preview API version. Bump the API version if the platform has moved.
- **Remote state**: uncomment and configure the `backend "azurerm"` block in `versions.tf` for
  shared state.
- **Private networking**: this workshop deployment uses public endpoints for simplicity. For a
  hardened variant, add private endpoints, disable public network access, and place the container
  app behind an internal environment + Front Door/APIM.
- **The app today** serves the local orchestrator stub. Wire it to the Foundry hosted agent by
  consuming `AZURE_AI_PROJECT_ENDPOINT` and `FOUNDRY_MODEL_DEPLOYMENT` (already injected as env
  vars) in a follow-up; the `/api/v1/agent/invoke` contract stays the same.
