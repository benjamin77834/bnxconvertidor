# src/data_quality.py
"""
Comparador de CALIDAD DE DATOS entre dos salidas (p.ej. Ab Initio real vs el
PySpark/Python del convertidor).

Dado dos datasets (A = baseline / Ab Initio, B = convertidor), calcula por
columna estadisticas (count, nulls, media, mediana, varianza, min/max,
percentiles, cardinalidad) y las COMPARA:

  - distribucional: diferencia de media/varianza/percentiles por columna.
  - por llave (opcional): aparea filas por una columna id y mide % de celdas
    identicas por columna.

Produce un reporte estructurado (dict) con un VEREDICTO global y por columna,
que se puede guardar (JSON) y exportar a CSV/HTML. Sin dependencias pesadas:
usa el csv stdlib + estadistica propia (no requiere pandas, aunque lo usa si
esta disponible para parquet).
"""
import csv
import io
import json
import math
import statistics as _st
from datetime import datetime


# ---------------------------------------------------------------------------
# Carga de datos (CSV siempre; parquet si hay pandas)
# ---------------------------------------------------------------------------
def load_table(raw_bytes, filename=""):
    """Carga un dataset a (columns:list[str], rows:list[list]). Soporta CSV
    (stdlib) y parquet (si pandas+pyarrow estan instalados)."""
    name = (filename or "").lower()
    if name.endswith(".parquet") or raw_bytes[:4] == b"PAR1":
        try:
            import pandas as pd
            df = pd.read_parquet(io.BytesIO(raw_bytes))
            cols = [str(c) for c in df.columns]
            rows = df.astype(object).where(df.notna(), None).values.tolist()
            return cols, rows
        except Exception as e:
            raise ValueError(f"No se pudo leer el parquet (requiere pandas+pyarrow): {e}")
    # CSV / texto
    text = None
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = raw_bytes.decode(enc)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    if text is None:
        text = raw_bytes.decode("latin-1", errors="replace")
    # Detectar separador (coma, punto y coma o tab).
    sample = text[:4000]
    delim = ","
    for d in (",", ";", "\t", "|"):
        if sample.count(d) > sample.count(delim):
            delim = d
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    rows = list(reader)
    if not rows:
        return [], []
    cols = [c.strip() for c in rows[0]]
    data = rows[1:]
    return cols, data


# ---------------------------------------------------------------------------
# Estadistica por columna
# ---------------------------------------------------------------------------
def _to_float(v):
    if v is None:
        return None
    try:
        s = str(v).strip().replace(",", "")
        if s == "":
            return None
        return float(s)
    except (ValueError, TypeError):
        return None


def _percentile(sorted_vals, p):
    """Percentil p (0-100) de una lista YA ordenada (interpolacion lineal)."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def column_stats(values):
    """Estadisticas de una columna (lista de valores crudos). Decide si es
    numerica (>=80% convertibles a float) y calcula metricas acordes."""
    n = len(values)
    nulls = sum(1 for v in values if v is None or str(v).strip() == "")
    non_null = [v for v in values if v is not None and str(v).strip() != ""]
    nums = [_to_float(v) for v in non_null]
    nums = [x for x in nums if x is not None]
    is_numeric = non_null and (len(nums) / len(non_null) >= 0.8)

    stats = {
        "count": n,
        "nulls": nulls,
        "null_pct": round(100.0 * nulls / n, 2) if n else 0.0,
        "distinct": len(set(str(v) for v in non_null)),
        "numeric": bool(is_numeric),
    }
    if is_numeric and nums:
        s = sorted(nums)
        stats.update({
            "mean": round(_st.fmean(nums), 6),
            "median": round(_st.median(nums), 6),
            "stdev": round(_st.pstdev(nums), 6) if len(nums) > 1 else 0.0,
            "variance": round(_st.pvariance(nums), 6) if len(nums) > 1 else 0.0,
            "min": round(s[0], 6),
            "max": round(s[-1], 6),
            "p25": round(_percentile(s, 25), 6),
            "p50": round(_percentile(s, 50), 6),
            "p75": round(_percentile(s, 75), 6),
            "p90": round(_percentile(s, 90), 6),
            "p99": round(_percentile(s, 99), 6),
        })
    else:
        # Categorica: top valores por frecuencia.
        freq = {}
        for v in non_null:
            k = str(v)
            freq[k] = freq.get(k, 0) + 1
        top = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:5]
        stats["top_values"] = [{"value": k, "count": c} for k, c in top]
    return stats


def _col_values(columns, rows, col):
    idx = columns.index(col)
    return [(r[idx] if idx < len(r) else None) for r in rows]


# ---------------------------------------------------------------------------
# Comparacion
# ---------------------------------------------------------------------------
def _pct_diff(a, b):
    """Diferencia relativa (%) entre dos numeros, robusta a 0."""
    if a is None or b is None:
        return None
    if a == 0 and b == 0:
        return 0.0
    denom = max(abs(a), abs(b), 1e-9)
    return round(100.0 * abs(a - b) / denom, 2)


def compare(colsA, rowsA, colsB, rowsB, key=None, tol_pct=5.0):
    """Compara dos datasets. Devuelve el reporte estructurado.

    key: nombre de columna comun para apareo fila-a-fila (opcional).
    tol_pct: tolerancia (%) de diferencia de media para marcar una columna OK.
    """
    setA, setB = set(colsA), set(colsB)
    common = [c for c in colsA if c in setB]
    only_a = [c for c in colsA if c not in setB]
    only_b = [c for c in colsB if c not in setA]

    columns_report = []
    n_ok = 0
    for c in common:
        va = _col_values(colsA, rowsA, c)
        vb = _col_values(colsB, rowsB, c)
        sa = column_stats(va)
        sb = column_stats(vb)
        entry = {"column": c, "A": sa, "B": sb, "numeric": sa.get("numeric") and sb.get("numeric")}
        if entry["numeric"]:
            entry["diff"] = {
                "mean_pct": _pct_diff(sa.get("mean"), sb.get("mean")),
                "stdev_pct": _pct_diff(sa.get("stdev"), sb.get("stdev")),
                "p50_pct": _pct_diff(sa.get("p50"), sb.get("p50")),
                "p90_pct": _pct_diff(sa.get("p90"), sb.get("p90")),
            }
            md = entry["diff"]["mean_pct"]
            entry["status"] = "ok" if (md is not None and md <= tol_pct) else "drift"
        else:
            # Categorica: comparar cardinalidad y % de nulos.
            entry["diff"] = {
                "distinct_a": sa.get("distinct"), "distinct_b": sb.get("distinct"),
                "null_pct_a": sa.get("null_pct"), "null_pct_b": sb.get("null_pct"),
            }
            same_card = sa.get("distinct") == sb.get("distinct")
            same_null = abs(sa.get("null_pct", 0) - sb.get("null_pct", 0)) <= tol_pct
            entry["status"] = "ok" if (same_card and same_null) else "drift"
        if entry["status"] == "ok":
            n_ok += 1
        columns_report.append(entry)

    # Apareo por llave (opcional): % de celdas identicas por columna.
    key_report = None
    if key and key in setA and key in setB:
        ia, ib = colsA.index(key), colsB.index(key)
        mapA = {}
        for r in rowsA:
            if ia < len(r):
                mapA[str(r[ia])] = r
        matched = 0
        cell_match = {c: 0 for c in common}
        cell_total = {c: 0 for c in common}
        for r in rowsB:
            if ib >= len(r):
                continue
            k = str(r[ib])
            ra = mapA.get(k)
            if ra is None:
                continue
            matched += 1
            for c in common:
                ca, cb = colsA.index(c), colsB.index(c)
                av = str(ra[ca]) if ca < len(ra) else ""
                bv = str(r[cb]) if cb < len(r) else ""
                cell_total[c] += 1
                if av == bv:
                    cell_match[c] += 1
        key_report = {
            "key": key,
            "matched_rows": matched,
            "rows_a": len(rowsA), "rows_b": len(rowsB),
            "columns": [
                {"column": c,
                 "match_pct": round(100.0 * cell_match[c] / cell_total[c], 2) if cell_total[c] else None}
                for c in common
            ],
        }

    n_common = len(common)
    verdict = {
        "columns_total": n_common,
        "columns_ok": n_ok,
        "columns_drift": n_common - n_ok,
        "only_in_a": only_a,
        "only_in_b": only_b,
        "rows_a": len(rowsA),
        "rows_b": len(rowsB),
        "quality_pct": round(100.0 * n_ok / n_common, 1) if n_common else 0.0,
    }
    verdict["grade"] = (
        "A" if verdict["quality_pct"] >= 95 and not only_a and not only_b else
        "B" if verdict["quality_pct"] >= 85 else
        "C" if verdict["quality_pct"] >= 70 else "D")

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "verdict": verdict,
        "columns": columns_report,
        "key_compare": key_report,
        "tol_pct": tol_pct,
    }


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
def report_to_csv(report):
    """CSV plano de las metricas por columna (una fila por columna)."""
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow([
        "column", "status", "numeric",
        "A_count", "A_nulls", "A_mean", "A_stdev", "A_p50", "A_p90", "A_distinct",
        "B_count", "B_nulls", "B_mean", "B_stdev", "B_p50", "B_p90", "B_distinct",
        "mean_diff_pct", "stdev_diff_pct",
    ])
    for e in report.get("columns", []):
        a, b, d = e.get("A", {}), e.get("B", {}), e.get("diff", {})
        w.writerow([
            e.get("column"), e.get("status"), e.get("numeric"),
            a.get("count"), a.get("nulls"), a.get("mean"), a.get("stdev"), a.get("p50"), a.get("p90"), a.get("distinct"),
            b.get("count"), b.get("nulls"), b.get("mean"), b.get("stdev"), b.get("p50"), b.get("p90"), b.get("distinct"),
            d.get("mean_pct"), d.get("stdev_pct"),
        ])
    return out.getvalue()


def report_to_html(report, title="Comparación de calidad de datos"):
    """Reporte HTML autocontenido (imprimible a PDF)."""
    v = report.get("verdict", {})
    grade_color = {"A": "#16a34a", "B": "#65a30d", "C": "#d97706", "D": "#dc2626"}.get(v.get("grade"), "#64748b")
    rows_html = []
    for e in report.get("columns", []):
        a, b, d = e.get("A", {}), e.get("B", {}), e.get("diff", {})
        st_color = "#16a34a" if e.get("status") == "ok" else "#dc2626"
        if e.get("numeric"):
            cells = (f"<td>{a.get('mean','')}</td><td>{b.get('mean','')}</td>"
                     f"<td>{d.get('mean_pct','')}%</td>"
                     f"<td>{a.get('stdev','')}</td><td>{b.get('stdev','')}</td>"
                     f"<td>{a.get('p50','')}</td><td>{b.get('p50','')}</td>")
        else:
            cells = (f"<td>cat</td><td>cat</td><td>-</td>"
                     f"<td>{a.get('distinct','')}</td><td>{b.get('distinct','')}</td>"
                     f"<td>{a.get('null_pct','')}%</td><td>{b.get('null_pct','')}%</td>")
        rows_html.append(
            f"<tr><td><b>{e.get('column')}</b></td>"
            f"<td style='color:{st_color};font-weight:700'>{e.get('status','').upper()}</td>{cells}</tr>")
    key_html = ""
    if report.get("key_compare"):
        kc = report["key_compare"]
        kcols = "".join(
            f"<tr><td>{c['column']}</td><td>{c['match_pct']}%</td></tr>"
            for c in kc.get("columns", []))
        key_html = f"""
        <h3>Apareo por llave: {kc.get('key')}</h3>
        <p>Filas apareadas: <b>{kc.get('matched_rows')}</b> (A={kc.get('rows_a')}, B={kc.get('rows_b')})</p>
        <table><tr><th>Columna</th><th>% celdas idénticas</th></tr>{kcols}</table>"""
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>{title}</title><style>
  body{{font-family:system-ui,Segoe UI,Arial;margin:28px;color:#0f172a}}
  h1{{margin:0 0 4px}} .sub{{color:#64748b;font-size:13px}}
  .grade{{display:inline-block;font-size:40px;font-weight:800;color:{grade_color};
    border:3px solid {grade_color};border-radius:12px;padding:4px 18px;margin:12px 0}}
  table{{border-collapse:collapse;width:100%;margin:12px 0;font-size:12px}}
  th,td{{border:1px solid #e2e8f0;padding:6px 8px;text-align:left}}
  th{{background:#f1f5f9}}
  .kpi{{display:inline-block;margin-right:24px}} .kpi b{{font-size:20px}}
</style></head><body>
<h1>{title}</h1>
<div class="sub">Generado: {report.get('generated_at','')} · A = baseline (Ab Initio) · B = convertidor</div>
<div class="grade">{v.get('grade','?')}</div>
<div>
  <span class="kpi">Calidad<br><b>{v.get('quality_pct',0)}%</b></span>
  <span class="kpi">Columnas OK<br><b>{v.get('columns_ok',0)}/{v.get('columns_total',0)}</b></span>
  <span class="kpi">Con drift<br><b>{v.get('columns_drift',0)}</b></span>
  <span class="kpi">Filas A/B<br><b>{v.get('rows_a',0)} / {v.get('rows_b',0)}</b></span>
</div>
{"<p style='color:#dc2626'>Solo en A: " + ", ".join(v.get('only_in_a',[])) + "</p>" if v.get('only_in_a') else ""}
{"<p style='color:#dc2626'>Solo en B: " + ", ".join(v.get('only_in_b',[])) + "</p>" if v.get('only_in_b') else ""}
<h3>Comparación por columna</h3>
<table>
  <tr><th>Columna</th><th>Estado</th><th>media A</th><th>media B</th><th>Δ media</th>
      <th>stdev A</th><th>stdev B</th><th>p50 A</th><th>p50 B</th></tr>
  {''.join(rows_html)}
</table>
{key_html}
</body></html>"""
