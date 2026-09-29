import os, sys, time, json
print("start", flush=True)
from durabletask.azuremanaged.client import DurableTaskSchedulerClient
from durabletask.azuremanaged.worker import DurableTaskSchedulerWorker
from discharge_transition_agent import dts
ep, th = dts._endpoint(), dts._taskhub()
print("connecting", ep, th, flush=True)
w = DurableTaskSchedulerWorker(host_address=ep, secure_channel=False, taskhub=th, token_credential=None)
w.add_orchestrator(dts.discharge_exception_approval)
w.add_activity(dts.notify_care_manager)
w.add_activity(dts.finalize_exception_packet)
w.start()
print("worker started", flush=True)
time.sleep(3)
c = DurableTaskSchedulerClient(host_address=ep, secure_channel=False, taskhub=th, token_credential=None)
cid = "smoke-escalate-1"
print("scheduling", flush=True)
c.schedule_new_orchestration(dts.ORCHESTRATION_NAME, input={"correlationId": cid, "caseId":"P0147", "policyDecision":"escalate"}, instance_id=cid)
print("scheduled; waiting", flush=True)
state = c.wait_for_orchestration_completion(cid, timeout=20)
out = json.loads(state.serialized_output) if state and state.serialized_output else {}
print("RESULT status=", out.get("status"), "runtime=", getattr(state,"runtime_status",None), flush=True)
sys.exit(0 if out.get("status")=="Escalated" else 1)
