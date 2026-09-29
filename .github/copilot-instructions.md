# GitHub Copilot Instructions — Kaiser Discharge Transition Exception Coordinator Workshop

These instructions ground GitHub Copilot (chat, agent, and plan mode) for this repository.
Read this file fully before generating code, plans, or edits.

## What this repository is

A two-day onsite workshop reference implementation for Kaiser Permanente teams. It teaches
secure, governed, observable healthcare **agent** patterns on Microsoft Foundry. The running
use case is a **Discharge Transition Exception Coordinator**.

This is a **teaching/reference implementation with synthetic data**, not a production clinical
system and not clinical guidance.

## The use case (do not drift from this)

A care manager or ADT nurse reviews tomorrow's synthetic discharge-candidate list. The agent:

1. Assembles minimum-necessary case context.
2. **Consumes** an approved risk score from a deterministic tool (`risk_score.get`).
3. Retrieves effective-dated transition protocols (RAG).
4. Identifies incomplete discharge-transition elements ("transition gaps").
5. Drafts an exception packet with proposed owners and due times.
6. Stops at a human approval gate (HITL).
7. Emits audit + observability signals.

## Hard safety boundary (enforce in code, not just prompts)

The system may draft, cite, propose owners, and create review tasks. It must **never**:

1. Decide discharge readiness or state a patient is "safe to discharge".
2. Make a clinical determination or interpret clinical significance of pending results.
3. Change discharge, medication, or treatment orders.
4. **Generate, infer, recalculate, or override** the approved risk score.
5. Send patient-facing content or execute patient-impacting actions without human approval.

If a requested change would violate these, stop and flag it instead of implementing it.

## Architecture (target)

```
React UI  ->  Backend API  ->  Foundry Hosted Agent (Discharge Transition Orchestrator)
                                  -> Case Context Agent
                                  -> Risk Score Agent      (risk_score.get)
                                  -> Evidence Retrieval Agent (Foundry IQ / RAG)
                                  -> Transition Exception Agent
                                  -> Care Plan Drafting Agent
                                  -> Policy Guardrail Agent
                                  -> Human Review Agent
                              ->  MCP tools -> mock EHR / risk service / KB / HITL / audit
                              ->  App Insights + Log Analytics
```

Today the multi-agent workflow can run two ways, both behind the same `/api/v1/agent/invoke`
contract: (1) a **local orchestrator stub** in `backend/` (Node), and (2) a **code-first Python
agent service** in `agent-service/` (orchestrator + 7 specialists, Foundry-ready). Set
`AGENT_SERVICE_URL` on the backend to delegate to the Python agents. Either can be replaced by a
real Foundry hosted agent later without changing the contract.

## Tech stack and locations

| Area | Stack | Location |
| --- | --- | --- |
| Frontend | React 19 + TypeScript + Vite | `app/readmission-review-tracker/` |
| Backend | Node.js + Express (CommonJS) | `backend/` |
| Agents | Manifest YAML + prompts | `agents/` |
| Agent service | Python code-first multi-agent (FastAPI) | `agent-service/` |
| MCP tools | JSON Schemas | `mcp-server/tool-contracts/` |
| RAG sources | Markdown | `data/rag-docs/` |
| Policy/guardrails | Markdown | `policy/` |
| Governance | YAML + Markdown | `governance/` |
| Observability | Markdown + KQL | `observability/`, `fabric/kql/` |
| Evaluation | JSONL + Markdown | `evaluation/` |
| Infrastructure | Terraform + PowerShell | `infra/terraform/`, `infra/scripts/` |
| Requirements | Markdown | `docs/requirements/` |

## API contract (do not break)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Liveness. |
| GET | `/api/v1/cases` | Case worklist. |
| GET | `/api/v1/cases/:id` | Case payload. |
| POST | `/api/v1/agent/invoke` | Run workflow; returns the exception packet. |

Every request/response carries `x-correlation-id`. The invoke response shape is defined in
`backend/README.md` and consumed by `app/readmission-review-tracker/src/api.ts`. If you change
this shape, update both sides and the requirements docs in the same change.

## Coding conventions

1. Keep the frontend React + TypeScript; keep the backend CommonJS Express.
2. No secrets in code, prompts, or committed files. Synthetic data only.
3. Preserve `x-correlation-id` propagation across every new endpoint and agent hop.
4. Every tool call and policy decision should be observable (name, decision, latency).
5. Keep tools narrowly scoped; PHI-minimizing defaults (redacted/aggregate) unless an
   explicit logged scope is present.
6. Prefer small, testable modules per agent/tool so each can be demoed independently.
7. Match existing file/naming patterns; do not restructure folders without cause.

## Validation (run before declaring a task done)

```powershell
# Repo scaffold + safety-string check
.\scripts\validate.ps1

# Frontend build (type-check + bundle)
cd app\readmission-review-tracker; npm run build

# Backend smoke test
cd backend; npm install; npm start   # then GET /api/health returns 200
```

Do not commit generated artifacts: `node_modules/`, `dist/`, `*.tsbuildinfo`,
`vite.config.js`, `vite.config.d.ts`.

## Working agreement with the human

- Scout (a separate assistant) orchestrates workshop content, sequencing, and requirements.
- GitHub Copilot handles delegated **development** tasks in VS Code.
- Pick up work items from `docs/requirements/dev-backlog.md`.
- Follow the chapter/checkpoint delivery model in `docs/chapter-delivery-model.md`.
- When a task is ambiguous or would cross the safety boundary, ask before proceeding.
