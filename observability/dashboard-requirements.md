# Dashboard Requirements

## Dashboard 1: Agent fleet

Purpose: See active agents, versions, deployment state, traffic, success rate, and latency.

Required visuals:

1. Invocations by agent/version.
2. Run success rate.
3. P50/P95/P99 latency.
4. Exceptions by dependency.
5. Token usage by agent/version.

## Dashboard 2: RAG quality

Purpose: Confirm the agent is grounded in approved evidence.

Required visuals:

1. Retrieval count by source.
2. Citation count distribution.
3. Missing-evidence rate.
4. Conflicting-evidence escalations.
5. Retrieval latency.

## Dashboard 3: Tool governance

Purpose: Understand MCP/tool behavior and denied access.

Required visuals:

1. Tool calls by tool name.
2. Allow/deny/redact/escalate decisions.
3. Denials by policy.
4. Expanded-scope requests.
5. Tool latency and failures.

## Dashboard 4: HITL workflow

Purpose: Track human review throughput and bottlenecks.

Required visuals:

1. Tasks created.
2. Pending review backlog.
3. Approval/rejection/rework rate.
4. Average review time.
5. Timeout/escalation count.

## Dashboard 5: Evaluation and trust

Purpose: Determine whether the agent is ready for pilot.

Required visuals:

1. Groundedness score trend.
2. Clinical-safety failures.
3. PHI-minimization failures.
4. HITL-bypass attempts.
5. Red-team scan findings.
6. Release gate status.

## Dashboard 6: Cost/value

Purpose: Track cost drivers against operational value.

Required visuals:

1. Token usage.
2. Model call volume.
3. Tool call volume.
4. Average cost proxy per case.
5. Tasks reviewed per agent run.
6. Avoided manual lookup time estimate.

