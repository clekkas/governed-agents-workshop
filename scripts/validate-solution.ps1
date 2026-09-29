# Full-solution local validation.
# Runs repo scaffold validation, the frontend production build, and a backend smoke test.
# Exit code is non-zero if any stage fails.

$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\.."
$failures = @()

function Section($name) { Write-Host "`n=== $name ===" -ForegroundColor Cyan }

# 1. Repo scaffold + safety-string validation.
Section "Repo scaffold validation"
try {
  & "$root\scripts\validate.ps1"
  if ($LASTEXITCODE -ne 0) { throw "validate.ps1 exit $LASTEXITCODE" }
} catch {
  $failures += "Repo scaffold: $($_.Exception.Message)"
}

# 2. Frontend production build (type-check + bundle).
Section "Frontend build"
$ui = Join-Path $root "app\readmission-review-tracker"
try {
  Push-Location $ui
  if (-not (Test-Path "node_modules")) { npm install | Out-Host }
  npm run build | Out-Host
  if ($LASTEXITCODE -ne 0) { throw "npm run build exit $LASTEXITCODE" }
  Remove-Item -Force -ErrorAction SilentlyContinue `
    "tsconfig.tsbuildinfo","tsconfig.node.tsbuildinfo","vite.config.js","vite.config.d.ts"
} catch {
  $failures += "Frontend build: $($_.Exception.Message)"
} finally {
  Pop-Location
}

# 3. Backend smoke test — start server, hit key endpoints, stop.
Section "Backend smoke test"
$backend = Join-Path $root "backend"
$proc = $null
try {
  Push-Location $backend
  if (-not (Test-Path "node_modules")) { npm install | Out-Host }
  $env:PORT = "8099"
  $proc = Start-Process -FilePath "node" -ArgumentList "src/index.js" -PassThru -WindowStyle Hidden
  Start-Sleep -Seconds 3

  $health = Invoke-RestMethod -Uri "http://127.0.0.1:8099/api/health"
  if ($health.status -ne "ok") { throw "health not ok" }

  $cases = Invoke-RestMethod -Uri "http://127.0.0.1:8099/api/v1/cases"
  if (-not $cases.cases -or $cases.cases.Count -lt 1) { throw "no cases returned" }

  $invoke = Invoke-RestMethod -Uri "http://127.0.0.1:8099/api/v1/agent/invoke" -Method Post `
    -ContentType "application/json" -Body '{"caseId":"P0147"}'
  if (-not $invoke.requiresHumanReview) { throw "invoke did not require human review" }

  $escalate = Invoke-RestMethod -Uri "http://127.0.0.1:8099/api/v1/agent/invoke" -Method Post `
    -ContentType "application/json" -Body '{"caseId":"P0310"}'
  if ($escalate.policyDecision -ne "escalate") { throw "P0310 did not escalate (got $($escalate.policyDecision))" }

  Write-Host "Backend smoke test passed." -ForegroundColor Green
} catch {
  $failures += "Backend smoke: $($_.Exception.Message)"
} finally {
  if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
  Pop-Location
}

# 3b. Agent evaluation harness — golden + adversarial safety gates (if the venv is present).
Section "Agent evaluation harness"
$agent = Join-Path $root "agent-service"
$venvPy = Join-Path $agent ".venv\Scripts\python.exe"
if (Test-Path $venvPy) {
  try {
    Push-Location $agent
    & $venvPy "eval\evaluate_agent.py" | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "evaluate_agent.py exit $LASTEXITCODE (a safety gate failed)" }
    Write-Host "Evaluation harness passed." -ForegroundColor Green
  } catch {
    $failures += "Eval harness: $($_.Exception.Message)"
  } finally {
    Pop-Location
  }
} else {
  Write-Host "Skipped: agent-service\.venv not found (run pip install -r requirements.txt)." -ForegroundColor Yellow
}

# Summary + exit code.
Section "Result"
if ($failures.Count -eq 0) {
  Write-Host "Full-solution validation PASSED." -ForegroundColor Green
  exit 0
} else {
  Write-Host "Full-solution validation FAILED:" -ForegroundColor Red
  $failures | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
  exit 1
}
