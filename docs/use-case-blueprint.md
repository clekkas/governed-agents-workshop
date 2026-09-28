# Use Case Blueprint: Discharge Transition Exception Coordinator

## Use case

A care manager or ADT nurse reviews tomorrow's synthetic discharge-candidate list. The agent gathers approved context, consumes an existing approved risk score, retrieves relevant transition protocols, identifies incomplete transition elements, drafts an exception packet with proposed owners and due times, and routes the packet for human review.

## Actors

| Actor | Responsibility |
| --- | --- |
| Care manager | Reviews evidence, edits plan, approves, rejects, or requests rework. |
| Agent team | Retrieves, summarizes, cites, detects transition gaps, drafts exception packet, and routes. |
| MCP server | Enforces tool contracts, authorization, scope, redaction, and audit. |
| Knowledge owner | Approves RAG source documents and citation requirements. |
| Security/privacy owner | Approves identity, access, PHI-minimization, and audit controls. |
| Operations owner | Reviews telemetry, incidents, adoption, and cost/value. |

## Agent permissions by risk zone

| Zone | Agent behavior | Examples | Required control |
| --- | --- | --- | --- |
| Green | Retrieve, summarize, explain | Summarize synthetic case; cite protocol | Standard scoped tool access |
| Yellow | Recommend or prepare an action | Draft exception packet; prepare review task | Evidence required; human review required |
| Red | Consequential action | Approve plan; change orders; contact patient | Not allowed for agent; human-only |

## Multi-agent design

The workshop demonstrates a multi-agent orchestration rather than one large assistant:

| Agent | Responsibility |
| --- | --- |
| Discharge Transition Orchestrator | Coordinates the workflow, preserves state, and assembles the exception packet. |
| Case Context Agent | Retrieves redacted synthetic case context and utilization signals. |
| Risk Score Agent | Retrieves an approved risk score, provenance, timestamp, and driver codes. |
| Evidence Retrieval Agent | Builds the RAG evidence packet with citations and missing-evidence signals. |
| Transition Exception Agent | Identifies medication, appointment, pending-result, DME, service, transportation, language, social-support, referral, and task gaps. |
| Care Plan Drafting Agent | Drafts owner, due-time, and task/outreach text from evidence and gap context. |
| Policy Guardrail Agent | Validates prohibited claims, PHI minimization, citations, and HITL boundaries. |
| Human Review Agent | Creates and tracks HITL review tasks and audit events. |

## Workflow

1. Care manager selects a synthetic case from the worklist.
2. Discharge Transition Orchestrator starts an invocation and creates a correlation ID.
3. Case Context Agent retrieves redacted case context through `patient.get` and aggregate utilization through `utilization.history`.
4. Risk Score Agent retrieves the approved risk score through `risk_score.get`.
5. Evidence Retrieval Agent retrieves effective-dated transition protocol evidence through `protocol.search`.
6. Transition Exception Agent identifies incomplete operational transition elements.
7. Care Plan Drafting Agent drafts owner, due-time, and task/outreach recommendations.
8. Policy Guardrail Agent checks prohibited claims, PHI exposure, citation coverage, missing information, and no autonomous discharge decision.
9. Human Review Agent creates a HITL review task through `task.create`.
10. Human reviewer approves, edits, rejects, requests rework, or escalates.
11. All specialist handoffs are logged and visible in telemetry.

## Non-goals

1. No diagnosis.
2. No medical advice.
3. No discharge decision.
4. No medication order changes.
5. No real patient/member data.
6. No autonomous action without human review.
7. No LLM-generated risk score.
8. No interpretation of clinical significance for pending results.

## Success criteria

1. Agent output includes cited evidence or missing-evidence disclosure.
2. Tool calls are case-scoped and auditable.
3. PHI-shaped data is minimized by default.
4. Approved risk score includes provenance and is not recalculated by the agent.
5. Human review is mandatory for draft exception packets.
6. Evaluation detects unsafe claims, missing citations, tool-denial leakage, HITL bypass attempts, and invented risk scores.
7. Observability shows agent behavior, not just service uptime.
