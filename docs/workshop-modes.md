# Workshop Modes

This repository runs in two distinct modes. Scout (workshop orchestrator) decides which mode is
active; GitHub Copilot executes delegated dev work inside whichever mode is in play.

| Mode | Purpose | Audience | Primary docs |
| --- | --- | --- | --- |
| **Mode 1 — Pre-Workshop Validation** | Build, deploy, and validate the complete solution on Azure + Microsoft Foundry, then tag a known-good release. | Delivery team, before the event. | `docs/mode-1-pre-workshop-validation.md` |
| **Mode 2 — Workshop Run-of-Show** | Deliver the two-day workshop chapter by chapter from prepared checkpoints. | Facilitators, during the event. | `workshop-assets/run-of-show.md`, `docs/chapter-delivery-model.md` |

## How the modes relate

```
Mode 1 (validate everything) ──produces──> tags: solution-validated-*, chapter-*  ──used by──> Mode 2 (deliver)
```

Mode 1 proves the whole thing works end to end on real infrastructure and freezes it as tags.
Mode 2 never builds cloud infra live; it advances through the pre-made chapter checkpoints.

## Git tag strategy (shared)

Two tag families, both created during Mode 1 so Mode 2 is deterministic.

### Release tags (Mode 1 output)
- `solution-validated-YYYYMMDD` — full solution built, deployed, and smoke-tested on Azure/Foundry.
- `solution-local-YYYYMMDD` — full solution validated locally (no cloud), fallback baseline.

### Chapter checkpoint tags (Mode 2 rails)
One tag per chapter state, matching `workshop-assets/run-of-show.md`:

```
chapter-00-start
chapter-01-backend-tests
chapter-02-mcp-validate
chapter-03-guardrails
chapter-04-rag
chapter-05-multi-agent
chapter-06-observability
chapter-07-hitl
chapter-09-toolboxes
chapter-final
```

Rules:
- Tags are immutable once the workshop is scheduled. Re-cut with a `-v2` suffix if a fix is required.
- Every tag must pass `scripts/validate-solution.ps1` before it is created.
- Chapter tags are cut in order so each builds on the previous.

## Switching modes

| Action | Command |
| --- | --- |
| Validate full solution (Mode 1) | `./scripts/validate-solution.ps1` |
| Cut a validated release tag (Mode 1) | see `docs/mode-1-pre-workshop-validation.md` |
| Jump to a chapter checkpoint (Mode 2) | `./scripts/chapter.ps1 <chapter-tag>` |
| Return to latest | `git checkout main` |

## Guardrails (both modes)

- Synthetic data only; no PHI; no secrets committed.
- Do not deploy to Azure/Foundry without Scout + human approval (Mode 1 only, deliberate).
- Preserve the safety boundary in `.github/copilot-instructions.md`.
