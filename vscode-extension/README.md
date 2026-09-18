# py2spark — Python a PySpark 3 (extensión de VS Code)

Convierte código Python (pandas) a **PySpark 3** desde el editor. Usa el mismo
motor `py2spark` que la CLI y el portal BNX (endpoint `/py2spark`).

## Comandos

- **py2spark: Convertir selección a PySpark** — convierte el texto seleccionado
  (o todo el documento si no hay selección).
- **py2spark: Convertir archivo Python a PySpark** — convierte el archivo entero
  y abre el resultado en un editor nuevo.

Ambos aparecen también en el menú contextual del editor (clic derecho) cuando el
lenguaje es Python.

## Configuración

- `py2spark.serverUrl` (default `http://localhost:8081`): URL base del portal BNX
  que expone `/py2spark`.
- `py2spark.openInNewEditor` (default `true`): abrir el PySpark generado en un
  editor nuevo en vez de reemplazar la selección.

## Qué traduce

pandas → PySpark: `read_csv/read_parquet`, filtros booleanos, `groupby/agg`,
`merge` → `join`, `sort_values` → `orderBy`, selección/asignación de columnas,
`rename/drop/head`, `to_csv/to_parquet`, `len(df)` → `count()`, entre otros.

Lo que no es traducible 1:1 (p. ej. `apply` con lambda, `iterrows`) se marca con
`# TODO py2spark:` para revisión manual, sin romper el resto del código.

## Requisitos

El portal BNX debe estar accesible en `py2spark.serverUrl`. No requiere Python
instalado en la máquina: la conversión ocurre en el servidor.
