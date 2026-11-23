# Function App identity: manage VMs only in the target VM resource group.
resource "azurerm_role_assignment" "function_vm_contributor" {
  scope                = azurerm_resource_group.vm.id
  role_definition_name = "Virtual Machine Contributor"
  principal_id         = azurerm_function_app_flex_consumption.vm_automation.identity[0].principal_id
  principal_type       = "ServicePrincipal"
}

# Flex deployment package storage and Functions host storage use the Function App identity.
resource "azurerm_role_assignment" "function_storage_blob" {
  scope                = azurerm_storage_account.function.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = azurerm_function_app_flex_consumption.vm_automation.identity[0].principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "function_storage_queue" {
  scope                = azurerm_storage_account.function.id
  role_definition_name = "Storage Queue Data Contributor"
  principal_id         = azurerm_function_app_flex_consumption.vm_automation.identity[0].principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "function_storage_table" {
  scope                = azurerm_storage_account.function.id
  role_definition_name = "Storage Table Data Contributor"
  principal_id         = azurerm_function_app_flex_consumption.vm_automation.identity[0].principal_id
  principal_type       = "ServicePrincipal"
}
