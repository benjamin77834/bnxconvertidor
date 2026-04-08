# src/plan_parser.py
"""
Parses Ab Initio PLAN and PSET files.
PLAN: execution order, dependencies between graphs.
PSET: runtime parameters (paths, connections, thresholds).
Generates .mp with orchestration DAG.
"""
import re


def parse_plan(path):
    """Parse a .plan file into graphs with dependencies."""
    graphs = {}
    plan_name = ""
    current = None

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Plan name
            m = re.match(r"PLAN\s+(\w+)", line, re.I)
            if m:
                plan_name = m.group(1)
                continue

            # Version
            if line.upper().startswith("VERSION"):
                continue

            # Graph definition
            m = re.match(r"GRAPH\s+(\w+)", line, re.I)
            if m:
                current = m.group(1)
                graphs[current] = {
                    "name": current,
                    "mp": None, "xfr": None, "dml": None,
                    "depends": [],
                    "schedule": None,
                    "priority": "MEDIUM",
                    "on_success": None,
                    "on_failure": None,
                }
                continue

            if current:
                # Properties
                m = re.match(r"MP:\s*(.+)", line, re.I)
                if m: graphs[current]["mp"] = m.group(1).strip(); continue

                m = re.match(r"XFR:\s*(.+)", line, re.I)
                if m: graphs[current]["xfr"] = m.group(1).strip(); continue

                m = re.match(r"DML:\s*(.+)", line, re.I)
                if m: graphs[current]["dml"] = m.group(1).strip(); continue

                m = re.match(r"DEPENDS:\s*(.+)", line, re.I)
                if m:
                    deps = [d.strip() for d in m.group(1).split(",")]
                    graphs[current]["depends"] = deps
                    continue

                m = re.match(r"SCHEDULE:\s*(.+)", line, re.I)
                if m: graphs[current]["schedule"] = m.group(1).strip(); continue

                m = re.match(r"PRIORITY:\s*(.+)", line, re.I)
                if m: graphs[current]["priority"] = m.group(1).strip().upper(); continue

                m = re.match(r"ON_SUCCESS:\s*(.+)", line, re.I)
                if m: graphs[current]["on_success"] = m.group(1).strip(); continue

                m = re.match(r"ON_FAILURE:\s*(.+)", line, re.I)
                if m: graphs[current]["on_failure"] = m.group(1).strip(); continue

    return {"name": plan_name, "graphs": graphs}


def parse_pset(path):
    """Parse a .pset file into key-value parameters."""
    params = {}

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            m = re.match(r"(\w+)\s*=\s*(.+)", line)
            if m:
                params[m.group(1)] = m.group(2).strip()

    return params


def plan_to_graph(parsed_plan, parsed_pset=None):
    """Convert parsed PLAN to .mp format with orchestration DAG."""
    graphs = parsed_plan["graphs"]
    pset = parsed_pset or {}

    mp_lines = [f"# Auto-generated from Ab Initio PLAN: {parsed_plan['name']}", ""]

    # Determine node types based on name patterns
    for name, g in graphs.items():
        if any(k in name.lower() for k in ["ingest", "read", "load"]):
            ntype = "SOURCE"
        elif any(k in name.lower() for k in ["report", "write", "notify", "export"]):
            ntype = "SINK"
        elif any(k in name.lower() for k in ["join", "enrich", "merge"]):
            ntype = "JOIN"
        elif any(k in name.lower() for k in ["dedup"]):
            ntype = "DEDUP"
        elif any(k in name.lower() for k in ["agg", "total", "balance", "revenue"]):
            ntype = "TRANSFORM"
        elif any(k in name.lower() for k in ["clean", "filter", "validate"]):
            ntype = "TRANSFORM"
        elif any(k in name.lower() for k in ["risk", "aml", "fraud", "score"]):
            ntype = "TRANSFORM"
        else:
            ntype = "TRANSFORM"
        g["node_type"] = ntype

    # Group by phase (based on dependencies depth)
    phases = {}
    def get_depth(name, visited=None):
        if visited is None: visited = set()
        if name in visited: return 0
        visited.add(name)
        g = graphs.get(name)
        if not g or not g["depends"]: return 0
        return 1 + max(get_depth(d, visited) for d in g["depends"] if d in graphs)

    for name in graphs:
        depth = get_depth(name)
        if depth not in phases: phases[depth] = []
        phases[depth].append(name)

    # Write subgraphs by phase
    for depth in sorted(phases.keys()):
        phase_name = f"Phase_{depth}"
        mp_lines.append(f"SUBGRAPH {phase_name} {{")
        for name in phases[depth]:
            g = graphs[name]
            mp_lines.append(f"  NODE {name} : {g['node_type']}")
        mp_lines.append("}")
        mp_lines.append("")

    # Write edges from dependencies
    for name, g in graphs.items():
        for dep in g["depends"]:
            if dep in graphs:
                mp_lines.append(f"{dep} -> {name}")

    # Generate XFR with PSET parameters
    xfr_lines = [f"# Auto-generated from Ab Initio PLAN + PSET", ""]

    s3_input = pset.get("S3_INPUT", "s3://datalake/raw")
    s3_output = pset.get("S3_OUTPUT", "s3://datalake/curated")
    output_format = pset.get("OUTPUT_FORMAT", "parquet").lower()
    kafka_brokers = pset.get("KAFKA_BROKERS")
    kafka_topic = pset.get("KAFKA_TOPIC_EVENTS")

    for name, g in graphs.items():
        ntype = g["node_type"]
        if ntype == "SOURCE":
            xfr_lines.append(f"{name}:")
            if kafka_brokers and "event" in name.lower():
                xfr_lines.append(f"  source_type kafka")
                xfr_lines.append(f"  topic {kafka_topic or 'events'}")
                xfr_lines.append(f"  connection {kafka_brokers}")
            else:
                xfr_lines.append(f"  source_type s3")
                xfr_lines.append(f"  path {s3_input}/{name.lower()}")
                xfr_lines.append(f"  format {output_format}")
            xfr_lines.append("")
        elif ntype == "SINK":
            xfr_lines.append(f"{name}:")
            xfr_lines.append(f"  sink_type s3")
            xfr_lines.append(f"  path {s3_output}/{name.lower()}")
            xfr_lines.append(f"  format {output_format}")
            xfr_lines.append(f"  mode overwrite")
            xfr_lines.append("")
        elif ntype == "JOIN" and g["depends"]:
            xfr_lines.append(f"{name}:")
            xfr_lines.append(f"  join_key customer_id")
            xfr_lines.append(f"  join_type left")
            xfr_lines.append("")
        elif ntype == "DEDUP":
            xfr_lines.append(f"{name}:")
            xfr_lines.append(f"  dedup_keys tx_id")
            xfr_lines.append(f"  order_by tx_date")
            xfr_lines.append("")

    return {
        "mp": "\n".join(mp_lines),
        "xfr": "\n".join(xfr_lines),
        "pset": pset,
    }
