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
    node_by_nid = {}       # nid -> dict del nodo (para adjuntar params por vertice)
    current_node = None    # ultimo nodo vertice visto (para asociarle key/keep/...)
    # Mapas para reconstruir los edges por puertos.
    oport2vertex = {}      # oportId -> vertexObjId
    iport2vertex = {}      # iportId -> vertexObjId
    flow_src = {}          # flowId -> oportId  (origen)
    flow_dst = {}          # flowId -> (iportId, ordinal)  (destino + puerto in)
    proto_of = {}          # instanceObjId -> prototypeObjId (XXGobject_proto_object)
    port_binding = {}      # portId(externo) <-> portId(interno) de subgrafos
    vertex_name = {}       # objId -> nombre visible (de XXGgraph_vertex_vertex)

    def _last_two_ids(ln):
        # captura los dos ids finales '...}A|B|}' de las lineas de relacion.
        mm = re.search(r'\}(\d+)\|(\d+)\|\}', ln)
        return (mm.group(1), mm.group(2)) if mm else (None, None)

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        # --- Relaciones puerto<->vertice y flow<->puerto (edges por puertos) ---
        # Cualquiera de estas lineas marca el fin del bloque de parametros del
        # vertice actual (los params de un vertice van justo despues de su linea).
        if any(t in line for t in ("XXGvertex_oport_oport", "XXGvertex_iport_iport",
                                    "XXGoport_dst_flow", "XXGiport_src_flow",
                                    "XXGflow", "XXGiport", "XXGoport")):
            current_node = None
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
        # Bindings de puertos entre niveles (subgrafo <-> padre): un puerto
        # externo del subgrafo se "enlaza" a un puerto interno. Cuando un flow
        # apunta a un puerto binding, hay que seguir el enlace hasta el puerto
        # real del componente. Guardamos el enlace en ambos sentidos.
        if "XXGoport_binding_oport" in line or "XXGiport_binding_iport" in line:
            a_port, b_port = _last_two_ids(line)
            if a_port and b_port:
                port_binding[a_port] = b_port
                port_binding[b_port] = a_port
            continue
        # Nombre visible del componente: XXGgraph_vertex_vertex|..|{Nombre|}graph|objId|
        if "XXGgraph_vertex_vertex" in line:
            nm = re.search(r'\{([^|{}]+)\|\}', line)
            _g, obj = _last_two_ids(line)
            if nm and obj:
                vertex_name[obj] = nm.group(1).strip()
            continue
        # proto_object: '...}<prototypeId>|<instanceId>|}' — el mismo componente
        # aparece como prototipo (con params: key/keep) e instancia (con puertos).
        # Guardamos instance->prototype para FUSIONAR sus params despues.
        if "XXGobject_proto_object" in line:
            proto_id, inst_id = _last_two_ids(line)
            if proto_id and inst_id:
                proto_of[inst_id] = proto_id
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

        # Parse vertex de PROCESO (pvertex), DATASET (fvertex) o TABLA DB
        # (tvertex: Input_Table/Unload de Teradata/Oracle). Mismo objId en idx 2.
        m = re.match(r'\{[^|]*\|XXG[pft]vertex\|(\d+)\|', line)
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

            # Desambiguar nombres duplicados: MUCHOS componentes comparten nombre
            # (12 'Reformat', varios 'copy'...). Antes se comparaba contra node_map
            # (indexado por objId) y nunca detectaba el choque -> todos colapsaban
            # al mismo nid, creando self-loops y ciclos falsos. Usamos el set de
            # nids ya usados y sufijamos con el objId para que cada componente sea
            # un nodo unico.
            if nid in node_by_nid:
                nid = f"{nid}_{vid}"

            node_map[vid] = {"id": nid, "name": comp_name, "type": ntype}
            _node = {
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
            }
            nodes.append(_node)
            node_by_nid[nid] = _node
            # Este pasa a ser el vertice "actual": los XXparameter que siguen
            # (key, keep, select, ...) pertenecen a el hasta el proximo vertice.
            current_node = _node
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

        # Parse parameters: {id|XXparameter|name|value|...}
        m = re.match(r'\{[^|]*\|XXparameter\|([^|]+)\|([^|]*)\|', line)
        if m:
            pname = m.group(1).strip()
            pval = m.group(2).strip()
            # Si pertenece a un vertice (hay current_node), capturar los
            # parametros relevantes del componente (key de dedup/sort, keep...).
            if current_node is not None and pname in (
                "key", "keep", "select", "dedup_key", "sorted-input",
                "!prototype_path", "prototype_path", "mpname", "URL", "Layout",
                "file", "path"
            ):
                # La key de Ab Initio viene como '\{campo1; campo2\}': limpiar
                # backslashes de escape y separar por ';'/','/espacio.
                if pname in ("key", "dedup_key"):
                    raw = pval.replace("\\{", "").replace("\\}", "") \
                              .replace("{", "").replace("}", "").strip()
                    keys = [k.strip() for k in re.split(r"[;,\s]+", raw) if k.strip()]
                    if keys:
                        current_node["dedup_keys"] = keys
                        current_node["key_cols"] = keys
                elif pname in ("!prototype_path", "prototype_path"):
                    # El prototipo puede venir en linea aparte: reclasificar el
                    # nodo (p.ej. Lookup_File.mdc -> SOURCE, Dedup_Sorted -> DEDUP).
                    _proto = pval.split("/")[-1]
                    if _proto.lower().endswith((".mpc", ".mdc")):
                        _proto = _proto[:-4]
                    if not current_node.get("prototype"):
                        current_node["prototype"] = _proto
                        _t = _map_abinitio_type(_proto)
                        # Reclasificar solo si el tipo actual era el generico.
                        if current_node.get("type") in (None, "TRANSFORM"):
                            current_node["type"] = _t
                        # Marcar los Lookup_File como fuentes de lookup.
                        if "lookup" in _proto.lower():
                            current_node["is_lookup_file"] = True
                elif pname in ("URL", "Layout", "file", "path"):
                    # Ruta del dataset (source/sink/lookup file).
                    if not current_node.get("data_path"):
                        current_node["data_path"] = pval
                else:
                    current_node[pname] = pval
            else:
                # Parametro a nivel de grafo (INPUT_FILE, OUTPUT_PATH, etc.).
                params[pname] = pval
            continue

    # --- Fusionar prototipo <-> instancia ---
    # El mismo componente aparece 2 veces (prototipo con params key/keep, e
    # instancia con puertos). proto_of mapea instancia->prototipo. PERO los flows
    # pueden conectar a CUALQUIERA de los dos vertices (via sus puertos), asi que
    # no podemos asumir cual eliminar. Estrategia:
    #  1) determinar que vertices participan realmente en algun flow (tienen edge)
    #  2) fusionar los params en AMBOS (bidireccional) para no perder la key
    #  3) eliminar el vertice del par que NO tiene ningun flow (huerfano)
    _connected = set()  # objIds de vertices que participan en algun flow
    for _flow, _op in flow_src.items():
        _v = oport2vertex.get(_op)
        if _v:
            _connected.add(_v)
    for _flow, (_ip, _o) in flow_dst.items():
        _v = iport2vertex.get(_ip)
        if _v:
            _connected.add(_v)

    _drop_ids = set()
    for inst_id, proto_id in proto_of.items():
        a_info = node_map.get(inst_id)
        b_info = node_map.get(proto_id)
        if not a_info or not b_info:
            continue
        a_node = node_by_nid.get(a_info["id"])
        b_node = node_by_nid.get(b_info["id"])
        if not a_node or not b_node:
            continue
        # Fusion bidireccional de params relevantes (no perder la dedup key).
        for _f in ("dedup_keys", "key_cols", "keep", "select", "prototype"):
            if a_node.get(_f) and not b_node.get(_f):
                b_node[_f] = a_node[_f]
            elif b_node.get(_f) and not a_node.get(_f):
                a_node[_f] = b_node[_f]
        # Tipo mas especifico (Dedup_Sorted->DEDUP) para ambos.
        for src, dst, si, di in ((a_node, b_node, a_info, b_info),
                                  (b_node, a_node, b_info, a_info)):
            if src.get("type") and src["type"] not in ("TRANSFORM",) \
                    and dst.get("type") in (None, "TRANSFORM"):
                dst["type"] = src["type"]
                di["type"] = src["type"]
        # Eliminar el que NO participa en ningun flow (el huerfano del par).
        inst_connected = inst_id in _connected
        proto_connected = proto_id in _connected
        if inst_connected and not proto_connected:
            _drop_ids.add(b_info["id"])   # sobra el prototipo
        elif proto_connected and not inst_connected:
            _drop_ids.add(a_info["id"])   # sobra la instancia
        elif not inst_connected and not proto_connected:
            # Ninguno conectado: conservar uno (la instancia) y soltar el otro.
            _drop_ids.add(b_info["id"])
        # Si AMBOS estan conectados, no eliminar (son nodos distintos reales).

    if _drop_ids:
        nodes = [n for n in nodes if n["id"] not in _drop_ids]

    # --- Reconstruir edges por la cadena flow -> puerto -> vertice ---
    # Para cada flow que tenga origen (oport) y destino (iport) resueltos a
    # vertices reales, emitimos una arista con el ordinal del puerto de entrada
    # (to_port) para que el DAG ordene bien los padres de un JOIN/MERGE.
    def _resolve_vtx(port, port2vtx):
        # Resuelve el vertice de un puerto; si el puerto es un binding de
        # subgrafo, sigue el enlace hasta el puerto real del componente.
        v = port2vtx.get(port)
        if v is not None:
            return v
        bound = port_binding.get(port)
        if bound is not None:
            return port2vtx.get(bound) or iport2vertex.get(bound) or oport2vertex.get(bound)
        return None

    for flow_id, oport in flow_src.items():
        dst = flow_dst.get(flow_id)
        if not dst:
            continue
        iport, ordinal = dst
        src_vtx = _resolve_vtx(oport, oport2vertex)
        dst_vtx = _resolve_vtx(iport, iport2vertex)
        if src_vtx in node_map and dst_vtx in node_map:
            edges.append({
                "from": node_map[src_vtx]["id"],
                "to": node_map[dst_vtx]["id"],
                "to_port": ordinal,
            })

    # Marcar los Lookup_File como fuentes de lookup (SOURCE) por su prototipo.
    # Se hace al FINAL (tras la fusion prototipo/instancia) para que el flag
    # quede en el nodo que realmente sobrevive.
    for _n in nodes:
        if "lookup" in (_n.get("prototype") or "").lower():
            _n["is_lookup_file"] = True
            _n["type"] = "SOURCE"

    return {"nodes": nodes, "edges": edges, "subgraphs": {},
            "abinitio_params": params, "vertex_names": vertex_name}


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