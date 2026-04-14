# Requirements Document — Flink Codegen

## Introducción

Agregar Apache Flink como nuevo target de generación de código al BNX Convertidor. Actualmente el sistema soporta Glue y PySpark como targets. Este feature permite convertir grafos Ab Initio (archivos `.mp`) a jobs de Apache Flink usando PyFlink (Python API), con soporte para Table API/Flink SQL donde sea posible y DataStream API para operaciones específicas de streaming.

El módulo seguirá el mismo patrón arquitectónico de `glue_codegen.py` y `spark_codegen.py`, soportando los 11 tipos de nodo existentes, Mega-DAG (graph boundaries), y las tres fuentes/destinos: Kafka, S3/filesystem, JDBC.

## Glossary

- **Flink_Codegen**: Módulo de generación de código PyFlink ubicado en `src/codegen/flink_codegen.py`
- **PyFlink**: API de Python para Apache Flink, equivalente a PySpark para Spark
- **Table_API**: API declarativa de Flink para procesamiento de datos tabulares, similar a Spark SQL
- **Flink_SQL**: Lenguaje SQL soportado nativamente por Flink para definir transformaciones
- **DataStream_API**: API de bajo nivel de Flink para procesamiento de streams con control fino
- **StreamTableEnvironment**: Entorno de ejecución de Flink que combina Table API con streaming
- **DAG**: Directed Acyclic Graph — representación del pipeline de datos parseado desde archivos `.mp`
- **XFR_Rules**: Reglas de transformación parseadas desde archivos `.xfr` que definen select, where, group_by, join_key, etc.
- **Mega_DAG**: DAG unificado construido a partir de múltiples grafos con graph boundaries y cross-graph edges
- **Graph_Boundaries**: Metadatos del Mega_DAG que indican a qué grafo pertenece cada nodo
- **Node**: Elemento del DAG con tipo (SOURCE, TRANSFORM, JOIN, etc.), padres e hijos
- **Target_Selector**: Componente de UI que permite elegir el target de generación de código
- **BNX_Compiler**: Sistema completo de compilación que parsea `.mp`, construye DAG, valida y genera código

## Requirements

### Requirement 1: Módulo Flink Codegen

**User Story:** Como desarrollador del BNX Convertidor, quiero un módulo `flink_codegen.py` que genere código PyFlink, para que los grafos Ab Initio puedan ejecutarse en Apache Flink.

#### Acceptance Criteria

1. THE Flink_Codegen SHALL exponer una función `generate_flink(dag, output_path, xfr_rules=None)` con la misma firma que `generate_glue` y `generate_spark`
2. THE Flink_Codegen SHALL generar código Python válido que importe `pyflink.table`, `pyflink.datastream`, y `pyflink.table.expressions`
3. THE Flink_Codegen SHALL inicializar un `StreamTableEnvironment` como entorno de ejecución principal
4. THE Flink_Codegen SHALL iterar `dag.execution_order` y generar código para cada nodo según su tipo
5. THE Flink_Codegen SHALL incluir un header con timestamp de generación y versión BNX, consistente con los otros codegens

### Requirement 2: Soporte de nodos SOURCE

**User Story:** Como usuario, quiero que los nodos SOURCE generen código PyFlink para leer desde Kafka, S3/filesystem y JDBC, para que pueda ingestar datos de las mismas fuentes que en Glue/Spark.

#### Acceptance Criteria

1. WHEN un nodo SOURCE tiene `source_type` igual a "kafka" y un `topic` definido en XFR_Rules, THE Flink_Codegen SHALL generar código que cree una tabla Flink SQL con conector Kafka en modo streaming
2. WHEN un nodo SOURCE tiene `source_type` igual a "s3" o no tiene `source_type` definido, THE Flink_Codegen SHALL generar código que lea archivos desde el `path` usando Table API en modo batch
3. WHEN un nodo SOURCE tiene `source_type` igual a "jdbc" con `table` o `connection` definidos, THE Flink_Codegen SHALL generar código que lea desde la base de datos usando el conector JDBC de Flink
4. WHEN un nodo SOURCE tiene `format` igual a "csv", THE Flink_Codegen SHALL configurar el conector filesystem con formato CSV y opciones de header
5. WHEN un nodo SOURCE tiene `format` igual a "parquet" o no tiene formato definido, THE Flink_Codegen SHALL usar formato parquet como default para lectura de archivos

### Requirement 3: Soporte de nodos TRANSFORM

**User Story:** Como usuario, quiero que los nodos TRANSFORM generen código Flink SQL equivalente a las transformaciones PySpark, para que la lógica de negocio se preserve.

#### Acceptance Criteria

1. WHEN un nodo TRANSFORM tiene `select` y `where` en XFR_Rules, THE Flink_Codegen SHALL generar una sentencia Flink SQL con SELECT y WHERE correspondientes
2. WHEN un nodo TRANSFORM tiene `group_by` en XFR_Rules, THE Flink_Codegen SHALL generar una sentencia Flink SQL con GROUP BY y funciones de agregación
3. WHEN un nodo TRANSFORM no tiene regla XFR asociada, THE Flink_Codegen SHALL generar un SELECT * desde la tabla padre
4. IF un nodo TRANSFORM no tiene nodo padre, THEN THE Flink_Codegen SHALL generar un comentario indicando la ausencia de padre

### Requirement 4: Soporte de nodos JOIN

**User Story:** Como usuario, quiero que los nodos JOIN generen código Flink SQL para combinar datasets, para que los joins del grafo Ab Initio se traduzcan correctamente.

#### Acceptance Criteria

1. WHEN un nodo JOIN tiene 2 o más padres, THE Flink_Codegen SHALL generar una sentencia Flink SQL JOIN usando la `join_key` y `join_type` de XFR_Rules
2. WHEN un nodo JOIN no tiene `join_key` definida, THE Flink_Codegen SHALL usar "id" como join key por defecto
3. WHEN un nodo JOIN no tiene `join_type` definido, THE Flink_Codegen SHALL usar "INNER" como tipo de join por defecto
4. WHEN un nodo JOIN tiene más de 2 padres, THE Flink_Codegen SHALL generar joins encadenados para cada padre adicional

### Requirement 5: Soporte de nodos DEDUP

**User Story:** Como usuario, quiero que los nodos DEDUP generen código Flink para eliminar duplicados, para que la deduplicación del grafo Ab Initio funcione en Flink.

#### Acceptance Criteria

1. WHEN un nodo DEDUP tiene `dedup_keys` en XFR_Rules, THE Flink_Codegen SHALL generar código Flink SQL con ROW_NUMBER() OVER (PARTITION BY keys) para deduplicar
2. WHEN un nodo DEDUP tiene `order_by` en XFR_Rules, THE Flink_Codegen SHALL incluir ORDER BY en la window function para mantener el registro más reciente
3. WHEN un nodo DEDUP no tiene `dedup_keys`, THE Flink_Codegen SHALL usar ["id"] como keys por defecto

### Requirement 6: Soporte de nodos NORMALIZE

**User Story:** Como usuario, quiero que los nodos NORMALIZE generen código Flink para expandir registros, para que la normalización del grafo Ab Initio se traduzca a Flink.

#### Acceptance Criteria

1. WHEN un nodo NORMALIZE tiene `explode_col` en XFR_Rules, THE Flink_Codegen SHALL generar código que use la función UNNEST de Flink SQL para expandir la columna array
2. WHEN un nodo NORMALIZE tiene `split_col` y `delimiter` en XFR_Rules, THE Flink_Codegen SHALL generar código que primero divida el string y luego aplique UNNEST
3. WHEN un nodo NORMALIZE no tiene configuración de explode ni split, THE Flink_Codegen SHALL pasar los datos sin transformación desde el padre

### Requirement 7: Soporte de nodos LOOKUP

**User Story:** Como usuario, quiero que los nodos LOOKUP generen código Flink para enriquecer datos con tablas de referencia, para que los lookups del grafo Ab Initio funcionen en Flink.

#### Acceptance Criteria

1. WHEN un nodo LOOKUP tiene 2 o más padres, THE Flink_Codegen SHALL generar un LEFT JOIN en Flink SQL entre el dataset principal (primer padre) y la tabla de referencia (segundo padre)
2. WHEN un nodo LOOKUP tiene `lookup_key` en XFR_Rules, THE Flink_Codegen SHALL usar esa key como condición del LEFT JOIN
3. WHEN un nodo LOOKUP tiene `lookup_select` en XFR_Rules, THE Flink_Codegen SHALL seleccionar solo las columnas especificadas de la tabla de referencia

### Requirement 8: Soporte de nodos CONCATENATE y GATHER

**User Story:** Como usuario, quiero que los nodos CONCATENATE y GATHER generen código Flink para unir datasets, para que la unión de streams del grafo Ab Initio se traduzca a Flink.

#### Acceptance Criteria

1. WHEN un nodo CONCATENATE tiene 2 o más padres, THE Flink_Codegen SHALL generar código Flink SQL con UNION ALL para combinar las tablas
2. WHEN un nodo GATHER tiene 2 o más padres, THE Flink_Codegen SHALL generar código Flink SQL con UNION ALL para combinar las tablas
3. WHEN un nodo CONCATENATE o GATHER tiene un solo padre, THE Flink_Codegen SHALL asignar directamente la tabla del padre

### Requirement 9: Soporte de nodos PARTITION y FILTER

**User Story:** Como usuario, quiero que los nodos PARTITION y FILTER generen código Flink equivalente, para que el particionamiento y filtrado del grafo Ab Initio funcionen en Flink.

#### Acceptance Criteria

1. WHEN un nodo PARTITION tiene `partition_keys` en XFR_Rules, THE Flink_Codegen SHALL generar código que configure el particionamiento de la tabla usando las keys especificadas
2. WHEN un nodo FILTER tiene `where` en XFR_Rules, THE Flink_Codegen SHALL generar una tabla filtrada con la condición WHERE y una tabla de rechazos con la condición negada (NOT)
3. WHEN un nodo FILTER no tiene condición `where`, THE Flink_Codegen SHALL pasar los datos sin filtrar y generar una tabla de rechazos vacía

### Requirement 10: Soporte de nodos SINK

**User Story:** Como usuario, quiero que los nodos SINK generen código PyFlink para escribir a Kafka, S3/filesystem y JDBC, para que los resultados se persistan en los mismos destinos que en Glue/Spark.

#### Acceptance Criteria

1. WHEN un nodo SINK tiene `sink_type` igual a "kafka" y un `topic` definido, THE Flink_Codegen SHALL generar código que cree una tabla Flink SQL con conector Kafka y ejecute un INSERT INTO
2. WHEN un nodo SINK tiene `sink_type` igual a "s3" o no tiene `sink_type` definido, THE Flink_Codegen SHALL generar código que escriba al `path` usando el conector filesystem de Flink
3. WHEN un nodo SINK tiene `sink_type` igual a "jdbc" con `table` o `connection` definidos, THE Flink_Codegen SHALL generar código que escriba a la base de datos usando el conector JDBC de Flink
4. IF un nodo SINK no tiene nodo padre, THEN THE Flink_Codegen SHALL generar un comentario indicando que no hay datos para escribir

### Requirement 11: Soporte de Mega-DAG y Graph Boundaries

**User Story:** Como usuario, quiero que el Flink_Codegen soporte Mega-DAG con graph boundaries, para que los pipelines multi-grafo se generen correctamente como en Glue/Spark.

#### Acceptance Criteria

1. WHEN el DAG tiene `graph_boundaries` definidos, THE Flink_Codegen SHALL insertar comentarios de separación `# === GRAPH: {nombre} ===` cuando el nodo actual pertenece a un grafo diferente al anterior
2. THE Flink_Codegen SHALL construir un mapa inverso de nodo a grafo usando `dag.graph_boundaries` para determinar las transiciones entre grafos

### Requirement 12: Soporte de Window Operations para Streaming

**User Story:** Como usuario, quiero que el Flink_Codegen soporte window operations de Flink SQL para agregaciones sobre datos streaming, para aprovechar las capacidades nativas de streaming de Flink.

#### Acceptance Criteria

1. WHEN un nodo TRANSFORM tiene `group_by` y el source upstream es de tipo Kafka (streaming), THE Flink_Codegen SHALL generar código Flink SQL con TUMBLE window para agregaciones temporales
2. WHEN un nodo TRANSFORM tiene `window_size` en XFR_Rules, THE Flink_Codegen SHALL usar ese valor como tamaño de ventana en la función TUMBLE
3. WHEN un nodo TRANSFORM tiene `group_by` pero el source upstream no es streaming, THE Flink_Codegen SHALL generar un GROUP BY estándar sin window

### Requirement 13: Integración con CLI (main.py)

**User Story:** Como usuario del CLI, quiero poder especificar `--target flink` para generar código PyFlink, para que pueda usar Flink desde la línea de comandos.

#### Acceptance Criteria

1. WHEN el usuario ejecuta `main.py` con `--target flink`, THE BNX_Compiler SHALL invocar `generate_flink(dag, output_path, xfr_rules)` en lugar de `generate_glue` o `generate_spark`
2. THE BNX_Compiler SHALL aceptar "flink" como valor válido en el argumento `--target` junto con "glue" y "spark"
3. WHEN el target es "flink", THE BNX_Compiler SHALL imprimir "🌊 Target: Apache Flink (PyFlink)" en la salida del CLI

### Requirement 14: Integración con API (server.py)

**User Story:** Como consumidor de la API, quiero enviar `target=flink` en los endpoints `/compile`, `/cobol` y `/plan`, para que la API genere código PyFlink.

#### Acceptance Criteria

1. WHEN el endpoint `/compile` recibe `target=flink`, THE BNX_Compiler SHALL generar código PyFlink usando Flink_Codegen
2. WHEN el endpoint `/cobol` recibe `target=flink`, THE BNX_Compiler SHALL generar código PyFlink usando Flink_Codegen
3. WHEN el endpoint `/plan` recibe `target=flink`, THE BNX_Compiler SHALL generar código PyFlink usando Flink_Codegen tanto en el path multi-MP como en el path legacy

### Requirement 15: Integración con Lambda (handler.py)

**User Story:** Como consumidor de la API Lambda, quiero que el handler soporte `target=flink`, para que las invocaciones Lambda generen código PyFlink.

#### Acceptance Criteria

1. WHEN el campo `target` del request es "flink", THE BNX_Compiler SHALL invocar `generate_flink` en la función `_generate_code` del handler Lambda
2. WHEN el campo `target` del request es "flink", THE BNX_Compiler SHALL invocar `generate_flink` en la función `_build_response` del handler Lambda para el path `/plan` multi-MP

### Requirement 16: Integración con UI (Target Selector)

**User Story:** Como usuario de la interfaz web, quiero ver un botón "Flink" en el selector de target junto a Glue y PySpark, para que pueda elegir Flink como target de generación.

#### Acceptance Criteria

1. THE Target_Selector SHALL mostrar tres opciones: "🔧 Glue", "⚡ PySpark", y "🌊 Flink"
2. WHEN el usuario selecciona "Flink", THE Target_Selector SHALL enviar `target=flink` en los requests de compilación
3. THE Target_Selector SHALL mostrar la descripción "PyFlink + Table API / Flink SQL" al hacer hover sobre el botón Flink

### Requirement 17: Compatibilidad Retroactiva

**User Story:** Como usuario existente, quiero que los targets Glue y PySpark sigan funcionando exactamente igual después de agregar Flink, para que mis pipelines existentes no se rompan.

#### Acceptance Criteria

1. THE BNX_Compiler SHALL mantener el comportamiento existente de `generate_glue` y `generate_spark` sin modificaciones a su lógica interna
2. WHEN el target es "glue" o no se especifica target, THE BNX_Compiler SHALL usar `generate_glue` como comportamiento por defecto
3. THE BNX_Compiler SHALL mantener todas las importaciones y referencias existentes a `glue_codegen` y `spark_codegen` sin cambios
