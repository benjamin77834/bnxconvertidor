# src/cobol_parser.py
"""
Parses COBOL source files and generates .mp, .xfr, .dml for BNX compiler.
Handles: FILE SECTION, WORKING-STORAGE, PROCEDURE DIVISION.
"""
import io
import re
import zipfile


# Extensiones que consideramos "codigo fuente" dentro de un ZIP, en orden de
# preferencia. Un .CBL exportado desde el mainframe/IDS suele venir realmente
# como un ZIP (firma 'PK\x03\x04') que empaqueta varios miembros; nos quedamos
# con el primero que parezca COBOL.
_SOURCE_EXTS = (".cbl", ".cob", ".cpy", ".alg", ".dma", ".mp", ".xfr", ".dml", ".txt")


def _looks_like_cobol(text):
    up = text.upper()
    return ("IDENTIFICATION DIVISION" in up or "PROCEDURE DIVISION" in up
            or "PROGRAM-ID" in up or "DATA DIVISION" in up)


def _text_score(text):
    """Puntua que tan 'legible' es un texto: ratio de caracteres imprimibles
    mas un bonus fuerte si contiene palabras clave COBOL. Sirve para elegir el
    codec correcto (p.ej. latin-1 vs cp500) cuando varios 'no lanzan'."""
    if not text:
        return -1.0
    sample = text[:20000]
    printable = sum(1 for c in sample if c == "\n" or c == "\t" or 32 <= ord(c) < 127)
    ratio = printable / len(sample)
    bonus = 0.0
    up = sample.upper()
    for kw in ("DIVISION", "SECTION", "PROGRAM-ID", "PIC ", "MOVE ", "$SET", "PERFORM"):
        if kw in up:
            bonus += 0.2
    return ratio + bonus


def _decode_bytes(raw):
    """Decodifica bytes a texto eligiendo el codec que produce el texto mas
    legible. No basta con 'el primero que no lance': cp500 decodifica cualquier
    byte pero puede devolver basura cuando el fuente ya estaba en ASCII/latin-1.
    """
    best_text = None
    best_score = -2.0
    for enc in ("utf-8", "latin-1", "cp500", "cp1140"):
        try:
            text = raw.decode(enc)
        except (UnicodeDecodeError, UnicodeError, LookupError):
            continue
        score = _text_score(text)
        if score > best_score:
            best_score, best_text = score, text
    if best_text is None:
        best_text = raw.decode("latin-1", errors="replace")
    return best_text


def extract_source_from_bytes(raw):
    """Devuelve el codigo fuente (texto) a partir de los bytes crudos subidos.

    Un .CBL del banco a menudo NO es texto: es un ZIP que empaqueta el COBOL
    real junto con otros miembros. Si detectamos la firma ZIP, extraemos el
    miembro que parezca codigo fuente; si no, decodificamos como texto.

    Nunca lanza por codificacion: usa latin-1 como ultimo recurso.
    """
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw

    # Firma de ZIP: 'PK\x03\x04'. Tambien aceptamos ZIP vacio ('PK\x05\x06').
    if raw[:2] == b"PK" and zipfile.is_zipfile(io.BytesIO(raw)):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                members = [n for n in zf.namelist() if not n.endswith("/")]
                decoded = []
                for name in members:
                    try:
                        text = _decode_bytes(zf.read(name))
                    except Exception:
                        continue
                    decoded.append((name, text))
                # 1) Preferir el miembro cuyo contenido parezca COBOL.
                for name, text in decoded:
                    if _looks_like_cobol(text):
                        return text
                # 2) Si no, el primero con extension de codigo fuente conocida.
                for name, text in decoded:
                    low = name.lower()
                    if any(low.endswith(ext) for ext in _SOURCE_EXTS):
                        return text
                # 3) Si no, el miembro mas grande (suele ser el fuente).
                if decoded:
                    return max(decoded, key=lambda nt: len(nt[1]))[1]
        except (zipfile.BadZipFile, OSError):
            pass  # cae al decode de texto normal

    return _decode_bytes(raw)


def parse_cobol(path):
    # Probar UTF-8 primero, luego EBCDIC (cp500/cp1140) y por ultimo latin-1
    # (que decodifica cualquier byte, es el fallback que nunca falla).
    # OJO: 'cp1047' NO es un codec de Python (daba LookupError -> 500). Los
    # codecs EBCDIC validos son cp500 y cp1140. Capturamos LookupError por si
    # algun codec no esta disponible en el entorno.
    content = None
    last = None
    for enc in ("utf-8", "cp500", "cp1140", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                data = f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
        except LookupError:
            # codec no registrado en este Python: saltarlo sin romper.
            continue
        last = data
        # Sanity check: un COBOL valido trae DIVISION o SECTION. Si lo cumple,
        # es la codificacion correcta; si no, seguimos probando pero guardamos
        # el ultimo decodificado como respaldo.
        if "DIVISION" in data.upper() or "SECTION" in data.upper():
            content = data
            break
    if content is None:
        content = last  # usar el ultimo decodificado (p.ej. latin-1)

    if not content:
        raise ValueError(f"Cannot decode COBOL file: {path}")

    lines = [l.rstrip() for l in content.splitlines()]

    files = _parse_file_section(lines)
    fields = _parse_fields(lines)
    procedures = _parse_procedures(lines)
    filters = _parse_filters(lines)
    joins = _parse_joins(lines, fields)
    computes = _parse_computes(lines)

    return {
        "files": files,
        "fields": fields,
        "procedures": procedures,
        "filters": filters,
        "joins": joins,
        "computes": computes,
        "encoding": "EBCDIC" if content and "COMP-3" in content.upper() else "ASCII",
    }


def _parse_file_section(lines):
    """Extract SELECT ... ASSIGN TO statements ? source/sink files."""
    files = {}
    for line in lines:
        # ASSIGN TO puede traer el destino entre comillas ('ARCHIVO') o como
        # literal/palabra reservada sin comillas (DISK, REMOTE, PRINTER...).
        m = re.match(
            r"\s*SELECT\s+([\w-]+)\s+ASSIGN\s+TO\s+'?([\w./-]+)'?",
            line, re.I,
        )
        if m:
            name = m.group(1).replace("-", "_")
            assign = m.group(2).strip().strip("'\"").rstrip(".")
            files[name] = assign
    return files


def _parse_fields(lines):
    """Extract FD + 05 level fields ? schema per file. Handles COMP-3, COMP, FILLER."""
    schemas = {}
    current_fd = None

    for line in lines:
        m_fd = re.match(r"\s+FD\s+([\w-]+)", line, re.I)
        if m_fd:
            current_fd = m_fd.group(1).replace("-", "_")
            schemas[current_fd] = {}
            continue

        if current_fd:
            # Skip FILLER fields
            if re.match(r"\s+05\s+FILLER\s+", line, re.I):
                continue

            # Match: 05 FIELD-NAME PIC ... [COMP-3|COMP].
            m_field = re.match(r"\s+05\s+([\w-]+)\s+PIC\s+(.+?)\.?\s*$", line, re.I)
            if m_field:
                fname = m_field.group(1).replace("-", "_").lower()
                pic = m_field.group(2).strip().rstrip(".")
                ftype = _pic_to_type(pic)
                schemas[current_fd][fname] = ftype
            elif re.match(r"\s+(FD|WORKING-STORAGE|PROCEDURE)", line, re.I):
                current_fd = None

    return schemas


def _pic_to_type(pic):
    """Convert COBOL PIC to simple type. Handles COMP-3 (packed), COMP (binary), REDEFINES."""
    pic = pic.upper().strip()

    # COMP-3 (packed decimal) ? always numeric
    if "COMP-3" in pic:
        if "V" in pic:
            return "decimal"  # packed decimal with decimals
        return "long"  # packed integer

    # COMP (binary)
    if "COMP" in pic:
        if "V" in pic:
            return "double"
        digits = len(re.findall(r"9", pic.split("COMP")[0]))
        return "int" if digits <= 9 else "long"

    # Standard PIC
    if "V" in pic and "9" in pic:
        return "double"
    if "S9" in pic or "9" in pic:
        digits = len(re.findall(r"9", pic))
        return "int" if digits <= 8 else "long"
    return "string"


def _parse_procedures(lines):
    """Extract PERFORM statements ? processing steps."""
    procs = []
    for line in lines:
        m = re.match(r"\s+PERFORM\s+([\w-]+)", line, re.I)
        if m:
            procs.append(m.group(1).replace("-", "_").lower())
    return procs


def _parse_filters(lines):
    """Extract IF conditions ? WHERE clauses."""
    filters = {}
    current_para = None

    for line in lines:
        m_para = re.match(r"\s{7}([\w-]+)\.", line)
        if m_para:
            current_para = m_para.group(1).replace("-", "_").lower()
            continue

        if current_para and "IF " in line.upper():
            cond = re.sub(r"^\s+IF\s+", "", line, flags=re.I).strip()
            cond = cond.replace("END-IF", "").replace(".", "").strip()
            # Convert COBOL operators
            cond = cond.replace(" = ", " = ").replace(" > ", " > ").replace(" < ", " < ")
            cond = re.sub(r"\bAND\b", "AND", cond, flags=re.I)
            cond = re.sub(r"\bOR\b", "OR", cond, flags=re.I)
            if cond:
                filters[current_para] = cond

    return filters


def _parse_joins(lines, fields=None):
    """Detecta JOINS REALES: un parrafo une dos FICHEROS distintos.

    OJO: un COBOL procedural compara campos todo el tiempo (`IF A = B`) sin que
    eso sea un join. Marcar cada `IF a = b` como JOIN producia nodos JOIN sin
    llave valida (-> TODOs en el PySpark). Aqui exigimos evidencia real de join:

      1) el parrafo se llama 'join_*' / contiene 'match'/'merge', O
      2) el `IF a = b` compara un campo de un FICHERO con un campo de OTRO
         fichero distinto (segun los schemas FD), lo que si implica unir dos
         streams.

    'fields' es {fichero: {campo: tipo}} (de _parse_fields) para resolver a que
    fichero pertenece cada campo. Si no se provee, solo valen los join_* por
    nombre.
    """
    fields = fields or {}

    # Indice campo_normalizado -> fichero. Un campo puede repetirse; guardamos
    # el conjunto de ficheros que lo declaran.
    field_owner = {}
    for fname, cols in fields.items():
        for col in cols:
            field_owner.setdefault(col.lower(), set()).add(fname)

    def _owners(col):
        return field_owner.get(col.lower(), set())

    joins = {}
    current_para = None

    for line in lines:
        m_para = re.match(r"\s{7}([\w-]+)\.", line)
        if m_para:
            current_para = m_para.group(1).replace("-", "_").lower()
            continue
        if not current_para:
            continue

        name_is_join = (current_para.startswith("join_")
                        or "match" in current_para or "merge" in current_para)

        if "IF " in line.upper():
            m = re.search(r"IF\s+([\w-]+)\s*=\s*([\w-]+)", line, re.I)
            if m:
                left = m.group(1).replace("-", "_").lower()
                right = m.group(2).replace("-", "_").lower()
                if left == right:
                    continue
                # Join real si: nombre lo indica, O los campos vienen de dos
                # ficheros DISTINTOS (evidencia de que se unen dos streams).
                lo, ro = _owners(left), _owners(right)
                cross_file = bool(lo and ro and (lo != ro or len(lo | ro) > 1))
                if name_is_join or cross_file:
                    joins[current_para] = {"left": left, "right": right}

    return joins


def _parse_computes(lines):
    """Extrae logica aritmetica por parrafo.

    - 'ADD x TO y' (sin GIVING, y acumula) -> agregacion SUM(x) (como antes).
    - Aritmetica avanzada -> expresiones de columna (withColumn), que capturamos
      en 'arith' por parrafo (lista de (target, expr_sql)):
        COMPUTE z = (a + b) * c - d / e
        ADD a b TO c GIVING z
        SUBTRACT a FROM b GIVING z
        MULTIPLY a BY b GIVING z
        DIVIDE a INTO b GIVING z   /  DIVIDE a BY b GIVING z
    Devuelve {parrafo: {...sum...}} y adjunta ['arith'] = [(target, expr)]."""
    computes = {}
    arith = {}
    current_para = None

    for line in lines:
        m_para = re.match(r"\s{7}([\w-]+)\.", line)
        if m_para:
            current_para = m_para.group(1).replace("-", "_").lower()
            continue
        if not current_para:
            continue

        expr = _cobol_arith_expr(line)
        if expr:
            arith.setdefault(current_para, []).append(expr)
            continue

        # ADD x TO y (acumulador puro) -> SUM. Solo si no es un ADD ... GIVING.
        m_add = re.match(r"\s+ADD\s+([\w-]+)\s+TO\s+([\w-]+)\s*\.?\s*$", line, re.I)
        if m_add:
            src = m_add.group(1).replace("-", "_").lower()
            dst = m_add.group(2).replace("-", "_").lower()
            computes[current_para] = {"type": "sum", "source": src, "target": dst}

    # Adjuntar la aritmetica avanzada a la estructura devuelta.
    for para, exprs in arith.items():
        computes.setdefault(para, {})
        computes[para]["arith"] = exprs
    return computes


def _f(name):
    return name.replace("-", "_").lower()


def _cobol_arith_expr(line):
    """Si la linea es una operacion aritmetica COBOL, devuelve (target, expr_sql).
    expr_sql usa nombres de columna (lower, '-'->'_'). None si no aplica."""
    s = line.strip().rstrip(".")

    # COMPUTE z = <expr>
    m = re.match(r"COMPUTE\s+([\w-]+)\s*=\s*(.+)$", s, re.I)
    if m:
        target = _f(m.group(1))
        expr = _norm_arith(m.group(2))
        return (target, expr)

    # ADD a [b c ...] TO d GIVING z   -> z = a + b + ... + d
    m = re.match(r"ADD\s+(.+?)\s+TO\s+([\w-]+)\s+GIVING\s+([\w-]+)$", s, re.I)
    if m:
        terms = [_f(t) for t in re.split(r"\s+", m.group(1).strip())]
        terms.append(_f(m.group(2)))
        return (_f(m.group(3)), " + ".join(terms))

    # ADD a b ... GIVING z   -> z = a + b + ...
    m = re.match(r"ADD\s+(.+?)\s+GIVING\s+([\w-]+)$", s, re.I)
    if m:
        terms = [_f(t) for t in re.split(r"\s+", m.group(1).strip())]
        return (_f(m.group(2)), " + ".join(terms))

    # SUBTRACT a [b ...] FROM c GIVING z  -> z = c - a - b - ...
    m = re.match(r"SUBTRACT\s+(.+?)\s+FROM\s+([\w-]+)\s+GIVING\s+([\w-]+)$", s, re.I)
    if m:
        subs = [_f(t) for t in re.split(r"\s+", m.group(1).strip())]
        base = _f(m.group(2))
        return (_f(m.group(3)), base + "".join(f" - {t}" for t in subs))

    # MULTIPLY a BY b GIVING z  -> z = a * b
    m = re.match(r"MULTIPLY\s+([\w-]+)\s+BY\s+([\w-]+)\s+GIVING\s+([\w-]+)$", s, re.I)
    if m:
        return (_f(m.group(3)), f"{_f(m.group(1))} * {_f(m.group(2))}")

    # DIVIDE a INTO b GIVING z  -> z = b / a ;  DIVIDE a BY b GIVING z -> z = a / b
    m = re.match(r"DIVIDE\s+([\w-]+)\s+INTO\s+([\w-]+)\s+GIVING\s+([\w-]+)$", s, re.I)
    if m:
        return (_f(m.group(3)), f"{_f(m.group(2))} / {_f(m.group(1))}")
    m = re.match(r"DIVIDE\s+([\w-]+)\s+BY\s+([\w-]+)\s+GIVING\s+([\w-]+)$", s, re.I)
    if m:
        return (_f(m.group(3)), f"{_f(m.group(1))} / {_f(m.group(2))}")

    return None


def _norm_arith(expr):
    """Normaliza una expresion aritmetica a nombres de columna SQL-friendly:
    identificadores a lower/'-'->'_'; conserva operadores + - * / ( ) y numeros.
    COBOL usa ** para potencia -> SQL usa power(), pero lo dejamos como * * raro;
    aqui mapeamos ** a 'power' solo si aparece de forma simple."""
    # Reemplazar identificadores (letras/digitos/guion) por su forma de columna.
    def repl(m):
        tok = m.group(0)
        if re.fullmatch(r"\d+(\.\d+)?", tok):
            return tok  # numero
        return tok.replace("-", "_").lower()
    out = re.sub(r"[A-Za-z0-9_][\w-]*", repl, expr)
    return out.strip()


def cobol_to_graph(parsed):
    """Convert parsed COBOL to .mp, .xfr, .dml content strings."""
    files = parsed["files"]
    fields = parsed["fields"]
    procedures = list(parsed["procedures"])
    filters = parsed["filters"]
    joins = parsed["joins"]
    computes = parsed["computes"]

    # Incluir tambien los parrafos QUE TIENEN LOGICA aunque no se invoquen por
    # PERFORM (COBOL batch suele ejecutar parrafos en secuencia). Asi no se
    # pierden filtros/joins/aritmetica cuando no hay PERFORM explicito.
    for extra in list(filters.keys()) + list(joins.keys()) + list(computes.keys()):
        if extra not in procedures:
            procedures.append(extra)

    # Classify files as input/output
    input_files = {}
    output_files = {}
    for line in files:
        name_lower = line.lower()
        if "report" in name_lower or "error" in name_lower or "output" in name_lower or "reject" in name_lower or "statement" in name_lower or "fraud" in name_lower or "balance" in name_lower:
            output_files[line] = files[line]
        else:
            input_files[line] = files[line]

    # Build .mp
    mp_lines = ["# Auto-generated from COBOL", ""]

    # Sources
    for f in input_files:
        mp_lines.append(f"NODE Raw_{f} : SOURCE")

    mp_lines.append("")

    # Ingestion subgraph
    mp_lines.append("SUBGRAPH Ingestion {")
    for f in input_files:
        mp_lines.append(f"  NODE Clean_{f} : TRANSFORM")
    mp_lines.append("}")
    mp_lines.append("")

    # Process subgraph from procedures
    mp_lines.append("SUBGRAPH Process {")
    proc_nodes = []
    for proc in procedures:
        # Parrafos de E/S (abrir/leer/cerrar fichero) no son pasos de datos.
        if proc.startswith(("read_", "write_", "open_", "close_")):
            continue
        if proc in joins or proc.startswith("join_"):
            # JOIN SOLO cuando _parse_joins confirmo union de dos ficheros (o el
            # nombre lo indica). Asi no quedan JOINs sin llave que el codegen
            # convierte en TODOs.
            mp_lines.append(f"  NODE {proc} : JOIN")
            proc_nodes.append(proc)
        elif (proc in filters or proc in computes
              or proc.startswith(("filter_", "compute_", "detect_", "valid",
                                   "calc_", "sum_", "agg_", "transform_"))):
            # Parrafos con LOGICA DE DATOS reconocida (filtro, aritmetica,
            # validacion) -> TRANSFORM. No incluimos cada parrafo PERFORM
            # trivial (MOVE/GO TO) como nodo: un COBOL grande tiene miles y
            # saturan el grafo sin aportar transformacion.
            mp_lines.append(f"  NODE {proc} : TRANSFORM")
            proc_nodes.append(proc)
    mp_lines.append("}")
    mp_lines.append("")

    # Sinks
    for f in output_files:
        mp_lines.append(f"NODE Write_{f} : SINK")
    mp_lines.append("")

    # Edges: source -> clean
    for f in input_files:
        mp_lines.append(f"Raw_{f} -> Clean_{f}")

    # Edges: clean -> process nodes
    if proc_nodes:
        # All cleans feed into the first process node
        # For JOINs, also connect the previous node
        input_list = list(input_files.keys())
        for f in input_list:
            mp_lines.append(f"Clean_{f} -> {proc_nodes[0]}")

        # Chain process nodes -> los JOINs reciben 2 padres (prev + un clean)
        clean_idx = 0
        for i in range(len(proc_nodes) - 1):
            mp_lines.append(f"{proc_nodes[i]} -> {proc_nodes[i+1]}")
            nxt = proc_nodes[i+1]
            # Si el siguiente es un JOIN REAL (en 'joins' o nombre join_*), dale
            # un segundo padre desde una fuente limpia para que haya dos streams.
            is_join = nxt in joins or nxt.startswith("join_")
            if is_join and clean_idx < len(input_list):
                mp_lines.append(f"Clean_{input_list[clean_idx]} -> {nxt}")
                clean_idx = (clean_idx + 1) % len(input_list)

        # Last process -> sinks
        for f in output_files:
            mp_lines.append(f"{proc_nodes[-1]} -> Write_{f}")

    # Build .xfr
    xfr_lines = ["# Auto-generated from COBOL", ""]

    for f in input_files:
        if f in fields:
            cols = ", ".join(fields[f].keys())
            xfr_lines.append(f"Clean_{f}:")
            xfr_lines.append(f"  select {cols}")
            xfr_lines.append("")

    for proc in proc_nodes:
        if proc in filters:
            xfr_lines.append(f"{proc}:")
            xfr_lines.append(f"  select *")
            xfr_lines.append(f"  where {filters[proc]}")
            xfr_lines.append("")
        elif proc in joins:
            j = joins[proc]
            xfr_lines.append(f"{proc}:")
            xfr_lines.append(f"  join_key {j['left']}")
            xfr_lines.append(f"  join_type inner")
            xfr_lines.append("")
        elif proc in computes:
            c = computes[proc]
            xfr_lines.append(f"{proc}:")
            if c.get("arith"):
                # Aritmetica avanzada -> columnas calculadas (select con alias).
                # El codegen de Spark emite withColumn(target, expr(...)) por item.
                items = ["*"] + [f"{expr} as {target}" for (target, expr) in c["arith"]]
                xfr_lines.append(f"  select {', '.join(items)}")
            elif "source" in c and "target" in c:
                xfr_lines.append(f"  group_by {c['source']}")
                xfr_lines.append(f"  select SUM({c['source']}) as {c['target']}")
            xfr_lines.append("")
        elif proc.startswith("detect_") and proc in filters:
            xfr_lines.append(f"{proc}:")
            xfr_lines.append(f"  select *")
            xfr_lines.append(f"  where {filters[proc]}")
            xfr_lines.append("")
        else:
            # Parrafo procedural sin filtro/aritmetica/join reconocido: paso de
            # paso-a-traves explicito (select *). Deja el nodo valido y evita
            # que el codegen lo marque como incompleto.
            xfr_lines.append(f"{proc}:")
            xfr_lines.append(f"  select *")
            xfr_lines.append("")

    # Build .dml
    dml_lines = ["keys:"]
    for f in input_files:
        if f in fields and fields[f]:
            first_key = list(fields[f].keys())[0]
            dml_lines.append(f"  Raw_{f}: {first_key}")

    dml_lines.append("")
    dml_lines.append("schema:")
    for f in input_files:
        if f in fields and fields[f]:
            dml_lines.append(f"  Raw_{f}:")
            for col, typ in fields[f].items():
                dml_lines.append(f"    {col}: {typ}")
            dml_lines.append("")

    return {
        "mp": "\n".join(mp_lines),
        "xfr": "\n".join(xfr_lines),
        "dml": "\n".join(dml_lines),
    }
