# -----------------------------------------------------------------------------
# AWS Glue — Pipeline de Pruebas y Ejecucion
#
# Cuando BNX genera codigo (target=spark o target=glue), estos jobs
# lo ejecutan contra datos de prueba y validan que el output sea correcto.
#
# Jobs:
# 1. test-spark  — ejecuta codigo generado con target=spark
# 2. test-glue   — ejecuta codigo generado con target=glue
# 3. validate    — compara output spark vs glue vs expected
# -----------------------------------------------------------------------------

# --- Glue Job: PySpark (codigo generado por BNX target=spark) ---
resource "aws_glue_job" "test_spark" {
  name     = "${var.project_name}-test-spark-${var.environment}"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${data.aws_s3_bucket.existing_e2e.id}/scripts/spark_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                    = "python"
    "--TempDir"                         = "s3://${data.aws_s3_bucket.existing_e2e.id}/temp/"
    "--enable-metrics"                  = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--INPUT_PATH"                      = "s3://${data.aws_s3_bucket.existing_e2e.id}/raw/orders"
    "--OUTPUT_PATH"                     = "s3://${data.aws_s3_bucket.existing_e2e.id}/output/spark_output"
  }

  glue_version      = "4.0"
  number_of_workers = var.glue_num_workers
  worker_type       = var.glue_worker_type
  timeout           = 30
  max_retries       = 0

  execution_property {
    max_concurrent_runs = 1
  }

  tags = merge(local.common_tags, {
    Component = "Pipeline-Testing"
    Target    = "PySpark"
  })
}

# --- Glue Job: AWS Glue (codigo generado por BNX target=glue) ---
resource "aws_glue_job" "test_glue" {
  name     = "${var.project_name}-test-glue-${var.environment}"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${data.aws_s3_bucket.existing_e2e.id}/scripts/glue_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                    = "python"
    "--TempDir"                         = "s3://${data.aws_s3_bucket.existing_e2e.id}/temp/"
    "--enable-metrics"                  = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--INPUT_PATH"                      = "s3://${data.aws_s3_bucket.existing_e2e.id}/raw/orders"
    "--OUTPUT_PATH"                     = "s3://${data.aws_s3_bucket.existing_e2e.id}/output/glue_output"
  }

  glue_version      = "4.0"
  number_of_workers = var.glue_num_workers
  worker_type       = var.glue_worker_type
  timeout           = 30
  max_retries       = 0

  execution_property {
    max_concurrent_runs = 1
  }

  tags = merge(local.common_tags, {
    Component = "Pipeline-Testing"
    Target    = "AWSGlue"
  })
}

# --- Glue Job: Validacion de output (Python Shell, barato) ---
resource "aws_glue_job" "validate" {
  name     = "${var.project_name}-validate-${var.environment}"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "pythonshell"
    script_location = "s3://${data.aws_s3_bucket.existing_e2e.id}/scripts/validate_output.py"
    python_version  = "3.9"
  }

  default_arguments = {
    "--job-language"  = "python"
    "--SPARK_OUTPUT"  = "s3://${data.aws_s3_bucket.existing_e2e.id}/output/spark_output"
    "--GLUE_OUTPUT"   = "s3://${data.aws_s3_bucket.existing_e2e.id}/output/glue_output"
    "--EXPECTED_PATH" = "s3://${data.aws_s3_bucket.existing_e2e.id}/expected/"
  }

  max_capacity = 0.0625
  timeout      = 10
  max_retries  = 0

  tags = merge(local.common_tags, {
    Component = "Pipeline-Testing"
    Target    = "Validation"
  })
}

# -----------------------------------------------------------------------------
# Glue Catalog Database
# -----------------------------------------------------------------------------
resource "aws_glue_catalog_database" "bnx" {
  name        = replace("${var.project_name}_${var.environment}", "-", "_")
  description = "Glue Data Catalog - BNX Convertidor ETL jobs"
}
