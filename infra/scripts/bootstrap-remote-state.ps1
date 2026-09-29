# Bootstrap the Terraform remote state backend (Stage 2 of the staged-hybrid rollout).
#
# One-time, run locally with `az login`. Creates the resource group, storage account, and blob
# container that hold Terraform state, then prints the `-backend-config` values for CI and local use.
# Idempotent: re-running is safe (uses `az ... create` which no-ops if the resource exists).
#
# Why this exists: GitHub Actions runs are stateless, so Terraform state must live in Azure, not on a
# laptop. This backend must exist BEFORE any CI plan/apply. See infra/DEPLOYMENT.md.
#
# Usage:
#   ./bootstrap-remote-state.ps1 -Location eastus2
#   ./bootstrap-remote-state.ps1 -ResourceGroup rg-tfstate -StorageAccount sttfstatekp01 -Container tfstate

[CmdletBinding()]
param(
  [string]$ResourceGroup = "rg-tfstate-foundry-phase2",
  [string]$StorageAccount = "",                     # must be globally unique, 3-24 lowercase alnum
  [string]$Container = "tfstate",
  [string]$Location = "eastus2",
  [string]$StateKey = "foundry-phase2.tfstate"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command az -ErrorAction SilentlyContinue)) { throw "Azure CLI (az) is required. Install it and 'az login'." }
if (-not (az account show 2>$null)) { throw "Not logged in. Run 'az login' first." }

# Default a unique-ish storage account name if not supplied.
if (-not $StorageAccount) {
  $suffix = -join ((48..57) + (97..122) | Get-Random -Count 6 | ForEach-Object { [char]$_ })
  $StorageAccount = "sttfstate$suffix"
}
if ($StorageAccount.Length -gt 24 -or $StorageAccount -notmatch '^[a-z0-9]{3,24}$') {
  throw "StorageAccount '$StorageAccount' must be 3-24 lowercase alphanumeric characters."
}

$sub = (az account show --query id -o tsv)
Write-Host "Subscription: $sub" -ForegroundColor DarkGray
Write-Host "Creating remote-state backend..." -ForegroundColor Cyan

az group create --name $ResourceGroup --location $Location --output none
Write-Host "[ ok ] resource group: $ResourceGroup" -ForegroundColor Green

# Harden the state account: no public blob, TLS1.2, versioning for state recovery.
az storage account create `
  --name $StorageAccount --resource-group $ResourceGroup --location $Location `
  --sku Standard_LRS --kind StorageV2 `
  --allow-blob-public-access false --min-tls-version TLS1_2 --output none
az storage account blob-service-properties update `
  --account-name $StorageAccount --resource-group $ResourceGroup `
  --enable-versioning true --output none 2>$null
Write-Host "[ ok ] storage account: $StorageAccount (public blob disabled, TLS1.2, versioning on)" -ForegroundColor Green

# Create the container using Entra auth (no account keys).
az storage container create `
  --name $Container --account-name $StorageAccount --auth-mode login --output none
Write-Host "[ ok ] container: $Container" -ForegroundColor Green

Write-Host "`n=== Terraform backend config ===" -ForegroundColor Cyan
Write-Host @"
Local (partial backend init — no secrets in the repo):

  cd infra/terraform
  terraform init ``
    -backend-config="resource_group_name=$ResourceGroup" ``
    -backend-config="storage_account_name=$StorageAccount" ``
    -backend-config="container_name=$Container" ``
    -backend-config="key=$StateKey" ``
    -backend-config="use_azuread_auth=true"

If you were using local state, add -migrate-state to move it into Azure on the next init.
"@ -ForegroundColor Gray

Write-Host "=== GitHub repository variables to set (Settings > Secrets and variables > Actions > Variables) ===" -ForegroundColor Cyan
Write-Host "  TFSTATE_RESOURCE_GROUP   = $ResourceGroup"
Write-Host "  TFSTATE_STORAGE_ACCOUNT  = $StorageAccount"
Write-Host "  TFSTATE_CONTAINER        = $Container"
Write-Host "  TFSTATE_KEY              = $StateKey"
Write-Host "`nNext: run ./setup-github-oidc.ps1 to create the keyless GitHub -> Azure federation." -ForegroundColor Yellow
