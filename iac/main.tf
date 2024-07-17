resource "azurerm_resource_group" "rg" {
  name     = "CPEQ-${var.environment}"
  location = var.location

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}

resource "azurerm_container_registry" "acr" {
  name                = "crcpeq${var.environment}${var.location}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = false

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
  sku_name            = "Y1"

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}

resource "azurerm_user_assigned_identity" "function_app" {
  location            = azurerm_resource_group.rg.location
  name                = "id-func-${var.environment}-${var.location}"
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_role_assignment" "func_acr" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.function_app.principal_id
}

resource "azurerm_linux_function_app" "function_app" {
  name                = "func-cpeq-${var.environment}-${var.location}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  storage_account_name       = azurerm_storage_account.storage.name
  storage_account_access_key = azurerm_storage_account.storage.primary_access_key
  service_plan_id            = azurerm_service_plan.service_plan.id
  https_only                 = true

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.function_app.id]
  }

  site_config {

    application_stack {
      python_version = 3.12
    }
  }

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}
