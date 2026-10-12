# ============================================================
# BNX Metadata — construye un modelo CANONICO del grafo convertido
# (grafo + descripcion + nodos + columnas + linaje de columnas) y lo
# exporta a formatos de catalogo:
#   - canonico BNX (JSON)        : fuente de verdad, portable
#   - OpenLineage (JSON)         : estandar de linaje (Marquez/DataHub/...)
#   - Glue Data Catalog (boto3)  : script Python para crear tablas+metadata
#   - Databricks Unity Catalog   : DDL SQL (CREATE TABLE + COMMENT + PROPERTIES)
#
# El linaje se calcula aqui en Python (mismo criterio que la util del
# frontend ui/src/lib/lineage.js) a partir del DAG, las reglas XFR y el
# dml_schema. Es best-effort y determinístico.
# ============================================================
import json
import re
from datetime import datetime, timezone


# ---------- indices del grafo ----------
def _index(nodes, edges):
    by_id = {n["id"]: n for n in nodes}
    parents, children = {}, {}
    for n in nodes:
        parents[n["id"]] = []
        children[n["id"]] = []
    for e in edges:
        if e["from"] in children:
            children[e["from"]].append(e["to"])
        if e["to"] in parents:
            parents[e["to"]].append(e["from"])
    # fallback a parents/children declarados en el nodo
    for n in nodes:
        if not parents[n["id"]] and isinstance(n.get("parents"), list):
            parents[n["id"]] = list(n["parents"])
        if not children[n["id"]] and isinstance(n.get("children"), list):
            children[n["id"]] = list(n["children"])
    return by_id, parents, children


# ---------- columnas de una regla ----------
def _columns_from_rule(rule):
    """Columnas DECLARADAS por una regla (select real o dml_fields).
    Devuelve lista [{out, srcExpr, kind}] o None si es passthrough."""
    if not rule:
        return None
    sel = (rule.get("select") or "").strip()
    if sel and sel != "*":
        out = []
        for c in [s.strip() for s in sel.split(",") if s.strip()]:
            m = re.match(r"^(.*?)\s+as\s+(\w+)$", c, re.I)
            if m:
                out.append({"out": m.group(2), "srcExpr": m.group(1).strip(), "kind": "select"})
            else:
                out.append({"out": c, "srcExpr": c, "kind": "select"})
        return out
    dmlf = rule.get("dml_fields")
    if isinstance(dmlf, list) and dmlf:
        return [{"out": f.get("field"), "srcExpr": f.get("expr") or "", "kind": f.get("type") or "derived"}
                for f in dmlf]
    return None


def _refs_in_expr(expr):
    if not expr:
        return []
    refs = []
    for m in re.finditer(r'col\(\s*["\'](\w+)["\']\s*\)', expr):
        refs.append(m.group(1))
    for m in re.finditer(r'\bin\d*\.(\w+)', expr):
        refs.append(m.group(1))
    if not refs:
        s = expr.strip()
        if re.match(r'^\w+$', s):
            refs.append(s)
    # dedup preservando orden
    seen, out = set(), []
    for r in refs:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def _known_cols(nid, by_id, parents, dml_schema, _seen=None):
    """Columnas conocidas de un nodo (best-effort)."""
    if _seen is None:
        _seen = set()
    if nid in _seen:
        return []
    _seen.add(nid)
    n = by_id.get(nid)
    if not n:
        return []
    if (n.get("type") or "").upper() == "SOURCE":
        sc = dml_schema.get(n["id"]) or dml_schema.get(n.get("name")) or {}
        return list(sc.keys())
    rc = _columns_from_rule(n.get("rule"))
    if rc:
        return [c["out"] for c in rc]
    inh = []
    for p in parents.get(nid, []):
        for c in _known_cols(p, by_id, parents, dml_schema, _seen):
            if c not in inh:
                inh.append(c)
    return inh


def _column_lineage_for(nid, by_id, parents, dml_schema):
    """Linaje de columnas de un nodo: filas {out, from:[{node,col}], kind}."""
    n = by_id.get(nid)
    if not n:
        return {"kind": "none", "rows": []}
    ntype = (n.get("type") or "").upper()

    if ntype == "SOURCE":
        sc = dml_schema.get(n["id"]) or dml_schema.get(n.get("name")) or {}
        return {
            "kind": "source",
            "rows": [{"out": c, "from": [{"node": n["id"], "col": c}],
                      "kind": "origin", "dtype": t} for c, t in sc.items()],
        }

    ps = parents.get(nid, [])
    provider = {}
    for p in ps:
        for c in _known_cols(p, by_id, parents, dml_schema):
            provider.setdefault(c, p)

    def resolve(cols):
        out = []
        for c in cols:
            if c in provider:
                out.append({"node": provider[c], "col": c})
            elif len(ps) == 1:
                out.append({"node": ps[0], "col": c})
        return out

    declared = _columns_from_rule(n.get("rule"))
    if declared:
        rows = []
        for d in declared:
            rows.append({
                "out": d["out"],
                "from": resolve(_refs_in_expr(d["srcExpr"])),
                "kind": d["kind"],
                "expr": d["srcExpr"] if d["srcExpr"] and d["srcExpr"] != d["out"] else None,
            })
        return {"kind": ntype.lower(), "rows": rows}

    # passthrough
    join_key = (n.get("rule") or {}).get("join_key")
    all_cols = []
    for p in ps:
        for c in _known_cols(p, by_id, parents, dml_schema):
            if c not in all_cols:
                all_cols.append(c)
    rows = [{"out": c, "from": resolve([c]),
             "kind": "join-key" if (join_key and c == join_key) else "passthrough"}
            for c in all_cols]
    return {"kind": ntype.lower(), "joinKey": join_key, "rows": rows}


# ---------- modelo canonico ----------
def build_canonical(result):
    """Construye la metadata canonica BNX desde el `result` de /compile.

    result debe traer: nodes (con rule), edges, dml_schema, graph_name,
    description, params.
    """
    nodes = result.get("nodes", [])
    edges = result.get("edges", [])
    dml_schema = result.get("dml_schema", {}) or {}
    by_id, parents, children = _index(nodes, edges)

    canon_nodes = []
    for n in nodes:
        lin = _column_lineage_for(n["id"], by_id, parents, dml_schema)
        canon_nodes.append({
            "id": n["id"],
            "name": n.get("name") or n["id"],
            "type": (n.get("type") or "").upper(),
            "parents": parents.get(n["id"], []),
            "children": children.get(n["id"], []),
            "rule": n.get("rule") or {},
            "columns": lin["rows"],
        })

    return {
        "bnx_metadata_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "graph": {
            "name": result.get("graph_name") or "grafo",
            "description": result.get("description") or "",
            "params": result.get("params") or {},
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        "nodes": canon_nodes,
        "edges": [{"from": e["from"], "to": e["to"]} for e in edges],
    }


# ---------- mapeo de tipos ----------
_GLUE_TYPES = {
    "string": "string", "int": "int", "integer": "int", "long": "bigint",
    "double": "double", "float": "float", "decimal": "decimal(38,10)",
    "date": "date", "timestamp": "timestamp", "boolean": "boolean",
}


def _glue_type(t):
    return _GLUE_TYPES.get((t or "string").lower(), "string")


def _source_sink_tables(canonical):
    """Devuelve (sources, sinks) con sus columnas+tipos para el catalogo.

    Los tipos reales viven en los SOURCE (dml_schema). En un SINK la columna
    puede provenir de un nodo intermedio (Sort/Join), asi que el tipo se
    propaga TRANSITIVAMENTE: por cada nodo se resuelve el tipo de cada
    columna siguiendo su procedencia hasta encontrar el dtype de un SOURCE.
    """
    by_id = {n["id"]: n for n in canonical["nodes"]}

    # tipo conocido por (nodo, columna); se llena primero con los SOURCE.
    dtype_at = {}
    for n in canonical["nodes"]:
        if n["type"] == "SOURCE":
            for r in n["columns"]:
                dtype_at[(n["id"], r["out"])] = r.get("dtype", "string")

    def resolve_dtype(node_id, col, _seen=None):
        if _seen is None:
            _seen = set()
        key = (node_id, col)
        if key in dtype_at:
            return dtype_at[key]
        if key in _seen:
            return "string"
        _seen.add(key)
        n = by_id.get(node_id)
        if not n:
            return "string"
        for r in n["columns"]:
            if r["out"] == col:
                for f in r.get("from", []):
                    dt = resolve_dtype(f["node"], f["col"], _seen)
                    if dt and dt != "string":
                        dtype_at[key] = dt
                        return dt
        return "string"

    sources = {}
    for n in canonical["nodes"]:
        if n["type"] == "SOURCE":
            sources[n["id"]] = [(r["out"], r.get("dtype", "string")) for r in n["columns"]]

    sinks = {}
    for n in canonical["nodes"]:
        if n["type"] == "SINK":
            cols = [(r["out"], resolve_dtype(n["id"], r["out"])) for r in n["columns"]]
            sinks[n["id"]] = cols

    return sources, sinks


# ---------- OpenLineage ----------
def build_openlineage(canonical):
    """Genera un documento OpenLineage (run events) para el grafo.

    Modela cada nodo como un 'job' y cada SOURCE/SINK como 'dataset', con
    el columnLineage facet por dataset de salida. Es un export estatico
    (un unico COMPLETE event por job) apto para cargar en Marquez/DataHub.
    """
    ns = "bnx"
    job_name = canonical["graph"]["name"]
    now = canonical["generated_at"]
    events = []

    by_id = {n["id"]: n for n in canonical["nodes"]}

    for n in canonical["nodes"]:
        inputs, outputs = [], []
        # inputs: datasets de los padres SOURCE; outputs: este nodo si es SINK/SOURCE
        for p in n["parents"]:
            pn = by_id.get(p)
            if pn and pn["type"] in ("SOURCE", "SINK"):
                inputs.append({"namespace": ns, "name": p})
        if n["type"] in ("SOURCE", "SINK"):
            fields = []
            col_lineage = {}
            for r in n["columns"]:
                fields.append({"name": r["out"], "type": r.get("dtype", "string")})
                if r.get("from"):
                    col_lineage[r["out"]] = {
                        "inputFields": [
                            {"namespace": ns, "name": f["node"], "field": f["col"]}
                            for f in r["from"]
                        ]
                    }
            ds = {
                "namespace": ns,
                "name": n["id"],
                "facets": {
                    "schema": {
                        "_producer": "bnx-convertidor",
                        "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
                        "fields": fields,
                    },
                    "documentation": {
                        "_producer": "bnx-convertidor",
                        "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DocumentationDatasetFacet.json",
                        "description": canonical["graph"]["description"],
                    },
                },
            }
            if col_lineage:
                ds["facets"]["columnLineage"] = {
                    "_producer": "bnx-convertidor",
                    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/ColumnLineageDatasetFacet.json",
                    "fields": col_lineage,
                }
            outputs.append(ds)

        events.append({
            "eventType": "COMPLETE",
            "eventTime": now,
            "producer": "bnx-convertidor",
            "job": {"namespace": ns, "name": f"{job_name}.{n['id']}"},
            "run": {"runId": f"{job_name}-{n['id']}"},
            "inputs": inputs,
            "outputs": outputs,
        })

    return {"openlineage_version": "1.0.0", "namespace": ns, "events": events}


# ---------- Glue Data Catalog (boto3 script) ----------
def build_glue_script(canonical, database="bnx_catalog"):
    """Genera un script boto3 que crea/actualiza tablas en Glue Data Catalog
    con columnas, descripcion y el linaje serializado en Parameters."""
    sources, sinks = _source_sink_tables(canonical)
    tables = {**sources, **sinks}
    desc = canonical["graph"]["description"].replace('"', "'")
    lineage_json = json.dumps(
        {n["id"]: n["columns"] for n in canonical["nodes"]}, ensure_ascii=False
    )

    lines = []
    lines.append('"""')
    lines.append(f'BNX -> AWS Glue Data Catalog')
    lines.append(f'Grafo: {canonical["graph"]["name"]}')
    lines.append(f'Generado: {canonical["generated_at"]}')
    lines.append('Crea las tablas source/sink con columnas, descripcion y linaje')
    lines.append('(en Parameters). Ejecutar con credenciales AWS validas.')
    lines.append('"""')
    lines.append("import boto3, json")
    lines.append("")
    lines.append("glue = boto3.client('glue')")
    lines.append(f"DATABASE = {database!r}")
    lines.append("")
    lines.append("# Crear la base de datos si no existe")
    lines.append("try:")
    lines.append(f"    glue.create_database(DatabaseInput={{'Name': DATABASE, 'Description': {desc!r}}})")
    lines.append("except glue.exceptions.AlreadyExistsException:")
    lines.append("    pass")
    lines.append("")
    lines.append(f"GRAPH_LINEAGE = json.loads({lineage_json!r})")
    lines.append("")

    for tname, cols in tables.items():
        kind = "SOURCE" if tname in sources else "SINK"
        col_py = ", ".join(
            f"{{'Name': {c!r}, 'Type': {_glue_type(t)!r}}}" for c, t in cols
        )
        lines.append(f"# [{kind}] {tname}")
        lines.append("glue.create_table(")
        lines.append("    DatabaseName=DATABASE,")
        lines.append("    TableInput={")
        lines.append(f"        'Name': {tname.lower()!r},")
        lines.append(f"        'Description': {desc!r},")
        lines.append("        'Parameters': {")
        lines.append(f"            'bnx_graph': {canonical['graph']['name']!r},")
        lines.append(f"            'bnx_node_type': {kind!r},")
        lines.append(f"            'bnx_column_lineage': json.dumps(GRAPH_LINEAGE.get({tname!r}, [])),")
        lines.append("            'classification': 'parquet',")
        lines.append("        },")
        lines.append("        'StorageDescriptor': {")
        lines.append(f"            'Columns': [{col_py}],")
        lines.append("            'Location': 's3://CHANGE_ME/' + " + repr(tname.lower()) + ",")
        lines.append("            'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',")
        lines.append("            'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',")
        lines.append("            'SerdeInfo': {'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'},")
        lines.append("        },")
        lines.append("    },")
        lines.append(")")
        lines.append(f"print('[ok] tabla creada: ' + DATABASE + '.' + {tname.lower()!r})")
        lines.append("")

    lines.append("print('[ok] BNX -> Glue Catalog completado')")
    return "\n".join(lines)


# ---------- Databricks Unity Catalog (DDL SQL) ----------
def build_databricks_ddl(canonical, catalog="bnx_catalog", schema="default"):
    """Genera DDL SQL para Databricks Unity Catalog: CREATE TABLE con
    COMMENT (tabla y columnas) y TBLPROPERTIES con la metadata del grafo.
    Nota: Unity Catalog CAPTURA el lineage al ejecutar; aqui dejamos el
    linaje como propiedades/comentarios para documentacion."""
    sources, sinks = _source_sink_tables(canonical)
    tables = {**sources, **sinks}
    gname = canonical["graph"]["name"]
    gdesc = canonical["graph"]["description"].replace("'", "''")

    def q(s):
        return str(s).replace("'", "''")

    lines = []
    lines.append(f"-- BNX -> Databricks Unity Catalog")
    lines.append(f"-- Grafo: {gname}")
    lines.append(f"-- Generado: {canonical['generated_at']}")
    lines.append("")
    lines.append(f"CREATE CATALOG IF NOT EXISTS {catalog};")
    lines.append(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema} COMMENT '{gdesc}';")
    lines.append("")

    # mapa col -> origen (para comentar linaje por columna)
    for tname, cols in tables.items():
        kind = "SOURCE" if tname in sources else "SINK"
        node = next((n for n in canonical["nodes"] if n["id"] == tname), None)
        lineage_by_col = {}
        if node:
            for r in node["columns"]:
                if r.get("from"):
                    lineage_by_col[r["out"]] = ", ".join(f'{f["node"]}.{f["col"]}' for f in r["from"])

        lines.append(f"-- [{kind}] {tname}")
        lines.append(f"CREATE TABLE IF NOT EXISTS {catalog}.{schema}.{tname.lower()} (")
        col_lines = []
        for c, t in cols:
            dt = _glue_type(t)  # Databricks acepta los mismos nombres base
            cm = lineage_by_col.get(c)
            if cm:
                col_lines.append(f"    {c} {dt} COMMENT 'lineage: {q(cm)}'")
            else:
                col_lines.append(f"    {c} {dt}")
        lines.append(",\n".join(col_lines))
        lines.append(")")
        lines.append("USING DELTA")
        lines.append(f"COMMENT '{gdesc}'")
        lines.append("TBLPROPERTIES (")
        lines.append(f"    'bnx_graph' = '{q(gname)}',")
        lines.append(f"    'bnx_node_type' = '{kind}'")
        lines.append(");")
        lines.append("")

    return "\n".join(lines)


# ---------- entrypoint ----------
def build_all(result):
    """Devuelve los 4 artefactos de metadata desde el `result` de /compile."""
    canonical = build_canonical(result)
    return {
        "canonical": canonical,
        "openlineage": build_openlineage(canonical),
        "glue_script": build_glue_script(canonical),
        "databricks_ddl": build_databricks_ddl(canonical),
    }
