# Changelog — BNX Code Review

## 0.1.0
- Primera versión. Análisis de calidad estilo Sonar sobre PySpark/Python.
- Reglas: palabras reservadas / shadowing de built-ins, performance
  (.collect/.toPandas/.count), seguridad (secretos hardcodeados), smells
  (except desnudo, print, comparar con None, líneas largas, TODO/FIXME).
- Diagnósticos nativos en el editor (subrayado + panel Problems).
- Análisis automático al guardar (configurable) y comando manual.
