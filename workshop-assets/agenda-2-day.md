# Two-Day Agenda

Day 1: 9:00 AM - 4:00 PM. Day 2: 9:00 AM - 2:00 PM. Seven key items mapped across both days.
Each session uses the concept -> live edit -> run -> reveal-checkpoint rhythm
(see `docs/chapter-delivery-model.md`).

> **Sequence updated per the 9/29 planning call.** The customer reprioritized Day 1 to **lead with
> MCP + Work IQ + Toolboxes + Foundry IQ (agentic RAG)** in the morning; **Hosted Agents + BYO
> Registry are demoted to "tactical, later"** and moved to the Day 1 afternoon. Chapter numbers are
> topic identities (stable across decks/checkpoints); the **schedule order** below reflects the new
> priority. Toolboxes (Ch 8) is pulled forward to pair with MCP.

## Day 1: Build the agent (9:00 AM - 4:00 PM)

| Time | Chapter | Session | Key item | Output |
| --- | --- | --- | --- | --- |
| 9:00 - 9:30 | Ch 0 | Introduction, scenario & trust boundary | - | Shared risk model, success criteria |
| 9:30 - 10:45 | Ch 2 + Ch 8 | MCP Server (Work IQ) + Toolboxes | Items 2, 7 | Tool boundary + scope model; **secure-MCP standard**; toolbox as one governed endpoint |
| 10:45 - 11:00 | - | Break | - | - |
| 11:00 - 12:15 | Ch 4 | Foundry IQ, Building RAG | Item 4 | RAG architecture + citation contract; **existing-vs-Foundry Search**; **capability-host reuse + cost** |
| 12:15 - 1:00 | - | Lunch | - | - |
| 1:00 - 2:15 | Ch 3 | Compliance - Policy & Guardrails | Item 3 | Guardrail + PHI-minimization matrix; **healthcare content-safety (false-positive handling)** |
| 2:15 - 2:30 | - | Break | - | - |
| 2:30 - 3:45 | Ch 1 | Hosted Agents + BYO Registry | Item 1 | Deployment topology, registry controls; **hosted-vs-prompt-vs-custom decision** |
| 3:45 - 4:00 | Ch 5 | Day 1 playback | - | Recap, open risks, Day 2 setup |

## Day 2: Earn the right to trust it (9:00 AM - 2:00 PM)

| Time | Chapter | Session | Key item | Output |
| --- | --- | --- | --- | --- |
| 9:00 - 9:15 | - | Recap & environment check | - | Confirm Day 1 decisions |
| 9:15 - 10:30 | Ch 6 | LAW / Application Insights | Item 5 | Telemetry schema, KQL, dashboards; **dedicated LAW cluster + CMK + AMPLS for PHI in request/response** (Lee) |
| 10:30 - 10:45 | - | Break | - | - |
| 10:45 - 12:00 | Ch 7 | HITL - Data Task Scheduler | Item 6 | Review state machine + task schema |
| 12:00 - 12:45 | - | Lunch | - | - |
| 12:45 - 1:45 | Ch 9 | Day-2 ops & governance Q&A | - | Capability-host reuse + cost, secure-MCP recap, product-team topics (BYO AKS, roadmap) |
| 1:45 - 2:00 | Ch 9 | Closeout & roadmap | - | 30/60/90-day pilot roadmap |

## Key item coverage

| # | Key item | Day | Chapter | Delivery slot |
| --- | --- | --- | --- | --- |
| 2 | MCP Server (Work IQ) | Day 1 | Ch 2 | AM (lead) |
| 7 | Toolboxes | Day 1 | Ch 8 | AM (paired with MCP) |
| 4 | Foundry IQ, Building RAG | Day 1 | Ch 4 | AM |
| 3 | Compliance - Policy, Guardrail | Day 1 | Ch 3 | PM |
| 1 | Hosted Agents, BYO Registry for Hosted Agents | Day 1 | Ch 1 | PM (demoted) |
| 5 | LAW / App Insights | Day 2 | Ch 6 | AM |
| 6 | HITL - Data Task Scheduler | Day 2 | Ch 7 | AM |

## Notes

- Day 1 now leads with tools + grounding (Items 2, 7, 4), then policy (Item 3), then hosted-agent
  placement (Item 1); Day 2 covers operational readiness (Items 5-6) plus a governance Q&A.
- Session slots are ~75 minutes to allow one live coding moment plus a prepared checkpoint reveal.
- New source-grounded briefs to weave in: `docs/securing-mcp-servers.md`,
  `docs/capability-host-reuse-and-cost.md`.
- Prework and prerequisites: see `docs/facilitator-guide.md`. Deployment to Azure + Foundry: see `infra/README.md`.
