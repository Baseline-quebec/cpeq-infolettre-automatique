resource "azurerm_resource_group" "rg" {
  name     = "CPEQ-${var.environment}"
  location = var.location

  tags = {
    environment = var.environment
    project     = "CPEQ"
  }
}
