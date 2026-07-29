# -----------------------------------------------------------------------------
# API Gateway — Expone la Lambda BNX Compiler
# Necesario porque Function URL esta bloqueada por SCP del banco
#
# API ID: 6lewkixco1
# Stage: prod
# URL: https://6lewkixco1.execute-api.us-east-1.amazonaws.com/prod
# -----------------------------------------------------------------------------

# Referencia al API Gateway ya creado
# (creado manualmente, se puede importar con terraform import)
#
# Para importar al state:
#   terraform import aws_api_gateway_rest_api.bnx 6lewkixco1
#
# resource "aws_api_gateway_rest_api" "bnx" {
#   name        = "datalake-bnx-api-dev"
#   description = "BNX Convertidor API"
#   endpoint_configuration {
#     types = ["REGIONAL"]
#   }
#   tags = local.common_tags
# }
