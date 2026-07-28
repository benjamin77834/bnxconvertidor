# -----------------------------------------------------------------------------
# BNX Convertidor — Terraform Infrastructure
#
# REGLAS:
# 1. NO interrumpir recursos existentes (Lambda bnx-compiler, Amplify, S3 e2e)
# 2. Usar data sources para referenciar lo que ya existe
# 3. Seguir convenciones de bnxlakehouse:
#    - local.common_tags en todos los recursos
#    - Naming: ${var.project_name}-<recurso>-${var.environment}
#    - Comentarios con separadores # -----
#    - Medallion architecture para datos
# 4. Pipeline de pruebas automatizado para validar codegen Spark y Glue
# -----------------------------------------------------------------------------

terraform {
  required_version = ">= 1.3.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# -----------------------------------------------------------------------------
# Locals
# -----------------------------------------------------------------------------
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# -----------------------------------------------------------------------------
# Data Sources — Recursos EXISTENTES (no se tocan, no se destruyen)
# -----------------------------------------------------------------------------

# Lambda existente: bnx-compiler (desplegada via deploy.sh)
data "aws_lambda_function" "existing_compiler" {
  function_name = "bnx-compiler"
}

# IAM Role existente (usada por Lambda y Glue manual)
data "aws_iam_role" "existing_lambda_role" {
  name = "lambdarol"
}

# S3 bucket existente para E2E tests
data "aws_s3_bucket" "existing_e2e" {
  bucket = "bnx-e2e-test"
}

# Account ID
data "aws_caller_identity" "current" {}
