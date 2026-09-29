"""Workshop demo-only fault injection — the safe break-switch for the evaluation harness.

Set the env var EVAL_DEMO_BREAK to make the agent produce a specific SAFETY REGRESSION, so the
evaluation harness (eval/evaluate_agent.py) can be shown catching it live — with no code editing on
stage. It is OFF by default and does nothing unless the env var is set. Never set it in production.

Supported values:
  risk_score        RiskScoreAgent overwrites/lowers the approved score (fails risk_score_consumed).
  prohibited_claim  CarePlanDraftingAgent adds a "safe to discharge" line (fails no_prohibited_claim).
  phi               patient.get returns 'allow' instead of 'redact' (fails phi_minimized).

Usage (PowerShell):
  $env:EVAL_DEMO_BREAK = 'risk_score'   # inject the fault
  python eval/evaluate_agent.py         # watch the gate block (exit 1)
  Remove-Item Env:EVAL_DEMO_BREAK        # restore
"""

from __future__ import annotations

import os

_ENV = "EVAL_DEMO_BREAK"


def active_break() -> str | None:
    """Return the requested demo break kind, or None when disabled (the default)."""
    value = os.getenv(_ENV, "").strip().lower()
    return value or None


def is_break(kind: str) -> bool:
    return active_break() == kind
