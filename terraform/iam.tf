# -----------------------------------------------------------------------------
# IAM — Politica adicional para el Glue Role existente
# Permite acceso al bucket de scripts BNX
# El rol datalake-glue-role-dev YA EXISTE (del lakehouse)
# -----------------------------------------------------------------------------

resource "aws_iam_role_policy" "glue_bnx_access" {
  name = "${var.project_name}-glue-bnx-access-${var.environment}"
  role = data.aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.bnx_scripts.arn,
          "${aws_s3_bucket.bnx_scripts.arn}/*",
        ]
      }
    ]
  })
}
