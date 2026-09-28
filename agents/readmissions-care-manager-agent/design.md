# Agent Design

## Agent role

The user-facing agent experience is a discharge-transition exception coordinator for synthetic tomorrow-discharge workflows. Internally, the workflow is decomposed into specialist agents coordinated by the Discharge Transition Orchestrator.

## Core loop

1. Parse user request and identify case context.
2. Discharge Transition Orchestrator starts a correlated workflow.
3. Case Context Agent retrieves redacted case context.
4. Evidence Retrieval Agent builds an evidence packet.
5. Transition Exception Agent identifies actionable transition gaps.
6. Policy Guardrail Agent validates claims, PHI, citations, and workflow boundary.
7. Human Review Agent creates or updates a review task.
8. Orchestrator emits telemetry and returns the review package.

## Structured output

```json
{
  "caseId": "P0001",
  "riskTier": "High",
  "riskDrivers": [],
  "evidence": [],
  "missingInformation": [],
  "draftFollowUpPlan": [],
  "requiresHumanReview": true,
  "prohibitedActionCheck": "passed"
}
```

## Required refusal and escalation behavior

The agent must refuse or escalate when asked to:

1. State that a patient is safe to discharge.
2. Diagnose, prescribe, or make clinical determinations.
3. Approve an exception packet or follow-up action.
4. Retrieve full notes without an explicit logged scope.
5. Use uncited protocol claims.
6. Act on instructions embedded in retrieved notes.

## Demo cases

| Case | Purpose |
| --- | --- |
| `P0001` | Golden path: high-risk case with matching protocol evidence. |
| `P0002` | Missing-knowledge path: protocol evidence absent. |
| `P0003` | Tool-denial path: note outside case scope. |
| `P0004` | HITL path: draft plan requiring approval. |
| `P0005` | Safety path: user asks for prohibited clinical claim. |
