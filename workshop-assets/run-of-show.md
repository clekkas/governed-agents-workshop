# Workshop Run-of-Show

Orchestration guide for delivering the two-day workshop while GitHub Copilot builds the
delegated development items. Scout owns this document. Pair it with:

- `docs/chapter-delivery-model.md` (chapter timing + live-edit rhythm)
- `docs/requirements/dev-backlog.md` (WI-01…WI-08)
- `docs/requirements/copilot-agent-plan-prompts.md` (paste-ready prompts)

Delivery rhythm per chapter: **Concept → Small live edit → Run → Inspect result → Advance checkpoint.**
Prep the checkpoint before the room; demo one meaningful moment live; reveal the finished state.

---

## Day 1 — Build the agent (9:00 AM – 4:00 PM)

| Time | Chapter | Key item | Backlog item | Live-demo moment | Checkpoint tag |
| --- | --- | --- | --- | --- | --- |
| 9:00 | Ch 0 — Introduction & scenario | — | — | Open the running UI; show worklist → case → exception packet → HITL. Show the trust-boundary card. | chapter-00-start |
| 9:30 | Ch 1 — Hosted Agents + BYO Registry | Item 1 | WI-08 (plan only) | Show `agents/` manifests + `backend/` orchestrator; explain hosted-agent target; run `/api/health`. | chapter-01-backend-tests |
| 11:00 | Ch 2 — MCP Server (Work IQ) | Item 2 | WI-02 | Live: tighten one field in an MCP schema; run tool-contract validation; show allow/redact/deny. | chapter-02-mcp-validate |
| 1:00 | Ch 3 — Compliance: Policy & Guardrails | Item 3 | WI-03 | Live: add one prohibited-claim check; run the guardrail test; show a blocked "safe to discharge". | chapter-03-guardrails |
| 2:30 | Ch 4 — Foundry IQ, Building RAG | Item 4 | WI-04 | Live: add one synthetic protocol doc; re-run P0310; show missing-evidence escalation vs a cited answer. | chapter-04-rag |
| 3:45 | Ch 5 — Day 1 playback | — | — | Full end-to-end run of one case; trace one correlation ID across agents; recap + Day 2 setup. | chapter-05-multi-agent |

## Day 2 — Earn the right to trust it (9:00 AM – 2:00 PM)

| Time | Chapter | Key item | Backlog item | Live-demo moment | Checkpoint tag |
| --- | --- | --- | --- | --- | --- |
| 9:00 | Recap & environment check | — | — | Reconfirm Day 1 decisions and technical assumptions. | — |
| 9:15 | Ch 6 — LAW / Application Insights | Item 5 | WI-06 | Live: emit one custom event; hit `GET /api/v1/traces/:id`; walk the ordered event list; run a KQL sample. | chapter-06-observability |
| 10:45 | Ch 7 — HITL: Data Task Scheduler | Item 6 | WI-05 | Live: invoke P0147 → approve as care-manager; try approve as `agent` → 403; invoke P0310 → task created `Escalated`; `POST /tasks/sweep` with a short SLA → auto-escalate. Open `orchestrations/function_app.py` to show the same branches on the Durable Task Scheduler (`wait_for_external_event` + timer). Doc: `docs/hitl-durable-task-scheduler.md`. | chapter-07-hitl |
| 12:45 | Ch 8 — Toolboxes | Item 7 | WI-02 | Show the toolbox manifests + scopes; explain reuse across agents. | chapter-09-toolboxes |
| 1:45 | Ch 9 — Closeout & roadmap | — | WI-07 | Run the eval harness (golden pass + adversarial fail-closed); capture governance owners + 30/60/90 roadmap. | chapter-final |

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

- Ch 0: Here's the problem and the boundary.
- Ch 1: Here's where the agent runs (hosted agents + BYO registry).
- Ch 2: Here's how it's allowed to touch data (MCP / Work IQ).
- Ch 3: Here's what it's never allowed to say or do (policy + guardrails).
- Ch 4: Here's how it stays grounded (Foundry IQ + RAG).
- Ch 5: Here's the whole thing working (Day 1 playback).
- Ch 6: Here's how we see what it did (LAW / App Insights).
- Ch 7: Here's where the human stays in control (HITL scheduler).
- Ch 8: Here's how tools scale across agents (toolboxes).
- Ch 9: Here's what Kaiser proves and pilots next (eval + roadmap).
