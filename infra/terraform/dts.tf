# ------------------------------------------------------------------
# Durable Task Scheduler (DTS): durable HITL approval gate
# ------------------------------------------------------------------
# The graduation target for the in-process hitl.TaskStore. A care-manager review can
# now safely take hours or days: the orchestration pauses on a durable external event
# raced against a durable SLA timer, consuming no compute/tokens while it waits.
#
# Everything here is gated behind var.enable_dts (default false) so the standard gated
# apply is unchanged until DTS is deliberately activated. Activation also requires the
# Microsoft.DurableTask resource provider to be registered on the subscription:
#   az provider register --namespace Microsoft.DurableTask
#
# API version 2026-05-01-preview; Sweden Central is a supported scheduler region, so DTS
# co-locates with the rest of the workload (var.location).

locals {
  dts_name    = "dts-${local.base}"
  dts_taskhub = var.dts_taskhub_name
  # Empty string when DTS is disabled so container env stays valid and inert.
  dts_endpoint = length(azapi_resource.dts_scheduler) > 0 ? azapi_resource.dts_scheduler[0].output.properties.endpoint : ""
}

# The scheduler (top-level tracked resource under the resource group).
resource "azapi_resource" "dts_scheduler" {
  count     = var.enable_dts ? 1 : 0
  type      = "Microsoft.DurableTask/schedulers@2026-05-01-preview"
  name      = local.dts_name
  parent_id = azurerm_resource_group.rg.id
  location  = var.location

  body = {
    properties = {
      # Workshop-open. Tighten to the Container Apps environment egress for production.
      ipAllowlist = ["0.0.0.0/0"]
      sku = {
        name     = var.dts_sku_name
        capacity = var.dts_sku_capacity
      }
    }
  }

  response_export_values = ["properties.endpoint"]
  tags                   = local.tags
}

# The task hub within the scheduler that the worker + client bind to.
resource "azapi_resource" "dts_taskhub" {
  count     = var.enable_dts ? 1 : 0
  type      = "Microsoft.DurableTask/schedulers/taskHubs@2026-05-01-preview"
  name      = local.dts_taskhub
  parent_id = azapi_resource.dts_scheduler[0].id

  body = {
    properties = {}
  }
}

# Data-plane access for the app identity. The SAME user-assigned identity backs both the
# DtsGate client (in the FastAPI sidecar) and the worker container app, so one grant covers
# scheduling runs, raising decisions, and processing work items.
resource "azurerm_role_assignment" "app_dts" {
  count                = var.enable_dts ? 1 : 0
  scope                = azapi_resource.dts_scheduler[0].id
  role_definition_name = "Durable Task Data Contributor"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}

# ------------------------------------------------------------------
# Worker Container App: hosts the DTS orchestration + activities
# ------------------------------------------------------------------
# A separate, always-warm background app (no ingress). Reuses the agent image but overrides
# the entrypoint to run_worker() via `python -m discharge_transition_agent.dts`.
resource "azurerm_container_app" "worker" {
  count                        = var.enable_dts ? 1 : 0
  name                         = "ca-worker-${local.base}"
  container_app_environment_id = azurerm_container_app_environment.cae.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app.id]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.app.id
  }

  template {
    # Keep exactly one warm replica: the worker must stay resident to stream durable work items.
    min_replicas = 1
    max_replicas = 1

    container {
      name    = "worker"
      image   = var.container_image_agent
      cpu     = 0.5
      memory  = "1Gi"
      command = ["python", "-m", "discharge_transition_agent.dts"]

      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.app.client_id
      }
      env {
        name  = "DTS_ENDPOINT"
        value = local.dts_endpoint
      }
      env {
        name  = "DTS_TASKHUB"
        value = local.dts_taskhub
      }
      env {
        name  = "HITL_SLA_SECONDS"
        value = tostring(var.hitl_sla_seconds)
      }
      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.appi.connection_string
      }
    }
  }

  depends_on = [
    azurerm_role_assignment.app_dts,
    azapi_resource.dts_taskhub,
  ]
}
