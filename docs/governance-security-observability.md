# Governance, Security, and Observability

## Required controls

| Control | Workshop implementation |
| --- | --- |
| Synthetic data only | Data generator creates fictional patients, encounters, claims, vitals, notes, and care tasks. |
| PHI minimization | Tool contracts return redacted summaries by default. |
| Least privilege | Tool access is scoped by caller, patient context, and purpose. |
| Prompt safety | System instructions prohibit clinical determinations and discharge-order changes. |
| RAG grounding | Material claims require citations or missing-evidence disclosure. |
| HITL approval | Draft plans must be reviewed before operational use. |
| Audit logging | Tool calls, policy decisions, retrieval, and review actions emit audit events. |
| Observability | App Insights and LAW capture traces, failures, quality, and cost proxies. |

## Telemetry event taxonomy

| Event | Purpose |
| --- | --- |
| `AgentInvocationStarted` | Start of a workflow. |
| `RetrievalCompleted` | RAG query, source, citation count, and latency. |
| `ToolCallCompleted` | Tool name, scope, result, denial status, and latency. |
| `PolicyDecisionMade` | Policy layer, decision, severity, and rule ID. |
| `HumanReviewTaskCreated` | HITL task creation. |
| `HumanReviewCompleted` | Approval, rejection, rework, timeout, and reviewer role. |
| `AgentOutputEvaluated` | Quality, groundedness, safety, and rubric version. |

