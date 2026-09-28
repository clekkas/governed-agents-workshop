# Requirements & Delegation

This folder is the handoff surface between **Scout** (workshop orchestrator) and
**GitHub Copilot** (development implementer in VS Code).

| File | Purpose |
| --- | --- |
| `functional-requirements.md` | What the system must do. |
| `technical-requirements.md` | Stack, API contract, tool rules, validation. |
| `dev-backlog.md` | Prioritized, delegable work items with acceptance criteria. |
| `copilot-agent-plan-prompts.md` | Copy-paste prompts for Copilot Agent/plan mode. |

Also see:

- `.github/copilot-instructions.md` — repo-wide grounding Copilot reads automatically.
- `docs/chapter-delivery-model.md` — chapter/checkpoint delivery and live-coding model.
- `docs/solution-architecture-overview.md` — full architecture.
- `docs/use-case-blueprint.md` — the use case and multi-agent design.

## Roles

- **Scout** owns the workshop narrative, sequencing, requirements, and prioritization.
- **GitHub Copilot** owns delegated development inside the guardrails above.
- The human reviews plans, approves cloud actions, and confirms safety-boundary decisions.
