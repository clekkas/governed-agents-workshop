// Local multi-agent orchestrator stub.
//
// This simulates the Discharge Transition Orchestrator coordinating specialist
// agents through mock MCP tools, so the UI has a working end-to-end path before a
// real Microsoft Foundry hosted agent is deployed. The API contract this produces
// is the same one the hosted agent will fulfill later — only the internals change.
//
// Safety boundary enforced here (not just in prompts):
//   - risk score is consumed from a tool, never generated
//   - draft packets require human review
//   - missing/blocked evidence escalates instead of guessing

const tools = require("./mockTools");

function proposeOwners(reviewCase) {
  // Map each gap to a proposed owner + due time. Draft only; never executed.
  const owners = {
    "Metro General": [
      "Owner: pharmacist pool · due today 2:00 PM · verify medication reconciliation status.",
      "Owner: scheduling team · due today 3:00 PM · confirm follow-up appointment options.",
      "Owner: social work queue · due today 3:30 PM · review transportation support need.",
    ],
    "Riverside Health": [
      "Owner: scheduling team · due tomorrow 10:30 AM · confirm appointment options.",
      "Owner: care manager · due tomorrow noon · review and edit exception packet.",
    ],
    "Community Medical": [
      "Do not use exception packet operationally.",
      "Owner: ADT nurse · due now · assign pending-result owner before discharge workflow proceeds.",
      "Retrieve missing protocol or escalate to human reviewer.",
    ],
  };
  return owners[reviewCase.facility] || ["Owner: care manager · review transition gaps."];
}

function runOrchestrator(reviewCase, correlationId) {
  const toolCalls = [];
  const agentHandoffs = [];

  function record(agentName, role, status, summary, handoffTo) {
    agentHandoffs.push({ agentName, role, status, summary, handoffTo });
  }

  // 1. Orchestrator starts the correlated workflow.
  record(
    "Discharge Transition Orchestrator",
    "Coordinator",
    "completed",
    "Started discharge-transition exception workflow and assembled specialist outputs.",
    "Case Context Agent",
  );

  // 2. Case Context Agent — redacted minimum-necessary context.
  const ctx = tools.patientGet(reviewCase);
  toolCalls.push(ctx);
  const util = tools.utilizationHistory(reviewCase);
  toolCalls.push(util);
  record("Case Context Agent", "Context", "completed", "Returned redacted case summary and utilization signals.", "Risk Score Agent");

  // 3. Risk Score Agent — approved deterministic score, never generated.
  const risk = tools.riskScoreGet(reviewCase);
  toolCalls.push(risk);
  record("Risk Score Agent", "Approved score", "completed", "Returned approved score, provenance, timestamp, and driver codes.", "Evidence Retrieval Agent");

  // 4. Evidence Retrieval Agent — RAG evidence packet.
  const protocols = tools.protocolSearch(reviewCase);
  toolCalls.push(protocols);
  const evidenceBlocked = protocols.decision === "review_required";
  record(
    "Evidence Retrieval Agent",
    "RAG",
    evidenceBlocked ? "blocked" : "completed",
    evidenceBlocked
      ? "Could not find the requested approved transition protocol source."
      : `Built evidence packet with ${reviewCase.evidence.length} citation(s).`,
    "Transition Exception Agent",
  );

  // 5. Transition Exception Agent — identify gaps.
  record(
    "Transition Exception Agent",
    "Gap detection",
    reviewCase.transitionGaps.length ? "needs-review" : "completed",
    `Identified ${reviewCase.transitionGaps.length} transition gap(s).`,
    "Care Plan Drafting Agent",
  );

  // 6. Care Plan Drafting Agent — draft owner/due-time text.
  const draftExceptionPacket = proposeOwners(reviewCase);
  record("Care Plan Drafting Agent", "Drafting", "completed", "Prepared draft exception packet with proposed owners and due times.", "Policy Guardrail Agent");

  // 7. Policy Guardrail Agent — validate and decide.
  let policyDecision = "allow";
  if (evidenceBlocked || reviewCase.context.specialtyProtocol === "missing") {
    policyDecision = "escalate";
  } else if (reviewCase.transitionGaps.length > 0) {
    policyDecision = "review_required";
  }
  record(
    "Policy Guardrail Agent",
    "Safety",
    policyDecision === "escalate" ? "blocked" : "needs-review",
    policyDecision === "escalate"
      ? "Blocked operational draft until missing evidence is resolved."
      : "Allowed exception packet creation but required HITL before operational use.",
    "Human Review Agent",
  );

  // 8. Human Review Agent — create pending review task + audit.
  const task = tools.taskCreate(reviewCase);
  toolCalls.push(task);
  const audit = tools.auditWrite(reviewCase, "exception_packet_drafted");
  toolCalls.push(audit);
  record("Human Review Agent", "HITL", "needs-review", "Created pending human review task and wrote audit event.");

  return {
    correlationId,
    caseId: reviewCase.id,
    summary: reviewCase.summary,
    approvedRiskScore: {
      tier: risk.result.tier,
      score: risk.result.score,
      provenance: risk.result.provenance,
    },
    transitionGaps: reviewCase.transitionGaps,
    missingInformation: reviewCase.missingInformation,
    evidence: reviewCase.evidence.map((e) => ({ source: e.source, citation: e.citation, claim: e.claim, confidence: e.confidence })),
    draftExceptionPacket,
    toolCalls: toolCalls.map((t) => ({ name: t.name, decision: t.decision, latencyMs: t.latencyMs })),
    agentHandoffs,
    policyDecision,
    requiresHumanReview: true,
  };
}

module.exports = { runOrchestrator };
