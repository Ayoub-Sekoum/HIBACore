# ---------------------------------------------------------------------------
# modules/networking/variables.tf
# ---------------------------------------------------------------------------

variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "location" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}

# ---- VNet CIDRs ----

variable "hub_vnet_address_space" {
  type    = string
  default = "10.0.0.0/16"
}

variable "spoke_vnet_address_space" {
  type    = string
  default = "10.1.0.0/16"
}

variable "subnet_private_endpoints_cidr" {
  type    = string
  default = "10.1.0.0/24"
}

variable "subnet_aca_cidr" {
  type    = string
  default = "10.1.1.0/23"
}

variable "subnet_apim_cidr" {
  type    = string
  default = "10.1.3.0/28"
}

variable "subnet_aci_cidr" {
  type    = string
  default = "10.1.4.0/24"
}
