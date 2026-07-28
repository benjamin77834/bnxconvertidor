# ═══════════════════════════════════════════════════════════
# AWS Amplify — Frontend (React App)
# ═══════════════════════════════════════════════════════════

resource "aws_amplify_app" "frontend" {
  name       = "${var.project_name}-ui"
  repository = var.amplify_repository

  # OAuth token para acceso al repo (si se provee)
  access_token = var.amplify_oauth_token != "" ? var.amplify_oauth_token : null

  iam_service_role_arn = aws_iam_role.amplify_role.arn

  build_spec = <<-EOT
    version: 1
    applications:
      - frontend:
          phases:
            preBuild:
              commands:
                - cd ui
                - npm ci
            build:
              commands:
                - npm run build
          artifacts:
            baseDirectory: ui/dist
            files:
              - '**/*'
          cache:
            paths:
              - ui/node_modules/**/*
        appRoot: .
  EOT

  environment_variables = {
    VITE_API_URL = aws_lambda_function_url.compiler_url.function_url
    _LIVE_UPDATES = jsonencode([
      {
        pkg     = "node"
        type    = "nvm"
        version = "18"
      }
    ])
  }

  custom_rule {
    source = "/<*>"
    status = "404-200"
    target = "/index.html"
  }

  tags = {
    Component = "Frontend"
  }
}

# --- Branch de produccion ---
resource "aws_amplify_branch" "main" {
  app_id      = aws_amplify_app.frontend.id
  branch_name = var.amplify_branch

  framework = "React"
  stage     = var.environment == "prod" ? "PRODUCTION" : "DEVELOPMENT"

  enable_auto_build = true

  environment_variables = {
    VITE_API_URL = aws_lambda_function_url.compiler_url.function_url
  }
}
