terraform {
  required_version = ">= 1.8.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.53"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote state — Azure Blob Storage
  # Credentials injected via environment variables in CI (OIDC)
  # ARM_CLIENT_ID / ARM_SUBSCRIPTION_ID / ARM_TENANT_ID
  backend "azurerm" {
    resource_group_name  = "rg-tfstate"
    storage_account_name = "sttfstatechatbot" # set per environment
    container_name       = "tfstate"
    key                  = "chatbot.terraform.tfstate"
    use_oidc             = true # GitHub Actions OIDC — no stored credentials
  }
}
