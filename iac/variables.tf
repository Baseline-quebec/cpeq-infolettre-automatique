variable "environment" {
  type        = string
  description = "The name of the current environment."
  default     = "dev"
}

variable "location" {
  type        = string
  description = "The Azure Location where to deploy resources."
}
