resource "azurerm_virtual_network" "vm" {
  name                = "vnet-vm-automation"
  address_space       = ["10.10.0.0/16"]
  location            = azurerm_resource_group.vm.location
  resource_group_name = azurerm_resource_group.vm.name
  tags                = local.common_tags
}

resource "azurerm_subnet" "vm" {
  name                 = "snet-vm"
  resource_group_name  = azurerm_resource_group.vm.name
  virtual_network_name = azurerm_virtual_network.vm.name
  address_prefixes     = ["10.10.1.0/24"]
}

resource "azurerm_network_security_group" "vm" {
  name                = "nsg-vm-automation"
  location            = azurerm_resource_group.vm.location
  resource_group_name = azurerm_resource_group.vm.name
  tags                = local.common_tags

  security_rule {
    name                       = "Allow-SSH-From-Admin"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = var.admin_source_cidr
    destination_address_prefix = "*"
  }
}

resource "azurerm_subnet_network_security_group_association" "vm" {
  subnet_id                 = azurerm_subnet.vm.id
  network_security_group_id = azurerm_network_security_group.vm.id
}
