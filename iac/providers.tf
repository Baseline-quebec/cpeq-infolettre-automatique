terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0.2"
    }

    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.15.0"
    }
  }

  required_version = ">= 1.8.0"
}

provider "azurerm" {
  features {}

  # This provider is configured through environment variables.
}

provider "azuread" {
  # This provider is configured through environment variables.
}
