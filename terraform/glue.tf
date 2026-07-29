# -----------------------------------------------------------------------------
# AWS Glue — Jobs de BNX Convertidor (Pipeline E2E)
# Usa el Glue Role existente del lakehouse (datalake-glue-role-dev)
# -----------------------------------------------------------------------------

# --- Glue Job: PySpark (codigo generado por BNX target=spark) ---
resource "aws_glue_job" "bnx_test_spark" {
  name     = "${var.project_name}-bnx-test-spark-${var.environment}"
  role_arn = data.aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.bnx_scripts.id}/spark/spark_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                    = "python"
    "--TempDir"                         = "s3://${aws_s3_bucket.bnx_scripts.id}/temp/"
    "--enable-metrics"                  = "true"
    "--enable-continuous-cloudwatch-log" = "true"
  }

  glue_version      = "4.0"
  number_of_workers = var.glue_num_workers
  worker_type       = var.glue_worker_type
  timeout           = 30
  max_retries       = 0

  execution_property {
    max_concurrent_runs = 1
  }

  tags = merge(local.common_tags, { Target = "PySpark" })
}

# --- Glue Job: AWS Glue (codigo generado por BNX target=glue) ---
resource "aws_glue_job" "bnx_test_glue" {
  name     = "${var.project_name}-bnx-test-glue-${var.environment}"
  role_arn = data.aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.bnx_scripts.id}/glue/glue_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                    = "python"
    "--TempDir"                         = "s3://${aws_s3_bucket.bnx_scripts.id}/temp/"
    "--enable-metrics"                  = "true"
    "--enable-continuous-cloudwatch-log" = "true"
  }

  glue_version      = "4.0"
  number_of_workers = var.glue_num_workers
  worker_type       = var.glue_worker_type
  timeout           = 30
  max_retries       = 0

  execution_property {
    max_concurrent_runs = 1
  }

  tags = merge(local.common_tags, { Target = "AWSGlue" })
}
