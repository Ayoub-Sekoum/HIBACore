resource "azurerm_container_app_environment" "this" {
  name                       = "${var.project_name}-env-${var.environment}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = var.log_analytics_workspace_id
  infrastructure_subnet_id   = var.subnet_id

  tags = var.tags
}

resource "azurerm_container_app" "backend" {
  name                         = "${var.project_name}-backend-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Multiple"

  template {
    container {
      name   = "backend"
      image  = var.backend_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "APP_NAME"
        value = "HOBA AI"
      }
      env {
        name  = "CORS_ORIGINS"
        value = "https://kind-sea-0cb86dc03.7.azurestaticapps.net,http://localhost:5173"
      }
      env {
        name  = "ENVIRONMENT"
        value = "prod"
      }
      # Add other necessary env vars from implementation plan
    }
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 8000
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [var.managed_identity_id]
  }

  registry {
    server   = split("/", var.backend_image)[0]
    identity = var.managed_identity_id
  }


  tags = var.tags
}

resource "azurerm_container_app" "worker" {
  name                         = "${var.project_name}-worker-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  template {
    container {
      name   = "worker"
      image  = var.backend_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "IS_WORKER"
        value = "true"
      }
    }
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [var.managed_identity_id]
  }

  registry {
    server   = split("/", var.backend_image)[0]
    identity = var.managed_identity_id
  }


  tags = var.tags
}

output "backend_url" {
  value = azurerm_container_app.backend.ingress[0].fqdn
}

output "aca_environment_id" {
  value = azurerm_container_app_environment.this.id
}
