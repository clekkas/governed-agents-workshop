terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.20"
    }
    azapi = {
      source  = "azure/azapi"
      version = "~> 2.2"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote state (Stage 2+): activate by copying backend.tf.example to backend.tf and running
  # `terraform init -migrate-state -backend-config=...`. Left out here so Stage 1 uses local state
  # with zero friction. See infra/DEPLOYMENT.md.
}
