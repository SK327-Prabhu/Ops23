variable "aws_region" {
  type        = string
  description = "AWS region for deploying Ops23 infrastructure"
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Project name prefix used for resource naming and tagging"
  default     = "ops23"
}

variable "environment" {
  type        = string
  description = "Deployment environment (e.g., dev, staging, prod)"
  default     = "dev"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type for the application host"
  default     = "t3.micro"
}

variable "ami_id" {
  type        = string
  description = "Specific AMI ID for the EC2 instance. If left blank, the latest Amazon Linux 2023 AMI is selected automatically."
  default     = ""
}

variable "app_port" {
  type        = number
  description = "TCP port on which the Ops23 FastAPI application listens"
  default     = 8000
}
