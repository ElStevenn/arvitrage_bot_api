variable "vpc_id" {
  description = "The ID of the VPC where resources will be deployed."
  type        = string
}

variable "subnet_id" {
  description = "The ID of the subnet where the EC2 instance will be deployed."
  type        = string
}
