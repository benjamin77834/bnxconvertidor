# -----------------------------------------------------------------------------
# S3 - Buckets para BNX Convertidor
# Sigue Medallion Architecture de bnxlakehouse:
#   Landing (grafos crudos) → Bronze (compilados) → Gold (ejecutados/validados)
# -----------------------------------------------------------------------------

# Landing: Grafos .mp/.xfr/.dml originales del banco
resource "aws_s3_bucket" "landing" {
  bucket = "${var.project_name}-landing-${var.environment}"
  tags   = local.common_tags
}

# Bronze: Codigo generado por BNX (spark_job.py, glue_job.py)
resource "aws_s3_bucket" "bronze" {
  bucket = "${var.project_name}-bronze-${var.environment}"
  tags   = local.common_tags
}

# Gold: Output de ejecucion validado (resultados correctos)
resource "aws_s3_bucket" "gold" {
  bucket = "${var.project_name}-gold-${var.environment}"
  tags   = local.common_tags
}

# Scripts: Glue scripts activos para el pipeline
resource "aws_s3_bucket" "scripts" {
  bucket = "${var.project_name}-scripts-${var.environment}"
  tags   = local.common_tags
}

# Reports: Reportes regulatorios generados
resource "aws_s3_bucket" "reports" {
  bucket = "${var.project_name}-reports-${var.environment}"
  tags   = local.common_tags
}

# -----------------------------------------------------------------------------
# Encriptacion server-side para todos los buckets
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_server_side_encryption_configuration" "landing_encryption" {
  bucket = aws_s3_bucket.landing.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bronze_encryption" {
  bucket = aws_s3_bucket.bronze.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "gold_encryption" {
  bucket = aws_s3_bucket.gold.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "scripts_encryption" {
  bucket = aws_s3_bucket.scripts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "reports_encryption" {
  bucket = aws_s3_bucket.reports.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# -----------------------------------------------------------------------------
# Bloquear acceso publico en todos los buckets
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_public_access_block" "landing_public_access" {
  bucket                  = aws_s3_bucket.landing.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "bronze_public_access" {
  bucket                  = aws_s3_bucket.bronze.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "gold_public_access" {
  bucket                  = aws_s3_bucket.gold.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "scripts_public_access" {
  bucket                  = aws_s3_bucket.scripts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "reports_public_access" {
  bucket                  = aws_s3_bucket.reports.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -----------------------------------------------------------------------------
# Versionado en Landing y Bronze (trazabilidad de grafos y codigo)
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_versioning" "landing_versioning" {
  bucket = aws_s3_bucket.landing.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "bronze_versioning" {
  bucket = aws_s3_bucket.bronze.id
  versioning_configuration {
    status = "Enabled"
  }
}

# -----------------------------------------------------------------------------
# Lifecycle: mover grafos viejos a Glacier despues de 90 dias
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_lifecycle_configuration" "landing_lifecycle" {
  bucket = aws_s3_bucket.landing.id

  rule {
    id     = "archive-old-graphs"
    status = "Enabled"

    filter {
      prefix = ""
    }

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }
}

# -----------------------------------------------------------------------------
# Notificacion S3: cuando llega un grafo al landing, dispara Lambda pipeline
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_notification" "landing_notification" {
  bucket = aws_s3_bucket.landing.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.pipeline_trigger.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".mp"
  }

  depends_on = [aws_lambda_permission.allow_s3_landing]
}
