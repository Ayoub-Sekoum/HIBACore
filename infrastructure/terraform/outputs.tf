# ---------------------------------------------------------------------------
# Root outputs.tf
# ---------------------------------------------------------------------------

output "networking" {
  description = "Key networking outputs for reference"
  value = {
    spoke_vnet_id               = module.networking.spoke_vnet_id
    hub_vnet_id                 = module.networking.hub_vnet_id
    subnet_private_endpoints_id = module.networking.subnet_private_endpoints_id
    subnet_aca_id               = module.networking.subnet_aca_id
    subnet_apim_id              = module.networking.subnet_apim_id
    subnet_aci_id               = module.networking.subnet_aci_id
    resource_group_spoke        = module.networking.resource_group_spoke_name
    resource_group_hub          = module.networking.resource_group_hub_name
    private_dns_zone_ids        = module.networking.private_dns_zone_ids
  }
}
