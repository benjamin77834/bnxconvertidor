# BNX Convertidor — Terraform Infrastructure

## Principio clave: NO interrumpir lo existente

Este Terraform usa **data sources** para referenciar los recursos que ya estan en produccion (Lambda, Amplify, S3 bucket, IAM role). No los recrea, no los modifica, no los destruye.

| Recurso | Estado | Como se maneja |
|---------|--------|----------------|
| Lambda `bnx-compiler` | YA EXISTE | `data.aws_lambda_function` (solo referencia) |
| Amplify app | YA EXISTE | Comentado (no se toca) |
| S3 `bnx-e2e-test` | YA EXISTE | `data.aws_s3_bucket` (solo referencia) |
| IAM `lambdarol` | YA EXISTE | `data.aws_iam_role` (solo referencia) |

## Que crea (NUEVO)

| Recurso | Descripcion |
|---------|-------------|
| **S3 (data)** | Bucket para datos raw/curated/archive con lifecycle |
| **S3 (scripts)** | Bucket para scripts Glue y paquetes |
| **S3 (reports)** | Bucket para reportes regulatorios |
| **Glue Job (spark)** | Ejecuta codigo generado con target=spark |
| **Glue Job (glue)** | Ejecuta codigo generado con target=glue |
| **Glue Job (validate)** | Valida output Spark vs Glue vs Expected |
| **Step Functions** | Pipeline E2E completo (compile → run → validate → notify) |
| **EventBridge** | Ejecucion diaria programada (opcional) |
| **IAM Roles** | Nuevos roles para Glue, Step Functions, EventBridge |
| **CloudWatch Dashboard** | Metricas de Lambda + Pipeline + Glue |
| **CloudWatch Alarms** | Errores Lambda, duracion, throttles, pipeline failures |
| **SNS Topic** | Alertas por email |

## Pipeline E2E

El pipeline automatiza la prueba completa de conversion:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ BNX Lambda  │────>│  Glue Jobs  │────>│  Validate   │
│ (compile)   │     │ (spark+glue)│     │  (compare)  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                        ┌──────┴──────┐
                                        │  SNS Alert  │
                                        │ (pass/fail) │
                                        └─────────────┘
```

1. **Compila** el grafo .mp/.xfr con BNX Lambda (target=spark y target=glue)
2. **Ejecuta** ambos scripts en Glue (en paralelo)
3. **Valida** que el output sea igual entre Spark y Glue
4. **Notifica** el resultado via SNS

## Uso rapido

```bash
cd terraform

# Copiar variables
cp terraform.tfvars.example terraform.tfvars

# Inicializar
terraform init

# Ver que va a crear (NO destruye nada existente)
terraform plan

# Aplicar
terraform apply

# Ver outputs
terraform output
```

## Ejecutar pipeline manualmente

### Via Step Functions (despues de terraform apply)
```bash
aws stepfunctions start-execution \
  --state-machine-arn $(terraform output -raw pipeline_arn) \
  --region us-east-1
```

### Via script directo (sin Terraform)
```bash
./scripts/run_pipeline.sh --graph ../e2e/test.mp --xfr ../e2e/test.xfr
```

## Habilitar ejecucion diaria

```bash
terraform apply -var="enable_daily_pipeline=true"
```

Esto activa el EventBridge rule que ejecuta el pipeline a las 6am UTC diariamente.

## Estructura

```
terraform/
├── main.tf              # Provider + data sources (recursos existentes)
├── variables.tf         # Variables configurables
├── iam.tf              # Roles NUEVOS (Glue, StepFn, EventBridge)
├── s3.tf               # Buckets NUEVOS (data, scripts, reports)
├── lambda.tf           # Solo log group (Lambda YA EXISTE)
├── amplify.tf          # Comentado (Amplify YA EXISTE)
├── glue.tf             # Glue jobs para pipeline E2E
├── pipeline.tf         # Step Functions + EventBridge
├── monitoring.tf       # CloudWatch dashboard + alarmas + SNS
├── outputs.tf          # URLs, ARNs, comandos utiles
├── terraform.tfvars.example
├── README.md
└── scripts/
    ├── run_pipeline.sh     # Ejecutar pipeline manualmente
    └── validate_output.py  # Script de validacion (Glue Python Shell)
```

## Destruir (solo lo nuevo)

```bash
terraform destroy
```

Esto SOLO destruye los recursos creados por Terraform. La Lambda, Amplify y bucket E2E existente NO se tocan.
