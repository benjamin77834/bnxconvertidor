import re


def _extract_constants(content):
    """Extract constant declarations from Ab Initio XFR header.
    
    Pattern: constant string('value') NAME parameter = 'default';
             constant integer(0) NAME parameter = 0;
    
    Returns dict: {NAME: value_string}
    """
    constants = {}
    for m in re.finditer(r"constant\s+\w+\('([^']*)'\)\s+(\w+)", content):
        constants[m.group(2)] = m.group(1)
    for m in re.finditer(r"constant\s+\w+\((\d+)\)\s+(\w+)", content):
        constants[m.group(2)] = m.group(1)
    return constants


def _parse_dml_fields(dml_content, constants=None):
    """Parse Ab Initio DML field assignments into Spark-compatible expressions.
    
    Handles:
    - out.FIELD :: in.V_FIELD  (rename)
    - out.FIELD :: string_pad(string_substring(in.X, 1, 12), 12)  (string ops)
    - out.FIELD :: (if (is_blank(...)) NULL else re_replace(...))  (conditional trim)
    - out.FIELD :: string_lrtrim('VALUE')  (literal)
    - out.FIELD :: (datetime(...))now1()  (current_timestamp)
    - out.FIELD :: in.D_FIELD  (date passthrough)
    - out.FIELD :0: expr  (with default 0)
    - out.* :: in.*  (passthrough all)
    - out.FIELD :: CONSTANT_NAME  (resolved from constants dict)
    """
    constants = constants or {}
    fields = []
    
    # Extract field assignments: out.FIELD :: expression;
    # Handle multi-line expressions by joining everything first
    flat = dml_content.replace('\n', ' ')
    
    # Find all out.FIELD :: EXPR patterns (terminated by ;)
    assignments = re.findall(r'out\.(\w+)\s*:(?:\d+)?:\s*(.+?)(?:;|$)', flat)
    
    for field_name, raw_expr in assignments:
        expr = raw_expr.strip().rstrip(';').strip()
        
        # Skip passthrough (out.* :: in.*)
        if field_name == '*':
            continue
        
        # Simple passthrough: in.FIELD or in.V_FIELD
        if re.match(r'^in\.\w+$', expr):
            src = expr.replace('in.', '')
            if src.lower() != field_name.lower():
                fields.append({"field": field_name, "expr": f'col("{src}").alias("{field_name}")', "type": "rename"})
            continue
        
        # Literal string: string_lrtrim('VALUE') or just 'VALUE'
        lit_match = re.match(r"^string_lrtrim\(\s*'([^']+)'\s*\)$", expr)
        if lit_match:
            fields.append({"field": field_name, "expr": f'lit("{lit_match.group(1)}")', "type": "literal"})
            continue
        
        # Direct string literal
        lit_match2 = re.match(r"^'([^']*)'$", expr)
        if lit_match2:
            fields.append({"field": field_name, "expr": f'lit("{lit_match2.group(1)}")', "type": "literal"})
            continue
        
        # NULL
        if expr == 'NULL':
            fields.append({"field": field_name, "expr": 'lit(None)', "type": "literal"})
            continue
        
        # Constant reference: just an identifier that matches a declared constant
        if constants and expr in constants:
            val = constants[expr]
            if val == '':
                fields.append({"field": field_name, "expr": 'lit("")', "type": "literal"})
            else:
                fields.append({"field": field_name, "expr": f'lit("{val}")', "type": "literal"})
            continue
        
        # Numeric literal or zero default
        if re.match(r'^-?\d+(\.\d+)?$', expr):
            fields.append({"field": field_name, "expr": f'lit({expr})', "type": "literal"})
            continue
        
        # now1() → current_timestamp
        if 'now1()' in expr:
            fields.append({"field": field_name, "expr": 'current_timestamp()', "type": "function"})
            continue
        
        # string_pad / string_substring pattern
        if 'string_pad' in expr or 'string_substring' in expr:
            # Map to lpad/rpad/substring
            spark_expr = _map_string_ops(expr)
            fields.append({"field": field_name, "expr": spark_expr, "type": "string_op"})
            continue
        
        # is_blank pattern with re_replace (conditional trim)
        if 'is_blank' in expr and 're_replace' in expr:
            # This is: if is_blank(trim(field)) then NULL else trim(field)
            # Extract the source field
            src_match = re.search(r'in\.(\w+)', expr)
            if src_match:
                src_field = src_match.group(1)
                spark_expr = f'when(trim(col("{src_field}")) == "", lit(None)).otherwise(trim(col("{src_field}")))'
                fields.append({"field": field_name, "expr": spark_expr, "type": "conditional_trim"})
                continue
        
        # first_defined pattern with numeric default
        if 'first_defined' in expr and 'else 0' in expr:
            src_match = re.search(r'in\.(\w+)', expr)
            if src_match:
                src_field = src_match.group(1)
                spark_expr = f'coalesce(col("{src_field}"), lit(0))'
                fields.append({"field": field_name, "expr": spark_expr, "type": "coalesce"})
                continue
        
        # Generic: just store the raw expression as comment
        src_match = re.search(r'in\.(\w+)', expr)
        if src_match:
            src_field = src_match.group(1)
            fields.append({"field": field_name, "expr": f'col("{src_field}")', "type": "passthrough", "comment": expr[:80]})
        else:
            fields.append({"field": field_name, "expr": f'lit(None)  # TODO: {expr[:60]}', "type": "todo"})
    
    return fields


def _map_string_ops(expr):
    """Map Ab Initio string operations to Spark expressions."""
    # string_pad(string_substring(in.X, 1, 12), 12) → lpad(substring(col("X"), 1, 12), 12, " ")
    # string_substring(in.X, 1, N) → substring(col("X"), 1, N)
    
    # Extract inner field reference
    src_match = re.search(r'in\.(\w+)', expr)
    src_field = src_match.group(1) if src_match else "unknown"
    
    # Check for string_substring
    sub_match = re.search(r'string_substring\s*\([^,]+,\s*(\d+),\s*(\d+)\)', expr)
    start = sub_match.group(1) if sub_match else "1"
    length = sub_match.group(2) if sub_match else "255"
    
    # Check for string_pad (lpad) — allow flexible spacing
    pad_match = re.search(r'string_pad\s*\(.+?,\s*(\d+)\s*\)', expr)
    if pad_match:
        pad_len = pad_match.group(1)
        return f'lpad(substring(col("{src_field}"), {start}, {length}), {pad_len}, " ")'
    
    return f'substring(col("{src_field}"), {start}, {length})'

def parse_xfr(path):
    """
    Parsea archivos .xfr con formato:
        NodeName:
          select col1, col2, ...
          where condition
    
    También soporta DML nativo de Ab Initio (out :: reformat(in) = begin...end;)
    Retorna dict: { "nodename": { "select": "...", "where": "..." } }
    """
    xfr_map = {}
    current = None
    raw_dml_buffer = []
    in_raw_dml = False

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if the file contains multiple concatenated .xfr files (from Grafos)
    stripped_content = content.strip()
    if '# ===' in stripped_content:
        # Multiple .xfr files concatenated — parse each one separately
        parsed_xfrs = []
        sections = stripped_content.split('# ===')
        for section in sections:
            if not section.strip():
                continue
            # Extract filename from header
            lines = section.split('\n')
            header = lines[0].strip().rstrip('=').strip() if lines else ''
            body = '\n'.join(lines[1:]) if lines else ''
            # Extract constants before cleaning
            constants = _extract_constants(body)
            # Clean and parse
            clean = []
            for ln in body.split('\n'):
                l = ln.strip()
                if l.startswith('include ') or l.startswith('//') or l.startswith('constant '):
                    continue
                clean.append(l)
            clean_body = '\n'.join(clean).strip()
            if clean_body.startswith("out") and "::" in clean_body:
                fields = _parse_dml_fields(clean_body, constants)
                if fields:
                    parsed_xfrs.append({"name": header, "dml_fields": fields})
        if parsed_xfrs:
            return {"_multi_xfr": parsed_xfrs}
    
    # Check if the entire file is a raw DML transform (no NodeName: headers)
    # Remove include lines and comments
    constants = _extract_constants(stripped_content)
    clean_lines = []
    for line in stripped_content.split('\n'):
        ln = line.strip()
        if ln.startswith('include ') or ln.startswith('//') or ln.startswith('constant '):
            continue
        clean_lines.append(ln)
    clean_content = '\n'.join(clean_lines).strip()
    
    if clean_content.startswith("out") and "::" in clean_content and ("begin" in clean_content.lower() or "end;" in clean_content):
        # Entire file is a single raw DML — parse field assignments
        if "lookup_count" in clean_content or "lookup_next" in clean_content:
            lkp_match = re.search(r'lookup_count\("([^"]+)"', clean_content)
            lookup_name = lkp_match.group(1).replace("-", "_").lower() if lkp_match else "lookup"
            return {"_raw_dml": {"transform": "lookup_join", "lookup_name": lookup_name, "raw_transform": clean_content[:500]}}
        
        # Parse field assignments from DML
        fields = _parse_dml_fields(clean_content, constants)
        if fields:
            return {"_raw_dml": {"dml_fields": fields, "raw_transform": clean_content[:300]}}
        return {"_raw_dml": {"raw_transform": clean_content[:500]}}

    for line in content.split("\n"):
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            if in_raw_dml:
                raw_dml_buffer.append(line)
            continue

        # Detecta cabecera de nodo: "NodeName:"
        if re.match(r"^\w+\s*:$", stripped):
            # Save previous raw DML if any
            if current and in_raw_dml and raw_dml_buffer:
                raw_text = "\n".join(raw_dml_buffer).strip()
                if "lookup_count" in raw_text or "lookup_next" in raw_text:
                    lkp_match = re.search(r'lookup_count\("([^"]+)"', raw_text)
                    lookup_name = lkp_match.group(1).replace("-", "_").lower() if lkp_match else "lookup"
                    xfr_map[current] = {"transform": "lookup_join", "lookup_name": lookup_name, "raw_transform": raw_text[:500]}
                else:
                    xfr_map[current] = {"raw_transform": raw_text}
            
            current = stripped.rstrip(":").strip().lower()
            xfr_map[current] = {"select": "*", "where": None}
            raw_dml_buffer = []
            in_raw_dml = False
            continue

        if current is None:
            continue

        # Detect start of raw DML (Ab Initio native format)
        if stripped.startswith("out") and "::" in stripped and ("reformat" in stripped or "rollup" in stripped):
            in_raw_dml = True
            raw_dml_buffer = [line]
            continue
        
        if in_raw_dml:
            raw_dml_buffer.append(line)
            # Check if DML block ended
            if stripped.endswith("end;") or stripped == "end;":
                raw_text = "\n".join(raw_dml_buffer).strip()
                if "lookup_count" in raw_text or "lookup_next" in raw_text:
                    lkp_match = re.search(r'lookup_count\("([^"]+)"', raw_text)
                    lookup_name = lkp_match.group(1).replace("-", "_").lower() if lkp_match else "lookup"
                    xfr_map[current] = {"transform": "lookup_join", "lookup_name": lookup_name, "raw_transform": raw_text[:500]}
                else:
                    xfr_map[current] = {"raw_transform": raw_text}
                in_raw_dml = False
                raw_dml_buffer = []
            continue
            if m_select:
                xfr_map[current]["select"] = m_select.group(1).strip()
                continue

            m_where = re.match(r"(?i)^where\s+(.+)$", stripped)
            if m_where:
                xfr_map[current]["where"] = m_where.group(1).strip()
                continue

            m_group = re.match(r"(?i)^group_by\s+(.+)$", stripped)
            if m_group:
                xfr_map[current]["group_by"] = [c.strip() for c in m_group.group(1).split(",")]
                continue

            m_jkey = re.match(r"(?i)^join_key\s+(.+)$", stripped)
            if m_jkey:
                xfr_map[current]["join_key"] = m_jkey.group(1).strip()
                continue

            m_jtype = re.match(r"(?i)^join_type\s+(.+)$", stripped)
            if m_jtype:
                xfr_map[current]["join_type"] = m_jtype.group(1).strip()
                continue

            # DEDUP directives
            m_dedup = re.match(r"(?i)^dedup_keys\s+(.+)$", stripped)
            if m_dedup:
                xfr_map[current]["dedup_keys"] = [c.strip() for c in m_dedup.group(1).split(",")]
                continue

            m_order = re.match(r"(?i)^order_by\s+(.+)$", stripped)
            if m_order:
                xfr_map[current]["order_by"] = m_order.group(1).strip()
                continue

            # NORMALIZE directives
            m_explode = re.match(r"(?i)^explode_col\s+(.+)$", stripped)
            if m_explode:
                xfr_map[current]["explode_col"] = m_explode.group(1).strip()
                continue

            m_split = re.match(r"(?i)^split_col\s+(.+)$", stripped)
            if m_split:
                xfr_map[current]["split_col"] = m_split.group(1).strip()
                continue

            m_delim = re.match(r"(?i)^delimiter\s+(.+)$", stripped)
            if m_delim:
                xfr_map[current]["delimiter"] = m_delim.group(1).strip()
                continue

            # LOOKUP directives
            m_lkey = re.match(r"(?i)^lookup_key\s+(.+)$", stripped)
            if m_lkey:
                xfr_map[current]["lookup_key"] = m_lkey.group(1).strip()
                continue

            m_lsel = re.match(r"(?i)^lookup_select\s+(.+)$", stripped)
            if m_lsel:
                xfr_map[current]["lookup_select"] = m_lsel.group(1).strip()
                continue

            # SOURCE/SINK directives
            for directive in ["source_type", "sink_type", "path", "format", "topic", "table", "connection", "mode", "partition_keys", "num_partitions", "partition_filter", "scan_year", "scan_month", "window_size"]:
                m = re.match(rf"(?i)^{directive}\s+(.+)$", stripped)
                if m:
                    xfr_map[current][directive] = m.group(1).strip()
                    break

    return xfr_map