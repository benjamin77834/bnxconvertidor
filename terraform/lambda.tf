# ═══════════════════════════════════════════════════════════
# Lambda — API Backend (BNX Compiler)
# ═══════════════════════════════════════════════════════════

# --- Lambda Function ---
resource "aws_lambda_function" "compiler" {
  function_name = "${var.project_name}-compiler"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda.handler.handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT  = var.environment
      DATA_BUCKET  = aws_s3_bucket.data_bucket.id
      SCRIPTS_BUCKET = aws_s3_bucket.scripts_bucket.id
    }
  }

  tags = {
    Component = "API"
  }
}

# --- Package Lambda code ---
data "archive_file" "lambda_package" {
  type        = "zip"
  output_path = "${path.module}/.build/lambda_package.zip"

  source {
    content  = file("${path.module}/../lambda/handler.py")
    filename = "lambda/handler.py"
  }

  # Include src/ directory
  dynamic "source" {
    for_each = fileset("${path.module}/../src", "**/*.py")
    content {
      content  = file("${path.module}/../src/${source.value}")
      filename = "src/${source.value}"
    }
  }
}

# --- Lambda Function URL (public API) ---
resource "aws_lambda_function_url" "compiler_url" {
  function_name      = aws_lambda_function.compiler.function_name
  authorization_type = "NONE"

  cors {
    allow_origins  = ["*"]
    allow_methods  = ["POST", "GET", "OPTIONS"]
    allow_headers  = ["Content-Type", "Authorization"]
    max_age        = 86400
  }
}

# --- Lambda Permission for Function URL ---
resource "aws_lambda_permission" "function_url" {
  statement_id           = "AllowFunctionURLInvoke"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.compiler.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

# --- CloudWatch Log Group ---
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.compiler.function_name}"
  retention_in_days = 30
}
