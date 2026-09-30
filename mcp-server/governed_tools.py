"""Governed clinical tool logic for the discharge-transition MCP server.

Pure, dependency-free functions that implement the *governed* behavior of each tool in the
discharge-transition trust boundary. The real MCP server (`server.py`) wraps these with the MCP
protocol; the agent-service keeps an equivalent in-process implementation. Keeping the logic here
means the behavior is identical whether it runs in-process or over MCP, and it stays unit-testable
without the MCP SDK.

Governed guarantees enforced in code (not just prompts):
- ``patient.get`` returns a redacted, minimum-necessary summary (decision ``redact``).
- ``risk_score.get`` is read-only and deterministic; it echoes the approved score, never generates
  or overrides it.
- ``utilization.history`` is aggregate-only by default.
- ``protocol.search`` escalates (``review_required``) when a required specialty protocol is missing.
- ``task.create`` drafts a review task only; it cannot approve.
- ``audit.write`` is always-on.

All data is synthetic. Argument shapes are validated against the JSON contracts in
``tool-contracts/`` via :func:`validate_args`.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

CONTRACTS_DIR = os.path.join(os.path.dirname(__file__), "tool-contracts")

_LATENCY = {
    "patient.get": 118,
    "utilization.history": 164,
    "risk_score.get": 74,
    "protocol.search": 242,
    "task.create": 96,
    "audit.write": 55,
    "notes.get": 88,
}


@dataclass
class ToolResult:
    """The governed outcome of a tool call: a policy decision plus a payload."""

    name: str
    decision: str
    latency_ms: int
    result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "decision": self.decision,
            "latency_ms": self.latency_ms,
            "result": self.result,
        }


def _timed(name: str, decision: str, result: dict[str, Any]) -> ToolResult:
    return ToolResult(name=name, decision=decision, latency_ms=_LATENCY.get(name, 120), result=result)


# --------------------------------------------------------------------------- contract validation
def _validate(schema: dict[str, Any], value: Any, path: str, errors: list[str]) -> None:
    t = schema.get("type")
    if t == "object":
        if not isinstance(value, dict):
            errors.append(f"{path}: expected object")
            return
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{path}: missing required property '{req}'")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(f"{path}: additional property '{key}' not allowed")
        for key, sub in props.items():
            if key in value:
                _validate(sub, value[key], f"{path}.{key}", errors)
    elif t == "array":
        if not isinstance(value, list):
            errors.append(f"{path}: expected array")
            return
        if "items" in schema:
            for i, item in enumerate(value):
                _validate(schema["items"], item, f"{path}[{i}]", errors)
    elif t == "string":
        if not isinstance(value, str):
            errors.append(f"{path}: expected string")
        elif "enum" in schema and value not in schema["enum"]:
            errors.append(f"{path}: '{value}' not in enum {schema['enum']}")
    elif t == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{path}: expected boolean")
    elif t in ("integer", "number"):
        if not isinstance(value, (int, float)) or isinstance(value, bool) or (
            t == "integer" and not isinstance(value, int)
        ):
            errors.append(f"{path}: expected {t}")
            return
        if schema.get("minimum") is not None and value < schema["minimum"]:
            errors.append(f"{path}: {value} < minimum {schema['minimum']}")
        if schema.get("maximum") is not None and value > schema["maximum"]:
            errors.append(f"{path}: {value} > maximum {schema['maximum']}")


def load_contract(tool: str) -> dict[str, Any]:
    with open(os.path.join(CONTRACTS_DIR, f"{tool}.schema.json"), encoding="utf-8") as fh:
        return json.load(fh)


def validate_args(tool: str, args: dict[str, Any]) -> list[str]:
    """Return a list of contract-violation messages (empty means the args conform)."""
    return _validate_collect(load_contract(tool), args)


def _validate_collect(schema: dict[str, Any], value: Any) -> list[str]:
    errors: list[str] = []
    _validate(schema, value, "$", errors)
    return errors


class ContractError(ValueError):
    """Raised when tool arguments violate the published JSON contract."""


def _checked(tool: str, args: dict[str, Any]) -> None:
    errors = validate_args(tool, args)
    if errors:
        raise ContractError(f"{tool}: {'; '.join(errors)}")


# --------------------------------------------------------------------------- governed tools
def patient_get(patientId: str, correlationId: str, purpose: str = "care-review", expandedScope: bool = False) -> ToolResult:
    _checked("patient.get", {"patientId": patientId, "correlationId": correlationId, "purpose": purpose, "expandedScope": expandedScope})
    # Redacted, minimum-necessary context only. No raw PHI leaves the boundary.
    return _timed("patient.get", "redact", {
        "patientId": patientId,
        "patient_label": f"Synthetic patient {patientId}",
        "diagnosis_category": "CHF",
        "minimum_necessary": True,
    })


def utilization_history(patientId: str, correlationId: str, lookbackDays: int = 365, aggregateOnly: bool = True) -> ToolResult:
    _checked("utilization.history", {"patientId": patientId, "correlationId": correlationId, "lookbackDays": lookbackDays, "aggregateOnly": aggregateOnly})
    return _timed("utilization.history", "allow", {"aggregate": True, "encounters_365d": 3, "aggregateOnly": aggregateOnly})


def risk_score_get(patientId: str, encounterId: str, correlationId: str, includeDriverCodes: bool = True) -> ToolResult:
    _checked("risk_score.get", {"patientId": patientId, "encounterId": encounterId, "correlationId": correlationId, "includeDriverCodes": includeDriverCodes})
    # Read-only + deterministic: echoes the approved score with provenance; never recalculated.
    score = {"score": 0.72, "band": "high", "source": "approved-deterministic-model", "read_only": True}
    if includeDriverCodes:
        score["driver_codes"] = ["I50.9", "E11.65"]
    return _timed("risk_score.get", "allow", score)


def protocol_search(query: str, correlationId: str, facility: str | None = None, topK: int = 5, specialtyRequired: bool = False, specialtyFound: bool = True) -> ToolResult:
    args = {"query": query, "correlationId": correlationId, "topK": topK}
    if facility is not None:
        args["facility"] = facility
    _checked("protocol.search", args)
    decision = "review_required" if (specialtyRequired and not specialtyFound) else "allow"
    evidence = [] if decision == "review_required" else [
        {"source": "CHF Discharge Follow-Up Protocol", "claim": "Follow-up within 48-72h.", "effective_date": "2026-01-01"}
    ]
    return _timed("protocol.search", decision, {"evidence": evidence})


def task_create(patientId: str, correlationId: str, draftPlan: str, evidence: list[dict[str, Any]], assignedRole: str = "Care Manager") -> ToolResult:
    _checked("task.create", {"patientId": patientId, "correlationId": correlationId, "draftPlan": draftPlan, "evidence": evidence, "assignedRole": assignedRole})
    # Draft only: creates a PendingReview task; it can never approve.
    return _timed("task.create", "review_required", {"task_id": f"task-{patientId}", "status": "PendingReview", "assigned_role": assignedRole})


def audit_write(correlationId: str, eventType: str, actor: str, timestamp: str) -> ToolResult:
    _checked("audit.write", {"correlationId": correlationId, "eventType": eventType, "actor": actor, "timestamp": timestamp})
    return _timed("audit.write", "allow", {"recorded": True, "eventType": eventType})


def notes_get(patientId: str, encounterId: str, correlationId: str, redactedOnly: bool = True) -> ToolResult:
    _checked("notes.get", {"patientId": patientId, "encounterId": encounterId, "correlationId": correlationId, "redactedOnly": redactedOnly})
    return _timed("notes.get", "redact", {"excerpts": ["[redacted clinical note excerpt]"], "redactedOnly": redactedOnly})


# Dispatch table: MCP tool name -> (callable, ordered arg names pulled from the invocation dict).
TOOLS = {
    "patient.get": patient_get,
    "utilization.history": utilization_history,
    "risk_score.get": risk_score_get,
    "protocol.search": protocol_search,
    "task.create": task_create,
    "audit.write": audit_write,
    "notes.get": notes_get,
}


def call(tool: str, args: dict[str, Any]) -> ToolResult:
    """Invoke a governed tool by MCP name with a kwargs dict. Validates the contract first."""
    if tool not in TOOLS:
        raise KeyError(f"unknown tool '{tool}'")
    return TOOLS[tool](**args)
