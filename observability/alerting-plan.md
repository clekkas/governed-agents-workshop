# Alerting Plan

## Alert categories

| Category | Example alert | Suggested action |
| --- | --- | --- |
| Reliability | Run success rate below threshold | Inspect traces and dependency failures |
| Latency | P95 agent latency exceeds target | Check model throttling, tool latency, retrieval complexity |
| Safety | Prohibited clinical claim detected | Block release, inspect prompt/tool chain |
| Data protection | PHI-minimization failure | Inspect tool response and output validator |
| HITL | Review backlog or timeout spike | Escalate to operations owner |
| RAG | Missing citation rate exceeds threshold | Inspect retrieval, source metadata, prompt changes |
| Cost | Token usage spike | Inspect prompt growth, tool definitions, retrieval context size |

## Workshop alert examples

1. Any `safe-discharge` policy failure is Sev 2 in pilot.
2. HITL bypass attempt count above zero is release-blocking until reviewed.
3. Missing citation rate above 5% blocks release candidate.
4. Tool denial leakage is release-blocking.
5. P95 end-to-end latency above agreed target requires performance review.

