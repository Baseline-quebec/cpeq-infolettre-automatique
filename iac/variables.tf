variable "environment" {
  type        = string
  description = "The name of the current environment."
  default     = "dev"
}

variable "location" {
  type        = string
  description = "The Azure Location where to deploy resources."
}

variable "build_pipeline_object_id" {
  type        = string
  description = "Object ID of the Service Principal used by the Build pipeline to push Docker images to the Container Registry"
}

variable "onedrive_client_id" {
  sensitive   = true
  type        = string
  description = "Client ID of the Service Principal used to interact with OneDrive. The value of this variable is stored as an Environment Secret in Github, is injected in Terraform through Github Action, and is meant to be stored in a Keyvault."
}

variable "onedrive_client_secret" {
  sensitive   = true
  type        = string
  description = "Client Secret of the Service Principal used to interact with OneDrive. The value of this variable is stored as an Environment Secret in Github, is injected in Terraform through Github Action, and is meant to be stored in a Keyvault."
}

variable "onedrive_tenant_id" {
  sensitive   = true
  type        = string
  description = "Tenant ID of the Service Principal used to interact with OneDrive. The value of this variable is stored as an Environment Secret in Github, is injected in Terraform through Github Action, and is meant to be stored in a Keyvault."
}

variable "openai_api_key" {
  sensitive   = true
  type        = string
  description = "OpenAI API Key. The value of this variable is stored as an Environment Secret in Github, is injected in Terraform through Github Action, and is meant to be stored in a Keyvault."
}

variable "webscraper_io_api_key" {
  sensitive   = true
  type        = string
  description = "WebscraperIO API Key. The value of this variable is stored as an Environment Secret in Github, is injected in Terraform through Github Action, and is meant to be stored in a Keyvault."
}
