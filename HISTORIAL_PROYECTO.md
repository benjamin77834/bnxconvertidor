# Historial del Proyecto BNX Convertidor

## Bitacora de Desarrollo — Escrita por el equipo de desarrollo

---

## Que es BNX Convertidor

Es una plataforma que construimos para migrar los grafos ETL legacy de Ab Initio (y programas COBOL) a codigo cloud-native ejecutable en AWS Glue, PySpark, Apache Flink, Step Functions, Terraform y Airflow. Lo estamos haciendo para un banco mexicano que tiene ~40,000 jobs en Ab Initio y necesita salir de esa plataforma.

---

## 20 de marzo 2026 — Dia 1: Arrancamos

Creamos el repositorio con el motor de migracion ETL version 7. La primera version ya tenia parsers basicos para archivos .mp (grafos), .xfr (reglas de transformacion) y generadores de codigo para Glue y Spark. Organizamos el codigo fuente en `src/` con la estructura modular que usariamos de ahi en adelante.

---

## 23 de marzo — Dia 2: Documentacion y ramas

Actualizamos el README con instrucciones de uso. Creamos las ramas `empresav2` y `empresav3` para iterar sobre la version que le mostrariamos al banco.

---

## 26 de marzo — Dia 3: Gran reestructura + UI

Este fue un dia grande. Hicimos varias cosas:

1. **Creamos la interfaz grafica** — app React con Vite y ReactFlow para visualizar los DAGs.
2. **Creamos el server FastAPI** (`api/server.py`) para exponer la compilacion como servicio.
3. **Limpieza masiva del codigo** — borramos todo el codigo disperso (carpetas `compiler/`, `dag/`, `parsers/` viejas) y consolidamos todo en la estructura `src/` limpia.
4. **Construimos el DAG Builder** con topological sort, validador semantico y motor de accuracy.
5. **Creamos grafos de prueba**: monster (complejo, 20+ nodos), advanced, y small.
6. **Preparamos el deploy** — Lambda handler + configuracion de Amplify.

---

## 27 de marzo — Dia 4: Deploy a AWS

Desplegamos por primera vez a produccion:
- Subimos el backend como AWS Lambda con lambda_package.zip
- Configuramos Lambda URL para invocaciones directas
- Agregamos un grafo de prueba complejo con DML para validar el flujo completo
- Mejoramos el DagViewer y el validador

---

## 28 de marzo — Dia 5: Parser COBOL + Metricas

Construimos el **parser de COBOL**: toma un archivo `.cbl` y lo convierte automaticamente en `.mp` + `.xfr` + `.dml`, que luego compila a Glue/Spark como cualquier otro grafo. Creamos un archivo COBOL de ejemplo bancario. Tambien arrancamos la pagina de Metricas con estimaciones de costos y horas-hombre.

---

## 29 de marzo — Dia 6: Iteraciones en metricas

Ajustamos la pagina de metricas con varias iteraciones de mejoras visuales y de contenido.

---

## 31 de marzo — Dia 7: Designer + Banking + Governance

Dia productivo. Construimos tres paginas nuevas:

1. **Designer Page** — editor visual drag-and-drop donde puedes armar grafos arrastrando nodos.
2. **Banking Model Page** — modelo operativo bancario con fases y responsabilidades.
3. **Governance Page** — gobierno de datos basado en framework DAMA.

Tambien agregamos archivos COBOL mas complejos (EBCDIC batch, tarjeta de credito) y mejoramos los code generators y el XFR parser.

---

## 1 de abril — Dia 8: Gobierno de datos a profundidad

Iteramos extensivamente sobre la GovernancePage. Le metimos politicas de datos, roles, controles, y alineacion con DAMA DMBOK. Mejoramos los estilos CSS generales de la UI.

---

## 5 de abril — Dia 9: Pagina de Arquitectura

Creamos la **ArchitecturePage** con un diagrama interactivo de la arquitectura del sistema y un glosario de componentes tecnicos.

---

## 6 de abril — Dia 10: Mejoras en Metricas

Mas refinamientos a MetricsPage — ajustes de estimaciones y presentacion.

---

## 7 de abril — Dia 11: Parser de PLANs Ab Initio

Gran feature nuevo:

1. **Construimos `plan_parser.py`** — parsea archivos PLAN y PSET de Ab Initio.
2. Los PLANs definen el "Grafo de Grafos": multiples grafos con dependencias entre ellos.
3. Creamos ejemplos reales: `sample_banking.plan` (22 grafos, pipeline bancario diario completo) y `credit_card.plan` (pipeline de tarjeta de credito).
4. Generamos codigo PySpark a partir de planes completos.
5. Agregamos la carpeta `samples/` con README explicativo.

---

## 8 de abril — Dia 12: DAMA Page + Multi-source

Creamos la **DamaPage** como componente separado (antes estaba dentro de Governance). Agregamos grafos de ejemplo multi-source (multiples fuentes de datos en un solo pipeline).

---

## 9 de abril — Dia 13: Pagina Ejecutiva

Construimos la **ExecutivePage**: un resumen nivel C-level con:
- Visualizacion del pipeline F1/F2/F3 (fases de migracion)
- Comparativa de tecnologias
- KPIs ejecutivos

Tambien refrescamos la UI general y mejoramos el DagViewer.

---

## 13-14 de abril — Dias 14-15: Flink + Planes Ciclicos

1. **Nuevo generador: Apache Flink** — genera codigo PyFlink + Flink SQL.
2. **Planes ciclicos** — implementamos soporte para `MAX_ITERATIONS` y `CONVERGENCE` en planes que necesitan iterar (ej: scoring de riesgo iterativo).
3. Agregamos el glosario de mecanismos (los 11 tipos de nodo + concepto de Grafo de Grafos).
4. Debuggeamos y arreglamos la deteccion de mp_files en Lambda.

---

## 15-17 de abril — Dia 16: Motor de Refactorizacion

Construimos el **refactor_engine.py** que migra codigo legacy automaticamente:

| Migracion | Que hace |
|-----------|----------|
| Spark 2 → 3 | SparkContext→SparkSession, registerTempTable→createOrReplaceTempView |
| Python 2 → 3 | print→print(), unicode→str, has_key→in |
| Glue 2 → 4 | GlueVersion upgrade, Python 2→3 en scripts Glue |

Agregamos archivos de ejemplo para refactorizar, integramos con la UI y la API, y reescribimos el README completo.

---

## 22 de abril — Dia 17: Admin Mode + Downloads

1. **Modo admin** con password en la pagina de Arquitectura — muestra el codigo fuente de cada componente.
2. **Endpoint de descarga ZIP** — puedes bajar backend, frontend o todo con scripts de instalacion incluidos.
3. Documentacion de uso batch en el CLI.

---

## 23 de abril — Dia 18: Formato nativo Ab Initio

Atacamos el problema de los .mp reales del banco:

1. **Parser GDE nativo** — los .mp del banco no vienen en formato texto limpio sino en formato serializado GDE (XXGpvertex/XXGedge). Construimos el parser para eso.
2. Agregamos un grafo monster de 45 nodos en formato nativo como prueba.
3. **Editor multi-tab** (MP/XFR/PSET) con syntax highlighting y status indicators.
4. Soporte para formato nativo de PSET (KEY||||VALUE + expresiones PDL).
5. Analisis de costos de licencia Ab Initio + timeline actualizado.

---

## 28 de abril — Dia 19: Bug critico

Encontramos y arreglamos un bug de indentacion en el parser de formato BNX que hacia que no se parsearan los nodos correctamente. Era un bug critico que rompia la compilacion.

---

## 4 de mayo — Dia 20: Filtro de fechas

Agregamos **filtro de scan date** (scan_year/scan_month/partition_filter) al codegen. Tambien mapeamos funciones de fecha de Ab Initio (string_to_date, date_to_string, etc.) a sus equivalentes en PySpark.

---

## 5 de mayo — Dia 21: SonarQube + Seguridad

Preparamos el proyecto para compliance bancario:
- Configuramos `sonar-project.properties` para SonarQube
- Creamos `requirements.txt` para escaneo de dependencias con BlackDuck
- Actualizamos `.gitignore`

---

## 6 de mayo — Dia 22: CLI + Packaging

1. **`bnx.sh`** — script CLI para compilar, testear y deployar rapido.
2. **`package.sh`** — empaqueta todo en un .7z portable de 72KB listo para transferir al servidor seguro del banco.
3. **Visualizador de DAG en HTML** — genera un archivo HTML con el grafo interactivo.
4. Limpiamos emojis del HTML para servidores que no soportan UTF-8.

---

## 7 de mayo — Dia 23: Motor OCR

Construimos una feature nueva: **OCR para grafos Ab Initio**.

- Subes una imagen (screenshot de un grafo en GDE) o pegas texto
- El motor extrae la estructura del grafo (nodos + conexiones)
- Lo convierte a .mp y luego lo compila normalmente
- Soporta multi-paste con acumulacion y pegado de imagen desde clipboard (Cmd+V)

Creamos `src/ocr_engine.py` para esto.

---

## 8 de mayo — Dia 24: Estimador de costos + Matriz de decision

1. **Cloud Cost Estimator** — slider de 1K a 40K jobs que compara costos de Ab Initio vs EKS vs LeapLogic vs BNX a 5 anos.
2. **Matriz de decision ejecutiva** — tabla comparativa con pros/cons/costos de cada opcion.
3. Tema visual MonkeyPhone (verde + dorado).
4. Boton de exportar a PDF.
5. Agregamos LeapLogic a la comparativa ejecutiva.

---

## 10 de mayo — Dia 25: Polish de metricas

Varias iteraciones refinando la pagina de metricas — numeros, presentacion, graficos.

---

## 25 de mayo — Dia 26: GDE Parser mejorado + Roadmap

1. Mejoramos el parser GDE nativo (enfoque finditer para mayor robustez).
2. Limpieza ASCII final para compatibilidad con servidores del banco.
3. **Creamos `PLAN_TRABAJO_3MESES.md`** — plan SDLC bancario completo: SonarQube, SAST/DAST, testing formal, CI/CD, QA, CAB, deploy produccion.
4. Agregamos pagina de Roadmap al UI.
5. Actualizamos los scripts de packaging.

---

## 3 de junio — Dia 27: GDE Parser completo

El parser GDE quedo funcional al 100%:
- Extrae nombres correctamente
- Parsea edges del formato serializado
- Extrae transforms embebidos en el formato nativo
- Fix en serve_ui para manejar los transforms extraidos

---

## 24 de junio — Dia 28: Target Python/Pandas

Agregamos **Python/Pandas como target de generacion de codigo** — para equipos que no necesitan Spark y prefieren pandas puro. Tambien arreglamos un bug en el groupby con quoting de columnas.

---

## Resumen de lo que tenemos hoy

| Componente | Estado |
|-----------|--------|
| Parser MP (texto) | Completo |
| Parser MP (GDE nativo) | Completo |
| Parser XFR | Completo |
| Parser DML | Completo |
| Parser COBOL | Completo |
| Parser PLAN/PSET | Completo |
| DAG Builder + Mega-DAG | Completo |
| Validador semantico | Completo |
| Codegen Glue | Completo |
| Codegen Spark | Completo |
| Codegen Flink | Completo |
| Codegen Step Functions | Completo |
| Codegen Terraform | Completo |
| Codegen Airflow | Completo |
| Codegen Python/Pandas | Completo |
| Motor de refactorizacion | Completo |
| Motor OCR | Completo |
| Motor de accuracy | Completo |
| UI React (6 tabs) | Completo |
| API FastAPI + Lambda | Completo |
| CLI batch | Completo |
| Packaging portable | Completo |
| Deploy Amplify + Lambda | Activo |

---

## Que sigue (segun plan de 3 meses)

1. Pruebas con grafos reales del banco (5+ grafos diferentes)
2. Tests unitarios al 60% de cobertura
3. SonarQube: 0 Critical, 0 Blocker
4. SAST/DAST scan + remediacion
5. Pipeline CI/CD bancario
6. Documentacion SAD/DDD formato banco
7. QA formal + UAT
8. RFC + CAB (Change Advisory Board)
9. Deploy a produccion con monitoreo

---

## URLs de produccion

- **UI**: https://empresav4.d330swque2c5nj.amplifyapp.com
- **API**: https://rcp5mtwkqngtb3fv3fiourq2hq0qptmy.lambda-url.us-east-1.on.aws
