import type { ReviewCase } from "./types";

export const reviewCases: ReviewCase[] = [
  {
    id: "P0147",
    patientLabel: "Synthetic Case P0147",
    facility: "Metro General",
    diagnosis: "CHF",
    riskTier: "High",
    riskScore: 0.82,
    riskScoreProvenance: "risk_score.get · TSL v5 · 06:00 batch",
    status: "PendingReview",
    due: "Today, 4:00 PM",
    summary:
      "Synthetic tomorrow-discharge candidate with approved high transition-support score, CHF context, and open transition gaps requiring care-manager review.",
    riskDrivers: [
      "Recent inpatient encounter with CHF as primary diagnosis.",
      "Approved risk score indicates higher transition-support need.",
      "Driver codes returned by risk_score.get include prior utilization and medication complexity.",
    ],
    transitionGaps: [
      "Medication reconciliation is incomplete.",
      "Follow-up appointment is not confirmed within the protocol window.",
      "Transportation support status is unresolved.",
    ],
    missingInformation: [
      "Confirmed follow-up appointment availability.",
      "Transportation support status.",
    ],
    draftPlan: [
      "Owner: pharmacist pool · due today 2:00 PM · verify medication reconciliation status.",
      "Owner: scheduling team · due today 3:00 PM · confirm follow-up appointment options.",
      "Owner: social work queue · due today 3:30 PM · review transportation support need.",
    ],
    evidence: [
      {
        id: "E1",
        source: "CHF Follow-Up Protocol",
        citation: "rag-docs/chf_discharge_followup_protocol.md",
        claim:
          "CHF transition planning may include weight monitoring, medication reconciliation, and cardiology or primary care follow-up.",
        confidence: "High",
      },
      {
        id: "E2",
        source: "Medication Reconciliation Policy",
        citation: "rag-docs/medication_reconciliation_policy.md",
        claim:
          "Medication discrepancies should be surfaced to a reviewer before operational use.",
        confidence: "High",
      },
    ],
    toolCalls: [
      { id: "T1", name: "patient.get", decision: "redact", latencyMs: 118 },
      { id: "T2", name: "utilization.history", decision: "allow", latencyMs: 164 },
      { id: "T3", name: "risk_score.get", decision: "allow", latencyMs: 74 },
      { id: "T4", name: "protocol.search", decision: "allow", latencyMs: 242 },
      { id: "T5", name: "task.create", decision: "review_required", latencyMs: 96 },
    ],
    agentContributions: [
      {
        id: "A1",
        agentName: "Discharge Transition Orchestrator",
        role: "Coordinator",
        status: "completed",
        summary: "Started discharge-transition exception workflow and assembled specialist outputs.",
        handoffTo: "Case Context Agent",
      },
      {
        id: "A2",
        agentName: "Case Context Agent",
        role: "Context",
        status: "completed",
        summary: "Returned redacted case summary and utilization signals.",
        handoffTo: "Evidence Retrieval Agent",
      },
      {
        id: "A3",
        agentName: "Risk Score Agent",
        role: "Approved score",
        status: "completed",
        summary: "Returned approved TSL score, provenance, timestamp, and driver codes.",
        handoffTo: "Evidence Retrieval Agent",
      },
      {
        id: "A4",
        agentName: "Evidence Retrieval Agent",
        role: "RAG",
        status: "completed",
        summary: "Built evidence packet with two high-confidence citations.",
        handoffTo: "Transition Exception Agent",
      },
      {
        id: "A5",
        agentName: "Transition Exception Agent",
        role: "Gap detection",
        status: "needs-review",
        summary: "Identified medication, appointment, and transportation transition gaps.",
        handoffTo: "Policy Guardrail Agent",
      },
      {
        id: "A6",
        agentName: "Policy Guardrail Agent",
        role: "Safety",
        status: "needs-review",
        summary: "Allowed exception packet creation but required HITL before operational use.",
        handoffTo: "Human Review Agent",
      },
    ],
    timeline: [
      {
        id: "L1",
        label: "Agent invocation started",
        actor: "Hosted agent",
        timestamp: "09:18",
      },
      {
        id: "L2",
        label: "Evidence packet assembled",
        actor: "Foundry IQ / RAG",
        timestamp: "09:19",
      },
      {
        id: "L3",
        label: "Exception packet routed for review",
        actor: "HITL scheduler",
        timestamp: "09:20",
      },
    ],
    correlationId: "trace-kp-0147-a92f",
  },
  {
    id: "P0221",
    patientLabel: "Synthetic Case P0221",
    facility: "Riverside Health",
    diagnosis: "COPD",
    riskTier: "Medium",
    riskScore: 0.58,
    riskScoreProvenance: "risk_score.get · TSL v5 · 06:00 batch",
    status: "InReview",
    due: "Tomorrow, 10:30 AM",
    summary:
      "Synthetic COPD tomorrow-discharge candidate with approved medium transition-support score and incomplete appointment context.",
    riskDrivers: [
      "COPD diagnosis with prior ED visit in synthetic history.",
      "Approved score returned with utilization and diagnosis driver codes.",
    ],
    transitionGaps: [
      "Appointment availability has not been retrieved.",
      "Owner for follow-up confirmation is not assigned.",
    ],
    missingInformation: ["Current appointment availability."],
    draftPlan: [
      "Owner: scheduling team · due tomorrow 10:30 AM · confirm appointment options.",
      "Owner: care manager · due tomorrow noon · review and edit exception packet.",
    ],
    evidence: [
      {
        id: "E3",
        source: "Readmission Follow-Up Protocol",
        citation: "rag-docs/readmission_followup_protocol.md",
        claim:
          "Elevated transition support need should route to care-manager review with transition planning elements.",
        confidence: "Medium",
      },
    ],
    toolCalls: [
      { id: "T5", name: "patient.get", decision: "redact", latencyMs: 103 },
      { id: "T6", name: "protocol.search", decision: "allow", latencyMs: 219 },
    ],
    agentContributions: [
      {
        id: "A5",
        agentName: "Discharge Transition Orchestrator",
        role: "Coordinator",
        status: "completed",
        summary: "Routed case through context, approved score, and evidence specialists.",
        handoffTo: "Risk Score Agent",
      },
      {
        id: "A6",
        agentName: "Evidence Retrieval Agent",
        role: "RAG",
        status: "needs-review",
        summary: "Found general transition guidance but appointment source is missing.",
        handoffTo: "Transition Exception Agent",
      },
      {
        id: "A7",
        agentName: "Transition Exception Agent",
        role: "Gap detection",
        status: "completed",
        summary: "Prepared a limited exception packet with missing appointment availability noted.",
        handoffTo: "Human Review Agent",
      },
    ],
    timeline: [
      {
        id: "L4",
        label: "Reviewer opened task",
        actor: "Care manager",
        timestamp: "11:42",
      },
    ],
    correlationId: "trace-kp-0221-b31c",
  },
  {
    id: "P0310",
    patientLabel: "Synthetic Case P0310",
    facility: "Community Medical",
    diagnosis: "Pneumonia",
    riskTier: "Critical",
    riskScore: 0.91,
    riskScoreProvenance: "risk_score.get · TSL v5 · 06:00 batch",
    status: "NeedsRework",
    due: "Overdue",
    summary:
      "Synthetic pneumonia tomorrow-discharge candidate where the agent identified missing protocol evidence and the reviewer requested rework.",
    riskDrivers: [
      "Recent inpatient stay in synthetic record.",
      "Approved risk score returned critical transition-support tier.",
      "Requested specialty workflow lacks approved protocol evidence.",
    ],
    transitionGaps: [
      "Pending result owner is not assigned.",
      "Specialty protocol source is missing from approved RAG content.",
      "Reviewer requested claim-level citation mapping before action.",
    ],
    missingInformation: [
      "Applicable specialty protocol not found in approved RAG sources.",
      "Reviewer requested source-specific plan mapping.",
    ],
    draftPlan: [
      "Do not use exception packet operationally.",
      "Owner: ADT nurse · due now · assign pending-result owner before discharge workflow proceeds.",
      "Retrieve missing protocol or escalate to human reviewer.",
    ],
    evidence: [
      {
        id: "E4",
        source: "Escalation and Handoff Policy",
        citation: "rag-docs/escalation_and_handoff_policy.md",
        claim:
          "Missing or conflicting evidence should be escalated to human review.",
        confidence: "High",
      },
    ],
    toolCalls: [
      { id: "T7", name: "protocol.search", decision: "review_required", latencyMs: 311 },
      { id: "T8", name: "audit.write", decision: "allow", latencyMs: 55 },
    ],
    agentContributions: [
      {
        id: "A8",
        agentName: "Discharge Transition Orchestrator",
        role: "Coordinator",
        status: "completed",
        summary: "Stopped transition workflow after specialist escalation signal.",
        handoffTo: "Policy Guardrail Agent",
      },
      {
        id: "A9",
        agentName: "Evidence Retrieval Agent",
        role: "RAG",
        status: "blocked",
        summary: "Could not find the requested approved transition protocol source.",
        handoffTo: "Policy Guardrail Agent",
      },
      {
        id: "A10",
        agentName: "Policy Guardrail Agent",
        role: "Safety",
        status: "blocked",
        summary: "Blocked operational draft until missing evidence is resolved.",
        handoffTo: "Human Review Agent",
      },
    ],
    timeline: [
      {
        id: "L5",
        label: "Missing evidence detected",
        actor: "Policy validator",
        timestamp: "14:06",
      },
      {
        id: "L6",
        label: "Reviewer requested rework",
        actor: "Care manager",
        timestamp: "14:18",
      },
    ],
    correlationId: "trace-kp-0310-c77e",
  },
];
