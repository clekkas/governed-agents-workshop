# Agent Governance Plan

## Governance objective

Define how the readmissions care operations assistant is owned, reviewed, evaluated, monitored, and controlled from workshop prototype through pilot readiness.

## Ownership matrix

| Area | Owner | Required decision |
| --- | --- | --- |
| Agent behavior | Product/workflow owner | Approved use case and prohibited behaviors |
| Data sources | Data owner | Approved synthetic and future candidate sources |
| Knowledge base | Knowledge owner | Approved RAG docs, metadata, refresh cadence |
| Tools | Engineering owner | Tool schemas, scopes, error behavior |
| Security | Security owner | Identity, RBAC, endpoint access |
| Privacy/compliance | Privacy owner | PHI minimization, audit, retention |
| HITL | Operations owner | Reviewer roles, escalation, timeout |
| Evaluation | AI quality owner | Rubrics, golden set, pass thresholds |
| Observability | Operations owner | Dashboards, alerts, incident process |

## Governance gates

| Gate | Required evidence |
| --- | --- |
| Use-case approval | Workflow, actors, outcomes, excluded actions |
| Data approval | Synthetic-only confirmation or governed data approval |
| Tool approval | Schema, scope, auth, audit, denial behavior |
| Knowledge approval | Source list, citations, metadata, refresh owner |
| Safety approval | Prohibited claims and adversarial tests |
| HITL approval | Human review state machine and ownership |
| Observability approval | Trace, metrics, dashboard, alert plan |
| Pilot readiness | Evaluation baseline and rollback plan |

