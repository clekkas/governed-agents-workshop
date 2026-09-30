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
    Write-Host "[mcp] deploy: build + provision the hosted (internal-ingress) MCP server on Azure" -ForegroundColor Cyan
    Write-Host "      -> infra\scripts\deploy.ps1 -EnableMcpServer   (az acr build mcp-server/Dockerfile; terraform enable_mcp_server=true)"
    Write-Host "      -> internal Container App, http transport; agent routes via USE_EXTERNAL_MCP + MCP_SERVER_URL"
    Write-Host "      -> local/stdio still works: python mcp-server/server.py (MCP_TRANSPORT=stdio default)"
    Write-Host "      -> Work IQ (M365 context) attaches SEPARATELY: enable_workiq=true (Entra OBO, no app secret)"
  }
}
finally { Pop-Location }
