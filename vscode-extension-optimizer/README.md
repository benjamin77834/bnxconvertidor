# BNX PySpark Optimizer (extensión VS Code)

Optimiza código **PySpark** por reglas de performance, sin IA, usando el mismo
motor del portal BNX (`/optimize`). No requiere Python instalado en tu máquina:
la extensión envía el código al portal y recibe el PySpark optimizado.

## Qué optimiza
- **Cache** de DataFrames reusados cuyo linaje es costoso (join, groupBy/agg,
  dropDuplicates, Window) — evita recomputar el mismo shuffle N veces.
- **Broadcast join** cuando el lado derecho es un lookup/catálogo pequeño.
- **Coalesce** en la escritura para reducir el número de archivos de salida.

No cambia la semántica del job: aplica patrones estándar de Spark.

## Uso
1. Asegúrate de que el portal BNX esté corriendo (por defecto `http://localhost:8081`).
2. Abre un archivo PySpark (`.py`).
3. Click derecho → **PySpark Optimizer: Optimizar archivo** (o *Optimizar selección*).
   También desde la paleta de comandos (Cmd/Ctrl+Shift+P).
4. El PySpark optimizado se abre en un editor nuevo (configurable).

## Configuración
- `psparkOptimizer.serverUrl` — URL del portal BNX (default `http://localhost:8081`).
- `psparkOptimizer.openInNewEditor` — abrir el resultado en editor nuevo (default `true`).

## Nota
La optimización aplica al target **PySpark**. Si el código es de AWS Glue
(`GlueContext`/`awsglue`), el portal responde que debe compilarse como `spark`.
