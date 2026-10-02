# Framework de Modelos (MVP enterprise) integrado al convertidor BNX.
# Operacionaliza un modelo entregado por negocio: pipeline declarativo (YAML) ->
# codigo + PMML -> SHA-256 + cifrado + firma Ed25519 -> verificacion (deployable).
from .runner import run_framework, verify_manifest

__all__ = ["run_framework", "verify_manifest"]
