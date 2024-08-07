terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.111.0"
    }
  }

  required_version = ">= 1.8.0"
}

provider "azurerm" {
  features {}
  # This provider is configured through environment variables.
}
