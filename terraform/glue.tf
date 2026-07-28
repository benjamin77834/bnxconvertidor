# ═══════════════════════════════════════════════════════════
# AWS Glue — ETL Jobs (generados por BNX)
# ═══════════════════════════════════════════════════════════

# --- Glue Job template (para jobs generados por el compilador) ---
resource "aws_glue_job" "bnx_etl" {
  name     = "${var.project_name}-etl-job"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.scripts_bucket.id}/glue/bnx_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"           = "python"
    "--TempDir"                = "s3://${aws_s3_bucket.scripts_bucket.id}/temp/"
    "--enable-metrics"         = "true"
    "--enable-spark-ui"        = "true"
    "--spark-event-logs-path"  = "s3://${aws_s3_bucket.scripts_bucket.id}/spark-logs/"
    "--enable-continuous-cloudwatch-log" = "true"
  }

  glue_version      = "4.0"
  number_of_workers = var.glue_num_workers
  worker_type       = var.glue_worker_type
  timeout           = 60
  max_retries       = 1

  execution_property {
    max_concurrent_runs = 3
  }

  tags = {
    Component = "ETL"
    Generated = "BNX-Compiler"
  }
}

# --- Glue Job para E2E testing ---
resource "aws_glue_job" "bnx_e2e_test" {
  name     = "${var.project_name}-e2e-test"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.scripts_bucket.id}/glue/e2e_test.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language" = "python"
    "--TempDir"      = "s3://${aws_s3_bucket.scripts_bucket.id}/temp/"
  }

  glue_version      = "4.0"
  number_of_workers = 2
  worker_type       = "G.1X"
  timeout           = 30
  max_retries       = 0

  tags = {
    Component = "Testing"
  }
}

# --- Glue Catalog Database ---
resource "aws_glue_catalog_database" "bnx_db" {
  name = replace("${var.project_name}-${var.environment}", "-", "_")

  description = "Base de datos del catalogo para BNX Convertidor ETL jobs"
}
