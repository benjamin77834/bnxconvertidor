# -----------------------------------------------------------------------------
# BNX Convertidor — Terraform en DataLab (cuenta 107094296911)
#
# Despliega el pipeline E2E de BNX Convertidor dentro de la plataforma
# de datos fundacional (bnxlakehouse) ya desplegada.
#
# REGLAS:
# 1. Usar profile "datalab" (cuenta 107094296911)
# 2. Reutilizar recursos existentes del lakehouse (roles, catalog, buckets)
# 3. Solo crear lo nuevo: Glue jobs, Lambda trigger, Step Functions
# 4. Seguir naming: datalake-<recurso>-<env> (como el lakehouse)
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
  region  = var.aws_region
  profile = "datalab"
}

# -----------------------------------------------------------------------------
# Locals
# -----------------------------------------------------------------------------
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "bnx-convertidor"
  }
}

# -----------------------------------------------------------------------------
# Data Sources — Recursos del Lakehouse YA DESPLEGADOS
# -----------------------------------------------------------------------------

# Glue Role existente del lakehouse
data "aws_iam_role" "glue_role" {
  name = "datalake-glue-role-${var.environment}"
}

# Lambda Role existente del lakehouse
data "aws_iam_role" "lambda_role" {
  name = "datalake-lambda-role-${var.environment}"
}

# Glue Catalog existente (referencia por nombre, no data source)
locals {
  glue_catalog_db = "datalake_${var.environment}"
}

# Account ID
data "aws_caller_identity" "current" {}
