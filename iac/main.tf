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

data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "build_pipeline" {
  scope                = azurerm_container_registry.acr.id
  principal_id         = var.build_pipeline_object_id
  role_definition_name = "AcrPush"
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

resource "azurerm_role_assignment" "acrpull" {
  scope                = azurerm_container_registry.acr.id
  principal_id         = azurerm_user_assigned_identity.identity.principal_id
  role_definition_name = "AcrPull"
}

resource "time_sleep" "wait_rbac_propagation" {
  depends_on      = [azurerm_role_assignment.acrpull, azurerm_role_assignment.build_pipeline]
  create_duration = "1m"

  triggers = {
    container_app  = azurerm_role_assignment.acrpull.scope
    build_pipeline = azurerm_role_assignment.build_pipeline.scope
  }
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
      image  = "${azurerm_container_registry.acr.login_server}/cpeq/infolettre-automatique:latest"
      cpu    = 1
      memory = "2.0Gi"
    }
    max_replicas = 1
    min_replicas = 0

    http_scale_rule {
      name                = "wake-up-container"
      concurrent_requests = 1
    }
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.identity.id]
  }

  ingress {
    target_port      = 8000
    external_enabled = true
    transport        = "http2"
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
