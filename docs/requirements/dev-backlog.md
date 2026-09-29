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

## WI-04 — RAG evidence packet builder  [DONE]  (tag: chapter-04-rag)
Implemented in the Python agent service: `agent-service/src/discharge_transition_agent/knowledge.py`
reads `data/rag-docs/`, retrieves claim-level citations, scores confidence, keeps diagnosis-specific
docs from leaking across diagnoses, and flags a missing specialty protocol so the workflow escalates.
Wired through the `protocol.search` tool and the Evidence Retrieval Agent.
**Acceptance met:** golden case cites real docs; missing-protocol (pneumonia) escalates, not guesses.
Covered by tests in `agent-service/tests/test_contract.py`.

## WI-04b — RAG best practices + retrieval evaluation  [DONE]  (tag: chapter-04-rag)
Deep-scanned the Azure GPT-RAG accelerator and captured KP-facing patterns in
`docs/rag-guidance-gpt-rag.md` (grounding approaches, OBO permission trimming, governance
checklist, telemetry, "measure retrieval before you tune"). Built a working local retrieval
evaluation harness at `agent-service/eval/` (`qrels.jsonl` rubric 0-4 with tune/held_out splits +
`evaluate_retrieval.py` computing precision@k, recall@k, MRR, with an optional gate).
**Acceptance met:** eval runs on both splits (tune P@3 ≈ 0.78, held_out ≈ 0.67, MRR 1.0);
retrieval quality locked by `test_retrieval_ranks_specialty_first`.

## WI-05 — HITL state machine + persistence (Data Task Scheduler)  [DONE]  (tag: chapter-05-hitl)
Durable review-task store backs the approve/rework/reject actions with the full state machine in
`hitl/state-machine.md`. Implemented in both services with an identical contract:
`agent-service/src/discharge_transition_agent/hitl.py` (file-backed, thread-safe) and
`backend/src/hitl/taskStore.js` (Node mirror, source of truth on the app path). Endpoints:
`GET /api/v1/tasks`, `GET /api/v1/tasks/:id`, `GET /api/v1/tasks/:id/audit`,
`POST /api/v1/tasks/:id/action`, `POST /api/v1/tasks/sweep`. Every invoke registers a task; policy
escalations create the task already `Escalated`; overdue tasks auto-escalate on sweep (timer branch).
The UI action buttons call the API and reflect the returned state, with an offline fallback.
The **Durable Task Scheduler** graduation target ships as reference code in
`agent-service/orchestrations/` (`function_app.py` + `client_raise_event.py`) with the mapping doc
`docs/hitl-durable-task-scheduler.md`.
**Acceptance met:** illegal transitions -> 409; approve/reject without a human actor -> 403; every
transition writes an audit record. Covered by `agent-service/tests/test_hitl.py` (8 tests).

## WI-06 — Observability events + trace endpoint  [DONE]  (tag: chapter-06-observability)
Emit the custom event taxonomy to a structured store and add `GET /api/v1/traces/:correlationId`
that returns the ordered events for a run.
**Acceptance met:** a single invoke produces a complete, ordered, correlated event list (verified:
19-event trace across run.started → 6 tool.called → 8 agent.handoff → policy.decision →
run.completed → review.created → review.transition).

**Activity feed (live UI preview):**
- `backend/src/logs/logBuffer.js` — dependency-free ring buffer (last 200) with incremental
  `list(sinceSeq, limit)`; `GET /api/v1/logs?since=&limit=` (`routes/logs.js`).
- Structured invoke/HITL events + HTTP mirror (clean, no ANSI) + rejected transitions as `warn`.
- UI: full-width "Backend activity log" panel polling every 2s, color-coded, live/offline badge.

**Correlation trace (acceptance surface):**
- `backend/src/observability/traceStore.js` — per-correlation-ID ordered event store with a stable
  taxonomy: `run.started`, `tool.called` (name/decision/latency), `agent.handoff`, `policy.decision`,
  `run.completed`, `review.created`, `review.transition`. Capped at 200 runs.
- `GET /api/v1/traces` (list) and `GET /api/v1/traces/:id` (full ordered events; 404 if unknown),
  wired from the invoke route (all 3 paths) and the HITL action route.
- Tests: `backend/test/traceStore.test.js` (5, `npm test` via `node --test`).
- Doc: `docs/observability-correlation-trace.md` (taxonomy, demo script, App Insights/LAW graduation
  with the correlation ID as the KQL pivot; notes the buffer is process-local, not durable).

**Follow-up (done):**
- Each activity-log line with a correlation ID shows a **trace ↗** link; clicking it opens a right-side
  drawer rendering the full ordered event list from `GET /api/v1/traces/:id`
  (`app/readmission-review-tracker`, `fetchTrace` + `describeTraceEvent`). Verified live.

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
