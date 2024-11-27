variable "mongo_root_username" {
  description = "username for mongodb"
  type      = string
  sensitive = true
  default   = "root"
}

variable "mongo_root_password" {
  description = "password for mongodb"
  type        = string
  sensitive   = true
}

variable "subnet_id" {
  description = "subnet id"
  type        = string
  sensitive   = false
}

variable "vpc_id" {
  description = "Virtural Private Cloud ID"
  type        = string
  sensitive   = false
  default     = "vpc-00a6f6c0e0afb0484"
}