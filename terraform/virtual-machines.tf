resource "azurerm_public_ip" "vm" {
  for_each            = var.vm_names
  name                = "pip-${each.key}"
  location            = azurerm_resource_group.vm.location
  resource_group_name = azurerm_resource_group.vm.name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = local.common_tags
}

resource "azurerm_network_interface" "vm" {
  for_each            = var.vm_names
  name                = "nic-${each.key}"
  location            = azurerm_resource_group.vm.location
  resource_group_name = azurerm_resource_group.vm.name
  tags                = local.common_tags

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.vm.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.vm[each.key].id
  }
}

resource "azurerm_network_interface_security_group_association" "vm" {
  for_each                  = var.vm_names
  network_interface_id      = azurerm_network_interface.vm[each.key].id
  network_security_group_id = azurerm_network_security_group.vm.id
}

resource "azurerm_linux_virtual_machine" "vm" {
  for_each            = var.vm_names
  name                = each.key
  computer_name       = each.key
  location            = azurerm_resource_group.vm.location
  resource_group_name = azurerm_resource_group.vm.name
  size                = var.vm_size
  admin_username      = var.vm_admin_username

  network_interface_ids = [
    azurerm_network_interface.vm[each.key].id
  ]

  disable_password_authentication = true

  admin_ssh_key {
    username   = var.vm_admin_username
    public_key = var.admin_ssh_public_key
  }

  os_disk {
    name                 = "osdisk-${each.key}"
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  tags = merge(local.common_tags, {
    Environment  = title(var.target_environment)
    AutoSchedule = "true"
  })
}
