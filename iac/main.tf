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

resource "azurerm_user_assigned_identity" "identity" {
  location            = azurerm_resource_group.rg.location
  name                = "id-func-${var.environment}-${var.location}"
  resource_group_name = azurerm_resource_group.rg.name

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}

resource "azurerm_role_assignment" "app_acrpull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.identity.principal_id
}

resource "azurerm_container_app_environment" "environment" {
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

  ingress {
    target_port  = 8000
    exposed_port = 80
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.identity.id
  }

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}
