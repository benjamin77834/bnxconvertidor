# src/ocr_engine.py
"""
OCR Engine for BNX Convertidor.
Extracts text from images of Ab Initio graphs/logs.
Uses AWS Textract for accurate text extraction.
Fallback: basic pattern matching on raw text.
"""
import re
import json


def extract_text_from_image(image_bytes):
    """
    Extract text from image using AWS Textract.
    Returns the raw text content.
    """
    try:
        import boto3
        client = boto3.client('textract', region_name='us-east-1')
        response = client.detect_document_text(
            Document={'Bytes': image_bytes}
        )
        # Combine all detected text blocks
        lines = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                lines.append(block['Text'])
        return '\n'.join(lines)
    except ImportError:
        return None  # boto3 not available
    except Exception as e:
        return f"ERROR: {str(e)}"


def parse_extracted_text(text):
    """
    Parse extracted text (from OCR or direct paste) and detect Ab Initio format.
    Returns structured data: nodes, edges, parameters, metadata.
    """
    result = {
        "format": "unknown",
        "graph_name": None,
        "nodes": [],
        "edges": [],
        "flows": [],
        "parameters": [],
        "watchers": [],
        "metadata": {},
        "raw_lines": 0,
    }

    lines = text.strip().split('\n')
    result["raw_lines"] = len(lines)

    # Detect format
    if any("XXGpvertex" in l for l in lines):
        result["format"] = "abinitio_native_mp"
    elif any("XXGflow" in l for l in lines):
        result["format"] = "abinitio_execution_log"
    elif any("XXGgraph" in l for l in lines):
        result["format"] = "abinitio_graph_def"
    elif any("NODE" in l and ":" in l for l in lines):
        result["format"] = "bnx_mp"
    elif any("||||" in l for l in lines):
        result["format"] = "abinitio_pset"
    else:
        result["format"] = "text"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # XXGgraph ? graph definition
        m = re.search(r'XXGgraph.*\|([^|]+)\|', line)
        if m and not result["graph_name"]:
            # Try to extract graph name
            parts = line.split('|')
            for p in parts:
                if p and not p.isdigit() and len(p) > 3 and 'XXG' not in p and '@' not in p:
                    result["graph_name"] = p.strip()
                    break

        # Fallas_diferencia or job name from log
        m = re.search(r'Fallas_\w+|Job\s+"([^"]+)"', line)
        if m and not result["graph_name"]:
            result["graph_name"] = m.group(1) if m.group(1) else m.group(0)

        # XXGpvertex ? node
        m = re.match(r'\{[^|]*\|XXGpvertex\|(\d+)\|', line)
        if m:
            vid = m.group(1)
            name_match = re.search(r'@1\|([^|]+)\|', line)
            name = name_match.group(1).strip() if name_match else f"Node_{vid}"
            result["nodes"].append({"id": vid, "name": name, "raw": line[:100]})
            continue

        # XXGflow ? edge/flow
        m = re.match(r'\{[^|]*\|XXGflow\|(\d+)\|(\d+)\|(\d+)\|', line)
        if m:
            flow_id = m.group(1)
            # Extract port references from the line
            result["flows"].append({"id": flow_id, "raw": line[:100]})
            continue

        # XXGedge ? direct edge
        m = re.match(r'\{[^|]*\|XXGedge\|(\d+)\|(\d+)\|', line)
        if m:
            result["edges"].append({"from": m.group(1), "to": m.group(2)})
            continue

        # XXparameter
        m = re.match(r'\{[^|]*\|XXparameter\|([^|]+)\|([^|]*)\|', line)
        if m:
            result["parameters"].append({"key": m.group(1).strip(), "value": m.group(2).strip()})
            continue

        # XXGwatcher
        if "XXGwatcher" in line:
            result["watchers"].append(line[:80])
            continue

        # XXGrunsettings
        if "XXGrunsettings" in line:
            result["metadata"]["run_settings"] = line[:100]
            continue

        # Execution metadata
        if "Ejecuci" in line or "iniciada" in line or "complet?" in line:
            if "iniciada" in line:
                result["metadata"]["start_time"] = line
            elif "complet" in line:
                result["metadata"]["end_time"] = line

        if "Tiempo de ejecuci" in line:
            result["metadata"]["execution_time"] = line

        if "usuario" in line:
            result["metadata"]["user"] = line

    return result


def text_to_mp(parsed):
    """Convert parsed OCR/text data to .mp format for compilation."""
    mp_lines = [f"# Auto-generated from OCR/text extraction"]
    mp_lines.append(f"# Source format: {parsed['format']}")
    if parsed.get("graph_name"):
        mp_lines.append(f"# Graph: {parsed['graph_name']}")
    mp_lines.append("")

    if parsed["nodes"]:
        for node in parsed["nodes"]:
            # Infer type from name
            name = node["name"]
            name_lower = name.lower()
            if any(k in name_lower for k in ["read", "input", "scan", "source", "extract"]):
                ntype = "SOURCE"
            elif any(k in name_lower for k in ["write", "output", "sink", "load"]):
                ntype = "SINK"
            elif any(k in name_lower for k in ["merge", "join", "lookup"]):
                ntype = "JOIN"
            elif any(k in name_lower for k in ["rollup", "aggregate", "summary"]):
                ntype = "TRANSFORM"
            elif any(k in name_lower for k in ["sort", "reformat", "transform"]):
                ntype = "TRANSFORM"
            elif any(k in name_lower for k in ["filter"]):
                ntype = "FILTER"
            elif any(k in name_lower for k in ["partition"]):
                ntype = "PARTITION"
            elif any(k in name_lower for k in ["dedup"]):
                ntype = "DEDUP"
            else:
                ntype = "TRANSFORM"

            safe_name = re.sub(r'[^\w]', '_', name)
            mp_lines.append(f"NODE {safe_name} : {ntype}")

        mp_lines.append("")
        for edge in parsed["edges"]:
            # Map vertex IDs to node names
            from_node = next((n for n in parsed["nodes"] if n["id"] == edge["from"]), None)
            to_node = next((n for n in parsed["nodes"] if n["id"] == edge["to"]), None)
            if from_node and to_node:
                from_name = re.sub(r'[^\w]', '_', from_node["name"])
                to_name = re.sub(r'[^\w]', '_', to_node["name"])
                mp_lines.append(f"{from_name} -> {to_name}")

    return "\n".join(mp_lines)
