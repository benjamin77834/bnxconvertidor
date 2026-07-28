# ═══════════════════════════════════════════════════════════
# Variables
# ═══════════════════════════════════════════════════════════

variable "aws_region" {
  description = "Region de AWS"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Ambiente: dev, staging, prod"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Nombre del proyecto (prefijo para recursos)"
  type        = string
  default     = "bnx-convertidor"
}

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

variable "lambda_runtime" {
  description = "Runtime de Python para Lambda"
  type        = string
  default     = "python3.11"
}

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

variable "amplify_repository" {
  description = "URL del repositorio Git para Amplify"
  type        = string
  default     = "https://github.com/benjamin77834/bnxconvertidor"
}

variable "amplify_branch" {
  description = "Rama para deploy de Amplify"
  type        = string
  default     = "empresav4"
}

variable "amplify_oauth_token" {
  description = "GitHub OAuth token para Amplify (sensitive)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "alert_email" {
  description = "Email para alertas de CloudWatch"
  type        = string
  default     = "ops@bank.com"
}
