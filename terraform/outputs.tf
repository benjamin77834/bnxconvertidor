# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

# --- Recursos EXISTENTES (referencia, no gestionados) ---
output "existing_lambda_arn" {
  description = "ARN de la Lambda existente (no gestionada por TF)"
  value       = data.aws_lambda_function.existing_compiler.arn
}

output "existing_e2e_bucket" {
  description = "Bucket E2E existente"
  value       = data.aws_s3_bucket.existing_e2e.id
}

# --- S3 Buckets (nuevos) ---
output "landing_bucket" {
  description = "Bucket Landing (grafos originales del banco)"
  value       = aws_s3_bucket.landing.id
}

output "bronze_bucket" {
  description = "Bucket Bronze (codigo generado por BNX)"
  value       = aws_s3_bucket.bronze.id
}

output "gold_bucket" {
  description = "Bucket Gold (output validado)"
  value       = aws_s3_bucket.gold.id
}

output "scripts_bucket" {
  description = "Bucket de scripts Glue"
  value       = aws_s3_bucket.scripts.id
}

# --- Pipeline ---
output "pipeline_arn" {
  description = "ARN del pipeline Step Functions"
  value       = aws_sfn_state_machine.e2e_pipeline.arn
}

output "pipeline_console_url" {
  description = "URL de la consola Step Functions"
  value       = "https://${var.aws_region}.console.aws.amazon.com/states/home?region=${var.aws_region}#/statemachines/view/${aws_sfn_state_machine.e2e_pipeline.arn}"
}

output "pipeline_start_command" {
  description = "Comando para ejecutar el pipeline manualmente"
  value       = "aws stepfunctions start-execution --state-machine-arn ${aws_sfn_state_machine.e2e_pipeline.arn} --region ${var.aws_region}"
}

# --- Glue Jobs ---
output "glue_spark_job" {
  description = "Nombre del Glue job PySpark"
  value       = aws_glue_job.test_spark.name
}

output "glue_glue_job" {
  description = "Nombre del Glue job AWS Glue"
  value       = aws_glue_job.test_glue.name
}

output "glue_validate_job" {
  description = "Nombre del Glue job de validacion"
  value       = aws_glue_job.validate.name
}

# --- Monitoreo ---
output "dashboard_url" {
  description = "URL del dashboard CloudWatch"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.bnx.dashboard_name}"
}

output "sns_topic_arn" {
  description = "ARN del topic SNS para alertas"
  value       = aws_sns_topic.alerts.arn
}
