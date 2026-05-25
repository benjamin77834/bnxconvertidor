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
    
    # First pass: extract components, ports, and flows
    # Components: }@1|TYPE|...|ID|DISPLAY_NAME|Ab Initio Software|...
    # Vertex ports: XXGvertex_oport → {0|out|}VERTEX_ID|PORT_ID|}
    #               XXGvertex_iport → {0|in|}VERTEX_ID|PORT_ID|}
    # Flow connections: XXGoport_dst_flow → {0|}PORT_ID|FLOW_ID|}  (output port goes to flow)
    #                   XXGiport_src_flow → {0|}PORT_ID|FLOW_ID|}  (input port comes from flow)
    # Edge logic: oport of vertex A → flow F → iport of vertex B  =  A → B
    
    node_by_id = {}       # component_id (large) -> {name, type, display_name}
    vertex_to_comp = {}   # small vertex_id -> component_id (large) -- built later
    
    # Port mappings
    oport_to_vertex = {}  # output_port_id -> vertex_id
    iport_to_vertex = {}  # input_port_id -> vertex_id
    oport_to_flow = {}    # output_port_id -> flow_id
    iport_from_flow = {}  # input_port_id -> flow_id
    
    # Track vertex IDs (small numbers from port definitions)
    vertex_ids = set()
    
    # Extract ports and flows using findall on entire content (file may have binary/non-standard line endings)
    # Output ports: {2010212001|XXGvertex_oport|17|0|34|0|{0|out|}17|18|}
    for m in re.finditer(r'XXGvertex_oport\|[^{]*\{0\|out\d*\|\}(\d+)\|(\d+)\|', content):
        vertex_id = m.group(1)
        port_id = m.group(2)
        oport_to_vertex[port_id] = vertex_id
        vertex_ids.add(vertex_id)
    
    # Input ports: {2010211001|XXGvertex_iport|19|0|37|0|{0|in|}17|19|}
    for m in re.finditer(r'XXGvertex_iport\|[^{]*\{0\|in\d*\|\}(\d+)\|(\d+)\|', content):
        vertex_id = m.group(1)
        port_id = m.group(2)
        iport_to_vertex[port_id] = vertex_id
        vertex_ids.add(vertex_id)
    
    # Oport to flow: {2010213001|XXGoport_dst_flow|20|0|39|0|{0|}19|6|}
    for m in re.finditer(r'XXGoport_dst_flow\|[^{]*\{0\|\}?(\d+)\|(\d+)\|', content):
        port_id = m.group(1)
        flow_id = m.group(2)
        oport_to_flow[port_id] = flow_id
    
    # Iport from flow: {2010214001|XXGiport_src_flow|18|0|36|0|{0|}18|5|}
    for m in re.finditer(r'XXGiport_src_flow\|[^{]*\{0\|\}?(\d+)\|(\d+)\|', content):
        port_id = m.group(1)
        flow_id = m.group(2)
        iport_from_flow[port_id] = flow_id
    
    # Now parse line-by-line for components and parameters
    for line in re.split(r'[\r\n]+', content):
        line = line.strip()
        if not line:
            continue
        
        # Parameters: {30001002|XXparameter|NAME|...|...}
        if "|XXparameter|" in line:
            parts = line.split("|")
            if len(parts) >= 3:
                param_name = parts[2].strip()
                params[param_name] = ""
            continue
        
        # IMPORTANT: Check ports BEFORE component definitions
        # Ports are now extracted via findall above, skip them here
        if "|XXGvertex_oport|" in line or "|XXGvertex_iport|" in line:
            continue
        
        # Flow connections also extracted above
        if "|XXGoport_dst_flow|" in line or "|XXGiport_src_flow|" in line:
            continue
        
        # Component definition: }@1|TYPE|positions...|ID|DISPLAY_NAME|Ab Initio Software|...
        if "}@1|" in line or "}0|" in line:
            for marker in ["}@1|", "}0|"]:
                idx = line.find(marker)
                while idx >= 0:
                    comp_str = line[idx + len(marker):]
                    parts = comp_str.split("|")
                    if len(parts) >= 9:
                        comp_type = parts[0].strip()
                        if comp_type and comp_type[0].isupper() and "XXG" not in comp_type:
                            comp_id = None
                            display_name = comp_type
                            for i in range(1, min(12, len(parts))):
                                val = parts[i].strip()
                                if val.isdigit() and int(val) > 100:
                                    if i + 1 < len(parts):
                                        next_val = parts[i + 1].strip()
                                        if next_val and not next_val.isdigit() and next_val[0].isalpha():
                                            comp_id = val
                                            display_name = next_val
                                            break
                            if comp_id and comp_id not in node_by_id:
                                ntype = _map_component_type(comp_type)
                                safe_name = re.sub(r'[^\w]', '_', display_name)
                                node_by_id[comp_id] = {
                                    "name": safe_name,
                                    "type": ntype,
                                    "display_name": display_name,
                                    "comp_type": comp_type,
                                }
                    next_idx = line.find(marker, idx + 1)
                    idx = next_idx
            continue
        
        # Vertex output port: {2010212001|XXGvertex_oport|17|0|34|0|{0|out|}17|18|}
        if "|XXGvertex_oport|" in line:
            # Exact format: {0|out|}VERTEX_ID|PORT_ID|}
            m = re.search(r'out\d*\|\}(\d+)\|(\d+)\|', line)
            if m:
                vertex_id = m.group(1)
                port_id = m.group(2)
                oport_to_vertex[port_id] = vertex_id
                vertex_ids.add(vertex_id)
            else:
                if len(oport_to_vertex) == 0 and len(vertex_ids) == 0:
                    # Debug: show first non-matching line
                    print(f"  [dbg] oport NO MATCH: {line[:100]}")
            continue
        
        # Vertex input port: {2010211001|XXGvertex_iport|19|0|37|0|{0|in|}17|19|}
        if "|XXGvertex_iport|" in line:
            m = re.search(r'in\d*\|\}(\d+)\|(\d+)\|', line)
            if m:
                vertex_id = m.group(1)
                port_id = m.group(2)
                iport_to_vertex[port_id] = vertex_id
                vertex_ids.add(vertex_id)
            else:
                if len(iport_to_vertex) == 0 and len(vertex_ids) == 0:
                    print(f"  [dbg] iport NO MATCH: {line[:100]}")
            continue
        
        # Output port to flow: {2010213001|XXGoport_dst_flow|20|0|39|0|{0|}19|6|}
        # Pattern: {0|}PORT_ID|FLOW_ID|}
        if "|XXGoport_dst_flow|" in line:
            m = re.search(r'\{0\|\}?(\d+)\|(\d+)\|', line)
            if m:
                port_id = m.group(1)
                flow_id = m.group(2)
                oport_to_flow[port_id] = flow_id
            continue
        
        # Input port from flow: {2010214001|XXGiport_src_flow|18|0|36|0|{0|}18|5|}
        if "|XXGiport_src_flow|" in line:
            m = re.search(r'\{0\|\}?(\d+)\|(\d+)\|', line)
            if m:
                port_id = m.group(1)
                flow_id = m.group(2)
                iport_from_flow[port_id] = flow_id
            continue
    
    # Build edges: oport → flow → iport
    # For each flow_id, find which output port sends to it and which input port receives from it
    # oport_to_flow: port_id -> flow_id (output port sends to this flow)
    # iport_from_flow: port_id -> flow_id (input port receives from this flow)
    
    # Invert: flow_id -> source_vertex (via oport)
    flow_to_src_vertex = {}
    for port_id, flow_id in oport_to_flow.items():
        if port_id in oport_to_vertex:
            flow_to_src_vertex[flow_id] = oport_to_vertex[port_id]
    
    # For each iport that receives from a flow, find the source vertex
    edge_set = set()
    for port_id, flow_id in iport_from_flow.items():
        if port_id in iport_to_vertex and flow_id in flow_to_src_vertex:
            src_vertex = flow_to_src_vertex[flow_id]
            dst_vertex = iport_to_vertex[port_id]
            if src_vertex != dst_vertex:
                edge_set.add((src_vertex, dst_vertex))
    
    # Now map vertex IDs (small) to component names
    # The vertex IDs from ports should correspond to the order of components
    # Try to match by looking at XXGpvertex lines that contain both vertex_id and component_id
    # For now, use vertex_ids directly as node identifiers if we can't map them
    
    # Debug output
    print(f"  [dbg] Components (at1): {len(node_by_id)}")
    print(f"  [dbg] Vertex IDs from ports: {len(vertex_ids)}")
    print(f"  [dbg] Output ports: {len(oport_to_vertex)}, Input ports: {len(iport_to_vertex)}")
    print(f"  [dbg] Oport->flow: {len(oport_to_flow)}, Iport<-flow: {len(iport_from_flow)}")
    print(f"  [dbg] Edges resolved: {len(edge_set)}")
    if edge_set:
        for i, (s, d) in enumerate(list(edge_set)[:5]):
            print(f"  [dbg] edge: vertex {s} -> vertex {d}")

    # Build final node and edge lists
    # We have two sets of IDs:
    # - node_by_id: large component IDs (32589, etc.) with names
    # - vertex_ids: small vertex IDs (17, 20, etc.) from port definitions
    # - edge_set: edges between small vertex IDs
    
    # Try to map small vertex IDs to component names
    # Strategy: the XXGpvertex lines contain both - check if vertex count matches component count
    # If vertex_ids count ~= node_by_id count, map them by order of appearance
    
    # Build nodes from vertex_ids if we have edges, otherwise from node_by_id
    if edge_set and vertex_ids:
        # We have edges between vertex IDs - use vertex IDs as primary
        # Map vertex_id -> component info by matching counts/order
        sorted_vertices = sorted(vertex_ids, key=lambda x: int(x))
        sorted_comps = sorted(node_by_id.keys(), key=lambda x: int(x))
        
        # Create a vertex_id -> name mapping
        vertex_names = {}
        if len(sorted_vertices) <= len(sorted_comps) * 2:
            # Try to match by position in XXGpvertex lines
            # Each component appears in a XXGpvertex line with its vertex_id
            # For now, assign names sequentially or by proximity
            for i, vid in enumerate(sorted_vertices):
                if i < len(sorted_comps):
                    vertex_names[vid] = node_by_id[sorted_comps[i]]
                else:
                    vertex_names[vid] = {"name": f"Node_{vid}", "type": "TRANSFORM", "display_name": f"Node_{vid}", "comp_type": "Unknown"}
        else:
            for vid in sorted_vertices:
                vertex_names[vid] = {"name": f"Node_{vid}", "type": "TRANSFORM", "display_name": f"Node_{vid}", "comp_type": "Unknown"}
        
        # Build nodes
        seen_names = set()
        for vid in sorted_vertices:
            info = vertex_names[vid]
            name = info["name"]
            if name in seen_names:
                name = f"{name}_{vid}"
            seen_names.add(name)
            nodes.append({
                "id": name,
                "name": info["display_name"],
                "type": info["type"],
                "params": "",
                "subgraph": None,
            })
            # Update vertex_names with final name for edge building
            vertex_names[vid]["final_name"] = name
        
        # Build edges
        for src_vid, dst_vid in edge_set:
            if src_vid in vertex_names and dst_vid in vertex_names:
                edges.append({
                    "from": vertex_names[src_vid].get("final_name", vertex_names[src_vid]["name"]),
                    "to": vertex_names[dst_vid].get("final_name", vertex_names[dst_vid]["name"]),
                })
    else:
        # No edges resolved - just output components as disconnected nodes
        for cid, info in node_by_id.items():
            nodes.append({
                "id": info["name"],
                "name": info["display_name"],
                "type": info["type"],
                "params": "",
                "subgraph": None,
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
        blocking = [e for e in errors if "no parent nod" not in e and "nothing to write" not in e]
        non_blocking = [e for e in errors if "no parent nod" in e or "nothing to write" in e]
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
