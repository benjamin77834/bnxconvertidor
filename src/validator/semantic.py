# src/validator/semantic.py
"""
Validaci?n sem?ntica del DAG antes de codegen.
Detecta errores de join key, nodos hu?rfanos, ciclos, etc.
"""

# Columnas conocidas por tipo de nodo seg?n su schema inferido
# Se construye propagando los campos a trav?s del DAG

def _infer_columns(node, dag, xfr_rules, col_cache, dml_schema=None):
    """Infiere las columnas disponibles en un nodo dado su tipo y padres."""
    if node.id in col_cache:
        return col_cache[node.id]

    # Mark as in-progress to prevent infinite recursion
    col_cache[node.id] = set()

    ntype = node.type.upper()
    rule = xfr_rules.get(node.id.lower()) or xfr_rules.get(node.name.lower()) or {}

    cols = set()

    if ntype == "SOURCE":
        # Prioridad 1: schema del DML
        if dml_schema and node.name in dml_schema:
            cols = set(dml_schema[node.name].keys())
        elif dml_schema and node.id in dml_schema:
            cols = set(dml_schema[node.id].keys())
        else:
            # Fallback: columnas del select en xfr
            select = rule.get("select", "*")
            if select != "*":
                for col in select.split(","):
                    col = col.strip()
                    if " as " in col.lower():
                        cols.add(col.lower().split(" as ")[-1].strip())
                    elif "(" not in col:
                        cols.add(col.strip())

    elif ntype in ("TRANSFORM", "XFR"):
        # Hereda columnas del padre + aplica select
        if node.parents and node.parents[0] in dag.nodes:
            parent_cols = _infer_columns(dag.nodes[node.parents[0]], dag, xfr_rules, col_cache, dml_schema)
            group_by = rule.get("group_by", [])
            select = rule.get("select", "*")

            if group_by:
                # groupBy: solo quedan las keys + aliases del agg
                cols = set(group_by)
                for col in select.split(","):
                    col = col.strip()
                    if " as " in col.lower():
                        cols.add(col.lower().split(" as ")[-1].strip())
            elif select == "*":
                cols = set(parent_cols)
            else:
                for col in select.split(","):
                    col = col.strip()
                    if " as " in col.lower():
                        cols.add(col.lower().split(" as ")[-1].strip())
                    elif "(" not in col:
                        cols.add(col.strip())

    elif ntype == "JOIN":
        for pid in node.parents:
            if pid in dag.nodes:
                parent_cols = _infer_columns(dag.nodes[pid], dag, xfr_rules, col_cache, dml_schema)
                cols |= parent_cols

    elif ntype == "DEDUP":
        if node.parents and node.parents[0] in dag.nodes:
            cols = set(_infer_columns(dag.nodes[node.parents[0]], dag, xfr_rules, col_cache, dml_schema))

    elif ntype == "NORMALIZE":
        if node.parents and node.parents[0] in dag.nodes:
            cols = set(_infer_columns(dag.nodes[node.parents[0]], dag, xfr_rules, col_cache, dml_schema))

    elif ntype == "LOOKUP":
        for pid in node.parents:
            if pid in dag.nodes:
                parent_cols = _infer_columns(dag.nodes[pid], dag, xfr_rules, col_cache, dml_schema)
                cols |= parent_cols

    elif ntype in ("CONCATENATE", "GATHER"):
        for pid in node.parents:
            if pid in dag.nodes:
                parent_cols = _infer_columns(dag.nodes[pid], dag, xfr_rules, col_cache, dml_schema)
                cols |= parent_cols

    elif ntype == "PARTITION":
        if node.parents and node.parents[0] in dag.nodes:
            cols = set(_infer_columns(dag.nodes[node.parents[0]], dag, xfr_rules, col_cache, dml_schema))

    elif ntype == "FILTER":
        if node.parents and node.parents[0] in dag.nodes:
            cols = set(_infer_columns(dag.nodes[node.parents[0]], dag, xfr_rules, col_cache, dml_schema))

    elif ntype == "SINK":
        if node.parents and node.parents[0] in dag.nodes:
            cols = _infer_columns(dag.nodes[node.parents[0]], dag, xfr_rules, col_cache, dml_schema)

    col_cache[node.id] = cols
    return cols


def validate(dag, xfr_rules, dml_schema=None):
    """
    Valida el DAG sem?nticamente.
    Retorna lista de errores encontrados.
    Supports Mega-DAG cross-graph validation.
    """
    errors = []
    warnings = []
    col_cache = {}

    # --- Cross-graph edge validation (Mega-DAG) ---
    cross_graph_edges = getattr(dag, 'cross_graph_edges', [])
    retroceso_edges = getattr(dag, 'retroceso_edges', [])
    graph_boundaries = getattr(dag, 'graph_boundaries', {})

    for cge in cross_graph_edges:
        from_id = cge.get("from", "")
        to_id = cge.get("to", "")
        if from_id not in dag.nodes:
            errors.append(f"? Cross-graph edge: source node '{from_id}' not found in graph '{cge.get('source_graph', '?')}'")
        if to_id not in dag.nodes:
            errors.append(f"? Cross-graph edge: target node '{to_id}' not found in graph '{cge.get('target_graph', '?')}'")

    for re_edge in retroceso_edges:
        from_id = re_edge.get("from", "")
        to_id = re_edge.get("to", "")
        src_graph = re_edge.get("source_graph", "")
        tgt_graph = re_edge.get("target_graph", "")
        # Retrocesos must cross graph boundaries
        if src_graph == tgt_graph:
            errors.append(
                f"? Retroceso edge '{from_id}' ? '{to_id}' is within graph '{src_graph}'. "
                f"Retrocesos must cross graph boundaries."
            )
        # Validate SINK?SOURCE
        if from_id in dag.nodes and dag.nodes[from_id].type.upper() != "SINK":
            warnings.append(f"[!]  Retroceso source '{from_id}' is not a SINK node")
        if to_id in dag.nodes and dag.nodes[to_id].type.upper() != "SOURCE":
            warnings.append(f"[!]  Retroceso target '{to_id}' is not a SOURCE node")

    for node in dag.execution_order:
        ntype = node.type.upper()
        rule = xfr_rules.get(node.id.lower()) or xfr_rules.get(node.name.lower()) or {}

        # 1. Nodos JOIN sin join_key definida
        if ntype == "JOIN":
            join_key = rule.get("join_key")
            if not join_key:
                warnings.append(f"[w] JOIN '{node.name}' has no join_key - defaulting to 'id'")
            else:
                # Verificar que la join_key existe en los padres
                for pid in node.parents:
                    if pid not in dag.nodes:
                        continue
                    parent_cols = _infer_columns(dag.nodes[pid], dag, xfr_rules, col_cache, dml_schema)
                    if parent_cols and join_key not in parent_cols:
                        errors.append(
                            f"[!] JOIN '{node.name}': join_key '{join_key}' not found in parent '{pid}' "
                            f"(available: {sorted(parent_cols)})"
                        )

        # 2. TRANSFORM sin padre
        if ntype in ("TRANSFORM", "XFR") and not node.parents:
            errors.append(f"[w] TRANSFORM '{node.name}' has no parent node")

        # 3. SINK sin padre
        if ntype == "SINK" and not node.parents:
            errors.append(f"[!] SINK '{node.name}' has no parent - nothing to write")

        # 3b. DEDUP sin padre o sin dedup_keys
        if ntype == "DEDUP":
            if not node.parents:
                errors.append(f"[w] DEDUP '{node.name}' has no parent node")
            elif rule.get("dedup_keys") is None and not rule:
                warnings.append(f"[w] DEDUP '{node.name}' has no dedup_keys - using default ['id']")

        # 3c. NORMALIZE sin padre o sin config
        if ntype == "NORMALIZE":
            if not node.parents:
                errors.append(f"[w] NORMALIZE '{node.name}' has no parent node")
            elif not rule.get("explode_col") and not rule.get("split_col"):
                warnings.append(f"[w] NORMALIZE '{node.name}' has no explode_col or split_col")

        # 3d. LOOKUP sin 2 padres o sin lookup_key
        if ntype == "LOOKUP":
            if len(node.parents) < 2:
                errors.append(f"[!] LOOKUP '{node.name}' needs 2 parents (main + reference), has {len(node.parents)}")
            elif not rule.get("lookup_key"):
                warnings.append(f"[w] LOOKUP '{node.name}' has no lookup_key - using default 'id'")

        # 4. TRANSFORM referencia columna en where que no existe
        if ntype in ("TRANSFORM", "XFR") and node.parents:
            if node.parents[0] not in dag.nodes:
                continue
            parent_cols = _infer_columns(dag.nodes[node.parents[0]], dag, xfr_rules, col_cache)
            where = rule.get("where")
            group_by = rule.get("group_by", [])
            select = rule.get("select", "*")
            if where and parent_cols:
                import re
                # Aliases generados por este mismo nodo (no existen en el padre, se crean aqu?)
                self_aliases = set()
                for col in select.split(","):
                    col = col.strip()
                    if " as " in col.lower():
                        self_aliases.add(col.lower().split(" as ")[-1].strip())
                self_aliases |= set(group_by)

                ref_cols = re.findall(r'\b([a-zA-Z_]\w*)\b', where)
                skip = {
                    "AND", "OR", "NOT", "IS", "NULL", "IN", "LIKE", "BETWEEN",
                    "true", "false", "TRUE", "FALSE",
                }
                string_vals = set(re.findall(r"'([^']+)'", where))

                for rc in ref_cols:
                    if rc in skip or rc.upper() in skip:
                        continue
                    if rc in string_vals or rc[0].isdigit():
                        continue
                    if rc in self_aliases:  # columna creada por este nodo
                        continue
                    if rc not in parent_cols:
                        warnings.append(
                            f"[!]  TRANSFORM '{node.name}': column '{rc}' in where clause "
                            f"may not exist in parent '{node.parents[0]}'"
                        )

        # Precalcular columnas para este nodo
        _infer_columns(node, dag, xfr_rules, col_cache, dml_schema)

    return errors, warnings
