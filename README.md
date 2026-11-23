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

### Pila de ciencia de datos en el Framework MLOps v2
El env que se baja (`preparar_vendor.py`, `start_server.sh`; tag del Release `vendor-linux-v2`, configurable con `--tag` o `BNX_VENDOR_TAG`) ya trae PySpark **y** la pila: xgboost, lightgbm, scikit-learn, scipy, statsmodels, matplotlib, seaborn, joblib, threadpoolctl (+ transitivas). En la pagina del paquete la opcion "Incluir pila de ciencia de datos" viene activada; si la desmarcas solo van las librerias que tu codigo importa (xgboost/sklearn/lightgbm/scipy/...), y un paquete sin ellas sigue ligero. `setup.sh` las instala offline desde `vendor/` y, si falta una wheel, completa por internet.
OpenMP: en Mac, `setup.sh`/`run.sh` usan la `libomp` de scikit-learn (`DYLD_LIBRARY_PATH`) si no hay `brew install libomp`; en Linux hace falta `libgomp` (`yum install libgomp` / `apt-get install libgomp1`); en Windows el Visual C++ Redistributable.

### Simular los jobs desde la UI (Framework MLOps v2, Mac/Linux + Java)
En el reporte del paquete generado, el panel **🖥 Simular jobs** corre cada job (o todos) como un terminal en vivo:
`python main.py --demo --source <job>` (todos: `--demo --continuar-si-falla`), Spark local con datos sinteticos. Muestra
el log (autoscroll, colores `[OK]`/`[ERROR]`), estado, duracion, boton Cancelar (mata el arbol de procesos) y Copiar log;
al terminar, resumen por job (estado, tiempo, filas escritas) y el visor de `demo_out/`.
- **El PIVOTE corre siempre primero.** Todos: pivotes (`*_pivot`, ruta `.../pivot/` o `"pivot": true` en `orden.json`) y luego el
  resto por `depends_on` (lo hace el runner de `main.py`, tambien fuera de la UI). Un job suelto que no es pivote corre antes el
  pivote de su mismo modelo (`rps_target` -> `rps_pivot`) si su salida no esta ya en `demo_out/` de la sesion; `↺ Reiniciar demo_out` empieza limpio.
- El paquete se monta en `<cache>/_simular/<hash del ZIP>/` y su `.venv` se crea UNA vez con `setup.sh` (offline desde `vendor/`; lo que no
  sirva en esta maquina lo completa por internet) y se reutiliza mientras el ZIP no cambie. Python: el target del paquete si existe (`python3.11`), si no el del host con aviso.
- Config de negocio (`bin/settings`: `spark.json`, `jobs.json`, `config_custom.json`, `<modelo>/<job>.json`): al subir la carpeta del proyecto la UI sube tambien los `.json/.yaml/.cfg/.ini` que viven bajo una carpeta `settings/`; van a `bank_src/settings/` del paquete (config interna del banco: queda en el ZIP, nunca en git) y la simulacion la usa por defecto. El campo "Carpeta `bin/settings`" se pre-llena con la detectada y se puede cambiar por una ruta local (validada, solo lectura; se recuerda por proyecto). **Sin settings** el demo los INFIERE del codigo (AST de los jobs y de `utils/`, `toolbox/`, `bnmxverse/`: `self.config['x']`, `settings['tables_info'][t]['database']`, `config_custom[...]`) y rellena placeholders; las claves inventadas quedan en `demo_out/REPORTE_DEMO.json` (`settings_inventados`). Si falta una clave el terminal dice cual y en que archivo deberia estar.
- Ambiente (`uat`/`prod`/`sbx`): selector "Ambiente de los settings" (default: el que trae todas las claves; si `uat` esta incompleto, `prod`). Si una clave existe en otro ambiente el aviso lo dice (`'lag_ecm_pivot' esta en 'prod' pero no en 'uat'`); los settings del banco nunca se modifican.
- Recursos del demo: `local[N]` con `N = BNX_DEMO_CORES` o `min(4, max(1, cpus-1))`, `shuffle.partitions = max(4, N)`, AQE con `initialPartitionNum = 2N`, `repartition(1000)` limitado a `2N` solo en demo, `spark.driver.memory = BNX_DEMO_MEM` (4g), sin barras `[Stage ...]`. Encabezado: `demo: local[4] de 10 nucleos | shuffle 4 | AQE on | driver 4g`.
- Monitoreo de recursos (CPU/memoria, cada `BNX_MONITOR_INTERVALO` s, default 1; `BNX_MONITOR=0` lo apaga): proceso del runner + hijos (JVM, workers) con psutil si esta, `/proc` en Linux o `ps` en Mac. La `TABLA DE TIEMPOS` agrega CPU % prom/pico, nucleos prom, memoria pico, tareas Spark y eficiencia (`CPU / (tiempo x nucleos asignados)`), y termina con `CPU: promedio X% de N nucleos (efectivos Y; ...)`. La UI dibuja CPU y memoria en vivo con marcas por job.
- Un run a la vez por paquete (409); solo desde localhost; `BNX_SIMULAR_TIMEOUT` (s, default 1800), `BNX_SIMULAR_DIR` cambia la carpeta de trabajo. Windows: mensaje "requiere Mac/Linux (o WSL) y Java".
- Nombres de jobs por ruta (`rps_target`...): suban la **carpeta completa** (o con su ruta); archivos sueltos sin ruta quedan `job`, `job_2`... con aviso.
  Si el portal se arranco antes de actualizar el codigo, la pagina avisa (`/api/health` -> `codigo_desactualizado`): reinicialo.
### Simular en Linux RHEL 8 x86_64 (Podman en Mac Apple Silicon)
La simulacion "Este equipo" corre con el venv de la Mac; no prueba lo que pasa en el servidor del banco (RHEL 8, glibc 2.28, Python 3.11, Java 17, wheels manylinux x86_64). El selector **Dónde simular → Linux RHEL 8 x86_64 (contenedor)** corre el paquete en un contenedor `linux/amd64` (Rosetta en la VM de Podman):
- Requisitos: `brew install podman`. Una sola vez, el boton **Preparar Linux (una vez, ~8 GB)** (o `bash tools/linux/simular_en_linux.sh preparar`) crea la maquina `bnx-linux` (4 CPU, 6 GB RAM, 30 GB de disco; `podman machine init --cpus 4 --memory 6144 --disk-size 30`) y las imagenes `bnx-rhel8` (servidor SIN PySpark) y `bnx-rhel8-spark` (servidor con PySpark 3.5.6 en el python3.11 del sistema) desde `tools/linux/Containerfile.rhel8`. Las imagenes NO llevan codigo del banco: el ZIP se extrae en `<cache>/_simular_linux/<hash>/` y se **monta** en `/work`.
- Que corre (igual que en el servidor): `bash setup.sh` con `--network none` (prueba que `vendor/` esta completo), `python check_env.py` y `bash run.sh --demo [--source <job>]` (pivote primero), con el log en vivo; cancelar hace `podman kill` + `rm -f`. Un run Linux a la vez. El terminal muestra `Linux RHEL 8 x86_64 · Python 3.11.x · glibc 2.28 · Java 17` detectado dentro del contenedor. Un paquete "sin PySpark" usa la imagen con PySpark del sistema y `setup.sh` debe autodetectarlo sin preguntar.
- CLI: `bash tools/linux/simular_en_linux.sh simular framework_mlops_v2_con_pyspark.zip [job|todos] [--settings /ruta/bin/settings]`; `... cluster ZIP` prueba `BNX_SPARK=cluster bash run.sh` con un `spark3-submit` FALSO (imprime argv) y `/etc/spark3/conf` falso (`tools/linux/fake/`): valida `--conf spark.pyspark.driver.python`, `SPARK_CONF_DIR` del cluster sin reemplazar, y cola/executors del `spark.json`.
- Que valida: Python 3.11/glibc 2.28/x86_64, wheels offline completas, deteccion del PySpark del sistema, imports, y el codigo de los jobs con datos sinteticos. Que NO: no hay YARN, Hive, Teradata ni red del banco; los tiempos con emulacion x86_64 son varias veces los del servidor real. Los temporales de Spark (`.bnx_tmp`) van en `tmpfs` porque la JVM bajo Rosetta+virtiofs deja carpetas ilegibles.
- Espacio: la maquina ocupa ~12 GB en disco y las imagenes ~1.2 GB; `bash tools/linux/simular_en_linux.sh apagar` detiene la VM. Los paquetes montados se limpian con el boton "Limpiar simulaciones".
### Cache de vendor (Framework MLOps v2, paquetes Linux offline)
Los wheels que se empaquetan (PySpark 3.5.6/4.0.0, py4j, pandas/numpy manylinux, mex-lib del banco)
viven **dentro del venv**: `.venv/bnx_vendor_cache/` (o `BNX_VENDOR_CACHE=/otra/ruta`). `./start_server.sh`
lo revisa al arrancar y, si falta algo, pregunta si bajarlo/generarlo (3.8, 3.12, ambas) o importarlo
desde un ZIP; sin terminal interactiva solo avisa (o baja solo con `BNX_VENDOR_AUTO=3.8|3.12|ambas`).
```bash
.venv/bin/python preparar_vendor.py --estado            # que falta (--json para maquinas)
.venv/bin/python preparar_vendor.py --python 3.12        # baja/genera (~500 MB por version)
.venv/bin/python preparar_vendor.py --zip bnx_vendor_py3.8.zip   # sin internet: ZIP de otra maquina
python exportar_vendor.py --python 3.8                   # en la maquina con cache: arma el ZIP
```
Las mex-lib del banco no estan en PyPI: llegan por ZIP o desde la pagina "Librerias del banco".
La pagina del Framework MLOps v2 tambien tiene el boton **Bajar/generar cache**.

### Ejecución en el cluster (YARN) sin instalar en otros nodos

**Regla:** todo se instala **solo en el nodo desde donde lanzas** (edge node / master). Los
workers del cluster **no se tocan**: no llevan venv, ni librerías, ni este paquete.

#### Dónde se instala y qué corre dónde
| Pieza | Dónde vive / corre | Qué necesita |
|---|---|---|
| `setup.sh` (crea `.venv` con Python 3.11 y las librerías) | **solo el edge node** | nada en los workers |
| **Driver** (`main.py`, tus jobs, pandas, xgboost, sklearn...) | el edge node (`--deploy-mode client`) | el `.venv` del edge node |
| **Executors** | JVM de Spark en los workers (los arranca YARN) | solo Java/Spark del cluster, **sin Python** |

Mientras el código use **SQL / DataFrame** (select, join, groupBy, agg, funciones de
`pyspark.sql.functions`, `spark.sql(...)`, escribir/leer parquet), todo el trabajo pesado lo hace la
JVM de los executors y **los workers no necesitan Python**. Python solo hace de "control remoto" en el driver.

#### Cómo lanzar
```bash
# una sola vez, en el edge node
bash setup.sh

# la consulta/job en YARN con los recursos del banco (cola, executors, memoria)
BNX_SPARK=cluster bash run.sh --config pivot.json --settings /ruta/bin/settings --env uat --cohort 202501 --extract-only

# jobs del banco (run(kernel)) con sus settings
BNX_SPARK=cluster bash run.sh --settings /ruta/bin/settings --env uat --fid <fid>
```
Al arrancar, `run.sh` imprime `[spark-conf]` con lo que va a pedir a YARN y `main.py` imprime
`[spark] master=... applicationId=...` con lo que realmente quedó (cola, executors, memoria, particiones).

#### Cómo se aplican los recursos
`run.sh` calcula la configuración de **lanzamiento** (`spark.executor.*`, `spark.yarn.queue`,
`spark.dynamicAllocation.*`, `spark.driver.memory`...) y la pasa al `spark-submit` con un `--conf` por clave
(se guarda en `.bnx_spark_conf.properties`; no se usa `--properties-file` para no perder el
`spark-defaults.conf` del cluster). Orden de prioridad, de menor a mayor:
1. Valores por defecto: asignación dinámica activada y `spark.sql.shuffle.partitions=200`, sin cola.
2. `spark.conf` del cfg JSON del framework (`{"spark": {"conf": {...}}}`).
3. `spark.json` del banco (`--settings <bin/settings>` o `CONF_PATH`): bloque `default` (o el de `spark_config`;
   con `BNX_SPARK_MODELO=<modelo>` el `spark_config` de ese modelo). Con `--env uat` la cola es `spark_queue_uat`.
4. `BNX_DRIVER_MEMORY=8g` (solo la memoria del driver).
5. `BNX_SPARK_CONF="spark.executor.memory=20g;spark.executor.cores=4"` (pares separados por `;`): lo último que dices tú.

Nunca se pisa el `--master` (usa `BNX_MASTER=...` si necesitas otro) ni se quitan `lz4` ni el tmp propio.
Aviso: `spark.driver.memory` del banco puede ser grande (p.ej. 24g); el edge node debe tener esa RAM libre
o baja la memoria con `BNX_DRIVER_MEMORY`.

#### Un solo nodo (sin YARN): `local[*]`
Con datos reales (`--config` o `--settings`) y sin cluster, la sesión usa **todos los núcleos** del nodo
(`local[*]`), `spark.sql.shuffle.partitions = max(8, 2 x núcleos)` y la memoria del driver
(`BNX_DRIVER_MEMORY`, o el `spark.driver.memory` del cfg, o la mitad de la RAM hasta 32g).
En local la memoria del driver solo vale **al lanzar**, por eso `run.sh` la pasa con `--driver-memory`
(si corres `python main.py` a mano, exporta `PYSPARK_SUBMIT_ARGS="--driver-memory 16g pyspark-shell"`).
El modo demo (sin `--config` ni `--settings`, o con `--demo`) sigue en `local[1]` con 2 particiones.
```bash
bash run.sh --config cfg.json --extract-only
BNX_DRIVER_MEMORY=16g bash run.sh --config cfg.json
```

#### Cómo leer la tabla de tiempos
Al final de cada corrida sale `TABLA DE TIEMPOS` con `master` y `applicationId`, y una fila por etapa:
`preflight` (consulta al catálogo, sin leer datos), `extract` (query + write a parquet, con particiones del
query y archivos escritos), `aggregate`, `conteo` y `kernel` (jobs del banco). La última línea dice qué fue lo más
lento. Pistas: pocas particiones con mucho tiempo = poco paralelismo (sube executors o `spark.sql.shuffle.partitions`);
muchos archivos pequeños = demasiadas particiones; `preflight` lento = problema del metastore.
Para contar filas escritas (una pasada extra, apagada por defecto): `BNX_CONTAR_FILAS=1`.
Para saltar el chequeo previo del catálogo: `BNX_PREFLIGHT=0`.

#### Cuándo SÍ hace falta Python en los workers
Estos patrones ejecutan Python **dentro de los executors** y fallan en YARN si los nodos no tienen
Python 3.11 con las mismas librerías:
- `udf`, `F.udf`, `@udf`, `pandas_udf`, `spark.udf.register(...)` con función Python
- `applyInPandas`, `mapInPandas`, `applyInPandasWithState`, `mapInArrow`
- `df.rdd`, `rdd.map / flatMap / filter / mapPartitions`, `foreach`, `foreachPartition`, `sparkContext.parallelize`
- `pyspark.pandas` / `pandas_api()`
- `xgboost.spark` / `SparkXGBClassifier`, `SparkXGBRegressor`
- sklearn / xgboost / lightgbm usados dentro de una `udf`

El portal los detecta al generar el paquete (aviso en el reporte, por archivo y línea) y `main.py` los
vuelve a avisar al arrancar en modo cluster. Qué hacer:
1. Reescribir con funciones de **Spark SQL / DataFrame** (`when`, `regexp_extract`, `expr`, ventanas...).
2. O **agregar en Spark y calcular en el driver**: `toPandas()` sobre un resultado **pequeño** y ahí usar pandas/sklearn/xgboost.
   Cuidado con la memoria: `toPandas()` trae todo al driver; agrega/filtra antes y ajusta `BNX_DRIVER_MEMORY`.
3. Último recurso (apagado por defecto): `BNX_ENVIAR_VENV=1` empaqueta el `.venv` y lo manda con `--archives`.

### Python en los executors: librerías enviadas con el job (sin instalar en los nodos)
Caso real: `PythonException ... worker.py ... cloudpickle.loads ... ModuleNotFoundError: No module named 'numpy'`. El
código del banco registra UDF (`udf.register("quita_acentos", ...)`, y las mex-lib: feature_engineering, group_by...). Esas
funciones corren en el **Python de los workers**, que no tiene las librerías del `.venv` (el venv solo lo usa el driver).
**Qué hace `run.sh` solo** (modo cluster, `BNX_DEPS_EXECUTORS=1` por defecto): si detecta Python en workers (modelo, `bank_src`
y wheels del banco; resultado en `.bnx_workers_python.json`) empaqueta **solo el site-packages** del venv (sin intérprete, sin
`pyspark`/`py4j`, sin `__pycache__`) en `.bnx_deps/bnxdeps-<hash>.tar.gz` (cacheado por hash del venv), lo envía con
`--archives <tgz>#bnxdeps` y fija `spark.executorEnv.PYTHONPATH=./bnxdeps` (antepone; conserva lo que ya fije el cluster).
Es temporal (vive en el contenedor YARN del job): **no se instala nada en los nodos**.
Solo funciona si el Python de los executors es de la **misma versión menor (3.11)** que el venv. Por eso antes hace un
**probe** (mini job en YARN, cacheado 12 h en `.bnx_tmp/probe_*.json`; `BNX_PROBE_FORZAR=1` lo repite). Si no coincide, **no corre
el job a ciegas**: imprime las opciones y sale (`BNX_PROBE_IGNORAR=1` sigue igual).
**Comandos para Angel** (en el edge, sin exportar `PYSPARK_PYTHON`):
1. `spark3-submit --master yarn --deploy-mode client probe_workers.py` (Python por defecto del cluster)
2. `spark3-submit --master yarn --deploy-mode client --conf spark.pyspark.python=/usr/bin/python3.11 probe_workers.py`
Resultado y qué hacer:
- (1) imprime versión `3.11` y `numpy=False`: todo listo, `BNX_SPARK=cluster bash run.sh ...` envía las librerías.
- (1) falla con "different version" o imprime otra versión, y (2) imprime `3.11`: usar `BNX_EXECUTOR_PYTHON=/usr/bin/python3.11 BNX_SPARK=cluster bash run.sh ...`.
- Ninguna da 3.11: preguntar a plataforma qué Python 3.11 hay en los nodos (otra ruta); o reescribir la UDF con funciones de Spark SQL
  (`quita_acentos` → `lower(translate(coalesce(c,''), 'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN'))`); plan B: `BNX_SPARK=local bash run.sh ...` en el edge.
- Desactivar todo: `BNX_DEPS_EXECUTORS=0`. Forzar el envío aunque no se detecte UDF: `BNX_DEPS_FORZAR=1`.
Si aun así falla en runtime con ese error, el framework lo traduce a "FALTA <módulo> en los EXECUTORS" (terminal, log, `BNX_FALTANTES.json`, pantalla).
**Librerías UNA vez en HDFS (Cloudera YARN, mismas versiones en todos los nodos):** con `BNX_DEPS_HDFS=<carpeta hdfs>` `run.sh` sube el
`.tgz` a `<carpeta>/bnxdeps_<hash12>.tgz` (hash del venv) solo si no existe (`hdfs dfs -test -e`; si falta: `-mkdir -p` y `-put`, permisos 644)
y usa `--archives hdfs://.../bnxdeps_<hash>.tgz#bnxdeps`. YARN lo localiza en cada contenedor: **todos los nodos reciben el mismo archivo**, no se
sube desde el edge en cada corrida y no se instala nada. Log: `[run.sh] librerias de executors: hdfs:///.../bnxdeps_<hash>.tgz (reutilizado|subido ahora, N MB)`.
Si `hdfs` no está en el PATH o el `put` falla, avisa y envía desde el edge como antes. Comando recomendado:
`BNX_SPARK=cluster BNX_DEPS_HDFS=hdfs:///user/<usuario>/bnx/deps bash run.sh --settings ... --env ... --source <job>`
Si el venv cambia, se sube otra versión (otro hash). Para borrar las viejas: `BNX_DEPS_HDFS=hdfs:///user/<usuario>/bnx/deps bash run.sh --limpiar-deps-hdfs`
(lista y pide confirmación en terminal; conserva la del venv actual).
**Qué UDF pedía numpy en el caso de RPS:** `rmeans` de la mex-lib *feature engineering* (`base_features.py` /
`feature_engineering_standard.py`: `np.mean(x)`), activada por `"rmeans"` en `config_custom.json`. cloudpickle manda la
función por valor y en el worker importa sus globales (`np`). `quita_acentos` (data_pull) pediría `unidecode`, no numpy.
El error salió del `worker.py` del executor, que antes de leer la UDF ya validó que su Python es de la misma versión menor que
el driver: lo más probable es que el probe salga bien y baste con enviar el site-packages.
**UDF nativas (`BNX_UDF_NATIVAS=1`; run.sh lo activa solo si el probe dice que el Python de los executors no sirve):**
`bank_compat` intercepta `udf.register` / `F.udf` / `@udf` y, si el cuerpo de la función es simple (if/return,
asignaciones, aritmética, comparaciones, `x[i]`, `np.mean/sum/min/max` sobre arrays, `[v for v in x if ...]`, `len`,
`float/int`, `lower/upper/strip/replace`, `unidecode(x)`), NO registra la UDF de Python: la cambia por una expresión nativa de
Spark (`translate`, `aggregate`, `filter`, `CASE WHEN`...). En SQL (`spark.sql`, `selectExpr`, `expr`, `filter('...')`) se
reescribe el texto; vía DataFrame devuelve un `Column`. No se toca el código del banco. En el log:
`[compat] UDF quita_acentos -> expresion nativa Spark (translate/lower), sin Python en los workers` y en `BNX_FALTANTES.json`
como PARCHEADO (no validado). Se cambian `quita_acentos`, `rmeans`, `rt_mod`, `df_mod`; `incremental` (bucle) se queda en
Python (no usa numpy). Diferencias: `unidecode` translitera todo Unicode (emojis, griego, cirílico, `€`→`EUR`); la versión
nativa solo quita diacríticos latinos (Latin-1, Latin Extended-A/B, ß/æ/œ/ø/ł...). Errores de Python (índice fuera de rango,
división entre 0) siguen la regla de Spark (`spark.sql.ansi.enabled`: error o NULL).
   Aun así los nodos necesitan `python3.11` en la misma ruta que el edge node. Solo para quien lo necesite.

Ejemplo de ejecución local (para probar sin cluster): `bash run.sh --config cfg.json --extract-only`.
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
# IMPORTANTE:
# - incluir main.py: el handler importa `from main import parse_project`.
#   Sin main.py la Lambda arranca con Runtime.ImportModuleError: No module named 'main'.
# - incluir bnx_library/ (sin Repo_Git): son los grafos que /library sirve como
#   FALLBACK cuando el S3 de DataLab esta bloqueado cross-account. Sin ellos, la
#   biblioteca en la nube (Amplify) sale vacia. bnx_library/ esta en .gitignore
#   pero el zip se arma desde disco, asi que igual se incluye.
zip -r lambda_package.zip lambda/handler.py main.py src/ -x "src/__pycache__/*" "src/**/__pycache__/*" "**/__pycache__/*"
zip -r lambda_package.zip bnx_library/ -x "bnx_library/Repo_Git/*" "bnx_library/_flat/*" "**/.DS_Store"
aws lambda update-function-code --function-name bnx-compiler --zip-file fileb://lambda_package.zip --region us-east-1 --profile default
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

## 📚 Biblioteca de grafos (local + S3)

Los grafos de la pestaña **Grafos** (endpoint `/library`) se guardan en **dos
lugares a la vez**:

1. **Local** — `./bnx_library/` en disco. Es la **fuente de verdad** y el
   **fallback**: siempre se escribe aquí primero, aunque S3 no esté disponible.
   (`bnx_library/` está en `.gitignore`; los grafos no viajan por git.)
2. **S3** — se sube además a un bucket, *best-effort*. Si S3 falla (sin
   credenciales, sin red, sin `boto3`/AWS CLI), el guardado local no se ve
   afectado y la UI sigue funcionando.

El flujo cubre `save` / `upload` (suben a S3) y `delete` (borra en local **y**
S3). Al arrancar, el servidor hace una **sincronización bidireccional** de la
biblioteca:

1. **Baja** de S3 lo que falte en local (descarga incremental).
2. **Sube** a S3 lo que falte en el bucket (push incremental de lo que ya tenías
   en disco).

Ninguna dirección borra: la unión local + S3 **solo crece**. Así cada máquina
aporta sus grafos al bucket y recibe los de las demás — nunca se pierden grafos.
La sincronización **siempre se intenta al arrancar** el server (bajada + subida);
si falla, se reintenta a los 30 s, 2 min y 5 min. Además corre cada
`BNX_LIBRARY_SYNC_EVERY` minutos (default 10; `0` lo apaga) y bajo demanda con el
botón **🔄 Sincronizar** de la página de Grafos, que muestra el resultado o el
motivo del fallo.

### Configuración (variables de entorno)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `BNX_AWS_PROFILE` | `monkeyapp` | Perfil de `~/.aws` para acceder a S3 |
| `BNX_S3_BUCKET` | `bnx-e2e-test` | Bucket donde viven los grafos |
| `BNX_S3_PREFIX` | `library/` | Prefijo (carpeta) dentro del bucket |
| `BNX_LIBRARY_SYNC_EVERY` | `10` | Minutos entre sincronizaciones periódicas (`0` = apagado). La de arranque siempre se hace |

Por defecto apunta a la cuenta **monkey** (`034711235858`), bucket
`s3://bnx-e2e-test/library/`, perfil `monkeyapp`. Para usar otra cuenta/bucket,
exporta las variables antes de arrancar `serve_ui.py`:

```bash
export BNX_AWS_PROFILE=otro_perfil
export BNX_S3_BUCKET=mi-bucket
export BNX_S3_PREFIX=grafos/
python serve_ui.py
```

### Acceso a S3

El upload usa **`boto3`** si está instalado; si no, cae a **AWS CLI** (`aws s3
cp`/`rm`). Basta con tener uno de los dos y credenciales válidas para el perfil
configurado. `boto3` es opcional (`requirements.txt` lo lista como tal); el
guardado local nunca depende de S3.

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
