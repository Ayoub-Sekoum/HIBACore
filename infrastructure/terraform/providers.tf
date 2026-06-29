provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
    cognitive_account {
      purge_soft_delete_on_destroy = false
    }
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
  }

  # Authenticates via:
  # - OIDC in GitHub Actions (use_oidc = true must be set in backend OR via ARM_USE_OIDC env)
  # - Azure CLI locally (az login)
  # Never use client_secret in code.
  subscription_id = var.subscription_id
}

provider "azuread" {
  tenant_id = var.entra_tenant_id
}

provider "random" {}
