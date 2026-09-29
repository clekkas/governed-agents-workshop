# Discharge Transition Exception Coordinator

React UI artifact for the Kaiser readmissions agent workshop.

The app showcases the workshop use case: a care manager or ADT nurse reviews synthetic discharge-transition exceptions, sees an approved risk-score response, reviews cited evidence and transition gaps, and records a human review action. It must not provide autonomous clinical actions.

## What this UI demonstrates

1. Synthetic tomorrow-discharge candidate worklist.
2. Case summary and approved risk-score context (with provenance).
3. Retrieved evidence with citations.
4. Transition gaps, missing information, and guardrail state.
5. Draft exception packet requiring human review.
6. HITL actions: approve / request rework / reject, gated behind a required reviewer-name field; the
   backend enforces the state machine (illegal transitions and non-human approvals are rejected).
7. Observability: a live backend activity-log panel, and a clickable correlation ID that opens the
   full ordered trace for a run.

## Local development

The UI calls the backend at `/api/v1/*` and falls back to bundled sample data when the backend is
unreachable (offline workshop). For the live experience, run the backend (and optionally the Python
agent service) first — see the root `README.md`.

```powershell
npm install
npm run dev      # http://127.0.0.1:5173, proxies /api to the backend on :8080
```

Or let the backend serve the built UI as a single process (`npm run build`, then the backend serves
`dist/` at http://127.0.0.1:8080).

## Build

```powershell
npm run build
```

The UI is wired to the backend (`src/api.ts`) with a live/offline fallback. Later phases swap the
backend's local orchestrator for a Foundry hosted agent without changing the API contract.
