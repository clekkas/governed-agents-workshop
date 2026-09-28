// Mock MCP tools. These stand in for the governed MCP tool boundary that the
// specialist agents call. Each returns a { decision, latencyMs, result } shape so
// the orchestrator can record tool calls and policy decisions. In a later chapter
// these are replaced by a real MCP server; the agent-facing contract stays the same.

function withTiming(name, decision, result) {
  // Deterministic-ish latency so demos read naturally without being flaky.
  const base = { "patient.get": 118, "utilization.history": 164, "risk_score.get": 74, "protocol.search": 242, "task.create": 96, "audit.write": 55 };
  return { name, decision, latencyMs: base[name] || 120, result };
}

// patient.get — returns redacted minimum-necessary context only.
function patientGet(reviewCase) {
  return withTiming("patient.get", "redact", {
    patientLabel: reviewCase.patientLabel,
    facility: reviewCase.facility,
    diagnosis: reviewCase.diagnosis,
    encounters: reviewCase.context.encounters,
  });
}

// utilization.history — aggregate only, never event-level by default.
function utilizationHistory(reviewCase) {
  return withTiming("utilization.history", "allow", {
    aggregate: true,
    driverCodes: reviewCase.approvedRiskScore.driverCodes,
  });
}

// risk_score.get — deterministic approved score with provenance. Never generated.
function riskScoreGet(reviewCase) {
  return withTiming("risk_score.get", "allow", { ...reviewCase.approvedRiskScore });
}

// protocol.search — approved RAG sources with citations. Decision reflects whether
// approved evidence was found; a missing specialty protocol requires review.
function protocolSearch(reviewCase) {
  const decision = reviewCase.context.specialtyProtocol === "missing" ? "review_required" : "allow";
  return withTiming("protocol.search", decision, { evidence: reviewCase.evidence });
}

// task.create — creates a draft HITL review task only; cannot approve it.
function taskCreate(reviewCase) {
  return withTiming("task.create", "review_required", {
    taskId: `task-${reviewCase.id}`,
    status: "PendingReview",
    assignedRole: "Care Manager",
  });
}

// audit.write — always-on compliance record.
function auditWrite(reviewCase, eventType) {
  return withTiming("audit.write", "allow", { eventType, caseId: reviewCase.id });
}

module.exports = {
  patientGet,
  utilizationHistory,
  riskScoreGet,
  protocolSearch,
  taskCreate,
  auditWrite,
};
