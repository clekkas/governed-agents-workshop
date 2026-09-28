# Lab Progression

Use one evolving agent across all labs.

## Lab 1: Minimal care operations agent

Build a simple synthetic scenario and orchestration loop. The Discharge Transition Orchestrator can identify a case and route to a Case Context Agent.

## Lab 2: Governed tool access

Expose narrow synthetic healthcare operations through MCP. Case Context Agent and Evidence Retrieval Agent call `patient.get`, `utilization.history`, and `protocol.search`. Show allow, deny, redact, and audit behavior.

## Lab 3: Hosted Agent deployment

Package the code-first agent for managed hosting. Discuss BYO Registry once the separate sample repo is available.

## Lab 4: Enterprise knowledge and RAG

Add approved synthetic guidance. Evidence Retrieval Agent builds an evidence packet. Transition Exception Agent can only draft from that packet and approved risk-score context.

## Lab 5: Human approval boundary

Human Review Agent creates a HITL review task. The orchestration can draft but not approve.

## Lab 6: Break the agent intentionally

Inject bad retrieval, tool failure, policy denial, latency, unsafe prompt, or broken handoff. Diagnose through traces and evaluations.

## Lab 7: Governance design exercise

Teams complete the governance plan: owner, data owner, source list, tools, prohibited actions, approval points, monitoring owner, and escalation path.
