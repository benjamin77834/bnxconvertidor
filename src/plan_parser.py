# src/plan_parser.py
"""
Parses Ab Initio PLAN and PSET files.
PLAN: execution order, dependencies between graphs.
PSET: runtime parameters (paths, connections, thresholds).
Generates .mp with orchestration DAG.
Supports "Grafo de Grafos": multiple .mp files referenced from a PLAN.
"""
import re
import os
from dataclasses import dataclass, field


def parse_plan(path):
    """Parse a .plan file into graphs with dependencies."""
    graphs = {}
    plan_name = ""
    current = None

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Plan name
            m = re.match(r"PLAN\s+(\w+)", line, re.I)
            if m:
                plan_name = m.group(1)
                continue

            # Version
            if line.upper().startswith("VERSION"):
                continue

            # Graph definition
            m = re.match(r"GRAPH\s+(\w+)", line, re.I)
            if m:
                current = m.group(1)
                graphs[current] = {
                    "name": current,
                    "mp": None, "xfr": None, "dml": None,
                    "depends": [],
                    "schedule": None,
                    "priority": "MEDIUM",
                    "on_success": None,
                    "on_failure": None,
                    "max_iterations": None,
                    "convergence": None,
                }
                continue

            if current:
                # Properties
                m = re.match(r"MP:\s*(.+)", line, re.I)
                if m: graphs[current]["mp"] = m.group(1).strip(); continue

                m = re.match(r"XFR:\s*(.+)", line, re.I)
                if m: graphs[current]["xfr"] = m.group(1).strip(); continue

                m = re.match(r"DML:\s*(.+)", line, re.I)
                if m: graphs[current]["dml"] = m.group(1).strip(); continue

                m = re.match(r"DEPENDS:\s*(.+)", line, re.I)
                if m:
                    deps = [d.strip() for d in m.group(1).split(",")]
                    graphs[current]["depends"] = deps
                    continue

                m = re.match(r"SCHEDULE:\s*(.+)", line, re.I)
                if m: graphs[current]["schedule"] = m.group(1).strip(); continue

                m = re.match(r"PRIORITY:\s*(.+)", line, re.I)
                if m: graphs[current]["priority"] = m.group(1).strip().upper(); continue

                m = re.match(r"ON_SUCCESS:\s*(.+)", line, re.I)
                if m: graphs[current]["on_success"] = m.group(1).strip(); continue

                m = re.match(r"ON_FAILURE:\s*(.+)", line, re.I)
                if m: graphs[current]["on_failure"] = m.group(1).strip(); continue

                m = re.match(r"MAX_ITERATIONS:\s*(.+)", line, re.I)
                if m: graphs[current]["max_iterations"] = int(m.group(1).strip()); continue

                m = re.match(r"CONVERGENCE:\s*(.+)", line, re.I)
                if m: graphs[current]["convergence"] = m.group(1).strip(); continue

    return {"name": plan_name, "graphs": graphs}


def parse_pset(path):
    """Parse a .pset file into key-value parameters.
    Supports both formats:
    - BNX simple: KEY = VALUE
    - Ab Initio native: KEY||||VALUE
    """
    params = {}

    with open(path, "r") as f:
        content = f.read()

    # Auto-detect format
    is_native = "||||" in content or content.strip().startswith("!prototype")

    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if is_native:
            # Skip prototype header
            if line.startswith("!prototype"):
                continue
            # Formato nativo Ab Initio. El separador entre NOMBRE y VALOR puede ser:
            #   NOMBRE||||VALOR         (4 pipes, sin flag de tipo)
            #   NOMBRE|FLAG|||VALOR     (1 pipe + flag de 1 char + 3 pipes)
            # donde FLAG es un caracter de tipo/scope (p.ej. $, c, P, |c|).
            # Ejemplos reales:
            #   V_FILE_NAME||||ALS_ACCRL_MAST_D
            #   V_MF_FILE_NAME|$|||$ECS_FILE_TRALS.BXM...
            #   OUT_FILE_DML|c|||DRI_${S_CNTRY_CDE}_${V_FILE_NAME}_OUT.dml
            m = re.match(r"(\w+)\|(?:[^|]?)\|{3}(.*)", line)  # NOMBRE|FLAG|||VALOR
            if not m:
                m = re.match(r"(\w+)\|{4}(.*)", line)          # NOMBRE||||VALOR
            if m:
                key = m.group(1).strip()
                val = m.group(2).strip()
                # Guardamos el valor tal cual (puede referenciar otras vars $ECS_*,
                # ${VAR} o PDL $[...]); la resolucion final la hace el entorno del job.
                params[key] = val
                continue
        else:
            # BNX simple format: KEY = VALUE
            m = re.match(r"(\w+)\s*=\s*(.+)", line)
            if m:
                params[m.group(1)] = m.group(2).strip()
                continue

    # Resolver referencias internas ${VAR} usando los valores del propio pset.
    # Ej: OUT_FILE_DML = DRI_${S_CNTRY_CDE}_${V_FILE_NAME}_OUT.dml
    #     -> DRI_484_ALS_ACCRL_MAST_D_OUT.dml
    # Las referencias a variables externas ($ECS_*, ${VAR} no definida en el pset)
    # se dejan tal cual: se resuelven en el entorno del job.
    def _resolve(val, seen):
        if not isinstance(val, str) or "${" not in val:
            return val
        def _rep(mm):
            name = mm.group(1)
            if name in params and name not in seen:
                return _resolve(params[name], seen | {name})
            return mm.group(0)  # no definida: dejar ${VAR}
        return re.sub(r"\$\{(\w+)\}", _rep, val)

    for k in list(params.keys()):
        params[k] = _resolve(params[k], {k})

    return params


def plan_to_graph(parsed_plan, parsed_pset=None):
    """Convert parsed PLAN to .mp format with orchestration DAG."""
    graphs = parsed_plan["graphs"]
    pset = parsed_pset or {}

    mp_lines = [f"# Auto-generated from Ab Initio PLAN: {parsed_plan['name']}", ""]

    # Determine node types based on name patterns
    for name, g in graphs.items():
        if any(k in name.lower() for k in ["ingest", "read", "load"]):
            ntype = "SOURCE"
        elif any(k in name.lower() for k in ["report", "write", "notify", "export"]):
            ntype = "SINK"
        elif any(k in name.lower() for k in ["join", "enrich", "merge"]):
            ntype = "JOIN"
        elif any(k in name.lower() for k in ["dedup"]):
            ntype = "DEDUP"
        elif any(k in name.lower() for k in ["agg", "total", "balance", "revenue"]):
            ntype = "TRANSFORM"
        elif any(k in name.lower() for k in ["clean", "filter", "validate"]):
            ntype = "TRANSFORM"
        elif any(k in name.lower() for k in ["risk", "aml", "fraud", "score"]):
            ntype = "TRANSFORM"
        else:
            ntype = "TRANSFORM"
        g["node_type"] = ntype

    # Group by phase (based on dependencies depth)
    phases = {}
    def get_depth(name, visited=None):
        if visited is None: visited = set()
        if name in visited: return 0
        visited.add(name)
        g = graphs.get(name)
        if not g or not g["depends"]: return 0
        return 1 + max(get_depth(d, visited) for d in g["depends"] if d in graphs)

    for name in graphs:
        depth = get_depth(name)
        if depth not in phases: phases[depth] = []
        phases[depth].append(name)

    # Write subgraphs by phase
    for depth in sorted(phases.keys()):
        phase_name = f"Phase_{depth}"
        mp_lines.append(f"SUBGRAPH {phase_name} {{")
        for name in phases[depth]:
            g = graphs[name]
            mp_lines.append(f"  NODE {name} : {g['node_type']}")
        mp_lines.append("}")
        mp_lines.append("")

    # Write edges from dependencies
    for name, g in graphs.items():
        for dep in g["depends"]:
            if dep in graphs:
                mp_lines.append(f"{dep} -> {name}")

    # Generate XFR with PSET parameters
    xfr_lines = [f"# Auto-generated from Ab Initio PLAN + PSET", ""]

    s3_input = pset.get("S3_INPUT", "s3://datalake/raw")
    s3_output = pset.get("S3_OUTPUT", "s3://datalake/curated")
    output_format = pset.get("OUTPUT_FORMAT", "parquet").lower()
    kafka_brokers = pset.get("KAFKA_BROKERS")
    kafka_topic = pset.get("KAFKA_TOPIC_EVENTS")

    for name, g in graphs.items():
        ntype = g["node_type"]
        if ntype == "SOURCE":
            xfr_lines.append(f"{name}:")
            if kafka_brokers and "event" in name.lower():
                xfr_lines.append(f"  source_type kafka")
                xfr_lines.append(f"  topic {kafka_topic or 'events'}")
                xfr_lines.append(f"  connection {kafka_brokers}")
            else:
                xfr_lines.append(f"  source_type s3")
                xfr_lines.append(f"  path {s3_input}/{name.lower()}")
                xfr_lines.append(f"  format {output_format}")
            xfr_lines.append("")
        elif ntype == "SINK":
            xfr_lines.append(f"{name}:")
            xfr_lines.append(f"  sink_type s3")
            xfr_lines.append(f"  path {s3_output}/{name.lower()}")
            xfr_lines.append(f"  format {output_format}")
            xfr_lines.append(f"  mode overwrite")
            xfr_lines.append("")
        elif ntype == "JOIN" and g["depends"]:
            xfr_lines.append(f"{name}:")
            xfr_lines.append(f"  join_key customer_id")
            xfr_lines.append(f"  join_type left")
            xfr_lines.append("")
        elif ntype == "DEDUP":
            xfr_lines.append(f"{name}:")
            xfr_lines.append(f"  dedup_keys tx_id")
            xfr_lines.append(f"  order_by tx_date")
            xfr_lines.append("")

    return {
        "mp": "\n".join(mp_lines),
        "xfr": "\n".join(xfr_lines),
        "pset": pset,
    }


# ???????????????????????????????????????????????????????????????
# GRAFO DE GRAFOS ? Multi-MP support
# ???????????????????????????????????????????????????????????????

@dataclass
class ResolvedGraph:
    """Represents a single graph resolved from a PLAN."""
    name: str
    ast: dict                          # {nodes, edges, subgraphs}
    xfr_rules: dict = field(default_factory=dict)
    dml_schema: dict = field(default_factory=dict)
    is_auto_generated: bool = False
    depends: list = field(default_factory=list)


def substitute_pset_params(content, pset_params):
    """
    Replace ${PARAM_NAME} in content with PSET values.
    Returns (substituted_content, warnings).
    """
    warnings = []
    used = set()

    def replacer(m):
        key = m.group(1)
        if key in pset_params:
            used.add(key)
            return pset_params[key]
        warnings.append(f"[!]  PSET parameter '${{{key}}}' is not defined")
        return m.group(0)  # leave unchanged

    result = re.sub(r'\$\{(\w+)\}', replacer, content)
    return result, warnings


def namespace_ast(ast, graph_name):
    """
    Prefix all node IDs with '{graph_name}__'.
    Preserves original node name as display name.
    """
    prefix = f"{graph_name}__"
    id_map = {}

    new_nodes = []
    for node in ast["nodes"]:
        new_id = prefix + node["id"]
        id_map[node["id"]] = new_id
        new_nodes.append({
            **node,
            "id": new_id,
            "name": node["name"],
            "subgraph": graph_name,
            "source_graph": graph_name,
        })

    new_edges = []
    for edge in ast.get("edges", []):
        new_edges.append({
            "from": id_map.get(edge["from"], prefix + edge["from"]),
            "to": id_map.get(edge["to"], prefix + edge["to"]),
        })

    new_subgraphs = {}
    for sg_name, node_ids in ast.get("subgraphs", {}).items():
        new_sg_name = f"{graph_name}__{sg_name}"
        new_subgraphs[new_sg_name] = [id_map.get(nid, prefix + nid) for nid in node_ids]
    # Add the whole graph as a subgraph
    new_subgraphs[graph_name] = [n["id"] for n in new_nodes]

    return {"nodes": new_nodes, "edges": new_edges, "subgraphs": new_subgraphs}


def detect_retrocesos(parsed_plan):
    """
    Detect backward references (feedback loops) in GRAPH dependencies.
    Also detects SCHEDULE: CYCLIC graphs.
    Returns list of (from_graph, to_graph) tuples that form cycles.
    """
    graphs = parsed_plan["graphs"]
    adj = {name: g.get("depends", []) for name, g in graphs.items()}
    retrocesos = []

    def can_reach(start, target, visited=None):
        if visited is None:
            visited = set()
        if start == target:
            return True
        if start in visited:
            return False
        visited.add(start)
        for dep in adj.get(start, []):
            if can_reach(dep, target, visited):
                return True
        return False

    for name, g in graphs.items():
        for dep in g.get("depends", []):
            if dep in graphs and can_reach(dep, name):
                retrocesos.append((name, dep))

    # Also detect SCHEDULE: CYCLIC ? self-loops (graph depends on itself implicitly)
    for name, g in graphs.items():
        if (g.get("schedule") or "").upper() == "CYCLIC" and not any(r[0] == name for r in retrocesos):
            # A cyclic graph creates a self-loop retroceso
            retrocesos.append((name, name))

    return retrocesos


def resolve_graph_references(parsed_plan, mp_files=None, pset_params=None, base_dir=None):
    """
    For each GRAPH in the PLAN:
    - If it has an MP property and the file exists ? parse it
    - If MP property but file missing ? error
    - If no MP property ? auto-generate with plan_to_graph logic
    Returns (list[ResolvedGraph], errors, warnings).
    """
    from src.mp_parser import parse_mp_ast
    from src.xfr_parser import parse_xfr
    from src.dml_parser import parse_dml

    mp_files = mp_files or {}
    pset_params = pset_params or {}
    graphs = parsed_plan["graphs"]
    resolved = []
    errors = []
    warnings = []

    for name, g in graphs.items():
        mp_ref = g.get("mp")
        xfr_ref = g.get("xfr")
        dml_ref = g.get("dml")

        # --- Resolve MP ---
        ast = None
        is_auto = False

        if mp_ref:
            # Check mp_files dict first (uploaded files), then filesystem
            mp_path = mp_files.get(mp_ref) or mp_files.get(os.path.basename(mp_ref))
            if not mp_path and base_dir:
                candidate = os.path.join(base_dir, mp_ref)
                if os.path.exists(candidate):
                    mp_path = candidate
            if not mp_path:
                # Try the ref as absolute/relative path
                if os.path.exists(mp_ref):
                    mp_path = mp_ref

            if mp_path and os.path.exists(mp_path):
                ast = parse_mp_ast(mp_path)
            else:
                errors.append(f"? GRAPH '{name}': MP file '{mp_ref}' not found or unreadable")
                continue
        else:
            # Auto-generate a simple single-node graph for this GRAPH
            # Use plan_to_graph logic for this single graph
            single_plan = {"name": parsed_plan["name"], "graphs": {name: g}}
            auto = plan_to_graph(single_plan, pset_params)
            import tempfile
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp", mode="w")
            tmp.write(auto["mp"])
            tmp.close()
            ast = parse_mp_ast(tmp.name)
            os.unlink(tmp.name)
            is_auto = True
            warnings.append(f"[!]  GRAPH '{name}': no MP file, auto-generating graph")

        # Namespace the AST
        ast = namespace_ast(ast, name)

        # --- Resolve XFR ---
        xfr_rules = {}
        if xfr_ref:
            xfr_path = mp_files.get(xfr_ref) or mp_files.get(os.path.basename(xfr_ref))
            if not xfr_path and base_dir:
                candidate = os.path.join(base_dir, xfr_ref)
                if os.path.exists(candidate):
                    xfr_path = candidate
            if not xfr_path and os.path.exists(xfr_ref):
                xfr_path = xfr_ref

            if xfr_path and os.path.exists(xfr_path):
                # Read, substitute PSET params, then parse
                with open(xfr_path, "r") as f:
                    xfr_content = f.read()
                xfr_content, pset_warns = substitute_pset_params(xfr_content, pset_params)
                for w in pset_warns:
                    warnings.append(f"GRAPH '{name}': {w}")
                # Write substituted content to temp and parse
                import tempfile
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xfr", mode="w")
                tmp.write(xfr_content)
                tmp.close()
                xfr_rules = parse_xfr(tmp.name)
                os.unlink(tmp.name)
            else:
                warnings.append(f"[!]  GRAPH '{name}': XFR file '{xfr_ref}' not found, using default rules")

        # --- Resolve DML ---
        dml_schema = {}
        if dml_ref:
            dml_path = mp_files.get(dml_ref) or mp_files.get(os.path.basename(dml_ref))
            if not dml_path and base_dir:
                candidate = os.path.join(base_dir, dml_ref)
                if os.path.exists(candidate):
                    dml_path = candidate
            if not dml_path and os.path.exists(dml_ref):
                dml_path = dml_ref

            if dml_path and os.path.exists(dml_path):
                dml_data = parse_dml(dml_path)
                dml_schema = dml_data.get("schema", {})
            else:
                warnings.append(f"[!]  GRAPH '{name}': DML file '{dml_ref}' not found, using default schema")

        resolved.append(ResolvedGraph(
            name=name,
            ast=ast,
            xfr_rules=xfr_rules,
            dml_schema=dml_schema,
            is_auto_generated=is_auto,
            depends=g.get("depends", []),
        ))
        # Attach cycle config from GRAPH properties and PSET
        resolved[-1]._max_iterations = g.get("max_iterations") or pset_params.get("MAX_ITERATIONS")
        resolved[-1]._convergence = g.get("convergence") or pset_params.get("CONVERGENCE")
        if resolved[-1]._max_iterations:
            try:
                resolved[-1]._max_iterations = int(resolved[-1]._max_iterations)
            except (ValueError, TypeError):
                resolved[-1]._max_iterations = 5
        # Also store PSET versions for fallback
        resolved[-1]._pset_max_iterations = int(pset_params.get("MAX_ITERATIONS", 5)) if pset_params.get("MAX_ITERATIONS") else 5
        resolved[-1]._pset_convergence = pset_params.get("CONVERGENCE")

    return resolved, errors, warnings


def _create_cross_graph_edges(resolved_graphs, dependencies, retrocesos):
    """Create edges between graphs based on DEPENDS relationships."""
    cross_edges = []
    retroceso_set = set(retrocesos)
    graph_map = {g.name: g for g in resolved_graphs}

    for graph_name, deps in dependencies.items():
        g = graph_map.get(graph_name)
        if not g:
            continue
        target_sources = [n for n in g.ast["nodes"] if n["type"].upper() == "SOURCE"]

        for dep_name in deps:
            dep_g = graph_map.get(dep_name)
            if not dep_g:
                continue

            edge_type = "retroceso" if (graph_name, dep_name) in retroceso_set else "normal"

            # Self-loop retroceso (SCHEDULE: CYCLIC)
            if graph_name == dep_name:
                dep_sinks = [n for n in g.ast["nodes"] if n["type"].upper() == "SINK"]
                target_sources_self = [n for n in g.ast["nodes"] if n["type"].upper() == "SOURCE"]
                for sink in dep_sinks:
                    for source in target_sources_self:
                        edge = {
                            "from": sink["id"],
                            "to": source["id"],
                            "source_graph": graph_name,
                            "target_graph": graph_name,
                            "type": "retroceso",
                            "cross_graph": True,
                            "self_loop": True,
                        }
                        edge["max_iterations"] = getattr(g, '_max_iterations', None) or getattr(g, '_pset_max_iterations', 5)
                        edge["convergence"] = getattr(g, '_convergence', None) or getattr(g, '_pset_convergence', None)
                        cross_edges.append(edge)
                continue

            dep_sinks = [n for n in dep_g.ast["nodes"] if n["type"].upper() == "SINK"]

            edge_type = "retroceso" if (graph_name, dep_name) in retroceso_set else "normal"

            for sink in dep_sinks:
                for source in target_sources:
                    edge = {
                        "from": sink["id"],
                        "to": source["id"],
                        "source_graph": dep_name,
                        "target_graph": graph_name,
                        "type": edge_type,
                        "cross_graph": True,
                    }
                    if edge_type == "retroceso":
                        # Get iteration config from graph or PSET
                        edge["max_iterations"] = getattr(g, '_max_iterations', None) or getattr(g, '_pset_max_iterations', 5)
                        edge["convergence"] = getattr(g, '_convergence', None) or getattr(g, '_pset_convergence', None)
                    cross_edges.append(edge)

    return cross_edges


def merge_asts(resolved_graphs, dependencies, retrocesos):
    """
    Combine all namespaced ASTs into a single unified AST.
    Creates cross-graph edges based on dependencies.
    """
    all_nodes = []
    all_edges = []
    all_subgraphs = {}

    for g in resolved_graphs:
        all_nodes.extend(g.ast["nodes"])
        all_edges.extend(g.ast["edges"])
        all_subgraphs.update(g.ast.get("subgraphs", {}))

    # Add self-loop retrocesos to dependencies
    extended_deps = {k: list(v) for k, v in dependencies.items()}
    for (from_g, to_g) in retrocesos:
        if from_g == to_g and from_g not in extended_deps.get(from_g, []):
            if from_g not in extended_deps:
                extended_deps[from_g] = []
            extended_deps[from_g].append(from_g)

    cross_edges = _create_cross_graph_edges(resolved_graphs, extended_deps, retrocesos)

    # Separate retroceso edges
    normal_cross = [e for e in cross_edges if e.get("type") != "retroceso"]
    retroceso_cross = [e for e in cross_edges if e.get("type") == "retroceso"]

    # Add normal cross-graph edges to the main edge list
    all_edges.extend(normal_cross)

    return {
        "nodes": all_nodes,
        "edges": all_edges,
        "subgraphs": all_subgraphs,
        "cross_graph_edges": cross_edges,
        "retroceso_edges": retroceso_cross,
    }


def pretty_print_mega_dag(merged_ast):
    """Serialize a Mega-DAG to readable .mp format."""
    lines = ["# Mega-DAG ? Grafo de Grafos", ""]

    subgraphs = merged_ast.get("subgraphs", {})
    nodes_by_id = {n["id"]: n for n in merged_ast["nodes"]}

    # Write subgraphs
    for sg_name, node_ids in subgraphs.items():
        # Skip nested subgraphs (only write top-level graph subgraphs)
        if "__" in sg_name:
            continue
        lines.append(f"SUBGRAPH {sg_name} {{")
        for nid in node_ids:
            node = nodes_by_id.get(nid)
            if node:
                lines.append(f"  NODE {nid} : {node['type']}")
        lines.append("}")
        lines.append("")

    # Write intra-graph edges
    lines.append("# Intra-graph edges")
    for edge in merged_ast["edges"]:
        if not edge.get("cross_graph"):
            lines.append(f"{edge['from']} -> {edge['to']}")

    # Write cross-graph edges
    cross = merged_ast.get("cross_graph_edges", [])
    if cross:
        lines.append("")
        lines.append("# Cross-graph edges")
        for edge in cross:
            tag = " [retroceso]" if edge.get("type") == "retroceso" else ""
            lines.append(f"# {edge.get('source_graph', '?')} -> {edge.get('target_graph', '?')}{tag}")
            lines.append(f"{edge['from']} -> {edge['to']}")

    return "\n".join(lines)
