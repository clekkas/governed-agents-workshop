# Development Backlog — delegated to GitHub Copilot

Scout (workshop orchestrator) maintains this backlog. GitHub Copilot implements items in VS Code.
Work top-to-bottom unless Scout re-prioritizes. Each item has acceptance criteria and a suggested
git checkpoint tag (see `docs/chapter-delivery-model.md`).

Status legend: TODO / IN PROGRESS / DONE / BLOCKED.

---

## DONE (already implemented)

- Frontend UI (React + TS + Vite) with single/batch modes, citation focus, payload/raw views.
- Backend API skeleton (health, cases, agent invoke) with local orchestrator stub.
- UI wired to backend with live/offline fallback.

---

## WI-01 — Backend endpoint tests  [TODO]  (tag: chapter-01-backend-tests)
Add a minimal Node test (built-in `node:test`) covering health, cases list/get (200 + 404),
and invoke (200 + 400 on missing caseId, correct `policyDecision` for P0310).
**Acceptance:** `node --test` passes; no new heavy deps; documented in `backend/README.md`.

## WI-02 — MCP tool contract validation  [TODO]  (tag: chapter-02-mcp-validate)
Add a script that validates each mock tool's output against the JSON schema in
`mcp-server/tool-contracts/`. Wire it into `scripts/validate.ps1` or an npm script.
**Acceptance:** validation fails loudly if a tool output drifts from its schema.

## WI-03 — Policy/guardrail enforcement module  [TODO]  (tag: chapter-03-guardrails)
Extract policy checks from the orchestrator into `backend/src/orchestrator/policy.js` implementing
the guardrail matrix in `policy/guardrail-test-matrix.md` (prohibited claims, PHI, citation
required, HITL bypass). Return structured policy decisions.
**Acceptance:** each row in the matrix has a corresponding check + a test asserting the decision.

## WI-04 — RAG evidence packet builder  [TODO]  (tag: chapter-04-rag)
Implement an evidence-packet builder that reads `data/rag-docs/`, returns claim-level citations,
and flags missing/conflicting evidence per `docs/rag-development-patterns.md`.
**Acceptance:** golden case cites real docs; a missing-protocol case escalates, not guesses.

## WI-05 — HITL state machine + persistence  [TODO]  (tag: chapter-05-hitl)
Back the review actions (approve/rework/reject) with the state machine in `hitl/state-machine.md`
and an in-memory task store exposed via new endpoints (e.g. `POST /api/v1/tasks/:id/action`).
Emit audit events per transition.
**Acceptance:** invalid transitions are rejected; every transition writes an audit record.

## WI-06 — Observability events + trace endpoint  [TODO]  (tag: chapter-06-observability)
Emit the custom event taxonomy (see technical requirements) to a local structured log and add a
dev-only `GET /api/v1/traces/:correlationId` that returns the ordered events for a run.
**Acceptance:** a single invoke produces a complete, ordered, correlated event list.

## WI-07 — Evaluation harness runner  [TODO]  (tag: chapter-07-eval)
Add a runner that executes `evaluation/golden-cases.jsonl` and `evaluation/adversarial-cases.jsonl`
against the invoke endpoint and asserts expectations (cites evidence, escalates, refuses risk-score
recalculation, requires human review).
**Acceptance:** runner reports pass/fail per case; adversarial risk-score-override case must fail-closed.

## WI-08 — Foundry hosted agent scaffold  [TODO]  (tag: chapter-08-foundry)
Scaffold the code-first hosted agent that fulfills the same invoke contract, using the specialist
agent manifests in `agents/`. Keep the local orchestrator as the offline fallback.
**Acceptance:** same request/response contract; documented deploy path; no secrets committed.
Coordinate with Scout before any cloud deployment.

---

## Rules for every work item

1. Do not break the API contract without updating `backend/README.md`, `src/api.ts`, and the
   requirements docs in the same change.
2. Preserve the safety boundary (see `.github/copilot-instructions.md`).
3. Run validation: `scripts/validate.ps1`, frontend `npm run build`, backend smoke test.
4. Keep changes small and demoable; align to one chapter checkpoint.
5. Synthetic data only; no secrets.
