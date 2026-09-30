# Chapter child runner: LAW / Application Insights observability (Ch 6).
[CmdletBinding()]
param([ValidateSet("validate", "deploy")][string]$Mode = "validate")
$ErrorActionPreference = "Stop"
$repo = Resolve-Path "$PSScriptRoot\..\..\.."

Write-Host "[observability] validate: correlation trace store + ordered events"
Push-Location (Join-Path $repo "backend")
try {
  node --test test/traceStore.test.js
  if ($Mode -eq "deploy") {
    Write-Host "[observability] deploy: LAW + App Insights (PHI posture)" -ForegroundColor Cyan
    Write-Host "      -> terraform apply (azurerm_log_analytics_workspace.law + azurerm_application_insights.appi)"
    Write-Host "      -> dedicated LAW cluster + CMK + AMPLS for request/response content (see observability-dedicated-cluster-cmk-ampls.md)"
  }
}
finally { Pop-Location }
