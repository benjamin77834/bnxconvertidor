# Requirements Document — Grafo de Grafos

## Introducción

El proyecto BNX Convertidor actualmente procesa un único archivo `.mp` (grafo) o genera uno internamente a partir de un archivo `.plan`. La funcionalidad "Grafo de Grafos" permite que un archivo PLAN referencie múltiples archivos `.mp` externos (cada uno representando un componente/grafo individual) y los combine en un mega-DAG unificado. Esto habilita la orquestación de pipelines complejos donde cada grafo es un componente independiente con sus propias transformaciones, y el PLAN define las dependencias entre ellos — incluyendo retrocesos (backward references / feedback loops). Los parámetros PSET se aplican de forma transversal a todos los grafos.

## Glossary

- **PLAN_Parser**: Módulo `src/plan_parser.py` que parsea archivos `.plan` y genera representaciones internas de grafos con dependencias.
- **MP_Parser**: Módulo `src/mp_parser.py` que parsea un archivo `.mp` individual en un AST (nodos, edges, subgraphs).
- **DAG_Builder**: Módulo `src/dag/builder.py` que construye un DAG ejecutable a partir de un AST.
- **Mega_DAG**: DAG unificado resultante de combinar múltiples grafos individuales (.mp) con sus dependencias inter-grafo definidas en el PLAN.
- **Cross_Graph_Edge**: Arista que conecta un nodo SINK de un grafo con un nodo SOURCE de otro grafo, representando una dependencia entre componentes.
- **Retroceso**: Referencia hacia atrás (backward reference / feedback loop) donde un grafo posterior alimenta datos de vuelta a un grafo anterior en el pipeline.
- **PSET**: Archivo de parámetros runtime (paths, conexiones, thresholds) que se aplican transversalmente a todos los grafos del PLAN.
- **Graph_Namespace**: Prefijo único derivado del nombre del GRAPH en el PLAN, usado para evitar colisiones de nombres de nodos entre grafos distintos.
- **Semantic_Validator**: Módulo `src/validator/semantic.py` que valida el DAG antes de la generación de código.
- **API_Server**: Servidor FastAPI en `api/server.py` que expone los endpoints de compilación.
- **Lambda_Handler**: Handler AWS Lambda en `lambda/handler.py` que procesa requests de compilación.
- **Compiler_UI**: Interfaz React en `ui/src/App.jsx` que permite subir archivos y visualizar resultados.
- **Codegen**: Módulos de generación de código (`glue_codegen.py`, `spark_codegen.py`, etc.) que producen jobs ejecutables a partir del DAG.

## Requirements

### Requirement 1: Resolución de referencias MP externas en PLAN

**User Story:** Como desarrollador de pipelines, quiero que el PLAN resuelva las referencias MP/XFR/DML a archivos externos reales, para que cada GRAPH use su propio grafo definido en un archivo `.mp` separado.

#### Acceptance Criteria

1. WHEN a PLAN file contains a GRAPH definition with an MP property referencing an external file path, THE PLAN_Parser SHALL resolve that reference and load the corresponding `.mp` file content.
2. WHEN a PLAN file contains a GRAPH definition with an XFR property referencing an external file path, THE PLAN_Parser SHALL resolve that reference and load the corresponding `.xfr` file content.
3. WHEN a PLAN file contains a GRAPH definition with a DML property referencing an external file path, THE PLAN_Parser SHALL resolve that reference and load the corresponding `.dml` file content.
4. WHEN a GRAPH definition has no MP property, THE PLAN_Parser SHALL auto-generate the `.mp` content for that graph using the existing name-based heuristic logic.
5. IF a referenced MP file path does not exist or is unreadable, THEN THE PLAN_Parser SHALL return a descriptive error indicating the graph name and the missing file path.
6. IF a referenced XFR or DML file path does not exist, THEN THE PLAN_Parser SHALL log a warning and continue processing with default rules for that graph.

### Requirement 2: Parsing y namespacing de múltiples archivos MP

**User Story:** Como desarrollador de pipelines, quiero que múltiples archivos `.mp` se parseen individualmente y sus nodos se mantengan separados por namespace, para que no haya colisiones de nombres entre grafos distintos.

#### Acceptance Criteria

1. WHEN multiple `.mp` files are loaded from a PLAN, THE MP_Parser SHALL parse each file independently into its own AST.
2. THE PLAN_Parser SHALL prefix each node ID with the Graph_Namespace (derived from the GRAPH name in the PLAN) to ensure uniqueness across all loaded graphs.
3. WHEN two different `.mp` files contain nodes with the same name, THE PLAN_Parser SHALL differentiate them using the Graph_Namespace prefix.
4. THE PLAN_Parser SHALL preserve the original node names as display names while using namespaced IDs internally.

### Requirement 3: Construcción del Mega-DAG unificado

**User Story:** Como desarrollador de pipelines, quiero que todos los grafos individuales se combinen en un único Mega_DAG con las dependencias inter-grafo, para que el sistema pueda orquestar la ejecución completa del pipeline.

#### Acceptance Criteria

1. WHEN all individual `.mp` files have been parsed and namespaced, THE DAG_Builder SHALL merge all ASTs into a single unified AST containing all nodes, edges, and subgraphs.
2. WHEN a GRAPH definition has a DEPENDS property listing other graph names, THE DAG_Builder SHALL create Cross_Graph_Edges connecting the SINK nodes of the dependency graph to the SOURCE nodes of the dependent graph.
3. THE Mega_DAG SHALL preserve each original graph as a distinct subgraph within the unified structure.
4. WHEN the Mega_DAG is constructed, THE DAG_Builder SHALL compute a valid topological execution order across all graphs.
5. IF the dependency graph between GRAPHs contains a cycle that is not marked as a Retroceso, THEN THE DAG_Builder SHALL return an error indicating the cycle path.

### Requirement 4: Soporte para retrocesos (feedback loops)

**User Story:** Como desarrollador de pipelines, quiero poder definir retrocesos entre grafos, para que un grafo posterior pueda alimentar datos de vuelta a un grafo anterior sin que el sistema lo rechace como un ciclo inválido.

#### Acceptance Criteria

1. WHEN a PLAN file contains a GRAPH with a DEPENDS property that creates a backward reference to a graph that also depends (directly or transitively) on the current graph, THE PLAN_Parser SHALL identify this as a Retroceso.
2. WHEN a Retroceso is detected, THE DAG_Builder SHALL mark the corresponding Cross_Graph_Edge as a feedback edge and exclude it from the topological sort computation.
3. THE Semantic_Validator SHALL validate that Retroceso edges connect only between graph boundaries (SINK-to-SOURCE) and not within a single graph.
4. THE Codegen SHALL generate checkpoint/staging logic for Retroceso edges so that the feedback data is written to a staging location and read in a subsequent iteration.

### Requirement 5: Aplicación transversal de parámetros PSET

**User Story:** Como desarrollador de pipelines, quiero que los parámetros PSET se apliquen a todos los grafos del PLAN, para que las configuraciones de paths, conexiones y thresholds sean consistentes en todo el pipeline.

#### Acceptance Criteria

1. WHEN a PSET file is provided alongside a PLAN, THE PLAN_Parser SHALL parse the PSET parameters and make them available to all graphs in the PLAN.
2. WHEN generating XFR rules for a graph that has an external `.xfr` file, THE PLAN_Parser SHALL substitute PSET parameter references (e.g., `${S3_INPUT}`) with their resolved values within the XFR content.
3. WHEN generating XFR rules for a graph without an external `.xfr` file, THE PLAN_Parser SHALL use PSET parameters to auto-generate XFR rules using the existing heuristic logic.
4. IF a PSET parameter is referenced in an XFR file but not defined in the PSET, THEN THE PLAN_Parser SHALL log a warning indicating the undefined parameter name and the graph where it is referenced.

### Requirement 6: Endpoint API para compilación multi-MP

**User Story:** Como consumidor de la API, quiero poder enviar múltiples archivos `.mp` junto con un `.plan`, para que el sistema compile el pipeline completo como un Mega_DAG.

#### Acceptance Criteria

1. THE API_Server SHALL accept multiple `.mp` files in the `/plan` endpoint via multipart form fields named `mp_files`.
2. THE Lambda_Handler SHALL accept multiple `.mp` files in the `/plan` endpoint via multipart form fields named `mp_files`.
3. WHEN multiple `.mp` files are received, THE API_Server SHALL pass them to the PLAN_Parser for resolution against GRAPH MP references.
4. WHEN no external `.mp` files are provided, THE API_Server SHALL fall back to the existing auto-generation behavior for backward compatibility.
5. THE API_Server SHALL return the Mega_DAG response including a `graphs` field listing each individual graph with its nodes, edges, and subgraph membership.
6. THE API_Server SHALL return a `cross_graph_edges` field listing all Cross_Graph_Edges with their source graph, target graph, and edge type (normal or retroceso).

### Requirement 7: Soporte de UI para carga de múltiples archivos MP

**User Story:** Como usuario de la interfaz, quiero poder subir múltiples archivos `.mp` junto con mi `.plan`, para que el sistema procese el pipeline completo desde la UI.

#### Acceptance Criteria

1. THE Compiler_UI SHALL provide a file upload control in the Ab Initio PLAN section that accepts multiple `.mp` files.
2. WHEN the user uploads `.mp` files, THE Compiler_UI SHALL display the list of uploaded `.mp` file names with the ability to remove individual files.
3. WHEN the user clicks the PLAN upload button, THE Compiler_UI SHALL send all uploaded `.mp` files along with the PLAN, PSET, and XFR files to the `/plan` endpoint.
4. THE Compiler_UI SHALL display each graph as a visually distinct subgraph in the DAG viewer, with Cross_Graph_Edges rendered as dashed lines between subgraphs.
5. THE Compiler_UI SHALL display Retroceso edges with a distinct visual style (e.g., red dashed lines with an arrow indicator) to differentiate them from normal Cross_Graph_Edges.

### Requirement 8: Validación semántica del Mega-DAG

**User Story:** Como desarrollador de pipelines, quiero que la validación semántica funcione correctamente sobre el Mega_DAG completo, para que se detecten errores tanto dentro de cada grafo como entre grafos.

#### Acceptance Criteria

1. THE Semantic_Validator SHALL validate each individual graph's internal structure (join keys, orphan nodes, parent requirements) within the Mega_DAG.
2. THE Semantic_Validator SHALL validate Cross_Graph_Edges ensuring that the source node exists in the dependency graph and the target node exists in the dependent graph.
3. THE Semantic_Validator SHALL propagate column inference across Cross_Graph_Edges so that a dependent graph's SOURCE nodes inherit the schema from the dependency graph's SINK nodes.
4. IF a Cross_Graph_Edge references a node that does not exist in the expected graph, THEN THE Semantic_Validator SHALL return an error indicating the invalid cross-graph reference.
5. THE Semantic_Validator SHALL validate that Retroceso edges do not create infinite loops (each Retroceso must have a defined iteration limit or termination condition in the PLAN).

### Requirement 9: Generación de código unificado desde el Mega-DAG

**User Story:** Como desarrollador de pipelines, quiero que el codegen produzca un único job unificado a partir del Mega_DAG, para que todo el pipeline se ejecute como una sola unidad.

#### Acceptance Criteria

1. WHEN the Mega_DAG passes validation, THE Codegen SHALL generate a single unified Glue/Spark job that processes all graphs in topological order.
2. THE Codegen SHALL include comments in the generated code marking the boundaries between individual graphs (e.g., `# === GRAPH: ingest_transactions ===`).
3. THE Codegen SHALL generate Step Functions, Terraform, and Airflow artifacts that represent the Mega_DAG as a single orchestrated workflow.
4. WHEN Retroceso edges exist, THE Codegen SHALL generate iteration logic with a configurable maximum iteration count and convergence check.

### Requirement 10: Compatibilidad hacia atrás

**User Story:** Como usuario existente, quiero que los flujos actuales de compilación de un solo `.mp` y de PLAN sin archivos externos sigan funcionando sin cambios, para que la nueva funcionalidad no rompa mi trabajo existente.

#### Acceptance Criteria

1. WHEN a single `.mp` file is submitted to the `/compile` endpoint without a PLAN, THE API_Server SHALL process it using the existing single-graph pipeline without any changes in behavior.
2. WHEN a PLAN file is submitted without external `.mp` files, THE API_Server SHALL auto-generate the `.mp` content using the existing `plan_to_graph` logic.
3. WHEN a PLAN file is submitted with external `.mp` files, THE API_Server SHALL use the external files for graphs that have MP references and auto-generate for graphs that do not.
4. THE Compiler_UI SHALL maintain the existing upload flow for single MP/XFR/DML files and COBOL files without any changes to their behavior.

### Requirement 11: Serialización y pretty-printing del Mega-DAG

**User Story:** Como desarrollador de pipelines, quiero poder exportar el Mega_DAG generado como un archivo `.mp` unificado, para que pueda inspeccionar, depurar y reutilizar el grafo combinado.

#### Acceptance Criteria

1. THE PLAN_Parser SHALL produce a unified `.mp` string representation (pretty-printed) of the Mega_DAG that includes all subgraphs, nodes, and edges.
2. FOR ALL valid Mega_DAG structures, parsing the pretty-printed `.mp` output and then pretty-printing it again SHALL produce an equivalent `.mp` string (round-trip property).
3. THE pretty-printed `.mp` output SHALL include SUBGRAPH blocks for each original graph and clearly mark Cross_Graph_Edges with comments indicating the source and target graphs.
