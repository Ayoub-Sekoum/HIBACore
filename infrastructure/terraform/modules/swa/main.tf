resource "azurerm_static_web_app" "this" {
  name                = "${var.project_name}-frontend-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku_tier            = "Free"
  sku_size            = "Free"

  tags = var.tags
}

output "frontend_url" {
  value = azurerm_static_web_app.this.default_host_name
}

output "api_key" {
  value = azurerm_static_web_app.this.api_key
  sensitive = true
}
