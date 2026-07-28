# BNX Convertidor — Terraform Infrastructure

## Que despliega

| Recurso | Descripcion |
|---------|-------------|
| **Lambda** | API del compilador BNX (Python 3.11, Function URL publica) |
| **Amplify** | Frontend React (auto-deploy desde Git) |
| **S3 (data)** | Bucket para datos raw/curated/archive con versionado y lifecycle |
| **S3 (scripts)** | Bucket para scripts Glue y paquetes Lambda |
| **S3 (reports)** | Bucket para reportes regulatorios (CNBV, UIF) |
| **Glue Job** | Job ETL template para ejecutar codigo generado por BNX |
| **Glue Catalog** | Base de datos del catalogo para metadatos |
| **IAM Roles** | Roles para Lambda, Glue y Amplify con minimo privilegio |
| **CloudWatch** | Dashboard + alarmas (errores, latencia, throttles) |
| **SNS** | Topic de alertas con suscripcion email |

## Prerequisitos

1. AWS CLI configurado con credenciales
2. Terraform >= 1.5.0
3. GitHub OAuth token (para Amplify auto-deploy)

## Uso rapido

```bash
cd terraform

# Copiar variables
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars con tus valores

# Inicializar
terraform init

# Ver que va a crear
terraform plan

# Aplicar
terraform apply

# Ver outputs (URLs, nombres, ARNs)
terraform output
```

## Estructura

```
terraform/
├── main.tf              # Provider AWS + backend
├── variables.tf         # Todas las variables configurables
├── iam.tf              # Roles y politicas (Lambda, Glue, Amplify)
├── s3.tf               # Buckets (data, scripts, reports)
├── lambda.tf           # Lambda function + Function URL + logs
├── glue.tf             # Glue jobs + Catalog database
├── amplify.tf          # Amplify app + branch
├── monitoring.tf       # CloudWatch dashboard + alarmas + SNS
├── outputs.tf          # URLs y ARNs de salida
├── terraform.tfvars.example  # Valores de ejemplo
└── README.md           # Este archivo
```

## Ambientes

Puedes tener multiples ambientes cambiando `environment`:

```bash
# Dev
terraform workspace new dev
terraform apply -var="environment=dev"

# Staging
terraform workspace new staging
terraform apply -var="environment=staging"

# Prod
terraform workspace new prod
terraform apply -var="environment=prod"
```

## Despues del apply

1. **Lambda URL** se imprime en outputs — usala en `ui/src/config.js`
2. **Amplify** hace auto-deploy al detectar push en la rama configurada
3. **Glue job** queda listo — sube scripts a `s3://bnx-convertidor-scripts-prod/glue/`
4. **Dashboard** disponible en CloudWatch para monitoreo
5. **Alertas** llegan al email configurado cuando hay errores

## Destruir

```bash
terraform destroy
```

> Los buckets S3 con datos NO se destruyen por default (tienen `lifecycle { prevent_destroy }` implicito por versionado). Vacialos primero si quieres eliminarlos.
