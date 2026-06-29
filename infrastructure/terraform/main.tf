# ---------------------------------------------------------------------------
# Root main.tf — AI Multi-Tenant Chatbot Enterprise
# Orchestrates all modules
# ---------------------------------------------------------------------------

locals {
  common_tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
    owner       = var.owner_email
    updated_at  = formatdate("YYYY-MM-DD", timestamp())
  }
  resource_group_name = "rg-${var.project_name}-${var.environment}"
}

# ---------------------------------------------------------------------------
# Monitoring & Identity (Satisfying dependencies for ACA)
# ---------------------------------------------------------------------------

resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-${var.project_name}-${var.environment}"
  location            = var.location
  resource_group_name = module.networking.resource_group_spoke_name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days
  tags                = local.common_tags
}

resource "azurerm_user_assigned_identity" "aca" {
  name                = "id-${var.project_name}-aca-${var.environment}"
  location            = var.location
  resource_group_name = module.networking.resource_group_spoke_name
  tags                = local.common_tags
}

resource "azurerm_container_registry" "main" {
  name                = "acr${replace(var.project_name, "-", "")}${var.environment}"
  resource_group_name = module.networking.resource_group_spoke_name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = true
  tags                = local.common_tags
}

resource "azurerm_role_assignment" "aca_acrpull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.aca.principal_id
}



# ---------------------------------------------------------------------------
# Task 1.01 — Networking (Hub-Spoke + Private DNS + NSGs)
# ---------------------------------------------------------------------------

module "networking" {
  source = "./modules/networking"

  project_name = var.project_name
  environment  = var.environment
  location     = var.location
  tags         = local.common_tags

  hub_vnet_address_space        = var.hub_vnet_address_space
  spoke_vnet_address_space      = var.spoke_vnet_address_space
  subnet_private_endpoints_cidr = var.subnet_private_endpoints_cidr
  subnet_aca_cidr               = var.subnet_aca_cidr
  subnet_apim_cidr              = var.subnet_apim_cidr
  subnet_aci_cidr               = var.subnet_aci_cidr
}

# ---------------------------------------------------------------------------
# Task 1.02 — Key Vault
# (module will be added in next task)
# ---------------------------------------------------------------------------

# module "keyvault" { ... }

# ---------------------------------------------------------------------------
# Task 1.03 — Log Analytics + Application Insights
# (module will be added in next task)
# ---------------------------------------------------------------------------

# module "monitoring" { ... }

# ---------------------------------------------------------------------------
# Task 1.04 — Azure OpenAI
# (module will be added in next task)
# ---------------------------------------------------------------------------

# module "openai" { ... }

# ---------------------------------------------------------------------------
# Task 1.05 — Cosmos DB
# ---------------------------------------------------------------------------

# module "cosmos" { ... }

# ---------------------------------------------------------------------------
# Task 1.06 — PostgreSQL Flexible Server
# ---------------------------------------------------------------------------

# module "postgres" { ... }

# ---------------------------------------------------------------------------
# Task 1.07 — Azure AI Search
# ---------------------------------------------------------------------------

# module "ai_search" { ... }

# ---------------------------------------------------------------------------
# Task 1.08 — Service Bus
# ---------------------------------------------------------------------------

# module "servicebus" { ... }

# ---------------------------------------------------------------------------
# Task 1.09 — Storage Account (RAG blobs)
# ---------------------------------------------------------------------------

# module "storage" { ... }

# ---------------------------------------------------------------------------
# Task 1.10 — Container Registry
# ---------------------------------------------------------------------------

# module "acr" { ... }

# ---------------------------------------------------------------------------
# Task 1.11 — Azure Container Apps Environment + Apps
# ---------------------------------------------------------------------------

module "aca" {
  source = "./modules/aca"

  project_name               = var.project_name
  environment                = var.environment
  location                   = var.location
  resource_group_name        = module.networking.resource_group_spoke_name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  subnet_id                  = module.networking.subnet_aca_id
  backend_image              = "acrhobaenterpriseprod.azurecr.io/hoba-backend:latest"
  managed_identity_id        = azurerm_user_assigned_identity.aca.id
  tags                       = local.common_tags
}




# ---------------------------------------------------------------------------
# Task 1.14 — Static Web App (Frontend)
# ---------------------------------------------------------------------------

module "swa" {
  source = "./modules/swa"

  project_name        = var.project_name
  environment         = var.environment
  location            = "westeurope" # SWA is restricted in some regions
  resource_group_name = module.networking.resource_group_spoke_name
  tags                = local.common_tags
}



