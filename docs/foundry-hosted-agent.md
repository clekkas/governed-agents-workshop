# Foundry hosted agent — deploy path (WI-08)

The Discharge Transition Exception Coordinator is **code-first**: the same Python service
(`agent-service/`) runs locally (deterministic, offline) and deploys as a **Microsoft Foundry hosted
agent**. The invoke contract does not change — the local orchestrator is simply the offline fallback.

> Coordinate with the workshop owner before any cloud deployment. Synthetic data only.

## What "hosted agent" means here

- The agent runtime is the FastAPI app `discharge_transition_agent.app:app`, which serves
  `POST /api/v1/agent/invoke` and returns the shared `InvokeResult` contract.
- The orchestrator coordinates 7 specialist agents. Their **declared** manifests live in
  `agents/*/agent.yaml`; `agent_manifests.py` checks the manifests match the running code
  (`tests/test_manifests.py`), and `GET /api/v1/agents` reports the set + any drift.
- The Foundry model is used **only** to refine draft wording (`foundry.py`), never to generate a risk
  score, make a clinical determination, or bypass human review. With no model configured the service
  runs fully offline.

## Contract stability (local == hosted)

| | Local | Hosted (Foundry / container) |
| --- | --- | --- |
| Entry | `uvicorn discharge_transition_agent.app:app` | same app, `azure.yaml` module `discharge_transition_agent.app:app` |
| Invoke | `POST /api/v1/agent/invoke` | identical |
| Model | disabled → deterministic draft | `FOUNDRY_MODEL_DEPLOYMENT` via managed identity |
| Auth to model | `az` token (dev) | managed identity (`DefaultAzureCredential`) |

The Node backend reaches either one through `AGENT_SERVICE_URL` and falls back to its in-process
orchestrator if the agent service is unavailable — so the UI always has a working path.

## Prerequisites

1. Provision the Foundry project + model deployment and supporting resources with
   `infra/terraform/` (see `infra/README.md`). This creates the AI Services account, project, model
   deployment, Application Insights connection, and the app's user-assigned managed identity.
2. `az login` to the target subscription; ensure the deploying identity can create/deploy agents.
3. Install the Foundry extras where the SDK builds (Linux container / CI):
   `pip install -r agent-service/requirements-foundry.txt`.

## Option A — container sidecar (implemented in Terraform)

`infra/terraform` deploys the agent service as a **second container** in the same Container App as the
backend (see `infra/README.md`). `infra/scripts/deploy.ps1` builds `agent-service/Dockerfile`, pushes
to ACR, and rolls the image. The backend reaches the agent at `localhost:8081`; the agent calls the
Foundry model with the app's managed identity. No keys — RBAC only.

## Option B — azd hosted agent

`agent-service/azure.yaml` declares this folder as a Foundry hosted agent for the Azure Developer CLI:

```powershell
cd agent-service
azd ai agent deploy      # or: azd deploy
```

Set the model to match the provisioned deployment (Terraform output / `FOUNDRY_MODEL_DEPLOYMENT`);
`azure.yaml` defaults to `gpt-4o-mini` — change it if your project uses another (e.g. `gpt-5-mini`).

## Configuration (no secrets)

Configure via environment / `.env` (never committed — `.env.example` has placeholders only):

| Var | Meaning |
| --- | --- |
| `AZURE_AI_PROJECT_ENDPOINT` | Foundry project endpoint (or `AZURE_AI_FOUNDRY_ACCOUNT` + `..._PROJECT`) |
| `FOUNDRY_MODEL_DEPLOYMENT` | model deployment name in the project |
| `AZURE_SUBSCRIPTION_ID` / `AZURE_TENANT_ID` | Azure context for `DefaultAzureCredential` |

Authentication is via `az login` / managed identity — there are **no API keys** in the repo or in the
deployed app. Verify live connectivity with `agent-service/scripts/foundry_smoke.py`.

## Verify

```powershell
# manifest/runtime conformance
cd agent-service
.\.venv\Scripts\python.exe tests\test_manifests.py

# declared agents + drift (against a running service)
curl http://127.0.0.1:8081/api/v1/agents
```
