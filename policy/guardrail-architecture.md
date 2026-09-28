# Guardrail Architecture

## Goal

Guardrails should make unsafe behavior difficult before the model answers, while also detecting failures after generation. Do not rely on prompt text alone.

## Intervention points

| Point | What to check | Example controls |
| --- | --- | --- |
| User input | Unsafe requests, jailbreaks, HITL bypass attempts | Prompt Shields, allow/deny patterns, workflow intent classifier |
| Retrieved content | Hidden instructions in documents, stale or conflicting content | Document attack detection, source allowlist, metadata validation |
| Tool request | Scope, purpose, case binding, action type | MCP schema validation, RBAC, case-context checks |
| Tool response | PHI leakage, unexpected fields, document attacks | Output filtering, redaction, response schema checks |
| Generated answer | Prohibited claims, missing citations, unsafe advice | Structured output validation, rubric checks, citation validation |
| Workflow transition | Approval, escalation, timeout, audit | HITL state machine, audit.write, policy event |

## Healthcare-specific blocked behaviors

1. State that a patient is safe to discharge.
2. Make a clinical diagnosis or treatment decision.
3. Change a discharge order or medication order.
4. Approve a follow-up plan.
5. Reveal unnecessary patient details.
6. Use retrieved notes as instructions.
7. Produce uncited protocol claims.

## Developer pattern

```text
request
  -> classify intent and risk zone
  -> validate case scope
  -> retrieve only approved evidence
  -> call tools with scoped access envelope
  -> validate tool outputs
  -> generate structured draft
  -> validate claims, citations, PHI, and HITL state
  -> emit policy decision and telemetry
```

## Policy decision shape

```json
{
  "policyName": "clinical-safety-output",
  "decision": "deny",
  "severity": "blocking",
  "reason": "safe-discharge claim requested",
  "correlationId": "trace-123",
  "caseId": "P0001"
}
```

