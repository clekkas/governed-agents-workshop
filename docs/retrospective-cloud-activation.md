# Retrospective — Governed Terraform CI/CD on a private-only Azure tenant (Option B)

A build-along record of how we stood up **keyless, self-hosted GitHub Actions Terraform CI/CD**
against a Microsoft-managed subscription whose Azure Policy forbids public storage access and public
VM IPs. Every step below explains **what it does, why, and how to validate it by hand**.

Synthetic data only. Non-secret identifiers are shown so the steps are reproducible; secrets live in
GitHub, never in the repo.

![Cloud activation architecture](cloud-activation-architecture.svg)

## The problem we were solving

We wanted the standard pattern: **PR → `terraform plan` → merge → gated `terraform apply`**, run by
GitHub Actions with **no stored credentials** (OIDC) and **remote Terraform state** in Azure Blob.

Two tenant guardrails broke the standard recipe:

- **Storage accounts must be private** (public network access disabled by policy). Microsoft-hosted
  GitHub runners live on the public internet and therefore **cannot reach the state account**.
- **VMs cannot have public IPs** (also policy).

The answer (Option B): run the pipeline on a **self-hosted runner inside an Azure VNet**, and reach
the state account through a **private endpoint**. Auth stays keyless via **Entra Workload Identity
Federation (OIDC)**.

---

## Environment (reference values)

| Thing | Value |
| --- | --- |
| Subscription | `<SUBSCRIPTION_ID>` (MCAPS) |
| Tenant | `<TENANT_ID>` |
| Resource group | `rg-tfstate-foundry-phase2` (eastus2) |
| State account / container / key | `sttfstategovagent01` / `tfstate` / `foundry-phase2.tfstate` |
| VNet / subnets | `vnet-tfrunner` 10.20.0.0/16 · `snet-runner` .1.0/24 · `snet-pe` .2.0/24 |
| Private endpoint | `pe-tfstate-blob` → 10.20.2.4 |
| Runner VM | `vm-ghrunner` (Standard_D2s_v3, no public IP, private IP 10.20.1.4) |
| GitHub repo | `clekkas/governed-agents-inpractice-workshop` |
| OIDC app / SP | client `<OIDC_APP_CLIENT_ID>` / SP obj `<OIDC_SP_OBJECT_ID>` |

---

## Step 1 — Remote state storage account

**What / why.** Terraform state must live somewhere stateless runners can share. We created a
Storage account + `tfstate` container. Tenant policy immediately disabled public access and shared-key
auth — which is the whole reason the rest of Option B exists.

**Command (essence).** `infra/scripts/bootstrap-remote-state.ps1` → `az group create`,
`az storage account create`, container create.

**Validate manually.**
```powershell
az storage account show -n sttfstategovagent01 -g rg-tfstate-foundry-phase2 `
  --query "{public:publicNetworkAccess, sharedKey:allowSharedKeyAccess, tls:minimumTlsVersion}" -o json
# expect: public=Disabled, sharedKey=false  -> confirms the private-only constraint
```

## Step 2 — VNet + subnets

**What / why.** A network for the runner (`snet-runner`) and the private endpoint (`snet-pe`). The
runner must live on the same VNet (or a peered one) that can resolve/route to the private endpoint.

**Validate manually.**
```powershell
az network vnet subnet list -g rg-tfstate-foundry-phase2 --vnet-name vnet-tfrunner `
  --query "[].{name:name, prefix:addressPrefix}" -o table
# expect: snet-runner 10.20.1.0/24  and  snet-pe 10.20.2.0/24
```

## Step 3 — Private endpoint + private DNS

**What / why.** The **private endpoint** projects the blob service into `snet-pe` as a private NIC
(10.20.2.4). The **private DNS zone** `privatelink.blob.core.windows.net`, linked to the VNet, makes
the account's public FQDN resolve to that private IP — so `sttfstategovagent01.blob.core.windows.net`
routes over the VNet instead of the internet. Without the DNS zone, the name would still resolve to a
public IP that policy blocks.

**Validate manually.**
```powershell
# the DNS A record points at the PE
az network private-dns record-set a list -g rg-tfstate-foundry-phase2 `
  --zone-name privatelink.blob.core.windows.net --query "[].{name:name, ip:aRecords[0].ipv4Address}" -o table
# from the runner VM, the FQDN must resolve to 10.20.2.4 (see Step 4's run-command check)
```

## Step 4 — Self-hosted runner VM

**What / why.** A Linux VM in `snet-runner` with **no public IP** (policy) that runs the GitHub
Actions runner. It reaches **github.com outbound** (to receive jobs) and the **state account
privately** (via the PE). We configured it entirely with `az vm run-command` — no SSH, no inbound
ports. Installed: the runner service, `az` CLI, `git`.

**Gotchas we hit:** `Standard_B2s`/several sizes were capacity-restricted in eastus2 (used
`Standard_D2s_v3`); public IPs are policy-blocked (created with none); passing a multi-line bash
script to `run-command` mangled CRLF line endings (fixed by base64-encoding an LF-only script).

**Validate manually.**
```powershell
# runner registered + online in GitHub
gh api repos/clekkas/governed-agents-inpractice-workshop/actions/runners `
  --jq '.runners[] | {name,status,labels:[.labels[].name]}'
# from inside the VM: github reachable AND storage resolves privately
az vm run-command invoke -g rg-tfstate-foundry-phase2 -n vm-ghrunner --command-id RunShellScript `
  --scripts "curl -sS -m 10 -o /dev/null -w 'github=%{http_code}\n' https://api.github.com; getent hosts sttfstategovagent01.blob.core.windows.net" `
  --query "value[0].message" -o tsv
# expect: github=200  and  10.20.2.4 ... sttfstategovagent01.blob.core.windows.net
```

## Step 5 — Entra Workload Identity Federation (OIDC)

**What / why.** Instead of a client secret, GitHub Actions presents a short-lived **OIDC token**;
Entra trusts it via a **federated credential** whose `subject` matches the workflow's token. We
created an app registration + service principal and 3 federated credentials (main branch, PRs, the
`production` environment).

**The enterprise twist.** This Microsoft-managed github.com **customizes the token `sub` claim** to
embed immutable numeric IDs, e.g.
`repo:clekkas@<OWNER_ID>/governed-agents-inpractice-workshop@<REPO_ID>:ref:refs/heads/main`.
The plain `repo:owner/name:...` federated subject is rejected with `AADSTS700213`. We read the
presented subject from the failing run log and created matching ID-embedded credentials.

**Validate manually.**
```powershell
az ad app federated-credential list --id <OIDC_APP_CLIENT_ID> --query "[].subject" -o tsv
# expect BOTH the plain and the ID-embedded (repo:clekkas@<OWNER_ID>/...@<REPO_ID>:...) subjects
```

## Step 6 — Roles

**What / why.** The OIDC SP needs to manage resources and (because the infra creates role
assignments) assign roles: **Contributor + User Access Administrator** at subscription scope. It also
needs **Storage Blob Data Contributor** on the state account to read/write state. Data-plane storage
RBAC takes several minutes to propagate — expect a first `403 AuthorizationPermissionMismatch` that
clears on retry.

**Validate manually.**
```powershell
$sub='<SUBSCRIPTION_ID>'
az role assignment list --assignee <OIDC_APP_CLIENT_ID> `
  --query "[].{role:roleDefinitionName, scope:scope}" -o table
# expect Contributor + User Access Administrator (subscription) and Storage Blob Data Contributor (state account)
```

## Step 7 — GitHub repo configuration

**What / why.** The workflows read Azure identity from **secrets** and the state backend from
**variables** (so no account names or IDs are committed). An **environment** named `production` gates
`apply`.

**Validate manually.**
```powershell
gh secret   list --repo clekkas/governed-agents-inpractice-workshop   # AZURE_CLIENT_ID / TENANT / SUBSCRIPTION
gh variable list --repo clekkas/governed-agents-inpractice-workshop   # TFSTATE_* (RG/STORAGE_ACCOUNT/CONTAINER/KEY)
gh api repos/clekkas/governed-agents-inpractice-workshop/environments --jq '.environments[].name'  # production
```

## Step 8 — Workflows target the self-hosted runner

**What / why.** `terraform-plan.yml` and `terraform-apply.yml` run on `[self-hosted, azure-vnet]`.
Each does: `azure/login` (OIDC) → activate the remote backend (`cp backend.tf.example backend.tf`) →
**create the state container on the runner** (`az storage container create --auth-mode login`, since
key auth is off and only the runner has private access) → `terraform init` (remote) → `fmt` /
`validate` / `plan` (and `apply` in the other file).

**Gotchas we hit:** `hashicorp/setup-terraform` wraps `terraform` in Node → set
`terraform_wrapper: false` (runner has no system node); `azure/login` needs `az` on the runner
(installed in Step 4); the `tfstate` container had to be created from the runner, not a laptop.

**Validate manually (trigger a plan and read the result).**
```powershell
gh workflow run "Terraform Plan" --repo clekkas/governed-agents-inpractice-workshop --ref main
$id = gh run list --repo clekkas/governed-agents-inpractice-workshop --workflow "Terraform Plan" --limit 1 --json databaseId --jq '.[0].databaseId'
gh run watch $id --repo clekkas/governed-agents-inpractice-workshop --exit-status
gh run view  $id --repo clekkas/governed-agents-inpractice-workshop --log | Select-String 'Plan:'
# expect: "Plan: 22 to add, 0 to change, 0 to destroy"  (our verified result)
```

---

## End-to-end request flow (numbers match the diagram)

1. **Job dispatch.** GitHub Actions queues the job; the self-hosted runner picks it up over its
   **outbound** long-poll (no inbound ports open on the VM).
2. **Present OIDC token.** The workflow requests a GitHub OIDC token and calls `azure/login`.
3. **Federated exchange.** Entra matches the token `subject` to a federated credential and returns a
   short-lived Azure access token — **no client secret anywhere**.
4. **Remote state over private link.** `terraform init/plan` reads and writes state to
   `sttfstategovagent01` **through the private endpoint** (10.20.2.4); public access stays disabled.
5. **Plan / apply.** `plan` (done — 22 to add) and, when triggered and approved, `apply` manages the
   target workload infra (Foundry, AI Search, Container Apps + sidecar, ACR, Key Vault, LAW/App
   Insights, managed identity + role assignments).

---

## What is NOT done yet

- **`terraform apply`** has not run — no target infrastructure is deployed (the plan shows 22 would be
  created). Apply is `workflow_dispatch`-only and should be gated by adding **required reviewers** to
  the `production` environment first.
- **App container images** are still built by `infra/scripts/deploy.ps1` (`az acr build`); an
  image-build workflow is a future add.

## Cost & teardown

```powershell
# stop compute between sessions (done tonight)
az vm deallocate -g rg-tfstate-foundry-phase2 -n vm-ghrunner
az vm start      -g rg-tfstate-foundry-phase2 -n vm-ghrunner

# full teardown when finished (also removes the state account)
az group delete -n rg-tfstate-foundry-phase2 --yes
az ad app delete --id <OIDC_APP_CLIENT_ID>
```

## Lessons (the workshop takeaways)

1. **Enterprise network policy dictates CI topology.** Private-only storage means Microsoft-hosted
   runners can't reach state — you need a self-hosted runner on the VNet + a private endpoint.
2. **Keyless is achievable but claim-shape matters.** Enterprise-managed GitHub customizes the OIDC
   `sub`; federated credentials must match the exact ID-embedded subject.
3. **Least privilege has a floor.** Creating role assignments needs User Access Administrator; scope
   it to a resource group where you can.
4. **Data-plane RBAC is eventually consistent.** Budget minutes, not seconds, after granting Storage
   Blob Data roles.
5. **Self-hosted runners are bare.** They need `az`, `git`, and `terraform_wrapper: false`; configure
   them without inbound access via `az vm run-command`.
