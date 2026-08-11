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
    if n.startswith("v") and "_src_" in n:
        return "SOURCE"
    if any(k in n for k in ["write", "output", "sink", "load", "target"]):
        return "SINK"
    if n.startswith("v") and "_tgt_" in n:
        return "SINK"
    if any(k in n for k in ["merge", "join"]):
        return "JOIN"
    if any(k in n for k in ["lookup", "lkp"]):
        return "LOOKUP"
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
    
    # FIRST: Try XXGgraph_vertex_vertex + XXGraph_flow_flow (simpler format like DR_BASIC_COUNT)
    # XXGgraph_vertex_vertex: {2010601001|XXGgraph_vertex_vertex|8|0|16|0|{Filter_by_Expression|}1|9|}
    # Format: {NAME|}VID1|VID2|}  where VID2 is the vertex ID
    
    # Detect subgraph IDs (XXGgraph entities that are NOT the root graph)
    subgraph_ids = set()
    for m in re.finditer(r'XXGgraph\|(\d+)\|', content):
        subgraph_ids.add(m.group(1))
    # Root graph (id=1) is not a subgraph vertex  
    subgraph_ids.discard("1")
    subgraph_ids.discard("0")
    
    # Track which vertices belong to subgraphs (parent is a subgraph, not root graph)
    subgraph_children = set()  # vertex IDs that are inside a subgraph
    
    for m in re.finditer(r'XXGgraph_vertex_vertex\|\d+\|\d+\|\d+\|\d+\|\{([^}]+)\|\}?(\d+)\|(\d+)\|', content):
        name = m.group(1).strip().rstrip('|')
        vid1 = m.group(2)  # parent graph vertex ID
        vid2 = m.group(3)  # this component's vertex ID
        # vid2 is the vertex ID for this component
        # Skip subgraph vertices (they are containers, not actual data components)
        if vid2 in subgraph_ids:
            continue
        # If parent is a subgraph (not root graph "1"), mark as subgraph child
        if vid1 in subgraph_ids:
            subgraph_children.add(vid2)
            continue
        if name and not name.startswith("{"):
            safe_name = re.sub(r'[^\w]', '_', name)
            if vid2 not in node_by_id:
                ntype = _map_component_type(name)
                node_by_id[vid2] = {
                    "name": safe_name,
                    "type": ntype,
                    "display_name": name,
                    "comp_type": name,
                }
    
    # Detect Output_File vs Input_File using mode parameter and port types
    # Output_File has write port (XXGiport with "write") and mode=0x0062
    # Input_File has read port (XXGoport with "read") and mode=0x0001
    # Strategy: find XXGfvertex blocks that contain Output_File.mdc or mode|0x0062
    # and match them to vertex IDs
    
    # Build a map: vertex_id -> has_write_port (iport with 'write' name)
    write_port_vertices = set()
    for m in re.finditer(r'XXGvertex_iport_iport\|\d+\|\d+\|\d+\|\d+\|\{\d+\|write\|\}(\d+)\|(\d+)\|', content):
        write_port_vertices.add(m.group(1))
    # Also simpler format
    for m in re.finditer(r'XXGvertex_iport\|\d+\|\d+\|\d+\|\d+\|\{\d+\|write\|\}(\d+)\|(\d+)\|', content):
        write_port_vertices.add(m.group(1))
    
    # Reclassify: vertices with write ports that are named "Input_File*" or "Output*" → SINK
    for vid in write_port_vertices:
        if vid in node_by_id:
            info = node_by_id[vid]
            if info["type"] == "SOURCE":
                info["type"] = "SINK"
                print(f"  [dbg] Reclassified {info['display_name']} (vertex {vid}) as SINK (has write port)")
    
    # Also detect from XXGfvertex blocks with Output_File.mdc prototype
    for m in re.finditer(r'XXGfvertex\|(\d+)\|.*?Output_File\.mdc', content):
        # The XXGfvertex ID is followed by XXGgraph_vertex_vertex mapping it
        pass
    
    # Extract Layout paths (source/sink file paths) from XXGfvertex components
    # Pattern: Layout|/path/to/file| inside XXGfvertex blocks
    # Match Layout paths to vertex IDs via eme_dataset_mapping paths
    layout_paths = {}
    for m in re.finditer(r'XXGfvertex\|(\d+)\|.*?(?:Layout\|([^|]+)\|)', content):
        fvertex_id = m.group(1)
        path = m.group(2).strip()
        if path and path.startswith("/"):
            layout_paths[fvertex_id] = path
    
    # Also extract paths from eme_dataset_mapping (more reliable for actual data paths)
    # Strategy: find all XXGfvertex positions, then for each one, find the Layout|/path| 
    # that appears between it and the next XXGfvertex (or end of content)
    fvertex_positions = [(m.start(), m.group(1)) for m in re.finditer(r'XXGfvertex\|(\d+)\|', content)]
    for i, (pos, fvid) in enumerate(fvertex_positions):
        # Determine end boundary (next XXGfvertex or end)
        end_pos = fvertex_positions[i + 1][0] if i + 1 < len(fvertex_positions) else len(content)
        block = content[pos:end_pos]
        # Look for Layout|/path| in this block
        lm = re.search(r'Layout\|(/[^|]+)\|', block)
        if lm:
            layout_paths[fvid] = lm.group(1).strip()
        # Also check eme_dataset_mapping interp
        em = re.search(r'dataset_path\s+_interp_\("(/[^"]+)"', block)
        if em and fvid not in layout_paths:
            layout_paths[fvid] = em.group(1).strip()
    
    if layout_paths:
        print(f"  [dbg] Layout paths: {layout_paths}")
    
    # Detect XXGtvertex (Input_Table / Output_Table) — database connections
    db_sources = {}
    tvertex_positions = [(m.start(), m.group(1)) for m in re.finditer(r'XXGtvertex\|(\d+)\|', content)]
    for i, (pos, tvid) in enumerate(tvertex_positions):
        end_pos = tvertex_positions[i + 1][0] if i + 1 < len(tvertex_positions) else len(content)
        block = content[pos:end_pos]
        # Extract DB info
        dbms_m = re.search(r'dbms\|(\w+)\|', block)
        table_spec_m = re.search(r'table_spec\|([^|]+)\|', block)
        config_m = re.search(r'config_file\|([^|]+)\|', block)
        if dbms_m:
            db_info = {"dbms": dbms_m.group(1)}
            if table_spec_m:
                db_info["query"] = table_spec_m.group(1).strip()
            if config_m:
                db_info["config_file"] = config_m.group(1).strip()
            db_sources[tvid] = db_info
    
    if db_sources:
        print(f"  [dbg] DB sources: {list(db_sources.keys())} ({list(db_sources.values())[0].get('dbms', '?')})")
    
    # Assign paths and DB info to nodes
    for vid, info in node_by_id.items():
        if vid in layout_paths:
            info["data_path"] = layout_paths[vid]
        if vid in db_sources:
            info["db_source"] = db_sources[vid]
    
    # XXGraph_flow_flow: {2010604001|XXGraph_flow_flow|4|0|8|0|{Flow_1|}3|5|}
    # Format: {FLOW_NAME|}FROM_VERTEX|TO_VERTEX|}
    flow_edges_direct = []
    for m in re.finditer(r'XXGraph_flow_flow\|\d+\|\d+\|\d+\|\d+\|\{([^}]+)\|\}?(\d+)\|(\d+)\|', content):
        fname = m.group(1).strip()
        from_v = m.group(2)
        to_v = m.group(3)
        flow_edges_direct.append((from_v, to_v))
    
    if flow_edges_direct and node_by_id:
        print(f"  [dbg] Direct flow edges found: {len(flow_edges_direct)}")
        # We have both vertex names and direct edges - build the graph
        for src, dst in flow_edges_direct:
            if src in node_by_id and dst in node_by_id:
                edge_set.add((src, dst))
    
    # Output ports: {2010212001|XXGvertex_oport_oport|9|0|18|0|{0|out|}9|10|}
    # Generic: accept any port name between pipes
    for m in re.finditer(r'XXGvertex_oport_oport\|\d+\|\d+\|\d+\|\d+\|\{\d+\|[^|]+\|\}(\d+)\|(\d+)\|', content):
        vertex_id = m.group(1)
        port_id = m.group(2)
        oport_to_vertex[port_id] = vertex_id
        vertex_ids.add(vertex_id)
    
    # Also try simple _oport format: {2010212001|XXGvertex_oport|10|0|18|0|{0|out|}9|10|}
    for m in re.finditer(r'XXGvertex_oport\|\d+\|\d+\|\d+\|\d+\|\{\d+\|[^|]+\|\}(\d+)\|(\d+)\|', content):
        vertex_id = m.group(1)
        port_id = m.group(2)
        if port_id not in oport_to_vertex:
            oport_to_vertex[port_id] = vertex_id
            vertex_ids.add(vertex_id)
    
    # Input ports: {2010211001|XXGvertex_iport_iport|2838|0|4563|0|{0|in|}1721|1726|}
    for m in re.finditer(r'XXGvertex_iport_iport\|\d+\|\d+\|\d+\|\d+\|\{\d+\|[^|]+\|\}(\d+)\|(\d+)\|', content):
        vertex_id = m.group(1)
        port_id = m.group(2)
        iport_to_vertex[port_id] = vertex_id
        vertex_ids.add(vertex_id)
    
    # Simple _iport format: {2010211001|XXGvertex_iport|15|0|29|0|{0|in|}9|15|}
    for m in re.finditer(r'XXGvertex_iport\|\d+\|\d+\|\d+\|\d+\|\{\d+\|[^|]+\|\}(\d+)\|(\d+)\|', content):
        vertex_id = m.group(1)
        port_id = m.group(2)
        if port_id not in iport_to_vertex:
            iport_to_vertex[port_id] = vertex_id
            vertex_ids.add(vertex_id)
    
    # Oport to flow: {2010213001|XXGoport_dst_flow|2834|0|4556|0|{0|}1722|1720|}
    # NOTE: A single oport can send to MULTIPLE flows (fan-out, e.g. Replicate)
    for m in re.finditer(r'XXGoport_dst_flow\|\d+\|\d+\|\d+\|\d+\|\{\d+\|\}(\d+)\|(\d+)\|', content):
        port_id = m.group(1)
        flow_id = m.group(2)
        if port_id not in oport_to_flow:
            oport_to_flow[port_id] = []
        oport_to_flow[port_id].append(flow_id)
    
    # Iport from flow: {2010214001|XXGiport_src_flow|2824|0|4541|0|{0|}1717|1692|}
    # NOTE: A single iport can receive from MULTIPLE flows (fan-in, e.g. Concatenate)
    for m in re.finditer(r'XXGiport_src_flow\|\d+\|\d+\|\d+\|\d+\|\{\d+\|\}(\d+)\|(\d+)\|', content):
        port_id = m.group(1)
        flow_id = m.group(2)
        if port_id not in iport_from_flow:
            iport_from_flow[port_id] = []
        iport_from_flow[port_id].append(flow_id)
    
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
                # Skip: numeric IDs, internal params, structural refs, template params
                if (param_name and not param_name.isdigit() 
                    and not param_name.startswith("_") 
                    and not param_name.startswith("!")
                    and "XXG" not in param_name
                    and not any(x in param_name for x in [
                        "interface", "condition", "display_name", "keyword", 
                        "metadata", "mpcmodtime", "operation", "num_", "type",
                        "mpname", "image__", "port_analysis", "continuous",
                        "filter_aggregate", "propagat", "doc_", "callback",
                        "threshold", "limit_keyword", "ramp_keyword",
                    ])):
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
                if port_id not in oport_to_flow:
                    oport_to_flow[port_id] = []
                if flow_id not in oport_to_flow[port_id]:
                    oport_to_flow[port_id].append(flow_id)
            continue
        
        # Input port from flow: {2010214001|XXGiport_src_flow|18|0|36|0|{0|}18|5|}
        if "|XXGiport_src_flow|" in line:
            m = re.search(r'\{0\|\}?(\d+)\|(\d+)\|', line)
            if m:
                port_id = m.group(1)
                flow_id = m.group(2)
                if port_id not in iport_from_flow:
                    iport_from_flow[port_id] = []
                if flow_id not in iport_from_flow[port_id]:
                    iport_from_flow[port_id].append(flow_id)
            continue
    
    # Build edges: oport → flow → iport
    # For each flow_id, find which output port sends to it and which input port receives from it
    # oport_to_flow: port_id -> flow_id (output port sends to this flow)
    # iport_from_flow: port_id -> flow_id (input port receives from this flow)
    
    # Invert: flow_id -> source_vertex (via oport)
    # oport_to_flow values are now LISTS (fan-out support: one port → multiple flows)
    flow_to_src_vertex = {}
    for port_id, flow_ids in oport_to_flow.items():
        if port_id in oport_to_vertex:
            for flow_id in flow_ids:
                flow_to_src_vertex[flow_id] = oport_to_vertex[port_id]
    
    # For each iport that receives from a flow, find the source vertex
    # iport_from_flow values are now LISTS (fan-in support)
    edge_set = set()
    for port_id, flow_ids in iport_from_flow.items():
        if port_id in iport_to_vertex:
            dst_vertex = iport_to_vertex[port_id]
            # Skip edges involving subgraph children
            if dst_vertex in subgraph_children:
                continue
            for flow_id in flow_ids:
                if flow_id in flow_to_src_vertex:
                    src_vertex = flow_to_src_vertex[flow_id]
                    # Skip edges involving subgraph children
                    if src_vertex in subgraph_children:
                        continue
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
    # - node_by_id: vertex_id -> {name, type} from XXGgraph_vertex_vertex
    # - vertex_ids: all vertex IDs seen in port definitions
    # - edge_set: edges between vertex IDs
    
    # node_by_id already maps vertex_id -> component name (from XXGgraph_vertex_vertex)
    # vertex_ids from ports should overlap with node_by_id keys
    
    # Build nodes: use node_by_id for named nodes, create Node_X for unnamed ones
    if edge_set and vertex_ids:
        all_vertex_ids = vertex_ids.copy()
        # Also add vertex_ids from edge_set that might not be in vertex_ids
        for src, dst in edge_set:
            all_vertex_ids.add(src)
            all_vertex_ids.add(dst)
        
        # Build vertex_names using node_by_id (direct mapping from XXGgraph_vertex_vertex)
        vertex_names = {}
        for vid in sorted(all_vertex_ids, key=lambda x: int(x)):
            if vid in node_by_id:
                vertex_names[vid] = node_by_id[vid]
            else:
                # Unknown vertex - might be a port-only node (reject, error, log output)
                vertex_names[vid] = {"name": f"Node_{vid}", "type": "TRANSFORM", "display_name": f"Node_{vid}", "comp_type": "Unknown"}
        
        # Build nodes (only include vertices that participate in edges or are named components)
        seen_names = set()
        included_vids = set()
        
        # First include all vertices in edges
        for src, dst in edge_set:
            included_vids.add(src)
            included_vids.add(dst)
        # Also include all named components
        for vid in node_by_id:
            included_vids.add(vid)
        
        for vid in sorted(included_vids, key=lambda x: int(x)):
            if vid not in vertex_names:
                continue
            info = vertex_names[vid]
            name = info["name"]
            if name in seen_names:
                name = f"{name}_{vid}"
            seen_names.add(name)
            node_data = {
                "id": name,
                "name": info["display_name"],
                "type": info["type"],
                "params": "",
                "subgraph": None,
                "vertex_id": vid,
            }
            # Include data_path if available (for SOURCE/SINK)
            if "data_path" in info:
                node_data["data_path"] = info["data_path"]
            # Include db_source if available (for Input_Table/Output_Table)
            if "db_source" in info:
                node_data["db_source"] = info["db_source"]
            nodes.append(node_data)
            vertex_names[vid]["final_name"] = name
        
        # Build edges
        for src_vid, dst_vid in edge_set:
            if src_vid in vertex_names and dst_vid in vertex_names:
                src_name = vertex_names[src_vid].get("final_name", vertex_names[src_vid]["name"])
                dst_name = vertex_names[dst_vid].get("final_name", vertex_names[dst_vid]["name"])
                edges.append({
                    "from": src_name,
                    "to": dst_name,
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


def parse_ksh(ksh_path):
    """Parse Ab Initio .ksh deployment script to extract metadata."""
    metadata = {
        "graph_name": "",
        "mp_path": "",
        "ab_home": "",
        "ab_version": "",
        "project_dir": "",
        "components_path": "",
        "variables": {},
    }
    
    with open(ksh_path, "r", errors="replace") as f:
        content = f.read()
    
    # AB_GRAPH_NAME
    m = re.search(r'AB_GRAPH_NAME[=;]([^\s;\n]+)', content)
    if m:
        val = m.group(1).strip().replace("AB_GRAPH_NAME=", "")
        metadata["graph_name"] = val
    
    # AB_HOME
    m = re.search(r'AB_HOME[=;]AB_HOME[=;]?([^\s;\n}]+)', content)
    if not m:
        m = re.search(r'AB_HOME[=;]([^\s;\n}]+)', content)
    if m:
        metadata["ab_home"] = m.group(1).replace("${AB_HOME:-", "").rstrip("}")
    
    # AB_COMPATIBILITY (version)
    m = re.search(r'AB_COMPATIBILITY[=;](\S+)', content)
    if m:
        metadata["ab_version"] = m.group(1)
    
    # air sandbox run ... .mp
    m = re.search(r'air\s+sandbox\s+run\s+"?([^"\s]+\.mp)"?', content)
    if m:
        metadata["mp_path"] = m.group(1)
    
    # PROJECT_DIR
    m = re.search(r'PROJECT_DIR[=;]PROJECT_DIR[=;]?([^\s;\n}]+)', content)
    if not m:
        m = re.search(r'PROJECT_DIR[=;]([^\s;\n}]+)', content)
    if m:
        metadata["project_dir"] = m.group(1).replace("${PROJECT_DIR:-", "").rstrip("}")
    
    # AB_COMPONENTS
    m = re.search(r'AB_COMPONENTS[=;]AB_COMPONENTS[=;]?([^\s;\n}]+)', content)
    if m:
        metadata["components_path"] = m.group(1).replace('"', '').replace("'", "")
    
    # Extract all export variables
    for m in re.finditer(r'export\s+(\w+)[;=](\w+)=([^\s;\n]+)', content):
        metadata["variables"][m.group(1)] = m.group(3)
    
    return metadata


def _generate_pandas(dag, output_path, xfr_rules=None):
    """Generate pure Python code using pandas (no Spark/Glue dependencies)."""
    import os
    xfr_rules = xfr_rules or {}
    from datetime import datetime
    
    with open(output_path, "w") as f:
        f.write(f'"""\nBNX V54 - Python Puro (pandas)\nGenerated at: {datetime.now()}\nNo requiere Spark, Glue ni Flink. Solo: pip install pandas\n"""\n\n')
        f.write("import pandas as pd\nimport os\n\n")
        f.write('print("[*] BNX Python Job Started")\n\n')
        
        for node in dag.execution_order:
            var_id = node.id
            name = node.name
            ntype = node.type.upper()
            parents = node.parents
            rule = xfr_rules.get(var_id.lower()) or xfr_rules.get(name.lower()) or {}
            
            if ntype == "SOURCE":
                path = rule.get("path", f"data/{var_id.lower()}.csv") if rule else f"data/{var_id.lower()}.csv"
                f.write(f'# [+] SOURCE: {name}\n')
                f.write(f'{var_id}_df = pd.read_csv("{path}")\n')
                f.write(f'print(f"[>] SOURCE {name}: {{len({var_id}_df)}} rows")\n\n')
            
            elif ntype == "FILTER":
                f.write(f'# [-] FILTER: {name}\n')
                if parents:
                    where = rule.get("where", "") if rule else ""
                    if where:
                        # Translate Ab Initio built-in functions to pandas equivalents
                        if "next_in_sequence()" in where:
                            # next_in_sequence() > 1 skips header rows in raw/fixed-width files.
                            # No-op for structured formats (CSV with header already parsed).
                            f.write(f'# next_in_sequence() filter: no-op for CSV/parquet (header handled by reader)\n')
                            f.write(f'{var_id}_df = {parents[0]}_df.copy()\n')
                        elif re.search(r'\b(string_|decimal_|integer_|date_|is_blank|is_defined)', where):
                            # Other Ab Initio functions that can't go in .query() - use .copy() as fallback
                            f.write(f'# TODO: Ab Initio expression not directly translatable: {where}\n')
                            f.write(f'{var_id}_df = {parents[0]}_df.copy()\n')
                        else:
                            # Standard expression compatible with pandas query
                            f.write(f'{var_id}_df = {parents[0]}_df.query("{where}")\n')
                    else:
                        f.write(f'{var_id}_df = {parents[0]}_df.copy()\n')
                else:
                    f.write(f'{var_id}_df = pd.DataFrame()\n')
                f.write(f'print(f"[~] FILTER {name}: {{len({var_id}_df)}} rows")\n\n')
            
            elif ntype == "JOIN":
                f.write(f'# [~] JOIN: {name}\n')
                if len(parents) >= 2:
                    jk = rule.get("join_key", "id") if rule else "id"
                    jt = rule.get("join_type", "inner") if rule else "inner"
                    f.write(f'{var_id}_df = {parents[0]}_df.merge({parents[1]}_df, on="{jk}", how="{jt}")\n')
                elif parents:
                    f.write(f'{var_id}_df = {parents[0]}_df.copy()\n')
                else:
                    f.write(f'{var_id}_df = pd.DataFrame()\n')
                f.write(f'print(f"[~] JOIN {name}: {{len({var_id}_df)}} rows")\n\n')
            
            elif ntype == "SINK":
                f.write(f'# [*] SINK: {name}\n')
                if parents:
                    path = rule.get("path", f"output/{var_id.lower()}.csv") if rule else f"output/{var_id.lower()}.csv"
                    dir_part = os.path.dirname(path)
                    if dir_part:
                        f.write(f'os.makedirs("{dir_part}", exist_ok=True)\n')
                    f.write(f'{parents[0]}_df.to_csv("{path}", index=False)\n')
                    f.write(f'print(f"[>] SINK {name}: {{len({parents[0]}_df)}} rows -> {path}")\n\n')
                else:
                    f.write(f'# SINK {name} has no parent\n')
                    f.write(f'print("[!] SINK {name}: no data")\n\n')
            
            else:  # TRANSFORM, PARTITION, CONCATENATE, etc.
                f.write(f'# [.] {ntype}: {name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    select = rule.get("select", "") if rule else ""
                    where = rule.get("where", "") if rule else ""
                    group_by = rule.get("group_by", []) if rule else []
                    
                    # Map Ab Initio string functions to pandas expressions
                    # string_upcase(in.field) -> df["field"].str.upper()
                    string_transforms = []
                    if select:
                        for part in select.split(","):
                            part = part.strip()
                            # Match: string_upcase(in.field) as alias OR string_upcase(field) as alias
                            m_str = re.match(r'(string_\w+)\((?:in\.)?(\w+)\)\s+as\s+(\w+)', part, re.I)
                            if m_str:
                                fn, field, alias = m_str.group(1).lower(), m_str.group(2), m_str.group(3)
                                pandas_fn = {
                                    'string_upcase': '.str.upper()',
                                    'string_downcase': '.str.lower()',
                                    'string_lrtrim': '.str.strip()',
                                    'string_ltrim': '.str.lstrip()',
                                    'string_rtrim': '.str.rstrip()',
                                    'string_length': '.str.len()',
                                    'string_reverse': '.str[::-1]',
                                }.get(fn, '')
                                if pandas_fn:
                                    string_transforms.append((field, alias, pandas_fn))
                    
                    # Deduplicate group_by keys preserving order
                    if group_by:
                        group_by = list(dict.fromkeys(group_by))
                    
                    if string_transforms and not group_by:
                        # Generate pandas string operations
                        f.write(f'{var_id}_df = {src}.copy()\n')
                        for field, alias, pandas_fn in string_transforms:
                            f.write(f'{var_id}_df["{alias}"] = {var_id}_df["{field}"]{pandas_fn}\n')
                    elif group_by and select:
                        # Aggregation
                        keys_str = "[" + ", ".join(f"'{k}'" for k in group_by) + "]"
                        # Parse select for agg functions
                        agg_parts = []
                        for part in select.split(","):
                            part = part.strip()
                            m = re.match(r'(\w+)\((\w+)\)\s+as\s+(\w+)', part, re.I)
                            if m:
                                fn, field, alias = m.group(1).lower(), m.group(2), m.group(3)
                                agg_parts.append(f"{alias}=('{field}', '{fn}')")
                        if agg_parts:
                            agg_str = ", ".join(agg_parts)
                            f.write(f"{var_id}_df = {src}.groupby({keys_str}).agg({agg_str}).reset_index()\n")
                        else:
                            f.write(f"{var_id}_df = {src}.groupby({keys_str}).first().reset_index()\n")
                    elif where:
                        f.write(f'{var_id}_df = {src}.query("{where}")\n')
                    elif select and select != "*":
                        cols = [c.strip() for c in select.split(",")]
                        f.write(f'{var_id}_df = {src}[{cols}]\n')
                    else:
                        f.write(f'{var_id}_df = {src}.copy()\n')
                else:
                    f.write(f'{var_id}_df = pd.DataFrame()\n')
                f.write(f'print(f"[~] {ntype} {name}: {{len({var_id}_df)}} rows")\n\n')
        
        f.write('print("[ok] BNX Python Job Finished")\n')


def _extract_embedded_transforms(content):
    """Extract transform rules and keys from embedded DML in GDE .mp files.
    
    Parses patterns like:
    {30001002|XXparameter|transform|out :: rollup(in) =
    begin
        out.id :: in.id;
        out.nombre :: in.nombre;
        out.monto :: sum(in.monto);
    end;|3|1|1|@{0|}}
    
    {30001002|XXparameter|key|\\{nombre\\}|3|2|$|@{0|}}
    
    Returns dict of xfr_rules keyed by component name.
    """
    xfr_rules = {}
    
    # Extract all transform blocks
    # They appear as XXparameter|transform|BODY or XXparameter|transform0|BODY etc.
    # The body can contain pipes (|) inside GDE format, escaped braces (\{ \}), and multiline content
    # Strategy: find "transform0|" then capture until we hit the pattern for next parameter field "|N|N|"
    raw_transforms = re.findall(
        r'XXparameter\|transform\d*\|(.*?)(?:\|\d+\|\d+\|)',
        content, re.DOTALL
    )
    # Filter: only keep transforms that have actual DML content (:: or begin/end)
    transforms = [t.strip() for t in raw_transforms if '::' in t or 'begin' in t.lower()]
    
    # Extract keys (group by fields)
    # Key format: key|\{field1; field2\}| or key|\{\}| (empty = all fields)
    # Strategy: extract keys with their position context to map to components
    keys_raw = re.findall(r'XXparameter\|key\|([^|]*)\|', content)
    keys = []
    for k in keys_raw:
        # Remove escaped braces and clean
        cleaned = k.replace('\\{', '').replace('\\}', '').replace('{', '').replace('}', '').strip()
        if cleaned:
            keys.append(cleaned)
    
    # Better: extract keys per component using XXGpvertex/XXGfvertex position mapping
    # Find which vertex each key belongs to by position in content
    vertex_positions = [(m.start(), m.group(1)) for m in re.finditer(r'XXG[pft]vertex\|(\d+)\|', content)]
    key_positions = [(m.start(), m.group(1)) for m in re.finditer(r'XXparameter\|key\|([^|]*)\|', content)]
    
    # Map each key to its containing vertex
    keys_by_vertex = {}
    for key_pos, key_val in key_positions:
        # Find the vertex that contains this key (last vertex before this position)
        owning_vertex = None
        for vpos, vid in vertex_positions:
            if vpos < key_pos:
                owning_vertex = vid
            else:
                break
        if owning_vertex:
            cleaned = key_val.replace('\\{', '').replace('\\}', '').replace('{', '').replace('}', '').strip()
            if cleaned:
                if owning_vertex not in keys_by_vertex:
                    keys_by_vertex[owning_vertex] = []
                keys_by_vertex[owning_vertex].append(cleaned)
    
    if keys_by_vertex:
        print(f"  [dbg] Keys by vertex: {keys_by_vertex}")
    
    # Extract dedup 'keep' settings (first, last, unique-only)
    keeps = re.findall(r'XXparameter\|keep\|(\w+)\|', content)
    try:
        print(f"  [dbg] Extracted keys: {keys}")
    except (UnicodeEncodeError, OSError):
        print(f"  [dbg] Extracted keys: {len(keys)} keys found")
    
    # Extract filter expressions (for Filter_by_Expression components)
    filters = re.findall(r'XXparameter\|select_expr\|([^|]+)\|', content)
    # Also extract 'select' parameters that contain filter expressions (Reformat with pre-filter)
    select_filters = re.findall(r'XXparameter\|select\|([^|]+)\|', content)
    for sf in select_filters:
        sf = sf.strip()
        if sf and ('==' in sf or '!=' in sf or '>' in sf or '<' in sf or 'in(' in sf.lower()):
            filters.append(sf)
    if filters:
        print(f"  [dbg] Extracted filters: {filters}")
    
    # Map filters (select_expr) to their containing vertex
    filters_by_vertex = {}
    filter_positions = [(m.start(), m.group(1)) for m in re.finditer(r'XXparameter\|select_expr\|([^|]+)\|', content, re.DOTALL)]
    for fpos, fval in filter_positions:
        owning_vertex = None
        for vpos, vid in vertex_positions:
            if vpos < fpos:
                owning_vertex = vid
            else:
                break
        if owning_vertex and fval.strip():
            # Clean up newlines in filter expression
            filters_by_vertex[owning_vertex] = fval.strip().replace('\n', ' ')
    
    # Also map 'select' filters (from Reformat components) by vertex
    select_filter_positions = [(m.start(), m.group(1)) for m in re.finditer(r'XXparameter\|select\|([^|]+)\|', content)]
    for sfpos, sfval in select_filter_positions:
        sfval = sfval.strip()
        if sfval and ('==' in sfval or '!=' in sfval or '>' in sfval or '<' in sfval):
            owning_vertex = None
            for vpos, vid in vertex_positions:
                if vpos < sfpos:
                    owning_vertex = vid
                else:
                    break
            if owning_vertex:
                filters_by_vertex[owning_vertex] = sfval
    
    if filters_by_vertex:
        print(f"  [dbg] Filters by vertex: {filters_by_vertex}")
    
    # Extract record schemas (out_metadata)
    schemas = re.findall(r'XXparameter\|out_metadata\|record\s*(.*?)(?:end;|\|)', content, re.DOTALL)
    
    # Parse transform bodies into field mappings
    # Each component gets its own set of rules
    # We track transforms by their position/context
    component_transforms = {}
    current_component_idx = 0
    
    for transform in transforms:
        rules = {"fields": [], "aggregations": [], "type": "passthrough", "raw_body": transform}
        
        # Parse "out :: rollup(in) = begin ... end;"
        if "rollup" in transform.lower():
            rules["type"] = "rollup"
        elif "reformat" in transform.lower() or "::" in transform:
            rules["type"] = "reformat"
        
        # Extract field assignments: out.field :: expression;
        field_matches = re.findall(r'out\.(\w+)\s*::\s*(.+?);', transform)
        for field_name, expression in field_matches:
            expr = expression.strip()
            # Skip newline/record terminator fields
            if field_name == "newline" or field_name == "*" or field_name == "V_FILLER":
                continue
            # Skip passthrough (out.* :: in.*)
            if expr == "in.*" or expr == "in." + field_name:
                continue
            # Detect aggregation functions
            agg_match = re.match(r'(sum|count|min|max|avg|first|last)\((?:in\.)?(\w+)\)', expr)
            if agg_match:
                rules["aggregations"].append({
                    "field": field_name,
                    "function": agg_match.group(1),
                    "source_field": agg_match.group(2),
                })
            elif expr.startswith("in."):
                rules["fields"].append({
                    "field": field_name,
                    "source": expr.replace("in.", ""),
                })
            elif re.match(r"^'[^']*'$", expr) or re.match(r'^"[^"]*"$', expr):
                # String literal
                rules["fields"].append({
                    "field": field_name,
                    "literal": expr.strip("'\""),
                    "literal_type": "string",
                })
            elif re.match(r'^-?\d+(\.\d+)?$', expr):
                # Numeric literal
                rules["fields"].append({
                    "field": field_name,
                    "literal": expr,
                    "literal_type": "number",
                })
            else:
                rules["fields"].append({
                    "field": field_name,
                    "expression": expr,
                })
        
        component_transforms[current_component_idx] = rules
        print(f"  [dbg] Transform #{current_component_idx}: type={rules['type']}, fields={len(rules['fields'])}, aggs={len(rules['aggregations'])}")
        current_component_idx += 1
    
    # Build xfr_rules dict
    # We'll match these to components by order later
    # For now, store with index keys
    result = {
        "transforms": component_transforms,
        "keys": keys,
        "keys_by_vertex": keys_by_vertex,
        "filters": filters,
        "filters_by_vertex": filters_by_vertex,
        "keeps": keeps,
    }
    
    return result


def _apply_embedded_transforms(node_by_id, embedded, xfr_rules):
    """Apply extracted embedded transforms to the xfr_rules dict.
    
    Maps transforms to components by type:
    - Sort components get sort_by rules
    - Rollup components get rollup transforms + keys
    - Filter components get filter expressions
    - Reformat components get field mappings or raw transform
    - Lookup (Output File with mode lookup) gets lookup_key
    """
    import re as _re
    keys = embedded.get("keys", [])
    keys_by_vertex = embedded.get("keys_by_vertex", {})
    filters = embedded.get("filters", [])
    filters_by_vertex = embedded.get("filters_by_vertex", {})
    transforms = embedded.get("transforms", {})
    keeps = embedded.get("keeps", [])
    
    # Track which keys have been used
    key_idx = 0
    filter_idx = 0
    keep_idx = 0
    
    # Build reverse map: node_id (from node_map) -> vertex_id
    # node_map keys are node IDs (names), we need to find vertex IDs
    # The caller passes node_map built from ast nodes, but we need vertex IDs
    # for keys_by_vertex lookup. We'll try matching by iterating.
    
    for vid, info in sorted(node_by_id.items(), key=lambda x: str(x[0])):
        comp_name = info["name"]
        comp_type = info["comp_type"].lower()
        name_lower = comp_name.lower()
        
        # Get keys specific to this vertex (from position-based extraction)
        vertex_keys = keys_by_vertex.get(vid, [])
        
        # --- DEDUP --- (must be checked BEFORE sort, since "dedup_sorted" contains "sort")
        if "dedup" in comp_type or "dedup" in comp_name.lower():
            # Skip if already defined by external .xfr (has dedup_keys with actual values)
            if name_lower in xfr_rules and xfr_rules[name_lower].get("dedup_keys"):
                keep_idx += 1 if keeps else 0
                continue
            rule = {}
            if vertex_keys:
                # Use vertex-specific keys
                dedup_fields = []
                for k in vertex_keys:
                    dedup_fields.extend([f.strip() for f in k.replace(';', ',').split(',') if f.strip()])
                rule["dedup_keys"] = dedup_fields
            elif keys and key_idx < len(keys):
                key_str = keys[key_idx]
                dedup_fields = [f.strip().rstrip('}').lstrip('{') for f in key_str.replace(';', ',').split(',') if f.strip()]
                rule["dedup_keys"] = dedup_fields
                key_idx += 1
            else:
                rule["dedup_keys"] = []
            # Apply keep setting
            if keeps and keep_idx < len(keeps):
                keep_val = keeps[keep_idx]
                if keep_val == "last":
                    rule["keep"] = "last"
                keep_idx += 1
            xfr_rules[name_lower] = rule
        
        # --- SORT ---
        elif "sort" in comp_type and "sort" in comp_name.lower():
            # Skip if .xfr already has a real sort_by rule
            if name_lower in xfr_rules and xfr_rules[name_lower].get("sort_by"):
                continue
            if vertex_keys:
                sort_fields = []
                for k in vertex_keys:
                    sort_fields.extend([f.strip() for f in k.replace(';', ',').split(',') if f.strip()])
                if sort_fields:
                    xfr_rules[name_lower] = {"sort_by": sort_fields}
            elif keys and key_idx < len(keys):
                key_str = keys[key_idx]
                sort_fields = [f.strip().rstrip('}').lstrip('{') for f in key_str.replace(';', ',').split(',') if f.strip()]
                if sort_fields:
                    xfr_rules[name_lower] = {"sort_by": sort_fields}
                key_idx += 1
        
        # --- LOOKUP (Output File with mode=lookup and key) ---
        elif ("output" in comp_type or "file" in comp_type) and "lkp" in comp_name.lower():
            # This is a lookup file — mark it with lookup_key
            if keys and key_idx < len(keys):
                key_str = keys[key_idx]
                lookup_keys = [f.strip().rstrip('}').lstrip('{') for f in key_str.replace(';', ',').split(',') if f.strip()]
                xfr_rules[name_lower] = {
                    "lookup_key": lookup_keys[0] if lookup_keys else "",
                    "source_type": "lookup",
                }
                key_idx += 1
        
        # --- ROLLUP ---
        elif "rollup" in comp_type:
            for tidx, trules in list(transforms.items()):
                if trules["type"] == "rollup":
                    rule = {}
                    if keys and key_idx < len(keys):
                        key_str = keys[key_idx]
                        rule["group_by"] = [f.strip().rstrip('}').lstrip('{') for f in key_str.replace(';', ',').split(',') if f.strip()]
                        key_idx += 1
                    if trules["aggregations"]:
                        rule["select"] = ", ".join(
                            f'{a["function"]}({a["source_field"]}) as {a["field"]}' 
                            for a in trules["aggregations"]
                        )
                    xfr_rules[name_lower] = rule
                    del transforms[tidx]
                    break
        
        # --- FILTER ---
        elif "filter" in comp_type:
            # Use vertex-specific filter if available
            vertex_filter = filters_by_vertex.get(vid)
            if vertex_filter:
                xfr_rules[name_lower] = {"where": vertex_filter}
            elif filters and filter_idx < len(filters):
                xfr_rules[name_lower] = {"where": filters[filter_idx]}
                filter_idx += 1
        
        # --- REFORMAT ---
        elif "reformat" in comp_type:
            # Skip if .xfr already defines real rules for this component
            existing = xfr_rules.get(name_lower, {})
            has_real_xfr = (existing.get("select", "*") != "*" or 
                           existing.get("where") or 
                           existing.get("transform") or
                           existing.get("raw_transform") or
                           existing.get("literals"))
            if has_real_xfr:
                continue
            for tidx, trules in list(transforms.items()):
                if trules["type"] in ("reformat", "passthrough"):
                    # Check if transform has lookup_count/lookup_next (complex lookup pattern)
                    raw_body = trules.get("raw_body", "")
                    if "lookup_count" in raw_body or "lookup_next" in raw_body:
                        # Complex lookup join — generate a comment with the original logic
                        # and a simplified version using broadcast join
                        lookup_name = ""
                        import re as _re
                        lkp_match = _re.search(r'lookup_count\("([^"]+)"', raw_body)
                        if lkp_match:
                            lookup_name = lkp_match.group(1).replace("-", "_").lower()
                        
                        # Extract output fields from out.field :: expressions
                        out_fields = _re.findall(r'out\.(\w+)\s*::', raw_body)
                        
                        xfr_rules[name_lower] = {
                            "transform": "lookup_join",
                            "lookup_name": lookup_name,
                            "raw_transform": raw_body[:500],
                            "output_fields": out_fields,
                        }
                        del transforms[tidx]
                        break
                    
                    # Regular reformat with field mappings
                    fields = trules.get("fields", [])
                    if fields:
                        select_parts = []
                        literal_parts = []
                        for f in fields:
                            if "literal" in f:
                                # Literal assignment: withColumn("field", lit(value))
                                literal_parts.append(f)
                            elif "expression" in f:
                                select_parts.append(f'{f["expression"]} as {f["field"]}')
                            elif "source" in f:
                                if f["source"] == f["field"]:
                                    select_parts.append(f["field"])
                                else:
                                    select_parts.append(f'{f["source"]} as {f["field"]}')
                        
                        rule = {}
                        if select_parts:
                            rule["select"] = ", ".join(select_parts)
                        if literal_parts:
                            rule["literals"] = literal_parts
                        # Apply select filter if available for this Reformat
                        if filters and filter_idx < len(filters):
                            rule["where"] = filters[filter_idx]
                            filter_idx += 1
                        if rule:
                            xfr_rules[name_lower] = rule
                    elif "out.*" in raw_body and "::" in raw_body:
                        # Simple passthrough with maybe one extra field
                        extra_fields = _re.findall(r'out\.(\w+)\s*::\s*(.+?);', raw_body)
                        transforms_list = []
                        for field, expr in extra_fields:
                            if field != "*" and "in." not in expr.replace("in.*", ""):
                                transforms_list.append(f"{expr.strip()} as {field}")
                        if transforms_list:
                            xfr_rules[name_lower] = {"transform_exprs": transforms_list}
                    else:
                        # No fields extracted but we have a filter for this reformat
                        if filters and filter_idx < len(filters):
                            xfr_rules[name_lower] = {"where": filters[filter_idx]}
                            filter_idx += 1
                    
                    del transforms[tidx]
                    break


def parse_project(file_path):
    """Smart parser: detects format and parses accordingly."""
    with open(file_path, "r", errors="replace") as f:
        content = f.read()
    
    # Clean null bytes and other binary artifacts
    content = content.replace('\x00', '').replace('\x01', '').replace('\x02', '')
    
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

    # Parse KSH metadata if provided via --ksh
    ksh_metadata = {}

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
    # Handle raw DML transforms from .xfr
    if "_multi_xfr" in xfr_rules:
        # Multiple .xfr files — assign each to a TRANSFORM node in order
        multi = xfr_rules.pop("_multi_xfr")
        transform_nodes = [n for n in ast.get("nodes", []) if n["type"].upper() == "TRANSFORM"]
        for i, xfr_data in enumerate(multi):
            if i < len(transform_nodes):
                nid = transform_nodes[i]["id"].lower()
                xfr_rules[nid] = {"dml_fields": xfr_data["dml_fields"]}
                print(f"[i] Applied {xfr_data['name']} ({len(xfr_data['dml_fields'])} fields) to {nid}")
    elif "_raw_dml" in xfr_rules:
        raw_rule = xfr_rules.pop("_raw_dml")
        if raw_rule.get("dml_fields"):
            xfr_rules["_global_dml_fields"] = raw_rule["dml_fields"]
        else:
            xfr_rules["_global_raw_dml"] = raw_rule
    # Remove placeholder entries (select: "*", where: None) that would block embeddeds
    xfr_rules = {k: v for k, v in xfr_rules.items() 
                 if not (v.get("select") == "*" and v.get("where") is None and len(v) == 2)}
    dml = parse_dml(dml_path) if dml_path else {}
    dml_schema = dml.get("schema", {})

    # Extract embedded transforms from GDE .mp (DML transforms, keys, filters)
    if ast.get("abinitio_params") is not None:  # Always extract for GDE format (even if no params)
        with open(project_path, "r", errors="replace") as f:
            raw_content = f.read().replace('\x00', '')
        embedded = _extract_embedded_transforms(raw_content)
        if embedded["transforms"] or embedded["keys"] or embedded["keys_by_vertex"] or embedded["filters"] or embedded["filters_by_vertex"] or embedded["keeps"]:
            print(f"[i] Embedded transforms: {len(embedded['transforms'])} transforms, {len(embedded['keys'])} keys, {len(embedded['filters'])} filters")
            # Build node_by_id using VERTEX IDs as keys (for keys_by_vertex mapping)
            node_map = {}
            for node_data in ast.get("nodes", []):
                vid = node_data.get("vertex_id", node_data["id"])
                node_map[vid] = {
                    "name": node_data["id"],
                    "comp_type": node_data.get("name", node_data["id"]),
                }
            _apply_embedded_transforms(node_map, embedded, xfr_rules)
            if xfr_rules:
                print(f"[i] XFR rules generated: {list(xfr_rules.keys())}")
                for rk, rv in xfr_rules.items():
                    print(f"    {rk}: {rv}")
    
    # Apply data_path from GDE nodes to xfr_rules (for SOURCE/SINK path resolution)
    for node_data in ast.get("nodes", []):
        if "data_path" in node_data:
            ntype = node_data["type"].upper()
            node_id_lower = node_data["id"].lower()
            if ntype == "SOURCE":
                if node_id_lower not in xfr_rules:
                    xfr_rules[node_id_lower] = {}
                xfr_rules[node_id_lower]["path"] = f"s3://bnx/raw{node_data['data_path']}"
            elif ntype == "SINK":
                if node_id_lower not in xfr_rules:
                    xfr_rules[node_id_lower] = {}
                xfr_rules[node_id_lower]["path"] = f"s3://bnx/output{node_data['data_path']}"

    # Apply _global_dml_fields to TRANSFORM nodes that don't have rules
    if "_global_dml_fields" in xfr_rules:
        dml_fields = xfr_rules.pop("_global_dml_fields")
        for node_data in ast.get("nodes", []):
            if node_data["type"].upper() == "TRANSFORM":
                nid = node_data["id"].lower()
                if nid not in xfr_rules:
                    xfr_rules[nid] = {"dml_fields": dml_fields}
                    print(f"[i] Applied DML fields ({len(dml_fields)} fields) to {nid}")
                    break  # Apply to first transform without rules

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
    elif target == "python":
        _generate_pandas(dag, output_path, xfr_rules)
        print(f"\n[>] Target: Python Puro (pandas)")
    else:
        generate_glue(dag, output_path, xfr_rules)

    # Inject Ab Initio parameters as configuration block at top of generated file
    abi_params = ast.get("abinitio_params", {})
    all_params = {**abi_params, **pset_params}
    # Skip param injection if too many — add as comments only
    if all_params and len(all_params) <= 50:
        with open(output_path, "r") as f:
            generated_code = f.read()
        
        # Build config block
        config_lines = []
        config_lines.append("# " + "=" * 60)
        config_lines.append("# AB INITIO PARAMETERS (extracted from .mp + .pset)")
        config_lines.append("# " + "=" * 60)
        config_lines.append("ABINITIO_CONFIG = {")
        
        # Group params by category
        kafka_params = {k: v for k, v in all_params.items() if any(x in k.lower() for x in ["kafka", "confluent", "schema_registry", "topic", "bootstrap", "consumer", "producer"])}
        source_params = {k: v for k, v in all_params.items() if any(x in k.lower() for x in ["source", "input", "read", "extract"])}
        target_params = {k: v for k, v in all_params.items() if any(x in k.lower() for x in ["target", "output", "write", "sink", "load"])}
        dml_params = {k: v for k, v in all_params.items() if any(x in k.lower() for x in ["dml", "schema", "format", "record"])}
        other_params = {k: v for k, v in all_params.items() if k not in kafka_params and k not in source_params and k not in target_params and k not in dml_params}
        
        def write_section(name, params_dict):
            if not params_dict:
                return
            config_lines.append(f"    # -- {name} --")
            for k, v in sorted(params_dict.items()):
                safe_v = str(v).replace('"', '\\"') if v else ""
                config_lines.append(f'    "{k}": "{safe_v}",')
        
        write_section("KAFKA / CONFLUENT", kafka_params)
        write_section("SOURCE", source_params)
        write_section("TARGET / SINK", target_params)
        write_section("DML / SCHEMA", dml_params)
        write_section("OTHER", other_params)
        
        config_lines.append("}")
        config_lines.append("")
        config_lines.append("# " + "-" * 60)
        config_lines.append("# TO CUSTOMIZE: modify values above, then adjust code below")
        config_lines.append("# Kafka: update bootstrap_servers, topic, schema_registry_url")
        config_lines.append("# Source: update paths, formats, connection strings")
        config_lines.append("# Target: update output paths, table names")
        config_lines.append("# " + "-" * 60)
        config_lines.append("")
        
        # Insert after the imports (after the docstring)
        insert_point = generated_code.find('\n\n', generated_code.find('"""', 3))
        if insert_point > 0:
            new_code = generated_code[:insert_point + 2] + "\n".join(config_lines) + "\n" + generated_code[insert_point + 2:]
        else:
            new_code = "\n".join(config_lines) + "\n" + generated_code
        
        with open(output_path, "w") as f:
            f.write(new_code)
        
        print(f"[i] Injected {len(all_params)} parameters into {output_path}")
        print(f"    Kafka: {len(kafka_params)}, Source: {len(source_params)}, Target: {len(target_params)}, DML: {len(dml_params)}")
        print(f"\n[>] Target: AWS Glue")
    elif all_params and len(all_params) > 50:
        # Too many params — add as comments only (reference)
        with open(output_path, "r") as f:
            generated_code = f.read()
        
        comment_lines = []
        comment_lines.append("# " + "=" * 60)
        comment_lines.append(f"# AB INITIO PARAMETERS ({len(all_params)} params — reference only)")
        comment_lines.append("# " + "=" * 60)
        for k, v in sorted(list(all_params.items())[:30]):
            safe_v = str(v).replace("\n", " ")[:60] if v else ""
            comment_lines.append(f"# {k} = {safe_v}")
        if len(all_params) > 30:
            comment_lines.append(f"# ... and {len(all_params) - 30} more parameters")
        comment_lines.append("# " + "=" * 60)
        comment_lines.append("")
        
        insert_point = generated_code.find('\n\n', generated_code.find('"""', 3))
        if insert_point > 0:
            new_code = generated_code[:insert_point + 2] + "\n".join(comment_lines) + "\n" + generated_code[insert_point + 2:]
        else:
            new_code = "\n".join(comment_lines) + "\n" + generated_code
        
        with open(output_path, "w") as f:
            f.write(new_code)
        
        print(f"[i] Added {len(all_params)} parameters as comments in {output_path}")

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
    parser.add_argument("--ksh", required=False, default=None)
    parser.add_argument("--target", choices=["glue", "spark", "flink", "python"], default="glue")
    args = parser.parse_args()
    
    # Parse KSH if provided
    if args.ksh:
        ksh_meta = parse_ksh(args.ksh)
        print(f"[i] KSH loaded: {args.ksh}")
        print(f"    Graph: {ksh_meta['graph_name']}")
        print(f"    MP path: {ksh_meta['mp_path']}")
        print(f"    Ab Initio: {ksh_meta['ab_version']}")
        print(f"    AB_HOME: {ksh_meta['ab_home']}")
        print()
    
    main(args.project, args.output, args.xfr, args.dml, args.pset, args.target)
