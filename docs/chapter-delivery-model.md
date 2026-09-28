# Chapter Delivery Model

## Principle

The workshop should feel technical and credible without forcing participants to watch boilerplate typing. Each chapter combines concise explanation, one meaningful live development task, and a prepared checkpoint.

Use this rhythm:

```text
Concept -> Small live edit -> Run -> Inspect result -> Advance checkpoint
```

## Two-day chapter structure

| Time | Chapter | Theme | Delivery mode |
| --- | --- | --- | --- |
| Day 1 9:00 | Chapter 0 - The Mission | Scenario, goals, trust boundaries | Presentation and repo orientation |
| Day 1 10:00 | Chapter 1 - Hosted Agents | Runtime, deployment, BYO Registry | Show scaffold and deployment path |
| Day 1 11:00 | Chapter 2 - The Tool Boundary | MCP and Work IQ | Live-edit one tool contract |
| Day 1 1:00 | Chapter 3 - The Safety Rail | Compliance, policy, guardrails | Add one guardrail test live |
| Day 1 2:00 | Chapter 4 - Ground Truth | Foundry IQ and RAG | Build one evidence packet live |
| Day 1 3:00 | Chapter 5 - Agent Teamwork | Multi-agent orchestration | Show one specialist handoff |
| Day 1 4:00 | Chapter 6 - Day 1 Playback | Working reference flow | Run end-to-end demo |
| Day 2 9:00 | Chapter 7 - Observability | App Insights, Log Analytics, traces | Run KQL against prepared trace data |
| Day 2 10:00 | Chapter 8 - Human Review | HITL workflow | Demo approve/rework flow |
| Day 2 11:00 | Chapter 9 - Toolboxes | Reusable governed capabilities | Show toolbox manifest and scope model |
| Day 2 1:00 | Chapter 10 - Break It on Purpose | Failure injection | Run retrieval miss or policy denial |
| Day 2 2:00 | Chapter 11 - Evaluation Gates | Quality, safety, regression | Run eval suite and inspect failures |
| Day 2 3:00 | Chapter 12 - Pilot Readiness | Governance plan and roadmap | Decision workshop |
| Day 2 4:00 | Chapter 13 - Executive Playback | What Kaiser can pilot | Final demo and decisions |

## Coding style

Each coding chapter should include exactly one live edit:

| Chapter | Live task |
| --- | --- |
| Hosted Agents | Change one agent instruction or version value. |
| MCP and Work IQ | Add or tighten one field in a tool schema. |
| Guardrails | Add one prohibited-claim test. |
| RAG | Add one synthetic protocol snippet or evidence-packet field. |
| Multi-agent | Add one specialist handoff step. |
| Observability | Add one custom telemetry event or KQL query. |
| HITL | Change a task state from pending to rework. |
| Evaluation | Add one adversarial eval case. |

## Checkpoint strategy

Use git tags for stable chapter states:

```text
chapter-00-start
chapter-01-hosted-agent
chapter-02-mcp-tools
chapter-03-guardrails
chapter-04-rag
chapter-05-multi-agent
chapter-06-observability
chapter-07-hitl
chapter-08-evaluation
chapter-final
```

Use branches for instructor preparation:

```text
chapter/01-hosted-agent
chapter/02-mcp-tools
chapter/03-guardrails
chapter/04-rag
chapter/05-multi-agent
chapter/06-observability
chapter/07-hitl
chapter/08-evaluation
```

## Script strategy

Add a chapter advancement script:

```powershell
.\scripts\chapter.ps1 03
```

The script should:

1. Confirm the working tree state.
2. Move to the correct chapter checkpoint.
3. Copy prepared files for the chapter if needed.
4. Install dependencies only when required.
5. Run targeted validation.
6. Print the next instructor command.

## Demo reliability rules

1. Never type boilerplate live.
2. Keep a known-good checkpoint for every chapter.
3. Run each chapter from a clean terminal and predictable folder.
4. Keep local-only secrets and tenant-specific values out of the repo.
5. Have screenshots or static output ready for cloud/network failures.
6. Treat every failure as a teaching moment only if it fits the timebox.

