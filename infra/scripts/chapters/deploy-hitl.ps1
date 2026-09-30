# Chapter child runner: HITL - Durable Task Scheduler (Ch 7).
[CmdletBinding()]
param([ValidateSet("validate", "deploy")][string]$Mode = "validate")
$ErrorActionPreference = "Stop"
$repo = Resolve-Path "$PSScriptRoot\..\..\.."

Write-Host "[hitl] validate: review state machine + task schema"
Push-Location (Join-Path $repo "agent-service")
try {
  python tests/test_hitl.py
  if ($Mode -eq "deploy") {
    Write-Host "[hitl] deploy: Durable Task Scheduler graduation target" -ForegroundColor Cyan
    Write-Host "      -> terraform apply (dts.tf: dts_scheduler + dts_taskhub + worker container app)"
    Write-Host "      -> set TF_VAR_enable_dts=true, TF_VAR_hitl_mode=dts (see hitl-durable-task-scheduler.md)"
  }
}
finally { Pop-Location }
