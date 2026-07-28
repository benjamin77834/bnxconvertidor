# -----------------------------------------------------------------------------
# CloudWatch + SNS — Monitoreo y Alertas
# Usa data source de la Lambda existente (no la recrea)
# -----------------------------------------------------------------------------

# --- SNS Topic para alertas ---
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts-${var.environment}"
  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# -----------------------------------------------------------------------------
# Alarmas
# -----------------------------------------------------------------------------

# Lambda Errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.project_name}-lambda-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Lambda compiler tiene mas de 5 errores en 10 min"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = data.aws_lambda_function.existing_compiler.function_name
  }

  tags = local.common_tags
}

# Lambda Duration
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.project_name}-lambda-duration-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Average"
  threshold           = 30000
  alarm_description   = "Lambda promedio >30s"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = data.aws_lambda_function.existing_compiler.function_name
  }

  tags = local.common_tags
}

# Pipeline Failures
resource "aws_cloudwatch_metric_alarm" "pipeline_failures" {
  alarm_name          = "${var.project_name}-pipeline-failures-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Pipeline E2E fallo"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.e2e_pipeline.arn
  }

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Dashboard
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_dashboard" "bnx" {
  dashboard_name = "${var.project_name}-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "BNX Compiler: Invocations & Errors"
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", data.aws_lambda_function.existing_compiler.function_name],
            ["AWS/Lambda", "Errors", "FunctionName", data.aws_lambda_function.existing_compiler.function_name],
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "BNX Compiler: Duration (ms)"
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", data.aws_lambda_function.existing_compiler.function_name, { stat = "Average" }],
            ["AWS/Lambda", "Duration", "FunctionName", data.aws_lambda_function.existing_compiler.function_name, { stat = "p99" }],
          ]
          period = 300
          region = var.aws_region
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "Pipeline E2E: Executions"
          metrics = [
            ["AWS/States", "ExecutionsStarted", "StateMachineArn", aws_sfn_state_machine.e2e_pipeline.arn],
            ["AWS/States", "ExecutionsSucceeded", "StateMachineArn", aws_sfn_state_machine.e2e_pipeline.arn],
            ["AWS/States", "ExecutionsFailed", "StateMachineArn", aws_sfn_state_machine.e2e_pipeline.arn],
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "Pipeline Trigger Lambda"
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.pipeline_trigger.function_name],
            ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.pipeline_trigger.function_name],
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
        }
      },
    ]
  })
}

# -----------------------------------------------------------------------------
# Budget (Control de costos, como bnxlakehouse)
# -----------------------------------------------------------------------------
resource "aws_budgets_budget" "monthly" {
  name         = "${var.project_name}-monthly-${var.environment}"
  budget_type  = "COST"
  limit_amount = var.budget_monthly
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }
}
