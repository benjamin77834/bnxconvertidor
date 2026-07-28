# -----------------------------------------------------------------------------
# Step Functions — Pipeline E2E de Pruebas
#
# Flujo:
# 1. Ejecutar Glue Job (PySpark) en paralelo con Glue Job (Glue)
# 2. Esperar que ambos terminen
# 3. Ejecutar validacion de output (comparar spark vs glue vs expected)
# 4. Notificar resultado via SNS
#
# Este pipeline NO toca la Lambda ni el Amplify existentes.
# Solo ejecuta los scripts que BNX ya genero y valida resultados.
# -----------------------------------------------------------------------------

resource "aws_sfn_state_machine" "e2e_pipeline" {
  name     = "${var.project_name}-e2e-pipeline-${var.environment}"
  role_arn = aws_iam_role.stepfunctions_role.arn

  definition = jsonencode({
    Comment = "BNX E2E: Ejecuta codigo generado en Spark y Glue, valida output"
    StartAt = "RunJobs"
    States = {

      # Step 1: Ejecutar ambos Glue Jobs en paralelo
      RunJobs = {
        Type     = "Parallel"
        Next     = "ValidateOutput"
        Branches = [
          {
            StartAt = "RunSparkJob"
            States = {
              RunSparkJob = {
                Type     = "Task"
                Resource = "arn:aws:states:::glue:startJobRun.sync"
                Parameters = {
                  JobName = aws_glue_job.test_spark.name
                }
                ResultPath = "$.sparkResult"
                Catch = [{
                  ErrorEquals = ["States.ALL"]
                  Next        = "SparkFailed"
                }]
                End = true
              }
              SparkFailed = {
                Type   = "Pass"
                Result = { status = "FAILED", target = "spark" }
                ResultPath = "$.sparkResult"
                End    = true
              }
            }
          },
          {
            StartAt = "RunGlueJob"
            States = {
              RunGlueJob = {
                Type     = "Task"
                Resource = "arn:aws:states:::glue:startJobRun.sync"
                Parameters = {
                  JobName = aws_glue_job.test_glue.name
                }
                ResultPath = "$.glueResult"
                Catch = [{
                  ErrorEquals = ["States.ALL"]
                  Next        = "GlueFailed"
                }]
                End = true
              }
              GlueFailed = {
                Type   = "Pass"
                Result = { status = "FAILED", target = "glue" }
                ResultPath = "$.glueResult"
                End    = true
              }
            }
          }
        ]
      }

      # Step 2: Validar output (Spark vs Glue vs Expected)
      ValidateOutput = {
        Type     = "Task"
        Resource = "arn:aws:states:::glue:startJobRun.sync"
        Parameters = {
          JobName = aws_glue_job.validate.name
        }
        ResultPath = "$.validation"
        Next       = "NotifySuccess"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "NotifyFailure"
        }]
      }

      # Step 3a: Exito
      NotifySuccess = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn = aws_sns_topic.alerts.arn
          Subject  = "BNX Pipeline E2E: PASSED"
          Message  = "Pipeline E2E completado. Spark y Glue generaron output correcto y validado."
        }
        End = true
      }

      # Step 3b: Fallo
      NotifyFailure = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn = aws_sns_topic.alerts.arn
          Subject  = "BNX Pipeline E2E: FAILED"
          Message  = "Pipeline E2E FALLO. Revisar logs en CloudWatch."
        }
        End = true
      }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.pipeline_logs.arn}:*"
    include_execution_data = true
    level                  = "ERROR"
  }

  tags = local.common_tags
}

# --- Log group para el pipeline ---
resource "aws_cloudwatch_log_group" "pipeline_logs" {
  name              = "/aws/states/${var.project_name}-e2e-pipeline-${var.environment}"
  retention_in_days = 14
  tags              = local.common_tags
}

# -----------------------------------------------------------------------------
# EventBridge — Ejecucion programada (opcional)
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_event_rule" "daily_e2e" {
  name                = "${var.project_name}-daily-e2e-${var.environment}"
  description         = "Ejecuta el pipeline E2E diariamente"
  schedule_expression = var.pipeline_schedule
  is_enabled          = var.enable_daily_pipeline

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "pipeline_target" {
  rule      = aws_cloudwatch_event_rule.daily_e2e.name
  target_id = "RunE2EPipeline"
  arn       = aws_sfn_state_machine.e2e_pipeline.arn
  role_arn  = aws_iam_role.eventbridge_role.arn

  input = jsonencode({
    test_suite = "daily"
    triggered  = "scheduled"
  })
}
