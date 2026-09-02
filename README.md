# 🚀 BNX Convertidor

Plataforma para convertir o refactorizar grafos Legacy a Cloud.

Compila grafos Ab Initio (.mp/.xfr/.dml), COBOL (.cbl), y PLANs multi-grafo a código ejecutable en AWS Glue, PySpark, Apache Flink, Step Functions, Terraform y Airflow.

Además de compilar, la plataforma permite **probar el código generado sin subir nada a AWS**:

- **Data Redactada**: genera datos sintéticos con PII enmascarada a partir del esquema real del grafo.
- **Ejecutor de prueba PySpark local**: corre el código generado con esos datos y muestra entradas/salidas por nodo (consola en vivo).
- **Optimizador de performance (por reglas, sin IA)**: aplica `cache`/`broadcast`/`coalesce` y compara original vs optimizado en un benchmark que simula la nube.

> Estatus de conversión (ago 2026): validada de forma funcional para grafos de complejidad baja-media. Barrido de 36 grafos de referencia → 35/36 ejecutan y producen salidas correctas.

---

## 📁 Estructura del Proyecto

```
bnxconvertidor/
├── src/                          # 🔧 BACKEND — Core Engine
│   ├── mp_parser.py              # Parser de grafos .mp (NODE/SUBGRAPH/edges)
│   ├── xfr_parser.py             # Parser de reglas .xfr (select/where/group_by)
│   ├── dml_parser.py             # Parser de schema .dml (keys/tipos)
│   ├── cobol_parser.py           # Parser COBOL (.cbl) → .mp/.xfr/.dml
│   ├── plan_parser.py            # Parser Ab Initio PLAN/PSET + Grafo de Grafos
│   ├── accuracy.py               # Motor de accuracy (cobertura de traducción)
│   ├── refactor_engine.py        # Refactorizador Spark 2→3, Python 2→3, Glue 2→4
│   ├── dag/
│   │   └── builder.py            # DAG Builder + Mega-DAG + topological sort
│   ├── validator/
│   │   └── semantic.py           # Validación semántica + column inference
│   └── codegen/
│       ├── glue_codegen.py       # Generador AWS Glue (PySpark + GlueContext)
│       ├── spark_codegen.py      # Generador PySpark (SparkSession)
│       ├── flink_codegen.py      # Generador Apache Flink (PyFlink + Flink SQL)
│       ├── stepfunctions_codegen.py  # Generador AWS Step Functions (JSON)
│       ├── terraform_codegen.py  # Generador Terraform (.tf)
│       └── airflow_codegen.py    # Generador Apache Airflow (DAG Python)
│
├── api/
│   └── server.py                 # 🌐 FastAPI Server (desarrollo local)
│
├── lambda/
│   └── handler.py                # ⚡ AWS Lambda Handler (producción)
│
├── ui/                           # 🎨 FRONTEND — React App
│   ├── src/
│   │   ├── App.jsx               # App principal (6 tabs, compilador, uploads)
│   │   ├── config.js             # URL de la Lambda
│   │   ├── index.css             # Estilos globales
│   │   └── components/
│   │       ├── ExecutivePage.jsx  # 🎯 Resumen C-level
│   │       ├── FileUpload.jsx    # Upload .mp/.xfr/.dml
│   │       ├── DagViewer.jsx     # Visualizador de DAG (ReactFlow)
│   │       ├── DesignerPage.jsx  # 🎨 Editor visual drag & drop
│   │       ├── BankingModelPage.jsx  # 🏦 Modelo operativo bancario
│   │       ├── GovernancePage.jsx    # Gobierno de datos (DAMA + políticas)
│   │       ├── DamaPage.jsx      # Framework DAMA
│   │       ├── ArchitecturePage.jsx  # 🏗️ Arquitectura + Glosario
│   │       └── MetricsPage.jsx   # 📊 Métricas y estimaciones
│   ├── package.json
│   └── vite.config.js
│
├── main.py                       # 🖥️ CLI — Compilador batch
├── graphs/                       # Grafos de ejemplo
│   └── test_mega/                # Grafos para Mega-DAG
├── cobol/                        # Archivos COBOL de ejemplo
├── abinitio/                     # Archivos Ab Initio de ejemplo
├── samples/
│   └── refactor/                 # Archivos para probar refactorización
├── e2e/                          # Test end-to-end en AWS Glue
├── amplify.yml                   # Config de Amplify build
└── .gitignore
```

---

## 🔧 Backend — Core Engine

### Parsers
| Parser | Archivo | Entrada | Salida |
|--------|---------|---------|--------|
| MP Parser | `src/mp_parser.py` | `.mp` (grafo) | AST {nodes, edges, subgraphs} |
| XFR Parser | `src/xfr_parser.py` | `.xfr` (reglas) | Dict de reglas por nodo |
| DML Parser | `src/dml_parser.py` | `.dml` (schema) | Dict de keys y tipos |
| COBOL Parser | `src/cobol_parser.py` | `.cbl` (COBOL) | .mp + .xfr + .dml generados |
| PLAN Parser | `src/plan_parser.py` | `.plan` + `.pset` | Grafos con dependencias |

### DAG Builder
- Construye DAG con topological sort
- Soporta Mega-DAG (múltiples grafos combinados)
- Excluye retrocesos (feedback loops) del topo sort
- Detecta ciclos no válidos

### Validador Semántico
- Infiere columnas a través del DAG
- Valida join keys existen en padres
- Detecta nodos huérfanos
- Valida cross-graph edges en Mega-DAG

### Code Generators
| Target | Archivo | Tecnología |
|--------|---------|------------|
| AWS Glue | `glue_codegen.py` | PySpark + GlueContext |
| PySpark | `spark_codegen.py` | SparkSession puro |
| Apache Flink | `flink_codegen.py` | PyFlink + Flink SQL |
| Step Functions | `stepfunctions_codegen.py` | JSON state machine |
| Terraform | `terraform_codegen.py` | HCL (.tf) |
| Airflow | `airflow_codegen.py` | Python DAG |

### Refactorizador
| Migración | Cambios principales |
|-----------|-------------------|
| Spark 2→3 | SparkContext→SparkSession, registerTempTable→createOrReplaceTempView, unionAll→union |
| Python 2→3 | print→print(), unicode→str, has_key→in, iteritems→items, except comma→as |
| Glue 2→4 | GlueVersion 2.0→4.0, Python 2→3, shebang update |

### 11 Tipos de Nodo
| Tipo | Descripción | Ab Initio equivalente |
|------|-------------|----------------------|
| SOURCE | Lectura (S3/Kafka/JDBC) | Read, Scan |
| TRANSFORM | SELECT/WHERE/GROUP BY | Reformat, Rollup |
| JOIN | Combinar por key | Join |
| DEDUP | Deduplicar por key | Dedup Sort |
| NORMALIZE | Expandir filas (explode) | Normalize |
| LOOKUP | Referencia broadcast | Lookup |
| CONCATENATE | Union sin key | Concatenate |
| GATHER | Merge streams | Gather |
| PARTITION | Repartir por key | Partition by Key |
| FILTER | Filtrar con rechazo | Filter by Expression |
| SINK | Escritura (S3/Kafka/JDBC) | Write |

---

## 🎨 Frontend — React App

### Pestañas
| Tab | Descripción |
|-----|-------------|
| 🎯 Executive | Resumen C-level, pipeline F1/F2/F3, comparativa |
| 🔧 Compiler | Upload, compilar, visualizar DAG, optimizar performance, descargar código |
| 🧪 Data Redactada | Datos sintéticos + prueba PySpark local + enviar a AWS |
| 🎨 Designer | Editor visual drag & drop de grafos |
| 🏦 Banking | Modelo operativo, DAMA, gobierno de datos |
| 🏗️ Architecture | Diagrama interactivo + glosario de mecanismos |
| 📊 Metrics | Horas-hombre, estimación 40K jobs, costos |

### Funcionalidades del Compiler
- Upload .mp + .xfr + .dml → compilar a Glue/Spark/Flink
- Upload .cbl → conversión COBOL automática
- Upload PSET + XFR + MP files + PLAN → Mega-DAG (Grafo de Grafos)
- Upload .py → refactorización Spark 2→3 / Python 2→3
- Edición de nodos en el DAG con recompilación
- Descarga: Code, DAG (SVG), Full Report, StepFn, Terraform, Airflow
- **Optimizar performance**: genera una versión optimizada del PySpark y muestra el diff (pantalla completa, líneas resaltadas) + benchmark original vs optimizado

### Data Redactada (datos sintéticos + prueba local)
- Genera datos sintéticos con PII enmascarada infiriendo el esquema real del grafo (record format del .mp, casts, select)
- Detecta PII por nombre de campo (nombre, cuenta, tarjeta, email, rfc/ssn, etc.)
- Valores de join compartidos para que los joins emparejen datos (no dejan columnas en NULL)
- **Ejecutar prueba PySpark**: corre el código generado localmente con esos datos, con consola en vivo (SSE) y conteo de filas por tabla de entrada/salida
- **Enviar a AWS**: empaqueta el PySpark con los datos embebidos (código autocontenido) y lo despacha al pipeline Glue con polling de estado

---

## 🖥️ Uso — Modo Batch (CLI)

### Compilar un grafo
```bash
python3 main.py --project graph.mp --xfr rules.xfr --target glue --output job.py
```

### Targets disponibles
```bash
python3 main.py --project graph.mp --target glue --output glue_job.py
python3 main.py --project graph.mp --target spark --output spark_job.py
python3 main.py --project graph.mp --target flink --output flink_job.py
```

### Con schema DML
```bash
python3 main.py --project graph.mp --xfr rules.xfr --dml schema.dml --target glue --output job.py
```

---

## 🌐 Uso — Modo Gráfico (UI)

### Desarrollo local
```bash
cd ui
npm install
npm run dev
# Abre http://localhost:3000
```

### Producción
- **UI (Amplify)**: https://empresav4.d330swque2c5nj.amplifyapp.com
- **API (Lambda)**: https://rcp5mtwkqngtb3fv3fiourq2hq0qptmy.lambda-url.us-east-1.on.aws
- **UI + prueba Spark local (EC2 vía CloudFront, HTTPS)**: https://d1bgd4yg4qrgz0.cloudfront.net

> Amplify + Lambda sirven la UI y la compilación. La **prueba PySpark local** (Data Redactada → "Ejecutar prueba")
> necesita un runtime con Spark, que la Lambda no tiene: para eso se usa el despliegue EC2 servido por CloudFront.

### EC2 (mismo comportamiento que en local, ahora en la nube)
El servidor `serve_ui.py` sirve la UI y la API en el mismo puerto (8081), igual que en la Mac. Corre en una EC2
con Spark instalado, como servicio systemd. CloudFront le pone HTTPS delante.

```bash
# Actualizar la EC2 con los últimos cambios
ssh -i /ruta/monkey2.pem ec2-user@<IP-EC2>
cd app && git pull && sudo systemctl restart bnx
```

---

## ⚡ API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/compile` | POST | Compila .mp + .xfr + .dml → código |
| `/cobol` | POST | Convierte .cbl → grafo → código |
| `/plan` | POST | Compila PLAN + PSET + MP files → Mega-DAG |
| `/refactor` | POST | Refactoriza código legacy (Spark 2/Python 2/Glue 2) |
| `/datagen` | POST | Genera datos sintéticos (PII enmascarada) desde el grafo (JSON) |
| `/optimize` | POST | Devuelve el PySpark optimizado (cache/broadcast/coalesce) + resumen de cambios |
| `/optimize/compare` | POST | Ejecuta original vs optimizado y compara tiempos + equivalencia de salidas |
| `/run` (SSE) | POST | Ejecuta el PySpark generado localmente con datos sintéticos (solo EC2, requiere Spark) |

### Ejemplo: compilar un grafo
```bash
curl -X POST https://API_URL/compile \
  -F "mp=@graph.mp" \
  -F "xfr=@rules.xfr" \
  -F "target=glue"
```

### Ejemplo: refactorizar código
```bash
curl -X POST https://API_URL/refactor \
  -F "code=@spark2_code.py" \
  -F "source_version=all"
```

---

## ☁️ Deploy

### Lambda (Backend)
```bash
zip -r lambda_package.zip lambda/handler.py src/ -x "src/__pycache__/*" "src/**/__pycache__/*"
aws lambda update-function-code --function-name bnx-compiler --zip-file fileb://lambda_package.zip --region us-east-1
```

### Amplify (Frontend)
```bash
git add <archivos>          # evitar git add -A: hay zips y credenciales excluidos
git commit -m "update"
git push origin empresav4
# Amplify auto-deploys from Git
```

### EC2 + CloudFront (UI con prueba Spark local)
La EC2 corre `serve_ui.py` como servicio systemd (`bnx.service`) con Spark instalado.
CloudFront va delante para dar HTTPS con certificado válido.

```bash
# 1. Push de los cambios
git push origin empresav4

# 2. Actualizar la instancia
ssh -i /ruta/monkey2.pem ec2-user@<IP-EC2>
cd app
git pull
sudo systemctl restart bnx     # reinicia el servicio
sudo systemctl status bnx       # verificar que quedó activo
```

- Instancia: `t3.xlarge` (4 vCPU / 16 GB), Amazon Linux 2023, Java 17 + PySpark 3.5.1
- Servicio: `bnx.service` (systemd) → `serve_ui.py` en el puerto 8081
- HTTPS: distribución CloudFront delante de la EC2 (redirige HTTP→HTTPS)

---

## 🏗️ Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  .mp / .xfr │     │   .cbl       │     │ .plan/.pset │
│  .dml       │     │   (COBOL)    │     │ + .mp files │
└──────┬──────┘     └──────┬───────┘     └──────┬──────┘
       │                   │                    │
       ▼                   ▼                    ▼
┌──────────────────────────────────────────────────────┐
│                    PARSERS                            │
│  mp_parser · xfr_parser · dml_parser · cobol_parser  │
│  plan_parser (Grafo de Grafos + Planes Cíclicos)     │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│              DAG BUILDER + VALIDATOR                  │
│  Topological sort · Column inference · Accuracy       │
│  Mega-DAG · Cross-graph edges · Retrocesos           │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                 CODE GENERATORS                       │
│  Glue · Spark · Flink · StepFn · Terraform · Airflow │
└──────────────────────┬───────────────────────────────┘
                       │
              ┌────────┴─────────────────┐
              ▼                          ▼
        ┌──────────┐     ┌──────────┐   ┌──────────────────────┐
        │  Lambda  │     │ Amplify  │   │  EC2 (Spark local)   │
        │  (API)   │     │  (UI)    │   │  serve_ui.py :8081   │
        └──────────┘     └──────────┘   │  systemd bnx.service │
         compilar          UI web       └──────────┬───────────┘
                                                    │ HTTPS
                                              ┌─────▼──────┐
                                              │ CloudFront │
                                              └────────────┘
                                        prueba PySpark real + datos sintéticos
```

Dos formas de servir la app:
- **Amplify (UI) + Lambda (API)**: compilar, refactorizar, generar datos. Sin Spark.
- **EC2 + CloudFront**: todo lo anterior **más** ejecutar la prueba PySpark local con datos sintéticos (necesita runtime Spark).

---

## 📋 Formatos de Archivo

### .mp (Graph)
```
NODE ReadCSV : SOURCE
NODE CleanData : TRANSFORM
NODE WriteOutput : SINK

ReadCSV -> CleanData
CleanData -> WriteOutput
```

### .xfr (Transform Rules)
```
ReadCSV:
  source_type s3
  path s3://bucket/data
  format csv

CleanData:
  select id, name, amount
  where amount > 0

WriteOutput:
  sink_type s3
  path s3://bucket/output
  format parquet
  mode overwrite
```

### .plan (PLAN — Grafo de Grafos)
```
PLAN banking_pipeline
VERSION 2.0

GRAPH ingest
  MP: graphs/ingest.mp
  XFR: graphs/ingest.xfr
  PRIORITY: HIGH

GRAPH enrich
  MP: graphs/enrich.mp
  DEPENDS: ingest

GRAPH report
  MP: graphs/report.mp
  DEPENDS: enrich
  SCHEDULE: CYCLIC
  MAX_ITERATIONS: 10
  CONVERGENCE: delta < 0.01
```

### .pset (Parameters)
```
S3_INPUT = s3://datalake/raw
S3_OUTPUT = s3://datalake/curated
OUTPUT_FORMAT = parquet
MAX_ITERATIONS = 10
CONVERGENCE = delta < 0.01
```
