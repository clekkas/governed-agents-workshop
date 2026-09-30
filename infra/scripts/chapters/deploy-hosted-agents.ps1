# Chapter child runner: Hosted agents + BYO registry (Ch 1).
[CmdletBinding()]
param([ValidateSet("validate", "deploy")][string]$Mode = "validate")
$ErrorActionPreference = "Stop"
$repo = Resolve-Path "$PSScriptRoot\..\..\.."

Write-Host "[hosted-agents] validate: agent manifest conformance"
Push-Location (Join-Path $repo "agent-service")
try {
  python tests/test_manifests.py
  if ($Mode -eq "deploy") {
    Write-Host "[hosted-agents] deploy: build + roll the agent image, hosted-agent target" -ForegroundColor Cyan
    Write-Host "      -> az acr build (agent-service/Dockerfile); terraform apply rolls container_image_agent"
    Write-Host "      -> BYO registry: sample end-to-end only (not pre-staged) - see facilitator-cheatsheet.md"
  }
}
finally { Pop-Location }
