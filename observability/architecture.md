# Observability Architecture

## Goal

Agent observability must explain behavior, not just uptime. A healthcare agent can be technically healthy while producing unsupported claims, bypassing human review, leaking unnecessary data, or failing to retrieve the right evidence.

## Observability layers

| Layer | What to observe | Primary tool |
| --- | --- | --- |
| Foundry agent runtime | Agent runs, latency, token usage, run success, evaluation results | Foundry Agent Monitoring Dashboard |
| Traces | Agent spans, retrieval operations, tool calls, exceptions, prompt/retrieval behavior | Foundry tracing + Application Insights |
| Application code | Custom orchestration, policy checks, MCP calls, HITL task creation | Application Insights / OpenTelemetry |
| Logs and analysis | KQL investigations, joins, trend analysis, alert queries | Log Analytics |
| Quality and safety | Groundedness, task adherence, safety, red-team results | Foundry evaluations and scheduled scans |
| Operations | Incidents, dashboards, alerts, runbooks, cost/value | Azure Monitor Workbooks, alerts, dashboards |

## Recommended workshop setup

1. Connect Application Insights to the Foundry project.
2. Enable server-side tracing first.
3. Add client-side OpenTelemetry instrumentation only for custom code paths.
4. Emit custom events for policy, MCP, RAG, HITL, and evaluation milestones.
5. Query traces and events in Log Analytics.
6. Convert recurring failure patterns into alerts and evaluation gates.

## Correlation model

Every major event should include:

| Field | Purpose |
| --- | --- |
| `correlationId` | End-to-end workflow ID across agent, tools, RAG, HITL, and evaluation. |
| `agentName` | Logical agent. |
| `agentVersion` | Version under test. |
| `caseId` | Synthetic case identifier. |
| `actorRole` | Care manager, engineer, evaluator, or system. |
| `eventType` | Retrieval, tool, policy, HITL, output, evaluation. |
| `decision` | Allow, deny, redact, escalate, approve, reject, rework. |
| `latencyMs` | Component latency. |
| `tokenCount` | Prompt/completion or aggregate token usage where available. |
| `citationCount` | Number of citations used in the output. |
| `reviewState` | HITL task state. |

## Five observability lenses

| Lens | Core question | Signals |
| --- | --- | --- |
| Effectiveness | Is the agent useful and grounded? | Evaluation scores, citation coverage, reviewer approval rate |
| Health | Is the workflow reliable? | Exceptions, dependency failures, latency, timeouts |
| Adoption | Are intended users using it correctly? | Invocations, active users, repeat usage, abandoned tasks |
| Cost/value | Is usage worth the cost? | Token usage, model calls, tool calls, review throughput |
| Governance/trust | Is the agent staying inside controls? | Policy denials, redactions, HITL stops, audit completeness |

