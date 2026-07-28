# -----------------------------------------------------------------------------
# AWS Amplify — Frontend (YA EXISTE, no se gestiona desde aqui)
#
# La app Amplify esta desplegada manualmente y hace auto-deploy desde Git.
# Este archivo solo documenta la configuracion para referencia.
#
# App ID: d330swque2c5nj
# Branch: empresav4
# URL: https://empresav4.d330swque2c5nj.amplifyapp.com
# -----------------------------------------------------------------------------

# NO crear recursos Amplify — ya existe y funciona.
# Si necesitas un nuevo ambiente, descomenta:

# resource "aws_amplify_app" "frontend" {
#   name       = "${var.project_name}-ui-${var.environment}"
#   repository = "https://github.com/benjamin77834/bnxconvertidor"
#   build_spec = file("${path.module}/../amplify.yml")
#   tags       = local.common_tags
# }
