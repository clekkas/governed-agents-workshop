# Facilitator Guide

## Workshop posture

Lead with architecture, controls, and engineering patterns. The goal is not to prove that an agent can answer a prompt; the goal is to show how to design a governed healthcare agent system.

Use the Chapter delivery model in `docs/chapter-delivery-model.md`: explain the concept, make one small live edit, run it, inspect the result, then advance to a prepared checkpoint. Do not type full implementations live.

## Key decisions to capture

1. Which data is allowed in the pilot.
2. Which identities and roles are in scope.
3. Which tools belong behind MCP.
4. Which sources are allowed for RAG.
5. Which policy and guardrail tests block release.
6. Which telemetry events are mandatory.
7. Which human approvals are required.
8. Which BYO registry sample repo will be incorporated.

## Closeout outputs

1. Target architecture.
2. Tool and data inventory.
3. Policy and guardrail matrix.
4. HITL state machine.
5. Evaluation gate list.
6. 30/60/90-day roadmap.
