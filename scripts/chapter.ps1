# Mode 2 chapter switcher. Checks out a chapter checkpoint tag for delivery.
# Usage:
#   ./scripts/chapter.ps1 list                 # list chapter tags
#   ./scripts/chapter.ps1 chapter-02-mcp-validate
#   ./scripts/chapter.ps1 main                 # return to latest

param(
  [Parameter(Mandatory = $true)]
  [string]$Target
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\.."
Push-Location $root
try {
  if ($Target -eq "list") {
    Write-Host "Chapter checkpoint tags:" -ForegroundColor Cyan
    git tag --list "chapter-*" | Sort-Object
    return
  }

  if ($Target -eq "main") {
    git checkout main
    Write-Host "On main (latest)." -ForegroundColor Green
    return
  }

  # Guard against losing uncommitted work.
  $dirty = git status --porcelain
  if ($dirty) {
    Write-Host "Working tree is not clean. Commit or stash before switching chapters." -ForegroundColor Yellow
    git status --short
    exit 1
  }

  # Verify the tag exists.
  $exists = git tag --list $Target
  if (-not $exists) {
    Write-Host "Tag '$Target' not found. Run './scripts/chapter.ps1 list'." -ForegroundColor Red
    exit 1
  }

  git checkout $Target
  Write-Host "Checked out chapter checkpoint: $Target" -ForegroundColor Green
  Write-Host "Reminder: this is a detached checkpoint for demo. Return with './scripts/chapter.ps1 main'." -ForegroundColor DarkGray
} finally {
  Pop-Location
}
