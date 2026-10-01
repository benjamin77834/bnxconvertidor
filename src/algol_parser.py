# src/algol_parser.py
"""
Parser de ALGOL (variante de mainframe Unisys MCP / Burroughs) a .mp/.xfr/.dml
para el compilador BNX, siguiendo el mismo patron que cobol_parser.

Cubre el subconjunto tipico de ETL batch en ALGOL de Unisys:
  - Declaraciones de archivos:  FILE NOMBRE (KIND=DISK, ...);
  - Registros/campos:           RECORD / EBCDIC/REAL/INTEGER/ALPHA ... ;
  - Procedimientos:             PROCEDURE NOMBRE; BEGIN ... END;
  - Lectura/escritura:          READ(archivo, ...);  WRITE(archivo, ...);
  - Filtros:                    IF <cond> THEN ...
  - Joins:                      IF campoA = campoB THEN ...
  - Agregaciones:               total := total + campo;   (acumuladores)

NO es un compilador ALGOL completo: la logica algoritmica fina (loops
anidados, procedimientos recursivos) puede requerir ajuste manual. El objetivo
es reconstruir el flujo ETL (fuentes -> transforms/filtros/join/agg -> sinks).
"""
import re


def parse_algol(path):
    """Lee el archivo ALGOL (UTF-8 o EBCDIC) y extrae la estructura ETL."""
    content = None
    for enc in ["utf-8", "cp500", "cp1047", "latin-1"]:
        try:
            with open(path, "r", encoding=enc) as f:
                content = f.read()
            up = content.upper()
            # Sanity check: ALGOL de Unisys suele tener BEGIN/END/PROCEDURE/FILE.
            if "BEGIN" in up or "PROCEDURE" in up or "FILE " in up:
                break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if not content:
        raise ValueError(f"No se pudo decodificar el archivo ALGOL: {path}")

    lines = [l.rstrip() for l in content.splitlines()]

    files = _parse_files(lines)
    fields = _parse_fields(lines)
    procedures = _parse_procedures(lines)
    filters = _parse_filters(lines)
    joins = _parse_joins(lines)
    computes = _parse_computes(lines)

    return {
        "files": files,
        "fields": fields,
        "procedures": procedures,
        "filters": filters,
        "joins": joins,
        "computes": computes,
        "encoding": "EBCDIC" if ("EBCDIC" in content.upper()) else "ASCII",
    }


def _norm(name):
    return re.sub(r"[^\w]", "_", name).strip("_")


def _parse_files(lines):
    """Declaraciones de archivos ALGOL:
       FILE CUSTOMER (KIND=DISK, ...);
       FILE REPORT (KIND=PRINTER, ...);
    Devuelve {NOMBRE: kind} (kind en minusculas, '' si no se indica)."""
    files = {}
    for line in lines:
        m = re.match(r"\s*FILE\s+([A-Za-z][\w-]*)\s*(?:\((.*?)\))?\s*;?", line, re.I)
        if m:
            name = _norm(m.group(1))
            attrs = (m.group(2) or "")
            km = re.search(r"KIND\s*=\s*(\w+)", attrs, re.I)
            kind = km.group(1).lower() if km else ""
            files[name] = kind
    return files


# Tipos ALGOL -> tipo simple del grafo.
def _algol_type(decl):
    d = decl.upper()
    if "REAL" in d or "DOUBLE" in d:
        return "double"
    if "INTEGER" in d:
        # INTEGER grande -> long
        return "int"
    if "BOOLEAN" in d:
        return "int"
    if "EBCDIC" in d or "ALPHA" in d or "STRING" in d or "CHARACTER" in d or "PIC" in d:
        return "string"
    # EBCDIC ARRAY [...] suele ser texto
    if "ARRAY" in d:
        return "string"
    return "string"


def _parse_fields(lines):
    """Campos por archivo/record. En ALGOL de Unisys los campos de un registro
    suelen declararse dentro de un RECORD <FILE> ... o como DEFINE. Reconocemos:
       RECORD CUSTOMER_REC;
         EBCDIC CUST_ID [0:9];
         REAL   CUST_BALANCE;
       ...
       (o bloques FIELD = ...). El record se asocia al FILE del mismo prefijo.
    Devuelve {FILE: {campo: tipo}}."""
    schemas = {}
    current = None

    for raw in lines:
        line = raw.strip()
        # Inicio de un record: RECORD <NOMBRE>;  o  <FILE> RECORD ... ;
        m_rec = re.match(r"(?:RECORD\s+)?([A-Za-z][\w-]*)\s+RECORD\b", line, re.I) \
            or re.match(r"RECORD\s+([A-Za-z][\w-]*)", line, re.I)
        if m_rec:
            current = _norm(m_rec.group(1))
            # Normalizar: quitar sufijos tipicos (_REC, _RECORD) para casar con el FILE.
            current = re.sub(r"_(REC|RECORD)$", "", current, flags=re.I)
            schemas.setdefault(current, {})
            continue

        if current is not None:
            # Fin del record.
            if re.match(r"(END|PROCEDURE|FILE)\b", line, re.I):
                current = None
                continue
            # Declaracion de campo tipada: <TIPO> NOMBRE [ ... ] ;
            m_f = re.match(
                r"(EBCDIC|REAL|INTEGER|BOOLEAN|ALPHA|STRING|CHARACTER|DOUBLE)\b.*?\b([A-Za-z][\w-]*)\s*(?:\[.*?\])?\s*;?$",
                line, re.I)
            if m_f:
                fname = _norm(m_f.group(2)).lower()
                schemas[current][fname] = _algol_type(m_f.group(1))
    return schemas


def _parse_procedures(lines):
    """Procedimientos (pasos de proceso). ALGOL: PROCEDURE NOMBRE; o
    invocaciones de procedimiento. Capturamos las DEFINICIONES de procedure."""
    procs = []
    for line in lines:
        m = re.match(r"\s*(?:REAL|INTEGER|BOOLEAN|EBCDIC\s+)?PROCEDURE\s+([A-Za-z][\w-]*)", line, re.I)
        if m:
            procs.append(_norm(m.group(1)).lower())
    return procs


def _split_procs(lines):
    """Devuelve lista de (nombre_proc, [lineas_del_cuerpo]) para asociar logica
    (IF/joins/acumuladores) a cada procedimiento. Delimita por 'PROCEDURE'."""
    blocks = []
    current = None
    body = []
    for raw in lines:
        m = re.match(r"\s*(?:REAL|INTEGER|BOOLEAN|EBCDIC\s+)?PROCEDURE\s+([A-Za-z][\w-]*)", raw, re.I)
        if m:
            if current is not None:
                blocks.append((current, body))
            current = _norm(m.group(1)).lower()
            body = []
        elif current is not None:
            body.append(raw)
    if current is not None:
        blocks.append((current, body))
    return blocks


def _parse_filters(lines):
    """IF <cond> THEN -> clausula WHERE por procedimiento."""
    filters = {}
    for proc, body in _split_procs(lines):
        for line in body:
            if re.search(r"\bIF\b", line, re.I):
                cond = re.sub(r".*?\bIF\b", "", line, flags=re.I)
                cond = re.split(r"\bTHEN\b", cond, flags=re.I)[0].strip().rstrip(";")
                # Normalizar operadores ALGOL -> SQL-like.
                cond = cond.replace("NEQ", "!=").replace("GEQ", ">=").replace("LEQ", "<=")
                cond = cond.replace(" EQL ", " = ").replace(" GTR ", " > ").replace(" LSS ", " < ")
                cond = re.sub(r"\bAND\b", "AND", cond, flags=re.I)
                cond = re.sub(r"\bOR\b", "OR", cond, flags=re.I)
                cond = _norm_fields_in_cond(cond)
                # Solo guardar si NO es un join puro (campo = campo) -> eso va a joins.
                if cond and not re.fullmatch(r"[\w]+\s*=\s*[\w]+", cond):
                    filters.setdefault(proc, cond)
    return filters


def _norm_fields_in_cond(cond):
    # minusculas y guiones->underscore para identificadores.
    def repl(m):
        return m.group(0).replace("-", "_").lower()
    return re.sub(r"[A-Za-z][\w-]*", repl, cond)


def _parse_joins(lines):
    """IF campoA = campoB (dos identificadores) -> join key por procedimiento."""
    joins = {}
    for proc, body in _split_procs(lines):
        for line in body:
            m = re.search(r"\bIF\s+([A-Za-z][\w-]*)\s*(?:=|EQL)\s*([A-Za-z][\w-]*)", line, re.I)
            if m:
                left = _norm(m.group(1)).lower()
                right = _norm(m.group(2)).lower()
                if left != right:
                    joins.setdefault(proc, {"left": left, "right": right})
    return joins


def _parse_computes(lines):
    """Acumuladores: total := total + campo;  -> agregacion SUM(campo)."""
    computes = {}
    for proc, body in _split_procs(lines):
        for line in body:
            m = re.search(
                r"([A-Za-z][\w-]*)\s*:=\s*([A-Za-z][\w-]*)\s*\+\s*([A-Za-z][\w-]*)",
                line, re.I)
            if m:
                target = _norm(m.group(1)).lower()
                a, b = _norm(m.group(2)).lower(), _norm(m.group(3)).lower()
                # el sumando que NO es el propio acumulador es la fuente.
                source = b if a == target else a
                computes.setdefault(proc, {"type": "sum", "source": source, "target": target})
    return computes


def algol_to_graph(parsed):
    """Convierte el ALGOL parseado a strings .mp/.xfr/.dml (mismo formato que COBOL)."""
    files = parsed["files"]
    fields = parsed["fields"]
    procedures = parsed["procedures"]
    filters = parsed["filters"]
    joins = parsed["joins"]
    computes = parsed["computes"]

    # Clasificar archivos como entrada/salida.
    input_files, output_files = {}, {}
    for name in files:
        low = name.lower()
        kind = (files[name] or "").lower()
        is_out = ("printer" in kind or "report" in low or "error" in low
                  or "output" in low or "out" in low or "reject" in low
                  or "result" in low or "statement" in low)
        (output_files if is_out else input_files)[name] = files[name]
    # Si no se detecto ninguna salida, el ultimo archivo se trata como sink.
    if files and not output_files:
        last = list(files.keys())[-1]
        output_files[last] = files[last]
        input_files.pop(last, None)

    # --- .mp ---
    mp = ["# Auto-generated from ALGOL (Unisys)", ""]
    for f in input_files:
        mp.append(f"NODE Raw_{f} : SOURCE")
    mp.append("")
    mp.append("SUBGRAPH Ingestion {")
    for f in input_files:
        mp.append(f"  NODE Clean_{f} : TRANSFORM")
    mp.append("}")
    mp.append("")

    mp.append("SUBGRAPH Process {")
    proc_nodes = []
    for proc in procedures:
        if proc.startswith(("read_", "write_", "open_", "close_", "init_")):
            continue
        if proc in joins:
            mp.append(f"  NODE {proc} : JOIN")
            proc_nodes.append(proc)
        elif proc in filters or proc.startswith(("filter_", "valid", "check_")):
            mp.append(f"  NODE {proc} : TRANSFORM")
            proc_nodes.append(proc)
        elif proc in computes or proc.startswith(("compute_", "total", "sum_", "accum")):
            mp.append(f"  NODE {proc} : TRANSFORM")
            proc_nodes.append(proc)
    mp.append("}")
    mp.append("")

    for f in output_files:
        mp.append(f"NODE Write_{f} : SINK")
    mp.append("")

    for f in input_files:
        mp.append(f"Raw_{f} -> Clean_{f}")
    if proc_nodes:
        input_list = list(input_files.keys())
        for f in input_list:
            mp.append(f"Clean_{f} -> {proc_nodes[0]}")
        clean_idx = 0
        for i in range(len(proc_nodes) - 1):
            mp.append(f"{proc_nodes[i]} -> {proc_nodes[i+1]}")
            if proc_nodes[i+1] in joins and input_list:
                mp.append(f"Clean_{input_list[clean_idx]} -> {proc_nodes[i+1]}")
                clean_idx = (clean_idx + 1) % len(input_list)
        for f in output_files:
            mp.append(f"{proc_nodes[-1]} -> Write_{f}")
    else:
        # Sin procedimientos de proceso: conectar cleans directo a sinks.
        for f in input_files:
            for o in output_files:
                mp.append(f"Clean_{f} -> Write_{o}")

    # --- .xfr ---
    xfr = ["# Auto-generated from ALGOL (Unisys)", ""]
    for f in input_files:
        if f in fields and fields[f]:
            cols = ", ".join(fields[f].keys())
            xfr.append(f"Clean_{f}:")
            xfr.append(f"  select {cols}")
            xfr.append("")
    for proc in proc_nodes:
        if proc in joins:
            j = joins[proc]
            xfr.append(f"{proc}:")
            xfr.append(f"  join_key {j['left']}")
            xfr.append(f"  join_type inner")
            xfr.append("")
        elif proc in filters:
            xfr.append(f"{proc}:")
            xfr.append(f"  select *")
            xfr.append(f"  where {filters[proc]}")
            xfr.append("")
        elif proc in computes:
            c = computes[proc]
            xfr.append(f"{proc}:")
            xfr.append(f"  group_by {c['source']}")
            xfr.append(f"  select SUM({c['source']}) as {c['target']}")
            xfr.append("")

    # --- .dml ---
    dml = ["keys:"]
    for f in input_files:
        if f in fields and fields[f]:
            first_key = list(fields[f].keys())[0]
            dml.append(f"  Raw_{f}: {first_key}")
    dml.append("")
    dml.append("schema:")
    for f in input_files:
        if f in fields and fields[f]:
            dml.append(f"  Raw_{f}:")
            for col, typ in fields[f].items():
                dml.append(f"    {col}: {typ}")
            dml.append("")

    return {
        "mp": "\n".join(mp),
        "xfr": "\n".join(xfr),
        "dml": "\n".join(dml),
    }
