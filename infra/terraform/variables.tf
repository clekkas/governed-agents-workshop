variable "subscription_id" {
  description = "Azure subscription ID. Leave empty to use the az login / ARM_SUBSCRIPTION_ID context."
  type        = string
  default     = ""
}

variable "name_prefix" {
  description = "Short prefix for resource names (lowercase letters/numbers)."
  type        = string
  default     = "dtec"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{1,10}$", var.name_prefix))
    error_message = "name_prefix must be 2-11 chars, lowercase letters/numbers, starting with a letter."
  }
}

variable "location" {
  description = "Azure region for all resources."
  type        = string
  default     = "swedencentral"
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default = {
    workload    = "foundry-phase2"
    environment = "workshop"
    data        = "synthetic-only"
    managed_by  = "terraform"
  }
}

variable "model_name" {
  description = "Foundry model to deploy for the agent."
  type        = string
  default     = "gpt-4o"
}

variable "model_version" {
  description = "Model version for the deployment."
  type        = string
  default     = "2024-11-20"
}

variable "model_capacity" {
  description = "Deployment capacity (thousands of tokens per minute)."
  type        = number
  default     = 30
}

variable "model_sku" {
  description = "Deployment SKU name (e.g. GlobalStandard, Standard)."
  type        = string
  default     = "GlobalStandard"
}

variable "container_image" {
  description = "Full image reference for the app container. On first apply, use a public placeholder; the deploy script pushes the real image and re-applies."
  type        = string
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "container_image_agent" {
  description = "Full image reference for the Python agent sidecar container. On first apply, use a public placeholder; the deploy script pushes the real image and re-applies."
  type        = string
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "app_min_replicas" {
  description = "Minimum container app replicas."
  type        = number
  default     = 1
}

variable "app_max_replicas" {
  description = "Maximum container app replicas."
  type        = number
  default     = 3
}

variable "search_sku" {
  description = "Azure AI Search SKU (basic or standard recommended for managed identity)."
  type        = string
  default     = "basic"
}

variable "search_location" {
  description = "Region for Azure AI Search. Separate from var.location so Search can be placed in a region with available capacity. Consolidated to swedencentral with the rest of the workload (eastus2/centralus had intermittent InsufficientResourcesAvailable)."
  type        = string
  default     = "swedencentral"
}
