"""Work IQ client seam — the M365 work-context lane for the discharge-transition agent.

Work IQ is Microsoft's **governed** workplace-intelligence service over Microsoft 365 (mail, Teams,
files, people, calendar). We *consume* it — we do not host it. It is intentionally a **separate
lane** from our clinical MCP tools: clinical / PHI data flows through the governed clinical MCP
server; Work IQ supplies the surrounding, non-clinical collaboration context (a coordination Teams
thread, a discharge-planning meeting summary, a SharePoint SOP).

Identity is the whole point: Work IQ is **Microsoft Entra delegated / on-behalf-of ONLY** — every
call runs as the signed-in user, honoring permissions, sensitivity labels, and DLP. There is no
app-only credential. This seam therefore requires a user token supplied at request time and is
**off by default** (``ENABLE_WORKIQ`` unset); with it off, the agent behaves exactly as before.

This module deliberately does not embed tenant secrets and does not call the network unless enabled
and given a token. The live path lazy-imports ``httpx`` so nothing here is a hard dependency of the
default flow or the evaluation gate.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class WorkIQConfig:
    enabled: bool
    endpoint: str

    @classmethod
    def from_env(cls) -> "WorkIQConfig":
        return cls(
            enabled=os.environ.get("ENABLE_WORKIQ", "").strip() in ("1", "true", "True"),
            endpoint=os.environ.get("WORKIQ_ENDPOINT", "https://workiq.svc.cloud.microsoft/").strip(),
        )


def is_enabled() -> bool:
    """True only when Work IQ is explicitly turned on. Default is off (in-process/no M365 lane)."""
    return WorkIQConfig.from_env().enabled


def work_context_summary(
    query: str,
    user_access_token: Optional[str],
    *,
    source: str = "teams",
    config: Optional[WorkIQConfig] = None,
) -> dict[str, Any]:
    """Return a compact, permission-scoped M365 work-context summary for ``query``.

    Governed behavior:
    - Returns a disabled/no-op result unless ``ENABLE_WORKIQ`` is set (keeps the default flow and the
      eval gate hermetic).
    - Requires ``user_access_token`` (Entra delegated / OBO). Refuses to call with app-only / no
      token — Work IQ does not support application-only auth, and we never fabricate one.
    - Never merged into the clinical MCP lane; the caller keeps PHI tools and this lane separate.
    """
    cfg = config or WorkIQConfig.from_env()
    if not cfg.enabled:
        return {"enabled": False, "reason": "Work IQ disabled (ENABLE_WORKIQ unset)", "results": []}
    if not user_access_token:
        return {
            "enabled": True,
            "reason": "Work IQ requires an Entra delegated / on-behalf-of user token; app-only auth is not supported.",
            "results": [],
        }
    return _call_workiq(cfg.endpoint, query, user_access_token, source)


def _call_workiq(endpoint: str, query: str, token: str, source: str) -> dict[str, Any]:  # pragma: no cover - live path
    """Call Work IQ over REST on behalf of the signed-in user.

    Lazy-imports ``httpx`` so it is not a hard dependency of the default (disabled) path. The REST
    shape follows the Work IQ API (see docs/work-iq-overview.md); confirm the current path/scopes
    against Microsoft Learn for your tenant before production use.
    """
    import httpx

    url = endpoint.rstrip("/") + "/rest/query"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"query": query, "source": source, "outputFormat": "compact"}
    with httpx.Client(timeout=20.0) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    return {"enabled": True, "source": source, "results": data.get("results", []), "raw": data}
