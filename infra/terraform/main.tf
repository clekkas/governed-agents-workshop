data "azurerm_client_config" "current" {}

resource "random_string" "suffix" {
  length  = 6
  upper   = false
  special = false
  numeric = true
}

locals {
  suffix = random_string.suffix.result
  base   = "${var.name_prefix}-${local.suffix}"
  # Names with no separators for resources that disallow hyphens.
  compact = "${var.name_prefix}${local.suffix}"
  tags    = var.tags
}

# ------------------------------------------------------------------
# Foundation
# ------------------------------------------------------------------

resource "azurerm_resource_group" "rg" {
  name     = "rg-${local.base}"
  location = var.location
  tags     = local.tags
}

resource "azurerm_log_analytics_workspace" "law" {
  name                = "law-${local.base}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.tags
}

resource "azurerm_application_insights" "appi" {
  name                = "appi-${local.base}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.law.id
  tags                = local.tags
}

# ------------------------------------------------------------------
# BYO Registry (theme: enterprise image provenance)
# ------------------------------------------------------------------

resource "azurerm_container_registry" "acr" {
  name                = "acr${local.compact}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "Standard"
  admin_enabled       = false
  tags                = local.tags
}

# ------------------------------------------------------------------
# Secrets
# ------------------------------------------------------------------

resource "azurerm_key_vault" "kv" {
  name                      = "kv-${local.base}"
  location                  = azurerm_resource_group.rg.location
  resource_group_name       = azurerm_resource_group.rg.name
  tenant_id                 = data.azurerm_client_config.current.tenant_id
  sku_name                  = "standard"
  enable_rbac_authorization = true
  purge_protection_enabled  = false
  tags                      = local.tags
}

# ------------------------------------------------------------------
# RAG data plane: Storage + Azure AI Search (Foundry IQ backing)
# ------------------------------------------------------------------

resource "azurerm_storage_account" "sa" {
  name                            = "st${local.compact}"
  location                        = azurerm_resource_group.rg.location
  resource_group_name             = azurerm_resource_group.rg.name
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  shared_access_key_enabled       = false # tenant policy: Entra-only data-plane auth
  allow_nested_items_to_be_public = false
  tags                            = local.tags
}

resource "azurerm_storage_container" "rag" {
  name                  = "rag-docs"
  storage_account_id    = azurerm_storage_account.sa.id
  container_access_type = "private"
}

resource "azurerm_search_service" "search" {
  name                         = "srch-${local.base}"
  location                     = azurerm_resource_group.rg.location
  resource_group_name          = azurerm_resource_group.rg.name
  sku                          = var.search_sku
  local_authentication_enabled = false

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# ------------------------------------------------------------------
# Workload identity for the app
# ------------------------------------------------------------------

resource "azurerm_user_assigned_identity" "app" {
  name                = "id-${local.base}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tags                = local.tags
}

# Pull images from ACR.
resource "azurerm_role_assignment" "app_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}

# Read secrets from Key Vault.
resource "azurerm_role_assignment" "app_kv_secrets" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}

# Read from Storage (RAG docs).
resource "azurerm_role_assignment" "app_storage_reader" {
  scope                = azurerm_storage_account.sa.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}

# Query the search index.
resource "azurerm_role_assignment" "app_search_reader" {
  scope                = azurerm_search_service.search.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}

# Call Foundry model inference.
resource "azurerm_role_assignment" "app_ai_user" {
  scope                = azurerm_ai_services.foundry.id
  role_definition_name = "Cognitive Services User"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}

# Search service reads blobs for indexing.
resource "azurerm_role_assignment" "search_storage_reader" {
  scope                = azurerm_storage_account.sa.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_search_service.search.identity[0].principal_id
}

# ------------------------------------------------------------------
# Container Apps: backend API + built UI (single image)
# ------------------------------------------------------------------

resource "azurerm_container_app_environment" "cae" {
  name                       = "cae-${local.base}"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.law.id
  tags                       = local.tags
}

resource "azurerm_container_app" "app" {
  name                         = "ca-${local.base}"
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

  ingress {
    external_enabled = true
    target_port      = 8080
    transport        = "auto"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.app_min_replicas
    max_replicas = var.app_max_replicas

    container {
      name   = "app"
      image  = var.container_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "HOST"
        value = "0.0.0.0"
      }
      env {
        name  = "PORT"
        value = "8080"
      }
      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.appi.connection_string
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.app.client_id
      }
      # Delegate agent invocation to the sidecar agent service over localhost.
      env {
        name  = "AGENT_SERVICE_URL"
        value = "http://localhost:8081"
      }
      env {
        name  = "AZURE_SEARCH_ENDPOINT"
        value = "https://${azurerm_search_service.search.name}.search.windows.net"
      }
      env {
        name  = "KEY_VAULT_URI"
        value = azurerm_key_vault.kv.vault_uri
      }
    }

    # Sidecar: the Python code-first multi-agent service. Shares the network
    # namespace with the backend, so the backend reaches it at localhost:8081.
    container {
      name   = "agent"
      image  = var.container_image_agent
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "HOST"
        value = "0.0.0.0"
      }
      env {
        name  = "PORT"
        value = "8081"
      }
      # Managed identity for Foundry model calls (SDK path via DefaultAzureCredential).
      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.app.client_id
      }
      env {
        name  = "AZURE_AI_PROJECT_ENDPOINT"
        value = "https://${azurerm_ai_services.foundry.name}.services.ai.azure.com/api/projects/${local.project_name}"
      }
      env {
        name  = "AZURE_AI_FOUNDRY_ACCOUNT"
        value = azurerm_ai_services.foundry.name
      }
      env {
        name  = "FOUNDRY_MODEL_DEPLOYMENT"
        value = azurerm_cognitive_deployment.model.name
      }
      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.appi.connection_string
      }
    }
  }

  depends_on = [
    azurerm_role_assignment.app_acr_pull
  ]
}
