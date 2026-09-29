"""Contract and safety tests for the agent service.

Run: python -m pytest  (from agent-service/), or python -m unittest.
No cloud dependency; the orchestrator runs deterministically offline.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discharge_transition_agent import cases  # noqa: E402
from discharge_transition_agent.orchestrator import DischargeTransitionOrchestrator  # noqa: E402

REQUIRED_KEYS = {
    "correlationId",
    "caseId",
    "summary",
    "approvedRiskScore",
    "transitionGaps",
    "missingInformation",
    "evidence",
    "draftExceptionPacket",
    "toolCalls",
    "agentHandoffs",
    "policyDecision",
    "requiresHumanReview",
}


def _run(case_id: str) -> dict:
    case = cases.get_case(case_id)
    assert case is not None
    result = DischargeTransitionOrchestrator().run(case, correlation_id="trace-test")
    return result.model_dump(by_alias=True)


def test_contract_shape():
    out = _run("P0147")
    assert REQUIRED_KEYS.issubset(out.keys())
    assert out["correlationId"] == "trace-test"
    assert out["requiresHumanReview"] is True


def test_risk_score_is_consumed_not_generated():
    out = _run("P0147")
    # Score must match the approved tool output exactly (never recalculated).
    assert out["approvedRiskScore"]["score"] == 0.82
    assert "risk_score.get" in out["approvedRiskScore"]["provenance"]
    tool_names = [t["name"] for t in out["toolCalls"]]
    assert "risk_score.get" in tool_names


def test_golden_path_cites_and_routes_to_review():
    out = _run("P0147")
    assert len(out["evidence"]) >= 1
    assert out["policyDecision"] in {"review_required", "allow"}
    assert out["requiresHumanReview"] is True


def test_missing_protocol_escalates():
    out = _run("P0310")
    assert out["policyDecision"] == "escalate"
    # Evidence retrieval should be blocked and surfaced as a handoff status.
    statuses = {h["agentName"]: h["status"] for h in out["agentHandoffs"]}
    assert statuses.get("Evidence Retrieval Agent") == "blocked"


def test_multi_agent_handoffs_present():
    out = _run("P0221")
    names = [h["agentName"] for h in out["agentHandoffs"]]
    for expected in [
        "Discharge Transition Orchestrator",
        "Case Context Agent",
        "Risk Score Agent",
        "Evidence Retrieval Agent",
        "Transition Exception Agent",
        "Care Plan Drafting Agent",
        "Policy Guardrail Agent",
        "Human Review Agent",
    ]:
        assert expected in names


def test_evidence_comes_from_real_docs():
    out = _run("P0147")
    assert len(out["evidence"]) >= 1
    # Citations must point at real rag-docs markdown files.
    for e in out["evidence"]:
        assert e["citation"].startswith("rag-docs/")
        assert e["citation"].endswith(".md")


def test_knowledge_base_loads_corpus():
    from discharge_transition_agent.knowledge import KnowledgeBase

    kb = KnowledgeBase()
    assert len(kb.docs) >= 4, f"expected protocol docs, loaded {len(kb.docs)} from {kb.docs_dir}"
    assert kb.has_protocol_for("CHF") is True
    assert kb.has_protocol_for("pneumonia") is False


def test_retrieval_ranks_specialty_first():
    from discharge_transition_agent.knowledge import KnowledgeBase

    kb = KnowledgeBase()
    results = kb.retrieve("CHF discharge follow-up medication cardiology", diagnosis="CHF", k=3)
    assert results, "expected CHF retrieval results"
    assert results[0]["citation"] == "rag-docs/chf_discharge_followup_protocol.md"
    # CHF-specific doc must not leak into a COPD query.
    copd = kb.retrieve("COPD discharge follow-up appointment", diagnosis="COPD", k=3)
    assert all(r["citation"] != "rag-docs/chf_discharge_followup_protocol.md" for r in copd)


if __name__ == "__main__":
    for fn in [
        test_contract_shape,
        test_risk_score_is_consumed_not_generated,
        test_golden_path_cites_and_routes_to_review,
        test_missing_protocol_escalates,
        test_multi_agent_handoffs_present,
        test_evidence_comes_from_real_docs,
        test_knowledge_base_loads_corpus,
        test_retrieval_ranks_specialty_first,
    ]:
        fn()
        print(f"ok  {fn.__name__}")
    print("all tests passed")
