"""Agent manifest loader + runtime conformance (WI-08).

The declarative agent manifests live in `agents/*/agent.yaml`. This module reads them (with a small
dependency-free YAML reader — the manifests are flat key/scalar and key/list only) and checks them
against the running code, so the hosted-agent scaffold and the local orchestrator cannot silently
drift from the declared design:

  * every specialist the orchestrator runs has a manifest, and vice versa;
  * the orchestrator manifest's `specialists` list matches the runtime specialist set.

The hosted Foundry agent and the local orchestrator fulfill the SAME invoke contract, so this
conformance check is the single source of truth for "which agents exist" across both.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .specialists import ORCHESTRATOR_NAME, SPECIALIST_NAMES, manifest_id

AGENTS_DIR = Path(__file__).resolve().parents[3] / "agents"
ORCHESTRATOR_MANIFEST_DIR = "readmissions-orchestrator"


def _parse_manifest(text: str) -> dict[str, Any]:
    """Minimal reader for the flat agent.yaml manifests (scalars + single-level lists)."""
    data: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and current_list_key is not None:
            data[current_list_key].append(stripped[2:].strip())
            continue
        if not line.startswith(" ") and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                data[key] = value
                current_list_key = None
            else:
                data[key] = []
                current_list_key = key
    return data


def load_manifest(dir_name: str) -> dict[str, Any]:
    path = AGENTS_DIR / dir_name / "agent.yaml"
    return _parse_manifest(path.read_text(encoding="utf-8"))


def list_manifest_dirs() -> list[str]:
    return sorted(
        p.name for p in AGENTS_DIR.iterdir() if p.is_dir() and (p / "agent.yaml").exists()
    )


def check_conformance() -> list[str]:
    """Return a list of human-readable conformance issues (empty == conformant)."""
    issues: list[str] = []

    manifests = {d: load_manifest(d) for d in list_manifest_dirs()}
    manifest_names = {m.get("name") for m in manifests.values()}

    # 1. Every runtime specialist has a manifest.
    runtime_ids = [manifest_id(n) for n in SPECIALIST_NAMES]
    for name, mid in zip(SPECIALIST_NAMES, runtime_ids):
        if mid not in manifest_names:
            issues.append(f"runtime specialist '{name}' has no manifest ('{mid}.agent.yaml')")

    # 2. Every specialist manifest maps to a runtime agent (ignore the orchestrator and the
    #    user-facing care-manager agent, which are not orchestrator specialists).
    non_specialist = {"discharge-transition-orchestrator", "readmissions-care-manager-agent"}
    for d, m in manifests.items():
        mname = m.get("name")
        if mname in non_specialist or d in (ORCHESTRATOR_MANIFEST_DIR, "readmissions-care-manager-agent"):
            continue
        if mname not in set(runtime_ids):
            issues.append(f"manifest '{d}' (name '{mname}') has no matching runtime specialist")

    # 3. The orchestrator manifest's specialists list matches the runtime specialist set.
    orch = manifests.get(ORCHESTRATOR_MANIFEST_DIR)
    if orch is None:
        issues.append(f"orchestrator manifest '{ORCHESTRATOR_MANIFEST_DIR}/agent.yaml' is missing")
    else:
        declared = set(orch.get("specialists", []))
        expected = set(runtime_ids)
        missing = expected - declared
        extra = declared - expected
        if missing:
            issues.append(f"orchestrator manifest is missing specialists: {sorted(missing)}")
        if extra:
            issues.append(f"orchestrator manifest lists unknown specialists: {sorted(extra)}")

    return issues


def summary() -> dict[str, Any]:
    return {
        "orchestrator": ORCHESTRATOR_NAME,
        "runtimeSpecialists": SPECIALIST_NAMES,
        "manifestDirs": list_manifest_dirs(),
        "issues": check_conformance(),
    }
