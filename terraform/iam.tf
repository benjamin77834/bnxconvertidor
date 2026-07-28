# -----------------------------------------------------------------------------
# IAM — Roles y Politicas
#
# El rol "lambdarol" YA EXISTE — no se recrea.
# Solo creamos roles NUEVOS para el pipeline de pruebas.
# -----------------------------------------------------------------------------

# --- Glue Role (para jobs del pipeline) ---
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

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_policy" "glue_s3_access" {
  name        = "${var.project_name}-glue-s3-${var.environment}"
  description = "Permite a Glue leer/escribir en buckets BNX y E2E"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
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

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "glue_s3" {
  role       = aws_iam_role.glue_role.name
  policy_arn = aws_iam_policy.glue_s3_access.arn
}

# --- Lambda Role (para pipeline trigger) ---
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

resource "aws_iam_policy" "lambda_pipeline_policy" {
  name        = "${var.project_name}-lambda-pipeline-policy-${var.environment}"
  description = "Permite a Lambda del pipeline invocar BNX compiler, Glue y S3"

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
        Effect = "Allow"
        Action = ["states:StartExecution"]
        Resource = aws_sfn_state_machine.e2e_pipeline.arn
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_pipeline" {
  role       = aws_iam_role.lambda_pipeline_role.name
  policy_arn = aws_iam_policy.lambda_pipeline_policy.arn
}

# --- Step Functions Role ---
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

resource "aws_iam_policy" "stepfunctions_policy" {
  name        = "${var.project_name}-sfn-policy-${var.environment}"
  description = "Permite a Step Functions invocar Lambda, Glue y SNS"

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

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "sfn_policy" {
  role       = aws_iam_role.stepfunctions_role.name
  policy_arn = aws_iam_policy.stepfunctions_policy.arn
}

# --- EventBridge Role ---
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
