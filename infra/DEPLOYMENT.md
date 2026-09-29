# Deployment — staged hybrid (local now, GitHub Actions final)

How the Discharge Transition Exception Coordinator infrastructure goes from a local proof to a
governed GitHub Actions pipeline. Synthetic data only; coordinate with the workshop owner before any
cloud deployment.

The model, in three stages:

| Stage | Runs where | State | Auth | Purpose |
| --- | --- | --- | --- | --- |
| 1. Prove it | Local `terraform apply` | local file | `az login` | Confirm the infra stands up end to end |
| 2. Bootstrap | Local, one-time | → remote (Azure blob) | `az login` | Create the state backend + GitHub OIDC federation |
| 3. Steady state | **GitHub Actions** | remote | OIDC (keyless) | PR → `plan` → gated `apply` |

Why staged: GitHub Actions runners are stateless, so Terraform state must live in Azure and auth
must be keyless (OIDC). Both of those have to exist *before* CI can run — a one-time local bootstrap.

---

## Stage 1 — prove it locally (local state)

```powershell
cd infra\scripts
.\preflight.ps1        # checks az, terraform, login, providers
.\deploy.ps1           # terraform apply -> az acr build x2 -> apply real images
```

State is a local `terraform.tfstate`. Good for a first run by one operator. Tear down with
`.\destroy.ps1`. Do **not** share local state or run it from two places.

## Stage 2 — bootstrap remote state + OIDC (one-time)

```powershell
cd infra\scripts

# 2a. Create the Azure blob backend for Terraform state (prints backend-config + repo variables).
.\bootstrap-remote-state.ps1 -Location eastus2

# 2b. Federate GitHub -> Azure with OIDC (no client secret; prints repo secrets).
.\setup-github-oidc.ps1 -Repo "<owner>/<repo>"
```

Then migrate the local state into Azure:

```powershell
cd infra\terraform
copy backend.tf.example backend.tf
terraform init -migrate-state `
  -backend-config="resource_group_name=<TFSTATE_RESOURCE_GROUP>" `
  -backend-config="storage_account_name=<TFSTATE_STORAGE_ACCOUNT>" `
  -backend-config="container_name=tfstate" `
  -backend-config="key=foundry-phase2.tfstate" `
  -backend-config="use_azuread_auth=true"
```

Configure the repo (values are printed by the scripts):

- **Secrets** (Settings → Secrets and variables → Actions → *Secrets*): `AZURE_CLIENT_ID`,
  `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.
- **Variables** (same page → *Variables*): `TFSTATE_RESOURCE_GROUP`, `TFSTATE_STORAGE_ACCOUNT`,
  `TFSTATE_CONTAINER`, `TFSTATE_KEY`.
- **Environment**: create an environment named `production` with **required reviewers** so `apply`
  is gated by a human.

## Stage 3 — GitHub Actions (remote state, OIDC)

Once Stage 2 is done, the workflows in `.github/workflows/` take over:

| Workflow | Trigger | Does |
| --- | --- | --- |
| `ci.yml` | push / PR | Build + test app (backend `node --test`, MCP contracts, UI build, agent-service tests + eval gate). No cloud. |
| `terraform-plan.yml` | PR touching `infra/**` | OIDC login → `fmt -check` → `init` (remote) → `validate` → `plan` (posted to the job summary). Read-only. |
| `terraform-apply.yml` | manual (`workflow_dispatch`) | Gated by the `production` environment → OIDC login → `init` → `apply`. Manual-only so it never fires unintentionally. |

Flow: open a PR → **plan** runs and shows the diff → review + approve → merge to `main`. Then
**apply** is triggered **manually** (Actions → Terraform Apply → Run workflow) and waits for the
`production` environment reviewer before applying. No credentials are ever stored; GitHub exchanges a
short-lived OIDC token for an Azure token at run time.

---

## Governance notes

- **Least privilege:** `setup-github-oidc.ps1` assigns `Contributor` + `User Access Administrator`
  (the infra creates role assignments). Scope them to a resource group instead of the whole
  subscription where possible (`-Scope`).
- **Plan-only option:** for a workshop you may not want CI to apply live at all — keep only
  `terraform-plan.yml` active (safe, no changes) and run `apply` manually. Disable/delete
  `terraform-apply.yml` to enforce that.
- **Images vs infra:** the workflows manage Terraform infrastructure. Container images are still
  built/pushed by `infra/scripts/deploy.ps1` (`az acr build`); add an image-build workflow when you
  want that in CI too.
- **No secrets committed:** `.env` is gitignored; `backend.tf` (the activated remote-state file) is
  gitignored; state account/OIDC identifiers live in GitHub secrets/variables, not the repo.
