# ------------------------------------------------------------------
# Remote/hosted MCP server — the governed clinical tool boundary as an
# Azure Container App with INTERNAL ingress (Layer 1 of secure MCP:
# private network, not publicly reachable).
# ------------------------------------------------------------------
# Reachable only from inside the Container App Environment (and its VNet). The app/agent call it at
# its internal FQDN over the streamable-http MCP transport. Same governed tools, same JSON
# contracts, same decisions as the in-process/stdio server — now a deployed, private service.
#
# Toggle with var.enable_mcp_server (default false so the base deploy is unchanged). The deploy
# script builds mcp-server/Dockerfile and passes the image via var.container_image_mcp.

resource "azurerm_container_app" "mcp" {
  count                        = var.enable_mcp_server ? 1 : 0
  name                         = "ca-mcp-${local.base}"
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

  # Internal ingress: private to the Container App Environment / VNet. No public endpoint.
  ingress {
    external_enabled = false
    target_port      = 8080
    transport        = "auto"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 1
    max_replicas = var.app_max_replicas

    container {
      name   = "mcp"
      image  = var.container_image_mcp
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "MCP_TRANSPORT"
        value = "http"
      }
      env {
        name  = "HOST"
        value = "0.0.0.0"
      }
      env {
        name  = "PORT"
        value = "8080"
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.app.client_id
      }
      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.appi.connection_string
      }
    }
  }
}
