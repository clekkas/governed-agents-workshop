# GitHub Copilot Agent / Plan Mode — Prompts

Copy-paste prompts for VS Code + GitHub Copilot **Agent mode** (and its plan step). Copilot
auto-reads `.github/copilot-instructions.md`, so these prompts stay short and point at backlog
items and requirements. Always review the generated **plan** before letting Agent mode execute.

## How to use

1. Open the repo folder `kaiser-readmissions-agent-workshop` in VS Code.
2. Open Copilot Chat, switch to **Agent** mode.
3. Add context if prompted: `.github/copilot-instructions.md`,
   `docs/requirements/`, and the folder for the work item (`backend/`, `app/`, etc.).
4. Paste the prompt for the work item.
5. Read the proposed plan. Confirm it respects the API contract and safety boundary. Then run it.
6. After it finishes, run validation (below) and review the diff.

## Standard preamble (optional, prepend to any prompt)

```
Follow .github/copilot-instructions.md and docs/requirements/ for this repo. Do not break the
/api contract or the safety boundary. Synthetic data only, no secrets. When done, run the
validation commands and summarize the diff. If anything is ambiguous or would cross the safety
boundary, stop and ask.
```

## Per-work-item prompts

### WI-01 — Backend endpoint tests
```
Plan and implement WI-01 in docs/requirements/dev-backlog.md. Add node:test coverage for the
backend endpoints in backend/, including 200/404/400 paths and the P0310 escalate case. No new
heavy dependencies. Update backend/README.md with how to run the tests.
```

### WI-02 — MCP tool contract validation
```
Plan and implement WI-02. Validate each mock tool output in backend/src/orchestrator/mockTools.js
against the JSON schemas in mcp-server/tool-contracts/. Add an npm script and wire it into the
repo validation. Fail loudly on schema drift.
```

### WI-03 — Policy/guardrail enforcement module
```
Plan and implement WI-03. Extract policy checks into backend/src/orchestrator/policy.js covering
every row in policy/guardrail-test-matrix.md. Return structured policy decisions and add tests
asserting each decision. Do not weaken any prohibited-claim or HITL-bypass rule.
```

### WI-04 — RAG evidence packet builder
```
Plan and implement WI-04. Build an evidence-packet module that reads data/rag-docs/, returns
claim-level citations, and flags missing/conflicting evidence per docs/rag-development-patterns.md.
A missing specialty protocol must escalate to human review, never fabricate guidance.
```

### WI-05 — HITL state machine + persistence
```
Plan and implement WI-05. Back review actions with the state machine in hitl/state-machine.md and
an in-memory task store. Add endpoints for review actions, reject invalid transitions, and write an
audit event on every transition. Update the UI review actions to call these endpoints.
```

### WI-06 — Observability events + trace endpoint
```
Plan and implement WI-06. Emit the custom event taxonomy from docs/requirements/technical-requirements.md
to a structured log, propagate x-correlation-id, and add a dev-only GET /api/v1/traces/:correlationId
returning the ordered events for a run.
```

### WI-07 — Evaluation harness runner
```
Plan and implement WI-07. Add a runner that executes evaluation/golden-cases.jsonl and
evaluation/adversarial-cases.jsonl against POST /api/v1/agent/invoke and asserts the expectations.
The adversarial risk-score-override case must fail closed (agent refuses).
```

### WI-08 — Foundry hosted agent scaffold
```
Plan WI-08 only (do not deploy). Scaffold a code-first Microsoft Foundry hosted agent that fulfills
the same /api/v1/agent/invoke contract using the specialist manifests in agents/. Keep the local
orchestrator as offline fallback. List the deploy steps but do not run any cloud deployment; I will
coordinate that separately.
```

## Validation to run after any item

```powershell
.\scripts\validate.ps1
cd app\readmission-review-tracker; npm run build; cd ..\..
cd backend; npm start   # confirm GET /api/health = 200, then stop
```

## Guardrails for Agent mode

- Never let Agent mode invent a risk score, remove a HITL gate, or add a "safe to discharge" path.
- Never commit `node_modules/`, `dist/`, `*.tsbuildinfo`, or secrets.
- Keep each session scoped to one work item / one chapter checkpoint.
- If the plan proposes broad refactors or folder moves, decline and narrow the scope.
