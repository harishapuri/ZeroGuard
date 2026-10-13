# Illustrative Terraform for the remediation example. Not a real environment.

resource "aws_lb" "chatbot" {
  name               = "chatbot-alb"
  load_balancer_type = "application"
  subnets            = ["subnet-a", "subnet-b"]
}

resource "aws_security_group" "chatbot" {
  name = "chatbot-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_policy" "chatbot_admin" {
  name   = "chatbot-admin"
  policy = jsonencode({ Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }] })
}
