"""FastAPI app exposing the agent invoke contract.

Endpoints match the Node backend so the UI and gateway are unchanged:
  GET  /api/health
  GET  /api/v1/cases
  GET  /api/v1/cases/{case_id}
  POST /api/v1/agent/invoke

Run locally:
  uvicorn discharge_transition_agent.app:app --host 127.0.0.1 --port 8081
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from . import __version__, cases
from .foundry import FoundryClient
from .foundry_agents import FoundryAgentOrchestrator, FoundryAgentsUnavailable
from .hitl import HitlError, TaskStore
from .models import InvokeRequest
from .orchestrator import DischargeTransitionOrchestrator


def _load_dotenv() -> None:
    """Load agent-service/.env into os.environ if present (no external dependency)."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

app = FastAPI(title="Discharge Transition Agent Service", version=__version__)

# Execution mode: "foundry" (default) drives the published Foundry hosted agents; "local" runs the
# deterministic in-process specialists (best for offline local tests and cloud-free deployment).
# Either mode enforces the same governed safety boundary and returns the same response contract.
EXECUTION_MODE = os.environ.get("AGENT_EXECUTION_MODE", "foundry").strip().lower()

_foundry = FoundryClient()
_local_orchestrator = DischargeTransitionOrchestrator(foundry=_foundry)
_foundry_orchestrator = FoundryAgentOrchestrator() if EXECUTION_MODE == "foundry" else None

# Human-in-the-loop backend: "local" (in-memory, file-backed TaskStore) or "dts" (durable gate on
# the Durable Task Scheduler). Both expose the same method surface, so the routes are identical.
HITL_MODE = os.environ.get("HITL_MODE", "local").strip().lower()
if HITL_MODE == "dts":
    from .hitl_dts import DtsTaskStore

    _tasks = DtsTaskStore()
else:
    _tasks = TaskStore()


def _run_workflow(case: dict, correlation_id: str) -> tuple[Any, str]:
    """Run the workflow with the configured mode; fall back to local on any Foundry problem.

    Returns (result, effective_mode) so callers/telemetry can see which path actually ran.
    """
    if EXECUTION_MODE == "foundry" and _foundry_orchestrator is not None:
        try:
            return _foundry_orchestrator.run(case, correlation_id=correlation_id), "foundry"
        except FoundryAgentsUnavailable:
            pass  # hosted agents unreachable — degrade to the deterministic local path
        except Exception:  # noqa: BLE001 — never fail the request because of the hosted path
            pass
    return _local_orchestrator.run(case, correlation_id=correlation_id), "local"


def _correlation_id(request: Request) -> str:
    incoming = request.headers.get("x-correlation-id", "").strip()
    return incoming or f"trace-{uuid.uuid4()}"


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    cid = _correlation_id(request)
    request.state.correlation_id = cid
    response: Response = await call_next(request)
    response.headers["x-correlation-id"] = cid
    return response


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "discharge-transition-agent-service",
        "execution_mode": EXECUTION_MODE,
        "hitl_mode": HITL_MODE,
        "foundry_agents_available": bool(_foundry_orchestrator and _foundry_orchestrator.available),
        "foundry_enabled": _foundry.enabled,
        "foundry_mode": _foundry.mode,
        "version": __version__,
    }


@app.get("/api/v1/agents")
def agents() -> dict:
    """Declared agents (from agents/*.yaml manifests) and their runtime conformance."""
    from . import agent_manifests

    return agent_manifests.summary()


@app.get("/api/v1/cases")
def list_cases() -> dict:
    return {"cases": cases.list_cases()}


@app.get("/api/v1/cases/{case_id}")
def get_case(case_id: str, request: Request) -> JSONResponse:
    case = cases.get_case(case_id)
    if case is None:
        return JSONResponse(
            status_code=404,
            content={
                "type": "about:blank",
                "title": "Case not found",
                "status": 404,
                "detail": f"No synthetic case with id '{case_id}'.",
                "correlationId": getattr(request.state, "correlation_id", None),
            },
        )
    return JSONResponse(content=case)


@app.post("/api/v1/agent/invoke")
def invoke(body: InvokeRequest, request: Request) -> JSONResponse:
    case = cases.get_case(body.case_id)
    if case is None:
        return JSONResponse(
            status_code=404,
            content={
                "type": "about:blank",
                "title": "Case not found",
                "status": 404,
                "detail": f"No synthetic case with id '{body.case_id}'.",
                "correlationId": getattr(request.state, "correlation_id", None),
            },
        )
    result = _run_workflow(case, correlation_id=getattr(request.state, "correlation_id", None))[0]
    payload = result.model_dump(by_alias=True)
    # Register the durable human-review task — the Data Task Scheduler approval gate. The run
    # drafts the packet; a care manager must act on it before anything downstream happens.
    _tasks.register_from_result(payload, case=case)
    # by_alias=True yields the camelCase contract the UI expects.
    return JSONResponse(content=payload)


def _hitl_error(exc: HitlError, request: Request) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status,
        content={
            "type": "about:blank",
            "title": "HITL transition error",
            "status": exc.status,
            "detail": str(exc),
            "correlationId": getattr(request.state, "correlation_id", None),
        },
    )


@app.get("/api/v1/tasks")
def list_tasks() -> dict:
    return {"tasks": _tasks.list_tasks()}


@app.get("/api/v1/tasks/{task_id}")
def get_task(task_id: str, request: Request) -> JSONResponse:
    try:
        return JSONResponse(content=_tasks.get_task(task_id))
    except HitlError as exc:
        return _hitl_error(exc, request)


@app.get("/api/v1/tasks/{task_id}/audit")
def get_task_audit(task_id: str, request: Request) -> JSONResponse:
    try:
        return JSONResponse(content={"taskId": task_id, "audit": _tasks.get_audit(task_id)})
    except HitlError as exc:
        return _hitl_error(exc, request)


@app.post("/api/v1/tasks/{task_id}/action")
async def task_action(task_id: str, request: Request) -> JSONResponse:
    body = {}
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001 — empty/invalid body is a 400 below
        body = {}
    action = (body or {}).get("action", "")
    actor = (body or {}).get("actor", "")
    note = (body or {}).get("note", "")
    try:
        task = _tasks.apply_action(task_id, action, actor=actor, note=note)
        return JSONResponse(content=task)
    except HitlError as exc:
        return _hitl_error(exc, request)


@app.post("/api/v1/tasks/sweep")
def sweep_tasks() -> dict:
    escalated = _tasks.sweep()
    return {"escalated": [t["taskId"] for t in escalated], "count": len(escalated)}
