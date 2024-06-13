terraform {
  backend "azurerm" {
    resource_group_name  = "Baseline-Core-Resources"
    storage_account_name = "baseline0terraform"
    container_name       = "cpeq"
    key                  = "terraform.tfstate"
    use_oidc             = true
    use_azuread_auth     = true
  }
}
