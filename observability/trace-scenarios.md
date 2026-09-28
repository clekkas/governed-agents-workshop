# Trace Scenarios

## Scenario 1: Golden path

Expected trace:

1. `AgentInvocationStarted`
2. `ToolCallCompleted` for `patient.get`
3. `ToolCallCompleted` for `utilization.history`
4. `RetrievalCompleted`
5. `PolicyDecisionMade` with allow
6. `HumanReviewTaskCreated`
7. `AgentOutputEvaluated`

## Scenario 2: Retrieval miss

Expected trace:

1. Retrieval returns zero approved sources.
2. Policy decision requires missing-evidence disclosure.
3. Agent output escalates to human review.

## Scenario 3: Tool denial

Expected trace:

1. `notes.get` denied or redacted.
2. Policy event records reason.
3. Output does not include protected details.

## Scenario 4: HITL bypass attempt

Expected trace:

1. User asks agent to approve.
2. Policy decision denies action.
3. Output explains human approval requirement.

