# Backend API — Discharge Transition Exception Coordinator

Node.js + Express backend skeleton for the workshop use case.

This is a **workshop backend**. It delegates the multi-agent workflow to the Python agent service
(`AGENT_SERVICE_URL`) and falls back to a local in-process orchestrator when that service is
unavailable, so the UI always has a working end-to-end path. It also hosts the HITL review-task
store, the activity-log feed, and the correlation-trace store. In later chapters the agent runtime is
a Microsoft Foundry hosted agent + MCP tool calls without changing the API contract.

## Run

```powershell
cd backend
npm install
npm start
```

The server listens on `http://127.0.0.1:8080` by default (override with `PORT`).

## Test

Tests use Node's built-in runner (`node:test`) — no external dependencies. The Express app only
binds a port when run directly, so tests mount it on an ephemeral port.

```powershell
cd backend
npm test        # node --test
```

Covers: health, cases list/get (200 + 404), invoke (200 with `requiresHumanReview`, 400 on missing
`caseId`, 404 on unknown case, P0310 `escalate`), and the correlation trace store.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/health` | Liveness probe. No auth. |
| GET | `/api/v1/cases` | List synthetic discharge-transition cases. |
| GET | `/api/v1/cases/:id` | Get one case payload envelope. |
| POST | `/api/v1/agent/invoke` | Run the orchestrator for a case and return the exception packet. |
| GET/POST | `/api/v1/tasks…` | HITL review tasks (list, get, audit, action, sweep). |
| GET | `/api/v1/logs` | Recent backend activity feed. |
| GET | `/api/v1/traces/:id` | The complete ordered event trace for one correlation ID. |

Every request/response carries an `x-correlation-id` header. Provide your own to trace a
workflow end to end, or the server generates one.

## Request envelope (POST /api/v1/agent/invoke)

```json
{
  "caseId": "P0147",
  "actorRole": "care-manager"
}
```

## Response shape

```json
{
  "correlationId": "trace-...",
  "caseId": "P0147",
  "summary": "string",
  "approvedRiskScore": { "tier": "High", "score": 0.82, "provenance": "risk_score.get ..." },
  "transitionGaps": ["string"],
  "missingInformation": ["string"],
  "evidence": [{ "source": "string", "citation": "string", "claim": "string" }],
  "draftExceptionPacket": ["string"],
  "toolCalls": [{ "name": "patient.get", "decision": "redact", "latencyMs": 118 }],
  "agentHandoffs": [{ "agentName": "string", "status": "string", "summary": "string" }],
  "policyDecision": "review_required",
  "requiresHumanReview": true
}
```

## Safety boundary

The backend never returns a discharge decision, a clinical determination, or a
generated risk score. The risk score is deterministic tool output with provenance.
