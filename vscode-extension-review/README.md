# BNX Code Review (estilo Sonar)

Analiza la calidad de tu código PySpark/Python directamente en VS Code y marca
los hallazgos como **diagnósticos nativos** (subrayado en el editor + panel
Problems). Usa el mismo motor del portal BNX (`/analyze`), sin necesidad de
Python en tu máquina.

## Qué detecta

- **Palabras reservadas / shadowing de built-ins** (estilo SonarLint): variables,
  parámetros o funciones que se llaman como un built-in de Python (`list`, `str`,
  `sum`, `filter`, `input`, ...) o como un soft keyword (`match`, `type`, ...).
- **Performance (PySpark)**: `.collect()`, `.toPandas()`, `.count()` repetido.
- **Seguridad**: credenciales/secretos hardcodeados, password JDBC en claro.
- **Code smells**: `except:` desnudo, `except` con `pass`, comparar con `None`
  usando `==`, `print()` en producción, funciones muy largas, líneas largas,
  TODO/FIXME.

## Uso

1. Abre un archivo `.py` (PySpark o Python).
2. Clic derecho → **BNX Review: Analizar archivo (calidad)**, o guarda el archivo
   (análisis automático al guardar, configurable).
3. Los hallazgos aparecen subrayados y en el panel **Problems**.

## Configuración

- `bnxReview.serverUrl` (por defecto `http://localhost:8081`): URL del portal BNX.
- `bnxReview.analyzeOnSave` (por defecto `true`): analizar al guardar.

El dato real (tu código) se envía al portal BNX configurado para analizarse; el
motor no modifica tu código, solo devuelve recomendaciones.
