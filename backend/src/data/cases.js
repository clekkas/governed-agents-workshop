// Synthetic discharge-transition cases. No real PHI. These mirror the shapes used
// by the UI so the backend can serve the same use case end to end. In a later
// chapter these are replaced by a mock EHR + risk-score service behind MCP tools.

const cases = [
  {
    id: "P0147",
    patientLabel: "Synthetic Case P0147",
    facility: "Metro General",
    diagnosis: "CHF",
    approvedRiskScore: {
      tier: "High",
      score: 0.82,
      provenance: "risk_score.get · TSL v5 · 06:00 batch",
      driverCodes: ["prior_utilization", "medication_complexity"],
    },
    summary:
      "Synthetic tomorrow-discharge candidate with approved high transition-support score, CHF context, and open transition gaps requiring care-manager review.",
    context: {
      encounters: 2,
      medicationReconciliation: "incomplete",
      followUpAppointment: "not_confirmed",
      transportation: "unresolved",
    },
    transitionGaps: [
      "Medication reconciliation is incomplete.",
      "Follow-up appointment is not confirmed within the protocol window.",
      "Transportation support status is unresolved.",
    ],
    missingInformation: [
      "Confirmed follow-up appointment availability.",
      "Transportation support status.",
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
  },
  {
    id: "P0221",
    patientLabel: "Synthetic Case P0221",
    facility: "Riverside Health",
    diagnosis: "COPD",
    approvedRiskScore: {
      tier: "Medium",
      score: 0.58,
      provenance: "risk_score.get · TSL v5 · 06:00 batch",
      driverCodes: ["utilization", "diagnosis"],
    },
    summary:
      "Synthetic COPD tomorrow-discharge candidate with approved medium transition-support score and incomplete appointment context.",
    context: {
      encounters: 1,
      followUpAppointment: "not_retrieved",
    },
    transitionGaps: [
      "Appointment availability has not been retrieved.",
      "Owner for follow-up confirmation is not assigned.",
    ],
    missingInformation: ["Current appointment availability."],
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
  },
  {
    id: "P0310",
    patientLabel: "Synthetic Case P0310",
    facility: "Community Medical",
    diagnosis: "Pneumonia",
    approvedRiskScore: {
      tier: "Critical",
      score: 0.91,
      provenance: "risk_score.get · TSL v5 · 06:00 batch",
      driverCodes: ["recent_inpatient", "specialty_workflow"],
    },
    summary:
      "Synthetic pneumonia tomorrow-discharge candidate where the agent identified missing protocol evidence and the reviewer requested rework.",
    context: {
      encounters: 3,
      specialtyProtocol: "missing",
    },
    transitionGaps: [
      "Pending result owner is not assigned.",
      "Specialty protocol source is missing from approved RAG content.",
      "Reviewer requested claim-level citation mapping before action.",
    ],
    missingInformation: [
      "Applicable specialty protocol not found in approved RAG sources.",
      "Reviewer requested source-specific plan mapping.",
    ],
    evidence: [
      {
        id: "E4",
        source: "Escalation and Handoff Policy",
        citation: "rag-docs/escalation_and_handoff_policy.md",
        claim: "Missing or conflicting evidence should be escalated to human review.",
        confidence: "High",
      },
    ],
  },
];

function listCases() {
  return cases.map((c) => ({
    id: c.id,
    patientLabel: c.patientLabel,
    facility: c.facility,
    diagnosis: c.diagnosis,
    riskTier: c.approvedRiskScore.tier,
    summary: c.summary,
  }));
}

function getCase(id) {
  return cases.find((c) => c.id === id) || null;
}

module.exports = { listCases, getCase };
