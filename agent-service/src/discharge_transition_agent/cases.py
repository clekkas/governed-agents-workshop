"""Synthetic discharge-transition cases. No real PHI.

Mirrors the Node backend's case data so both services serve the same use case.
In a later step these are replaced by a mock EHR + risk-score service behind MCP.
"""

from __future__ import annotations

from typing import Any

CASES: list[dict[str, Any]] = [
    {
        "id": "P0147",
        "patient_label": "Synthetic Case P0147",
        "facility": "Metro General",
        "diagnosis": "CHF",
        "approved_risk_score": {
            "tier": "High",
            "score": 0.82,
            "provenance": "risk_score.get - TSL v5 - 06:00 batch",
            "driver_codes": ["prior_utilization", "medication_complexity"],
        },
        "summary": (
            "Synthetic tomorrow-discharge candidate with approved high transition-support "
            "score, CHF context, and open transition gaps requiring care-manager review."
        ),
        "context": {
            "encounters": 2,
            "medication_reconciliation": "incomplete",
            "follow_up_appointment": "not_confirmed",
            "transportation": "unresolved",
        },
        "transition_gaps": [
            "Medication reconciliation is incomplete.",
            "Follow-up appointment is not confirmed within the protocol window.",
            "Transportation support status is unresolved.",
        ],
        "missing_information": [
            "Confirmed follow-up appointment availability.",
            "Transportation support status.",
        ],
        "evidence": [
            {
                "source": "CHF Follow-Up Protocol",
                "citation": "rag-docs/chf_discharge_followup_protocol.md",
                "claim": (
                    "CHF transition planning may include weight monitoring, medication "
                    "reconciliation, and cardiology or primary care follow-up."
                ),
                "confidence": "High",
            },
            {
                "source": "Medication Reconciliation Policy",
                "citation": "rag-docs/medication_reconciliation_policy.md",
                "claim": "Medication discrepancies should be surfaced to a reviewer before operational use.",
                "confidence": "High",
            },
        ],
    },
    {
        "id": "P0221",
        "patient_label": "Synthetic Case P0221",
        "facility": "Riverside Health",
        "diagnosis": "COPD",
        "approved_risk_score": {
            "tier": "Medium",
            "score": 0.58,
            "provenance": "risk_score.get - TSL v5 - 06:00 batch",
            "driver_codes": ["utilization", "diagnosis"],
        },
        "summary": (
            "Synthetic COPD tomorrow-discharge candidate with approved medium transition-support "
            "score and incomplete appointment context."
        ),
        "context": {"encounters": 1, "follow_up_appointment": "not_retrieved"},
        "transition_gaps": [
            "Appointment availability has not been retrieved.",
            "Owner for follow-up confirmation is not assigned.",
        ],
        "missing_information": ["Current appointment availability."],
        "evidence": [
            {
                "source": "Readmission Follow-Up Protocol",
                "citation": "rag-docs/readmission_followup_protocol.md",
                "claim": (
                    "Elevated transition support need should route to care-manager review "
                    "with transition planning elements."
                ),
                "confidence": "Medium",
            }
        ],
    },
    {
        "id": "P0310",
        "patient_label": "Synthetic Case P0310",
        "facility": "Community Medical",
        "diagnosis": "Pneumonia",
        "approved_risk_score": {
            "tier": "Critical",
            "score": 0.91,
            "provenance": "risk_score.get - TSL v5 - 06:00 batch",
            "driver_codes": ["recent_inpatient", "specialty_workflow"],
        },
        "summary": (
            "Synthetic pneumonia tomorrow-discharge candidate where the agent identified missing "
            "protocol evidence and the reviewer requested rework."
        ),
        "context": {"encounters": 3, "specialty_protocol": "missing"},
        "transition_gaps": [
            "Pending result owner is not assigned.",
            "Specialty protocol source is missing from approved RAG content.",
            "Reviewer requested claim-level citation mapping before action.",
        ],
        "missing_information": [
            "Applicable specialty protocol not found in approved RAG sources.",
            "Reviewer requested source-specific plan mapping.",
        ],
        "evidence": [
            {
                "source": "Escalation and Handoff Policy",
                "citation": "rag-docs/escalation_and_handoff_policy.md",
                "claim": "Missing or conflicting evidence should be escalated to human review.",
                "confidence": "High",
            }
        ],
    },
]

_BY_ID = {c["id"]: c for c in CASES}


def list_cases() -> list[dict[str, Any]]:
    return [
        {
            "id": c["id"],
            "patient_label": c["patient_label"],
            "facility": c["facility"],
            "diagnosis": c["diagnosis"],
            "risk_tier": c["approved_risk_score"]["tier"],
            "summary": c["summary"],
        }
        for c in CASES
    ]


def get_case(case_id: str) -> dict[str, Any] | None:
    return _BY_ID.get(case_id)
