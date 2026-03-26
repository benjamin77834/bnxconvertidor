# src/dml_parser.py
import re


def parse_dml(path):
    """
    Parsea archivos .dml con formato:
        keys:
          NodeName: key_col

        schema:
          NodeName:
            col_name: type
            ...

    Retorna:
        {
          "keys":   { "NodeName": "key_col" },
          "schema": { "NodeName": { "col_name": "type", ... } }
        }
    """
    keys = {}
    schema = {}

    current_section = None   # "keys" | "schema"
    current_node = None

    with open(path, "r") as f:
        for line in f:
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            # Detecta sección raíz: "keys:" o "schema:"
            if re.match(r"^keys\s*:$", stripped, re.I):
                current_section = "keys"
                current_node = None
                continue

            if re.match(r"^schema\s*:$", stripped, re.I):
                current_section = "schema"
                current_node = None
                continue

            indent = len(line) - len(line.lstrip())

            if current_section == "keys":
                # "  NodeName: key_col"
                m = re.match(r"(\w+)\s*:\s*(\w+)", stripped)
                if m:
                    keys[m.group(1)] = m.group(2)

            elif current_section == "schema":
                # Cabecera de nodo (indent == 2): "  NodeName:"
                if re.match(r"^\w+\s*:$", stripped) and indent <= 2:
                    current_node = stripped.rstrip(":")
                    schema[current_node] = {}
                # Columna (indent > 2): "    col_name: type"
                elif current_node and indent > 2:
                    m = re.match(r"(\w+)\s*:\s*(\w+)", stripped)
                    if m:
                        schema[current_node][m.group(1)] = m.group(2)

    return {"keys": keys, "schema": schema}
