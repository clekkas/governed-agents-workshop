# Backend API — Discharge Transition Exception Coordinator

Node.js + Express backend skeleton for the workshop use case.

This is a **workshop skeleton**. The multi-agent workflow currently runs as a local
in-process orchestrator stub so the UI has a working end-to-end path. In later chapters
it is replaced by a Microsoft Foundry hosted agent + MCP tool calls without changing the
API contract.

## Run

```powershell
cd backend
npm install
npm start
```

The server listens on `http://127.0.0.1:8080` by default (override with `PORT`).

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/health` | Liveness probe. No auth. |
| GET | `/api/v1/cases` | List synthetic discharge-transition cases. |
| GET | `/api/v1/cases/:id` | Get one case payload envelope. |
| POST | `/api/v1/agent/invoke` | Run the local orchestrator stub for a case and return the exception packet. |

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
