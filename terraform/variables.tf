# -----------------------------------------------------------------------------
# Variables generales (alineadas con bnxlakehouse)
# -----------------------------------------------------------------------------
variable "aws_region" {
  description = "Region de AWS"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre del proyecto (prefijo para recursos)"
  type        = string
  default     = "datalake"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# -----------------------------------------------------------------------------
# Variables de Glue (Pipeline de pruebas BNX)
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

# -----------------------------------------------------------------------------
# Variables de Alertas
# -----------------------------------------------------------------------------
variable "alert_email" {
  description = "Email para alertas"
  type        = string
  default     = "benjamin.garcia@banamex.com"
}
