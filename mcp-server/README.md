# MCP Server

The governed tool boundary for the discharge-transition agent — now with a **real, runnable MCP
server** in addition to the contracts.

## What's here

| File | Purpose |
| --- | --- |
| `tool-contracts/*.schema.json` | JSON Schemas for each governed tool's invocation arguments |
| `validate-contracts.js` | Dependency-free contract validator + drift self-test (wired into CI) |
| `governed_tools.py` | Pure, dependency-free governed tool logic (decisions + contract enforcement) |
| `server.py` | Real MCP **stdio** server exposing the 7 tools (uses the `mcp` SDK) |
| `test_server.py` | Dependency-free behavior tests for `governed_tools.py` (CI-safe) |
| `connections/` | MCP client configs: our clinical server + Microsoft **Work IQ** |
| `requirements.txt` | Runtime dep for `server.py` (`mcp`) |

## The two-lane design

- **Clinical / PHI → this server.** Seven governed tools (`patient.get`, `notes.get`,
  `utilization.history`, `risk_score.get`, `protocol.search`, `task.create`, `audit.write`) with
  contracts, redaction, a read-only risk score, draft-only task creation, and always-on audit.
- **M365 work context → Work IQ.** Consumed as a *separate* governed MCP connection under the same
  Entra / on-behalf-of identity. We don't build it. See `docs/work-iq-overview.md` and
  `connections/README.md`.

## Run the server

```powershell
pip install -r mcp-server/requirements.txt
python mcp-server/server.py            # speaks MCP over stdio
```

> Note: `server.py` needs the `mcp` package (see `requirements.txt`). The governed logic and its
> tests are dependency-free and run without it. In some locked-down environments the `mcp` wheel
> chain (e.g. `cryptography`) may not build; the contract validator and `test_server.py` still run.

## Validate (what CI runs)

```powershell
node mcp-server/validate-contracts.js   # contract conformance + drift self-test
python mcp-server/test_server.py        # governed decisions + contract enforcement
```

## Wire into the agent

The agent-service uses the tools **in-process by default** (identical governed logic). To route
through this server instead, set `USE_EXTERNAL_MCP=1` — see
`agent-service/src/discharge_transition_agent/mcp_client.py`.

## Chapter deploy runner

This capability is deployed via the MCP chapter runner:

```powershell
infra\scripts\deploy-chapters.ps1 -Chapters mcp            # validate
infra\scripts\deploy-chapters.ps1 -Chapters mcp -Deploy    # deploy actions
```

or the reusable workflow `.github/workflows/deploy-mcp.yml` (called by `deploy-chapters.yml`).

