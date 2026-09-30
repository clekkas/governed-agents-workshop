# Workshop Run-of-Show

Orchestration guide for delivering the two-day workshop while GitHub Copilot builds the
delegated development items. Scout owns this document. Pair it with:

- `facilitator-delivery-plan.md` (slide-keyed talk track + per-block demo cues and commands)
- `docs/chapter-delivery-model.md` (chapter timing + live-edit rhythm)
- `docs/requirements/dev-backlog.md` (WI-01…WI-08)
- `docs/requirements/copilot-agent-plan-prompts.md` (paste-ready prompts)

Delivery rhythm per chapter: **Concept → Small live edit → Run → Inspect result → Advance checkpoint.**
Prep the checkpoint before the room; demo one meaningful moment live; reveal the finished state.

---

## Day 1 — Build the agent (9:00 AM – 4:00 PM)

> Reordered per the 9/29 planning call: MCP + Toolboxes + Foundry IQ lead the morning; Hosted Agents
> + BYO Registry demoted to the afternoon. Chapter tags/numbers are stable topic identities.

| Time | Chapter | Key item | Backlog item | Live-demo moment | Checkpoint tag |
| --- | --- | --- | --- | --- | --- |
| 9:00 | Ch 0 — Introduction & scenario | — | — | Open the running UI; show worklist → case → exception packet → HITL. Show the trust-boundary card. | chapter-00-start |
| 9:30 | Ch 2 + Ch 8 — MCP Server (Work IQ) + Toolboxes | Items 2, 7 | WI-02 | Live: tighten one field in an MCP schema; run tool-contract validation; show allow/redact/deny. Frame the **secure-MCP** six layers (`docs/securing-mcp-servers.md`) and the toolbox as one governed endpoint. | chapter-02-mcp-validate |
| 11:00 | Ch 4 — Foundry IQ, Building RAG | Item 4 | WI-04 | Live: add one synthetic protocol doc; re-run P0310; show missing-evidence escalation vs a cited answer. Cover **existing-vs-Foundry Search** and **capability-host reuse + cost** (`docs/capability-host-reuse-and-cost.md`). | chapter-04-rag |
| 1:00 | Ch 3 — Compliance: Policy & Guardrails | Item 3 | WI-03 | Live: add one prohibited-claim check; run the guardrail test; show a blocked "safe to discharge". Cover **healthcare content-safety false positives** (the "Tylenol" case) + layered filtering. | chapter-03-guardrails |
| 2:30 | Ch 1 — Hosted Agents + BYO Registry | Item 1 | WI-08 (plan only) | Show `agents/` manifests + `backend/` orchestrator; explain hosted-agent target; run `/api/health`. Walk the **hosted-vs-prompt-vs-custom** decision. | chapter-01-backend-tests |
| 3:45 | Ch 5 — Day 1 playback | — | — | Full end-to-end run of one case; trace one correlation ID across agents; recap + Day 2 setup. | chapter-05-multi-agent |

## Day 2 — Earn the right to trust it (9:00 AM – 2:00 PM)

| Time | Chapter | Key item | Backlog item | Live-demo moment | Checkpoint tag |
| --- | --- | --- | --- | --- | --- |
| 9:00 | Recap & environment check | — | — | Reconfirm Day 1 decisions and technical assumptions. | — |
| 9:15 | Ch 6 — LAW / Application Insights | Item 5 | WI-06 | Live: invoke a case, copy its `x-correlation-id`, `GET /api/v1/traces/:id` → walk the ordered event list (tool.called policy decisions, agent.handoff chain, review.transition). Show the live Backend activity log panel. Frame **dedicated LAW cluster + CMK + AMPLS** for PHI in request/response (Lee leads). Doc: `docs/observability-correlation-trace.md`. | chapter-06-observability |
| 10:45 | Ch 7 — HITL: Data Task Scheduler | Item 6 | WI-05 | Live: invoke P0147 → approve as care-manager; try approve as `agent` → 403; invoke P0310 → task created `Escalated`; `POST /tasks/sweep` with a short SLA → auto-escalate. Open `orchestrations/function_app.py` to show the same branches on the Durable Task Scheduler (`wait_for_external_event` + timer). Doc: `docs/hitl-durable-task-scheduler.md`. | chapter-07-hitl |
| 12:45 | Ch 9 — Day-2 ops & governance Q&A | — | — | Open Q&A with product managers on the two hot topics (hosted agents, observability). Anchor answers on `docs/capability-host-reuse-and-cost.md` (reuse + cost) and `docs/securing-mcp-servers.md` (secure MCP). Cover BYO AKS + Foundry roadmap as futures. | — |
| 1:45 | Ch 9 — Closeout & roadmap | — | WI-07 | Run `scripts\demo-eval.ps1` (green → inject `EVAL_DEMO_BREAK=risk_score` → red/gate-blocked → revert → green) — no code editing. Runbook: `workshop-assets\demo-eval-runbook.md`. Capture governance owners + 30/60/90 roadmap. | chapter-final |

---

## Pre-workshop prep (Scout + implementer)

1. Have Copilot complete WI-01…WI-07 ahead of time; keep each as a tagged checkpoint/branch.
2. For each chapter, prepare: the "before" checkpoint, the one live edit, and the "after" reveal.
3. Dry-run every live-demo moment once from a clean terminal.
4. Keep static screenshots of each demo result as a network/cloud fallback.
5. Confirm synthetic data only; no tenant secrets on screen.

## Orchestration cues for Scout (me)

- Before each chapter, I post the concept framing and the single live edit to perform.
- I hold the checkpoint tags and tell you when to reveal the finished state.
- If a live edit runs long, I cut to the prepared checkpoint to protect timing.
- I track decisions, risks, and owners in the closeout structure of the facilitator runbook.

## The one-line story per chapter

Delivered in this order (chapter numbers are stable topic tags):

- Ch 0: Here's the problem and the boundary.
- Ch 2 + Ch 8: Here's how it's allowed to touch data, and how tools scale (MCP / Work IQ + toolboxes).
- Ch 4: Here's how it stays grounded (Foundry IQ + RAG).
- Ch 3: Here's what it's never allowed to say or do (policy + guardrails).
- Ch 1: Here's where the agent runs (hosted agents + BYO registry).
- Ch 5: Here's the whole thing working (Day 1 playback).
- Ch 6: Here's how we see what it did, and keep PHI safe (LAW / App Insights + dedicated cluster / CMK / AMPLS).
- Ch 7: Here's where the human stays in control (HITL scheduler).
- Ch 9: Here's what's reusable and what it costs, and what Kaiser pilots next (governance Q&A + eval + roadmap).
