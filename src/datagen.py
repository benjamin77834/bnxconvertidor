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


_GENERIC_COLUMNS = [
    ("id", "integer"),
    ("record_date", "date"),
    ("amount", "decimal"),
    ("status", "string"),
    ("description", "string"),
]


# Operadores de comparacion que, junto a un literal numerico, revelan que una
# columna es numerica y sugieren un valor que satisface el filtro (para que la
# prueba con datos sinteticos no quede en 0 filas por un filtro que nada cumple).
_CMP_RE = re.compile(
    r'(?:CAST\(\s*|coalesce\(\s*)?'                      # opcional CAST( o coalesce(
    r'(?:in\d*\.)?([A-Za-z_]\w*)'                        # columna
    r'(?:\s*,\s*[^)]*\))?'                               # opcional resto de coalesce(col, 0)
    r'(?:\s+AS\s+[A-Za-z]+\s*(?:\([^)]*\))?\s*\))?'      # opcional AS DECIMAL(10,0))
    r'\s*(>=|<=|!=|<>|==|=|>|<)\s*'                      # operador (incluye != y <>)
    r'(-?\d+(?:\.\d+)?)',                                # literal numerico
    re.IGNORECASE,
)

# Igualdad contra un literal STRING: col == 'Y'  /  col = "ABC"  (y != para exclusion).
_STR_EQ_RE = re.compile(
    r"(?:string_lrtrim\(\s*|trim\(\s*|CAST\(\s*)?"       # opcional trim/cast alrededor
    r"(?:in\d*\.)?([A-Za-z_]\w*)"                        # columna
    r"(?:\s*\)|\s+AS\s+[A-Za-z]+\s*)?"                   # cierre opcional del trim/cast
    r"\s*(==|=|!=|<>)\s*"                                # operador de igualdad
    r"'([^']*)'",                                        # literal string entre comillas simples
    re.IGNORECASE,
)


def _extract_numeric_constraints(xfr_rules):
    """Escanea las condiciones (where/filter) de las reglas del grafo y detecta
    columnas comparadas contra literales numericos. Devuelve:
        {col_lower: {"type": "integer"|"decimal", "satisfy": <valor>}}
    'satisfy' es un valor que hace VERDADERA la comparacion, para que los datos
    sinteticos pasen el filtro y las salidas no queden vacias.
    """
    constraints = {}
    if not isinstance(xfr_rules, dict):
        return constraints
    for rule in xfr_rules.values():
        if not isinstance(rule, dict):
            continue
        conds = []
        for k in ("where", "filter", "selection", "condition"):
            v = rule.get(k)
            if isinstance(v, str) and v.strip():
                conds.append(v)
        for cond in conds:
            for m in _CMP_RE.finditer(cond):
                col, op, lit = m.group(1), m.group(2), m.group(3)
                cl = col.lower()
                if cl in _SQL_KEYWORDS:
                    continue
                is_dec = "." in lit
                num = float(lit) if is_dec else int(lit)
                not_equal = False
                exact = False
                # Valor que satisface el operador.
                if op in ("=", "=="):
                    satisfy = num
                    exact = True  # debe ser EXACTAMENTE num
                elif op in (">=", "<="):
                    satisfy = num
                elif op == ">":
                    satisfy = num + (0.01 if is_dec else 1)
                elif op == "<":
                    satisfy = num - (0.01 if is_dec else 1)
                elif op in ("!=", "<>"):
                    # Cualquier valor distinto cumple; el generador usara base+delta.
                    satisfy = num
                    not_equal = True
                else:
                    satisfy = num
                # Si la columna aparece en varios filtros, el ultimo constraint gana
                # (suficiente para los casos tipicos de un solo filtro por columna).
                constraints[cl] = {
                    "type": "decimal" if is_dec else "integer",
                    "satisfy": satisfy,
                    "not_equal": not_equal,
                    "exact": exact,
                }
            # Igualdad contra literal STRING: generamos ese valor (o uno distinto
            # para !=) para que el filtro pase. No pisamos un constraint numerico
            # ya detectado para la misma columna.
            for m in _STR_EQ_RE.finditer(cond):
                col, op, val = m.group(1), m.group(2), m.group(3)
                cl = col.lower()
                if cl in _SQL_KEYWORDS or cl in constraints:
                    continue
                constraints[cl] = {
                    "type": "string",
                    "str_value": val,
                    "str_not_equal": op in ("!=", "<>"),
                }
    return constraints


# Cast Ab Initio/DML de una columna a un tipo concreto:
#   out.X :: (decimal(1)) in.X   |   out.X :: (integer(4)) in.X
#   out.X :: (date("YYYYMMDD")) in.X   |   CAST(in.X AS DECIMAL(10,2))
# Detecta el tipo destino y la columna ORIGEN (in.X) para tiparla en el SOURCE,
# de modo que el dato sintetico sea compatible con el cast (si no, el cast a
# decimal/int/date de un string aleatorio da NULL).
_CAST_ABINITIO_RE = re.compile(
    r'\(\s*(decimal|integer|int|real|double|float|numeric|date|datetime|timestamp)\b'
    r'[^)]*(?:\([^)]*\))?[^)]*\)+\s*'               # (decimal(1)) / (date("YYYYMMDD")) — tolera parentesis interno y cierres multiples
    r'(?:in\d*\.)?([A-Za-z_]\w*)',                  # columna origen in.X
    re.IGNORECASE,
)
_CAST_SQL_RE = re.compile(
    r'CAST\(\s*(?:in\d*\.)?([A-Za-z_]\w*)\s+AS\s+'
    r'(decimal|integer|int|bigint|long|smallint|real|double|float|numeric|date|datetime|timestamp)\b',
    re.IGNORECASE,
)


def _extract_cast_types(xfr_rules):
    """Escanea dml_fields/raw_transform/select y detecta columnas ORIGEN que un
    transform castea a un tipo concreto (decimal/int/date...). Devuelve
    {col_lower: tipo_normalizado}. Permite tipar el SOURCE upstream para que el
    dato sintetico sobreviva al cast (evita decimal(string)->NULL)."""
    casts = {}
    if not isinstance(xfr_rules, dict):
        return casts

    def _record(col, raw_type, precision=None):
        cl = (col or "").lower()
        if not cl or cl in _SQL_KEYWORDS:
            return
        t = normalize_type(raw_type)
        if t != "string":
            entry = {"type": t}
            if precision is not None:
                entry["precision"] = precision
            casts[cl] = entry

    def _prec(raw_type_full):
        # Extrae la precision de un cast: decimal(1) -> 1, decimal(10,2) -> 10.
        # Determina el rango maximo del valor sintetico para que no desborde.
        m = re.search(r'\(\s*(\d+)', raw_type_full or "")
        return int(m.group(1)) if m else None

    def _scan(text):
        if not isinstance(text, str) or not text:
            return
        # Ab Initio: capturamos el fragmento completo del cast para leer precision.
        for m in _CAST_ABINITIO_RE.finditer(text):
            _record(m.group(2), m.group(1), _prec(m.group(0)))
        for m in _CAST_SQL_RE.finditer(text):
            _record(m.group(1), m.group(2))

    for rule in xfr_rules.values():
        if not isinstance(rule, dict):
            continue
        _scan(rule.get("raw_transform"))
        _scan(rule.get("select"))
        for f in rule.get("dml_fields", []) or []:
            _scan(str(f.get("expr") or ""))
    return casts


def infer_schema_from_graph(ast, xfr_rules, dml_schema=None):
    """Extrae el esquema de ENTRADA y SALIDA por nodo a partir del grafo.

    Distingue:
      - ENTRADA (io="input"): lo que el nodo CONSUME. Columnas de SOURCE,
        y las referencias in.CAMPO de las expresiones de transformación.
      - SALIDA (io="output"): lo que el nodo PRODUCE. Los out.CAMPO de
        reformats/dml_fields, los alias del select, y columnas de SINK.

    Devuelve una lista de dicts, uno por (nodo, io) con columnas:
        [{"node": "cust_seg_func", "node_type": "TRANSFORM", "io": "input",
          "columns": [{"name", "type", "pii"}]},
         {"node": "cust_seg_func", "node_type": "TRANSFORM", "io": "output",
          "columns": [...]}]
    """
    dml_schema = dml_schema or {}
    nodes = ast.get("nodes", []) if isinstance(ast, dict) else []
    edges = ast.get("edges", []) if isinstance(ast, dict) else []

    # Constraints numericos de los filtros del grafo: columnas comparadas contra
    # numeros. Se usan para (a) tipar esas columnas como numericas y (b) generar
    # valores que satisfagan el filtro, evitando salidas en 0 filas.
    num_constraints = _extract_numeric_constraints(xfr_rules)
    # Tipos destino de casts (decimal/int/date): para tipar columnas ORIGEN y que
    # el dato sintetico sobreviva al cast (evita decimal(string)->NULL en la salida).
    cast_types = _extract_cast_types(xfr_rules)

    # Info por nodo: cols input/output (dict nombre_lower -> {name,type,pii})
    node_info = {}       # nname -> {"type", "in": {}, "out": {}}
    id_to_name = {}      # id/name lower -> nname (para trazar edges)
    join_key_names = set()  # nombres (lower) de columnas que son clave de join

    def _mk_col(name, ctype):
        return {"name": name, "type": normalize_type(ctype), "pii": detect_pii(name)}

    for nd in nodes:
        nid = nd.get("id", "")
        nname = nd.get("name", nid)
        ntype = nd.get("type", "TRANSFORM")
        id_to_name[nid.lower()] = nname
        id_to_name[nname.lower()] = nname

        in_cols, out_cols = {}, {}

        def add_in(name, ctype="string"):
            k = (name or "").lower()
            if name and k not in in_cols:
                in_cols[k] = _mk_col(name, ctype)

        def add_out(name, ctype="string"):
            k = (name or "").lower()
            if name and k not in out_cols:
                out_cols[k] = _mk_col(name, ctype)

        rule = xfr_rules.get(nid.lower()) or xfr_rules.get(nname.lower()) or {}
        if not isinstance(rule, dict):
            rule = {}

        # 0. record_fields: esquema REAL del nodo (del .mp GDE) — maxima prioridad
        for f in rule.get("record_fields", []) or []:
            add_in(f.get("name"), f.get("type", "string"))
            add_out(f.get("name"), f.get("type", "string"))

        # 1. .dml schema externo
        for schema_key in (nid, nname):
            if schema_key in dml_schema:
                for col, ctype in dml_schema[schema_key].items():
                    add_out(col, ctype)
                    add_in(col, ctype)

        # 2. dml_fields
        for f in rule.get("dml_fields", []) or []:
            add_out(f.get("field"), _infer_type_from_expr(f.get("expr")))
            for src in re.findall(r'col\("(\w+)"\)', str(f.get("expr") or "")):
                add_in(src, "string")

        # 3. select
        select = rule.get("select")
        if select and select != "*":
            for part in _split_select(select):
                m = re.match(r"(.+?)\s+as\s+(\w+)\s*$", part.strip(), re.I)
                if m:
                    expr_part, alias = m.group(1).strip(), m.group(2)
                    add_out(alias, _infer_type_from_expr(expr_part))
                    for src in re.findall(r'\b(?:in\d*\.)?(\w+)\b', expr_part):
                        if src.lower() not in _SQL_KEYWORDS and not src.isdigit():
                            add_in(src, "string")
                else:
                    col = part.strip().strip('"').split(".")[-1]
                    if re.match(r"^\w+$", col):
                        add_out(col, "string")
                        add_in(col, "string")

        # 4. raw_transform
        raw = rule.get("raw_transform")
        if raw:
            for fname, fexpr in re.findall(r"out\.(\w+)\s*::\s*(.+?);", raw):
                if fname not in ("newline", "V_FILLER"):
                    add_out(fname, _infer_type_from_expr(fexpr))
            for src in re.findall(r"in\d*\.(\w+)", raw):
                add_in(src, "string")

        # 4b. Columnas referenciadas en el WHERE/filtro del nodo: deben existir en
        # los datos para que el filtro pueda evaluarse (si no, la columna es NULL y
        # el filtro descarta todo). Las agregamos como entrada del nodo.
        for wkey in ("where", "filter", "selection", "condition"):
            wexpr = rule.get(wkey)
            if isinstance(wexpr, str) and wexpr.strip():
                # Quitar literales entre comillas ANTES de escanear identificadores.
                # Sin esto, un filtro como event_type=='finish' or ...=='stdout'
                # tomaria 'finish' y 'stdout' (valores, no columnas) como columnas.
                wexpr_nolit = re.sub(r"'[^']*'|\"[^\"]*\"", " ", wexpr)
                for src in re.findall(r'(?:in\d*\.)?([A-Za-z_]\w*)', wexpr_nolit):
                    sl = src.lower()
                    if sl not in _SQL_KEYWORDS and not src.isdigit() and len(src) > 1:
                        add_in(src, "string")

        # 5. keys (join/sort/dedup/group)
        for key in ("group_by", "dedup_keys", "join_key", "sort_by"):
            val = rule.get(key)
            names = []
            if isinstance(val, list):
                for c in val:
                    names += [s.strip() for s in re.split(r"[;,]", str(c)) if s.strip()]
            elif isinstance(val, str):
                names += [s.strip() for s in re.split(r"[;,]", val) if s.strip()]
            for nm in names:
                nm = re.sub(r"\s+(descending|ascending|desc|asc)$", "", nm, flags=re.I).strip()
                if re.match(r"^\w+$", nm):
                    add_in(nm, "string")
                    add_out(nm, "string")
                    # Las claves de JOIN se marcan para generar valores compartidos
                    if key == "join_key":
                        join_key_names.add(nm.lower())

        node_info[nname] = {"type": ntype, "in": in_cols, "out": out_cols}

    # --- PROPAGACION upstream: los SOURCE deben tener las columnas que sus
    # consumidores downstream referencian (join keys, sort keys, in. de reformats).
    # Construimos el mapa padres->hijos y propagamos las columnas de entrada de
    # cada hijo hacia sus padres (recursivo, hasta los SOURCE).
    children = {}  # nname -> [nnames hijos]
    parents = {}   # nname -> [nnames padres]
    for e in edges:
        fr = id_to_name.get(str(e.get("from", "")).lower())
        to = id_to_name.get(str(e.get("to", "")).lower())
        if fr and to:
            children.setdefault(fr, []).append(to)
            parents.setdefault(to, []).append(fr)

    # Propagar: para cada nodo, sus columnas de entrada deben existir en sus padres.
    # Iteramos varias veces (hasta estabilizar) porque la cadena puede ser larga.
    for _ in range(len(node_info) + 2):
        changed = False
        for nname, info in node_info.items():
            # columnas que este nodo consume (entrada) + las que produce que vienen de un padre
            needed = dict(info["in"])
            for par in parents.get(nname, []):
                pinfo = node_info.get(par)
                if not pinfo:
                    continue
                # el padre debe poder entregar lo que este nodo necesita
                target = pinfo["out"] if pinfo["type"] != "SOURCE" else pinfo["out"]
                for k, col in needed.items():
                    if k not in target:
                        target[k] = col
                        changed = True
                    # tambien reflejar en la entrada del padre (para seguir propagando)
                    if k not in pinfo["in"]:
                        pinfo["in"][k] = col
                        changed = True
        if not changed:
            break

    # --- Construir resultado ---
    result = []
    for nname, info in node_info.items():
        ntype = info["type"]
        in_cols = list(info["in"].values())
        out_cols = list(info["out"].values())

        # Fallback generico si un SOURCE/SINK quedo sin columnas
        if ntype == "SOURCE" and not out_cols and not in_cols:
            out_cols = [_mk_col(n, t) for n, t in _GENERIC_COLUMNS]
        if ntype == "SINK" and not in_cols and not out_cols:
            in_cols = [_mk_col(n, t) for n, t in _GENERIC_COLUMNS]

        # SOURCE con esquema POBRE (solo la clave de join, u <=2 columnas): el .mp
        # no declara el resto de columnas de esa tabla, asi que downstream salen
        # NULL. Rellenamos con columnas genericas CON datos para que las salidas
        # no se vean vacias (mejora de fidelidad; los nombres genericos no adivinan
        # los reales del banco, que no estan en el grafo).
        if ntype == "SOURCE":
            base = out_cols or in_cols
            if base and len(base) <= 2:
                existing = {c["name"].lower() for c in base}
                for gn, gt in _GENERIC_COLUMNS:
                    if gn.lower() not in existing:
                        base.append(_mk_col(gn, gt))
                        existing.add(gn.lower())
                if out_cols:
                    out_cols = base
                else:
                    in_cols = base

        # Marcar columnas que son clave de JOIN → se generan con valores compartidos
        for col in in_cols + out_cols:
            if col["name"].lower() in join_key_names:
                col["join_key"] = True
            # Columnas comparadas numericamente en un filtro: tiparlas como numericas
            # y adjuntar el valor que satisface el filtro para no quedar en 0 filas.
            cons = num_constraints.get(col["name"].lower())
            if cons:
                col["type"] = cons["type"]
                if cons.get("type") == "string":
                    # Igualdad contra literal string: generamos ese valor exacto,
                    # pero SOLO si esta columna es de un SOURCE (el valor de entrada
                    # sí controla el filtro). En nodos intermedios el filtro evalua
                    # el valor producido por un reformat, no el de origen.
                    col["str_value"] = cons.get("str_value")
                    if cons.get("str_not_equal"):
                        col["str_not_equal"] = True
                    if ntype == "SOURCE":
                        col["str_value_src"] = True
                        col["pii"] = None  # el filtro manda sobre el PII enmascarado
                else:
                    col["num_satisfy"] = cons["satisfy"]
                    if cons.get("not_equal"):
                        col["num_not_equal"] = True
                    if cons.get("exact"):
                        col["num_exact"] = True
            else:
                # Sin constraint de filtro: si un transform castea esta columna a
                # decimal/int/date, tiparla asi para que el dato sintetico sea
                # compatible con el cast (evita decimal("STATUS_X")->NULL). No pisa
                # tipos ya especificos (p.ej. una date declarada en el .dml).
                ct = cast_types.get(col["name"].lower())
                if ct and col.get("type", "string") == "string":
                    col["type"] = ct["type"]
                    # La precision del cast (decimal(1) -> 1 digito) acota el valor
                    # sintetico para que no desborde y termine en NULL.
                    if ct.get("precision") is not None:
                        col["max_precision"] = ct["precision"]

        if ntype == "SOURCE":
            cols = out_cols or in_cols
            if cols:
                result.append({"node": nname, "node_type": ntype, "io": "input", "columns": cols})
        elif ntype == "SINK":
            cols = in_cols or out_cols
            if cols:
                result.append({"node": nname, "node_type": ntype, "io": "output", "columns": cols})
        else:
            if in_cols:
                result.append({"node": nname, "node_type": ntype, "io": "input", "columns": in_cols})
            if out_cols:
                result.append({"node": nname, "node_type": ntype, "io": "output", "columns": out_cols})

    return result


# Palabras que no son nombres de columna al escanear expresiones
_SQL_KEYWORDS = {
    "cast", "as", "to_date", "to_timestamp", "int", "integer", "string", "decimal",
    "date", "datetime", "when", "then", "else", "end", "case", "and", "or", "not",
    "null", "is", "coalesce", "lit", "col", "expr", "trim", "lpad", "rpad",
    "substring", "concat", "size", "current_date", "current_timestamp", "yyyy",
    "mm", "dd", "true", "false",
}


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


def _join_key_pool(col_name, size=8):
    """Pool determinístico de valores para una clave de join.
    El mismo nombre de columna produce SIEMPRE el mismo pool, así distintas
    fuentes que se unen por esa clave comparten valores y el join empareja."""
    prefix = re.sub(r'[^A-Za-z0-9]', '', col_name).upper()[:6] or "KEY"
    return [f"{prefix}{i:04d}" for i in range(1, size + 1)]


def _gen_value(col, rng, row_idx):
    """Genera un valor sintético para una columna según tipo y PII."""
    # Constraint de igualdad contra literal STRING (col == 'Y') SOLO para columnas
    # de SOURCE (str_value_src). Para columnas calculadas en medio del pipeline no
    # aplica, porque el filtro evalua el valor PRODUCIDO por un reformat, no el de
    # entrada; forzar el dato de origen ahi no ayuda y puede romper otras ramas.
    sv = col.get("str_value")
    if sv is not None and col.get("str_value_src"):
        if col.get("str_not_equal"):
            return (sv + "_X") if isinstance(sv, str) else sv
        return sv

    # PRIORIDAD MAXIMA: constraint numerico de un filtro. Si el filtro compara esta
    # columna contra un numero, generamos valores que SATISFAGAN el filtro; de lo
    # contrario la prueba queda en 0 filas (el filtro descarta todo). Esto manda
    # incluso sobre join_key y PII: sin filas que pasen, no hay salida que revisar.
    satisfy = col.get("num_satisfy")
    if satisfy is not None:
        is_dec = col.get("type") == "decimal" or isinstance(satisfy, float)
        if col.get("num_not_equal"):
            # Operador '!=': cualquier valor distinto del literal cumple.
            base = int(satisfy) if not is_dec else satisfy
            delta = rng.randint(1, 500)
            return (base + delta) if not is_dec else round(base + delta, 2)
        if col.get("num_exact"):
            # Operador '=='/'=': debe ser EXACTAMENTE el valor (si no, el filtro
            # descarta la fila). Generamos el valor objetivo en todas las filas.
            return int(satisfy) if not is_dec else round(float(satisfy), 2)
        base = satisfy
        # Si tambien es clave de join, usamos un pool pequeno DETERMINISTICO (para
        # que empareje entre fuentes) pero numerico y dentro del rango que cumple.
        if col.get("join_key"):
            pool_size = 8
            idx = row_idx % pool_size
            return int(base) + idx if not is_dec else round(base + idx, 2)
        if is_dec:
            return round(base + rng.uniform(0, 500), 2)
        return int(base) + rng.randint(0, 500)

    # Clave de JOIN: valor de un pool compartido pequeño (para que empareje entre fuentes).
    # Tiene prioridad sobre PII para no romper el emparejamiento del join.
    if col.get("join_key"):
        pool = _join_key_pool(col.get("name", "key"))
        return pool[row_idx % len(pool)]

    pii = col.get("pii")
    if pii:
        return _redact_pii(pii, rng, row_idx)

    ctype = col.get("type", "string")
    name = col.get("name", "col")
    max_prec = col.get("max_precision")  # nº de digitos del cast destino (decimal(N))
    if ctype == "integer":
        if max_prec is not None:
            hi = max(1, (10 ** max(1, max_prec)) - 1)  # decimal(1)->9, decimal(3)->999
            return rng.randint(0, min(hi, 100000))
        return rng.randint(1, 100000)
    if ctype == "decimal":
        if max_prec is not None:
            # Acotar al numero de digitos del cast (p.ej. decimal(1) -> 0..9 enteros).
            hi = max(1, (10 ** max(1, max_prec)) - 1)
            if max_prec <= 1:
                return rng.randint(0, hi)  # decimal(1): sin decimales, cabe 0..9
            return round(rng.uniform(0, hi), 2)
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
        norm_col = {"name": name, "type": ctype, "pii": pii}
        # Preservar la marca de clave de join (valores compartidos entre fuentes)
        if col.get("join_key"):
            norm_col["join_key"] = True
        # Preservar constraints numericos de filtros (para generar valores que
        # satisfagan el filtro y no dejar las salidas en 0 filas).
        if col.get("num_satisfy") is not None:
            norm_col["num_satisfy"] = col["num_satisfy"]
        if col.get("num_not_equal"):
            norm_col["num_not_equal"] = True
        if col.get("num_exact"):
            norm_col["num_exact"] = True
        if col.get("str_value") is not None:
            norm_col["str_value"] = col["str_value"]
        if col.get("str_not_equal"):
            norm_col["str_not_equal"] = True
        if col.get("str_value_src"):
            norm_col["str_value_src"] = True
        # Preservar la precision del cast destino (decimal(N)) para acotar el valor
        # y que no desborde el tipo al aplicar el cast en el pipeline.
        if col.get("max_precision") is not None:
            norm_col["max_precision"] = col["max_precision"]
        norm_columns.append(norm_col)

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
