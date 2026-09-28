# Kaiser Readmissions Agent Workshop

Two-day onsite workshop for Kaiser Permanente teams designing secure, governed, observable healthcare agent patterns with Microsoft Foundry, Hosted Agents, BYO Registry, MCP/Work IQ, Foundry IQ/RAG, Application Insights, Log Analytics Workspace, human-in-the-loop review, and toolboxes.

## Scenario

The running scenario is a **Discharge Transition Exception Coordinator** for care managers and ADT nurses. The agent consumes an approved risk score from a deterministic tool, summarizes minimum-necessary synthetic context, retrieves effective-dated transition protocols, identifies actionable discharge-transition gaps, drafts owner/due-time recommendations, and routes an exception packet for human review.

The assistant must not:

1. State that a patient is safe to discharge.
2. Alter discharge orders.
3. Make clinical determinations.
4. Share patient-specific details outside approved workflows.
5. Turn a draft transition-exception packet into action without human approval.
6. Generate, infer, recalculate, or override the approved risk score.

All sample data is synthetic. Do not use real PHI in this workshop repo unless Kaiser Permanente governance explicitly approves the environment and data-handling process.

## Repository modes

This repo runs in two modes — see `docs/workshop-modes.md`.

| Mode | Purpose | Entry point |
| --- | --- | --- |
| **Mode 1 — Pre-Workshop Validation** | Build/deploy/validate the full solution on Azure + Foundry, then tag a known-good release. | `docs/mode-1-pre-workshop-validation.md` · `scripts/validate-solution.ps1` |
| **Mode 2 — Workshop Run-of-Show** | Deliver the two-day workshop chapter by chapter from prepared checkpoints. | `workshop-assets/run-of-show.md` · `scripts/chapter.ps1` |

## Workshop agenda

| Day | Focus | Modules |
| --- | --- | --- |
| Day 1 | Secure foundation and governed data access | Introduction, Hosted Agents, BYO Registry, MCP/Work IQ, compliance policy, guardrails, Foundry IQ/RAG |
| Day 2 | Operational readiness | LAW/App Insights, HITL Data Task Scheduler, toolboxes, end-to-end flow, evaluation and release gates |

## Repository layout

```text
kaiser-readmissions-agent-workshop/
├── docs/                 # Architecture, governance, data dictionary, facilitator guide
├── lab-guide/            # Participant-facing modules
├── data/                 # Synthetic data generator and RAG source documents
├── fabric/               # Fabric notebooks, DAX, and KQL starter assets
├── agents/               # Hosted-agent starter contract and instructions
├── backend/              # Node.js/Express API + local orchestrator stub
├── mcp-server/           # MCP tool contracts and future implementation surface
├── governance/           # Governance plan, approval matrix, tool permissions
├── observability/        # Trace scenarios, failure injection, runbook
├── policy/               # Guardrails, PHI minimization, prohibited claims, test prompts
├── hitl/                 # Data Task Scheduler schemas and state machine
├── evaluation/           # Golden cases, adversarial cases, judge rubric, calibration set
├── app/                  # Optional review tracker app placeholder
├── scripts/              # Setup and validation scripts
└── workshop-assets/      # Agenda, deck outline, facilitator runbook
```

## Prerequisites

Participant prerequisites depend on which labs are enabled:

1. Microsoft Fabric workspace for data foundation, semantic model, Fabric IQ, Data Agent, and notebooks.
2. Microsoft Foundry access for hosted-agent concepts and evaluation workflows.
3. Azure subscription for Azure AI Search, Application Insights, Log Analytics Workspace, Container Registry, and supporting resources.
4. GitHub or Azure DevOps repository for CI/CD discussions.
5. Synthetic data only for hands-on labs.

## First setup

Generate local synthetic CSVs:

```powershell
python .\data\generate_synthetic_healthcare_data.py --output .\data\synthetic
```

Run the backend API (local orchestrator stub):

```powershell
cd .\backend
npm install
npm start
# http://127.0.0.1:8080/api/health
```

Run repository validation:

```powershell
.\scripts\validate.ps1
```

## Workshop storyline

Day 1: Build the agent.

Day 2: Earn the right to trust it.

Use one evolving synthetic use case across all modules: a multi-agent discharge-transition exception coordinator that retrieves, summarizes, consumes an approved risk score, cites protocols, detects transition gaps, drafts an exception packet, validates policy, and routes work for human review.

The initial specialist agents are:

1. Discharge Transition Orchestrator
2. Case Context Agent
3. Evidence Retrieval Agent
4. Policy Guardrail Agent
5. Transition Exception Agent
6. Transition Exception Agent
7. Human Review Agent

## Architecture overview

Start with `docs\solution-architecture-overview.md` for the complete solution architecture.

Diagram artifacts:

1. `workshop-assets\architecture-overview.svg`
2. `workshop-assets\architecture-overview.excalidraw`

## BYO Registry note

The BYO Registry module is intentionally scaffolded but not implemented yet. A separate local sample repo will be provided and incorporated when that module is built.

## License

License is not yet selected. Do not redistribute externally until a license and notice strategy are approved.
