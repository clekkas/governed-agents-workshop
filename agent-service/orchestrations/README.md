# Durable Task Scheduler reference (Data Task Scheduler)

Teaching-grade reference for the agenda item **HITL — Data Task Scheduler**. It shows how the
local durable HITL store graduates to the **Microsoft Agent Framework Durable Extension** running on
**Azure Functions** with the **Durable Task Scheduler** backend.

> These files are **not** wired into the laptop demo. They require the Azure Functions host, a
> Durable Task Scheduler backend (or emulator), and the pre-release `agent-framework-*` packages,
> which do not build on Windows ARM64 today. The runnable path is the local store — same state
> machine, same audit contract, same timeout→escalate branch.

## Files

| File | Role | Local analogue |
| --- | --- | --- |
| `function_app.py` | `discharge_exception_approval` durable orchestration + activities | `hitl.TaskStore` + `app.py` invoke |
| `client_raise_event.py` | Raises the `ReviewDecision` external event | `POST /api/v1/tasks/{id}/action` |

## The pattern

1. The orchestration drafts the exception packet (durably checkpointed), then **pauses on
   `wait_for_external_event("ReviewDecision")`** raced against a durable timer (`create_timer`).
2. While paused, the Durable Task Scheduler persists the state and **compute scales to zero** — no
   VM, no model tokens, for hours or days.
3. The care manager's decision arrives as an external event → the orchestration resumes with full
   state and routes to Approved / NeedsRework / Rejected.
4. If the SLA timer fires first, the run **escalates** — the unattended-review safety branch.
5. Every branch calls an audit activity with the same fields the local store records.

## Why this matters for KP

- **Governance:** the approval is a durable, replayable, audited event — not an in-memory flag.
- **Safety:** the human-only guard and escalate-on-timeout are enforced in the workflow, so a
  forgotten review never becomes a silent approval.
- **FinOps:** scale-to-zero-while-waiting means a week-long approval costs nothing to wait on —
  the observability/FinOps chapter measures exactly this.

## Deploy sketch (supported host)

```bash
pip install azure-identity agent-framework-azurefunctions --pre azure-functions-durable
# provision a Durable Task Scheduler + task hub, set AzureWebJobsStorage + DTS connection,
# then: func azure functionapp publish <app-name>
```

See Microsoft Learn — *Durable Extension* (Agent Framework hosting on Azure Functions),
Human-in-the-loop orchestrations.
