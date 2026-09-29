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

## WI-01 — Backend endpoint tests  [DONE]  (tag: chapter-01-backend-tests)
`backend/test/endpoints.test.js` (Node built-in `node:test`, no deps) covers health, cases list/get
(200 + 404), invoke (200 + `requiresHumanReview`, 400 on missing caseId, 404 unknown, P0310
`escalate`) and `x-correlation-id`. App only binds a port under `require.main === module` so tests
mount it on an ephemeral port. `npm test` runs all backend tests; documented in `backend/README.md`.

## WI-02 — MCP tool contract validation  [DONE]  (tag: chapter-02-mcp-validate)
`mcp-server/validate-contracts.js` (dependency-free minimal JSON Schema validator) checks the
canonical invocation for each tool against `mcp-server/tool-contracts/*.schema.json`, runs a drift
self-test (a broken invocation for every tool MUST be rejected), and cross-checks every implemented
mock tool has a schema. Wired into `scripts/validate.ps1` and `npm run validate:contracts`.
**Acceptance met:** fails loudly (non-zero exit) on drift — verified across enum, maximum,
extra-property, missing-required, and nested-item violations.

## WI-03 — Policy/guardrail enforcement module  [DONE]  (tag: chapter-03-guardrails)
`backend/src/orchestrator/policy.js` centralizes the guardrail matrix: request/output screens
(`screenText` → prohibited claim, order/medication change, HITL bypass, prompt injection) and
run-condition checks (missing citation, PHI scope, evidence conflict), plus `decide(run)` returning a
structured `{decision, code, reason, blocking}`. The orchestrator now calls `policy.decide(...)`.
**Acceptance met:** every matrix row has a check + a test (`backend/test/policy.test.js`, 12 tests).

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

## WI-07 — Evaluation harness runner  [DONE]  (tag: chapter-07-eval)
Runner `agent-service/eval/evaluate_agent.py` executes `evaluation/golden-cases.jsonl` and
`evaluation/adversarial-cases.jsonl` against the orchestrator and asserts the passing gates from
`evaluation/evaluation-plan.md` on the structured invoke result (deterministic, offline, no LLM
judge). The JSONL cases carry a `caseId` and a `checks` list; checks are `cites_evidence`,
`discloses_missing_or_cites`, `routes_to_human_review`, `risk_score_consumed`, `no_prohibited_claim`,
`phi_minimized`, `no_autonomous_approval`, `escalates_when_missing`.
**Acceptance met:** reports pass/fail per case (6/6, 28/28 checks); exits non-zero on any failure;
the critical adversarial risk-score-override case (adv-003) is verified fail-closed (score consumed
unchanged with `risk_score.get` provenance — the agent has no path to regenerate it). `--json` for a
machine-readable summary. Covered by `agent-service/tests/test_eval.py` (incl. a broken-result
negative test) and run as a stage in `scripts/validate-solution.ps1`.

## WI-08 — Foundry hosted agent scaffold  [DONE]  (tag: chapter-08-foundry)
The code-first agent service already fulfills the invoke contract; WI-08 ties the declared agents to
the running code and documents the deploy path. Added `agent_manifests.py` (dependency-free reader +
`check_conformance()`), a canonical runtime registry (`SPECIALIST_CLASSES/NAMES`, `manifest_id`) in
`specialists.py`, `GET /api/v1/agents` (declared set + drift), and `tests/test_manifests.py` (3
tests). Fixed real drift: the orchestrator manifest was missing `care-plan-drafting-agent`. Deploy
guide in `docs/foundry-hosted-agent.md` (azd + container-sidecar paths, contract stability table,
managed-identity/no-keys config). `azure.yaml` unchanged; local orchestrator remains the offline
fallback. Wired conformance into `scripts/validate-solution.ps1`.
**Acceptance met:** same request/response contract; documented deploy path; no secrets committed
(`.env` gitignored; `.env.example` sub/tenant IDs replaced with placeholders; secret scan clean).
Coordinate with the workshop owner before any cloud deployment.

## WI-09 — CI/CD (staged hybrid: local → GitHub Actions)  [IN PROGRESS]  (tag: chapter-cicd)
Staged-hybrid Terraform execution: local apply now, GitHub Actions as the destination.
**Authored (ready to run):**
- `.github/workflows/ci.yml` — app build + tests (backend `node --test`, MCP contracts, UI build,
  agent-service tests + eval gate); no cloud.
- `.github/workflows/terraform-plan.yml` — PR `plan` (OIDC, remote backend via `-backend-config`,
  fmt/validate/plan to the job summary).
- `.github/workflows/terraform-apply.yml` — gated `apply` on the `production` environment (OIDC).
- `infra/scripts/bootstrap-remote-state.ps1` + `setup-github-oidc.ps1` — one-time Stage-2 bootstrap
  (remote state storage + keyless GitHub→Azure federation), plus `infra/terraform/backend.tf.example`.
- `infra/DEPLOYMENT.md` — the three-stage guide; `.gitignore` covers `backend.tf`/plan artifacts.
**Remaining (needs the user):** connect a remote GitHub repo; run the Stage-2 bootstrap scripts; set
the repo secrets/variables + `production` environment reviewers; then push to activate the workflows.
Workflow YAML validated (parses); live CI runs require the remote repo.

---

## Rules for every work item

1. Do not break the API contract without updating `backend/README.md`, `src/api.ts`, and the
   requirements docs in the same change.
2. Preserve the safety boundary (see `.github/copilot-instructions.md`).
3. Run validation: `scripts/validate.ps1`, frontend `npm run build`, backend smoke test.
4. Keep changes small and demoable; align to one chapter checkpoint.
5. Synthetic data only; no secrets.
