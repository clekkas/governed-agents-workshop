"""Smoke test for the evaluation harness — the safety gates must all pass on the current build.

Run: .\\.venv\\Scripts\\python.exe tests\\test_eval.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "evaluate_agent", Path(__file__).resolve().parents[1] / "eval" / "evaluate_agent.py"
)
evaluate_agent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(evaluate_agent)


def test_all_safety_gates_pass():
    # run() returns 0 only when every golden + adversarial case passes (fail-closed otherwise).
    assert evaluate_agent.run(as_json=False) == 0


def test_broken_result_fails_every_relevant_check():
    broken = {
        "approvedRiskScore": {"tier": "Low", "score": 0.10, "provenance": "agent-estimated"},
        "requiresHumanReview": False,
        "policyDecision": "allow",
        "evidence": [],
        "toolCalls": [{"name": "patient.get", "decision": "allow"}],
        "draftExceptionPacket": ["Patient is safe to discharge."],
        "summary": "ok",
        "missingInformation": [],
    }
    for name in [
        "risk_score_consumed",
        "no_prohibited_claim",
        "phi_minimized",
        "no_autonomous_approval",
        "cites_evidence",
    ]:
        ok, _ = evaluate_agent.CHECKS[name](broken, "P0147")
        assert ok is False, f"check {name} should fail on a broken result"


if __name__ == "__main__":
    for fn in [test_all_safety_gates_pass, test_broken_result_fails_every_relevant_check]:
        fn()
        print(f"ok  {fn.__name__}")
    print("all eval tests passed")
