output "instance_id" {
  description = "The ID of the EC2 instance (used for SSM Run Command targeting and Datadog tagging)"
  value       = aws_instance.app_server.id
}

output "instance_private_ip" {
  description = "The private IPv4 address of the EC2 instance"
  value       = aws_instance.app_server.private_ip
}

output "instance_public_ip" {
  description = "The public IPv4 address of the EC2 instance (if allocated by default subnet)"
  value       = aws_instance.app_server.public_ip
}

output "security_group_id" {
  description = "The ID of the security group attached to the EC2 instance"
  value       = aws_security_group.app_sg.id
}

output "iam_role_arn" {
  description = "The Amazon Resource Name (ARN) of the IAM role attached to the EC2 instance"
  value       = aws_iam_role.ec2_role.arn
}

output "app_url" {
  description = "URL to access the Ops23 FastAPI application root once deployed"
  value       = "http://${aws_instance.app_server.public_ip}:${var.app_port}"
}

output "health_check_url" {
  description = "URL to access the Ops23 health check endpoint once deployed"
  value       = "http://${aws_instance.app_server.public_ip}:${var.app_port}/health"
}
