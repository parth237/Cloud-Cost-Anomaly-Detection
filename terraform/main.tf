terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "Cloud-Cost-Anomaly-Detection"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# 1. IAM Role for Lambda with Least-Privilege Permissions
resource "aws_iam_role" "lambda_cost_auditor_role" {
  name = "cost-anomaly-detector-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Read-only policy for Cost Explorer and CloudWatch
resource "aws_iam_policy" "cost_read_policy" {
  name        = "CostExplorerAndMetricsReadOnly"
  description = "Allows reading Cost Explorer data and CloudWatch metrics"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetAnomalies",
          "cloudwatch:GetMetricData",
          "ec2:DescribeInstances",
          "ec2:DescribeVolumes",
          "rds:DescribeDBInstances"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_cost_policy" {
  role       = aws_iam_role.lambda_cost_auditor_role.name
  policy_arn = aws_iam_policy.cost_read_policy.arn
}

# 2. SNS Alert Topic for Anomaly Notifications
resource "aws_sns_topic" "cost_anomaly_alerts" {
  name = "cloud-cost-anomaly-alerts"
}

resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.cost_anomaly_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# 3. EventBridge Rule (Daily Scheduled Trigger)
resource "aws_cloudwatch_event_rule" "daily_cost_audit_schedule" {
  name                = "daily-cost-anomaly-audit-trigger"
  description         = "Triggers cost audit Lambda function daily at 06:00 UTC"
  schedule_expression = var.schedule_expression
}