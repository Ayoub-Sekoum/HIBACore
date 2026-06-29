# ---------------------------------------------------------------------------
# Global Variables — AI Multi-Tenant Chatbot Enterprise
# ---------------------------------------------------------------------------

variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  sensitive   = true
}

variable "entra_tenant_id" {
  description = "Microsoft Entra (Azure AD) Tenant ID"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Short project identifier, used in resource naming"
  type        = string
  default     = "chatbot"
}

variable "location" {
  description = "Primary Azure region"
  type        = string
  default     = "westeurope"
}

variable "location_secondary" {
  description = "Secondary Azure region for failover (OpenAI, Cosmos)"
  type        = string
  default     = "northeurope"
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

variable "hub_vnet_address_space" {
  description = "CIDR block for the Hub VNet"
  type        = string
  default     = "10.0.0.0/16"
}

variable "spoke_vnet_address_space" {
  description = "CIDR block for the Spoke VNet"
  type        = string
  default     = "10.1.0.0/16"
}

# Subnet CIDRs (inside spoke)
variable "subnet_private_endpoints_cidr" {
  type    = string
  default = "10.1.0.0/24"
}

variable "subnet_aca_cidr" {
  type    = string
  default = "10.1.1.0/23" # Azure Container Apps require /21 min, using /23 for dev
}

variable "subnet_apim_cidr" {
  type    = string
  default = "10.1.3.0/28"
}

variable "subnet_aci_cidr" {
  type    = string
  default = "10.1.4.0/24"
}

# ---------------------------------------------------------------------------
# Sizing (overridden per environment)
# ---------------------------------------------------------------------------

variable "cosmos_throughput" {
  description = "Cosmos DB provisioned throughput (RU/s)"
  type        = number
  default     = 400
}

variable "postgres_sku" {
  description = "PostgreSQL Flexible Server SKU"
  type        = string
  default     = "GP_Standard_D2s_v3"
}

variable "postgres_storage_mb" {
  description = "PostgreSQL storage in MB"
  type        = number
  default     = 32768 # 32 GB
}

variable "apim_sku" {
  description = "API Management SKU (e.g. Developer_1, Premium_1)"
  type        = string
  default     = "Developer_1"
}

variable "servicebus_sku" {
  description = "Service Bus namespace SKU — Premium required for Private Endpoints"
  type        = string
  default     = "Premium"
}

variable "log_retention_days" {
  description = "Log Analytics retention in days"
  type        = number
  default     = 90
}

# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

variable "owner_email" {
  description = "Owner contact email, added to all resource tags"
  type        = string
  default     = "platform@company.com"
}
# ---------------------------------------------------------------------------
# Missing Variables for ACA and SWA
# ---------------------------------------------------------------------------

variable "resource_group_name" {
  description = "Name of the resource group (if not created in networking)"
  type        = string
  default     = ""
}

variable "log_analytics_workspace_id" {
  description = "Log Analytics Workspace ID for ACA environment"
  type        = string
  default     = ""
}

variable "managed_identity_id" {
  description = "User Managed Identity ID for ACA"
  type        = string
  default     = ""
}
