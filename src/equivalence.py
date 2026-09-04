# src/equivalence.py
"""
Validacion de EQUIVALENCIA DE DATOS entre la salida del PySpark generado y una
salida de REFERENCIA (la que produce Ab Initio en produccion).

El objetivo es probar correctitud SEMANTICA, no solo que el codigo compile o que
tenga el mismo numero de filas. Se compara a tres niveles, de menor a mayor rigor:

  1. Esquema   — mismo conjunto de columnas (orden irrelevante).
  2. Conteo    — mismo numero de filas.
  3. Contenido — mismas filas (multiset, orden de filas irrelevante).

El contenido se compara como MULTISET (bolsa) de filas: dos salidas son iguales si
tienen exactamente las mismas filas con las mismas multiplicidades, sin importar
el orden en que Spark las haya producido. Esto refleja la semantica de un dataset
sin ORDER BY explicito.

Uso tipico:
    from src.equivalence import compare_tables, compare_outputs
    rep = compare_tables(actual_rows, expected_rows,
                         actual_cols=[...], expected_cols=[...])
    # rep["equivalent"] -> bool ; rep["schema"|"count"|"content"] -> detalle
"""

import csv as _csv
import io as _io
import hashlib as _hashlib
from collections import Counter


# ---------------------------------------------------------------------------
# Normalizacion de valores y filas
# ---------------------------------------------------------------------------
def _norm_value(v):
    """Normaliza un valor escalar para comparar sin ruido de formato.

    - None y "" se consideran el MISMO valor vacio (Ab Initio y Spark difieren en
      como serializan un nulo a CSV; tratarlos igual evita falsos negativos).
    - Numeros con formato equivalente colapsan: '1.0' == '1', '1.50' == '1.5'.
    - Strings: se recorta whitespace de los extremos.
    """
    if v is None:
        return ""
    s = str(v).strip()
    if s == "":
        return ""
    # Colapsar numeros equivalentes (1.0 == 1, 1.50 == 1.5, -0 == 0).
    try:
        f = float(s)
        if f == int(f):
            return str(int(f))
        # normalizar quitando ceros de cola sin perder precision razonable
        return ("%.10f" % f).rstrip("0").rstrip(".")
    except (ValueError, OverflowError):
        return s


def _row_key(row, columns):
    """Clave canonica de una fila: columnas ordenadas alfabeticamente, valores
    normalizados. Independiente del orden de columnas de origen."""
    cols = sorted(columns)
    parts = []
    for c in cols:
        parts.append(c + "=" + _norm_value(row.get(c)))
    return chr(1).join(parts)


def _rows_multiset(rows, columns):
    """Counter de claves de fila (multiset). Orden de filas irrelevante."""
    return Counter(_row_key(r, columns) for r in rows)


def content_checksum(rows, columns):
    """Checksum de contenido order-insensitive, MISMA formula que el harness
    (_bnx_content_checksum en test_runner): suma conmutativa de sha1 por fila +
    firma de esquema. Permite comparar sin materializar todas las filas."""
    cols = sorted(columns)
    acc = 0
    n = 0
    for r in rows:
        parts = []
        for c in cols:
            v = r.get(c)
            parts.append(c + "=" + (chr(0) + "NULL" + chr(0) if v is None or str(v) == "" else str(v)))
        h = _hashlib.sha1(chr(1).join(parts).encode("utf-8", "replace")).digest()
        acc = (acc + int.from_bytes(h, "big")) % (1 << 160)
        n += 1
    schema_sig = _hashlib.sha1(("|".join(cols)).encode("utf-8")).hexdigest()[:12]
    return f"{acc:040x}.{schema_sig}", n


# ---------------------------------------------------------------------------
# Lectura de CSV (salidas volcadas por el harness / referencia del usuario)
# ---------------------------------------------------------------------------
def read_csv_rows(text_or_path, delimiter=","):
    """Lee un CSV (ruta o contenido) y devuelve (columns, rows).

    rows: list[dict]. Robusto a BOM y a filas con columnas faltantes.
    """
    if text_or_path is None:
        return [], []
    content = text_or_path
    # Si parece una ruta existente, leerla.
    try:
        import os as _os
        if isinstance(text_or_path, str) and "\n" not in text_or_path and _os.path.exists(text_or_path):
            with open(text_or_path, "r", encoding="utf-8", errors="replace", newline="") as fh:
                content = fh.read()
    except OSError:
        pass
    content = content.lstrip("\ufeff")
    reader = _csv.DictReader(_io.StringIO(content), delimiter=delimiter)
    cols = list(reader.fieldnames or [])
    rows = [dict(r) for r in reader]
    return cols, rows


# ---------------------------------------------------------------------------
# Comparacion de una tabla contra su referencia
# ---------------------------------------------------------------------------
def compare_tables(actual_rows, expected_rows, actual_cols=None,
                   expected_cols=None, sample_limit=20):
    """Compara una tabla generada contra su referencia.

    Devuelve un dict con:
      equivalent: bool  (True solo si esquema+conteo+contenido coinciden)
      schema:   {"match", "actual_cols", "expected_cols", "missing", "extra"}
      count:    {"match", "actual", "expected", "delta"}
      content:  {"match", "only_in_actual", "only_in_expected",
                 "sample_only_actual", "sample_only_expected"}
      score:    0..100 (ponderado esquema/conteo/contenido)
    """
    actual_rows = actual_rows or []
    expected_rows = expected_rows or []
    actual_cols = actual_cols or (list(actual_rows[0].keys()) if actual_rows else [])
    expected_cols = expected_cols or (list(expected_rows[0].keys()) if expected_rows else [])

    a_set, e_set = set(actual_cols), set(expected_cols)
    missing = sorted(e_set - a_set)   # columnas de la referencia que faltan
    extra = sorted(a_set - e_set)     # columnas de mas en la salida generada
    schema_match = not missing and not extra

    count_match = len(actual_rows) == len(expected_rows)

    # Contenido: comparar SOLO sobre las columnas comunes (si el esquema difiere,
    # el contenido sobre columnas compartidas sigue siendo informativo).
    common_cols = sorted(a_set & e_set)
    a_ms = _rows_multiset(actual_rows, common_cols)
    e_ms = _rows_multiset(expected_rows, common_cols)
    only_actual = a_ms - e_ms       # filas de mas / diferentes en la salida
    only_expected = e_ms - a_ms     # filas que la referencia tiene y faltan
    content_match = (not only_actual) and (not only_expected) and bool(common_cols)

    def _sample(counter):
        out = []
        for key, mult in list(counter.items())[:sample_limit]:
            row = {}
            for kv in key.split(chr(1)):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    row[k] = v
            out.append({"row": row, "count": mult})
        return out

    # Score ponderado: esquema 30%, conteo 20%, contenido 50%.
    score = (30 if schema_match else 30 * len(a_set & e_set) / max(1, len(e_set))) \
        + (20 if count_match else 0) \
        + (50 if content_match else 0)

    return {
        "equivalent": schema_match and count_match and content_match,
        "score": round(score, 1),
        "schema": {
            "match": schema_match,
            "actual_cols": sorted(actual_cols),
            "expected_cols": sorted(expected_cols),
            "missing": missing,
            "extra": extra,
        },
        "count": {
            "match": count_match,
            "actual": len(actual_rows),
            "expected": len(expected_rows),
            "delta": len(actual_rows) - len(expected_rows),
        },
        "content": {
            "match": content_match,
            "compared_columns": common_cols,
            "only_in_actual": int(sum(only_actual.values())),
            "only_in_expected": int(sum(only_expected.values())),
            "sample_only_actual": _sample(only_actual),
            "sample_only_expected": _sample(only_expected),
        },
    }


# ---------------------------------------------------------------------------
# Comparacion de un conjunto de SINKs (salida completa del grafo)
# ---------------------------------------------------------------------------
def _norm_name(s):
    """Normaliza un nombre de tabla/sink para emparejar salida vs referencia:
    minusculas, sin sufijo _df, sin extension .csv, solo alfanumerico."""
    import re
    s = (s or "").strip().lower()
    s = re.sub(r"\.csv$", "", s)
    s = re.sub(r"_df$", "", s)
    s = re.sub(r"[^a-z0-9]", "", s)
    return s


def match_sinks(actual_tables, expected_tables):
    """Empareja tablas de salida con tablas de referencia por nombre normalizado.

    actual_tables / expected_tables: dict {nombre: {"columns", "rows"}}
    Devuelve lista de (nombre_display, actual|None, expected|None).
    """
    a_norm = {_norm_name(k): (k, v) for k, v in actual_tables.items()}
    e_norm = {_norm_name(k): (k, v) for k, v in expected_tables.items()}
    pairs = []
    for nk in sorted(set(a_norm) | set(e_norm)):
        a = a_norm.get(nk)
        e = e_norm.get(nk)
        display = (a[0] if a else None) or (e[0] if e else None)
        pairs.append((display, a[1] if a else None, e[1] if e else None))
    return pairs


def compare_outputs(actual_tables, expected_tables, sample_limit=20):
    """Compara TODAS las salidas del grafo contra la referencia.

    actual_tables / expected_tables: dict {nombre_sink: {"columns":[...], "rows":[...]}}

    Devuelve:
      {"equivalent": bool,          # True solo si TODOS los sinks son equivalentes
       "score": 0..100,             # promedio de scores por sink
       "total_sinks", "equivalent_sinks",
       "tables": [{"name","status","detail": <compare_tables>}]}

    status por tabla:
      "equivalent" | "different" | "missing_output" | "missing_reference"
    """
    pairs = match_sinks(actual_tables, expected_tables)
    tables = []
    scores = []
    equivalent_count = 0

    for name, a, e in pairs:
        if a is None:
            tables.append({"name": name, "status": "missing_output",
                           "detail": None})
            scores.append(0.0)
            continue
        if e is None:
            tables.append({"name": name, "status": "missing_reference",
                           "detail": None})
            # No hay referencia -> no penaliza ni suma (se reporta aparte).
            continue
        rep = compare_tables(a.get("rows", []), e.get("rows", []),
                             a.get("columns"), e.get("columns"),
                             sample_limit=sample_limit)
        status = "equivalent" if rep["equivalent"] else "different"
        if rep["equivalent"]:
            equivalent_count += 1
        scores.append(rep["score"])
        tables.append({"name": name, "status": status, "detail": rep})

    comparable = [t for t in tables if t["status"] in ("equivalent", "different")]
    total = len(comparable)
    overall = round(sum(scores) / len(scores), 1) if scores else 0.0
    all_equiv = total > 0 and equivalent_count == total and \
        not any(t["status"] == "missing_output" for t in tables)

    return {
        "equivalent": all_equiv,
        "score": overall,
        "total_sinks": total,
        "equivalent_sinks": equivalent_count,
        "tables": tables,
    }
