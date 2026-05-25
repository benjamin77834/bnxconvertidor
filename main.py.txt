# main.py
import argparse
import re
from src.mp_parser import parse_mp_ast
from src.dag.builder import build_dag
from src.xfr_parser import parse_xfr
from src.dml_parser import parse_dml
from src.plan_parser import parse_pset
from src.codegen.glue_codegen import generate_glue
from src.codegen.spark_codegen import generate_spark
from src.codegen.flink_codegen import generate_flink
from src.validator.semantic import validate
from src.accuracy import compute_accuracy


# ============================================================
# GDE Native Parser (Ab Initio serialized .mp format)
# Handles: XXGgraph_vertex_vertex, XXGobject_proto_object,
#           XXGiport_src_flow, XXparameter, XXGraph_flow_flow
# ============================================================

def _is_gde_format(content):
    """Detect if file is GDE serialized format (not text-based)."""
    return ("XXGgraph" in content or "XXGrepository" in content or
            "XXGobject_proto_object" in content or "XXGraph_flow_flow" in content)


def _map_component_type(name):
    """Map Ab Initio component/vertex name to BNX node type."""
    n = name.lower()
    if any(k in n for k in ["read", "input", "scan", "source", "extract", "ingest"]):
        return "SOURCE"
    if any(k in n for k in ["write", "output", "sink", "load", "target"]):
        return "SINK"
    if any(k in n for k in ["merge", "join", "lookup"]):
        return "JOIN"
    if any(k in n for k in ["filter", "select", "where", "filter_by"]):
        return "FILTER"
    if any(k in n for k in ["partition", "repartition", "round_robin"]):
        return "PARTITION"
    if any(k in n for k in ["dedup", "deduplicate", "remove_dup"]):
        return "DEDUP"
    if any(k in n for k in ["normalize", "denormalize"]):
        return "NORMALIZE"
    if any(k in n for k in ["concatenate", "gather", "combine", "fuse"]):
        return "CONCATENATE"
    if any(k in n for k in ["rollup", "aggregate", "summary"]):
        return "TRANSFORM"
    if any(k in n for k in ["sort", "sort_within"]):
        return "TRANSFORM"
    if any(k in n for k in ["reformat", "transform", "compute", "copy",
                             "replicate", "leading", "run_dml", "create_data",
                             "dml_script"]):
        return "TRANSFORM"
    return "TRANSFORM"


def _parse_gde_native(content):
    """Parse GDE serialized Ab Initio .mp format.
    
    Extracts:
    - Nodes from XXGgraph_vertex_vertex lines (component instances)
    - Edges from XXGraph_flow_flow lines (data flows between components)
    - Parameters from XXparameter lines
    """
    nodes = []
    edges = []
    params = {}
    
    # Maps: numeric_id -> node info
    vertex_map = {}   # vertex_id -> {name, node_id}
    flow_map = {}     # flow connections
    
    # First pass: extract all vertices (components) and flows
    for line in content.split("\n"):
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        
        # Parameters: {30001002|XXparameter|NAME|...|...}
        m = re.match(r'\{(\d+)\|XXparameter\|([^|]+)\|', line)
        if m:
            param_name = m.group(2).strip()
            # Try to get value - it's complex in GDE format
            # Format: {code|XXparameter|NAME|pos|size|RFK||{default}|}
            # We store the param name for reference
            params[param_name] = ""
            # Try to extract value after RFK
            val_match = re.search(r'RFK\|([^|{}\n]+)', line)
            if val_match:
                params[param_name] = val_match.group(1).strip()
            continue
        
        # Graph vertex (component instance):
        # {2010601001|XXGgraph_vertex_vertex|ID|0|POS|0|{NAME|SRC_ID|DST_ID|}
        m = re.match(r'\{\d+\|XXGgraph_vertex_vertex\|(\d+)\|\d+\|\d+\|\d+\|\{([^|]+)\|(\d+)\|(\d+)\|', line)
        if m:
            vid = m.group(1)
            name = m.group(2).strip()
            src_id = m.group(3)
            dst_id = m.group(4)
            vertex_map[vid] = {"name": name, "src_id": src_id, "dst_id": dst_id}
            continue
        
        # Flow (edge between components):
        # {2010604001|XXGraph_flow_flow|ID|0|POS|0|{NAME|FROM_ID|TO_ID|}
        m = re.match(r'\{\d+\|XXGraph_flow_flow\|(\d+)\|\d+\|\d+\|\d+\|\{([^|]+)\|(\d+)\|(\d+)\|', line)
        if m:
            fid = m.group(1)
            fname = m.group(2).strip()
            from_id = m.group(3)
            to_id = m.group(4)
            flow_map[fid] = {"name": fname, "from": from_id, "to": to_id}
            continue
        
        # Proto object (component definition with name):
        # {2010007001|XXGobject_proto_object|ID|0|POS|0|{VERTEX_ID|...|}
        m = re.match(r'\{\d+\|XXGobject_proto_object\|(\d+)\|\d+\|\d+\|\d+\|\{(\d+)\|', line)
        if m:
            # This links a proto to a vertex
            continue
        
        # Psameas object (component metadata/params):
        # {2010006001|XXGobject_psameas_object|ID|0|POS|0|{NAME|VALUE|...}
        m = re.match(r'\{\d+\|XXGobject_psameas_object\|(\d+)\|\d+\|\d+\|\d+\|\{([^|]+)\|([^|]*)\|', line)
        if m:
            pname = m.group(2).strip()
            pval = m.group(3).strip()
            if pname and pname not in ("Layout", "metadata"):
                params[pname] = pval
            continue
    
    # Build node list from vertices
    # vertex_map has entries like: {name, src_id, dst_id}
    # These represent connections: src_id -> name -> dst_id
    # We need to identify unique component IDs
    
    # Collect all unique component IDs referenced
    component_ids = set()
    component_names = {}  # id -> name
    
    for vid, info in vertex_map.items():
        src = info["src_id"]
        dst = info["dst_id"]
        name = info["name"]
        # The vertex_vertex entries define named connections between component IDs
        component_ids.add(src)
        component_ids.add(dst)
        # The name is the connection/component name
        if name and not name.startswith("Component"):
            component_names[src] = component_names.get(src, name)
    
    # Also get names from flow_map
    for fid, info in flow_map.items():
        from_id = info["from"]
        to_id = info["to"]
        component_ids.add(from_id)
        component_ids.add(to_id)
    
    # Build edges from vertex_vertex (these ARE the edges)
    edge_set = set()
    for vid, info in vertex_map.items():
        src = info["src_id"]
        dst = info["dst_id"]
        if src != dst:
            edge_set.add((src, dst))
    
    # Add edges from flow_flow
    for fid, info in flow_map.items():
        from_id = info["from"]
        to_id = info["to"]
        if from_id != to_id:
            edge_set.add((from_id, to_id))
    
    # Now we need to figure out which IDs are actual components
    # Components are IDs that appear as src or dst in edges
    all_edge_ids = set()
    for s, d in edge_set:
        all_edge_ids.add(s)
        all_edge_ids.add(d)
    
    # Assign names to component IDs
    # Use vertex_vertex names as edge labels, and psameas names as component names
    # The vertex_vertex "name" field is actually the component/connection name
    node_id_map = {}  # numeric_id -> node_id string
    
    for vid, info in vertex_map.items():
        name = info["name"]
        src = info["src_id"]
        dst = info["dst_id"]
        # Assign name to the destination (the component being connected TO)
        if name and dst in all_edge_ids:
            if dst not in node_id_map:
                safe_name = re.sub(r'[^\w]', '_', name)
                node_id_map[dst] = safe_name
        if name and src in all_edge_ids:
            if src not in node_id_map:
                safe_name = re.sub(r'[^\w]', '_', name)
                node_id_map[src] = safe_name
    
    # Fill unnamed components
    for cid in all_edge_ids:
        if cid not in node_id_map:
            node_id_map[cid] = f"Component_{cid}"
    
    # Deduplicate node names
    seen_names = {}
    for cid in list(node_id_map.keys()):
        name = node_id_map[cid]
        if name in seen_names:
            seen_names[name] += 1
            node_id_map[cid] = f"{name}_{seen_names[name]}"
        else:
            seen_names[name] = 0
    
    # Create node list
    for cid, nid in node_id_map.items():
        ntype = _map_component_type(nid)
        nodes.append({
            "id": nid,
            "name": nid,
            "type": ntype,
            "params": "",
            "subgraph": None,
        })
    
    # Create edge list
    for src, dst in edge_set:
        if src in node_id_map and dst in node_id_map:
            edges.append({
                "from": node_id_map[src],
                "to": node_id_map[dst],
            })
    
    print(f"[i] GDE Parser: {len(nodes)} nodes, {len(edges)} edges, {len(params)} params")
    
    return {"nodes": nodes, "edges": edges, "subgraphs": {}, "abinitio_params": params}


def parse_project(file_path):
    """Smart parser: detects format and parses accordingly."""
    with open(file_path, "r", errors="replace") as f:
        content = f.read()
    
    if _is_gde_format(content):
        print("[i] Detected: GDE native format (Ab Initio serialized)")
        return _parse_gde_native(content)
    else:
        print("[i] Detected: BNX/text format")
        return parse_mp_ast(file_path)


# ============================================================
# Main
# ============================================================

def main(project_path, output_path, xfr_path=None, dml_path=None, pset_path=None, target="glue"):
    print("[*] BNX V54 START\n")

    # Parse PSET parameters
    pset_params = {}
    if pset_path:
        pset_params = parse_pset(pset_path)
        print(f"[i] PSET loaded: {len(pset_params)} parameters")
        for k, v in list(pset_params.items())[:5]:
            print(f"    {k} = {v}")
        if len(pset_params) > 5:
            print(f"    ... and {len(pset_params) - 5} more")
        print()

    # Parse project (auto-detects GDE vs BNX format)
    ast = parse_project(project_path)
    dag = build_dag(ast)
    xfr_rules = parse_xfr(xfr_path) if xfr_path else {}
    dml = parse_dml(dml_path) if dml_path else {}
    dml_schema = dml.get("schema", {})

    if dml_schema:
        print(f"[i] DML schema loaded: {list(dml_schema.keys())}\n")

    # Validacion semantica
    errors, warnings = validate(dag, xfr_rules, dml_schema)
    for w in warnings:
        print(w)
    if errors:
        blocking = [e for e in errors if "no parent nod" not in e]
        non_blocking = [e for e in errors if "no parent nod" in e]
        if non_blocking:
            print(f"\n[w] WARNINGS (non-blocking): {len(non_blocking)} nodes without parent")
        if blocking:
            print("\n[!] VALIDATION FAILED:")
            for e in blocking:
                print(f"  {e}")
            print("\nFix the errors above before generating code.")
            return
    print("[ok] Validation passed\n")

    print("[>] EXECUTION ORDER:")
    for i, node in enumerate(dag.execution_order, start=1):
        print(f"  {i}. {node.name} ({node.type})")

    if target == "spark":
        generate_spark(dag, output_path, xfr_rules)
        print(f"\n[>] Target: PySpark")
    elif target == "flink":
        generate_flink(dag, output_path, xfr_rules)
        print(f"\n[>] Target: Apache Flink (PyFlink)")
    else:
        generate_glue(dag, output_path, xfr_rules)
        print(f"\n[>] Target: AWS Glue")

    # Accuracy report
    acc = compute_accuracy(dag, xfr_rules, dml_schema)
    print(f"\n[>] ACCURACY REPORT:")
    print(f"  Nodes:      {acc['resolved_nodes']}/{acc['total_nodes']} ({acc['node_accuracy']}%)")
    print(f"  Edges:      {acc['resolved_edges']}/{acc['total_edges']} ({acc['edge_accuracy']}%)")
    print(f"  Transforms: {acc['resolved_transforms']}/{acc['total_transforms']} ({acc['transform_accuracy']}%)")
    print(f"  Joins:      {acc['resolved_joins']}/{acc['total_joins']} ({acc['join_accuracy']}%)")
    print(f"  Overall:    {acc['overall_accuracy']}%")
    if acc['details']:
        print(f"\n  [!] Issues ({len(acc['details'])}):")
        for d in acc['details']:
            print(f"    {d['node']} ({d['type']}): {', '.join(d['issues'])}")

    print(f"\n[ok] Generated: {output_path}")
    print("[*] BNX V54 DONE\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--xfr", required=False, default=None)
    parser.add_argument("--dml", required=False, default=None)
    parser.add_argument("--pset", required=False, default=None)
    parser.add_argument("--target", choices=["glue", "spark", "flink"], default="glue")
    args = parser.parse_args()
    main(args.project, args.output, args.xfr, args.dml, args.pset, args.target)
