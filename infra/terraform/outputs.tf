output "resource_group" {
  description = "Resource group containing all workshop resources."
  value       = azurerm_resource_group.rg.name
}

output "app_url" {
  description = "Public URL of the deployed app (backend API + UI)."
  value       = "https://${azurerm_container_app.app.ingress[0].fqdn}"
}

output "acr_login_server" {
  description = "Azure Container Registry login server for image build/push."
  value       = azurerm_container_registry.acr.login_server
}

output "acr_name" {
  description = "Azure Container Registry name (for az acr build)."
  value       = azurerm_container_registry.acr.name
}

output "foundry_account_name" {
  description = "Microsoft Foundry (AI Services) account name."
  value       = azurerm_ai_services.foundry.name
}

output "foundry_project_endpoint" {
  description = "Foundry project endpoint for the agent runtime."
  value       = "https://${azurerm_ai_services.foundry.name}.services.ai.azure.com/api/projects/${local.project_name}"
}

output "model_deployment" {
  description = "Deployed Foundry model name."
  value       = azurerm_cognitive_deployment.model.name
}

output "application_insights_connection_string" {
  description = "Application Insights connection string."
  value       = azurerm_application_insights.appi.connection_string
  sensitive   = true
}

output "search_endpoint" {
  description = "Azure AI Search endpoint (Foundry IQ / RAG backing)."
  value       = "https://${azurerm_search_service.search.name}.search.windows.net"
}

output "key_vault_uri" {
  description = "Key Vault URI."
  value       = azurerm_key_vault.kv.vault_uri
}

output "app_identity_client_id" {
  description = "Client ID of the app's user-assigned managed identity."
  value       = azurerm_user_assigned_identity.app.client_id
}

output "dts_endpoint" {
  description = "Durable Task Scheduler endpoint (empty unless enable_dts=true)."
  value       = local.dts_endpoint
}

output "dts_taskhub" {
  description = "Durable Task Scheduler task hub name (empty unless enable_dts=true)."
  value       = var.enable_dts ? local.dts_taskhub : ""
}

output "mcp_internal_endpoint" {
  description = "Internal (private) URL of the hosted MCP server. Empty unless enable_mcp_server=true. Reachable only inside the Container App Environment / VNet."
  value       = var.enable_mcp_server ? "https://${try(azurerm_container_app.mcp[0].ingress[0].fqdn, "")}" : ""
}

output "workiq_endpoint" {
  description = "Work IQ endpoint advertised to the app/agent (empty unless enable_workiq=true). Consumed via Entra delegated/OBO at runtime; not provisioned here."
  value       = var.enable_workiq ? var.workiq_endpoint : ""
}
