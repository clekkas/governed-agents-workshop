# Evaluation harness — live workshop demo (green -> red -> green).
#
# Shows the agent evaluation harness as a release gate: it passes on the current build, BLOCKS when a
# safety regression is introduced, and passes again once reverted. The regression is injected with a
# safe env-flag (EVAL_DEMO_BREAK) — NO code editing on stage.
#
# Usage:
#   .\scripts\demo-eval.ps1                 # default fault: risk_score (the headline adv-003 attack)
#   .\scripts\demo-eval.ps1 -Break phi      # PHI leak fault
#   .\scripts\demo-eval.ps1 -Break prohibited_claim   # "safe to discharge" fault
#   .\scripts\demo-eval.ps1 -NoPause        # run straight through without waiting for Enter

[CmdletBinding()]
param(
  [ValidateSet("risk_score", "phi", "prohibited_claim")]
  [string]$Break = "risk_score",
  [switch]$NoPause
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\.."
$agent = Join-Path $root "agent-service"
$py = Join-Path $agent ".venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
  Write-Host "agent-service\.venv not found. Create it first:" -ForegroundColor Red
  Write-Host "  cd agent-service; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
  exit 1
}

function Step($text) {
  Write-Host ""
  Write-Host ("=" * 78) -ForegroundColor DarkGray
  Write-Host $text -ForegroundColor Cyan
  Write-Host ("=" * 78) -ForegroundColor DarkGray
}

function Pause-Demo($prompt) {
  if (-not $NoPause) { Read-Host "`n$prompt" | Out-Null }
}

function Invoke-Harness {
  Push-Location $agent
  try {
    & $py "eval\evaluate_agent.py"
    return $LASTEXITCODE
  } finally {
    Pop-Location
  }
}

# Make sure we start clean.
Remove-Item Env:EVAL_DEMO_BREAK -ErrorAction SilentlyContinue

Step "1/3  Baseline: run the safety gates on the current build (expect PASS, exit 0)"
Write-Host "Talk track: 'This runs the agent over golden + adversarial cases and checks the safety" -ForegroundColor DarkGray
Write-Host "boundary on every run. Green means every gate held.'" -ForegroundColor DarkGray
Pause-Demo "Press Enter to run the baseline"
$rc = Invoke-Harness
Write-Host "`nexit code = $rc" -ForegroundColor $(if ($rc -eq 0) { "Green" } else { "Red" })

Step "2/3  Inject a safety regression via EVAL_DEMO_BREAK=$Break (no code editing)"
Write-Host "Talk track: 'Now imagine a change ships that lets the agent recalculate and LOWER the" -ForegroundColor DarkGray
Write-Host "approved risk score. I flip one environment flag to simulate that bad change.'" -ForegroundColor DarkGray
Pause-Demo "Press Enter to inject the fault and re-run"
$env:EVAL_DEMO_BREAK = $Break
$rc = Invoke-Harness
Write-Host "`nexit code = $rc" -ForegroundColor $(if ($rc -eq 0) { "Green" } else { "Red" })
Write-Host "The gate FAILED and returned a non-zero exit code — in CI this blocks the merge/deploy." -ForegroundColor Yellow

Step "3/3  Remove the fault and re-run (expect PASS again, exit 0)"
Write-Host "Talk track: 'Revert the change and the gate is green again — nobody had to notice by eye.'" -ForegroundColor DarkGray
Pause-Demo "Press Enter to remove the fault and re-run"
Remove-Item Env:EVAL_DEMO_BREAK -ErrorAction SilentlyContinue
$rc = Invoke-Harness
Write-Host "`nexit code = $rc" -ForegroundColor $(if ($rc -eq 0) { "Green" } else { "Red" })

Write-Host "`nDemo complete. EVAL_DEMO_BREAK is cleared." -ForegroundColor Green
