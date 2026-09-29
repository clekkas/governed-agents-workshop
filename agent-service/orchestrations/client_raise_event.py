"""Raise the human decision as an external event to a waiting orchestration.

REFERENCE / TEACHING CODE — the client side of the Durable Task Scheduler approval gate. When the
care manager clicks Approve / Request changes / Reject in the UI, the backend raises a
``ReviewDecision`` event to the orchestration instance. The orchestration — which has been consuming
no compute while it waited — resumes with full state intact.

This is the exact analogue of ``POST /api/v1/tasks/{id}/action`` in the local store.

Usage (from an Azure Functions HTTP trigger or any Durable Task client host):
    await raise_review_decision(client, instance_id, action="approve", actor="care-manager")
"""

from __future__ import annotations

import azure.durable_functions as df


async def raise_review_decision(
    client: df.DurableOrchestrationClient,
    instance_id: str,
    action: str,
    actor: str,
    note: str = "",
) -> None:
    """Deliver a care-manager decision to a paused orchestration.

    action: one of "approve" | "request_changes" | "reject".
    actor:  the human reviewer's identity (required for approve/reject).
    """
    await client.raise_event(
        instance_id,
        "ReviewDecision",
        {"action": action, "actor": actor, "note": note},
    )


# Example Azure Functions HTTP trigger that fronts the above (sketch):
#
# @app.route(route="tasks/{instanceId}/action", methods=["POST"])
# @app.durable_client_input(client_name="client")
# async def task_action(req: func.HttpRequest, client) -> func.HttpResponse:
#     instance_id = req.route_params["instanceId"]
#     body = req.get_json()
#     await raise_review_decision(client, instance_id, body["action"], body["actor"], body.get("note", ""))
#     status = await client.get_status(instance_id)
#     return func.HttpResponse(status.to_json(), mimetype="application/json")
