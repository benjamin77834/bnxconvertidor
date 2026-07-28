# -----------------------------------------------------------------------------
# Lambda — Pipeline Trigger
#
# Esta Lambda se dispara cuando llega un .mp al bucket Landing.
# 1. Invoca BNX Compiler (Lambda existente) para generar spark y glue code
# 2. Guarda los scripts generados en Bronze
# 3. Inicia el Step Functions pipeline
#
# La Lambda "bnx-compiler" existente NO se toca.
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "pipeline_trigger" {
  function_name = "${var.project_name}-pipeline-trigger-${var.environment}"
  role          = aws_iam_role.lambda_pipeline_role.arn
  handler       = "index.handler"
  runtime       = "python3.12"
  timeout       = 120
  memory_size   = 256

  filename         = data.archive_file.pipeline_trigger.output_path
  source_code_hash = data.archive_file.pipeline_trigger.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT       = var.environment
      BNX_COMPILER_NAME = data.aws_lambda_function.existing_compiler.function_name
      BRONZE_BUCKET     = aws_s3_bucket.bronze.bucket
      SCRIPTS_BUCKET    = aws_s3_bucket.scripts.bucket
      E2E_BUCKET        = data.aws_s3_bucket.existing_e2e.id
      PIPELINE_ARN      = aws_sfn_state_machine.e2e_pipeline.arn
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_permission" "allow_s3_landing" {
  statement_id  = "AllowS3InvokeLambda"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pipeline_trigger.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.landing.arn
}

data "archive_file" "pipeline_trigger" {
  type        = "zip"
  output_path = "${path.module}/.build/pipeline_trigger.zip"

  source {
    content  = <<-EOF
import json
import boto3
import os
import urllib.parse

s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')
sfn = boto3.client('stepfunctions')

def handler(event, context):
    """
    Pipeline Trigger: Cuando llega un .mp al Landing bucket:
    1. Lee el archivo .mp (y .xfr si existe)
    2. Invoca BNX Compiler para generar codigo Spark y Glue
    3. Guarda los scripts en Bronze bucket
    4. Inicia el pipeline Step Functions para ejecutar y validar
    """
    compiler_name = os.environ['BNX_COMPILER_NAME']
    bronze_bucket = os.environ['BRONZE_BUCKET']
    scripts_bucket = os.environ['SCRIPTS_BUCKET']
    pipeline_arn = os.environ['PIPELINE_ARN']

    for record in event.get('Records', []):
        source_bucket = record['s3']['bucket']['name']
        source_key = urllib.parse.unquote_plus(record['s3']['object']['key'])

        if not source_key.endswith('.mp'):
            continue

        print(f"[BNX Pipeline] New graph detected: s3://{source_bucket}/{source_key}")

        # Leer el .mp
        mp_obj = s3.get_object(Bucket=source_bucket, Key=source_key)
        mp_content = mp_obj['Body'].read().decode('utf-8')

        # Buscar .xfr con el mismo nombre
        xfr_key = source_key.replace('.mp', '.xfr')
        xfr_content = ''
        try:
            xfr_obj = s3.get_object(Bucket=source_bucket, Key=xfr_key)
            xfr_content = xfr_obj['Body'].read().decode('utf-8')
            print(f"  Found XFR: {xfr_key}")
        except s3.exceptions.NoSuchKey:
            print(f"  No XFR found (optional)")

        # Compilar para Spark
        spark_payload = {
            'action': 'compile_inline',
            'mp_content': mp_content,
            'xfr_content': xfr_content,
            'target': 'spark'
        }

        spark_response = lambda_client.invoke(
            FunctionName=compiler_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(spark_payload)
        )
        spark_result = json.loads(spark_response['Payload'].read())
        spark_code = spark_result.get('code', '')

        # Compilar para Glue
        glue_payload = {
            'action': 'compile_inline',
            'mp_content': mp_content,
            'xfr_content': xfr_content,
            'target': 'glue'
        }

        glue_response = lambda_client.invoke(
            FunctionName=compiler_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(glue_payload)
        )
        glue_result = json.loads(glue_response['Payload'].read())
        glue_code = glue_result.get('code', '')

        # Guardar en Bronze
        graph_name = source_key.split('/')[-1].replace('.mp', '')
        from datetime import datetime
        date_prefix = datetime.utcnow().strftime('%Y/%m/%d')

        if spark_code:
            s3.put_object(
                Bucket=bronze_bucket,
                Key=f"{date_prefix}/{graph_name}/spark_job.py",
                Body=spark_code.encode('utf-8')
            )
            # Tambien copiar a scripts para ejecucion
            s3.put_object(
                Bucket=scripts_bucket,
                Key=f"spark/{graph_name}_spark.py",
                Body=spark_code.encode('utf-8')
            )
            print(f"  Spark code generated ({len(spark_code)} bytes)")

        if glue_code:
            s3.put_object(
                Bucket=bronze_bucket,
                Key=f"{date_prefix}/{graph_name}/glue_job.py",
                Body=glue_code.encode('utf-8')
            )
            s3.put_object(
                Bucket=scripts_bucket,
                Key=f"glue/{graph_name}_glue.py",
                Body=glue_code.encode('utf-8')
            )
            print(f"  Glue code generated ({len(glue_code)} bytes)")

        # Iniciar pipeline E2E
        if spark_code and glue_code:
            sfn.start_execution(
                stateMachineArn=pipeline_arn,
                input=json.dumps({
                    'graph_name': graph_name,
                    'source_key': source_key,
                    'spark_script': f"s3://{scripts_bucket}/spark/{graph_name}_spark.py",
                    'glue_script': f"s3://{scripts_bucket}/glue/{graph_name}_glue.py",
                })
            )
            print(f"  Pipeline started for {graph_name}")
        else:
            errors = spark_result.get('errors', []) + glue_result.get('errors', [])
            print(f"  Compilation failed: {errors}")

    return {'statusCode': 200, 'body': json.dumps('OK')}
    EOF
    filename = "index.py"
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Log Group para Lambda del pipeline
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "pipeline_trigger_logs" {
  name              = "/aws/lambda/${aws_lambda_function.pipeline_trigger.function_name}"
  retention_in_days = 14
  tags              = local.common_tags
}

# Log group para la Lambda existente (si no existe, se crea)
resource "aws_cloudwatch_log_group" "compiler_logs" {
  name              = "/aws/lambda/${data.aws_lambda_function.existing_compiler.function_name}"
  retention_in_days = 30
  tags              = local.common_tags

  lifecycle {
    ignore_changes = [retention_in_days]
  }
}
