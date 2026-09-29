"""Durable Task Scheduler (DTS) backed HITL store.

The production graduation of the file-backed ``hitl.TaskStore``. It exposes the *same* method
surface the FastAPI service depends on (``register_from_result`` / ``list_tasks`` / ``get_task`` /
``get_audit`` / ``apply_action`` / ``sweep``) so ``app.py`` can swap stores purely on the
``HITL_MODE`` env var, with no route changes.

Division of responsibility:
  * **DTS is the source of truth for state + audit history.** ``register_from_result`` schedules the
    ``discharge_exception_approval`` orchestration (instance id == correlationId); decisions are
    raised as the ``ReviewDecision`` external event; the durable SLA timer auto-escalates an
    unattended run server-side (so ``sweep`` is a no-op here).
  * **Rich display metadata is kept locally** (caseId, patient label, draft packet, evidence, …),
    because the orchestration only publishes ``{status, history}``. Reads overlay the live DTS
    status/history onto that metadata.

Actions the orchestration models: ``approve`` -> Approved, ``request_changes`` -> NeedsRework,
``reject`` -> Rejected (plus timer -> Escalated and policy-escalate on create). ``claim`` is a
local-only reviewer annotation (no durable state change). ``rework`` and manual ``escalate`` are
not modelled by the durable gate and are rejected with a clear error.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Optional

from . import dts as _dts
from .hitl import (
    _AGENT_ACTORS,
    _HUMAN_ONLY,
    TERMINAL_STATES,
    HitlError,
    _iso,
    _now,
    build_review_task,
)

# Decision actions the durable orchestration understands (raised as ReviewDecision events).
_DTS_DECISIONS = {"approve", "request_changes", "reject"}
# Actions the orchestration does not model; surfaced as clear 400s in DTS mode.
_UNSUPPORTED = {"rework", "escalate"}

_DEFAULT_SLA_SECONDS = int(os.getenv("HITL_SLA_SECONDS", "86400"))


class DtsTaskStore:
    """TaskStore-compatible facade over the Durable Task Scheduler."""

    def __init__(self, path: Optional[Path] = None, sla_seconds: int = _DEFAULT_SLA_SECONDS):
        env_path = os.getenv("HITL_DTS_INDEX_PATH")
        self.path = Path(path or env_path or (Path(__file__).resolve().parents[2] / ".hitl-dts-index.json"))
        self.sla_seconds = sla_seconds
        self._lock = threading.RLock()
        self._meta: dict[str, dict] = {}
        self._gate = _dts.DtsGate()
        self._load()

    # ---- persistence (display metadata only) -----------------------------
    def _load(self) -> None:
        if self.path.exists():
            try:
                self._meta = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._meta = {}

    def _persist(self) -> None:
        try:
            self.path.write_text(json.dumps(self._meta, indent=2), encoding="utf-8")
        except OSError:
            pass

    # ---- registration ----------------------------------------------------
    def register_from_result(self, result: dict, case: Optional[dict] = None) -> dict:
        """Schedule the durable approval-gate orchestration and record display metadata."""
        task = build_review_task(result, case, self.sla_seconds)
        task_id = task["taskId"]
        # The orchestration reads slaSeconds/policyDecision/correlationId/caseId from its input.
        run_input = dict(result)
        run_input.setdefault("slaSeconds", self.sla_seconds)
        try:
            self._gate.schedule(run_input)
        except Exception as exc:  # noqa: BLE001 — surface scheduler faults as a clean 502
            raise HitlError(f"Failed to schedule durable review: {exc}", status=502) from exc
        with self._lock:
            self._meta[task_id] = task
            self._persist()
        return task

    # ---- queries ---------------------------------------------------------
    def list_tasks(self) -> list[dict]:
        with self._lock:
            metas = list(self._meta.values())
        tasks = [self._overlay(m) for m in metas]
        return sorted(tasks, key=lambda t: t["createdAt"], reverse=True)

    def get_task(self, task_id: str) -> dict:
        meta = self._meta.get(task_id)
        if meta is None:
            raise HitlError(f"No review task for correlation id '{task_id}'.", status=404)
        return self._overlay(meta)

    def get_audit(self, task_id: str) -> list[dict]:
        return self.get_task(task_id)["history"]

    # ---- transitions -----------------------------------------------------
    def apply_action(self, task_id: str, action: str, actor: str = "", note: str = "") -> dict:
        action = (action or "").strip().lower()
        with self._lock:
            meta = self._meta.get(task_id)
            if meta is None:
                raise HitlError(f"No review task for correlation id '{task_id}'.", status=404)

            current = self._overlay(meta)["status"]
            if current in TERMINAL_STATES:
                raise HitlError(
                    f"Task is already {current}; no further transitions are allowed.", status=409
                )

            if action == "claim":
                # Local-only reviewer assignment; the durable status stays PendingReview.
                meta["assignedRole"] = actor or meta.get("assignedRole")
                meta["updatedAt"] = _iso(_now())
                self._persist()
                return self._overlay(meta)

            if action in _UNSUPPORTED:
                raise HitlError(
                    f"Action '{action}' is not supported in DTS mode (the durable gate has no "
                    f"corresponding transition).",
                    status=400,
                )

            if action not in _DTS_DECISIONS:
                raise HitlError(
                    f"Unknown action '{action}'. Valid: {', '.join(sorted(_DTS_DECISIONS | {'claim'}))}.",
                    status=400,
                )

            if action in _HUMAN_ONLY and (actor or "").strip().lower() in _AGENT_ACTORS:
                raise HitlError(
                    f"Action '{action}' requires a human reviewer; supply an 'actor'.", status=403
                )

            try:
                self._gate.raise_decision(task_id, action, actor=actor, note=note)
            except Exception as exc:  # noqa: BLE001
                raise HitlError(f"Failed to raise durable decision: {exc}", status=502) from exc

        # Give the worker a brief window to process the event so the response reflects the new state.
        return self._overlay(meta, wait_for_change_from=current)

    def sweep(self) -> list[dict]:
        """No-op: the durable SLA timer auto-escalates server-side; nothing to sweep here."""
        return []

    # ---- internals -------------------------------------------------------
    def _overlay(self, meta: dict, wait_for_change_from: Optional[str] = None) -> dict:
        """Return meta with live DTS status + history overlaid. Optionally poll briefly for change."""
        attempts = 10 if wait_for_change_from else 1
        state = None
        for i in range(attempts):
            try:
                state = self._gate.get_status(meta["taskId"])
            except Exception:  # noqa: BLE001 — scheduler unavailable: fall back to local metadata
                state = None
            status = (state or {}).get("status")
            if not wait_for_change_from or (status and status != wait_for_change_from):
                break
            if i < attempts - 1:
                time.sleep(0.3)

        task = dict(meta)
        if state:
            if state.get("status"):
                task["status"] = state["status"]
            if state.get("history"):
                task["history"] = state["history"]
            if task["status"] != meta.get("status"):
                task["updatedAt"] = _iso(_now())
        return task
