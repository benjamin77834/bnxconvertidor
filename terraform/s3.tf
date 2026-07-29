# -----------------------------------------------------------------------------
# S3 — Bucket para scripts y datos de BNX Convertidor
# Reutiliza el ecosistema del lakehouse, solo crea un bucket de scripts
# -----------------------------------------------------------------------------

# Bucket para scripts generados por BNX (spark_job.py, glue_job.py)
resource "aws_s3_bucket" "bnx_scripts" {
  bucket = "${var.project_name}-bnx-scripts-${var.environment}"
  tags   = local.common_tags
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bnx_scripts_encryption" {
  bucket = aws_s3_bucket.bnx_scripts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "bnx_scripts_public" {
  bucket                  = aws_s3_bucket.bnx_scripts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "bnx_scripts_versioning" {
  bucket = aws_s3_bucket.bnx_scripts.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Prefijos iniciales
resource "aws_s3_object" "scripts_spark" {
  bucket  = aws_s3_bucket.bnx_scripts.id
  key     = "spark/"
  content = ""
}

resource "aws_s3_object" "scripts_glue" {
  bucket  = aws_s3_bucket.bnx_scripts.id
  key     = "glue/"
  content = ""
}

resource "aws_s3_object" "scripts_temp" {
  bucket  = aws_s3_bucket.bnx_scripts.id
  key     = "temp/"
  content = ""
}

resource "aws_s3_object" "test_data" {
  bucket  = aws_s3_bucket.bnx_scripts.id
  key     = "test-data/orders.csv"
  content = <<-EOF
id,nombre,monto
1,juan perez,150.50
2,maria gomez,300.5
3,carlos lopez,75.25
4,ana martinez,200.0
5,luis rodriguez,120.25
6,juan perez,50.0
7,maria gomez,100.0
EOF
}
