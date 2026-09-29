# Agent Service — code-first multi-agent (Python, Foundry-ready)

The Discharge Transition Orchestrator and its specialist agents, implemented as a
code-first Python service. Runs locally with deterministic reasoning (no cloud needed) and
can call Microsoft Foundry models when configured. Fulfills the same
`/api/v1/agent/invoke` contract as the Node backend, so the UI and gateway are unchanged.

## Agents

| Agent | Responsibility |
| --- | --- |
| Discharge Transition Orchestrator | Coordinates specialists, preserves correlation ID, assembles the packet. |
| Case Context Agent | Redacted minimum-necessary context via `patient.get` / `utilization.history`. |
| Risk Score Agent | Consumes the approved score via `risk_score.get` (never generates it). |
| Evidence Retrieval Agent | Builds the RAG evidence packet via `protocol.search`; flags missing evidence. |
| Transition Exception Agent | Identifies incomplete transition elements. |
| Care Plan Drafting Agent | Drafts owner/due-time/task text (optionally model-refined). |
| Policy Guardrail Agent | Decides allow / review_required / escalate. |
| Human Review Agent | Creates the HITL review task via `task.create` and writes audit. |

## Run locally

```powershell
cd agent-service
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m uvicorn discharge_transition_agent.app:app --host 127.0.0.1 --port 8081
# http://127.0.0.1:8081/api/health
```

## Test

```powershell
.\.venv\Scripts\python.exe tests\test_contract.py   # contract + RAG retrieval (8 tests)
.\.venv\Scripts\python.exe tests\test_hitl.py       # durable HITL state machine (8 tests)
.\.venv\Scripts\python.exe tests\test_eval.py       # evaluation safety gates
.\.venv\Scripts\python.exe tests\test_manifests.py  # agents/ manifest <-> runtime conformance
# or: python -m pytest
```

## HITL review tasks (Data Task Scheduler gate)

Every `invoke` registers a durable review task. The store enforces the state machine
(`PendingReview → Approved / NeedsRework / Rejected`; policy escalation and SLA timeout →
`Escalated`), requires a human actor for approve/reject, and writes an append-only audit record per
transition (`hitl.py`). Endpoints:

| Method & path | Purpose |
| --- | --- |
| `GET /api/v1/tasks` | List review tasks (sweeps overdue first). |
| `GET /api/v1/tasks/{id}` | One task with full history. |
| `GET /api/v1/tasks/{id}/audit` | Just the audit trail. |
| `POST /api/v1/tasks/{id}/action` | `claim` / `approve` / `request_changes` / `reject` / `escalate` / `rework`. Body `{action, actor, note}`. |
| `POST /api/v1/tasks/sweep` | Force the timer→escalate sweep (demo fast-forward). |

The Durable Task Scheduler graduation target (Azure Functions + Agent Framework Durable Extension)
ships as reference code in `orchestrations/`. Full mapping: `docs/hitl-durable-task-scheduler.md`.

## Retrieval evaluation

`eval/` applies the GPT-RAG "measure retrieval before you tune" pattern locally — labeled qrels plus
a scorer (precision@k, recall@k, MRR) over the `KnowledgeBase`:

```powershell
.\.venv\Scripts\python.exe eval\evaluate_retrieval.py --split tune --k 3
```

See `eval/README.md` and `docs/rag-guidance-gpt-rag.md`.

## Use it from the Node backend

Point the backend at this service and it delegates `invoke` here (falling back to its local
stub on failure):

```powershell
# in the backend terminal
$env:AGENT_SERVICE_URL = "http://127.0.0.1:8081"
npm start
```

The backend sets an `x-agent-source` response header: `agent-service`, `local-fallback`, or `local`.

## Optional: Microsoft Foundry models (verified live)

Install the extra deps (or use the REST + `az` token path) and set the project + deployment to
let the drafting step call a Foundry model. The safety boundary is unchanged — the model only
rephrases draft lines (line-count guarded); it never generates a risk score, makes a clinical
determination, or approves anything.

Copy `.env.example` to `.env` (auto-loaded) or set env vars:

```
AZURE_AI_PROJECT_ENDPOINT=https://kaiser-foundry-resource.services.ai.azure.com/api/projects/workshop-demo-project
FOUNDRY_MODEL_DEPLOYMENT=gpt-5-mini
```

Then `az login` and run. The client uses two paths automatically:
1. **SDK** (`azure-ai-projects` + `azure-identity`) — best in containers with managed identity.
2. **REST + `az` token** (stdlib only) — works on dev machines where the SDK can't build.

Verify connectivity:

```powershell
.\.venv\Scripts\python.exe scripts\foundry_smoke.py
```

## Deploy to Foundry (hosted agent)

`azure.yaml` declares this folder as a Foundry hosted agent for `azd`. The same app runs locally
(deterministic, offline) and hosted; the invoke contract does not change. Full deploy path,
prerequisites, and no-secrets configuration: **`docs/foundry-hosted-agent.md`**. Azure + Foundry
provisioning is in `infra/README.md`.

## Agent manifests & conformance

The 7 specialist agents are declared in `agents/*/agent.yaml`. `agent_manifests.py` checks the
manifests match the running orchestrator (no drift), covered by `tests/test_manifests.py`, and
`GET /api/v1/agents` reports the declared set + any conformance issues.

## Contract

Request `{ "caseId": "P0147", "actorRole": "care-manager" }` → the InvokeResult documented in
`backend/README.md`. Every response carries `x-correlation-id`.
