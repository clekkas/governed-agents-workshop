# MCP Server

This folder defines the governed tool boundary for the workshop. Implementation will be added after the target runtime and BYO Registry sample are incorporated.

## Tool contracts

`tool-contracts/*.schema.json` are the JSON Schemas for each governed tool's invocation arguments.

Validate that the arguments the agent sends to each tool conform to its contract (and that the
validator catches drift):

```powershell
node mcp-server/validate-contracts.js
# or, from the backend folder: npm run validate:contracts
```

The validator is dependency-free, runs a drift self-test (a broken invocation must be rejected), and
is wired into `scripts/validate.ps1`. It fails loudly (non-zero exit) on any schema drift.

