resource "azurerm_function_app_flex_consumption" "vm_automation" {
  name                = local.function_app_name
  resource_group_name = azurerm_resource_group.function.name
  location            = azurerm_resource_group.function.location
  service_plan_id     = azurerm_service_plan.flex.id

  storage_container_type      = "blobContainer"
  storage_container_endpoint  = "${azurerm_storage_account.function.primary_blob_endpoint}${azurerm_storage_container.deployment.name}"
  storage_authentication_type = "SystemAssignedIdentity"

  runtime_name    = "python"
  runtime_version = "3.11"

  maximum_instance_count = var.maximum_instance_count
  instance_memory_in_mb  = var.instance_memory_in_mb

  https_only = true

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_insights_connection_string = azurerm_application_insights.function.connection_string
    minimum_tls_version                    = "1.2"
  }

  # Flex Consumption host storage uses identity-based connection settings.
  # AzureWebJobsStorage is intentionally empty for the current AzureRM provider workaround.
  app_settings = {
    #  "FUNCTIONS_WORKER_RUNTIME"         = "python"
    #  "FUNCTIONS_EXTENSION_VERSION"      = "~4"
    "AzureWebJobsStorage"                       = ""
    "AzureWebJobsStorage__accountName"          = azurerm_storage_account.function.name
    "APPLICATIONINSIGHTS_AUTHENTICATION_STRING" = "Authorization=AAD"
    "AZURE_SUBSCRIPTION_ID"                     = data.azurerm_client_config.current.subscription_id
    "TARGET_RESOURCE_GROUP"                     = azurerm_resource_group.vm.name
    "TARGET_ENVIRONMENT"                        = lower(var.target_environment)
    "DRY_RUN"                                   = tostring(var.dry_run)
    "ALLOW_PROD_AUTOMATION"                     = "false"
    "VM_START_SCHEDULE"                         = var.start_schedule_utc
    "VM_DEALLOCATE_SCHEDULE"                    = var.deallocate_schedule_utc
  }

  tags = local.common_tags

  lifecycle {
    ignore_changes = [
      app_settings["WEBSITE_RUN_FROM_PACKAGE"]
    ]
  }
}
