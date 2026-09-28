# Observability Runbook

## Five lenses

| Lens | Question | Example signals |
| --- | --- | --- |
| Effectiveness | Is the agent producing useful grounded output? | Groundedness, citation coverage, reviewer approval rate |
| Health | Is the system operating reliably? | Exceptions, latency, dependency failures, timeouts |
| Adoption | Are users using the workflow correctly? | Invocations, repeat usage, abandoned tasks |
| Cost/value | Is cost aligned to value? | Tokens, model calls, tool calls, review throughput |
| Governance/trust | Is the agent staying inside controls? | Policy denials, redactions, HITL stops, audit completeness |

## Troubleshooting flow

1. What agents and versions are active?
2. What happened in this invocation?
3. Which retrieval, tool, policy, and HITL events occurred?
4. Did the answer cite evidence?
5. Did policy block, redact, or escalate anything?
6. Did the reviewer approve, reject, or request rework?
7. Is this a model, tool, retrieval, policy, or workflow issue?

## Required dashboards

1. Agent fleet and version dashboard.
2. Invocation health dashboard.
3. Retrieval quality dashboard.
4. Tool call and denial dashboard.
5. HITL queue dashboard.
6. Cost/value dashboard.
7. Governance/trust dashboard.

