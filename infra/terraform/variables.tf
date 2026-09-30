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

# ------------------------------------------------------------------
# Remote/hosted MCP server (governed clinical tool boundary)
# ------------------------------------------------------------------
variable "enable_mcp_server" {
  description = "Deploy the governed clinical MCP server as an internal-ingress Container App. Default false keeps the base deploy unchanged (stdio/in-process tools still work)."
  type        = bool
  default     = false
}

variable "container_image_mcp" {
  description = "Full image reference for the remote MCP server container. On first apply use a public placeholder; the deploy script builds mcp-server/Dockerfile and re-applies with the real image."
  type        = string
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

# ------------------------------------------------------------------
# Work IQ — consumed M365 work-context service (Entra delegated / OBO only)
# ------------------------------------------------------------------
# Work IQ is a Microsoft-hosted, governed MCP/A2A/REST service. We do NOT provision it — these
# variables only plumb the endpoint + a feature flag into the app/agent so they can call it as a
# SEPARATE lane from the clinical MCP server. Auth is delegated/on-behalf-of at request time; there
# is no app-only credential to store here. See docs/work-iq-overview.md.
variable "enable_workiq" {
  description = "Advertise Work IQ (M365 work context) to the app/agent. Requires Entra delegated/OBO sign-in at runtime; no secret is provisioned."
  type        = bool
  default     = false
}

variable "workiq_endpoint" {
  description = "Work IQ endpoint base URL the agent uses for M365 work context (confirm per tenant against Microsoft Learn). Only used when enable_workiq=true."
  type        = string
  default     = "https://workiq.svc.cloud.microsoft/"
}

variable "search_sku" {
  description = "Azure AI Search SKU (basic or standard recommended for managed identity)."
  type        = string
  default     = "basic"
}

variable "search_location" {
  description = "Region for Azure AI Search. Separate from var.location because Search 'basic' SKU capacity is region-specific: swedencentral had no basic capacity (ResourcesForSkuUnavailable), so Search runs in norwayeast — a low-demand Nordic region near the rest of the workload."
  type        = string
  default     = "norwayeast"
}

# ------------------------------------------------------------------
# Durable Task Scheduler (DTS) — durable HITL approval gate
# ------------------------------------------------------------------

variable "enable_dts" {
  description = "Provision the Durable Task Scheduler, its task hub, the data-plane role, and the worker Container App. Default false keeps the standard gated apply unchanged. Requires the Microsoft.DurableTask provider to be registered on the subscription."
  type        = bool
  default     = false
}

variable "dts_taskhub_name" {
  description = "Name of the DTS task hub the worker and client bind to."
  type        = string
  default     = "discharge"
}

variable "dts_sku_name" {
  description = "DTS scheduler SKU name (e.g. Dedicated)."
  type        = string
  default     = "Dedicated"
}

variable "dts_sku_capacity" {
  description = "DTS scheduler SKU capacity (dedicated throughput units)."
  type        = number
  default     = 1
}

variable "hitl_mode" {
  description = "Human-in-the-loop backend the agent service uses: 'local' (in-memory TaskStore) or 'dts' (Durable Task Scheduler). Set to 'dts' only once enable_dts=true and the service DtsGate integration is in place."
  type        = string
  default     = "local"

  validation {
    condition     = contains(["local", "dts"], var.hitl_mode)
    error_message = "hitl_mode must be 'local' or 'dts'."
  }
}

variable "hitl_sla_seconds" {
  description = "Durable review SLA in seconds before an undecided run auto-escalates."
  type        = number
  default     = 86400
}
