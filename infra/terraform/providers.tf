provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }

  # subscription_id can be set here or via ARM_SUBSCRIPTION_ID / az login context.
  subscription_id = var.subscription_id != "" ? var.subscription_id : null
}

provider "azapi" {}

provider "random" {}
