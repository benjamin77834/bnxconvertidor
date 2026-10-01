# src/cobol_parser.py
"""
Parses COBOL source files and generates .mp, .xfr, .dml for BNX compiler.
Handles: FILE SECTION, WORKING-STORAGE, PROCEDURE DIVISION.
"""
import re


def parse_cobol(path):
    # Try UTF-8 first, then EBCDIC (cp500/cp1047)
    content = None
    for enc in ["utf-8", "cp500", "cp1047", "latin-1"]:
        try:
            with open(path, "r", encoding=enc) as f:
                content = f.read()
            # Sanity check: COBOL should have DIVISION or SECTION
            if "DIVISION" in content.upper() or "SECTION" in content.upper():
                break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if not content:
        raise ValueError(f"Cannot decode COBOL file: {path}")

    lines = [l.rstrip() for l in content.splitlines()]

    files = _parse_file_section(lines)
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
        "encoding": "EBCDIC" if content and "COMP-3" in content.upper() else "ASCII",
    }


def _parse_file_section(lines):
    """Extract SELECT ... ASSIGN TO statements ? source/sink files."""
    files = {}
    for line in lines:
        m = re.match(r"\s+SELECT\s+([\w-]+)\s+ASSIGN\s+TO\s+'(\w+)'", line, re.I)
        if m:
            name = m.group(1).replace("-", "_")
            assign = m.group(2)
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


def _parse_joins(lines):
    """Extract IF field = field patterns ? join keys."""
    joins = {}
    current_para = None

    for line in lines:
        m_para = re.match(r"\s{7}([\w-]+)\.", line)
        if m_para:
            current_para = m_para.group(1).replace("-", "_").lower()
            continue

        if current_para and "IF " in line.upper():
            m = re.search(r"IF\s+([\w-]+)\s*=\s*([\w-]+)", line, re.I)
            if m:
                left = m.group(1).replace("-", "_").lower()
                right = m.group(2).replace("-", "_").lower()
                if left != right:
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
        if proc.startswith("read_") or proc.startswith("write_") or proc.startswith(("open_", "close_")):
            continue
        if proc in joins or proc.startswith("join_"):
            mp_lines.append(f"  NODE {proc} : JOIN")
            proc_nodes.append(proc)
        elif (proc in filters or proc in computes
              or proc.startswith(("filter_", "compute_", "detect_", "valid"))):
            # filtros, aritmetica (compute/arith) y validaciones -> TRANSFORM.
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

        # Chain process nodes ? JOINs get 2 parents (prev + a clean source)
        clean_idx = 0
        for i in range(len(proc_nodes) - 1):
            mp_lines.append(f"{proc_nodes[i]} -> {proc_nodes[i+1]}")
            # If next is a JOIN, give it a second parent from a clean source
            if proc_nodes[i+1].startswith("join_") and clean_idx < len(input_list):
                mp_lines.append(f"Clean_{input_list[clean_idx]} -> {proc_nodes[i+1]}")
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
