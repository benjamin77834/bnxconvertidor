# src/dml_parser.py
import re


def _parse_dml_text(text):
    """Parsea el contenido (string) de UN .dml con formato:
        keys:
          NodeName: key_col
        schema:
          NodeName:
            col_name: type
    Retorna {"keys": {...}, "schema": {...}}.
    """
    keys = {}
    schema = {}

    current_section = None   # "keys" | "schema"
    current_node = None

    for line in text.splitlines():
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        # Detecta seccion raiz: "keys:" o "schema:"
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
            # Cabecera de nodo (indent <= 2): "  NodeName:"
            if re.match(r"^\w+\s*:$", stripped) and indent <= 2:
                current_node = stripped.rstrip(":")
                schema[current_node] = {}
            # Columna (indent > 2): "    col_name: type"
            elif current_node and indent > 2:
                m = re.match(r"(\w+)\s*:\s*(\w+)", stripped)
                if m:
                    schema[current_node][m.group(1)] = m.group(2)

    return {"keys": keys, "schema": schema}


def _merge_dml(acc, part):
    """Mergea un .dml parseado (part) dentro del acumulador (acc).

    Politica de colision por nombre de nodo:
      - schema: se mergean las COLUMNAS. Si una columna ya existe, gana la del
        primer archivo (no se pisa) para que el orden de subida sea predecible.
      - keys: si el nodo ya tiene key, se conserva la primera (no se pisa).
    Asi subir varios .dml SUMA definiciones en vez de que el ultimo gane.
    """
    for node, cols in part.get("schema", {}).items():
        if node not in acc["schema"]:
            acc["schema"][node] = {}
        for col, typ in cols.items():
            acc["schema"][node].setdefault(col, typ)
    for node, key in part.get("keys", {}).items():
        acc["keys"].setdefault(node, key)
    return acc


def parse_dml(path):
    """Parsea un archivo .dml. Soporta UN solo archivo o VARIOS concatenados.

    Varios .dml concatenados se separan con un marcador de linea:
        # === nombre_a.dml ===
        ...contenido...
        # === nombre_b.dml ===
        ...contenido...
    (mismo formato que el multi-.xfr). Cada bloque se parsea por separado y se
    mergea con _merge_dml (las columnas se SUMAN; en colision gana el primero).

    Retorna {"keys": {...}, "schema": {...}} igual que antes (compatible).
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Deteccion de concatenacion por marcador "# ===".
    if "# ===" in content:
        acc = {"keys": {}, "schema": {}}
        # El split por el marcador produce bloques; la primera parte antes del
        # primer marcador suele estar vacia, se ignora si no tiene contenido.
        sections = content.split("# ===")
        for section in sections:
            if not section.strip():
                continue
            lines = section.split("\n")
            # La primera linea es "nombre.dml ===" (cabecera del marcador): la
            # descartamos del cuerpo a parsear.
            body = "\n".join(lines[1:]) if len(lines) > 1 else ""
            part = _parse_dml_text(body)
            if part["schema"] or part["keys"]:
                _merge_dml(acc, part)
        return acc

    # Un solo archivo (comportamiento original).
    return _parse_dml_text(content)
