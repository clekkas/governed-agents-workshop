"""Emulator validation for the DTS approval gate (run inside a Linux container).

Starts the worker, then exercises the orchestration end to end against the DTS emulator:
  1. approve path      -> Approved (+ audit history, finalize)
  2. SLA timeout       -> Escalated (no decision)
  3. policy escalate   -> Escalated immediately
  4. human-only guard  -> agent approve ignored; real approve then wins

Exit code 0 on success, 1 on any assertion failure.
"""

from __future__ import annotations

import sys
import time

from durabletask.azuremanaged.client import DurableTaskSchedulerClient
from durabletask.azuremanaged.worker import DurableTaskSchedulerWorker

from discharge_transition_agent import dts

ENDPOINT = dts._endpoint()
TASKHUB = dts._taskhub()


def _result(cid: str, policy: str = "review_required", sla: int = 3600) -> dict:
    return {
        "correlationId": cid,
        "caseId": "P0147",
        "policyDecision": policy,
        "approvedRiskScore": {"tier": "High", "score": 0.82, "provenance": "TSL v5"},
        "draftExceptionPacket": ["Owner: pharmacist - verify med rec."],
        "transitionGaps": ["med reconciliation", "follow-up", "transport"],
        "slaSeconds": sla,
    }


def main() -> int:
    failures: list[str] = []

    worker = DurableTaskSchedulerWorker(
        host_address=ENDPOINT, secure_channel=False, taskhub=TASKHUB, token_credential=None
    )
    worker.add_orchestrator(dts.discharge_exception_approval)
    worker.add_activity(dts.notify_care_manager)
    worker.add_activity(dts.finalize_exception_packet)
    worker.start()
    time.sleep(2)

    client = DurableTaskSchedulerClient(
        host_address=ENDPOINT, secure_channel=False, taskhub=TASKHUB, token_credential=None
    )

    def check(name: str, cond: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}", flush=True)
        if not cond:
            failures.append(name)

    # --- 1. approve path ---
    cid = "trace-approve-1"
    client.schedule_new_orchestration(dts.ORCHESTRATION_NAME, input=_result(cid), instance_id=cid)
    time.sleep(2)
    client.raise_orchestration_event(cid, dts.REVIEW_EVENT, data={"action": "approve", "actor": "dr-smith", "note": "ok"})
    state = client.wait_for_orchestration_completion(cid, timeout=30)
    import json
    out = json.loads(state.serialized_output) if state and state.serialized_output else {}
    check("approve -> Approved", out.get("status") == "Approved", str(out.get("status")))
    check("approve audit has create+approve", len(out.get("history", [])) == 2)

    # --- 2. timeout -> escalate (short SLA) ---
    cid = "trace-timeout-1"
    client.schedule_new_orchestration(dts.ORCHESTRATION_NAME, input=_result(cid, sla=3), instance_id=cid)
    state = client.wait_for_orchestration_completion(cid, timeout=30)
    out = json.loads(state.serialized_output) if state and state.serialized_output else {}
    check("timeout -> Escalated", out.get("status") == "Escalated", str(out.get("status")))

    # --- 3. policy escalate -> immediate Escalated ---
    cid = "trace-escalate-1"
    client.schedule_new_orchestration(dts.ORCHESTRATION_NAME, input=_result(cid, policy="escalate"), instance_id=cid)
    state = client.wait_for_orchestration_completion(cid, timeout=30)
    out = json.loads(state.serialized_output) if state and state.serialized_output else {}
    check("policy escalate -> Escalated", out.get("status") == "Escalated", str(out.get("status")))

    # --- 4. human-only guard: agent approve ignored, then real approve ---
    cid = "trace-guard-1"
    client.schedule_new_orchestration(dts.ORCHESTRATION_NAME, input=_result(cid), instance_id=cid)
    time.sleep(2)
    client.raise_orchestration_event(cid, dts.REVIEW_EVENT, data={"action": "approve", "actor": "agent"})
    time.sleep(3)
    st = client.get_orchestration_state(cid)
    still_running = str(getattr(st, "runtime_status", "")).upper().endswith("RUNNING")
    check("agent approve did NOT complete run", still_running, str(getattr(st, "runtime_status", "")))
    client.raise_orchestration_event(cid, dts.REVIEW_EVENT, data={"action": "approve", "actor": "dr-jones"})
    state = client.wait_for_orchestration_completion(cid, timeout=30)
    out = json.loads(state.serialized_output) if state and state.serialized_output else {}
    check("real approve -> Approved", out.get("status") == "Approved", str(out.get("status")))

    print(f"\nRESULT: {'ALL PASS' if not failures else 'FAILURES: ' + ', '.join(failures)}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
