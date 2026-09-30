# Hosted vs Prompt vs Custom Agent — the decision (for Kaiser Permanente)

> Answers Matt's "tipping factor" question: given a use case, what pushes you toward a **prompt
> agent** (instructions only), a **hosted agent** (your code, Foundry-run), or **your own runtime**
> calling the Responses API? Framed across the SDLC (control, code to maintain, ops, cost, speed).
>
> Grounded in Microsoft Learn: **What is Foundry Agent Service** (`/azure/foundry/agents/overview`),
> **Hosted agents** (`/azure/foundry/agents/concepts/hosted-agents`).

## The spectrum (declarative → full code)

Foundry meets you anywhere from declarative config to a full container:

| Type | You build | Foundry manages | Runtime code to maintain |
| --- | --- | --- | --- |
| **Prompt agent** | Instructions + model + tools (portal or SDK/REST) | Everything (runtime, scaling, endpoint) | **None** |
| **Voice-based prompt agent** | Same, + audio settings | Real-time voice orchestration (Voice Live) | **None** |
| **Hosted agent** | Your **code + framework** (Agent Framework, LangGraph, OpenAI/Anthropic/Copilot SDK, or own code), shipped as a container or .zip | Managed endpoint, autoscaling, dedicated Entra identity, session state, observability | **Yes** |
| **Responses API (self-hosted)** | The whole agent runtime, elsewhere | Nothing — you just call Foundry models/tools | **Yes (all of it)** |

Under the hood a **hosted agent's code calls the Responses API on the project endpoint** for model
inference + platform tools (file search, code interpreter, web search, SharePoint, Work IQ, Fabric
IQ). So "hosted" = your logic, Foundry's hosting + tools + identity.

## The tipping factors (what pushes you each way)

| If the use case needs… | Choose |
| --- | --- |
| Only instructions + tools, no custom control flow | **Prompt agent** |
| Fastest start, internal tool, managed runtime, CI/CD via SDK/REST | **Prompt agent** |
| Real-time spoken conversation (call-center, voice) | **Voice-based prompt agent** |
| Custom/deterministic **orchestration**, **multi-agent** handoffs, branching control flow | **Hosted agent** |
| Bring an **existing framework/codebase** (LangGraph, Agent Framework, etc.) | **Hosted agent** |
| Calls into **your own custom code**/business logic | **Hosted agent** |
| Custom protocols (webhooks, AG-UI, custom voice) | **Hosted agent** |
| You already run a mature agent runtime and only want Foundry models/tools | **Responses API** |
| Strict need to run the runtime in your own environment/network | **Responses API / self-hosted** |

## The SDLC trade-off (Matt's lens)

| Dimension | Prompt agent | Hosted agent | Self-hosted (Responses API) |
| --- | --- | --- | --- |
| Control over logic | Low (config only) | High (your code) | Total |
| Code/infra to maintain | None | Container + code | Everything |
| Ops burden (scale, patch, monitor) | Foundry | Foundry hosts; you own the image | You own it all |
| Speed to first agent | Fastest | Medium | Slowest |
| Portability of logic | Low | High (standard frameworks) | High |
| Identity/observability built in | Yes | Yes (dedicated Entra id + tracing) | You wire it |
| Cost driver | Model + tools | Model + tools + container compute | Model + your infra |

**Rule of thumb:** start with a **prompt agent**; graduate to a **hosted agent** the moment you need
custom orchestration, multi-agent handoffs, an existing framework, or your own code in the loop;
reach for **self-hosted + Responses API** only when you must own the runtime/environment.

## Applied to the workshop use case

The Discharge Transition Exception Coordinator is a **multi-agent, deterministic workflow** (context
→ risk → evidence → exception → care-plan → guardrail → human-review) with custom control flow and a
HITL gate. That set of needs — custom orchestration + multi-agent + own code — is exactly the
**hosted-agent** tipping point, which is why the workshop builds it as hosted agents. A single-step
"summarize this protocol" tool, by contrast, would be a **prompt agent**. Show both live so KP sees
the boundary, not just the endpoint.

## What to tell app teams

1. Don't default to hosted agents because they sound powerful — **default to prompt agents** and let
   a real requirement (orchestration, multi-agent, existing code, custom protocol) pull you up.
2. Hosted agents still get managed hosting, scaling, identity, and tracing — you own the **logic**,
   not the plumbing.
3. Model choice is swappable in all types; it is not a reason to pick one type over another.

## References (public)

- Foundry Agent Service overview + agent types: `/azure/foundry/agents/overview`
- Hosted agents: `/azure/foundry/agents/concepts/hosted-agents`
- Prompt agent quickstart: `/azure/foundry/agents/quickstarts/prompt-agent`
- Responses API: `/azure/foundry/agents/quickstarts/responses-api`
