# Tear down all Azure + Foundry resources for the workshop deployment.
# Destroys everything Terraform created. Use after the workshop.

[CmdletBinding()]
param(
  [switch]$AutoApprove
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path "$PSScriptRoot\..\.."
$tf       = Join-Path $repoRoot "infra\terraform"
$approve  = ""
if ($AutoApprove.IsPresent) { $approve = "-auto-approve" }

if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
  throw "terraform not found on PATH."
}

Write-Host "Destroying all workshop resources..." -ForegroundColor Yellow
Push-Location $tf
try {
  terraform destroy -input=false $approve
  Write-Host "Teardown complete." -ForegroundColor Green
}
finally {
  Pop-Location
}
