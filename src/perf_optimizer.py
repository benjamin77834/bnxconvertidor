# -*- coding: utf-8 -*-
# src/perf_optimizer.py
"""
Optimizador de performance por REGLAS para el PySpark generado por BNX.

No usa IA. Aplica transformaciones deterministas y seguras de Spark que NO
cambian la logica del job (mismas filas/columnas de salida) pero mejoran el
rendimiento. Cada regla registra un cambio explicable para mostrarlo en la UI.

Reglas implementadas:
  1. CACHE de DataFrames reusados: si un *_df se usa como fuente en 2+ nodos
     hijos (tipico de los Replicate de Ab Initio), se materializa con .cache()
     para no recomputar el linaje en cada rama.
  2. BROADCAST en joins con lado pequeno: si el lado derecho de un join proviene
     de un catalogo/lookup (nombre contiene cat, lkp, lookup, ref, dim, mapeo),
     se envuelve con broadcast() para evitar el shuffle del lado grande.
  3. COALESCE antes de escrituras: .write...parquet(...) -> .coalesce(1).write...
     para reducir el numero de archivos de salida (menos overhead de I/O).

La funcion principal `optimize_pyspark(code)` devuelve:
  {
    "code": <str optimizado>,
    "changes": [{"rule","target","detail","count"}],
    "total_changes": int,
    "original_lines": int,
    "optimized_lines": int,
    "summary": {"cache_reused","broadcast_join","coalesce_write"},
  }
"""
import re
from collections import defaultdict


# Palabras que sugieren que un DataFrame es un catalogo/lookup pequeno (apto broadcast).
_SMALL_HINTS = ("cat_", "lkp", "lookup", "_ref", "ref_", "dim_", "_dim",
                "catalogo", "catalog", "mapeo", "map_", "_map", "cat_mapeo")


def _df_assign_target(line):
    """Si la linea es 'X_df = ...', devuelve 'X_df', si no None."""
    m = re.match(r'^\s*([A-Za-z_]\w*_df)\s*=\s*', line)
    return m.group(1) if m else None


def _count_source_usage(lines):
    """Cuenta cuantas veces cada *_df es usado como FUENTE (lado derecho) en
    todo el script. Sirve para decidir que DataFrames conviene cachear."""
    usage = defaultdict(int)
    for line in lines:
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        target = _df_assign_target(line)
        rhs = line.split('=', 1)[1] if ('=' in line and target) else line
        for df in set(re.findall(r'\b([A-Za-z_]\w*_df)\b', rhs)):
            if df != target:
                usage[df] += 1
    return usage


def _looks_small(df_name):
    n = df_name.lower()
    return any(h in n for h in _SMALL_HINTS)


def optimize_pyspark(code):
    """Aplica las reglas de performance al codigo PySpark. Devuelve dict."""
    if not code or not code.strip():
        return {"code": code or "", "changes": [], "total_changes": 0,
                "original_lines": 0, "optimized_lines": 0,
                "summary": {"cache_reused": 0, "broadcast_join": 0, "coalesce_write": 0}}

    lines = code.split("\n")
    original_lines = len(lines)
    changes = []

    usage = _count_source_usage(lines)

    # DataFrames candidatos a cache: usados como fuente 2+ veces y producto de una
    # transformacion (no un passthrough trivial X_df = Y_df, que no aporta linaje).
    produced_by = {}
    for line in lines:
        tgt = _df_assign_target(line)
        if tgt:
            produced_by[tgt] = line
    # Solo cacheamos DataFrames reusados cuyo linaje sea COSTOSO (join, groupBy/agg,
    # dropDuplicates, Window/row_number). Cachear un simple reformat/withColumn no
    # compensa el costo de memoria; cachear un shuffle si evita recomputarlo N veces.
    _costly_re = re.compile(r'\.(join|groupBy|agg|dropDuplicates|distinct)\(|row_number\(|Window\.')
    cache_candidates = set()
    for df, n in usage.items():
        if n >= 2 and df in produced_by:
            rhs = produced_by[df].split('=', 1)[1].strip()
            is_passthrough = bool(re.match(r'^[A-Za-z_]\w*_df\s*(#.*)?$', rhs))
            if is_passthrough:
                continue
            if not _costly_re.search(produced_by[df]):
                continue
            cache_candidates.add(df)

    # --- Regla 2: broadcast en joins con lado derecho pequeno (lookup/catalogo) ---
    join_re = re.compile(
        r'^(\s*)([A-Za-z_]\w*_df)\s*=\s*([A-Za-z_]\w*_df)\.join\(\s*([A-Za-z_]\w*_df)\s*,\s*(.*)$'
    )
    out = []
    join_broadcast_count = 0
    for line in lines:
        m = join_re.match(line)
        if m and 'broadcast(' not in line:
            indent, tgt, left, right, rest = m.groups()
            if _looks_small(right):
                out.append(f'{indent}{tgt} = {left}.join(broadcast({right}), {rest}')
                join_broadcast_count += 1
                changes.append({
                    "rule": "broadcast_join",
                    "target": tgt,
                    "detail": f"broadcast({right}): join con catalogo/lookup pequeno evita el shuffle del lado grande",
                    "count": 1,
                })
                continue
        out.append(line)
    lines = out

    # --- Regla 3: coalesce(1) antes de escrituras ---
    write_re = re.compile(r'^(\s*)([A-Za-z_]\w*_df)(\.write\b.*)$')
    out = []
    coalesce_count = 0
    for line in lines:
        m = write_re.match(line)
        if m and '.coalesce(' not in line and '_bnx_save_output' not in line:
            indent, df, rest = m.groups()
            out.append(f'{indent}{df}.coalesce(1){rest}')
            coalesce_count += 1
            changes.append({
                "rule": "coalesce_write",
                "target": df,
                "detail": "coalesce(1) antes de escribir: reduce archivos de salida y overhead de I/O",
                "count": 1,
            })
            continue
        out.append(line)
    lines = out

    # --- Regla 1: cache() en DataFrames reusados 2+ veces ---
    out = []
    cache_applied = set()
    for line in lines:
        out.append(line)
        tgt = _df_assign_target(line)
        if tgt and tgt in cache_candidates and tgt not in cache_applied:
            if '.cache(' in line or '.persist(' in line:
                cache_applied.add(tgt)
                continue
            indent = line[:len(line) - len(line.lstrip())]
            out.append(f'{indent}{tgt} = {tgt}.cache()  # BNX-PERF: reusado {usage[tgt]}x, se materializa una sola vez')
            cache_applied.add(tgt)

    cache_count = len(cache_applied)
    if cache_count:
        changes.insert(0, {
            "rule": "cache_reused",
            "target": ", ".join(sorted(cache_applied)[:6]) + (" ..." if cache_count > 6 else ""),
            "detail": f"{cache_count} DataFrame(s) reusados por varios nodos se cachean para no recomputar el linaje",
            "count": cache_count,
        })

    optimized = "\n".join(out)
    total = cache_count + join_broadcast_count + coalesce_count

    return {
        "code": optimized,
        "changes": changes,
        "total_changes": total,
        "original_lines": original_lines,
        "optimized_lines": len(out),
        "summary": {
            "cache_reused": cache_count,
            "broadcast_join": join_broadcast_count,
            "coalesce_write": coalesce_count,
        },
    }
