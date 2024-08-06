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
