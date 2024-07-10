resource "azurerm_resource_group" "rg" {
  name     = "CPEQ-${var.environment}"
  location = var.location

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}

resource "azurerm_storage_account" "storage" {
  name                     = "st0cpeq0${var.environment}0${var.location}"
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
  sku_name            = "F1"

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}

resource "azurerm_linux_function_app" "function_app" {
  name                = "func-automated-newsletter-${var.environment}-${var.location}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  storage_account_name       = azurerm_storage_account.storage.name
  storage_account_access_key = azurerm_storage_account.storage.primary_access_key
  service_plan_id            = azurerm_service_plan.service_plan.id

  site_config {}

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}
