"""Agent manifest conformance tests (WI-08).

The declarative manifests in agents/ must stay in sync with the running orchestrator, so the hosted
Foundry agent and the local orchestrator describe the same agent set.

Run: .\\.venv\\Scripts\\python.exe tests\\test_manifests.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discharge_transition_agent import agent_manifests as m  # noqa: E402
from discharge_transition_agent.specialists import SPECIALIST_NAMES, manifest_id  # noqa: E402


def test_manifests_conform_to_runtime():
    issues = m.check_conformance()
    assert issues == [], "manifest/runtime drift:\n  - " + "\n  - ".join(issues)


def test_every_specialist_has_a_manifest():
    dirs = set(m.list_manifest_dirs())
    for name in SPECIALIST_NAMES:
        assert manifest_id(name) in dirs, f"missing manifest dir for '{name}'"


def test_orchestrator_manifest_lists_all_specialists():
    orch = m.load_manifest(m.ORCHESTRATOR_MANIFEST_DIR)
    declared = set(orch.get("specialists", []))
    expected = {manifest_id(n) for n in SPECIALIST_NAMES}
    assert declared == expected, f"declared {sorted(declared)} != runtime {sorted(expected)}"


if __name__ == "__main__":
    for fn in [
        test_manifests_conform_to_runtime,
        test_every_specialist_has_a_manifest,
        test_orchestrator_manifest_lists_all_specialists,
    ]:
        fn()
        print(f"ok  {fn.__name__}")
    print("all manifest tests passed")
