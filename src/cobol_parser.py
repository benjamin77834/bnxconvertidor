# src/cobol_parser.py
"""
Parses COBOL source files and generates .mp, .xfr, .dml for BNX compiler.
Handles: FILE SECTION, WORKING-STORAGE, PROCEDURE DIVISION.
"""
import re


def parse_cobol(path):
    with open(path, "r") as f:
        lines = [l.rstrip() for l in f.readlines()]

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
    }


def _parse_file_section(lines):
    """Extract SELECT ... ASSIGN TO statements → source/sink files."""
    files = {}
    for line in lines:
        m = re.match(r"\s+SELECT\s+([\w-]+)\s+ASSIGN\s+TO\s+'(\w+)'", line, re.I)
        if m:
            name = m.group(1).replace("-", "_")
            assign = m.group(2)
            files[name] = assign
    return files


def _parse_fields(lines):
    """Extract FD + 05 level fields → schema per file."""
    schemas = {}
    current_fd = None

    for line in lines:
        m_fd = re.match(r"\s+FD\s+([\w-]+)", line, re.I)
        if m_fd:
            current_fd = m_fd.group(1).replace("-", "_")
            schemas[current_fd] = {}
            continue

        if current_fd:
            m_field = re.match(r"\s+05\s+([\w-]+)\s+PIC\s+(.+)\.", line, re.I)
            if m_field:
                fname = m_field.group(1).replace("-", "_").lower()
                pic = m_field.group(2).strip()
                ftype = _pic_to_type(pic)
                schemas[current_fd][fname] = ftype
            elif re.match(r"\s+(FD|WORKING-STORAGE|PROCEDURE)", line, re.I):
                current_fd = None

    return schemas


def _pic_to_type(pic):
    """Convert COBOL PIC to simple type."""
    pic = pic.upper()
    if "V" in pic or "9" in pic and "V" in pic:
        return "double"
    if "S9" in pic or "9" in pic:
        return "int" if len(re.findall(r"9", pic)) <= 8 else "double"
    return "string"


def _parse_procedures(lines):
    """Extract PERFORM statements → processing steps."""
    procs = []
    for line in lines:
        m = re.match(r"\s+PERFORM\s+([\w-]+)", line, re.I)
        if m:
            procs.append(m.group(1).replace("-", "_").lower())
    return procs


def _parse_filters(lines):
    """Extract IF conditions → WHERE clauses."""
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
    """Extract IF field = field patterns → join keys."""
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
    """Extract ADD/COMPUTE statements → aggregation logic."""
    computes = {}
    current_para = None

    for line in lines:
        m_para = re.match(r"\s{7}([\w-]+)\.", line)
        if m_para:
            current_para = m_para.group(1).replace("-", "_").lower()
            continue

        if current_para:
            m_add = re.match(r"\s+ADD\s+([\w-]+)\s+TO\s+([\w-]+)", line, re.I)
            if m_add:
                src = m_add.group(1).replace("-", "_").lower()
                dst = m_add.group(2).replace("-", "_").lower()
                computes[current_para] = {"type": "sum", "source": src, "target": dst}

    return computes


def cobol_to_graph(parsed):
    """Convert parsed COBOL to .mp, .xfr, .dml content strings."""
    files = parsed["files"]
    fields = parsed["fields"]
    procedures = parsed["procedures"]
    filters = parsed["filters"]
    joins = parsed["joins"]
    computes = parsed["computes"]

    # Classify files as input/output
    input_files = {}
    output_files = {}
    for line in files:
        name_lower = line.lower()
        if "report" in name_lower or "error" in name_lower or "output" in name_lower:
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
        if proc.startswith("read_"):
            continue
        if proc.startswith("write_"):
            continue
        if proc.startswith("filter_"):
            mp_lines.append(f"  NODE {proc} : TRANSFORM")
            proc_nodes.append(proc)
        elif proc.startswith("join_"):
            mp_lines.append(f"  NODE {proc} : JOIN")
            proc_nodes.append(proc)
        elif proc.startswith("compute_"):
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

    # Edges: clean -> first process node
    if proc_nodes:
        for f in input_files:
            mp_lines.append(f"Clean_{f} -> {proc_nodes[0]}")

        # Chain process nodes
        for i in range(len(proc_nodes) - 1):
            mp_lines.append(f"{proc_nodes[i]} -> {proc_nodes[i+1]}")

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
            xfr_lines.append(f"  group_by {c['source']}")
            xfr_lines.append(f"  select SUM({c['source']}) as {c['target']}")
            xfr_lines.append("")

    # Build .dml
    dml_lines = ["keys:"]
    for f in input_files:
        if f in fields:
            first_key = list(fields[f].keys())[0]
            dml_lines.append(f"  Raw_{f}: {first_key}")

    dml_lines.append("")
    dml_lines.append("schema:")
    for f in input_files:
        if f in fields:
            dml_lines.append(f"  Raw_{f}:")
            for col, typ in fields[f].items():
                dml_lines.append(f"    {col}: {typ}")
            dml_lines.append("")

    return {
        "mp": "\n".join(mp_lines),
        "xfr": "\n".join(xfr_lines),
        "dml": "\n".join(dml_lines),
    }
