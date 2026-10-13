# Changelog — BNX Code Review

## 0.2.0
- Modelo **SonarQube/SonarLint**: cada hallazgo trae su `type`
  (BUG / CODE_SMELL / VULNERABILITY / SECURITY_HOTSPOT), su severidad Sonar y la
  clave de regla (`python:Sxxxx`). El diagnóstico se muestra como SonarLint:
  `[TYPE] mensaje` con la clave de regla en el panel Problems.
- El portal BNX tiene además una pestaña **🛡️ Calidad** (dashboard estilo
  SonarQube): Quality Gate, ratings A–E, deuda técnica y lista de issues.

## 0.1.1
- Los hallazgos ahora se ven: `minor`→Warning e `info`→Information (antes caían
  en `Hint`, que VS Code dibuja casi invisible y a veces oculta del panel
  Problems). Al analizar a mano se abre el panel **Problems** y un botón "Ver
  Problems". Los hallazgos salen subrayados en el editor y listados en Problems
  (Cmd/Ctrl+Shift+M).

## 0.1.0
- Primera versión. Análisis de calidad estilo Sonar sobre PySpark/Python.
- Reglas: palabras reservadas / shadowing de built-ins, performance
  (.collect/.toPandas/.count), seguridad (secretos hardcodeados), smells
  (except desnudo, print, comparar con None, líneas largas, TODO/FIXME).
- Diagnósticos nativos en el editor (subrayado + panel Problems).
- Análisis automático al guardar (configurable) y comando manual.
