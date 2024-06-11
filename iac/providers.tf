terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0.2"
    }
  }

  required_version = ">= 1.8.0"

  backend "azurerm" {
    resource_group_name  = "Baseline-Core-Resources"
    storage_account_name = "baseline0terraform"
    container_name       = "cpeq"
    key                  = "terraform.tfstate"
    use_oidc             = true
    use_azuread_auth     = true
  }
}

provider "azurerm" {
  features {}

  # This provider is configured through environment variables.
  # See variables/dev.tfvars for values
}
