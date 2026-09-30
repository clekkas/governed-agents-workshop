# Facilitator Delivery Plan — slide-keyed talk track + demo cues

How to actually *run the room* with `kaiser-consolidated-customer-deck.pptx` (23 slides) across the
two days. For each time block: **which slides you show**, **what you say** (first-person talk track),
and **exactly when to leave the deck for a demo, what to show, and what to run**.

Pairs with: `run-of-show.md` (chapter/checkpoint table), `demo-eval-runbook.md` (eval gate),
`facilitator-cheatsheet.md` (who-asks-what → which brief).

> The consolidated deck is a *customer storyline*, not a linear click-through. Day 1 uses slides
> **1–17 + 21**; Day 2 uses **18–20 + 22–25**. Present the slides listed per block, then break to the
> live surface. Chapter numbers (Ch0…Ch9) are stable topic tags from the run-of-show.

## Before you start (once, off-screen)

Two terminals up and warm, health checked, browser on the UI:

```powershell
# Terminal A — Python agent-service  :8081
cd .\agent-service
.\.venv\Scripts\python.exe -m uvicorn discharge_transition_agent.app:app --app-dir src --host 127.0.0.1 --port 8081

# Terminal B — Node backend + built UI  :8080
cd .\backend
$env:AGENT_SERVICE_URL = "http://127.0.0.1:8081"
npm start                    # http://127.0.0.1:8080
curl http://127.0.0.1:8080/api/health   # expect { status: "ok" }
```

Keep a third terminal free for demo commands. Synthetic data only — never set `EVAL_DEMO_BREAK`
outside the eval demo. Have static screenshots of each demo result as a network fallback.

---

# DAY 1 — Build the agent (9:00 AM – 4:00 PM)

## 9:00–9:30 · Ch 0 — Introduction & scenario · Slides 1–6

**Slides 1–2 (Title, Agenda).** "Good morning. Two days, and this is a *build* workshop, not
slideware — we deploy and operate one governed discharge-transition agent together and, by tomorrow
afternoon, prove it with an evaluation gate. We resequenced the agenda after our 9/29 call: MCP,
toolboxes, and Foundry IQ/RAG lead this morning; hosted agents and BYO registry moved to this
afternoon as tactical-later, exactly as you asked."

**Slide 3 (Why governed agents).** "The reason we're here: an agent is only adoptable if capability
and obligation ship together. Every capability you want comes with an obligation — that pairing is
why Day 2 is guardrails, observability, and human-in-the-loop."

**Slide 4 (Scenario).** "Here's the running example we'll demo against all day: a Discharge
Transition Exception Coordinator. It **consumes** an approved risk score — it never invents or
recalculates one — summarizes minimum-necessary context, cites effective-dated protocols, finds
transition gaps, drafts owner/due-time recommendations, and routes an exception packet to a care
manager. The human approves; the agent never acts alone."

**Slide 5 (Safety boundary).** "This is the safety contract — the six things it must never do:
say 'safe to discharge,' alter orders, make clinical determinations, leak patient detail, act
without approval, or touch the risk score. Whenever anyone asks 'but could it…' today, I'll come
back to this slide. The answer is designed-in refusal, not hope."

**Slide 6 (Reference architecture).** "And here's what we actually deploy — Foundry account +
project with hosted agents, a Container Apps app with an MCP tool boundary and Azure AI Search for
RAG, and a trust plane of managed identity, Key Vault, App Insights, and a Durable Task Scheduler
for the human gate. It's all Terraform, reproducible, synthetic data only."

**▶ DEMO CUE — end of Slide 6 (first time you leave the deck).**
Say: "Rather than describe it, let me show you the finished thing running." Switch to the browser at
`http://127.0.0.1:8080`.
- Show the **worklist** → click a **case** → point out the **approved-risk context**, the **RAG
  evidence with citations**, the **tool/policy calls**, and the **HITL review panel with the
  required reviewer-name gate**.
- Return to Slide 5 for one sentence: "Notice the packet says *draft* and needs a human — that's the
  boundary, live."
- No script to run here; the app is already up. Checkpoint tag: `chapter-00-start`.

## 9:30–10:45 · Ch 2 + Ch 8 — MCP Server (Work IQ) + Toolboxes · Slides 7–11

**Slide 7 (divider: "Your priorities").** "Now we go through the nine things your team raised, in
your order. First: how is this agent even *allowed* to touch data."

**Slide 8 (Secure MCP + Work IQ).**
> *Transcript after you advance to Slide 8:* "This is the answer to Sarita's core question — how do
> we secure the MCP server. Six layers: private network with a dedicated MCP subnet; identity-based
> auth through project connections — managed or agentic identity, a user's Entra token when it's
> per-user data, custom keys only as a last resort; least-privilege tool contracts with RBAC; the
> Toolbox as a single governed endpoint; human approval on any write tool; and always-on audit. The
> agent doesn't get a database password — it gets a scoped, logged, revocable identity."

**Slide 9 (Work IQ — governed M365 context).** "One clarification on Work IQ, because it's changed:
it's not just a pattern, it's a shipping Microsoft service you *consume* — a governed MCP/A2A/REST
layer over Microsoft 365 (mail, Teams, files, people, calendar). It runs on the user's own Entra
identity — delegated or on-behalf-of only, never app-only — so the agent sees only what that user
can, with sensitivity labels, DLP, and an OPA policy engine on every call. The clean split for you:
clinical and PHI data stays on *our* governed MCP tools; Work IQ is how the agent safely reaches the
*surrounding* M365 work context — a coordination Teams thread, a planning meeting summary — without
us building or securing that server. It's usage-billed via Copilot Credits, managed in the M365 admin
center. Brief: `docs/work-iq-overview.md`."

**Slide 10 (Where the MCP server runs).** "Quick deployment note, since it's the obvious question:
the *same* governed server runs two ways — a **stdio** subprocess locally (zero infra, what we demo),
or a **Container App with internal ingress** on Azure, private to the VNet — which is literally the
private-network layer of the secure-MCP slide. Contracts and decisions are identical; the agent just
routes to the internal URL. And Work IQ stays the *other* lane — Microsoft-hosted, consumed on the
user's identity — never merged with our clinical tools. Diagram:
`workshop-assets/mcp-workiq-deployment.svg`."

**Slide 11 (Toolboxes).** "The natural follow-on: govern once, reuse everywhere. A toolbox is one
governed endpoint that many agents share — this is where credential rotation and policy live, so you
don't re-secure every tool for every agent."

**▶ DEMO CUE — after Slide 11.**
Say: "Let me run the MCP chapter through our deploy runner, then tighten one contract so you see the
boundary bite."
- Run the **MCP chapter runner** (master → child) so the room sees the per-capability CI/CD pattern:
  ```powershell
  infra\scripts\deploy-chapters.ps1 -Chapters mcp
  ```
  It runs the **tool-contract validation** (7 contracts + drift self-test) and the **governed server
  tests** (redact / read-only score / draft-only / escalation) — all green.
- Live edit: open an MCP tool schema, **narrow one field** (e.g. make a returned field redacted /
  drop a scope), then re-run `deploy-chapters.ps1 -Chapters mcp` and show the **allow / redact / deny**
  decision change (or the validator failing loudly on drift).
- Optional: `python mcp-server/server.py` to show the **real MCP stdio server** is runnable; note
  Work IQ attaches as a *separate* governed connection (`mcp-server/connections/`).
- Reveal the finished state at checkpoint `chapter-02-mcp-validate`.
- Anchor docs if asked: `docs/securing-mcp-servers.md`, `docs/work-iq-overview.md`. If the edit runs
  long, cut to the checkpoint.

> **Hosted MCP + Work IQ — the "how is it deployed?" answer.** If asked where the MCP server *lives*,
> use `workshop-assets/mcp-workiq-deployment.svg` (the two-lane deployment diagram) and this track:
> "The **same** governed server runs two ways. Locally it's a **stdio** subprocess — zero infra,
> what you're watching now. In Azure it's a **Container App with *internal* ingress** — private to
> the environment's VNet, which *is* Layer 1 of the secure-MCP slide, not a public endpoint. Flip
> `enable_mcp_server=true` (or `deploy.ps1 -EnableMcpServer`) and the agent routes to it over the
> internal URL via `USE_EXTERNAL_MCP` + `MCP_SERVER_URL`; nothing else changes because the contracts
> and decisions are identical. **Work IQ is the other lane** — we don't deploy it, it's
> Microsoft-hosted; we *consume* it on the user's Entra on-behalf-of token, so PHI stays on our MCP
> server and M365 work context comes from Work IQ. Two lanes, one identity, never merged." One-liner
> if pressed on cost: "our MCP server is just a Container App you already pay for; Work IQ is
> usage-based Copilot Credits."

## 10:45–11:00 · Break

## 11:00–12:15 · Ch 4 — Foundry IQ, Building RAG · Slides 12–15

**Slide 12 (Foundry IQ + RAG).** "This is grounding. The differentiators from a naïve RAG demo:
we build the **evidence packet before the answer**, and we **measure retrieval first**. If the
evidence isn't there, the agent escalates instead of guessing."

**Slide 13 (The RAG domain — deep dive).** "For the engineers in the room: here's the whole RAG
domain as a pipeline — **sources → ingest → retrieve → ground → measure**. Note diagnosis-scoping (a
CHF protocol can't ground a COPD case), claim-level citations, missing-evidence escalation, and a
measured retrieval gate. And the key graduation point: today it's a local KnowledgeBase; you swap in
Foundry IQ / Azure AI Search **under the same retrieval contract**, so the agents don't change.
Full picture: `workshop-assets/rag-domain.svg`; flow: `docs/rag-retrieval-flow.md`."

**Slide 14 (Search reuse + cost).** "This was your most-raised, critical question — can app teams
reuse the Search/Cosmos/Storage that Foundry provisions, or do they pay twice. Standard setup is
BYO: reuse existing or let Foundry provision. The real cost win is **Azure AI Search** — one
always-on service backing both agent vector stores and app RAG indexes. Cosmos and Storage are
consumption-priced, so little saving there. The caveat that matters: capability connections are
**immutable** — build on *separate* indexes/DBs/containers, never the agent's own."

**Slide 15 (SharePoint / O365 ingest).** "Matt's ask — RAG over SharePoint PDFs, PPT, Word, Excel.
Two patterns, and the one caveat to remember is **ACL trimming** on the indexed path so retrieval
honors permissions."

**▶ DEMO CUE — after Slide 15.**
Say: "Let me show grounding actually holding the line."
- Live edit: **add one synthetic protocol doc** to the knowledge source.
- **Re-run case P0310** and show **missing-evidence escalation** vs. a **cited answer** once the doc
  is present.
- Command (third terminal), then read the returned `correlationId`/citations:
  ```powershell
  Invoke-RestMethod -Method Post http://127.0.0.1:8080/api/v1/agent/invoke `
    -ContentType application/json -Body '{"caseId":"P0310","actorRole":"care_manager"}'
  ```
- Checkpoint `chapter-04-rag`. Docs: `existing-vs-foundry-search.md`,
  `capability-host-reuse-and-cost.md`.

## 12:15–1:00 · Lunch

## 1:00–2:15 · Ch 3 — Compliance: Policy & Guardrails · Slide 16

**Slide 16 (Guardrails + healthcare content safety).** "Now the flip side of the boundary — what it
must never *say*. This is Sarita's content-safety concern: the filter that blocks legitimate medical
questions, the 'Tylenol' false positive. The answer is layered tuning plus a ticket path, so a
benign clinical prompt passes but 'patient is safe to discharge' is still blocked."

**▶ DEMO CUE — after Slide 16.**
- Live edit: **add one prohibited-claim check**.
- Run the **guardrail test**; show a **blocked 'safe to discharge'**, and a **benign clinical prompt
  passing** (the Tylenol case). Doc: `docs/healthcare-content-safety.md`.

## 2:15–2:30 · Break

## 2:30–3:45 · Ch 1 — Hosted Agents + BYO Registry · Slide 17

**Slide 17 (Agent-type decision).** "You asked for the decision criteria. Default to a **prompt
agent**; graduate to a **hosted agent** the moment you need custom orchestration, multi-agent
handoffs, an existing framework, or your own code — which is exactly why *this* discharge use case is
hosted. BYO Registry we'll show as a sample end-to-end only; it's not something we pre-staged."

**▶ DEMO CUE — after Slide 17 (show, don't live-edit).**
- Open the `agents/` manifests and the `backend/` orchestrator; explain the hosted-agent target.
- Prove it's alive: `curl http://127.0.0.1:8080/api/health`. Checkpoint `chapter-01-backend-tests`.
- Doc: `docs/agent-type-decision.md`. Frame BYO AKS as roadmap/futures.

## 3:45–4:00 · Ch 5 — Day 1 playback · Slide 21

**Slide 21 (End-to-end).** "Let's see the whole thing work before we close." Then break to the demo.

**▶ DEMO CUE — after Slide 21.**
- Run **one case start to finish** in the UI, then pull its trace and walk the ordered events:
  ```powershell
  $r = Invoke-RestMethod -Method Post http://127.0.0.1:8080/api/v1/agent/invoke `
    -ContentType application/json -Body '{"caseId":"P0147","actorRole":"care_manager"}'
  Invoke-RestMethod "http://127.0.0.1:8080/api/v1/traces/$($r.correlationId)"
  ```
- "One correlation ID, every agent handoff and policy decision in order." Checkpoint
  `chapter-05-multi-agent`. Recap open risks, set up Day 2.

---

# DAY 2 — Earn the right to trust it (9:00 AM – 2:00 PM)

## 9:00–9:15 · Recap & environment check
Reconfirm Day 1 decisions; re-run the health check. (Optionally re-show Slides 4–5 for the boundary.)

## 9:15–10:30 · Ch 6 — LAW / Application Insights · Slide 18

**Slide 18 (Observability + CMK/AMPLS).** "Two things at once: how we see what the agent did, and how
we keep PHI safe while doing it. Every request carries an `x-correlation-id`; we can replay the exact
ordered event list. And because request/response content in Foundry logs can hold PHI, the posture
is a **dedicated Log Analytics cluster + customer-managed keys + AMPLS** — Lee leads this one."

**▶ DEMO CUE — after Slide 18.**
- Invoke a case, copy its `x-correlation-id`, then `GET /api/v1/traces/:id` and walk the
  **tool.called** policy decisions, the **agent.handoff** chain, and the **review.transition**:
  ```powershell
  $r = Invoke-RestMethod -Method Post http://127.0.0.1:8080/api/v1/agent/invoke `
    -ContentType application/json -Body '{"caseId":"P0147","actorRole":"care_manager"}'
  Invoke-RestMethod "http://127.0.0.1:8080/api/v1/traces/$($r.correlationId)"
  ```
- Show the **live Backend activity log panel** in the UI. Checkpoint `chapter-06-observability`.
  Doc: `docs/observability-correlation-trace.md`.

## 10:30–10:45 · Break

## 10:45–12:00 · Ch 7 — HITL: Data Task Scheduler · Slide 19

**Slide 19 (HITL / Durable Task Scheduler).** "This is the capstone and it's running today — where
the human stays in control. Three behaviors: a valid approval goes through, an illegal transition is
refused, and an overdue task auto-escalates on an SLA timer."

**▶ DEMO CUE — after Slide 19.** Primary surface is the **UI** (worklist → case → Approve with the
required reviewer name). Under-the-hood / backup via API:
- **Approve** P0147 as the care manager → task moves to Approved.
- **Wrong actor** (approve as `agent`) → **403**, refused.
- Invoke **P0310** → task created **Escalated** (policy path).
- Force the SLA timer with a short window → auto-escalate:
  ```powershell
  Invoke-RestMethod -Method Post http://127.0.0.1:8080/api/v1/tasks/sweep
  ```
- Open `agent-service/orchestrations/function_app.py` to show the **same branches** on the Durable
  Task Scheduler (`wait_for_external_event` + timer). Checkpoint `chapter-07-hitl`.
  Exact actor/role strings and task IDs: see `run-of-show.md` Ch 7 and `docs/hitl-durable-task-scheduler.md`.

## 12:00–12:45 · Lunch

## 12:45–1:45 · Ch 9 — Ops & governance Q&A · Slide 20 (+ recall 14)
**Slide 20 (divider: "Prove it + plan it").** Open Q&A. Drive answers with the cheat-sheet: reuse +
cost (`capability-host-reuse-and-cost.md`) and secure MCP (`securing-mcp-servers.md`); recall Slide 14
for the cost point. Cover BYO AKS + Foundry roadmap as futures.

## 1:45–2:00 · Ch 9 — Closeout & roadmap · Slides 22–25

**Slide 22 (Evaluation gate).** "Before you trust it, prove it — safety is testable and enforced in
CI." Then run the eval demo.

**▶ DEMO CUE — Slide 22 (the money demo, ~4 min, offline, no code editing).**
```powershell
.\scripts\demo-eval.ps1        # Enter advances each step
```
Arc: **green (6/6, exit 0)** → inject one flag `EVAL_DEMO_BREAK=risk_score` → **red / gate blocked
(exit 1)** → revert → **green**. Talk track: "That's the exact adv-003 attack — the agent lowering
the approved score. The gate named the violation and returned non-zero; in CI this **blocks the
merge**. Same command a GitHub Actions job runs on every PR." Full script: `demo-eval-runbook.md`.

**Slide 23 (Roadmap).** "Here's a concrete, cost-aware 30/60/90 tied to your priorities and the
two-quarter window you care about." Capture governance owners.

**Slide 24 (Where to go deeper).** "Leave-behind: source-grounded briefs by topic, each citing
current Microsoft Learn. The facilitator cheat-sheet maps each of your questions to the right brief."

**Slide 25 (Close).** "The through-line for two days: we didn't choose between capability and
governance — we built them together, in the order you asked for. Thank you."

---

## Quick demo-command reference

| Moment | Command |
| --- | --- |
| Health check | `curl http://127.0.0.1:8080/api/health` |
| MCP chapter runner | `infra\scripts\deploy-chapters.ps1 -Chapters mcp` (validate) · add `-Deploy` for deploy actions |
| Invoke a case | `Invoke-RestMethod -Method Post http://127.0.0.1:8080/api/v1/agent/invoke -ContentType application/json -Body '{"caseId":"P0147","actorRole":"care_manager"}'` |
| Read the trace | `Invoke-RestMethod "http://127.0.0.1:8080/api/v1/traces/<correlationId>"` |
| Force SLA escalation | `Invoke-RestMethod -Method Post http://127.0.0.1:8080/api/v1/tasks/sweep` |
| Eval release gate | `.\scripts\demo-eval.ps1` |

Cases: `P0147` (approve path), `P0310` (escalation path). Checkpoints per block are in `run-of-show.md`.
