# BNX Convertidor — Plan de Trabajo 3 Meses
## SDLC Bancario + SonarQube + Produccion

---

## Contexto

BNX Convertidor debe pasar por el ciclo SDLC bancario completo antes de entrar a produccion.
Esto incluye: code quality (SonarQube), seguridad (SAST/DAST), pruebas formales, 
documentacion de arquitectura, y aprobaciones de cambio (CAB).

---

## MES 1 — Estabilizacion + Code Quality

### Semana 1-2: Parser GDE Nativo (en curso)
- [ ] Completar parser de formato serializado Ab Initio (.mp nativo GDE)
- [ ] Resolver mapeo de edges (ports -> flows -> vertices)
- [ ] Validar con 3+ grafos reales del banco (diferentes complejidades)
- [ ] Generar job.py con edges correctos y DAG completo
- [ ] Documentar limitaciones del parser (que formatos soporta vs no)

### Semana 2-3: SonarQube Compliance
- [ ] Configurar SonarQube scanner en el proyecto
- [ ] Crear `sonar-project.properties`
- [ ] Resolver issues de severidad Critical/Blocker
- [ ] Eliminar code smells (duplicacion, complejidad ciclomatica)
- [ ] Cobertura de tests minima 60% (requerimiento banco)
- [ ] Configurar quality gates: 0 bugs, 0 vulnerabilities, <5% duplication
- [ ] Integrar scan en pipeline CI/CD (pre-merge)

### Semana 3-4: Testing Formal
- [ ] Unit tests para cada parser (mp, xfr, dml, pset, plan, cobol)
- [ ] Unit tests para cada codegen (glue, spark, flink, airflow, terraform)
- [ ] Integration tests: .mp real -> job.py -> validacion de output
- [ ] Test con grafos del banco (sanitizados)
- [ ] Documentar casos de prueba en formato banco (Test Plan)
- [ ] Configurar pytest + coverage report

---

## MES 2 — Seguridad + SDLC Bancario

### Semana 5-6: Seguridad (SAST/DAST)
- [ ] SAST scan (Checkmarx/Fortify/SonarQube Security)
- [ ] Remediar vulnerabilidades encontradas
- [ ] Validar que no hay secrets hardcodeados (ya limpiamos ASCII)
- [ ] Input validation en todos los parsers (archivos malformados)
- [ ] Sanitizacion de output (no inyeccion de codigo en job.py generado)
- [ ] Dependency check (pip audit / safety) — sin CVEs
- [ ] Documentar threat model basico

### Semana 6-7: Documentacion SDLC
- [ ] Documento de Arquitectura (SAD) — formato banco
- [ ] Diagrama de componentes (ya tenemos en ArchitecturePage)
- [ ] Diagrama de flujo de datos (DFD)
- [ ] Documento de Diseno Detallado (DDD)
- [ ] Runbook operativo (como ejecutar, troubleshooting)
- [ ] Documento de Rollback
- [ ] Matriz de riesgos

### Semana 7-8: CI/CD Pipeline Bancario
- [ ] Pipeline en herramienta del banco (Jenkins/GitLab CI/CodePipeline)
- [ ] Stages: lint -> test -> sonar -> security -> build -> deploy
- [ ] Artefacto versionado (tag + changelog)
- [ ] Deploy a ambiente DEV automatico
- [ ] Deploy a QA con aprobacion manual
- [ ] Configurar branch protection (no push directo a main)

---

## MES 3 — QA + CAB + Produccion

### Semana 9-10: QA Formal
- [ ] Pruebas en ambiente QA del banco
- [ ] Pruebas de regresion con grafos reales
- [ ] Pruebas de performance (40K jobs estimation validation)
- [ ] Pruebas de stress (archivos .mp grandes, >10K lineas)
- [ ] UAT con equipo de datos (validar output vs Ab Initio original)
- [ ] Sign-off de QA

### Semana 10-11: CAB (Change Advisory Board)
- [ ] RFC (Request for Change) documentado
- [ ] Impacto analisis
- [ ] Plan de implementacion
- [ ] Plan de rollback
- [ ] Ventana de cambio aprobada
- [ ] Comunicacion a stakeholders

### Semana 11-12: Deploy Produccion + Operacion
- [ ] Deploy a PROD (Lambda + Amplify)
- [ ] Smoke tests post-deploy
- [ ] Monitoreo CloudWatch (errores, latencia, invocaciones)
- [ ] Alertas SNS configuradas
- [ ] Handover a equipo de operaciones
- [ ] Documentacion de soporte L1/L2/L3
- [ ] Retrospectiva y plan de mejora continua

---

## Esfuerzos Actuales (lo que estamos haciendo ahora)

| Tarea | Estado | Impacto |
|-------|--------|---------|
| Parser GDE nativo (formato serializado) | En curso | Critico — sin esto no parsea .mp reales del banco |
| Limpieza ASCII (emojis removidos) | Completado | Necesario para servidores sin UTF-8 |
| CLI con --pset | Completado | Permite ejecutar desde terminal del banco |
| Validacion non-blocking | Completado | Genera codigo aunque haya warnings |
| Package 7z para transferencia | Completado | Permite mover codigo al servidor seguro |
| Metrics + Estimadores actualizados | Completado | Soporte a business case |

## Esfuerzos Futuros Identificados

| Tarea | Prioridad | Estimacion |
|-------|-----------|------------|
| Resolver edges del parser GDE (port mapping) | P0 | 1-2 dias |
| Tests unitarios (cobertura 60%+) | P1 | 1 semana |
| SonarQube setup + remediacion | P1 | 1 semana |
| Documentacion SAD/DDD formato banco | P2 | 3-5 dias |
| Pipeline CI/CD bancario | P2 | 3-5 dias |
| SAST scan + remediacion | P1 | 3-5 dias |
| Pruebas con 5+ grafos reales | P0 | 1 semana |
| UAT con equipo de datos | P1 | 1 semana |
| RFC + CAB | P2 | 2-3 dias (mas espera) |
| Deploy PROD + monitoreo | P2 | 2-3 dias |

---

## Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| Parser GDE no cubre todos los formatos | Validar con multiples .mp reales, iterar |
| SonarQube quality gate muy estricto | Negociar excepciones documentadas |
| Tiempos de aprobacion CAB largos | Iniciar RFC en semana 8, no esperar |
| Grafos muy complejos (>100 nodos) | Tests de stress, optimizar parser |
| Dependencia de acceso al servidor | Mantener package.sh actualizado |
| Equipo no familiarizado con Spark | Incluir sesion de capacitacion en UAT |

---

## Metricas de Exito

- SonarQube: 0 Critical, 0 Blocker, Coverage >60%
- Parser: 90%+ de grafos del banco parseados correctamente
- Codegen: Output ejecutable en Glue sin modificacion manual
- Performance: <30s para parsear + generar un grafo de 100 nodos
- Disponibilidad PROD: 99.9% (Lambda + Amplify)
