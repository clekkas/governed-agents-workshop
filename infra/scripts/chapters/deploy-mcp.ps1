# Chapter child runner: MCP server + tool boundary (Ch 2 / Ch 8).
[CmdletBinding()]
param([ValidateSet("validate", "deploy")][string]$Mode = "validate")
$ErrorActionPreference = "Stop"
$repo = Resolve-Path "$PSScriptRoot\..\..\.."

Write-Host "[mcp] validate: tool contracts + governed server logic"
Push-Location $repo
try {
  node mcp-server/validate-contracts.js
  python mcp-server/test_server.py
  if ($Mode -eq "deploy") {
    Write-Host "[mcp] deploy: publish governed MCP server (stdio) alongside the agent" -ForegroundColor Cyan
    Write-Host "      -> pip install -r mcp-server/requirements.txt; python mcp-server/server.py"
    Write-Host "      -> register mcp-server/connections/clinical.mcp.json in the client/Foundry project"
    Write-Host "      -> attach Work IQ separately via mcp-server/connections/workiq.mcp.json (Entra OBO, tenant sign-in)"
  }
}
finally { Pop-Location }
