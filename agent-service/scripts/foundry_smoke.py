"""Live Foundry connectivity smoke test.

Verifies the FoundryClient can reach the configured Foundry project + model and that the
Care Plan Drafting refinement works end to end. Requires:
  - pip install -r requirements-foundry.txt
  - az login (DefaultAzureCredential)
  - env: AZURE_AI_PROJECT_ENDPOINT (or ACCOUNT+PROJECT) and FOUNDRY_MODEL_DEPLOYMENT

Run: python scripts/foundry_smoke.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discharge_transition_agent import cases  # noqa: E402
from discharge_transition_agent.foundry import FoundryClient  # noqa: E402
from discharge_transition_agent.orchestrator import DischargeTransitionOrchestrator  # noqa: E402


def main() -> int:
    fc = FoundryClient()
    print(f"endpoint   : {fc.endpoint or '(none)'}")
    print(f"deployment : {fc.deployment or '(none)'}")
    print(f"enabled    : {fc.enabled}")
    if not fc.enabled:
        print("\nFoundry client not enabled. Set env vars and install requirements-foundry.txt,")
        print("then run 'az login'. Falling back to deterministic drafting.")
        return 1

    sample = ["Owner: pharmacist pool - due today 2:00 PM - verify medication reconciliation status."]
    refined = fc.refine_draft(cases.get_case("P0147"), sample, [])
    print("\nrefine_draft input :", sample[0])
    print("refine_draft output:", refined[0])

    # Full workflow with the live model wired into the drafting step.
    result = DischargeTransitionOrchestrator(foundry=fc).run(cases.get_case("P0147"), correlation_id="trace-smoke")
    print("\nWorkflow OK. policyDecision =", result.policy_decision)
    print("Draft packet lines:")
    for line in result.draft_exception_packet:
        print("  -", line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
