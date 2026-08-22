# src/datagen.py
"""
Generador de datos sintéticos redactados (BNX Data Redactada).

Modo 1: Datos sintéticos puros. No usa datos reales de entrada.
- Infiere el esquema (nombre de campo + tipo) desde el grafo convertido:
  dml_fields de las transformaciones, casts detectados (to_date, CAST AS DECIMAL),
  el schema de .dml, y los campos de select/join/dedup.
- Detecta campos PII por nombre (nombre, cuenta, tarjeta, email, etc.) y genera
  valores redactados/enmascarados en lugar de datos plausibles reales.
- Genera N filas y exporta a CSV o JSON.
"""
import re
import csv
import io
import json
import random
import string as _string
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Tipos de dato soportados
# ---------------------------------------------------------------------------
# Normalizamos los tipos Ab Initio / Spark a un conjunto interno:
#   string | integer | decimal | date | datetime | boolean
TYPE_ALIASES = {
    "string": "string", "varchar": "string", "char": "string", "text": "string",
    "str": "string",
    "int": "integer", "integer": "integer", "long": "integer", "bigint": "integer",
    "smallint": "integer", "number": "integer",
    "decimal": "decimal", "double": "decimal", "float": "decimal", "numeric": "decimal",
    "real": "decimal",
    "date": "date",
    "datetime": "datetime", "timestamp": "datetime",
    "bool": "boolean", "boolean": "boolean",
}


def normalize_type(raw_type):
    """Normaliza una cadena de tipo a uno de los tipos internos."""
    if not raw_type:
        return "string"
    t = str(raw_type).strip().lower()
    # decimal(12,2) → decimal
    t = re.sub(r"\(.*\)", "", t).strip()
    return TYPE_ALIASES.get(t, "string")


# ---------------------------------------------------------------------------
# Detección de PII por nombre de campo
# ---------------------------------------------------------------------------
# Cada categoría PII tiene patrones de nombre (regex sobre el nombre en minúsculas)
# y una función de redacción.
PII_PATTERNS = {
    "name":    r"(nombre|name|apellido|surname|firstname|lastname|fullname|cliente|customer_name)",
    "email":   r"(email|correo|e_mail|mail)",
    "phone":   r"(phone|telefono|tel|celular|movil|mobile|msisdn)",
    "card":    r"(card|tarjeta|pan|creditcard|debitcard)",
    "account": r"(account|cuenta|acct|iban|clabe)",
    "ssn":     r"(ssn|curp|rfc|dni|nss|tax_id|taxid|nif)",
    "address": r"(address|direccion|domicilio|street|calle|zip|postal|cp)",
    "dob":     r"(birth|nacimiento|dob|fecha_nac)",
    "id":      r"(customer_id|client_id|user_id|cust_id|id_cliente|id_usuario)",
}


def detect_pii(field_name):
    """Devuelve la categoría PII detectada por nombre, o None."""
    fname = (field_name or "").lower()
    for category, pattern in PII_PATTERNS.items():
        if re.search(pattern, fname):
            return category
    return None


# ---------------------------------------------------------------------------
# Inferencia de esquema desde el grafo
# ---------------------------------------------------------------------------
def _infer_type_from_expr(expr):
    """Infiere el tipo de un campo a partir de su expresión Spark/DML."""
    if not expr:
        return "string"
    e = str(expr).lower()
    if "to_date(" in e or "current_date(" in e:
        return "date"
    if "to_timestamp(" in e or "current_timestamp(" in e or "now" in e:
        return "datetime"
    if "as decimal" in e or "cast(" in e and "decimal" in e:
        return "decimal"
    if "as int" in e or "as integer" in e:
        return "integer"
    if "as string" in e or "lpad(" in e or "substring(" in e or "trim(" in e or "concat(" in e:
        return "string"
    if re.search(r"\blit\(\s*-?\d+\.\d+", e):
        return "decimal"
    if re.search(r"\blit\(\s*-?\d+\s*\)", e):
        return "integer"
    return "string"


def infer_schema_from_graph(ast, xfr_rules, dml_schema=None):
    """Extrae un esquema por nodo a partir del grafo convertido.

    Devuelve una lista de dicts:
        [{"node": "cust_seg_func", "node_type": "TRANSFORM",
          "columns": [{"name": "last_updated_date", "type": "date", "pii": "dob"|None}, ...]}]

    Fuentes por prioridad:
      1. dml_schema (.dml)  → tipos explícitos
      2. dml_fields (xfr)   → campo + expresión (inferimos tipo)
      3. select "a as b, c" → nombres de campo (tipo string por defecto)
    """
    dml_schema = dml_schema or {}
    result = []

    nodes = ast.get("nodes", []) if isinstance(ast, dict) else []
    for nd in nodes:
        nid = nd.get("id", "")
        nname = nd.get("name", nid)
        ntype = nd.get("type", "TRANSFORM")
        columns = []
        seen = set()

        def add_col(name, ctype):
            key = name.lower()
            if not name or key in seen:
                return
            seen.add(key)
            ntype_norm = normalize_type(ctype)
            columns.append({
                "name": name,
                "type": ntype_norm,
                "pii": detect_pii(name),
            })

        # 1. .dml schema (busca por id o name)
        for schema_key in (nid, nname):
            if schema_key in dml_schema:
                for col, ctype in dml_schema[schema_key].items():
                    add_col(col, ctype)

        # 2. xfr_rules: dml_fields / select
        rule = xfr_rules.get(nid.lower()) or xfr_rules.get(nname.lower()) or {}
        if isinstance(rule, dict):
            # dml_fields: [{"field": ..., "expr": ...}]
            for f in rule.get("dml_fields", []) or []:
                fname = f.get("field")
                ftype = _infer_type_from_expr(f.get("expr"))
                add_col(fname, ftype)

            # select: "a as A, b, to_date(x) as d"
            select = rule.get("select")
            if select and select != "*":
                for part in _split_select(select):
                    m = re.match(r"(.+?)\s+as\s+(\w+)\s*$", part.strip(), re.I)
                    if m:
                        expr_part, alias = m.group(1).strip(), m.group(2)
                        add_col(alias, _infer_type_from_expr(expr_part))
                    else:
                        col = part.strip().strip('"').split(".")[-1]
                        if re.match(r"^\w+$", col):
                            add_col(col, "string")

            # group_by / dedup_keys / join_key add plain columns
            for key in ("group_by", "dedup_keys"):
                val = rule.get(key)
                if isinstance(val, list):
                    for c in val:
                        add_col(str(c).strip(), "string")

        if columns:
            result.append({
                "node": nname,
                "node_type": ntype,
                "columns": columns,
            })

    return result


def _split_select(select):
    """Divide un select por comas de nivel superior (respeta paréntesis)."""
    parts = []
    depth = 0
    buf = []
    for ch in select:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return parts


# ---------------------------------------------------------------------------
# Generación de valores sintéticos
# ---------------------------------------------------------------------------
_FIRST_NAMES = ["Alex", "Sam", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Jamie"]
_LAST_NAMES = ["Smith", "Garcia", "Lopez", "Brown", "Davis", "Miller", "Wilson", "Moore"]


def _rand_date(rng, start_year=2020, end_year=2026):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, delta))


def _redact_pii(category, rng, row_idx):
    """Genera un valor redactado/enmascarado para un campo PII."""
    if category == "name":
        # Nombre parcialmente redactado
        first = rng.choice(_FIRST_NAMES)
        return f"{first[0]}{'*' * (len(first) - 1)} {rng.choice(_LAST_NAMES)[0]}****"
    if category == "email":
        return f"user{row_idx}****@example.com"
    if category == "phone":
        return f"+1-***-***-{rng.randint(1000, 9999)}"
    if category == "card":
        return f"****-****-****-{rng.randint(1000, 9999)}"
    if category == "account":
        return f"ACCT****{rng.randint(1000, 9999)}"
    if category == "ssn":
        return f"***-**-{rng.randint(1000, 9999)}"
    if category == "address":
        return f"*** REDACTED ST, CITY {rng.randint(10000, 99999)}"
    if category == "dob":
        # Fecha redactada al año
        return f"{rng.randint(1960, 2005)}-**-**"
    if category == "id":
        return f"ID****{rng.randint(100000, 999999)}"
    return "REDACTED"


def _gen_value(col, rng, row_idx):
    """Genera un valor sintético para una columna según tipo y PII."""
    pii = col.get("pii")
    if pii:
        return _redact_pii(pii, rng, row_idx)

    ctype = col.get("type", "string")
    name = col.get("name", "col")
    if ctype == "integer":
        return rng.randint(1, 100000)
    if ctype == "decimal":
        return round(rng.uniform(0, 100000), 2)
    if ctype == "date":
        return _rand_date(rng).strftime("%Y-%m-%d")
    if ctype == "datetime":
        return _rand_date(rng).strftime("%Y-%m-%d %H:%M:%S")
    if ctype == "boolean":
        return rng.choice([True, False])
    # string: valor genérico derivado del nombre
    suffix = "".join(rng.choices(_string.ascii_uppercase + _string.digits, k=6))
    return f"{name.upper()[:8]}_{suffix}"


def generate_rows(columns, n_rows=10, seed=None):
    """Genera n_rows filas sintéticas para una lista de columnas.

    columns: [{"name", "type", "pii"}]
    Devuelve: list[dict]
    """
    rng = random.Random(seed)
    rows = []
    for i in range(n_rows):
        row = {}
        for col in columns:
            row[col["name"]] = _gen_value(col, rng, i)
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Exportadores
# ---------------------------------------------------------------------------
def rows_to_csv(columns, rows, delimiter=","):
    """Serializa filas a CSV."""
    out = io.StringIO()
    field_names = [c["name"] for c in columns]
    writer = csv.DictWriter(out, fieldnames=field_names, delimiter=delimiter)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return out.getvalue()


def rows_to_json(rows):
    """Serializa filas a JSON."""
    return json.dumps(rows, indent=2, default=str)


# ---------------------------------------------------------------------------
# Entry point de alto nivel
# ---------------------------------------------------------------------------
def build_synthetic_data(columns, n_rows=10, fmt="csv", seed=None, delimiter=","):
    """Genera datos sintéticos redactados y los serializa.

    columns: [{"name", "type", "pii"?}]  — pii se detecta si no viene
    Devuelve dict: {"columns", "rows", "content", "format"}
    """
    # Completar detección de PII y normalización de tipo
    norm_columns = []
    for col in columns:
        name = col.get("name", "")
        ctype = normalize_type(col.get("type", "string"))
        pii = col.get("pii", None)
        if pii is None:
            pii = detect_pii(name)
        elif pii is False:
            pii = None  # PII explícitamente desactivada
        norm_columns.append({"name": name, "type": ctype, "pii": pii})

    rows = generate_rows(norm_columns, n_rows=n_rows, seed=seed)

    if fmt == "json":
        content = rows_to_json(rows)
    else:
        content = rows_to_csv(norm_columns, rows, delimiter=delimiter)
        fmt = "csv"

    return {
        "columns": norm_columns,
        "rows": rows,
        "content": content,
        "format": fmt,
    }
