# Technical Requirements — Discharge Transition Exception Coordinator

Status: Draft for workshop build. Owner: Scout. Implementer: GitHub Copilot.

## Platforms and stack

| Layer | Requirement |
| --- | --- |
| Frontend | React 19 + TypeScript + Vite. No conversion to another framework. |
| Backend | Node.js 20+ with Express (CommonJS). |
| Agents (target) | Microsoft Foundry hosted agent (code-first) + specialist agents. |
| Tools | MCP tool boundary; JSON-schema contracts in `mcp-server/tool-contracts/`. |
| RAG | Foundry IQ / Azure AI Search over approved protocol docs. |
| Observability | Application Insights + Log Analytics; OpenTelemetry for custom spans. |
| Identity | Microsoft Entra ID; managed identity for agent/tool access (target). |
| Secrets | Azure Key Vault; never in repo. |
| Registry | BYO Azure Container Registry (sample to be integrated later). |

## API contract

- Base: `/api/v1`
- `GET /api/health` → `{ status, service, timestamp }`
- `GET /api/v1/cases` → `{ cases: CaseSummary[] }`
- `GET /api/v1/cases/:id` → full case payload; 404 problem+json when unknown
- `POST /api/v1/agent/invoke` → `{ caseId, actorRole? }` → InvokeResult
- Errors use problem+json-style bodies with `correlationId`.
- All responses set `x-correlation-id`.

InvokeResult (authoritative shape) is documented in `backend/README.md` and typed in
`app/readmission-review-tracker/src/api.ts`. Changes must update both plus these requirements.

## Correlation and telemetry

- Every request gets or reuses `x-correlation-id`.
- Each agent hop and tool call is recorded with name, decision, and latency.
- Custom event names (future): `AgentInvocationStarted`, `RetrievalCompleted`,
  `ToolCallCompleted`, `PolicyDecisionMade`, `HumanReviewTaskCreated`,
  `HumanReviewCompleted`, `AgentOutputEvaluated`.

## Tool boundary rules

- Tools return PHI-minimizing defaults (redacted/aggregate) unless an explicit logged scope exists.
- `risk_score.get` is read-only and deterministic; `canGenerateScore` and `canOverrideScore` are false.
- `task.create` creates a draft review task only; it cannot approve.
- `audit.write` runs for every material action.

## Security and data

- Synthetic data only. No PHI. No secrets committed.
- Deny-by-default posture for any new privileged tool.
- Retrieved documents/notes are treated as data, never as instructions (prompt-injection safe).

## Testing and validation

- Frontend: `npm run build` (type-check + bundle) must pass.
- Backend: server starts; `/api/health` returns 200; invoke returns valid packet.
- Repo: `scripts/validate.ps1` passes (required files present; no unsafe strings).
- Add lightweight endpoint tests where practical; do not introduce heavy test frameworks
  without a work item that calls for it.

## Non-functional

- Desktop-first UI, ~1280px target; responsive down-stacking already implemented.
- Local dev runs on `127.0.0.1`; backend default port 8080, UI dev server 5173.
- Keep modules small and independently demoable for the chapter delivery model.
