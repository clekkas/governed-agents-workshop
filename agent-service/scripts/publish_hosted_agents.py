"""Publish the discharge-transition specialists as Foundry hosted (persistent) agents.

The workshop's multi-agent system runs as in-process Python specialists (see
discharge_transition_agent/specialists.py). Those never appear in the Foundry portal's
Agents blade because nothing registers them with the Foundry Agent Service.

This script closes that gap: it reads the declarative agent manifests in agents/*/agent.yaml
and creates one persistent Foundry agent per specialist (plus the orchestrator) on the
project, backed by the gpt-4o model deployment. Re-running is idempotent: an agent whose
name already exists is updated in place rather than duplicated.

Auth: uses DefaultAzureCredential (AzureCliCredential works — just `az login`). The signed-in
identity needs a data-plane role on the Foundry account, e.g. "Azure AI User" / "Azure AI
Developer" (or Cognitive Services User).

Usage:
    python publish_hosted_agents.py \
        --endpoint https://ais-dtec-hi61yc.services.ai.azure.com/api/projects/proj-dtec-hi61yc \
        --model gpt-4o
Environment fallbacks: AZURE_AI_PROJECT_ENDPOINT, FOUNDRY_MODEL_DEPLOYMENT.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential

# agents/ lives at repo root: this file is agent-service/scripts/publish_hosted_agents.py
AGENTS_DIR = Path(__file__).resolve().parents[2] / "agents"

# Register the orchestrator + its 7 specialists, in workflow order. The care-manager
# user-facing agent is intentionally excluded (it is not an orchestrator specialist).
AGENT_ORDER = [
    "readmissions-orchestrator",
    "case-context-agent",
    "risk-score-agent",
    "evidence-retrieval-agent",
    "transition-exception-agent",
    "care-plan-drafting-agent",
    "policy-guardrail-agent",
    "human-review-agent",
]


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
    return _parse_manifest((AGENTS_DIR / dir_name / "agent.yaml").read_text(encoding="utf-8"))


def build_instructions(m: dict[str, Any]) -> str:
    """Compose portal-visible agent instructions from the manifest fields."""
    parts: list[str] = []
    desc = m.get("description")
    if desc:
        parts.append(str(desc))

    responsibilities = m.get("responsibilities")
    if responsibilities:
        parts.append("Responsibilities:\n" + "\n".join(f"- {r}" for r in responsibilities))

    specialists = m.get("specialists")
    if specialists:
        parts.append("Coordinates these specialists in order:\n" + "\n".join(f"- {s}" for s in specialists))

    inputs = m.get("inputs")
    if inputs:
        parts.append("Inputs: " + ", ".join(inputs))

    outputs = m.get("outputs")
    if outputs:
        parts.append("Outputs: " + ", ".join(outputs))

    tools = m.get("tools")
    if tools:
        parts.append("Governed tools: " + ", ".join(tools))

    guardrails = m.get("guardrails")
    if guardrails:
        parts.append("Guardrails (must always hold):\n" + "\n".join(f"- {g}" for g in guardrails))

    parts.append(
        "This agent operates on SYNTHETIC data only. It never generates or overrides an "
        "approved risk score, never declares a patient safe to discharge, and routes all "
        "consequential actions to human review."
    )
    return "\n\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--endpoint", default=os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "").strip())
    ap.add_argument("--model", default=os.environ.get("FOUNDRY_MODEL_DEPLOYMENT", "gpt-4o").strip())
    ap.add_argument("--dry-run", action="store_true", help="Print what would be created without calling Foundry.")
    args = ap.parse_args()

    if not args.endpoint:
        print("ERROR: no project endpoint. Pass --endpoint or set AZURE_AI_PROJECT_ENDPOINT.", file=sys.stderr)
        return 2

    manifests = {name: load_manifest(name) for name in AGENT_ORDER}

    if args.dry_run:
        for name in AGENT_ORDER:
            m = manifests[name]
            print(f"\n=== {m.get('name', name)} (model={args.model}) ===")
            print(build_instructions(m))
        return 0

    client = AgentsClient(endpoint=args.endpoint, credential=DefaultAzureCredential())

    # Map existing agents by display name so re-runs update instead of duplicate.
    existing: dict[str, str] = {}
    try:
        for a in client.list_agents():
            if a.name:
                existing[a.name] = a.id
    except Exception as exc:  # listing failure shouldn't block creation
        print(f"WARN: could not list existing agents ({exc}); will create fresh.", file=sys.stderr)

    created, updated = [], []
    with client:
        for key in AGENT_ORDER:
            m = manifests[key]
            display_name = str(m.get("name", key))
            instructions = build_instructions(m)
            if display_name in existing:
                agent = client.update_agent(
                    agent_id=existing[display_name],
                    model=args.model,
                    name=display_name,
                    instructions=instructions,
                )
                updated.append((display_name, agent.id))
                print(f"UPDATED  {display_name:38s} {agent.id}")
            else:
                agent = client.create_agent(
                    model=args.model,
                    name=display_name,
                    instructions=instructions,
                )
                created.append((display_name, agent.id))
                print(f"CREATED  {display_name:38s} {agent.id}")

    print(f"\nDone. {len(created)} created, {len(updated)} updated, {len(AGENT_ORDER)} total.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
