variable "vpc_id" {
  description = "The ID of the VPC where resources will be deployed."
  type        = string
}

variable "subnet_id" {
  description = "The ID of the subnet where the EC2 instance will be deployed."
  type        = string
}

variable "ami_id" {
  description = "ID for the AMI instance (image)"
  type = string
  sensitive = false
}

variable "commit_message" {
    description = "value"
    type = string
    sensitive = false
}
