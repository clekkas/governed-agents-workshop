# Resume — cloud activation (Option B) playbook

Snapshot of the live cloud state so we can continue. Everything below is **already provisioned**;
tomorrow we restart the runner and (optionally) run the gated apply. Non-secret identifiers only.

## Status (as of 2026-09-29)

- **CI workflow:** green on GitHub-hosted runners.
- **Terraform Plan:** green end-to-end on the self-hosted runner — **`Plan: 22 to add`** (run `36523907847`).
- **Terraform Apply:** authored, `workflow_dispatch`-only, gated by the `production` environment. **Not run** (no infra deployed yet).
- **Runner VM:** **deallocated** overnight to stop compute billing.

## Live resources (subscription `0e494a0c-e2e6-41f8-8a50-6064d842225e`, tenant `16b3c013-d300-468d-ac64-7eda0820b6d3`)

Resource group **`rg-tfstate-foundry-phase2`** (eastus2):
- State account **`sttfstategovagent01`**, container `tfstate`, key `foundry-phase2.tfstate` (public access disabled; key auth disabled; reachable only via the private endpoint).
- VNet `vnet-tfrunner` (10.20.0.0/16): `snet-runner` (10.20.1.0/24), `snet-pe` (10.20.2.0/24).
- Private endpoint `pe-tfstate-blob` (10.20.2.4) + private DNS zone `privatelink.blob.core.windows.net`.
- Runner VM **`vm-ghrunner`** (`Standard_D2s_v3`, private IP 10.20.1.4, no public IP). Has az CLI, git, the GitHub runner service (systemd, auto-start), and a system managed identity (`e88380de-7493-4907-a4ca-20c9ed9974f0`) with Storage Blob Data Contributor on the state account.

GitHub repo **`clekkas/governed-agents-inpractice-workshop`**:
- OIDC app `gh-oidc-foundry-phase2` — client id `0882f573-10d6-4f32-940d-0354b760c3bb`, SP object id `04779896-8997-4816-b11e-d8338fb06684`.
- Federated credentials include the **enterprise ID-embedded subjects**, e.g.
  `repo:clekkas@314357/governed-agents-inpractice-workshop@1393826284:ref:refs/heads/main`
  (plus `:pull_request` and `:environment:production`).
- Secrets: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.
- Variables: `TFSTATE_RESOURCE_GROUP`, `TFSTATE_STORAGE_ACCOUNT`, `TFSTATE_CONTAINER`, `TFSTATE_KEY`.
- Roles: OIDC SP has Contributor + User Access Administrator (subscription) and Storage Blob Data Contributor (state account).

## Resume tomorrow

```powershell
# 1. Start the runner VM (its runner service auto-starts on boot)
az vm start -g rg-tfstate-foundry-phase2 -n vm-ghrunner

# 2. Confirm the runner is back online (wait ~60s after start)
gh api repos/clekkas/governed-agents-workshop/actions/runners --jq '.runners[] | {name,status}'

# 3. Re-run the plan to confirm the chain still works
gh workflow run "Terraform Plan" --repo clekkas/governed-agents-workshop --ref main
gh run watch (gh run list --repo clekkas/governed-agents-workshop --workflow "Terraform Plan" --limit 1 --json databaseId --jq '.[0].databaseId') --repo clekkas/governed-agents-workshop --exit-status
```

> **If a plan fails with `AADSTS700213 No matching federated identity record`:** the repo was
> **renamed**. The OIDC subject embeds the repo slug (e.g.
> `repo:clekkas@314357/<new-slug>@1393826284:ref:refs/heads/main`), so add federated credentials for
> the new slug. On 2026-09-29 the repo was renamed `governed-agents-inpractice-workshop` →
> `governed-agents-workshop`; new credentials were added and the git remote updated.

## Next steps (tomorrow's decisions)

1. **Gate the apply:** add required reviewers to the `production` GitHub environment
   (Settings → Environments → production) so apply pauses for approval.
2. **Run the apply (deploys 22 resources — real cost, ~$75+/mo incl. AI Search):**
   `gh workflow run "Terraform Apply"` → approve the environment gate → watch.
3. **App container images:** infra provisions the platform; the app/agent images are still built by
   `infra/scripts/deploy.ps1` (`az acr build`). Add an image-build workflow or run that step.
4. **Deploy-time verify:** hit the Container App URL; confirm the agent-service sidecar + Foundry model.

## Cost control

```powershell
az vm deallocate -g rg-tfstate-foundry-phase2 -n vm-ghrunner   # stop compute between sessions (done tonight)
az vm start      -g rg-tfstate-foundry-phase2 -n vm-ghrunner   # restart for the next session
```

## Full teardown (when the workshop is over)

```powershell
# If infra was applied, destroy it first (from the runner, which can reach state):
#   gh workflow run "Terraform Apply" ... is apply-only; run `terraform destroy` via a runner session or add a destroy workflow.
az group delete -n rg-tfstate-foundry-phase2 --yes   # removes runner, VNet, PE, and the state account
# Also remove the OIDC app + role assignments:
az ad app delete --id 0882f573-10d6-4f32-940d-0354b760c3bb
```
