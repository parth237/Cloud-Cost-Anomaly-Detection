variable "aws_region" {
  description = "AWS region for cost optimization resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "alert_email" {
  description = "Email address to receive cost anomaly alerts"
  type        = string
  default     = "cloud-ops@example.com"
}

variable "schedule_expression" {
  description = "EventBridge cron schedule for daily audit execution"
  type        = string
  default     = "cron(0 6 * * ? *)" # Runs daily at 06:00 UTC
}