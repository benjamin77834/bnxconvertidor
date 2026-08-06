import re

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
    
    # Check if the entire file is a raw DML transform (no NodeName: headers)
    stripped_content = content.strip()
    if stripped_content.startswith("out") and "::" in stripped_content and "begin" in stripped_content.lower():
        # Entire file is a single raw DML — detect lookup pattern
        if "lookup_count" in stripped_content or "lookup_next" in stripped_content:
            lkp_match = re.search(r'lookup_count\("([^"]+)"', stripped_content)
            lookup_name = lkp_match.group(1).replace("-", "_").lower() if lkp_match else "lookup"
            return {"_raw_dml": {"transform": "lookup_join", "lookup_name": lookup_name, "raw_transform": stripped_content[:500]}}
        return {"_raw_dml": {"raw_transform": stripped_content}}

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