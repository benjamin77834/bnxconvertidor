# src/mp_parser.py
import re

def normalize_id(name):
    safe = re.sub(r"[^\w]", "_", name.strip())
    # Un id que empieza con digito (p.ej. nombre de componente '100') genera
    # variables Python invalidas en el codegen ('100_df'). Prefijar con 'n_'.
    if safe and safe[0].isdigit():
        safe = "n_" + safe
    if not safe:
        safe = "node"
    return safe


def _detect_native_abinitio(content):
    """Detect if file is native Ab Initio format (XXGpvertex/XXGedge)."""
    return "XXGpvertex" in content or "XXGedge" in content


def _map_abinitio_type(component_name):
    """Map Ab Initio component names to BNX node types.

    Acepta tanto el nombre visible como el 'mpname'/prototype canonico de Ab
    Initio (create_data, reformat, rollup, dedup_sorted, join, lookup_file, etc.).
    El orden importa: primero los patrones especificos (dedup, create_data) y
    luego los genericos, para no clasificar mal (p.ej. 'dedup' antes que 'sort').
    """
    name = component_name.lower()
    # Create_Data / Generate_Records: GENERADOR de filas -> es una SOURCE (no
    # tiene entrada; produce registros a partir de un transform de literales).
    # Debe ir ANTES de 'reformat/transform' porque su mpname puede contener 'data'.
    if any(k in name for k in ["create_data", "create data", "generate_records",
                                "generate records", "gen_data"]):
        return "SOURCE"
    # Dedup Sort de Ab Initio (dedup_sorted / dedup sort / remove duplicates).
    # ANTES de 'sort' y de 'source' para no caer en TRANSFORM/otro por el token.
    if any(k in name for k in ["dedup", "deduplicate", "remove duplicate",
                                "remove_duplicate"]):
        return "DEDUP"
    # Lookup File (fuente de referencia para joins/lookup()). ANTES de join.
    if any(k in name for k in ["lookup_file", "lookup file"]):
        return "SOURCE"
    if any(k in name for k in ["read", "input", "scan", "source", "extract",
                                "input_file", "input_table", "intermediate_file"]):
        return "SOURCE"
    if any(k in name for k in ["write", "output", "sink", "load",
                                "output_file", "output_table", "update_table"]):
        return "SINK"
    if any(k in name for k in ["merge", "join", "lookup"]):
        return "JOIN"
    if any(k in name for k in ["rollup", "aggregate", "summary", "scan_"]):
        return "TRANSFORM"
    if any(k in name for k in ["reformat", "transform", "compute", "normalize",
                                "redefine_format", "redefine format", "copy"]):
        return "TRANSFORM"
    if any(k in name for k in ["sort"]):
        return "TRANSFORM"
    if any(k in name for k in ["partition", "repartition", "broadcast"]):
        return "PARTITION"
    if any(k in name for k in ["filter", "select", "where"]):
        return "FILTER"
    if any(k in name for k in ["concatenate", "concat", "gather", "combine",
                                "interleave"]):
        return "CONCATENATE"
    return "TRANSFORM"


def _parse_native_abinitio(content):
    """Parse native Ab Initio .mp format (formato repositorio EME).

    Los componentes son XXGpvertex (proceso) y XXGfvertex (datasets/archivos).
    Los flujos NO son aristas directas: se reconstruyen por la cadena
      flow  <-(XXGoport_dst_flow)-  oport  <-(XXGvertex_oport_oport)-  vertex_origen
      flow  <-(XXGiport_src_flow)-  iport  <-(XXGvertex_iport_iport)-  vertex_destino
    y el ordinal del puerto de entrada (in0/in1) viene en XXGiport_src_flow.
    """
    nodes = []
    edges = []
    params = {}
    node_map = {}          # objId (str) -> node info {id,name,type}
    # Mapas para reconstruir los edges por puertos.
    oport2vertex = {}      # oportId -> vertexObjId
    iport2vertex = {}      # iportId -> vertexObjId
    flow_src = {}          # flowId -> oportId  (origen)
    flow_dst = {}          # flowId -> (iportId, ordinal)  (destino + puerto in)

    def _last_two_ids(ln):
        # captura los dos ids finales '...}A|B|}' de las lineas de relacion.
        mm = re.search(r'\}(\d+)\|(\d+)\|\}', ln)
        return (mm.group(1), mm.group(2)) if mm else (None, None)

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        # --- Relaciones puerto<->vertice y flow<->puerto (edges por puertos) ---
        if "XXGvertex_oport_oport" in line:
            vtx, oport = _last_two_ids(line)
            if vtx and oport:
                oport2vertex[oport] = vtx
            continue
        if "XXGvertex_iport_iport" in line:
            vtx, iport = _last_two_ids(line)
            if vtx and iport:
                iport2vertex[iport] = vtx
            continue
        if "XXGoport_dst_flow" in line:
            oport, flow = _last_two_ids(line)
            if oport and flow:
                flow_src[flow] = oport
            continue
        if "XXGiport_src_flow" in line:
            iport, flow = _last_two_ids(line)
            if iport and flow:
                # ordinal del puerto de entrada: primer valor del payload {ORD|}
                ordm = re.search(r'\{(\d+)\|\}', line)
                ordinal = int(ordm.group(1)) if ordm else 0
                flow_dst[flow] = (iport, ordinal)
            continue

        # Parse vertex de PROCESO o de DATASET (fvertex): mismo objId en idx 2.
        m = re.match(r'\{[^|]*\|XXG[pf]vertex\|(\d+)\|', line)
        if m:
            vid = m.group(1)
            # El TIPO real del componente esta en el 'mpname' o en el
            # '!prototype_path' del vertice (p.ej. Validate/Create_Data.mpc,
            # Transform/Rollup.mpc, Dedup_Sorted.mpc), NO en la descripcion.
            # Preferimos el prototipo (nombre canonico del componente Ab Initio).
            proto = ""
            proto_m = re.search(r'\|!?prototype_path\|([^|]+)\|', line)
            if proto_m:
                # ultimo segmento del path, sin extension .mpc: Create_Data, Rollup...
                proto = proto_m.group(1).strip().split("/")[-1]
                if proto.lower().endswith(".mpc"):
                    proto = proto[:-4]
            mpname_m = re.search(r'\|mpname\|([^|]+)\|', line)
            mpname = mpname_m.group(1).strip().lstrip("?") if mpname_m else ""

            # Nombre visible: el que se ve en el canvas (@1|...) o el mpname.
            name_match = re.search(r'@1\|([^|]+)\|', line)
            if name_match:
                comp_name = name_match.group(1).strip()
            else:
                comp_name = mpname or proto or f"Component_{vid}"

            # Clasificar por el nombre CANONICO (prototipo/mpname), con fallback
            # al nombre visible. Asi Create_Data->SOURCE, Rollup->TRANSFORM, etc.
            type_hint = proto or mpname or comp_name
            ntype = _map_abinitio_type(type_hint)

            nid = normalize_id(comp_name)

            # Handle duplicate names
            if nid in node_map:
                nid = f"{nid}_{vid}"

            node_map[vid] = {"id": nid, "name": comp_name, "type": ntype}
            nodes.append({
                "id": nid,
                "name": comp_name,
                "type": ntype,
                "params": "",
                "subgraph": None,
                # Guardamos el prototipo/mpname para downstream (validador,
                # codegen) — permite detectar generadores (Create_Data) y el
                # tipo real sin re-parsear.
                "prototype": proto,
                "mpname": mpname,
            })
            continue

        # Compat: si el archivo trae aristas directas XXGedge, usarlas tambien.
        m = re.match(r'\{[^|]*\|XXGedge\|(\d+)\|(\d+)\|', line)
        if m:
            from_vid, to_vid = m.group(1), m.group(2)
            if from_vid in node_map and to_vid in node_map:
                edges.append({
                    "from": node_map[from_vid]["id"],
                    "to": node_map[to_vid]["id"],
                })
            continue

        # Parse parameters del grafo: {id|XXparameter|name|value|...}
        m = re.match(r'\{[^|]*\|XXparameter\|([^|]+)\|([^|]*)\|', line)
        if m:
            params[m.group(1).strip()] = m.group(2).strip()
            continue

    # --- Reconstruir edges por la cadena flow -> puerto -> vertice ---
    # Para cada flow que tenga origen (oport) y destino (iport) resueltos a
    # vertices reales, emitimos una arista con el ordinal del puerto de entrada
    # (to_port) para que el DAG ordene bien los padres de un JOIN/MERGE.
    for flow_id, oport in flow_src.items():
        dst = flow_dst.get(flow_id)
        if not dst:
            continue
        iport, ordinal = dst
        src_vtx = oport2vertex.get(oport)
        dst_vtx = iport2vertex.get(iport)
        if src_vtx in node_map and dst_vtx in node_map:
            edges.append({
                "from": node_map[src_vtx]["id"],
                "to": node_map[dst_vtx]["id"],
                "to_port": ordinal,
            })

    return {"nodes": nodes, "edges": edges, "subgraphs": {}, "abinitio_params": params}


def parse_mp_ast(file_path):
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Auto-detect native Ab Initio format
    if _detect_native_abinitio(content):
        return _parse_native_abinitio(content)

    # BNX format
    nodes = []
    edges = []
    subgraphs = {}
    current_subgraph = None

    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # SUBGRAPH inicio: SUBGRAPH NombreSub {
        m = re.match(r"(?i)SUBGRAPH\s+(\w+)\s*\{", line)
        if m:
            current_subgraph = m.group(1)
            subgraphs[current_subgraph] = []
            continue

        # Cierre de subgraph
        if line == "}":
            current_subgraph = None
            continue

        # Formato: NODE NombreNodo : tipo
        m = re.match(r"(?i)NODE\s+(\w+)\s*:\s*(\w+)", line)
        if m:
            nid = normalize_id(m.group(1))
            nodes.append({
                "id": nid,
                "name": m.group(1),
                "type": m.group(2).upper(),
                "params": "",
                "subgraph": current_subgraph
            })
            if current_subgraph:
                subgraphs[current_subgraph].append(nid)
            continue

        # Formato: A -> B  (edge)
        m = re.match(r"(\w+)\s*->\s*(\w+)", line)
        if m:
            edges.append({"from": normalize_id(m.group(1)), "to": normalize_id(m.group(2))})
            continue

        # Formato legacy: NombreNodo:TIPO:params
        parts = line.split(":")
        name = parts[0].strip()
        node_type = parts[1].strip() if len(parts) > 1 else "XFR"
        params = ":".join(parts[2:]).strip() if len(parts) > 2 else ""
        nid = normalize_id(name)
        nodes.append({
            "id": nid,
            "name": name,
            "type": node_type.upper(),
            "params": params,
            "subgraph": current_subgraph
        })
        if current_subgraph:
            subgraphs[current_subgraph].append(nid)

    return {"nodes": nodes, "edges": edges, "subgraphs": subgraphs}