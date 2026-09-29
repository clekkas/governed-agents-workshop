// Trace store tests (Node built-in test runner, no dependencies).
// Run: node --test  (from the backend/ folder)

const { test } = require("node:test");
const assert = require("node:assert");
const { TraceStore, EVENT } = require("../src/observability/traceStore");

function sampleResult(correlationId) {
  return {
    correlationId,
    caseId: "P0147",
    policyDecision: "review_required",
    requiresHumanReview: true,
    approvedRiskScore: { tier: "High", score: 0.82, provenance: "risk_score.get" },
    toolCalls: [
      { name: "risk_score.get", decision: "allow", latencyMs: 74 },
      { name: "protocol.search", decision: "allow", latencyMs: 242 },
    ],
    agentHandoffs: [
      { agentName: "Discharge Transition Orchestrator", role: "Coordinator", status: "completed", handoffTo: "Case Context Agent" },
      { agentName: "Human Review Agent", role: "HITL", status: "needs-review", handoffTo: null },
    ],
  };
}

test("recordInvoke builds a complete ordered event list", () => {
  const store = new TraceStore();
  store.recordInvoke(sampleResult("trace-a"), "local");
  const trace = store.get("trace-a");
  assert.ok(trace, "trace should exist");
  assert.equal(trace.caseId, "P0147");

  const types = trace.events.map((e) => e.type);
  // run.started, 2 tool.called, 2 agent.handoff, policy.decision, run.completed
  assert.equal(types[0], EVENT.RUN_STARTED);
  assert.equal(types.filter((t) => t === EVENT.TOOL_CALLED).length, 2);
  assert.equal(types.filter((t) => t === EVENT.AGENT_HANDOFF).length, 2);
  assert.equal(types[types.length - 2], EVENT.POLICY_DECISION);
  assert.equal(types[types.length - 1], EVENT.RUN_COMPLETED);

  // seq is monotonic starting at 1
  trace.events.forEach((e, i) => assert.equal(e.seq, i + 1));
});

test("review created and transition events append in order", () => {
  const store = new TraceStore();
  store.recordInvoke(sampleResult("trace-b"), "local");
  store.recordReviewCreated({ correlationId: "trace-b", caseId: "P0147", status: "PendingReview", dueAt: "2026-01-01T00:00:00Z" });
  store.recordTransition("trace-b", { caseId: "P0147", status: "Approved" }, "approve", "Nurse Alex");

  const events = store.get("trace-b").events;
  const created = events.find((e) => e.type === EVENT.REVIEW_CREATED);
  const transition = events.find((e) => e.type === EVENT.REVIEW_TRANSITION);
  assert.equal(created.status, "PendingReview");
  assert.equal(transition.action, "approve");
  assert.equal(transition.actor, "Nurse Alex");
  assert.equal(transition.to, "Approved");
  // transition comes after creation
  assert.ok(transition.seq > created.seq);
});

test("tool.called events preserve policy decision and latency", () => {
  const store = new TraceStore();
  store.recordInvoke(sampleResult("trace-c"), "agent-service");
  const tools = store.get("trace-c").events.filter((e) => e.type === EVENT.TOOL_CALLED);
  const risk = tools.find((t) => t.name === "risk_score.get");
  assert.equal(risk.decision, "allow");
  assert.equal(risk.latencyMs, 74);
});

test("unknown correlation id returns null", () => {
  const store = new TraceStore();
  assert.equal(store.get("nope"), null);
});

test("store caps the number of retained traces", () => {
  const store = new TraceStore(3);
  for (const id of ["t1", "t2", "t3", "t4"]) store.recordInvoke(sampleResult(id), "local");
  assert.equal(store.get("t1"), null, "oldest trace should be evicted");
  assert.ok(store.get("t4"), "newest trace should be retained");
  assert.equal(store.list().length, 3);
});
