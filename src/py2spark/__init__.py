# py2spark — Conversor de Python (pandas y afines) a PySpark 3.
#
# Motor reutilizable por: CLI (py2spark), endpoint del portal (/py2spark) y la
# extension de VS Code. La conversion es por ANALISIS AST (no regex fragil):
# reconocemos patrones idiomaticos de pandas y los reescribimos a su equivalente
# PySpark. Lo que no se puede traducir de forma fiel se marca con un comentario
# TODO (nunca se inventa una traduccion incorrecta), igual que el convertidor
# Ab Initio->Spark de este mismo proyecto.
#
# API principal:
#   from py2spark import convert_code
#   res = convert_code(source_str)         # -> {code, warnings, unsupported, ok}
#
# Filosofia:
#   - Fidelidad > cobertura. Preferimos un TODO honesto a un job roto.
#   - El PySpark generado siempre es Python valido (compila con ast.parse).
#   - Se agrega un preambulo con SparkSession + imports de pyspark.sql.functions.

from .converter import convert_code, convert_file
from .schema import infer_input_schema

__all__ = ["convert_code", "convert_file", "infer_input_schema"]
__version__ = "0.1.0"
