provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }

  # Tenant policy disables shared-key auth on storage accounts, so the provider must use Entra
  # (AAD) for storage data-plane operations (e.g. reading queue/blob service properties).
  storage_use_azuread = true

  # subscription_id can be set here or via ARM_SUBSCRIPTION_ID / az login context.
  subscription_id = var.subscription_id != "" ? var.subscription_id : null
}

provider "azapi" {}

provider "random" {}
