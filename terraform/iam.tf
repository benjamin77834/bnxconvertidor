# =============================================================================
# IAM Roles - BNX Convertidor (Pipeline E2E)
# =============================================================================
#
# Este archivo define los roles y politicas IAM para el pipeline de pruebas
# de BNX Convertidor: Lambda (pipeline trigger), Glue (jobs E2E),
# Step Functions (orquestacion) y EventBridge (schedule).
#
# El rol "lambdarol" YA EXISTE — no se recrea, solo se referencia.
#
# =============================================================================
# TABLA RESUMEN DE PERMISOS
# =============================================================================
#
# ┌─────────────────────┬─────────────────────────────┬───────────────────────────────────────────┬──────────────┐
# │ ROL                 │ POLÍTICA                    │ ACCIONES                                  │ RECURSO      │
# ├─────────────────────┼─────────────────────────────┼───────────────────────────────────────────┼──────────────┤
# │ (existente)         │ bnx-pipeline-permissions    │ iam:PassRole, glue:Create/Update/Start,   │ lambdarol,   │
# │ lambdarol           │ (inline en AWS, no en TF)   │ s3:Put/Get/List                           │ bnx-e2e-test │
# ├─────────────────────┼─────────────────────────────┼───────────────────────────────────────────┼──────────────┤
# │ glue_role           │ AWSGlueServiceRole          │ (politica gestionada AWS)                 │ *            │
# │                     │ glue-s3-access              │ s3:Get/Put/Delete, ListBucket             │ landing,     │
# │                     │                             │                                           │ bronze, gold │
# │                     │                             │                                           │ scripts, e2e │
# ├─────────────────────┼─────────────────────────────┼───────────────────────────────────────────┼──────────────┤
# │ lambda_pipeline     │ LambdaBasicExecution        │ (politica gestionada AWS)                 │ logs         │
# │                     │ pipeline-policy             │ lambda:Invoke, s3:Put/Get, glue:Start,    │ bnx-compiler,│
# │                     │                             │ states:StartExecution                     │ buckets, sfn │
# ├─────────────────────┼─────────────────────────────┼───────────────────────────────────────────┼──────────────┤
# │ stepfunctions_role  │ sfn-policy                  │ lambda:Invoke, glue:Start/Get/Stop,       │ compiler,    │
# │                     │                             │ sns:Publish, logs:*                        │ trigger, sns │
# ├─────────────────────┼─────────────────────────────┼───────────────────────────────────────────┼──────────────┤
# │ eventbridge_role    │ eventbridge-sfn             │ states:StartExecution                     │ pipeline sfn │
# └─────────────────────┴─────────────────────────────┴───────────────────────────────────────────┴──────────────┘
#
# =============================================================================

# -----------------------------------------------------------------------------
# IAM Role - AWS Glue (para jobs del pipeline E2E)
# -----------------------------------------------------------------------------
resource "aws_iam_role" "glue_role" {
  name = "${var.project_name}-glue-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Politica gestionada de Glue Service
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# Acceso de Glue a buckets del pipeline
resource "aws_iam_role_policy" "glue_s3_access" {
  name = "${var.project_name}-glue-s3-access-${var.environment}"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          data.aws_s3_bucket.existing_e2e.arn,
          "${data.aws_s3_bucket.existing_e2e.arn}/*",
          aws_s3_bucket.landing.arn,
          "${aws_s3_bucket.landing.arn}/*",
          aws_s3_bucket.bronze.arn,
          "${aws_s3_bucket.bronze.arn}/*",
          aws_s3_bucket.gold.arn,
          "${aws_s3_bucket.gold.arn}/*",
          aws_s3_bucket.scripts.arn,
          "${aws_s3_bucket.scripts.arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# IAM Role - Lambda Pipeline Trigger
# -----------------------------------------------------------------------------
resource "aws_iam_role" "lambda_pipeline_role" {
  name = "${var.project_name}-lambda-pipeline-${var.environment}"

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

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_pipeline_basic" {
  role       = aws_iam_role.lambda_pipeline_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Permisos del pipeline trigger: invocar BNX compiler, S3, Glue, Step Functions
resource "aws_iam_role_policy" "lambda_pipeline_policy" {
  name = "${var.project_name}-lambda-pipeline-policy-${var.environment}"
  role = aws_iam_role.lambda_pipeline_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["lambda:InvokeFunction"]
        Resource = data.aws_lambda_function.existing_compiler.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
        ]
        Resource = [
          data.aws_s3_bucket.existing_e2e.arn,
          "${data.aws_s3_bucket.existing_e2e.arn}/*",
          aws_s3_bucket.landing.arn,
          "${aws_s3_bucket.landing.arn}/*",
          aws_s3_bucket.bronze.arn,
          "${aws_s3_bucket.bronze.arn}/*",
          aws_s3_bucket.gold.arn,
          "${aws_s3_bucket.gold.arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJobRuns",
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["states:StartExecution"]
        Resource = aws_sfn_state_machine.e2e_pipeline.arn
      },
      {
        Effect   = "Allow"
        Action   = ["iam:PassRole"]
        Resource = aws_iam_role.glue_role.arn
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# IAM Role - Step Functions (orquestacion del pipeline)
# -----------------------------------------------------------------------------
resource "aws_iam_role" "stepfunctions_role" {
  name = "${var.project_name}-sfn-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "stepfunctions_policy" {
  name = "${var.project_name}-sfn-policy-${var.environment}"
  role = aws_iam_role.stepfunctions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = [
          data.aws_lambda_function.existing_compiler.arn,
          aws_lambda_function.pipeline_trigger.arn,
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJobRuns",
          "glue:BatchStopJobRun",
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = aws_sns_topic.alerts.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups",
        ]
        Resource = "*"
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# IAM Role - EventBridge (schedule del pipeline)
# -----------------------------------------------------------------------------
resource "aws_iam_role" "eventbridge_role" {
  name = "${var.project_name}-eventbridge-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "eventbridge_sfn" {
  name = "${var.project_name}-eventbridge-sfn-${var.environment}"
  role = aws_iam_role.eventbridge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "states:StartExecution"
        Resource = aws_sfn_state_machine.e2e_pipeline.arn
      }
    ]
  })
}
