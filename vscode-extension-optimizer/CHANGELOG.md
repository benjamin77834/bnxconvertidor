# Changelog

## 0.1.0
- Primera versión. Comandos "Optimizar selección" y "Optimizar archivo" que
  llaman al endpoint `/optimize` del portal BNX (cache / broadcast join /
  coalesce). Resultado en editor nuevo o reemplazando la selección.

## 0.2.0
- OFFLINE total: el motor de optimización ahora corre dentro de la extensión
  (`optimizer.js`, port de `src/perf_optimizer.py`). Ya NO llama al endpoint
  `/optimize` ni requiere el portal BNX corriendo ni Python en la máquina.
- Eliminada la configuración `psparkOptimizer.serverUrl` (ya no aplica).
- Mismas reglas y resultados que el motor Python (cache / broadcast / coalesce
  + reducción de código).
