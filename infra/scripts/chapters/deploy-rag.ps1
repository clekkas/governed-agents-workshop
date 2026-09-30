# Chapter child runner: Foundry IQ / RAG (Ch 4).
[CmdletBinding()]
param([ValidateSet("validate", "deploy")][string]$Mode = "validate")
$ErrorActionPreference = "Stop"
$repo = Resolve-Path "$PSScriptRoot\..\..\.."

Write-Host "[rag] validate: retrieval contract + citation behavior"
Push-Location (Join-Path $repo "agent-service")
try {
  python tests/test_contract.py
  if ($Mode -eq "deploy") {
    Write-Host "[rag] deploy: Azure AI Search index + knowledge source" -ForegroundColor Cyan
    Write-Host "      -> terraform apply (azurerm_search_service.search + storage rag container)"
    Write-Host "      -> load data/rag-docs into the index; reuse existing Search where present (see capability-host-reuse-and-cost.md)"
  }
}
finally { Pop-Location }
