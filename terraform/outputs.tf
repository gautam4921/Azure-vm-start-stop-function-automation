output "subscription_id" {
  value = data.azurerm_client_config.current.subscription_id
}

output "function_resource_group" {
  value = azurerm_resource_group.function.name
}

output "vm_resource_group" {
  value = azurerm_resource_group.vm.name
}

output "function_app_name" {
  value = azurerm_function_app_flex_consumption.vm_automation.name
}

output "function_app_hostname" {
  value = azurerm_function_app_flex_consumption.vm_automation.default_hostname
}

output "function_app_principal_id" {
  value = azurerm_function_app_flex_consumption.vm_automation.identity[0].principal_id
}

output "storage_account_name" {
  value = azurerm_storage_account.function.name
}

output "vm_public_ips" {
  value = {
    for name, ip in azurerm_public_ip.vm : name => ip.ip_address
  }
}

output "vm_private_ips" {
  value = {
    for name, nic in azurerm_network_interface.vm :
    name => nic.ip_configuration[0].private_ip_address
  }
}
