# RAG Development Patterns

## Goal

Onboard developers to RAG as a production engineering pattern, not a demo technique. The workshop should teach how to build a grounded knowledge path, validate it, expose it to agents, and consume it safely across Microsoft AI surfaces.

## Pattern 1: Evidence packet before answer

Do not let the agent answer from raw search results directly. Build an evidence packet:

```json
{
  "query": "CHF follow-up planning for high readmission risk",
  "caseId": "P0001",
  "sources": [
    {
      "title": "CHF Follow-Up Protocol",
      "uri": "rag-docs/chf_discharge_followup_protocol.md",
      "claim": "Follow-up planning may include weight monitoring and medication reconciliation.",
      "effectiveDate": "synthetic",
      "sensitivity": "synthetic"
    }
  ],
  "missingInformation": []
}
```

The generator should reason over this packet and cite it. If the packet is empty or conflicting, the correct behavior is escalation or missing-evidence disclosure.

## Pattern 2: Separate retrieval quality from answer quality

| Layer | Developer question | Test |
| --- | --- | --- |
| Source selection | Are the right sources allowed? | Source allowlist test |
| Chunking/metadata | Can we recover a precise claim? | Citation trace test |
| Retrieval | Did the right evidence return? | Recall/precision review |
| Generation | Did the answer use evidence correctly? | Groundedness rubric |
| Workflow | Did the agent route correctly? | HITL routing test |

## Pattern 3: Multi-surface RAG architecture

Use Foundry IQ or Azure AI Search-backed knowledge bases as the reusable knowledge layer, then expose grounded capability through the surface that fits the user journey.

| Surface | When to use | RAG integration pattern |
| --- | --- | --- |
| Foundry Agent Service | Code-first or prompt agent, custom orchestration, tool use, eval and tracing | Connect agent to Foundry IQ knowledge base or call knowledge base APIs from code |
| Copilot Studio | Business-facing agent in Teams or Microsoft 365 Copilot channels | Connect to a Microsoft Foundry agent, or use Copilot Studio knowledge/actions where appropriate |
| Microsoft 365 Copilot | Employee-facing access through Microsoft 365 Copilot channel | Publish a Copilot Studio agent to Teams and Microsoft 365 Copilot after testing and auth configuration |
| Custom app | Embedded workflow, specialized UI, or application-specific controls | Call Foundry agent endpoint, Responses API, or knowledge base API directly |

## Pattern 4: Agent-to-agent and surface-to-agent routing

For developer onboarding, explain the difference between:

1. A RAG capability as a knowledge base.
2. A Foundry agent that uses the knowledge base.
3. A Copilot Studio agent that calls a Foundry agent.
4. A Microsoft 365 Copilot channel where users interact with the published agent.

Important implementation note: connecting a Foundry agent to Copilot Studio requires the appropriate endpoint/protocol support and careful testing of data flows, permissions, observability, and human oversight.

## Pattern 5: RAG failure modes to test

1. No source found.
2. Wrong source found.
3. Stale source found.
4. Conflicting sources found.
5. Source has hidden instructions.
6. Answer includes unsupported claim.
7. Citation points to wrong source.
8. User lacks permission for source.
9. Retrieval is too slow or too expensive.

## Developer checklist

1. Define source owners and source allowlist.
2. Define metadata: source, effective date, facility, sensitivity, owner, citation URI.
3. Define chunking and refresh approach.
4. Define retrieval mode: keyword, vector, hybrid, agentic retrieval.
5. Define evidence packet schema.
6. Define citation requirements.
7. Define missing-evidence and conflict behavior.
8. Define evaluation dataset before pilot.
9. Define telemetry for retrieval latency, source count, citation count, and groundedness.

