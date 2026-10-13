# Illustrative Terraform for the remediation example. Not a real environment.

resource "aws_kms_key" "ledger" {
  description             = "Ledger encryption key"
  deletion_window_in_days = 30
}

resource "aws_sqs_queue" "events" {
  name = "chatbot-events"
}

resource "aws_db_instance" "ledger" {
  identifier          = "ledger"
  engine              = "postgres"
  instance_class      = "db.t3.medium"
  allocated_storage   = 20
  storage_encrypted   = true
  deletion_protection = false # flagged by CKV_AWS_293
}
