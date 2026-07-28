# ═══════════════════════════════════════════════════════════
# BNX Convertidor — Terraform Infrastructure
# Despliega TODOS los artefactos de la plataforma en AWS
# ═══════════════════════════════════════════════════════════

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend remoto (opcional — descomentar para equipo)
  # backend "s3" {
  #   bucket = "bnx-terraform-state"
  #   key    = "bnx-convertidor/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "BNX-Convertidor"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Team        = "Data-Engineering"
    }
  }
}
