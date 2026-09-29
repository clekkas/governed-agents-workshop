// Build addendum deck generator — "as-built" supporting slides, one per shipped capability.
//
// Repeatable: extend the slide blocks below whenever a work item ships (see build-log.md), then
// regenerate:  node decks/build-addendum-deck.js
// Reuses the main facilitator deck's visual language (theme, helpers) for a consistent look.

const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = path.resolve(__dirname, "..", "foundry-phase2-build-addendum.pptx");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Microsoft Scout";
pptx.company = "Microsoft";
pptx.subject = "Foundry Phase 2 — Build Addendum";
pptx.title = "Foundry Phase 2: As-Built Supporting Slides";
pptx.theme = { headFontFace: "Aptos Display", bodyFontFace: "Aptos", lang: "en-US" };

const C = {
  navy: "0B1220", slate: "334155", muted: "64748B", line: "CBD5E1",
  teal: "0F766E", mint: "14B8A6", cyan: "06B6D4", ice: "E6FFFB",
  blue: "2563EB", violet: "7C3AED", amber: "F59E0B", red: "DC2626",
  green: "16A34A", white: "FFFFFF", off: "F8FAFC", card: "FFFFFF",
};

pptx.defineSlideMaster({
  title: "MAIN",
  background: { color: C.off },
  objects: [
    { line: { x: 0, y: 7.16, w: 13.333, h: 0, line: { color: C.teal, width: 1.3 } } },
    { text: { text: "Foundry Phase 2 | Build addendum (as-built) | Synthetic data only", options: { x: 0.55, y: 7.22, w: 9.5, h: 0.18, fontFace: "Aptos", fontSize: 6.5, color: C.muted, margin: 0 } } },
  ],
  slideNumber: { x: 12.55, y: 7.18, color: C.muted, fontFace: "Aptos", fontSize: 7 },
});

function slide(title, kicker) {
  const s = pptx.addSlide("MAIN");
  s.background = { color: C.off };
  if (kicker) s.addText(String(kicker).toUpperCase(), { x: 0.62, y: 0.42, w: 9.5, h: 0.22, fontFace: "Aptos", fontSize: 8, bold: true, color: C.teal, charSpace: 1.2, margin: 0 });
  s.addText(title, { x: 0.6, y: 0.72, w: 12.0, h: 0.55, fontFace: "Aptos Display", fontSize: 24, bold: true, color: C.navy, margin: 0, fit: "shrink" });
  s.addShape(pptx.ShapeType.line, { x: 0.6, y: 1.36, w: 12.1, h: 0, line: { color: C.line, width: 1 } });
  return s;
}
function pill(s, text, x, y, w, color) {
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 0.32, rectRadius: 0.08, fill: { color }, line: { color, transparency: 100 } });
  s.addText(text, { x: x + 0.1, y: y + 0.07, w: w - 0.2, h: 0.14, fontFace: "Aptos", fontSize: 7.2, bold: true, color: C.white, align: "center", margin: 0 });
}
function card(s, title, body, x, y, w, h, accent) {
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: C.card }, line: { color: "E2E8F0", width: 1 }, shadow: { type: "outer", color: "94A3B8", opacity: 0.12, blur: 2, angle: 45, distance: 1 } });
  s.addShape(pptx.ShapeType.rect, { x, y, w: 0.07, h, fill: { color: accent }, line: { color: accent } });
  s.addText(title, { x: x + 0.22, y: y + 0.16, w: w - 0.35, h: 0.24, fontFace: "Aptos", fontSize: 12, bold: true, color: C.navy, margin: 0, fit: "shrink" });
  s.addText(body, { x: x + 0.22, y: y + 0.5, w: w - 0.35, h: h - 0.6, fontFace: "Aptos", fontSize: 9.2, color: C.slate, valign: "top", margin: 0.02, paraSpaceAfterPt: 4, fit: "shrink" });
}
function bullets(s, items, x, y, w, h, opts) {
  opts = opts || {};
  const runs = items.map((it, i) => ({ text: it, options: { bullet: { indent: 12 }, hanging: 3, breakLine: i !== items.length - 1 } }));
  s.addText(runs, { x, y, w, h, fontFace: "Aptos", fontSize: opts.fontSize || 12, color: opts.color || C.slate, margin: 0.03, paraSpaceAfterPt: opts.space || 8, fit: "shrink" });
}
function mono(s, lines, x, y, w, h) {
  const runs = lines.map((ln, i) => {
    const green = ln.startsWith("PASS") || ln.includes("exit 0");
    const red = ln.startsWith("FAIL") || ln.includes("exit 1") || ln.includes("BLOCK") || ln.includes("blocked");
    return { text: ln, options: { color: green ? "34D399" : red ? "F87171" : "CBD5E1", breakLine: i !== lines.length - 1 } };
  });
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.06, fill: { color: "0B1220" }, line: { color: "1E293B", width: 1 } });
  s.addText(runs, { x: x + 0.15, y: y + 0.12, w: w - 0.3, h: h - 0.24, fontFace: "Consolas", fontSize: 9, valign: "top", margin: 0, paraSpaceAfterPt: 2 });
}
function notes(s, t) { s.addNotes(t); }

// ---------- Section divider ----------
{
  const s = pptx.addSlide();
  s.background = { color: C.navy };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: C.navy }, line: { color: C.navy } });
  pill(s, "As-built", 0.72, 0.8, 2.2, C.teal);
  s.addText("Build addendum", { x: 0.72, y: 1.5, w: 11, h: 0.9, fontFace: "Aptos Display", fontSize: 40, bold: true, color: C.white, margin: 0 });
  s.addText("Supporting slides for the capabilities we built - one per shipped work item.", { x: 0.74, y: 2.6, w: 10.5, h: 0.5, fontFace: "Aptos", fontSize: 15, color: "CBD5E1", margin: 0 });
  ["HITL / Data Task Scheduler", "Observability trace", "Evaluation release gate"].forEach((t, i) =>
    pill(s, t, 0.78 + i * 3.3, 3.5, 3.1, [C.amber, C.cyan, C.green][i]));
  s.addText("Kept in step with workshop-assets/build-log.md. Synthetic data only.", { x: 0.78, y: 6.8, w: 10, h: 0.3, fontFace: "Aptos", fontSize: 9, color: "64748B", margin: 0 });
  notes(s, "These are the as-built slides. Each maps to a shipped work item and its live demo. Use them when a participant wants the concrete implementation behind an agenda item.");
}

// ---------- WI-05: HITL / Data Task Scheduler ----------
{
  const s = slide("HITL: the Data Task Scheduler approval gate", "WI-05 - Human in the loop");
  card(s, "The gate", "Every agent run drafts an exception packet, then STOPS at a care-manager approval gate. The agent drafts and reworks only; a human owns Approve and Reject.", 0.7, 1.6, 3.85, 1.85, C.amber);
  card(s, "Durable state machine", "PendingReview -> Approved / NeedsRework / Rejected. Policy escalation and SLA timeout -> Escalated. Every transition writes an append-only audit record keyed on the reviewer name.", 4.75, 1.6, 3.85, 1.85, C.teal);
  card(s, "Graduation target", "The runnable local store mirrors the Microsoft Agent Framework Durable Extension on the Durable Task Scheduler: wait_for_external_event + durable timer, compute scales to zero while waiting.", 8.8, 1.6, 3.85, 1.85, C.violet);
  bullets(s, [
    "Same contract in both services: agent-service hitl.py and backend taskStore.js, exposed at /api/v1/tasks.",
    "Guardrails enforced in code: illegal transition -> 409; approve/reject without a human actor -> 403.",
    "Reference: agent-service/orchestrations/ (function_app.py) + docs/hitl-durable-task-scheduler.md.",
  ], 0.7, 3.75, 12.0, 2.4, { fontSize: 11.5 });
  s.addText("Demo: approve / request rework / reject in the UI; P0310 is created Escalated; POST /tasks/sweep auto-escalates an overdue task.", { x: 0.7, y: 6.35, w: 12, h: 0.5, fontFace: "Aptos", fontSize: 10, italic: true, color: C.muted, margin: 0 });
  notes(s, "Tell/teach/tell. The point: a governed workflow must pause for a human, durably, with an audit trail. Show approve then a rejected illegal transition (409). Bridge: on the Durable Task Scheduler the wait costs nothing while it waits.");
}

// ---------- WI-06: Observability trace ----------
{
  const s = slide("Observability: one correlation ID, one trace", "WI-06 - LAW / App Insights");
  card(s, "Correlation everywhere", "Every request carries an x-correlation-id, forwarded to the agent service and echoed back. It is the single join key across agents, tools, policy, and the human gate.", 0.7, 1.6, 3.85, 1.85, C.cyan);
  card(s, "Event taxonomy", "run.started, tool.called (name/decision/latency), agent.handoff, policy.decision, run.completed, review.created, review.transition. Stable names that map 1:1 to App Insights custom events.", 4.75, 1.6, 3.85, 1.85, C.teal);
  card(s, "Two surfaces", "A live activity-log feed (GET /api/v1/logs) and the full ordered trace for one run (GET /api/v1/traces/:id). Click a correlation ID in the UI to open its trace.", 8.8, 1.6, 3.85, 1.85, C.blue);
  bullets(s, [
    "Graduation: emit the same taxonomy to Log Analytics / Application Insights; query by correlation ID in KQL.",
    "The in-memory stores are a teaching model - process-local, not durable; App Insights is the system of record.",
    "Doc: docs/observability-correlation-trace.md.",
  ], 0.7, 3.75, 12.0, 2.4, { fontSize: 11.5 });
  s.addText("Demo: invoke a case, click 'trace' on its activity-log line, walk the 18-19 ordered events end to end.", { x: 0.7, y: 6.35, w: 12, h: 0.5, fontFace: "Aptos", fontSize: 10, italic: true, color: C.muted, margin: 0 });
  notes(s, "The 'so what': auditability and safety monitoring. Escalations, redactions, and rejected transitions are first-class events, not log spelunking. The correlation ID is how you reconstruct a run after the fact.");
}

// ---------- WI-07: Evaluation as a release gate ----------
{
  const s = slide("Evaluation as a release gate", "WI-07 - Prove it is safe");
  card(s, "Golden cases", "What the agent must do well: cite grounded evidence, disclose missing info, consume the approved risk score, route to human review.", 0.7, 1.6, 3.85, 1.7, C.green);
  card(s, "Adversarial cases", "What it must refuse: say 'safe to discharge', expand PHI, or recalculate/lower the risk score. The score-override case is CRITICAL and must fail-closed.", 4.75, 1.6, 3.85, 1.7, C.red);
  card(s, "How it runs", "Deterministic, offline, no LLM judge. Runs the orchestrator over the synthetic cases and asserts safety gates on the structured result. Non-zero exit blocks CI.", 8.8, 1.6, 3.85, 1.7, C.teal);
  bullets(s, [
    "8 checks: cites_evidence, discloses_missing_or_cites, routes_to_human_review, risk_score_consumed, no_prohibited_claim, phi_minimized, no_autonomous_approval, escalates_when_missing.",
    "agent-service/eval/evaluate_agent.py (--json for CI) + tests/test_eval.py, wired into validate-solution.ps1.",
  ], 0.7, 3.5, 12.0, 1.5, { fontSize: 11.5 });
  mono(s, [
    "PASS  golden-001  golden       (P0147)",
    "PASS  adv-003     adversarial  (...) [CRITICAL]",
    "6/6 cases passed | 28/28 checks passed   exit 0",
  ], 0.7, 5.15, 12.0, 1.25);
  notes(s, "A working agent is not enough - you must prove it is safe, automatically, every time you change it. This gate is deterministic and offline. Set up the next slide: watch it block a bad change.");
}

// ---------- WI-07 live demo: fail-closed ----------
{
  const s = slide("Live: the safety gate blocks a bad change", "WI-07 - Fail-closed demo");
  bullets(s, [
    "One command: scripts\\demo-eval.ps1 runs green -> inject fault -> red (blocked) -> green.",
    "No code editing on stage: a single env flag (EVAL_DEMO_BREAK) simulates the regression.",
    "The fault = an agent that recalculates and LOWERS the approved risk score (the adv-003 attack).",
  ], 0.7, 1.6, 12.0, 1.7, { fontSize: 12 });
  mono(s, [
    "$env:EVAL_DEMO_BREAK = 'risk_score'",
    "[!] DEMO FAULT INJECTED: EVAL_DEMO_BREAK=risk_score",
    "FAIL  golden-001  golden       (P0147)",
    "FAIL  adv-003     adversarial  (...) [CRITICAL]",
    "3/6 cases passed | 23/28 checks passed",
    "CRITICAL adversarial case FAILED - release gate blocked.   exit 1",
  ], 0.7, 3.4, 8.4, 2.4);
  card(s, "The takeaway", "A safety regression that is easy to miss in review is caught automatically, with a precise reason and a build-blocking exit code. In CI, this red gate is a red PR check.", 9.3, 3.4, 3.35, 2.4, C.red);
  s.addText("Runbook: workshop-assets/demo-eval-runbook.md. Other faults: -Break phi, -Break prohibited_claim.", { x: 0.7, y: 6.35, w: 12, h: 0.4, fontFace: "Aptos", fontSize: 10, italic: true, color: C.muted, margin: 0 });
  notes(s, "The money moment. Run demo-eval.ps1. Beat 1 green. Beat 2 flip the flag, gate goes red and returns exit 1 - in CI this blocks the merge. Beat 3 revert, green again. Nobody had to catch it by eye.");
}

// ---------- WI-01/02/03: Quality & guardrail gates ----------
{
  const s = slide("Quality & guardrail gates", "WI-01 / 02 / 03 - Build discipline");
  card(s, "Endpoint tests (WI-01)", "Node built-in test runner, no deps. Health, cases (200/404), invoke (200/400/404), P0310 escalate, x-correlation-id. The app only binds a port when run directly, so tests mount it on an ephemeral port.", 0.7, 1.6, 3.85, 2.05, C.blue);
  card(s, "MCP contract validation (WI-02)", "Dependency-free JSON Schema validator checks each tool invocation against mcp-server/tool-contracts/. A drift self-test proves it fails loudly: a broken call for every tool MUST be rejected.", 4.75, 1.6, 3.85, 2.05, C.teal);
  card(s, "Policy module (WI-03)", "The guardrail matrix in one reusable place: screenText() refuses prohibited claims, order/med changes, HITL bypass, and prompt injection; decide() returns a structured run decision.", 8.8, 1.6, 3.85, 2.05, C.violet);
  bullets(s, [
    "Every guardrail-matrix row has a check and a test; the orchestrator now calls policy.decide(...).",
    "All gates run offline with no heavy dependencies and are wired into scripts/validate.ps1.",
  ], 0.7, 3.85, 12.0, 1.2, { fontSize: 11.5 });
  mono(s, [
    "npm test                          25 backend tests   PASS",
    "node mcp-server/validate-contracts.js   7 contracts  PASS (drift rejected)",
    ".\\scripts\\validate.ps1            Repository scaffold validation passed",
  ], 0.7, 5.15, 12.0, 1.25);
  notes(s, "This is the build discipline behind the demos: automated tests, machine-checked tool contracts, and one policy module encoding the guardrail matrix. The point for a DevOps audience: safety and correctness are enforced by gates in the pipeline, not by hope or code review alone.");
}

pptx.writeFile({ fileName: OUT }).then(() => console.log("wrote", OUT));