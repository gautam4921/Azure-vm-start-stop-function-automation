data "azurerm_client_config" "current" {}

resource "random_string" "suffix" {
  length  = 7
  lower   = true
  upper   = false
  numeric = true
  special = false
}

locals {
  common_tags = {
    Project     = "Azure-VM-Start-Stop"
    Environment = title(var.target_environment)
    ManagedBy   = "Terraform"
  }

  storage_account_name = "stvmauto${random_string.suffix.result}"
  function_app_name    = "${var.function_app_name_prefix}-${random_string.suffix.result}"
}

resource "azurerm_resource_group" "function" {
  name     = var.function_resource_group_name
  location = var.location
  tags     = local.common_tags
}

resource "azurerm_resource_group" "vm" {
  name     = var.vm_resource_group_name
  location = var.location
  tags     = local.common_tags
}

resource "azurerm_storage_account" "function" {
  name                     = local.storage_account_name
  resource_group_name      = azurerm_resource_group.function.name
  location                 = azurerm_resource_group.function.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  tags = local.common_tags
}

resource "azurerm_storage_container" "deployment" {
  name                  = "function-deployment"
  storage_account_id    = azurerm_storage_account.function.id
  container_access_type = "private"
}

resource "azurerm_log_analytics_workspace" "function" {
  name                = "law-vm-automation-${random_string.suffix.result}"
  location            = azurerm_resource_group.function.location
  resource_group_name = azurerm_resource_group.function.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.common_tags
}

resource "azurerm_application_insights" "function" {
  name                = "appi-vm-auto-${random_string.suffix.result}"
  location            = azurerm_resource_group.function.location
  resource_group_name = azurerm_resource_group.function.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.function.id
  tags                = local.common_tags
}

resource "azurerm_service_plan" "flex" {
  name                = "asp-vm-auto-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.function.name
  location            = azurerm_resource_group.function.location
  os_type             = "Linux"
  sku_name            = "FC1"
  tags                = local.common_tags
}
