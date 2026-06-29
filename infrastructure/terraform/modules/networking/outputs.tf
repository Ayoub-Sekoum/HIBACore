# ---------------------------------------------------------------------------
# modules/networking/outputs.tf
# ---------------------------------------------------------------------------

output "resource_group_hub_name" {
  description = "Hub resource group name"
  value       = azurerm_resource_group.hub.name
}

output "resource_group_spoke_name" {
  description = "Spoke resource group name"
  value       = azurerm_resource_group.spoke.name
}

output "hub_vnet_id" {
  description = "Hub Virtual Network ID"
  value       = azurerm_virtual_network.hub.id
}

output "spoke_vnet_id" {
  description = "Spoke Virtual Network ID"
  value       = azurerm_virtual_network.spoke.id
}

output "subnet_private_endpoints_id" {
  description = "Subnet ID for Private Endpoints — used by all other modules"
  value       = azurerm_subnet.private_endpoints.id
}

output "subnet_aca_id" {
  description = "Subnet ID for Azure Container Apps environment"
  value       = azurerm_subnet.aca.id
}

output "subnet_apim_id" {
  description = "Subnet ID for API Management (Internal VNet mode)"
  value       = azurerm_subnet.apim.id
}

output "subnet_aci_id" {
  description = "Subnet ID for Azure Container Instances (tool sandbox)"
  value       = azurerm_subnet.aci.id
}

# Private DNS Zone IDs — referenced by modules creating Private Endpoints
output "private_dns_zone_ids" {
  description = "Map of service name → Private DNS Zone ID"
  value = {
    for k, v in azurerm_private_dns_zone.zones : k => v.id
  }
}

# Private DNS Zone Names — referenced by azurerm_private_dns_zone_group
output "private_dns_zone_names" {
  description = "Map of service name → Private DNS Zone name (FQDN)"
  value = {
    for k, v in azurerm_private_dns_zone.zones : k => v.name
  }
}
