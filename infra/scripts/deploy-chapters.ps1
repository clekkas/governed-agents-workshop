# Chapter deploy runner (master).
#
# For demo purposes: a single entry point that invokes per-capability CHILD runners in
# infra/scripts/chapters/ — one per workshop chapter / core capability. Mirrors the CI master
# workflow (.github/workflows/deploy-chapters.yml) so you can rehearse the same sequence offline.
#
# Each child runner is idempotent and has two modes:
#   -Validate (default): run the capability's checks only (no cloud, safe in the room).
#   -Deploy:             run the capability's deploy action (may touch Azure; gated).
#
# Examples:
#   .\deploy-chapters.ps1                      # validate every chapter, in order
#   .\deploy-chapters.ps1 -Chapters mcp,rag    # validate just MCP + RAG
#   .\deploy-chapters.ps1 -Chapters mcp -Deploy   # deploy the MCP capability

[CmdletBinding()]
param(
  # Which chapters to run, in order. Default = all. Names match chapters/deploy-<name>.ps1.
  [string[]]$Chapters = @("mcp", "rag", "guardrails", "hosted-agents", "observability", "hitl"),
  [switch]$Deploy,        # run child deploy actions instead of validate-only
  [switch]$ContinueOnError # keep going if a child fails (default: stop)
)

$ErrorActionPreference = "Stop"
$childDir = Join-Path $PSScriptRoot "chapters"
$mode = if ($Deploy.IsPresent) { "deploy" } else { "validate" }

Write-Host "== Chapter runner ($mode) ==" -ForegroundColor Cyan
Write-Host "Chapters: $($Chapters -join ', ')`n"

$results = @()
foreach ($ch in $Chapters) {
  $script = Join-Path $childDir "deploy-$ch.ps1"
  if (-not (Test-Path $script)) {
    Write-Host "SKIP  $ch  (no child runner: $script)" -ForegroundColor Yellow
    $results += [pscustomobject]@{ Chapter = $ch; Status = "skipped" }
    continue
  }

  Write-Host "---- $ch ----" -ForegroundColor Cyan
  try {
    & $script -Mode $mode
    Write-Host "OK    $ch`n" -ForegroundColor Green
    $results += [pscustomobject]@{ Chapter = $ch; Status = "ok" }
  }
  catch {
    Write-Host "FAIL  $ch : $($_.Exception.Message)`n" -ForegroundColor Red
    $results += [pscustomobject]@{ Chapter = $ch; Status = "failed" }
    if (-not $ContinueOnError.IsPresent) {
      $results | Format-Table -AutoSize
      throw
    }
  }
}

Write-Host "== Summary ==" -ForegroundColor Cyan
$results | Format-Table -AutoSize
if ($results.Status -contains "failed") { exit 1 }
