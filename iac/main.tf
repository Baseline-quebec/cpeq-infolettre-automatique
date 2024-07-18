resource "azurerm_resource_group" "rg" {
  name     = "CPEQ-${var.environment}"
  location = var.location

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}

resource "azurerm_storage_account" "storage" {
  name                     = "st0cpeq0${var.environment}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}

resource "azurerm_service_plan" "service_plan" {
  name                = "asp-cpeq-${var.environment}-${var.location}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "Y1"

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}

resource "azurerm_linux_function_app" "function_app" {
  depends_on          = [azurerm_storage_account.storage]
  name                = "func-cpeq-${var.environment}-${var.location}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  storage_account_name        = azurerm_storage_account.storage.name
  storage_account_access_key  = azurerm_storage_account.storage.primary_access_key
  service_plan_id             = azurerm_service_plan.service_plan.id
  https_only                  = true
  functions_extension_version = "~4"

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}

resource "azurerm_linux_function_app_slot" "dev" {
  name                       = "dev"
  function_app_id            = azurerm_linux_function_app.function_app.id
  storage_account_name       = azurerm_storage_account.storage.name
  storage_account_access_key = azurerm_storage_account.storage.primary_access_key
  https_only                 = true

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }
}
