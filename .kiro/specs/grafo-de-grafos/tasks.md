# Implementation Plan: Grafo de Grafos

## Overview

Implementación incremental del soporte multi-MP en el compilador BNX. Se extiende el pipeline existente (PLAN → MP → DAG → Codegen) para resolver referencias a archivos `.mp` externos, combinarlos en un Mega-DAG unificado con namespacing, cross-graph edges, retrocesos y sustitución PSET transversal. Cada tarea construye sobre la anterior, validando funcionalidad core antes de avanzar.

## Tasks

- [x] 1. Definir dataclass ResolvedGraph y función substitute_pset_params
  - [x] 1.1 Crear dataclass `ResolvedGraph` en `src/plan_parser.py`
    - Agregar `from dataclasses import dataclass, field` al inicio del archivo
    - Definir `ResolvedGraph` con campos: `name`, `ast`, `xfr_rules`, `dml_schema`, `is_auto_generated`, `depends`
    - Seguir la especificación exacta del diseño (sección Dataclass auxiliar)
    - _Requirements: 1.1, 1.4, 2.1_

  - [x] 1.2 Implementar `substitute_pset_params(content, pset_params)` en `src/plan_parser.py`
    - Reemplazar `${PARAM_NAME}` en content con valores del PSET dict
    - Dejar `${PARAM}` sin sustituir si la key no existe en pset_params
    - Retornar tupla `(content_sustituido, warnings)` donde warnings lista los parámetros no definidos
    - Usar `re.sub` con pattern `\$\{(\w+)\}` para encontrar referencias
    - _Requirements: 5.2, 5.4_

  - [ ]* 1.3 Write property test for PSET substitution (Property 9)
    - **Property 9: PSET parameter substitution**
    - Generar strings con `${PARAM}` references y dicts PSET aleatorios con Hypothesis
    - Verificar que cada `${PARAM}` con key en PSET se reemplaza con su valor
    - Verificar que `${PARAM}` sin key en PSET queda sin cambios
    - **Validates: Requirements 5.2**

  - [ ]* 1.4 Write property test for undefined PSET warning (Property 10)
    - **Property 10: Warning on undefined PSET parameter**
    - Generar XFR content con `${PARAM}` donde PARAM no está en PSET
    - Verificar que se produce un warning que incluye el nombre del parámetro
    - **Validates: Requirements 5.4**

- [x] 2. Implementar namespace_ast y detect_retrocesos
  - [x] 2.1 Implementar `namespace_ast(ast, graph_name)` en `src/plan_parser.py`
    - Prefijar todos los node IDs con `{graph_name}__`
    - Actualizar todas las edge references (`from`, `to`) con IDs namespaciados
    - Preservar `node["name"]` original como display name
    - Agregar `subgraph` y `source_graph` a cada nodo
    - Renombrar subgraphs a `{graph_name}__{subgraph_name}`
    - Agregar el grafo completo como subgraph con key `graph_name`
    - Seguir el algoritmo exacto del diseño (sección Algoritmo de namespacing)
    - _Requirements: 2.2, 2.3, 2.4_

  - [ ]* 2.2 Write property test for namespace correctness (Property 2)
    - **Property 2: Namespace correctness**
    - Generar ASTs y graph names aleatorios con Hypothesis
    - Verificar: (a) todo node ID empieza con `{graph_name}__`, (b) todo edge referencia IDs namespaciados, (c) display name preservado, (d) dos ASTs con nombres distintos no colisionan
    - **Validates: Requirements 2.2, 2.3, 2.4**

  - [x] 2.3 Implementar `detect_retrocesos(parsed_plan)` en `src/plan_parser.py`
    - Construir grafo dirigido de dependencias entre GRAPHs
    - Para cada edge (A depends on B), verificar si B también depende transitivamente de A
    - Si sí → retroceso (A, B)
    - Retornar `list[tuple[str, str]]`
    - Seguir el algoritmo exacto del diseño (sección Algoritmo de detección de retrocesos)
    - _Requirements: 4.1_

  - [ ]* 2.4 Write property test for retroceso detection (Property 6)
    - **Property 6: Retroceso detection**
    - Generar PLANs con ciclos conocidos usando Hypothesis
    - Verificar que `detect_retrocesos` identifica correctamente los pares de retroceso
    - **Validates: Requirements 4.1**

- [ ] 3. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implementar resolve_graph_references y merge_asts
  - [x] 4.1 Implementar `resolve_graph_references(parsed_plan, mp_files, pset_params, base_dir)` en `src/plan_parser.py`
    - Para cada GRAPH en el PLAN:
      - Si tiene MP property y existe en mp_files → `parse_mp_ast(path)` + `namespace_ast`
      - Si tiene MP property pero no existe → error descriptivo con nombre del grafo y path
      - Si no tiene MP property → auto-generate con lógica existente de `plan_to_graph` + `namespace_ast`, marcar `is_auto_generated=True`
    - Resolver XFR externo si existe, aplicar `substitute_pset_params`
    - Resolver DML externo si existe, warning si falta
    - Retornar `list[ResolvedGraph]`
    - Importar `parse_mp_ast` de `src.mp_parser` y `parse_xfr` de `src.xfr_parser`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 5.1, 5.2, 5.3_

  - [ ]* 4.2 Write property test for external reference resolution (Property 1)
    - **Property 1: External reference resolution**
    - Generar PLANs con mezcla de grafos con/sin MP externo usando Hypothesis
    - Verificar: (a) grafos con MP externo tienen AST cargado, (b) grafos sin MP tienen `is_auto_generated=True`, (c) MP faltante produce error con nombre y path
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

  - [ ]* 4.3 Write property test for mixed MP resolution backward compatibility (Property 15)
    - **Property 15: Mixed MP resolution backward compatibility**
    - Generar PLANs donde algunos GRAPHs tienen MP externo y otros no
    - Verificar que se produce un `ResolvedGraph` válido para cada GRAPH
    - **Validates: Requirements 10.3**

  - [x] 4.4 Implementar `merge_asts(resolved_graphs, dependencies, retrocesos)` en `src/plan_parser.py`
    - Combinar todos los ASTs namespaciados en un único AST unificado
    - Crear cross-graph edges (SINK→SOURCE) basados en dependencies usando `_create_cross_graph_edges`
    - Implementar función auxiliar `_create_cross_graph_edges` según el diseño
    - Marcar edges de retroceso con metadata `type: "retroceso"`
    - Retornar dict con: `nodes`, `edges`, `subgraphs`, `cross_graph_edges`, `retroceso_edges`
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ]* 4.5 Write property test for merge preserves nodes (Property 3)
    - **Property 3: Merge preserves all nodes and subgraph structure**
    - Generar sets de ASTs namespaciados con Hypothesis
    - Verificar: (a) total nodos = suma de nodos input, (b) edges intra-grafo preservados, (c) cada graph name aparece como subgraph key
    - **Validates: Requirements 3.1, 3.3**

- [x] 5. Extender DAG Builder para Mega-DAG
  - [x] 5.1 Extender clase `DAG` en `src/dag/builder.py`
    - Agregar campos: `cross_graph_edges`, `retroceso_edges`, `graph_boundaries`
    - Inicializar como listas/dicts vacíos en `__init__`
    - Modificar `topo_sort` para excluir retroceso edges del ordenamiento
    - Detectar ciclos no-retroceso y lanzar error con el path del ciclo
    - _Requirements: 3.4, 3.5, 4.2_

  - [x] 5.2 Implementar `build_mega_dag(merged_ast)` en `src/dag/builder.py`
    - Construir DAG desde el AST unificado (merged_ast)
    - Poblar `cross_graph_edges` y `retroceso_edges` desde el merged_ast
    - Poblar `graph_boundaries` desde `merged_ast["subgraphs"]`
    - Excluir retroceso_edges del topo sort
    - Reutilizar `build_dag` existente para la construcción base, extendiendo con metadata
    - _Requirements: 3.4, 4.2_

  - [ ]* 5.3 Write property test for topological order validity (Property 4)
    - **Property 4: Topological order validity**
    - Generar Mega-DAGs sin ciclos no-retroceso con Hypothesis
    - Verificar que para cada edge no-retroceso (A→B), A aparece antes que B en execution_order
    - **Validates: Requirements 3.4**

  - [ ]* 5.4 Write property test for non-retroceso cycle detection (Property 5)
    - **Property 5: Non-retroceso cycle detection**
    - Generar grafos de dependencias con ciclos no marcados como retroceso
    - Verificar que `build_mega_dag` retorna error indicando el path del ciclo
    - **Validates: Requirements 3.5**

  - [ ]* 5.5 Write property test for retroceso edges excluded from topo sort (Property 7)
    - **Property 7: Retroceso edges excluded from topological sort**
    - Generar Mega-DAGs con retroceso edges
    - Verificar que topo sort completa sin error de ciclo y retroceso edges no restringen el orden
    - **Validates: Requirements 4.2**

- [ ] 6. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Extender Semantic Validator para Mega-DAG
  - [x] 7.1 Extender `validate()` en `src/validator/semantic.py`
    - Agregar validación de cross-graph edges: nodo source existe en grafo dependencia, nodo target existe en grafo dependiente
    - Agregar validación de retroceso boundaries: solo SINK→SOURCE entre grafos distintos
    - Agregar validación de iteration limit para retrocesos
    - Mantener toda la validación intra-grafo existente sin cambios
    - Usar `dag.cross_graph_edges`, `dag.retroceso_edges`, `dag.graph_boundaries` (campos nuevos del DAG)
    - _Requirements: 8.1, 8.2, 8.4, 8.5, 4.3_

  - [ ] 7.2 Implementar `_infer_columns_cross_graph()` en `src/validator/semantic.py`
    - Extender `_infer_columns` para SOURCE nodes que reciben datos de un cross-graph edge
    - Heredar columnas del SINK padre en otro grafo
    - Warning si column schema no se puede inferir completamente
    - _Requirements: 8.3_

  - [ ]* 7.3 Write property test for cross-graph edge validation (Property 11)
    - **Property 11: Cross-graph edge validation**
    - Generar Mega-DAGs con cross-graph edges válidos e inválidos
    - Verificar que edges a nodos inexistentes producen error de validación
    - **Validates: Requirements 8.2, 8.4**

  - [ ]* 7.4 Write property test for retroceso boundary validation (Property 8)
    - **Property 8: Retroceso boundary validation**
    - Generar retroceso edges intra-grafo y cross-graph
    - Verificar que intra-grafo produce error, cross-graph (SINK→SOURCE) es aceptado
    - **Validates: Requirements 4.3**

  - [ ]* 7.5 Write property test for column propagation (Property 12)
    - **Property 12: Column inference propagation across cross-graph edges**
    - Generar cross-graph edges SINK→SOURCE con columnas conocidas
    - Verificar que SOURCE en grafo B hereda columnas del SINK en grafo A
    - **Validates: Requirements 8.3**

  - [ ]* 7.6 Write property test for retroceso iteration limit (Property 13)
    - **Property 13: Retroceso iteration limit validation**
    - Generar retroceso edges con y sin max_iterations definido
    - Verificar que retrocesos sin iteration limit producen error de validación
    - **Validates: Requirements 8.5**

- [ ] 8. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Extender Codegen para Mega-DAG
  - [x] 9.1 Extender `generate_glue()` en `src/codegen/glue_codegen.py`
    - Insertar comentarios de boundary `# === GRAPH: {graph_name} ===` entre grafos
    - Usar `dag.graph_boundaries` para determinar cuándo cambia el grafo actual
    - Generar lógica de checkpoint/staging para retroceso edges
    - Generar iteration loop con max_iterations y convergence check para feedback edges
    - _Requirements: 9.1, 9.2, 9.4, 4.4_

  - [x] 9.2 Extender `generate_spark()` en `src/codegen/spark_codegen.py`
    - Mismas extensiones que glue_codegen: boundary comments, retroceso staging, iteration loop
    - _Requirements: 9.1, 9.2, 9.4_

  - [x] 9.3 Extender `generate_stepfunctions()` en `src/codegen/stepfunctions_codegen.py`
    - Representar el Mega-DAG como workflow unificado
    - Agrupar states por graph boundary
    - Agregar retry/iteration states para retrocesos
    - _Requirements: 9.3_

  - [x] 9.4 Extender `generate_terraform()` en `src/codegen/terraform_codegen.py`
    - Generar Glue jobs agrupados por graph boundary con tags
    - Agregar S3 buckets de staging para retrocesos
    - _Requirements: 9.3_

  - [x] 9.5 Extender `generate_airflow()` en `src/codegen/airflow_codegen.py`
    - Representar Mega-DAG como un solo Airflow DAG con task groups por graph boundary
    - Agregar sensor/retry tasks para retrocesos
    - _Requirements: 9.3_

  - [ ]* 9.6 Write property test for graph boundary comments (Property 14)
    - **Property 14: Graph boundary comments in generated code**
    - Generar Mega-DAGs con N grafos (N > 1)
    - Verificar que el código Glue/Spark generado contiene exactamente N comentarios `# === GRAPH: {graph_name} ===`
    - **Validates: Requirements 9.2**

  - [ ]* 9.7 Write unit tests for retroceso codegen
    - Test `test_retroceso_codegen_checkpoint`: verificar que codegen genera staging/checkpoint para retrocesos
    - Test `test_codegen_iteration_logic`: verificar que codegen genera iteration loop para retrocesos
    - _Requirements: 4.4, 9.4_

- [x] 10. Implementar pretty_print_mega_dag
  - [x] 10.1 Implementar `pretty_print_mega_dag(merged_ast)` en `src/plan_parser.py`
    - Serializar el Mega-DAG a formato `.mp` legible
    - Incluir SUBGRAPH blocks por cada grafo original
    - Marcar cross-graph edges con comentarios indicando source y target graph
    - Incluir todos los nodos con su tipo dentro de cada SUBGRAPH
    - Incluir todos los edges (intra-graph y cross-graph)
    - _Requirements: 11.1, 11.3_

  - [ ]* 10.2 Write property test for round-trip serialization (Property 16)
    - **Property 16: Mega-DAG serialization round-trip**
    - Generar Mega-DAGs válidos con Hypothesis
    - Verificar que `parse_mp_ast(pretty_print_mega_dag(mega_dag))` produce AST equivalente: mismos node IDs, mismos edges, misma membresía de subgraphs
    - **Validates: Requirements 11.1, 11.2, 11.3**

- [ ] 11. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Extender API Server y Lambda Handler
  - [x] 12.1 Extender endpoint `/plan` en `api/server.py`
    - Agregar parámetro `mp_files: list[UploadFile] = File(default=[])` al endpoint
    - Guardar cada mp_file en temp y construir dict `{filename: temp_path}`
    - Si `mp_files` no vacío: llamar `resolve_graph_references`, `merge_asts`, `build_mega_dag`
    - Si `mp_files` vacío: mantener flujo existente con `plan_to_graph` (backward compatibility)
    - Agregar campos `graphs`, `cross_graph_edges` a la respuesta JSON
    - Generar todos los artifacts (StepFunctions, Terraform, Airflow) desde el Mega-DAG
    - Limpiar temp files en bloque `finally`
    - _Requirements: 6.1, 6.3, 6.4, 6.5, 6.6_

  - [x] 12.2 Extender handler `/plan` en `lambda/handler.py`
    - Extraer mp_files del multipart (campos `mp_file_0`, `mp_file_1`, ... o `mp_files[]`)
    - Misma lógica que api/server.py: resolve → merge → build_mega_dag si hay mp_files
    - Fallback a `plan_to_graph` si no hay mp_files
    - Agregar campos `graphs`, `cross_graph_edges` a la respuesta
    - _Requirements: 6.2, 6.4_

  - [ ]* 12.3 Write unit tests for API backward compatibility
    - Test `test_api_no_mp_files_backward_compat`: POST /plan sin mp_files funciona como antes
    - Test `test_api_response_graphs_field`: response incluye campo `graphs`
    - Test `test_api_response_cross_graph_edges_field`: response incluye campo `cross_graph_edges`
    - Test `test_single_mp_compile_unchanged`: /compile con single MP sin cambios
    - Test `test_plan_without_external_mps`: PLAN sin MPs externos auto-genera
    - _Requirements: 6.4, 6.5, 6.6, 10.1, 10.2_

- [x] 13. Extender UI para multi-MP upload y visualización
  - [x] 13.1 Agregar upload múltiple de `.mp` files en `ui/src/App.jsx`
    - Agregar state `mpFiles` (array de File objects) y ref `mpFilesRef`
    - Agregar botón "4° 📦 .mp files" en sección Ab Initio PLAN que acepta `multiple`
    - Mostrar lista de archivos `.mp` subidos con nombre y botón ❌ para eliminar individual
    - En `compilePlan()`: adjuntar cada mp file al FormData como `mp_files`
    - Mantener flujo existente sin cambios cuando no hay mp_files
    - _Requirements: 7.1, 7.2, 7.3, 10.4_

  - [x] 13.2 Extender `DagViewer.jsx` para cross-graph edges y retrocesos
    - En `buildLayout()`: detectar edges con `cross_graph: true` en data
    - Renderizar cross-graph edges con estilo dashed púrpura (`stroke: '#8b5cf6'`, `strokeDasharray: '8 4'`)
    - Renderizar retroceso edges con estilo dashed rojo animado (`stroke: '#ef4444'`, `strokeDasharray: '6 3'`, `animated: true`)
    - Agrupar nodos visualmente por subgraph (graph boundary) usando colores de fondo distintos
    - _Requirements: 7.4, 7.5_

- [ ] 14. Checkpoint final — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requirements específicos para trazabilidad
- Los checkpoints aseguran validación incremental
- Los property tests validan las 16 propiedades de correctness del diseño usando Hypothesis
- Los unit tests validan ejemplos específicos y edge cases
- El lenguaje de implementación es Python (backend) y JavaScript/React (frontend)
