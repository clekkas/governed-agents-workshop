"""Dependency-free tests for the governed MCP tool logic (CI-safe).

Validates the *behavior* of the discharge-transition tools without needing the MCP SDK or a running
server: correct policy decisions, read-only risk score, draft-only task creation, escalation on
missing specialty protocol, and — critically — that argument contracts are enforced (drift is
rejected). Run:  python mcp-server/test_server.py
"""

from __future__ import annotations

import sys

import governed_tools as gt

CID = "trace-mcp-test"
_failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  PASS  {name}")
    else:
        _failures.append(f"{name}: {detail}")
        print(f"  FAIL  {name}  {detail}")


def main() -> int:
    print("Governed MCP tool tests\n")

    # 1. patient.get is always redacted (minimum necessary), never raw.
    r = gt.patient_get("P0147", CID)
    check("patient.get redacts", r.decision == "redact" and r.result.get("minimum_necessary") is True, str(r.to_dict()))

    # 2. risk_score.get is read-only and echoes an approved score; it is never recomputed.
    r = gt.risk_score_get("P0147", "E1", CID)
    check("risk_score.get read-only", r.decision == "allow" and r.result.get("read_only") is True, str(r.to_dict()))

    # 3. utilization.history is aggregate-only.
    r = gt.utilization_history("P0147", CID)
    check("utilization.history aggregate", r.result.get("aggregate") is True, str(r.to_dict()))

    # 4. protocol.search escalates when a required specialty protocol is missing.
    r = gt.protocol_search("CHF discharge", CID, specialtyRequired=True, specialtyFound=False)
    check("protocol.search escalates", r.decision == "review_required" and r.result.get("evidence") == [], str(r.to_dict()))
    r = gt.protocol_search("CHF discharge", CID)
    check("protocol.search cites when present", r.decision == "allow" and len(r.result.get("evidence", [])) == 1, str(r.to_dict()))

    # 5. task.create drafts a PendingReview task; it cannot approve.
    r = gt.task_create("P0147", CID, "Confirm follow-up in 48h.", [{"source": "CHF Protocol", "claim": "48-72h"}])
    check("task.create draft-only", r.decision == "review_required" and r.result.get("status") == "PendingReview", str(r.to_dict()))

    # 6. audit.write is always-on.
    r = gt.audit_write(CID, "task.created", "orchestrator", "2026-09-28T22:00:00Z")
    check("audit.write records", r.decision == "allow" and r.result.get("recorded") is True, str(r.to_dict()))

    # 7. Contract enforcement: an out-of-enum purpose must be rejected (drift caught).
    try:
        gt.patient_get("P0147", CID, purpose="unauthorized-bulk-export")
        check("patient.get rejects bad purpose", False, "no ContractError raised")
    except gt.ContractError:
        check("patient.get rejects bad purpose", True)

    # 8. Contract enforcement: task.create evidence item missing 'claim' must be rejected.
    try:
        gt.task_create("P0147", CID, "x", [{"source": "s"}])
        check("task.create rejects bad evidence", False, "no ContractError raised")
    except gt.ContractError:
        check("task.create rejects bad evidence", True)

    # 9. Every advertised tool is wired into the dispatch table.
    expected = {"patient.get", "utilization.history", "risk_score.get", "protocol.search", "task.create", "audit.write", "notes.get"}
    check("dispatch table complete", set(gt.TOOLS) == expected, str(set(gt.TOOLS)))

    print("")
    if _failures:
        print(f"MCP server tests FAILED ({len(_failures)} issue(s)):")
        for f in _failures:
            print(f" - {f}")
        return 1
    print("MCP server tests PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
