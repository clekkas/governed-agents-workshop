# Microsoft AI Surface Patterns

## Purpose

Developers need to understand where RAG and agents should live, and how the same grounded capability can appear across Microsoft AI surfaces.

## Surface decision guide

| Need | Recommended surface | Notes |
| --- | --- | --- |
| Custom code, custom orchestration, MCP tools, HITL routing | Microsoft Foundry Hosted Agent | Best fit for this workshop's core implementation. |
| Business maker-led agent with Teams/Microsoft 365 Copilot distribution | Microsoft Copilot Studio | Can connect to Microsoft Foundry agents; publish to Teams and Microsoft 365 Copilot after testing. |
| Enterprise work context from Microsoft 365 | Work IQ patterns | Use permission inheritance, DLP, sensitivity labels, and compact structured outputs. |
| Analytics and semantic business data | Fabric IQ / Fabric Data Agent | Use for OneLake, semantic models, ontology, and analytics context. |
| Standalone app-specific experience | Custom app + Foundry agent or knowledge base API | Best when UI, workflow, and policy need custom implementation. |

## Recommended workshop pattern

1. Build the core readmissions assistant as a Foundry Hosted Agent.
2. Give it RAG through Foundry IQ / approved knowledge sources.
3. Put tools behind MCP/toolboxes.
4. Add guardrails and HITL.
5. Demonstrate how the same capability could be surfaced through:
   - direct Foundry agent endpoint,
   - Copilot Studio connected agent,
   - Teams and Microsoft 365 Copilot channel via Copilot Studio,
   - custom care-manager app.

## Design caution

Publishing an agent into a new surface changes the experience, data flow, permissions, channel behavior, and test matrix. Treat each surface as a deployment target with its own validation, not just a new UI.

