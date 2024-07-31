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
  admin_enabled       = true

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}

resource "azurerm_role_assignment" "build_pipeline" {
  scope                = azurerm_container_registry.acr.id
  principal_id         = var.build_pipeline_client_id
  role_definition_name = "AcrPush"
}

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "keyvault" {
  name                        = "kvcpeq${var.environment}${var.location}"
  location                    = azurerm_resource_group.rg.location
  resource_group_name         = azurerm_resource_group.rg.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  enable_rbac_authorization   = true

  sku_name = "standard"
}

resource "azurerm_role_assignment" "terraform_secrets_admin" {
  scope                = azurerm_key_vault.keyvault.id
  principal_id         = data.azurerm_client_config.current.object_id
  role_definition_name = "Key Vault Secrets Officer"
}

resource "azurerm_user_assigned_identity" "identity" {
  location            = azurerm_resource_group.rg.location
  name                = "id-func-${var.environment}-${var.location}"
  resource_group_name = azurerm_resource_group.rg.name

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}

resource "azurerm_role_assignment" "keyvault_secret_read" {
  scope                = azurerm_key_vault.keyvault.id
  principal_id         = azurerm_user_assigned_identity.identity.principal_id
  role_definition_name = "Key Vault Secrets User"
}

resource "time_sleep" "wait_rbac_propagation" {
  depends_on      = [azurerm_role_assignment.keyvault_secret_read]
  create_duration = "1m"

  triggers = {
    container_app = azurerm_role_assignment.keyvault_secret_read.scope
    terraform     = azurerm_role_assignment.terraform_secrets_admin.scope
  }
}

resource "azurerm_key_vault_secret" "acr_password" {
  depends_on = [time_sleep.wait_rbac_propagation]

  name         = "ContainerRegistry--AdminPassword"
  value        = azurerm_container_registry.acr.admin_password
  key_vault_id = azurerm_key_vault.keyvault.id
}

resource "azurerm_container_app_environment" "environment" {
  depends_on = [time_sleep.wait_rbac_propagation]

  name                = "cae-cpeq-${var.environment}-${var.location}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}

resource "azurerm_container_app" "app" {
  name                         = "ca-cpeq-${var.environment}-${var.location}"
  container_app_environment_id = azurerm_container_app_environment.environment.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"

  template {
    container {
      name   = "infolettre-automatique"
      image  = "cpeq/infolettre-automatique:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
    max_replicas = 1
    min_replicas = 0
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.identity.id]
  }

  secret {
    name                = "acr-admin-password"
    identity            = azurerm_user_assigned_identity.identity.id
    key_vault_secret_id = azurerm_key_vault_secret.acr_password.id
  }

  registry {
    server               = azurerm_container_registry.acr.login_server
    username             = azurerm_container_registry.acr.admin_username
    password_secret_name = "acr-admin-password"
  }

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}
