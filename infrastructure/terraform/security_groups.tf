# Security group for Ops23 application host
# Note: Inbound SSH (port 22) is intentionally omitted.
# All operational and diagnostic access is handled securely via AWS Systems Manager (SSM) Session Manager.
resource "aws_security_group" "app_sg" {
  name        = "${var.project_name}-${var.environment}-app-sg"
  description = "Security group for Ops23 FastAPI application (Inbound port ${var.app_port}, no inbound SSH)"

  # Inbound traffic for FastAPI application and /health endpoint
  ingress {
    description = "Allow inbound HTTP traffic to Ops23 FastAPI application"
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound traffic: required for SSM Agent, Datadog telemetry, and OS updates
  egress {
    description = "Allow all outbound traffic for SSM agent, telemetry, and package management"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-app-sg"
  }
}
