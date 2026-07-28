# -----------------------------------------------------------------------------
# Variables generales
# -----------------------------------------------------------------------------
variable "aws_region" {
  description = "Region de AWS"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre del proyecto (se usa como prefijo en los recursos)"
  type        = string
  default     = "bnx-convertidor"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# -----------------------------------------------------------------------------
# Variables de Lambda
# -----------------------------------------------------------------------------
variable "lambda_memory_size" {
  description = "Memoria de la Lambda en MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout de la Lambda en segundos"
  type        = number
  default     = 60
}

# -----------------------------------------------------------------------------
# Variables de Glue (Pipeline de pruebas)
# -----------------------------------------------------------------------------
variable "glue_worker_type" {
  description = "Tipo de worker para Glue jobs"
  type        = string
  default     = "G.1X"
}

variable "glue_num_workers" {
  description = "Numero de workers para Glue jobs"
  type        = number
  default     = 2
}

# -----------------------------------------------------------------------------
# Variables de Pipeline
# -----------------------------------------------------------------------------
variable "enable_daily_pipeline" {
  description = "Habilitar ejecucion diaria del pipeline E2E (true/false)"
  type        = bool
  default     = false
}

variable "pipeline_schedule" {
  description = "Cron para ejecucion programada del pipeline (UTC)"
  type        = string
  default     = "cron(0 6 * * ? *)"
}

# -----------------------------------------------------------------------------
# Variables de Alertas
# -----------------------------------------------------------------------------
variable "alert_email" {
  description = "Email para alertas de CloudWatch y SNS"
  type        = string
  default     = "ops@bank.com"
}

# -----------------------------------------------------------------------------
# Variables de Control de Costos
# -----------------------------------------------------------------------------
variable "budget_monthly" {
  description = "Presupuesto mensual total en USD para BNX"
  type        = string
  default     = "500"
}
