# ---------------------------------------------------------------------------
# modules/networking/main.tf
# Hub-Spoke Virtual Network with Private DNS Zones and NSGs
# ---------------------------------------------------------------------------

locals {
  prefix = "${var.project_name}-${var.environment}"

  # Private DNS zones needed for all services behind Private Endpoints
  private_dns_zones = {
    keyvault   = "privatelink.vaultcore.azure.net"
    cosmos     = "privatelink.documents.azure.com"
    postgres   = "privatelink.postgres.database.azure.com"
    blob       = "privatelink.blob.core.windows.net"
    openai     = "privatelink.openai.azure.com"
    search     = "privatelink.search.windows.net"
    servicebus = "privatelink.servicebus.windows.net"
  }
}

# ---------------------------------------------------------------------------
# Resource Groups
# ---------------------------------------------------------------------------

resource "azurerm_resource_group" "hub" {
  name     = "rg-${local.prefix}-hub"
  location = var.location
  tags     = var.tags
}

resource "azurerm_resource_group" "spoke" {
  name     = "rg-${local.prefix}-spoke"
  location = var.location
  tags     = var.tags
}

# ---------------------------------------------------------------------------
# Hub Virtual Network
# Used for transit, DNS, future NVA/Firewall
# ---------------------------------------------------------------------------

resource "azurerm_virtual_network" "hub" {
  name                = "vnet-${local.prefix}-hub"
  resource_group_name = azurerm_resource_group.hub.name
  location            = azurerm_resource_group.hub.location
  address_space       = [var.hub_vnet_address_space]
  tags                = var.tags

  # Azure-provided DNS for Private DNS Zones
  dns_servers = []
}

# Hub has one subnet for future VPN/ExpressRoute Gateway
resource "azurerm_subnet" "hub_gateway" {
  name                 = "GatewaySubnet" # Required name for VPN/ER gateways
  resource_group_name  = azurerm_resource_group.hub.name
  virtual_network_name = azurerm_virtual_network.hub.name
  address_prefixes     = [cidrsubnet(var.hub_vnet_address_space, 8, 255)] # .255.0/24
}

# ---------------------------------------------------------------------------
# Spoke Virtual Network — where all workloads live
# ---------------------------------------------------------------------------

resource "azurerm_virtual_network" "spoke" {
  name                = "vnet-${local.prefix}-spoke"
  resource_group_name = azurerm_resource_group.spoke.name
  location            = azurerm_resource_group.spoke.location
  address_space       = [var.spoke_vnet_address_space]
  tags                = var.tags

  dns_servers = []
}

# ---- Subnet: Private Endpoints ----
# All PaaS services are exposed exclusively here — no public IPs anywhere
resource "azurerm_subnet" "private_endpoints" {
  name                 = "snet-private-endpoints"
  resource_group_name  = azurerm_resource_group.spoke.name
  virtual_network_name = azurerm_virtual_network.spoke.name
  address_prefixes     = [var.subnet_private_endpoints_cidr]

  # Required for Private Endpoints
  private_endpoint_network_policies = "Disabled"
}

# ---- Subnet: Azure Container Apps ----
resource "azurerm_subnet" "aca" {
  name                 = "snet-aca"
  resource_group_name  = azurerm_resource_group.spoke.name
  virtual_network_name = azurerm_virtual_network.spoke.name
  address_prefixes     = [var.subnet_aca_cidr]

  delegation {
    name = "aca-delegation"
    service_delegation {
      name = "Microsoft.App/environments"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

# ---- Subnet: API Management ----
resource "azurerm_subnet" "apim" {
  name                 = "snet-apim"
  resource_group_name  = azurerm_resource_group.spoke.name
  virtual_network_name = azurerm_virtual_network.spoke.name
  address_prefixes     = [var.subnet_apim_cidr]
}

# ---- Subnet: Azure Container Instances (Tool Sandbox) ----
resource "azurerm_subnet" "aci" {
  name                 = "snet-aci"
  resource_group_name  = azurerm_resource_group.spoke.name
  virtual_network_name = azurerm_virtual_network.spoke.name
  address_prefixes     = [var.subnet_aci_cidr]

  delegation {
    name = "aci-delegation"
    service_delegation {
      name = "Microsoft.ContainerInstance/containerGroups"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/action",
      ]
    }
  }
}

# ---------------------------------------------------------------------------
# VNet Peering — Hub ↔ Spoke (bidirectional)
# ---------------------------------------------------------------------------

resource "azurerm_virtual_network_peering" "hub_to_spoke" {
  name                      = "peer-hub-to-spoke"
  resource_group_name       = azurerm_resource_group.hub.name
  virtual_network_name      = azurerm_virtual_network.hub.name
  remote_virtual_network_id = azurerm_virtual_network.spoke.id

  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
  allow_gateway_transit        = true # Hub can share gateway with spokes
  use_remote_gateways          = false
}

resource "azurerm_virtual_network_peering" "spoke_to_hub" {
  name                      = "peer-spoke-to-hub"
  resource_group_name       = azurerm_resource_group.spoke.name
  virtual_network_name      = azurerm_virtual_network.spoke.name
  remote_virtual_network_id = azurerm_virtual_network.hub.id

  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
  allow_gateway_transit        = false
  use_remote_gateways          = false # set true when hub has VPN gateway
}

# ---------------------------------------------------------------------------
# Private DNS Zones — one per service type
# All zones linked to BOTH hub and spoke so DNS resolves everywhere
# ---------------------------------------------------------------------------

resource "azurerm_private_dns_zone" "zones" {
  for_each = local.private_dns_zones

  name                = each.value
  resource_group_name = azurerm_resource_group.hub.name
  tags                = var.tags
}

# Link every DNS zone to the Hub VNet
resource "azurerm_private_dns_zone_virtual_network_link" "hub_links" {
  for_each = local.private_dns_zones

  name                  = "link-hub-${each.key}"
  resource_group_name   = azurerm_resource_group.hub.name
  private_dns_zone_name = azurerm_private_dns_zone.zones[each.key].name
  virtual_network_id    = azurerm_virtual_network.hub.id
  registration_enabled  = false
  tags                  = var.tags
}

# Link every DNS zone to the Spoke VNet
resource "azurerm_private_dns_zone_virtual_network_link" "spoke_links" {
  for_each = local.private_dns_zones

  name                  = "link-spoke-${each.key}"
  resource_group_name   = azurerm_resource_group.hub.name
  private_dns_zone_name = azurerm_private_dns_zone.zones[each.key].name
  virtual_network_id    = azurerm_virtual_network.spoke.id
  registration_enabled  = false
  tags                  = var.tags
}

# ---------------------------------------------------------------------------
# Network Security Groups
# ---------------------------------------------------------------------------

# NSG: Private Endpoints subnet
# Only allow traffic FROM within the VNet — deny everything from internet
resource "azurerm_network_security_group" "private_endpoints" {
  name                = "nsg-${local.prefix}-private-endpoints"
  location            = var.location
  resource_group_name = azurerm_resource_group.spoke.name
  tags                = var.tags

  security_rule {
    name                       = "AllowVNetInbound"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "VirtualNetwork"
  }

  security_rule {
    name                       = "DenyInternetInbound"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "Internet"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "DenyInternetOutbound"
    priority                   = 4096
    direction                  = "Outbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "Internet"
  }
}

resource "azurerm_subnet_network_security_group_association" "private_endpoints" {
  subnet_id                 = azurerm_subnet.private_endpoints.id
  network_security_group_id = azurerm_network_security_group.private_endpoints.id
}

# NSG: ACI (Tool sandbox) — deny Internet outbound; only Service Bus/OpenAI via private endpoints
resource "azurerm_network_security_group" "aci" {
  name                = "nsg-${local.prefix}-aci"
  location            = var.location
  resource_group_name = azurerm_resource_group.spoke.name
  tags                = var.tags

  # Allow ACI to reach private endpoints subnet (for Service Bus, OpenAI calls)
  security_rule {
    name                       = "AllowToPrivateEndpoints"
    priority                   = 100
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["443", "5671", "5672"]
    source_address_prefix      = var.subnet_aci_cidr
    destination_address_prefix = var.subnet_private_endpoints_cidr
  }

  # Allow Azure infrastructure (IMDS, management)
  security_rule {
    name                       = "AllowAzureCloud"
    priority                   = 200
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = var.subnet_aci_cidr
    destination_address_prefix = "AzureCloud"
  }

  # Block all other Internet access — prevents data exfiltration from tool sandbox
  security_rule {
    name                       = "DenyInternetOutbound"
    priority                   = 4096
    direction                  = "Outbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "Internet"
  }
}

resource "azurerm_subnet_network_security_group_association" "aci" {
  subnet_id                 = azurerm_subnet.aci.id
  network_security_group_id = azurerm_network_security_group.aci.id
}

# NSG: APIM subnet — allow APIM management traffic + client HTTPS
resource "azurerm_network_security_group" "apim" {
  name                = "nsg-${local.prefix}-apim"
  location            = var.location
  resource_group_name = azurerm_resource_group.spoke.name
  tags                = var.tags

  # Required by APIM in Internal mode: Azure management plane
  security_rule {
    name                       = "AllowAPIMManagement"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3443"
    source_address_prefix      = "ApiManagement"
    destination_address_prefix = "VirtualNetwork"
  }

  # Allow HTTPS from VNet (ACA containers call APIM internally)
  security_rule {
    name                       = "AllowHTTPSFromVNet"
    priority                   = 200
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "VirtualNetwork"
  }

  security_rule {
    name                       = "DenyInternetInbound"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "Internet"
    destination_address_prefix = "*"
  }
}

resource "azurerm_subnet_network_security_group_association" "apim" {
  subnet_id                 = azurerm_subnet.apim.id
  network_security_group_id = azurerm_network_security_group.apim.id
}
