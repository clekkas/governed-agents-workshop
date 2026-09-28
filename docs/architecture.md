# Architecture

## Reference pattern

```mermaid
flowchart LR
    UI[Care manager UI] --> Agent[Hosted Agent]
    Agent --> Policy[Policy and Guardrails]
    Policy --> MCP[MCP Server]
    MCP --> Clinical[Clinical Context Toolbox]
    MCP --> Protocol[Protocol Toolbox]
    MCP --> Util[Utilization Toolbox]
    MCP --> Coord[Care Coordination Toolbox]
    Agent --> RAG[Foundry IQ / RAG Pattern]
    RAG --> Index[Search Index]
    Index --> Docs[Synthetic Protocol Docs]
    Agent --> HITL[Data Task Scheduler]
    HITL --> Reviewer[Human Review]
    Agent --> AppInsights[Application Insights]
    MCP --> AppInsights
    RAG --> AppInsights
    HITL --> LAW[Log Analytics Workspace]
    AppInsights --> LAW
```

## Design principles

1. Agents reason over evidence; tools perform bounded work.
2. MCP is the control plane for tool access.
3. RAG responses cite approved sources or disclose missing evidence.
4. Policy is layered across input, retrieval, tools, generation, output, and approval.
5. Human review is required before follow-up actions.
6. Observability captures behavior, quality, safety, cost, latency, and approval flow.
7. Registry and deployment controls are part of the release process, not an afterthought.

## Trust boundaries

| Boundary | Purpose |
| --- | --- |
| User identity | Captures who initiated the workflow. |
| Agent identity | Grants only required access to tools and telemetry. |
| MCP tool identity | Separates data access from model reasoning. |
| RAG index boundary | Restricts grounding to approved sources. |
| HITL boundary | Prevents autonomous operational action. |
| Registry boundary | Controls image provenance and release promotion. |

