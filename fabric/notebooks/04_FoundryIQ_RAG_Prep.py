"""Starter Fabric notebook: prepare RAG document metadata.

Implementation will depend on the selected search/indexing service.
"""

rag_sources = [
    "readmission_followup_protocol.md",
    "chf_discharge_followup_protocol.md",
    "medication_reconciliation_policy.md",
    "care_coordination_sop.md",
    "escalation_and_handoff_policy.md",
]

for source in rag_sources:
    print(f"Register source metadata for {source}")

