# Module 05: LAW and Application Insights Observability

## Objective

Instrument agent, RAG, MCP, policy, and HITL flows.

## Required events

1. `AgentInvocationStarted`
2. `RetrievalCompleted`
3. `ToolCallCompleted`
4. `PolicyDecisionMade`
5. `HumanReviewTaskCreated`
6. `HumanReviewCompleted`
7. `AgentOutputEvaluated`

## Output

Telemetry schema and starter KQL dashboard queries.

## Core concepts

| Concept | Why it matters |
| --- | --- |
| Application Insights | Stores Foundry traces and app telemetry for agent runs, code paths, exceptions, dependencies, and performance. |
| Log Analytics | Lets teams query telemetry with KQL, build investigations, alerts, and workbooks. |
| OpenTelemetry | Standard instrumentation model for traces, metrics, and logs across custom agent code and services. |
| Foundry tracing | Server-side traces for prompt and hosted agents after Application Insights is connected. |
| Agent Monitoring Dashboard | Operational view for token usage, latency, run success, evaluation metrics, and red-team results. |
| Continuous evaluation | Scheduled quality/safety checks against production or sampled agent outputs. |

## Hands-on exercise

1. Connect or identify the Application Insights resource for the Foundry project.
2. Review server-side traces for one golden-path run.
3. Emit or inspect custom events for `PolicyDecisionMade`, `ToolCallCompleted`, `RetrievalCompleted`, and `HumanReviewTaskCreated`.
4. Use Log Analytics to query by `correlationId`.
5. Map the run to the five observability lenses:
   - effectiveness,
   - health,
   - adoption,
   - cost/value,
   - governance/trust.
6. Identify one alert that would block pilot release.

## Required workshop deliverables

1. Telemetry event taxonomy.
2. Correlation ID convention.
3. Starter KQL queries.
4. Dashboard requirements.
5. Alerting plan.
6. Incident triage runbook.
