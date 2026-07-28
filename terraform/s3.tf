# ═══════════════════════════════════════════════════════════
# S3 Buckets — Almacenamiento
# ═══════════════════════════════════════════════════════════

# --- Bucket para datos (input/output de pipelines) ---
resource "aws_s3_bucket" "data_bucket" {
  bucket = "${var.project_name}-data-${var.environment}"
}

resource "aws_s3_bucket_versioning" "data_versioning" {
  bucket = aws_s3_bucket.data_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_encryption" {
  bucket = aws_s3_bucket.data_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data_public_block" {
  bucket = aws_s3_bucket.data_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lifecycle" {
  bucket = aws_s3_bucket.data_bucket.id

  rule {
    id     = "archive-old-data"
    status = "Enabled"

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

# --- Bucket para scripts (Glue jobs, Lambda packages) ---
resource "aws_s3_bucket" "scripts_bucket" {
  bucket = "${var.project_name}-scripts-${var.environment}"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "scripts_encryption" {
  bucket = aws_s3_bucket.scripts_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "scripts_public_block" {
  bucket = aws_s3_bucket.scripts_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- Bucket para reportes (regulatorio, CNBV, UIF) ---
resource "aws_s3_bucket" "reports_bucket" {
  bucket = "${var.project_name}-reports-${var.environment}"
}

resource "aws_s3_bucket_versioning" "reports_versioning" {
  bucket = aws_s3_bucket.reports_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "reports_encryption" {
  bucket = aws_s3_bucket.reports_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "reports_public_block" {
  bucket = aws_s3_bucket.reports_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- Prefijos iniciales (estructura de carpetas) ---
resource "aws_s3_object" "data_raw" {
  bucket  = aws_s3_bucket.data_bucket.id
  key     = "raw/"
  content = ""
}

resource "aws_s3_object" "data_curated" {
  bucket  = aws_s3_bucket.data_bucket.id
  key     = "curated/"
  content = ""
}

resource "aws_s3_object" "data_archive" {
  bucket  = aws_s3_bucket.data_bucket.id
  key     = "archive/"
  content = ""
}

resource "aws_s3_object" "scripts_glue" {
  bucket  = aws_s3_bucket.scripts_bucket.id
  key     = "glue/"
  content = ""
}

resource "aws_s3_object" "scripts_lambda" {
  bucket  = aws_s3_bucket.scripts_bucket.id
  key     = "lambda/"
  content = ""
}

resource "aws_s3_object" "scripts_temp" {
  bucket  = aws_s3_bucket.scripts_bucket.id
  key     = "temp/"
  content = ""
}
