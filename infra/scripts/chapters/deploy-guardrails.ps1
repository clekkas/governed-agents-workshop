# Chapter child runner: Compliance policy + guardrails (Ch 3).
[CmdletBinding()]
param([ValidateSet("validate", "deploy")][string]$Mode = "validate")
$ErrorActionPreference = "Stop"
$repo = Resolve-Path "$PSScriptRoot\..\..\.."

Write-Host "[guardrails] validate: policy/guardrail checks (prohibited claims, PHI minimization)"
Push-Location (Join-Path $repo "backend")
try {
  node --test test/policy.test.js
  if ($Mode -eq "deploy") {
    Write-Host "[guardrails] deploy: content-safety + guardrail policy" -ForegroundColor Cyan
    Write-Host "      -> apply policy/ guardrails to the Foundry content filter (layered tuning + ticket path)"
    Write-Host "      -> verify against policy/test-prompts.md (benign clinical passes; 'safe to discharge' blocked)"
  }
}
finally { Pop-Location }
