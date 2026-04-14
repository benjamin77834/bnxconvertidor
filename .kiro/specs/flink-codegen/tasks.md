# Plan de Implementación: Flink Codegen

## Resumen

Implementación incremental del módulo `flink_codegen.py` para generar código PyFlink (Table API / Flink SQL) a partir del DAG del BNX Compiler. Se comienza con la estructura base y los nodos más simples, se avanza hacia los nodos complejos, y se finaliza con la integración en CLI, API, Lambda y UI.

## Tareas

- [x] 1. Crear módulo base `src/codegen/flink_codegen.py` con estructura y nodos SOURCE
  - [x] 1.1 Crear archivo `src/codegen/flink_codegen.py` con función `generate_flink(dag, output_path, xfr_rules=None)`
    - Escribir el header con docstring, timestamp y versión BNX
    - Importar `pyflink.table`, `pyflink.datastream`, `pyflink.table.expressions`
    - Inicializar `StreamTableEnvironment`
    - Construir mapa inverso `node_to_graph` desde `dag.graph_boundaries` para soporte Mega-DAG
    - Iterar `dag.execution_order` con estructura de dispatch por `node.type`
    - Escribir footer con `t_env.execute('BNX Pipeline')`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 11.1, 11.2_

  - [x] 1.2 Implementar handler de nodos SOURCE con conectores Kafka, filesystem y JDBC
    - Generar DDL `CREATE TABLE ... WITH ('connector' = 'kafka')` cuando `source_type` es "kafka" y `topic` está definido
    - Generar DDL `CREATE TABLE ... WITH ('connector' = 'filesystem')` para S3/filesystem con soporte CSV, parquet y JSON
    - Generar DDL `CREATE TABLE ... WITH ('connector' = 'jdbc')` cuando `source_type` es "jdbc"
    - Usar defaults: filesystem si `source_type` no definido, parquet si `format` no definido, `localhost:9092` para Kafka sin connection, `jdbc:mysql://localhost:3306/db` para JDBC sin connection
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 1.3 Escribir property test para invariantes estructurales del código generado
    - **Property 1: Structural Invariants of Generated Code**
    - **Validates: Requirements 1.2, 1.3, 1.5**

  - [ ]* 1.4 Escribir property test para correctness de conectores SOURCE
    - **Property 3: SOURCE Connector Correctness**
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 2. Implementar handlers de nodos TRANSFORM, JOIN y DEDUP
  - [x] 2.1 Implementar handler de nodos TRANSFORM con Flink SQL
    - Generar `CREATE TEMPORARY VIEW ... AS SELECT {select} FROM {parent} WHERE {where}` para transforms simples
    - Generar `GROUP BY` con funciones de agregación cuando `group_by` está presente
    - Implementar `_is_streaming_upstream()` para detectar SOURCE Kafka upstream
    - Generar `TUMBLE` window cuando upstream es streaming y `group_by` está presente
    - Usar `window_size` de XFR rules (default 5 minutos)
    - Generar `SELECT *` cuando no hay regla XFR; generar comentario cuando no hay padre
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 12.1, 12.2, 12.3_

  - [x] 2.2 Implementar handler de nodos JOIN con Flink SQL
    - Generar `SELECT * FROM {parent1} {join_type} JOIN {parent2} ON {parent1}.{join_key} = {parent2}.{join_key}`
    - Soportar joins encadenados para N padres (N ≥ 2) generando N-1 JOINs
    - Defaults: `join_key` = "id", `join_type` = "INNER"
    - Manejar edge cases: 1 padre → asignar directo, 0 padres → None
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 2.3 Implementar handler de nodos DEDUP con ROW_NUMBER
    - Generar `ROW_NUMBER() OVER (PARTITION BY {dedup_keys} ORDER BY {order_by} DESC)` con `WHERE _rn = 1`
    - Generar `SELECT DISTINCT` cuando no hay `order_by`
    - Default: `dedup_keys` = ["id"]
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ]* 2.4 Escribir property tests para TRANSFORM, JOIN y DEDUP
    - **Property 4: TRANSFORM SQL Correctness**
    - **Property 5: JOIN Chained Correctness**
    - **Property 6: DEDUP ROW_NUMBER Correctness**
    - **Validates: Requirements 3.1, 3.2, 4.1, 4.4, 5.1, 5.2**

- [x] 3. Checkpoint — Verificar que los tests pasan
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implementar handlers de nodos NORMALIZE, LOOKUP, CONCATENATE, GATHER, PARTITION y FILTER
  - [x] 4.1 Implementar handler de nodos NORMALIZE con UNNEST
    - Generar `CROSS JOIN UNNEST({explode_col})` para explosión de arrays
    - Generar `STRING_TO_ARRAY` + `UNNEST` para split de strings con delimiter
    - Passthrough cuando no hay configuración de explode ni split
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 4.2 Implementar handler de nodos LOOKUP con LEFT JOIN
    - Generar `LEFT JOIN` entre primer padre (main) y segundo padre (referencia) usando `lookup_key`
    - Seleccionar solo columnas de `lookup_select` cuando está definido
    - Manejar edge cases: 1 padre → asignar directo, 0 padres → None
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 4.3 Implementar handlers de nodos CONCATENATE y GATHER con UNION ALL
    - Generar `UNION ALL` para combinar N tablas padre (N ≥ 2)
    - Asignar directo cuando hay un solo padre
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 4.4 Implementar handler de nodos PARTITION y FILTER
    - PARTITION: generar comentario indicando configuración de particionamiento (Flink no tiene repartition explícito)
    - FILTER: generar vista filtrada con `WHERE {condition}` y vista de rechazos con `WHERE NOT ({condition})`
    - FILTER sin condición: passthrough + tabla de rechazos vacía
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ]* 4.5 Escribir property tests para NORMALIZE, LOOKUP, CONCATENATE/GATHER y FILTER
    - **Property 7: NORMALIZE UNNEST for Array Explosion**
    - **Property 8: NORMALIZE Split+UNNEST for String Splitting**
    - **Property 9: LOOKUP LEFT JOIN Correctness**
    - **Property 10: UNION ALL Correctness for CONCATENATE and GATHER**
    - **Property 11: FILTER Dual Output Correctness**
    - **Validates: Requirements 6.1, 6.2, 7.1, 7.2, 7.3, 8.1, 8.2, 9.2**

- [x] 5. Implementar handler de nodos SINK y cobertura completa de nodos
  - [x] 5.1 Implementar handler de nodos SINK con conectores Kafka, filesystem y JDBC
    - Generar DDL `CREATE TABLE ... WITH ('connector' = 'kafka')` + `INSERT INTO` para Kafka
    - Generar DDL `CREATE TABLE ... WITH ('connector' = 'filesystem')` + `INSERT INTO` para S3/filesystem
    - Generar DDL `CREATE TABLE ... WITH ('connector' = 'jdbc')` + `INSERT INTO` para JDBC
    - Generar comentario cuando SINK no tiene padre
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 5.2 Implementar handler genérico para tipos de nodo desconocidos
    - Generar `SELECT *` desde el padre con comentario indicando el tipo
    - _Requirements: 1.4_

  - [ ]* 5.3 Escribir property tests para SINK, graph boundaries y node coverage
    - **Property 2: Node Coverage Completeness**
    - **Property 12: SINK Connector Correctness**
    - **Property 13: Graph Boundary Comments in Mega-DAG**
    - **Property 14: Streaming Window Conditional**
    - **Validates: Requirements 1.4, 10.1, 10.2, 10.3, 11.1, 12.1, 12.2, 12.3**

- [x] 6. Checkpoint — Verificar que todos los tests del módulo flink_codegen pasan
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Integrar Flink en CLI (`main.py`)
  - [x] 7.1 Agregar "flink" como opción válida en `--target` y branch de generación
    - Agregar `"flink"` a `choices=["glue", "spark", "flink"]` en argparse
    - Agregar `from src.codegen.flink_codegen import generate_flink` al inicio del archivo
    - Agregar branch `elif target == "flink": generate_flink(dag, output_path, xfr_rules)` y print `"🌊 Target: Apache Flink (PyFlink)"`
    - _Requirements: 13.1, 13.2, 13.3_

- [x] 8. Integrar Flink en API (`api/server.py`)
  - [x] 8.1 Agregar import y branches `target == "flink"` en endpoints `/compile`, `/cobol` y `/plan`
    - Agregar `from src.codegen.flink_codegen import generate_flink` al inicio
    - En `/compile`: agregar `elif target == "flink": generate_flink(dag, out.name, xfr_rules)` antes del else/glue
    - En `/cobol`: agregar branch flink en la generación de código
    - En `/plan`: agregar branch flink tanto en el path multi-MP como en el path legacy
    - _Requirements: 14.1, 14.2, 14.3_

- [x] 9. Integrar Flink en Lambda (`lambda/handler.py`)
  - [x] 9.1 Agregar import y branches `target == "flink"` en `_generate_code` y `_build_response`
    - Agregar `from src.codegen.flink_codegen import generate_flink` al inicio
    - En `_generate_code()`: agregar `elif target == "flink": generate_flink(dag, out.name, xfr_rules)` antes del else/glue
    - En `_build_response()`: agregar branch flink en la generación de código del path `/plan` multi-MP
    - _Requirements: 15.1, 15.2_

- [x] 10. Integrar Flink en UI (`App.jsx` y `DesignerPage.jsx`)
  - [x] 10.1 Agregar botón "🌊 Flink" al target selector en `App.jsx`
    - Agregar `{ id: 'flink', label: '🌊 Flink', desc: 'PyFlink + Table API / Flink SQL' }` al array de opciones del target selector en el sidebar
    - Actualizar `downloadCode` para generar nombre `flink_job.py` cuando target es flink
    - Actualizar el modal de código en DesignerPage para mostrar "🌊 Flink" cuando target es flink
    - _Requirements: 16.1, 16.2, 16.3_

  - [x] 10.2 Agregar botón "🌊 Flink" al target selector en `DesignerPage.jsx`
    - Agregar `'flink'` al array de targets en el Designer: `['glue', 'spark', 'flink']`
    - Agregar label `'🌊 Flink'` en el mapeo de botones del target selector
    - _Requirements: 16.1, 16.2_

- [x] 11. Checkpoint — Verificar compatibilidad retroactiva y tests finales
  - Ensure all tests pass, ask the user if questions arise.

  - [ ]* 11.1 Escribir property test de compatibilidad retroactiva
    - **Property 15: Backward Compatibility of Existing Generators**
    - **Validates: Requirements 17.1**

  - [ ]* 11.2 Escribir tests de integración para CLI, API y Lambda con target flink
    - Test que `main.py --target flink` invoca `generate_flink`
    - Test que POST `/compile` con `target=flink` retorna código PyFlink
    - Test que POST `/cobol` con `target=flink` retorna código PyFlink
    - Test que POST `/plan` con `target=flink` retorna código PyFlink
    - Test que Lambda handler con `target=flink` invoca `generate_flink`
    - _Requirements: 13.1, 14.1, 14.2, 14.3, 15.1, 17.1, 17.2, 17.3_

- [x] 12. Checkpoint final — Verificar que todos los tests pasan
  - Ensure all tests pass, ask the user if questions arise.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia los requisitos específicos para trazabilidad
- Los checkpoints aseguran validación incremental
- Los property tests validan propiedades universales de correctness definidas en el diseño
- Los unit tests validan ejemplos específicos y edge cases
- El módulo `flink_codegen.py` sigue el mismo patrón arquitectónico que `spark_codegen.py` y `glue_codegen.py`
