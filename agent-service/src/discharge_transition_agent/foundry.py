"""Optional Microsoft Foundry model client.

Delegates natural-language phrasing (refining the draft exception packet) to a Foundry model.
Two paths, tried in order, so it works both in containers and on constrained dev machines:

  1. SDK path: azure-ai-projects + azure-identity (project endpoint).
  2. REST path: az CLI access token + stdlib HTTP (no cryptography build needed).

It NEVER changes the safety boundary: it does not generate risk scores, make clinical
determinations, or bypass human review. On any problem it degrades to a no-op so the service
still runs fully offline and deterministically.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
import urllib.request
from typing import Any, Optional

_API_VERSION = "2025-01-01-preview"
_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"


class FoundryClient:
    def __init__(self) -> None:
        self.endpoint = self._resolve_endpoint()
        self.account = self._resolve_account()
        self.deployment = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT", "").strip()
        self.mode = "disabled"
        self._sdk_client = None
        self.enabled = False

        if not self.deployment or not (self.endpoint or self.account):
            return
        # Try SDK first (best in containers), then REST via az token (best on dev boxes).
        if self.endpoint and self._try_sdk():
            self.mode = "sdk"
            self.enabled = True
        elif self._token() and (self.account or self.endpoint):
            self.mode = "rest"
            self.enabled = True

    # ---- endpoint / account resolution ----

    @staticmethod
    def _resolve_endpoint() -> str:
        explicit = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "").strip()
        if explicit:
            return explicit
        account = os.environ.get("AZURE_AI_FOUNDRY_ACCOUNT", "").strip()
        project = os.environ.get("AZURE_AI_FOUNDRY_PROJECT", "").strip()
        if account and project:
            return f"https://{account}.services.ai.azure.com/api/projects/{project}"
        return ""

    def _resolve_account(self) -> str:
        acct = os.environ.get("AZURE_AI_FOUNDRY_ACCOUNT", "").strip()
        if acct:
            return acct
        # Derive from the project endpoint host: {account}.services.ai.azure.com
        if self.endpoint:
            try:
                host = urllib.parse.urlparse(self.endpoint).hostname or ""
                if host.endswith(".services.ai.azure.com"):
                    return host.split(".")[0]
            except Exception:
                pass
        return ""

    # ---- SDK path ----

    def _try_sdk(self) -> bool:
        try:
            from azure.ai.projects import AIProjectClient
            from azure.identity import DefaultAzureCredential

            project = AIProjectClient(endpoint=self.endpoint, credential=DefaultAzureCredential())
            self._sdk_client = project.get_openai_client()
            return True
        except Exception:
            self._sdk_client = None
            return False

    # ---- REST path ----

    def _token(self) -> Optional[str]:
        # Prefer azure-identity if importable; otherwise use the az CLI.
        try:
            from azure.identity import DefaultAzureCredential

            return DefaultAzureCredential().get_token(_TOKEN_SCOPE).token
        except Exception:
            pass
        try:
            out = subprocess.run(
                ["az", "account", "get-access-token", "--scope", _TOKEN_SCOPE, "--query", "accessToken", "-o", "tsv"],
                capture_output=True,
                text=True,
                timeout=30,
                shell=True,
            )
            token = out.stdout.strip()
            return token or None
        except Exception:
            return None

    def _rest_url(self) -> str:
        return (
            f"https://{self.account}.openai.azure.com/openai/deployments/"
            f"{self.deployment}/chat/completions?api-version={_API_VERSION}"
        )

    def _rest_chat(self, system: str, user: str) -> str:
        token = self._token()
        if not token:
            return ""
        body = json.dumps(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_completion_tokens": 400,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            self._rest_url(),
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return payload.get("choices", [{}])[0].get("message", {}).get("content", "") or ""

    def _sdk_chat(self, system: str, user: str) -> str:
        # gpt-5 family needs max_completion_tokens; older models accept max_tokens.
        try:
            resp = self._sdk_client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                max_completion_tokens=400,
            )
        except Exception:
            resp = self._sdk_client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.2,
                max_tokens=400,
            )
        return resp.choices[0].message.content or ""

    # ---- public API ----

    def refine_draft(self, case: dict[str, Any], draft: list[str], evidence: list[dict[str, Any]]) -> list[str]:
        """Rephrase draft packet lines for clarity only. Returns the original on any issue.

        The model may only rephrase existing lines; it must not add clinical judgment, approve
        anything, or invent owners/due times. We only accept output that preserves the line count.
        """
        if not self.enabled:
            return draft
        system = (
            "You rephrase draft care-coordination task lines for clarity only. "
            "Do not add clinical judgment, do not approve anything, do not invent owners "
            "or due times, and keep every line as a draft for human review. Return exactly the "
            "same number of lines, one per line."
        )
        user = "Rephrase these draft lines, one per line, keeping meaning identical:\n" + "\n".join(draft)
        try:
            text = self._sdk_chat(system, user) if self.mode == "sdk" else self._rest_chat(system, user)
        except Exception:
            return draft
        lines = [ln.strip("- ").strip() for ln in text.splitlines() if ln.strip()]
        return lines if len(lines) == len(draft) else draft
