# ------------------------------------------------------------------
# Microsoft Foundry: AI Services account + project + model deployment
# ------------------------------------------------------------------

locals {
  project_name = "proj-${local.base}"
}

# Foundry resource (Microsoft.CognitiveServices/accounts, kind = AIServices).
resource "azurerm_ai_services" "foundry" {
  name                  = "ais-${local.base}"
  location              = azurerm_resource_group.rg.location
  resource_group_name   = azurerm_resource_group.rg.name
  sku_name              = "S0"
  custom_subdomain_name = "ais-${local.base}"

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# Agent-compatible model deployment on the Foundry account.
resource "azurerm_cognitive_deployment" "model" {
  name                 = var.model_name
  cognitive_account_id = azurerm_ai_services.foundry.id

  model {
    format  = "OpenAI"
    name    = var.model_name
    version = var.model_version
  }

  sku {
    name     = var.model_sku
    capacity = var.model_capacity
  }
}

# Enable project management on the Foundry account (required before a project can be created).
# Not yet surfaced as a first-class azurerm argument, so patch it via azapi.
resource "azapi_update_resource" "foundry_allow_projects" {
  type        = "Microsoft.CognitiveServices/accounts@2025-04-01-preview"
  resource_id = azurerm_ai_services.foundry.id

  body = {
    properties = {
      allowProjectManagement = true
    }
  }
}

# Foundry project (new Foundry experience) as a sub-resource of the account.
# API version may need to be updated as the platform evolves.
resource "azapi_resource" "project" {
  type      = "Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview"
  name      = local.project_name
  parent_id = azurerm_ai_services.foundry.id
  location  = azurerm_resource_group.rg.location

  depends_on = [azapi_update_resource.foundry_allow_projects]

  identity {
    type = "SystemAssigned"
  }

  body = {
    properties = {
      displayName = "Discharge Transition Exception Coordinator"
      description = "Foundry Phase 2 workshop project (synthetic data)."
    }
  }

  tags = local.tags
}

# Connect Application Insights to the Foundry project so server-side agent
# tracing lights up automatically. API version may need updating over time.
resource "azapi_resource" "appinsights_connection" {
  type      = "Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview"
  name      = "appinsights"
  parent_id = azapi_resource.project.id

  body = {
    properties = {
      category      = "AppInsights"
      target        = azurerm_application_insights.appi.id
      authType      = "ApiKey"
      isSharedToAll = true
      credentials = {
        key = azurerm_application_insights.appi.connection_string
      }
      metadata = {
        ApiType    = "Azure"
        ResourceId = azurerm_application_insights.appi.id
      }
    }
  }
}
