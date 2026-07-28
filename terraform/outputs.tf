# ═══════════════════════════════════════════════════════════
# Outputs
# ═══════════════════════════════════════════════════════════

output "lambda_function_url" {
  description = "URL de la Lambda (API del compilador)"
  value       = aws_lambda_function_url.compiler_url.function_url
}

output "lambda_function_name" {
  description = "Nombre de la Lambda function"
  value       = aws_lambda_function.compiler.function_name
}

output "lambda_role_arn" {
  description = "ARN del rol de Lambda"
  value       = aws_iam_role.lambda_role.arn
}

output "amplify_app_url" {
  description = "URL de la app Amplify (frontend)"
  value       = "https://${var.amplify_branch}.${aws_amplify_app.frontend.id}.amplifyapp.com"
}

output "amplify_app_id" {
  description = "ID de la app Amplify"
  value       = aws_amplify_app.frontend.id
}

output "data_bucket_name" {
  description = "Nombre del bucket de datos"
  value       = aws_s3_bucket.data_bucket.id
}

output "scripts_bucket_name" {
  description = "Nombre del bucket de scripts"
  value       = aws_s3_bucket.scripts_bucket.id
}

output "reports_bucket_name" {
  description = "Nombre del bucket de reportes"
  value       = aws_s3_bucket.reports_bucket.id
}

output "glue_job_name" {
  description = "Nombre del Glue job principal"
  value       = aws_glue_job.bnx_etl.name
}

output "glue_role_arn" {
  description = "ARN del rol de Glue"
  value       = aws_iam_role.glue_role.arn
}

output "cloudwatch_dashboard_url" {
  description = "URL del dashboard de CloudWatch"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.bnx_dashboard.dashboard_name}"
}

output "sns_topic_arn" {
  description = "ARN del topic SNS para alertas"
  value       = aws_sns_topic.alerts.arn
}
