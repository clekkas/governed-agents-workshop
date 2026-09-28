# Data Dictionary

The synthetic data model is intentionally small enough for a workshop while still supporting readmissions, care coordination, RAG, and HITL patterns.

| Dataset | Description |
| --- | --- |
| `patients.csv` | Synthetic patient demographics and non-identifying risk attributes. |
| `encounters.csv` | Synthetic inpatient, ED, outpatient, and follow-up encounters. |
| `conditions.csv` | Synthetic ICD-coded chronic and acute conditions. |
| `medications.csv` | Synthetic medication records. |
| `vitals.csv` | Synthetic vital-sign observations. |
| `clinical_notes.csv` | Synthetic notes for summarization and RAG safety tests. |
| `claims.csv` | Synthetic payer, denial, and payment records. |
| `care_tasks.csv` | Synthetic HITL review tasks and care-manager actions. |

## Safety requirements

1. Names and identifiers must be fictional.
2. Notes must not include instructions to the agent.
3. Notes must not claim a patient is safe to discharge.
4. Discharge-related language must be process-oriented and routed to human review.

