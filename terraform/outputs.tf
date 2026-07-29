# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "bnx_scripts_bucket" {
  description = "Bucket de scripts BNX"
  value       = aws_s3_bucket.bnx_scripts.id
}

output "glue_spark_job" {
  description = "Nombre del Glue job PySpark"
  value       = aws_glue_job.bnx_test_spark.name
}

output "glue_glue_job" {
  description = "Nombre del Glue job AWS Glue"
  value       = aws_glue_job.bnx_test_glue.name
}

output "glue_role_arn" {
  description = "ARN del Glue role (del lakehouse)"
  value       = data.aws_iam_role.glue_role.arn
}

output "account_id" {
  description = "Account ID de DataLab"
  value       = data.aws_caller_identity.current.account_id
}

output "api_url" {
  description = "URL del API Gateway (BNX Compiler)"
  value       = "https://6lewkixco1.execute-api.us-east-1.amazonaws.com/prod"
}

output "amplify_url" {
  description = "URL de Amplify (UI)"
  value       = "https://empresav4.d142k2cigcx7cr.amplifyapp.com"
}

output "lambda_name" {
  description = "Nombre de la Lambda BNX Compiler"
  value       = "datalake-bnx-compiler-dev"
}
