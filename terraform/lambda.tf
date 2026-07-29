# -----------------------------------------------------------------------------
# Lambda — BNX Compiler en DataLab
# Se expone via API Gateway (no Function URL, bloqueada por SCP)
# -----------------------------------------------------------------------------

# La Lambda ya fue creada manualmente:
#   Name: datalake-bnx-compiler-dev
#   Role: datalake-lambda-role-dev
#   Runtime: python3.11
#   Handler: lambda.handler.handler
#   Memory: 512MB, Timeout: 60s
#
# Para actualizar el codigo:
#   cd bnxconvertidor
#   zip -r lambda_package.zip lambda/handler.py src/ main.py -x "src/__pycache__/*"
#   aws lambda update-function-code --function-name datalake-bnx-compiler-dev \
#     --zip-file fileb://lambda_package.zip --profile datalab --region us-east-1

# Referencia a la Lambda existente
data "aws_lambda_function" "bnx_compiler" {
  function_name = "datalake-bnx-compiler-dev"
}
