resource "azurerm_resource_group" "example" {
  name     = "example-resources"
  location = "West Europe"
}

resource "azurerm_key_vault" "keyvault" {
  name                       = "kvcpeq${var.environment}${var.location}"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  enable_rbac_authorization  = true

  sku_name = "standard"
}

resource "azurerm_role_assignment" "terraform_secrets" {
  scope                = azurerm_key_vault.keyvault.id
  principal_id         = var.build_pipeline_object_id
  role_definition_name = "Key Vault Secrets Officer"
}

resource "azurerm_role_assignment" "containerapp_read_secrets" {
  scope                = azurerm_container_registry.acr.id
  principal_id         = azurerm_user_assigned_identity.identity.principal_id
  role_definition_name = "Key Vault Secrets User"
}

resource "time_sleep" "wait_rbac_propagation" {
  depends_on      = [azurerm_role_assignment.terraform_secrets, azurerm_role_assignment.containerapp_read_secrets]
  create_duration = "1m"

  triggers = {
    container_app  = azurerm_role_assignment.terraform_secrets.scope
    build_pipeline = azurerm_role_assignment.containerapp_read_secrets.scope
  }
}

resource "azurerm_key_vault_secret" "onedrive_client_id" {
  name         = "onedrive-client-id"
  value        = var.onedrive_client_id
  key_vault_id = azurerm_key_vault.keyvault.id
}

resource "azurerm_key_vault_secret" "onedrive_client_secret" {
  name         = "onedrive-client-secret"
  value        = var.onedrive_client_secret
  key_vault_id = azurerm_key_vault.keyvault.id
}

resource "azurerm_key_vault_secret" "onedrive_tenant_id" {
  name         = "onedrive-tenant-id"
  value        = var.onedrive_tenant_id
  key_vault_id = azurerm_key_vault.keyvault.id
}

resource "azurerm_key_vault_secret" "openai_api_key" {
  name         = "openai-api-key"
  value        = var.openai_api_key
  key_vault_id = azurerm_key_vault.keyvault.id
}

resource "azurerm_key_vault_secret" "webscraper_io_api_key" {
  name         = "webscraper-io-api-key"
  value        = var.webscraper_io_api_key
  key_vault_id = azurerm_key_vault.keyvault.id
}
