import { useMemo, useEffect, useState } from 'react'
import ReactFlow, {
  Background, Controls, MiniMap,
  MarkerType, useNodesState, useEdgesState
} from 'reactflow'
import 'reactflow/dist/style.css'

const GLOSSARY = {
  DAG_BUILDER: {
    concepts: [
      { term: 'DAG', def: 'Directed Acyclic Graph — grafo dirigido sin ciclos. Cada nodo es una operación y cada edge es una dependencia. Garantiza que los datos fluyen en una sola dirección.' },
      { term: 'Topological Sort', def: 'Algoritmo que ordena los nodos del DAG de forma que cada nodo se procesa después de todos sus padres. Es lo que determina el orden de ejecución del pipeline.' },
      { term: 'Subgraph', def: 'Grupo de nodos relacionados dentro del DAG. Equivalente a un "sub-job" en Ab Initio. Permite organizar pipelines complejos en módulos.' },
      { term: 'Mega-DAG', def: 'DAG unificado construido a partir de múltiples grafos (.mp) referenciados por un PLAN. Cada grafo se convierte en un subgraph con namespacing para evitar colisiones de nombres.' },
      { term: 'Cross-Graph Edge', def: 'Conexión entre grafos en un Mega-DAG. Conecta el SINK de un grafo con el SOURCE del siguiente. Se visualiza como línea dashed púrpura.' },
    ]
  },
  MP_FILE: {
    concepts: [
      { term: 'Graph (.mp)', def: 'Archivo que define la estructura del pipeline. Usa formato declarativo: NODE X : TYPE para nodos, A -> B para edges, SUBGRAPH { } para agrupaciones.' },
      { term: 'SOURCE', def: 'Nodo de lectura de datos. Soporta S3 (CSV/Parquet/JSON), Kafka (streaming), JDBC (bases de datos). Equivale a Read en Ab Initio.' },
      { term: 'TRANSFORM', def: 'Nodo de transformación. Aplica SELECT, WHERE, GROUP BY según las reglas XFR. Equivale a Reformat/Rollup en Ab Initio.' },
      { term: 'JOIN', def: 'Combina dos o más datasets por una key. Soporta INNER, LEFT, RIGHT. Equivale a Join en Ab Initio.' },
      { term: 'DEDUP', def: 'Elimina registros duplicados por key. Usa ROW_NUMBER() con ORDER BY para mantener el más reciente. Equivale a Dedup Sort en Ab Initio.' },
      { term: 'NORMALIZE', def: 'Expande un registro en múltiples filas. Usa EXPLODE para arrays o SPLIT para strings. Equivale a Normalize en Ab Initio.' },
      { term: 'LOOKUP', def: 'Enriquece datos con una tabla de referencia usando broadcast join (LEFT JOIN). Equivale a Lookup en Ab Initio.' },
      { term: 'CONCATENATE', def: 'Une múltiples datasets sin key (UNION ALL). Equivale a Concatenate en Ab Initio.' },
      { term: 'GATHER', def: 'Merge múltiples streams en uno. Similar a Concatenate pero para streams. Equivale a Gather en Ab Initio.' },
      { term: 'PARTITION', def: 'Reparticiona datos por key a N particiones. Optimiza el paralelismo. Equivale a Partition by Key en Ab Initio.' },
      { term: 'FILTER', def: 'Filtra datos con condición WHERE. Tiene dos puertos de salida: datos que pasan y datos rechazados. Equivale a Filter by Expression en Ab Initio.' },
      { term: 'SINK', def: 'Nodo de escritura final. Soporta S3, Kafka, JDBC. Equivale a Write en Ab Initio.' },
    ]
  },
  XFR_FILE: {
    concepts: [
      { term: 'XFR (Transform Rules)', def: 'Archivo que define la lógica de cada nodo. Inspirado en Ab Initio Transform functions. Cada nodo tiene su bloque con select, where, group_by, join_key, etc.' },
      { term: 'Reformat', def: 'En Ab Initio, un componente que transforma campos. En BNX equivale a selectExpr() de Spark o SELECT en Flink SQL.' },
      { term: 'Rollup', def: 'En Ab Initio, un componente que agrega datos con GROUP BY. En BNX se traduce a groupBy().agg() en Spark o GROUP BY en Flink SQL.' },
      { term: 'PSET Substitution', def: 'Los archivos XFR pueden contener ${PARAM} que se reemplazan con valores del PSET. Permite parametrizar paths, conexiones y thresholds.' },
    ]
  },
  DML_FILE: {
    concepts: [
      { term: 'DML (Data Manipulation Language)', def: 'En Ab Initio, define el schema de los datos. En BNX define keys y tipos por tabla. Se usa para validación semántica.' },
      { term: 'Schema Inference', def: 'El validador propaga las columnas a través del DAG usando el DML como fuente de verdad para los SOURCE nodes.' },
    ]
  },
  COBOL_FILE: {
    concepts: [
      { term: 'COBOL', def: 'Lenguaje de programación de 1959, aún usado en mainframes bancarios. Los programas batch procesan archivos secuenciales con lógica de negocio.' },
      { term: 'EBCDIC', def: 'Extended Binary Coded Decimal Interchange Code — encoding de IBM mainframes. Diferente de ASCII/UTF-8. BNX detecta y convierte automáticamente.' },
      { term: 'COMP-3 (Packed Decimal)', def: 'Formato numérico de mainframe que empaqueta 2 dígitos por byte. BNX lo mapea a Spark DecimalType.' },
      { term: 'Copybook', def: 'Archivo COBOL reutilizable que define la estructura de un registro. Equivalente a un schema/DML.' },
    ]
  },
  MP_PARSER: {
    concepts: [
      { term: 'AST (Abstract Syntax Tree)', def: 'Representación intermedia del grafo parseado. Contiene nodes (id, name, type), edges (from, to), y subgraphs. Es la entrada del DAG Builder.' },
      { term: 'Namespacing', def: 'En Mega-DAG, cada nodo se prefija con el nombre del grafo (ej: ingest__ReadCSV) para evitar colisiones entre grafos que tienen nodos con el mismo nombre.' },
    ]
  },
  COBOL_PARSER: {
    concepts: [
      { term: 'FILE SECTION', def: 'Sección COBOL que define los archivos de entrada/salida. BNX la parsea para crear nodos SOURCE y SINK.' },
      { term: 'PROCEDURE DIVISION', def: 'Sección COBOL con la lógica de negocio. BNX detecta READ, WRITE, IF, PERFORM, COMPUTE para crear nodos TRANSFORM.' },
    ]
  },
  VALIDATOR: {
    concepts: [
      { term: 'Semantic Validation', def: 'Verifica que el grafo es ejecutable antes de generar código. Detecta: join keys que no existen en los padres, nodos sin padre, columnas perdidas por groupBy.' },
      { term: 'Column Inference', def: 'Propaga las columnas disponibles a través del DAG. Un groupBy reduce las columnas a las keys + aliases. Un join las combina.' },
      { term: 'Cross-Graph Validation', def: 'En Mega-DAG, valida que los cross-graph edges conectan nodos que existen en los grafos correctos y que los retrocesos son SINK→SOURCE entre grafos distintos.' },
    ]
  },
  ACCURACY: {
    concepts: [
      { term: 'Accuracy', def: 'Métrica que mide qué tan completa es la traducción del grafo al código. Evalúa: nodos resueltos, edges válidos, transforms con regla, joins con key.' },
      { term: 'Fórmula', def: 'Overall = Nodes×30% + Edges×20% + Transforms×30% + Joins×20%. 90%+ = producción, 70-89% = ajustes, <70% = faltan reglas.' },
    ]
  },
  GLUE_CODEGEN: {
    concepts: [
      { term: 'AWS Glue', def: 'Servicio serverless de ETL de AWS. Usa Apache Spark internamente. GlueContext extiende SparkContext con integración a S3, Glue Catalog, etc.' },
      { term: 'Codegen', def: 'Generación automática de código. BNX traduce cada nodo del DAG a una línea de PySpark válida según su tipo y reglas XFR.' },
      { term: 'Graph Boundaries', def: 'En Mega-DAG, el código generado incluye comentarios # === GRAPH: nombre === para marcar dónde empieza cada grafo.' },
    ]
  },
  SPARK_CODEGEN: {
    concepts: [
      { term: 'PySpark', def: 'API de Python para Apache Spark. Permite procesamiento distribuido de datos. BNX genera código PySpark puro sin dependencias de AWS.' },
      { term: 'SparkSession', def: 'Punto de entrada de Spark. Reemplaza a SparkContext + SQLContext. Permite leer/escribir datos y ejecutar SQL.' },
    ]
  },
  SF_CODEGEN: {
    concepts: [
      { term: 'Step Functions', def: 'Servicio de orquestación serverless de AWS. Define workflows como máquinas de estado JSON. Ejecuta Glue jobs en secuencia o paralelo.' },
      { term: 'State Machine', def: 'Modelo de ejecución donde cada estado es una tarea (Glue job) y las transiciones son las dependencias del DAG.' },
    ]
  },
  TF_CODEGEN: {
    concepts: [
      { term: 'Terraform', def: 'Herramienta de Infrastructure as Code (IaC) de HashiCorp. Define recursos AWS en archivos .tf declarativos. BNX genera S3, IAM, Glue jobs, CloudWatch.' },
      { term: 'IaC', def: 'Infrastructure as Code — definir infraestructura en archivos versionables en vez de configurar manualmente en la consola.' },
    ]
  },
  AF_CODEGEN: {
    concepts: [
      { term: 'Apache Airflow', def: 'Plataforma de orquestación de workflows. Define DAGs en Python con operadores para cada servicio (Glue, S3, etc.). Alternativa open-source a Step Functions.' },
      { term: 'MWAA', def: 'Amazon Managed Workflows for Apache Airflow — Airflow managed en AWS. No necesitas administrar servidores.' },
    ]
  },
  LAMBDA: {
    concepts: [
      { term: 'AWS Lambda', def: 'Servicio serverless que ejecuta código sin servidores. Cobra por invocación (~$0.20/1M requests). Ideal para APIs stateless como BNX.' },
      { term: 'Function URL', def: 'Endpoint HTTP directo para Lambda sin necesidad de API Gateway. Más simple y barato para APIs públicas.' },
    ]
  },
  AMPLIFY: {
    concepts: [
      { term: 'AWS Amplify', def: 'Servicio de hosting para apps web estáticas. Conecta a Git, hace build automático, sirve via CDN global. Free tier: 5GB/mes.' },
    ]
  },
  DESIGNER_UI: {
    concepts: [
      { term: 'ReactFlow', def: 'Librería React para crear editores de grafos interactivos. Soporta drag & drop, zoom, minimap, custom nodes. Es lo que usa el Designer y el DAG Viewer.' },
    ]
  },
  FASTAPI: {
    concepts: [
      { term: 'FastAPI', def: 'Framework Python para APIs REST. Async, validación automática con Pydantic, documentación OpenAPI. Se usa para desarrollo local.' },
      { term: 'Multipart Upload', def: 'Los archivos .mp/.xfr/.dml se envían como multipart/form-data. Permite subir múltiples archivos en un solo request.' },
    ]
  },
  COMPILER_UI: {
    concepts: [
      { term: 'Grafo de Grafos', def: 'Funcionalidad que permite subir múltiples .mp junto con un .plan. El sistema los combina en un Mega-DAG unificado con cross-graph edges.' },
      { term: 'Target Selector', def: 'Permite elegir entre Glue, PySpark y Flink como target de generación de código. El mismo grafo genera código diferente según el target.' },
    ]
  },
  XFR_PARSER: {
    concepts: [
      { term: 'Rule Matching', def: 'Las reglas XFR se asocian a nodos por nombre (case-insensitive). Cada nodo busca su regla en el dict de XFR rules.' },
    ]
  },
  DML_PARSER: {
    concepts: [
      { term: 'Type Mapping', def: 'Mapea tipos COBOL PIC a Spark: PIC 9 → IntegerType, PIC X → StringType, PIC S9V9 → DecimalType, COMP-3 → DecimalType.' },
    ]
  },
}

// Mecanismos del convertidor — sección de glosario general
const MECHANISMS = [
  {
    category: '📥 Entrada',
    items: [
      { name: 'Compilación .mp + .xfr + .dml', desc: 'Flujo principal: sube un grafo (.mp), reglas de transformación (.xfr) y schema (.dml). El sistema parsea, valida y genera código ejecutable.' },
      { name: 'Conversión COBOL', desc: 'Sube un archivo .cbl y el sistema detecta FILE SECTION, PROCEDURE DIVISION, EBCDIC/COMP-3. Genera automáticamente .mp + .xfr + .dml y compila.' },
      { name: 'Conversión Ab Initio PLAN', desc: 'Sube PSET (parámetros) + XFR (lógica) + PLAN (orquestación). El sistema genera el grafo desde las definiciones del PLAN.' },
      { name: 'Grafo de Grafos (Multi-MP)', desc: 'Sube múltiples .mp junto con un .plan. Cada .mp es un componente independiente. El PLAN define las dependencias entre ellos y se combinan en un Mega-DAG.' },
    ]
  },
  {
    category: '⚙️ Procesamiento',
    items: [
      { name: 'Parsing', desc: 'Cada tipo de archivo tiene su parser: mp_parser (grafos), xfr_parser (reglas), dml_parser (schema), cobol_parser (COBOL), plan_parser (PLAN/PSET).' },
      { name: 'Namespacing', desc: 'En Mega-DAG, cada nodo se prefija con el nombre del grafo (ej: ingest__ReadCSV) para evitar colisiones entre grafos con nodos del mismo nombre.' },
      { name: 'DAG Builder', desc: 'Construye el grafo dirigido acíclico con topological sort. Determina el orden de ejecución respetando las dependencias padre→hijo.' },
      { name: 'Validación Semántica', desc: 'Verifica que el grafo es ejecutable: join keys existen en los padres, nodos tienen padre, columnas referenciadas existen. Propaga schema a través del DAG.' },
      { name: 'Accuracy Engine', desc: 'Mide qué tan completa es la traducción: nodos resueltos, edges válidos, transforms con regla, joins con key. Fórmula ponderada para overall accuracy.' },
    ]
  },
  {
    category: '🔧 Generación de Código',
    items: [
      { name: 'AWS Glue (PySpark + GlueContext)', desc: 'Genera jobs para AWS Glue con GlueContext, spark.read/write, groupBy/agg, join, dropDuplicates. Soporta S3, Kafka, JDBC.' },
      { name: 'PySpark (SparkSession)', desc: 'Genera código PySpark puro sin dependencias AWS. Mismo patrón que Glue pero con SparkSession directamente.' },
      { name: 'Apache Flink (PyFlink + Flink SQL)', desc: 'Genera código PyFlink con StreamTableEnvironment. Usa CREATE TABLE para conectores y CREATE TEMPORARY VIEW para transformaciones SQL.' },
      { name: 'Step Functions (JSON)', desc: 'Genera workflow AWS Step Functions como máquina de estados JSON. Agrupa nodos por profundidad para ejecución paralela.' },
      { name: 'Terraform (.tf)', desc: 'Genera infraestructura como código: S3 buckets, IAM roles, Glue jobs, CloudWatch alarms. Listo para terraform apply.' },
      { name: 'Airflow (Python DAG)', desc: 'Genera DAG de Apache Airflow con GlueJobOperator. Incluye dependencias, retry, schedule. Compatible con MWAA.' },
    ]
  },
  {
    category: '🔄 Planes Cíclicos',
    items: [
      { name: 'Retrocesos (Feedback Loops)', desc: 'Cuando un grafo posterior alimenta datos de vuelta a uno anterior. Se detectan automáticamente por ciclos en las dependencias del PLAN. Se visualizan como edges rojos dashed animados en el DAG.' },
      { name: 'SCHEDULE: CYCLIC', desc: 'Directiva en el PLAN que marca un grafo como cíclico. Genera un loop de iteraciones en el código con checkpoint/staging entre cada iteración. El grafo se re-ejecuta hasta cumplir la condición de parada.' },
      { name: 'MAX_ITERATIONS', desc: 'Límite de seguridad para planes cíclicos. Se define en el PLAN o PSET. El loop se ejecuta máximo N veces. Previene loops infinitos si la convergencia no se alcanza.' },
      { name: 'CONVERGENCE', desc: 'Condición de parada para planes cíclicos (ej: delta < 0.01). Cuando se cumple, el loop termina antes de MAX_ITERATIONS. Se evalúa al final de cada iteración.' },
    ]
  },
  {
    category: '🌐 Conectores',
    items: [
      { name: 'S3 / Filesystem', desc: 'Lee/escribe archivos en S3 o filesystem local. Soporta CSV (con headers), Parquet, JSON, Avro. Es el conector por defecto.' },
      { name: 'Apache Kafka', desc: 'Lee/escribe streams de Kafka. En Glue/Spark usa readStream, en Flink usa conector nativo. Ideal para pipelines de streaming.' },
      { name: 'JDBC (Bases de datos)', desc: 'Lee/escribe a bases de datos via JDBC. Soporta MySQL, PostgreSQL, Oracle, SQL Server. Configurable con connection string y tabla.' },
    ]
  },
  {
    category: '🔗 Grafo de Grafos (Mega-DAG)',
    items: [
      { name: 'Concepto', desc: 'Un PLAN puede referenciar múltiples archivos .mp externos. Cada .mp es un componente/grafo independiente con sus propios nodos y transformaciones. El PLAN define las dependencias entre ellos.' },
      { name: 'Namespacing', desc: 'Cada nodo se prefija con el nombre del grafo (ej: ingest__ReadCSV, enrich__EnrichJoin) para evitar colisiones cuando dos grafos tienen nodos con el mismo nombre.' },
      { name: 'Cross-Graph Edges', desc: 'Conexiones automáticas entre grafos. Cuando el grafo B depende del grafo A, el sistema conecta los SINK de A con los SOURCE de B. Se visualizan como líneas dashed púrpura.' },
      { name: 'Merge de ASTs', desc: 'Todos los grafos individuales se combinan en un único AST unificado. Los nodos se namespacean, los edges intra-grafo se preservan, y se crean cross-graph edges según las dependencias del PLAN.' },
      { name: 'Flujo de Upload', desc: 'En la UI: 1° PSET (parámetros), 2° XFR (lógica), 3° MP files (grafos externos), 4° PLAN (orquestación). Al subir el PLAN se compila automáticamente el Mega-DAG completo.' },
      { name: 'Código Unificado', desc: 'El Mega-DAG genera un solo archivo de código (Glue/Spark/Flink) con comentarios # === GRAPH: nombre === marcando las fronteras entre grafos. Se ejecuta como un solo job.' },
    ]
  },
  {
    category: '📄 Archivos del Sistema',
    items: [
      { name: '.mp (Graph)', desc: 'Define la estructura del pipeline. Formato: NODE X : TYPE para nodos, A -> B para edges, SUBGRAPH nombre { } para agrupaciones. Es el archivo principal de entrada.' },
      { name: '.xfr (Transform Rules)', desc: 'Define la lógica de cada nodo. Formato YAML-like: NombreNodo: seguido de directivas (select, where, group_by, join_key, source_type, sink_type, path, format, etc.).' },
      { name: '.dml (Schema)', desc: 'Define el schema de datos. Sección keys: (key por tabla) y schema: (columnas con tipos). Se usa para validación semántica y column inference.' },
      { name: '.plan (PLAN)', desc: 'Orquestación de grafos. Define GRAPH con propiedades: MP (archivo .mp), XFR, DML, DEPENDS (dependencias), SCHEDULE, PRIORITY, MAX_ITERATIONS, CONVERGENCE, ON_SUCCESS, ON_FAILURE.' },
      { name: '.pset (Parameters)', desc: 'Parámetros runtime en formato KEY = VALUE. Se sustituyen en archivos XFR como ${PARAM}. Incluye paths S3, conexiones Kafka/JDBC, MAX_ITERATIONS, CONVERGENCE, etc.' },
      { name: '.cbl (COBOL)', desc: 'Código COBOL legacy. El parser detecta FILE SECTION (archivos I/O), PROCEDURE DIVISION (lógica), PIC types, COMP-3/EBCDIC. Genera automáticamente .mp + .xfr + .dml.' },
      { name: 'Código Generado (.py)', desc: 'Archivo Python generado por el codegen. Según el target: Glue (GlueContext + PySpark), Spark (SparkSession + PySpark), o Flink (StreamTableEnvironment + Flink SQL).' },
      { name: 'Step Functions (.json)', desc: 'Workflow AWS Step Functions como máquina de estados JSON. Cada fase del DAG es un estado Task o Parallel. Listo para deploy en AWS.' },
      { name: 'Terraform (.tf)', desc: 'Infraestructura como código. Genera S3 buckets (raw/curated/scripts/logs), IAM roles, Glue jobs, CloudWatch alarms. Listo para terraform apply.' },
      { name: 'Airflow DAG (.py)', desc: 'DAG de Apache Airflow con GlueJobOperator por nodo. Incluye dependencias, retry, schedule diario. Compatible con MWAA (Managed Airflow en AWS).' },
    ]
  },
  {
    category: '☁️ Despliegue',
    items: [
      { name: 'AWS Lambda + Function URL', desc: 'Backend serverless. El compilador corre en Lambda con Function URL pública. Sin servidores, pago por uso (~$5/mes).' },
      { name: 'AWS Amplify', desc: 'Frontend React hospedado en Amplify. Auto-deploy desde Git, CDN global, dominio custom. Free tier: 5GB/mes.' },
    ]
  },
  {
    category: '🎯 Tipos de Nodo (Legend)',
    color: true,
    items: [
      { name: 'SOURCE', color: '#22c55e', desc: 'Lectura de datos. Lee desde S3 (CSV/Parquet/JSON), Kafka (streaming) o JDBC (bases de datos). En Glue/Spark: spark.read.format(). En Flink: CREATE TABLE con conector. Equivale a Read/Scan en Ab Initio.' },
      { name: 'TRANSFORM', color: '#6366f1', desc: 'Transformación de datos. Aplica SELECT (columnas), WHERE (filtro), GROUP BY (agregación). En Glue/Spark: selectExpr(), where(), groupBy().agg(). En Flink: CREATE TEMPORARY VIEW con SQL. Equivale a Reformat/Rollup en Ab Initio.' },
      { name: 'JOIN', color: '#f59e0b', desc: 'Combina dos o más datasets por una key. Soporta INNER, LEFT, RIGHT, FULL. En Glue/Spark: df1.join(df2, on=key). En Flink: SQL JOIN ... ON. Soporta joins encadenados para 3+ padres. Equivale a Join en Ab Initio.' },
      { name: 'DEDUP', color: '#06b6d4', desc: 'Elimina registros duplicados por key. Usa ROW_NUMBER() OVER (PARTITION BY keys ORDER BY col DESC) para mantener el más reciente. En Spark: Window + row_number. En Flink: ROW_NUMBER() en SQL. Equivale a Dedup Sort en Ab Initio.' },
      { name: 'NORMALIZE', color: '#a855f7', desc: 'Expande un registro en múltiples filas. Dos modos: EXPLODE (array → filas) y SPLIT (string con delimiter → filas). En Spark: explode(col()). En Flink: CROSS JOIN UNNEST. Equivale a Normalize en Ab Initio.' },
      { name: 'LOOKUP', color: '#ec4899', desc: 'Enriquece datos con tabla de referencia usando broadcast LEFT JOIN. El primer padre es el dataset principal, el segundo es la referencia. En Spark: broadcast(). En Flink: LEFT JOIN. Equivale a Lookup en Ab Initio.' },
      { name: 'CONCATENATE', color: '#14b8a6', desc: 'Une múltiples datasets sin key (UNION ALL). Los datasets no necesitan tener el mismo schema — usa allowMissingColumns. En Spark: unionByName(). En Flink: UNION ALL. Equivale a Concatenate en Ab Initio.' },
      { name: 'GATHER', color: '#8b5cf6', desc: 'Merge múltiples streams en uno. Funcionalmente igual a CONCATENATE pero semánticamente indica merge de streams paralelos. En Spark: unionByName(). En Flink: UNION ALL. Equivale a Gather en Ab Initio.' },
      { name: 'PARTITION', color: '#f97316', desc: 'Reparticiona datos por key a N particiones. Optimiza el paralelismo distribuyendo datos por hash de la key. En Spark: repartition(N, key). En Flink: configuración de parallelism. Equivale a Partition by Key en Ab Initio.' },
      { name: 'FILTER', color: '#eab308', desc: 'Filtra datos con condición WHERE. Tiene DOS puertos de salida: datos que pasan el filtro y datos rechazados (NOT WHERE). En Spark: where() + where(NOT). En Flink: dos CREATE TEMPORARY VIEW. Equivale a Filter by Expression en Ab Initio.' },
      { name: 'SINK', color: '#ef4444', desc: 'Escritura final de datos. Escribe a S3 (Parquet/CSV/JSON), Kafka (streaming) o JDBC (bases de datos). Soporta mode overwrite/append. En Glue/Spark: df.write.format(). En Flink: INSERT INTO tabla_sink. Equivale a Write en Ab Initio.' },
    ]
  },
]

const COMPONENTS = [
  // Input Layer
  { id: 'MP_FILE', label: '.mp File\n(Graph)', x: 0, y: 0, group: 'input', desc: 'Define nodos (SOURCE, TRANSFORM, JOIN, DEDUP, NORMALIZE, LOOKUP, SINK), edges y subgraphs del pipeline' },
  { id: 'XFR_FILE', label: '.xfr File\n(Rules)', x: 0, y: 100, group: 'input', desc: 'Reglas de transformación: SELECT, WHERE, GROUP BY, join_key, dedup_keys, explode_col, source_type, etc.' },
  { id: 'DML_FILE', label: '.dml File\n(Schema)', x: 0, y: 200, group: 'input', desc: 'Schema de datos: keys por tabla y tipos de columna (string, double, int, timestamp)' },
  { id: 'COBOL_FILE', label: '.cbl File\n(COBOL)', x: 0, y: 300, group: 'input', desc: 'Código COBOL legacy con FILE SECTION, PROCEDURE DIVISION, PIC types, COMP-3/EBCDIC' },

  // Parsers
  { id: 'MP_PARSER', label: 'MP Parser\n(mp_parser.py)', x: 220, y: 0, group: 'parser', desc: 'Parsea NODE/SUBGRAPH/edges. Soporta formatos: NODE X : TYPE, A -> B, SUBGRAPH { }' },
  { id: 'XFR_PARSER', label: 'XFR Parser\n(xfr_parser.py)', x: 220, y: 100, group: 'parser', desc: 'Parsea select/where/group_by/join_key/dedup_keys/explode_col/source_type/sink_type' },
  { id: 'DML_PARSER', label: 'DML Parser\n(dml_parser.py)', x: 220, y: 200, group: 'parser', desc: 'Parsea keys y schema YAML-like. Mapea tipos COBOL PIC a Spark types' },
  { id: 'COBOL_PARSER', label: 'COBOL Parser\n(cobol_parser.py)', x: 220, y: 300, group: 'parser', desc: 'Parsea FILE SECTION, PROCEDURE DIVISION, IF/PERFORM. Detecta EBCDIC (cp500/cp1047). Genera .mp/.xfr/.dml' },

  // Core Engine
  { id: 'DAG_BUILDER', label: 'DAG Builder\n(dag/builder.py)', x: 440, y: 50, group: 'core', desc: 'Construye el DAG con nodos y edges. Topological sort con detección de ciclos. Maneja parents/children' },
  { id: 'VALIDATOR', label: 'Semantic Validator\n(validator/semantic.py)', x: 440, y: 150, group: 'core', desc: 'Infiere columnas por nodo. Valida join keys, nodos huérfanos, DEDUP/NORMALIZE/LOOKUP. Propaga schema del DML' },
  { id: 'ACCURACY', label: 'Accuracy Engine\n(accuracy.py)', x: 440, y: 250, group: 'core', desc: 'Mide cobertura: nodes, edges, transforms, joins. Calcula overall accuracy ponderado' },

  // Code Generation
  { id: 'GLUE_CODEGEN', label: 'Glue Codegen\n(glue_codegen.py)', x: 660, y: 20, group: 'codegen', desc: 'Genera AWS Glue jobs con GlueContext. Soporta 7 tipos de nodo + S3/JDBC/Kafka sources/sinks' },
  { id: 'SPARK_CODEGEN', label: 'PySpark Codegen\n(spark_codegen.py)', x: 660, y: 100, group: 'codegen', desc: 'Genera PySpark puro con SparkSession. Misma lógica que Glue pero sin dependencias AWS' },
  { id: 'SF_CODEGEN', label: 'Step Functions\n(stepfunctions.py)', x: 660, y: 180, group: 'codegen', desc: 'Genera AWS Step Functions JSON. Orquesta Glue jobs con fases paralelas y dependencias' },
  { id: 'TF_CODEGEN', label: 'Terraform\n(terraform.py)', x: 660, y: 260, group: 'codegen', desc: 'Genera Terraform .tf con S3 buckets, IAM roles, Glue jobs, CloudWatch. Infraestructura como código' },
  { id: 'AF_CODEGEN', label: 'Airflow DAG\n(airflow.py)', x: 660, y: 340, group: 'codegen', desc: 'Genera Apache Airflow DAG con GlueJobOperator. Orquestación alternativa a Step Functions' },

  // API Layer
  { id: 'FASTAPI', label: 'FastAPI Server\n(api/server.py)', x: 660, y: 280, group: 'api', desc: 'Endpoints: POST /compile (mp+xfr+dml), POST /cobol. Multipart upload, target selector' },
  { id: 'LAMBDA', label: 'AWS Lambda\n(lambda/handler.py)', x: 660, y: 370, group: 'api', desc: 'Handler serverless. Parsea multipart, rutas /compile y /cobol. Function URL con CORS' },

  // UI Layer
  { id: 'COMPILER_UI', label: '🔧 Compiler\n(App.jsx)', x: 900, y: 0, group: 'ui', desc: 'Upload .mp/.xfr/.dml, selecciona target Glue/Spark, visualiza DAG con ReactFlow, descarga código' },
  { id: 'DESIGNER_UI', label: '🎨 Designer\n(DesignerPage.jsx)', x: 900, y: 80, group: 'ui', desc: 'Editor visual drag & drop. Agrega nodos, conecta edges, edita reglas por nodo, compila y genera código' },
  { id: 'BANKING_UI', label: '🏦 Banking Model\n(BankingModelPage.jsx)', x: 900, y: 160, group: 'ui', desc: 'Modelo operativo bancario con 6 capas AWS. Editable, versionable, exportable' },
  { id: 'GOVERNANCE_UI', label: '🏛️ Governance\n(GovernancePage.jsx)', x: 900, y: 240, group: 'ui', desc: '8 dominios, 55+ políticas. Editable, notas custom, mapa de burbujas, export Report/JSON' },
  { id: 'METRICS_UI', label: '📊 Metrics\n(MetricsPage.jsx)', x: 900, y: 320, group: 'ui', desc: 'Horas-hombre, estimación 40K jobs, infraestructura, timeline, metodología de cálculo' },
  { id: 'ARCHITECTURE_UI', label: '🏗️ Architecture\n(ArchitecturePage.jsx)', x: 900, y: 400, group: 'ui', desc: 'Esta página — diagrama interactivo de la arquitectura del sistema BNX' },

  // Deploy
  { id: 'AMPLIFY', label: '☁️ AWS Amplify\n(Static Hosting)', x: 1120, y: 100, group: 'deploy', desc: 'Hosting del React build. CDN, dominio custom, auto-deploy desde Git' },
  { id: 'LAMBDA_DEPLOY', label: '⚡ Lambda URL\n(Serverless API)', x: 1120, y: 250, group: 'deploy', desc: 'Function URL pública. 256MB, Python 3.11, ~$5/mes' },
]

const EDGES_DEF = [
  // Input → Parsers
  ['MP_FILE', 'MP_PARSER'], ['XFR_FILE', 'XFR_PARSER'], ['DML_FILE', 'DML_PARSER'], ['COBOL_FILE', 'COBOL_PARSER'],
  // COBOL generates files
  ['COBOL_PARSER', 'MP_PARSER'], ['COBOL_PARSER', 'XFR_PARSER'], ['COBOL_PARSER', 'DML_PARSER'],
  // Parsers → Core
  ['MP_PARSER', 'DAG_BUILDER'], ['XFR_PARSER', 'VALIDATOR'], ['DML_PARSER', 'VALIDATOR'],
  ['DAG_BUILDER', 'VALIDATOR'], ['DAG_BUILDER', 'ACCURACY'], ['VALIDATOR', 'ACCURACY'],
  // Core → Codegen
  ['DAG_BUILDER', 'GLUE_CODEGEN'], ['DAG_BUILDER', 'SPARK_CODEGEN'],
  ['DAG_BUILDER', 'SF_CODEGEN'], ['DAG_BUILDER', 'TF_CODEGEN'], ['DAG_BUILDER', 'AF_CODEGEN'],
  ['VALIDATOR', 'GLUE_CODEGEN'], ['VALIDATOR', 'SPARK_CODEGEN'],
  // Core → API
  ['GLUE_CODEGEN', 'FASTAPI'], ['SPARK_CODEGEN', 'FASTAPI'],
  ['SF_CODEGEN', 'FASTAPI'], ['TF_CODEGEN', 'FASTAPI'], ['AF_CODEGEN', 'FASTAPI'],
  ['ACCURACY', 'FASTAPI'],
  ['GLUE_CODEGEN', 'LAMBDA'], ['SPARK_CODEGEN', 'LAMBDA'],
  ['SF_CODEGEN', 'LAMBDA'], ['TF_CODEGEN', 'LAMBDA'], ['AF_CODEGEN', 'LAMBDA'],
  ['ACCURACY', 'LAMBDA'],
  // API → UI
  ['FASTAPI', 'COMPILER_UI'], ['FASTAPI', 'DESIGNER_UI'],
  ['LAMBDA', 'COMPILER_UI'], ['LAMBDA', 'DESIGNER_UI'],
  // UI → Deploy
  ['COMPILER_UI', 'AMPLIFY'], ['DESIGNER_UI', 'AMPLIFY'], ['BANKING_UI', 'AMPLIFY'],
  ['GOVERNANCE_UI', 'AMPLIFY'], ['METRICS_UI', 'AMPLIFY'], ['ARCHITECTURE_UI', 'AMPLIFY'],
  ['LAMBDA', 'LAMBDA_DEPLOY'],
]

const GROUP_COLOR = {
  input: '#22c55e', parser: '#06b6d4', core: '#6366f1',
  codegen: '#f59e0b', api: '#ec4899', ui: '#a855f7', deploy: '#ef4444',
}
const GROUP_LABEL = {
  input: 'Input Files', parser: 'Parsers', core: 'Core Engine',
  codegen: 'Code Generation', api: 'API Layer', ui: 'UI (React)', deploy: 'AWS Deploy',
}

function buildArch(theme) {
  const t = theme || {}
  const nodes = COMPONENTS.map(c => ({
    id: c.id,
    position: { x: c.x, y: c.y },
    data: { label: c.label, desc: c.desc, group: c.group },
    style: {
      background: GROUP_COLOR[c.group] + '18',
      border: `2px solid ${GROUP_COLOR[c.group]}`,
      borderRadius: 8, color: t.text || '#e2e8f0',
      fontSize: 11, padding: '8px 10px', minWidth: 140,
      textAlign: 'center', whiteSpace: 'pre-line',
    }
  }))
  const edges = EDGES_DEF.map(([s, tgt], i) => ({
    id: `e${i}`, source: s, target: tgt,
    markerEnd: { type: MarkerType.ArrowClosed, color: '#47556960' },
    style: { stroke: '#47556960', strokeWidth: 1.2 },
  }))
  return { nodes, edges }
}

export default function ArchitecturePage({ theme }) {
  const t = theme || {}
  const { nodes: init, edges: initE } = useMemo(() => buildArch(t), [t])
  const [nodes, setNodes, onNodesChange] = useNodesState(init)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initE)
  const [selected, setSelected] = useState(null)
  const [showGlossary, setShowGlossary] = useState(false)

  useEffect(() => { setNodes(init) }, [init, setNodes])
  useEffect(() => { setEdges(initE) }, [initE, setEdges])

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      {/* Title */}
      <div style={{
        position: 'absolute', top: 16, left: 16, zIndex: 10,
        background: t.sidebar || '#161b27', padding: '12px 20px',
        borderRadius: 10, border: `1px solid ${t.border || '#334155'}`,
        boxShadow: '0 4px 20px rgba(0,0,0,.3)', maxWidth: 380,
      }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: t.text || '#e2e8f0' }}>
          🏗️ Arquitectura BNX Convertidor
        </div>
        <div style={{ fontSize: 12, color: t.dim || '#64748b', marginTop: 4 }}>
          {COMPONENTS.length} componentes · Click en un nodo para ver detalles
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
          {Object.entries(GROUP_LABEL).map(([k, v]) => (
            <span key={k} style={{
              fontSize: 9, padding: '2px 6px', borderRadius: 4,
              background: GROUP_COLOR[k] + '20', color: GROUP_COLOR[k], border: `1px solid ${GROUP_COLOR[k]}40`,
            }}>{v}</span>
          ))}
        </div>
        <button onClick={() => setShowGlossary(g => !g)} style={{
          marginTop: 10, padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 12,
          background: showGlossary ? '#6366f120' : (t.card || '#1e2433'),
          border: `1px solid ${showGlossary ? '#6366f1' : (t.border || '#334155')}`,
          color: showGlossary ? '#818cf8' : (t.muted || '#94a3b8'), fontWeight: 600, width: '100%',
        }}>📖 {showGlossary ? 'Cerrar Glosario' : 'Glosario de Mecanismos'}</button>
      </div>

      {/* Glossary panel */}
      {showGlossary && (
        <div style={{
          position: 'absolute', top: 16, left: 420, zIndex: 10, width: 420,
          maxHeight: 'calc(100vh - 120px)', overflowY: 'auto',
          background: t.sidebar || '#161b27', borderRadius: 10,
          border: `1px solid ${t.border || '#334155'}`,
          boxShadow: '0 8px 32px rgba(0,0,0,.4)',
        }}>
          <div style={{
            padding: '12px 16px', borderBottom: `1px solid ${t.border || '#334155'}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            position: 'sticky', top: 0, background: t.sidebar || '#161b27', zIndex: 1,
          }}>
            <span style={{ fontSize: 16, fontWeight: 700, color: t.text || '#e2e8f0' }}>
              📖 Glosario de Mecanismos
            </span>
            <button onClick={() => setShowGlossary(false)} style={{
              background: 'none', border: 'none', color: t.muted, fontSize: 16, cursor: 'pointer',
            }}>✕</button>
          </div>
          <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 16 }}>
            {MECHANISMS.map(cat => (
              <div key={cat.category}>
                <div style={{
                  fontSize: 14, fontWeight: 700, color: t.text || '#e2e8f0',
                  marginBottom: 8, padding: '4px 0',
                  borderBottom: `1px solid ${t.border || '#334155'}30`,
                }}>{cat.category}</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {cat.items.map(item => (
                    <div key={item.name} style={{
                      padding: '8px 10px', borderRadius: 6,
                      background: (t.bg || '#0f1117') + '80',
                      border: `1px solid ${item.color ? item.color + '40' : (t.border || '#334155') + '30'}`,
                    }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: item.color || '#818cf8', display: 'flex', alignItems: 'center', gap: 6 }}>
                        {item.color && <span style={{ width: 10, height: 10, borderRadius: '50%', background: item.color, flexShrink: 0 }} />}
                        {item.name}
                      </div>
                      <div style={{ fontSize: 12, color: t.muted || '#94a3b8', marginTop: 3, lineHeight: 1.6 }}>{item.desc}</div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detail panel */}
      {selected && (
        <div style={{
          position: 'absolute', top: 16, right: 16, zIndex: 10, width: 300,
          background: t.sidebar || '#161b27', borderRadius: 10,
          border: `1px solid ${t.border || '#334155'}`,
          boxShadow: '0 8px 32px rgba(0,0,0,.4)', overflow: 'hidden',
        }}>
          <div style={{
            padding: '10px 14px', background: GROUP_COLOR[selected.data.group] + '20',
            borderBottom: `1px solid ${t.border || '#334155'}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: t.text || '#e2e8f0' }}>
              {selected.data.label.split('\n')[0]}
            </span>
            <button onClick={() => setSelected(null)} style={{
              background: 'none', border: 'none', color: t.muted, fontSize: 16, cursor: 'pointer',
            }}>✕</button>
          </div>
          <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 8 }}>
            <span style={{
              padding: '2px 8px', borderRadius: 4, fontSize: 11, alignSelf: 'flex-start',
              background: GROUP_COLOR[selected.data.group] + '20',
              color: GROUP_COLOR[selected.data.group],
              border: `1px solid ${GROUP_COLOR[selected.data.group]}40`,
            }}>{GROUP_LABEL[selected.data.group]}</span>
            <div style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.7 }}>
              {selected.data.desc}
            </div>
            {GLOSSARY[selected.id] && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 4 }}>
                <span style={{ fontSize: 11, color: t.dim || '#64748b', textTransform: 'uppercase', letterSpacing: 1 }}>
                  Conceptos Clave
                </span>
                {GLOSSARY[selected.id].concepts.map(c => (
                  <div key={c.term} style={{
                    padding: '8px 10px', borderRadius: 6,
                    background: (t.bg || '#0f1117') + '80', border: `1px solid ${t.border || '#334155'}30`,
                  }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: GROUP_COLOR[selected.data.group] }}>{c.term}</div>
                    <div style={{ fontSize: 12, color: t.muted || '#94a3b8', marginTop: 3, lineHeight: 1.6 }}>{c.def}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <ReactFlow
        nodes={nodes} edges={edges}
        onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
        onNodeClick={(_, n) => setSelected(n)}
        onPaneClick={() => setSelected(null)}
        fitView minZoom={0.3}
      >
        <Background color={t.flowBg || '#1e2433'} gap={20} />
        <Controls />
        <MiniMap
          nodeColor={n => {
            const c = COMPONENTS.find(x => x.id === n.id)
            return GROUP_COLOR[c?.group] || '#64748b'
          }}
          style={{ background: t.card || '#1e2433' }}
        />
      </ReactFlow>
    </div>
  )
}
