# Set up keyless GitHub Actions -> Azure federation (OIDC) for the staged-hybrid rollout.
#
# One-time, run locally with `az login` by someone who can create app registrations and assign roles
# (Owner, or User Access Administrator + Contributor). Creates an Entra app + service principal,
# federates it to your GitHub repo (branch main, pull_request, and the 'production' environment),
# and assigns the roles Terraform needs. Prints the GitHub secrets/variables to configure.
#
# No client secret is created — GitHub authenticates with a short-lived OIDC token. See
# infra/DEPLOYMENT.md.
#
# Usage:
#   ./setup-github-oidc.ps1 -Repo "owner/repo"
#   ./setup-github-oidc.ps1 -Repo "owner/repo" -Scope "/subscriptions/<sub>/resourceGroups/kaiser-foundry-rg"

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Repo,   # e.g. "chrislekkas/kaiser-readmissions-agent-workshop"
  [string]$AppName = "gh-oidc-foundry-phase2",
  [string]$Scope = "",                            # defaults to the whole subscription
  [string]$Environment = "production"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command az -ErrorAction SilentlyContinue)) { throw "Azure CLI (az) is required." }
if (-not (az account show 2>$null)) { throw "Not logged in. Run 'az login' first." }
if ($Repo -notmatch '^[^/]+/[^/]+$') { throw "Repo must be 'owner/name'." }

$sub = (az account show --query id -o tsv)
$tenant = (az account show --query tenantId -o tsv)
if (-not $Scope) { $Scope = "/subscriptions/$sub" }

Write-Host "Subscription: $sub" -ForegroundColor DarkGray
Write-Host "Repo:         $Repo" -ForegroundColor DarkGray
Write-Host "Role scope:   $Scope`n" -ForegroundColor DarkGray

# 1. App registration + service principal.
$appId = (az ad app create --display-name $AppName --query appId -o tsv)
Write-Host "[ ok ] app registration: $AppName ($appId)" -ForegroundColor Green
az ad sp create --id $appId --output none 2>$null
$spId = (az ad sp show --id $appId --query id -o tsv)
Write-Host "[ ok ] service principal: $spId" -ForegroundColor Green

# 2. Federated credentials — one per subject the workflows use.
function New-Federation($name, $subject) {
  $body = @{ name = $name; issuer = "https://token.actions.githubusercontent.com"; subject = $subject; audiences = @("api://AzureADTokenExchange") } | ConvertTo-Json -Compress
  $tmp = New-TemporaryFile
  $body | Set-Content -Path $tmp -Encoding utf8
  az ad app federated-credential create --id $appId --parameters $tmp --output none 2>$null
  Remove-Item $tmp -ErrorAction SilentlyContinue
  Write-Host "[ ok ] federated credential: $name -> $subject" -ForegroundColor Green
}
New-Federation "main"        "repo:${Repo}:ref:refs/heads/main"
New-Federation "pull-request" "repo:${Repo}:pull_request"
New-Federation "env-$Environment" "repo:${Repo}:environment:$Environment"

# 3. Role assignments. Contributor to manage resources; User Access Administrator because the infra
#    creates role assignments (managed identity -> ACR/KeyVault/Storage/Search/Foundry).
foreach ($role in @("Contributor", "User Access Administrator")) {
  az role assignment create --assignee-object-id $spId --assignee-principal-type ServicePrincipal `
    --role $role --scope $Scope --output none 2>$null
  Write-Host "[ ok ] role: $role at $Scope" -ForegroundColor Green
}

Write-Host "`n=== GitHub secrets to set (Settings > Secrets and variables > Actions > Secrets) ===" -ForegroundColor Cyan
Write-Host "  AZURE_CLIENT_ID        = $appId"
Write-Host "  AZURE_TENANT_ID        = $tenant"
Write-Host "  AZURE_SUBSCRIPTION_ID  = $sub"
Write-Host "`nAlso create a GitHub environment named '$Environment' with required reviewers so apply is gated." -ForegroundColor Yellow
Write-Host "Least privilege: scope the roles to a resource group instead of the whole subscription when possible." -ForegroundColor Yellow
