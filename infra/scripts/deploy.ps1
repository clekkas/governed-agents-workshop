# Deploy the Discharge Transition Exception Coordinator to Azure + Microsoft Foundry.
#
# Flow:
#   1. terraform init + apply (provisions infra incl. ACR, with a placeholder image)
#   2. az acr build (builds and pushes the app image from the repo Dockerfile)
#   3. terraform apply -var container_image=<pushed image> (rolls the real image)
#
# Prereqs: az CLI (logged in), terraform, and access to create the resources.
# Nothing here uses real PHI. Review the plan before approving.

[CmdletBinding()]
param(
  [switch]$SkipBuild,      # skip az acr build (reuse existing image tag)
  [switch]$AutoApprove,    # pass -auto-approve to terraform
  [switch]$EnableMcpServer, # also build + deploy the hosted (internal) MCP server
  [string]$ImageTag = "latest"
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path "$PSScriptRoot\..\.."
$tf       = Join-Path $repoRoot "infra\terraform"
$approve  = ""
if ($AutoApprove.IsPresent) { $approve = "-auto-approve" }

function Require($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Required tool '$name' not found on PATH."
  }
}
Require az
Require terraform

Write-Host "== 1/3  Terraform init + apply (infra) ==" -ForegroundColor Cyan
Push-Location $tf
try {
  terraform init -input=false
  terraform apply -input=false $approve

  $acrName = terraform output -raw acr_name
  $appUrl  = terraform output -raw app_url

  if (-not $SkipBuild) {
    Write-Host "`n== 2/3  Build + push images to ACR ($acrName) ==" -ForegroundColor Cyan
    $loginServer = terraform output -raw acr_login_server

    # App image (backend + built UI) from the repo-root Dockerfile.
    $appImage = "discharge-transition:$ImageTag"
    az acr build --registry $acrName --image $appImage --file (Join-Path $repoRoot "Dockerfile") $repoRoot | Out-Host
    $fullAppImage = "$loginServer/$appImage"

    # Agent sidecar image (Python multi-agent service).
    $agentDir   = Join-Path $repoRoot "agent-service"
    $agentImage = "discharge-transition-agent:$ImageTag"
    az acr build --registry $acrName --image $agentImage --file (Join-Path $agentDir "Dockerfile") $agentDir | Out-Host
    $fullAgentImage = "$loginServer/$agentImage"

    # Optional: hosted (internal-ingress) MCP server image.
    $mcpArgs = @()
    if ($EnableMcpServer.IsPresent) {
      Write-Host "`n== 2b/3  Build + push MCP server image ==" -ForegroundColor Cyan
      $mcpDir   = Join-Path $repoRoot "mcp-server"
      $mcpImage = "discharge-transition-mcp:$ImageTag"
      az acr build --registry $acrName --image $mcpImage --file (Join-Path $mcpDir "Dockerfile") $mcpDir | Out-Host
      $fullMcpImage = "$loginServer/$mcpImage"
      $mcpArgs = @("-var", "enable_mcp_server=true", "-var", "container_image_mcp=$fullMcpImage")
    }

    Write-Host "`n== 3/3  Terraform apply (roll real images) ==" -ForegroundColor Cyan
    terraform apply -input=false $approve `
      -var "container_image=$fullAppImage" `
      -var "container_image_agent=$fullAgentImage" `
      @mcpArgs
  } else {
    Write-Host "Skipping image build (-SkipBuild)." -ForegroundColor Yellow
  }

  Write-Host "`nDeployment complete." -ForegroundColor Green
  Write-Host "App URL:            $(terraform output -raw app_url)"
  Write-Host "Foundry endpoint:   $(terraform output -raw foundry_project_endpoint)"
  Write-Host "Model deployment:   $(terraform output -raw model_deployment)"
  Write-Host "Search endpoint:    $(terraform output -raw search_endpoint)"
}
finally {
  Pop-Location
}
