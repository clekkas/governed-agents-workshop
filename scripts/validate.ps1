$ErrorActionPreference = "Stop"

$root = Resolve-Path "$PSScriptRoot\.."
$required = @(
  "README.md",
  "SECURITY.md",
  "docs\architecture.md",
  "lab-guide\Module00_Introduction.md",
  "lab-guide\Module09_Evaluation_And_Release_Gates.md",
  "data\generate_synthetic_healthcare_data.py",
  "mcp-server\tool-contracts\patient.get.schema.json",
  "hitl\task-schema.json",
  "policy\prohibited-claims.md",
  "evaluation\judge-rubric.md"
)

foreach ($path in $required) {
  $full = Join-Path $root $path
  if (-not (Test-Path $full)) {
    throw "Missing required file: $path"
  }
}

$unsafeMatches = Get-ChildItem $root -Recurse -File |
  Where-Object {
    $_.FullName -notlike "*\.git\*" -and
    $_.FullName -notlike "*\node_modules\*" -and
    $_.FullName -notlike "*\dist\*" -and
    $_.FullName -ne $PSCommandPath
  } |
  Select-String -Pattern "deemed safe for discharge" -ErrorAction SilentlyContinue
if ($unsafeMatches) {
  throw "Unsafe sample phrase found in repository content."
}

# MCP tool contract validation (WI-02): fails loudly if a tool invocation drifts from its schema.
$contractValidator = Join-Path $root "mcp-server\validate-contracts.js"
if (Test-Path $contractValidator) {
  & node $contractValidator
  if ($LASTEXITCODE -ne 0) { throw "MCP contract validation failed." }
}

Write-Host "Repository scaffold validation passed."
