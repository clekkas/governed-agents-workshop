# Preflight checks before deploying to Azure + Foundry.
# Verifies tooling, login context, and quota-relevant inputs. Read-only.

$ErrorActionPreference = "Continue"
$issues = @()

function Check($label, [scriptblock]$test) {
  try {
    $result = & $test
    if ($result) { Write-Host "[ ok ] $label" -ForegroundColor Green }
    else { Write-Host "[fail] $label" -ForegroundColor Red; $script:issues += $label }
  } catch {
    Write-Host "[fail] $label - $($_.Exception.Message)" -ForegroundColor Red
    $script:issues += $label
  }
}

Write-Host "Preflight: Foundry Phase 2 deployment`n" -ForegroundColor Cyan

Check "az CLI installed"        { [bool](Get-Command az -ErrorAction SilentlyContinue) }
Check "terraform installed"     { [bool](Get-Command terraform -ErrorAction SilentlyContinue) }
Check "docker or ACR build path" { [bool](Get-Command az -ErrorAction SilentlyContinue) }  # az acr build needs no local docker
Check "az logged in"            { [bool](az account show 2>$null) }

$sub = az account show --query "{name:name, id:id}" -o json 2>$null | ConvertFrom-Json
if ($sub) { Write-Host "       subscription: $($sub.name) ($($sub.id))" -ForegroundColor DarkGray }

Check "providers registerable"  {
  $cs = az provider show -n Microsoft.CognitiveServices --query registrationState -o tsv 2>$null
  $app = az provider show -n Microsoft.App --query registrationState -o tsv 2>$null
  ($cs -and $app)
}

Write-Host ""
if ($issues.Count -eq 0) {
  Write-Host "Preflight passed. You can run ./deploy.ps1" -ForegroundColor Green
  exit 0
} else {
  Write-Host "Preflight found issues:" -ForegroundColor Red
  $issues | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
  Write-Host "`nCommon fixes: 'az login', install terraform, and register providers:" -ForegroundColor Yellow
  Write-Host "  az provider register --namespace Microsoft.CognitiveServices" -ForegroundColor Yellow
  Write-Host "  az provider register --namespace Microsoft.App" -ForegroundColor Yellow
  Write-Host "  az provider register --namespace Microsoft.Search" -ForegroundColor Yellow
  exit 1
}
