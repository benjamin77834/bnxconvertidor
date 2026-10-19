// optimizer.js — Motor de optimizacion PySpark por REGLAS, 100% OFFLINE.
//
// Port a JavaScript de src/perf_optimizer.py (BNX). NO se conecta a ningun
// servidor: la extngmc .vsix hace todo el trabajo localmente. Mismas reglas
// deterministas que no cambian la logica del job:
//   1. CACHE de DataFrames reusados 2+ veces con linaje costoso.
//   2. BROADCAST en joins con lado derecho pequeno (catalogo/lookup).
//   3. COALESCE(1) antes de escrituras.
//   + Fase de REDUCCION/limpieza (passthrough, select('*'), duplicados,
//     imports no usados, lineas en blanco).
//
// optimizePyspark(code, includeCoalesce=true) -> { code, changes, total_changes,
//   original_lines, optimized_lines, lines_removed, summary }

// Palabras que sugieren un DataFrame pequeno (apto broadcast).
const SMALL_HINTS = [
  "cat_", "lkp", "lookup", "_ref", "ref_", "dim_", "_dim",
  "catalogo", "catalog", "mapeo", "map_", "_map", "cat_mapeo",
];

/** Escapa una cadena para uso literal en una RegExp. */
function reEscape(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Si la linea es 'X_df = ...', devuelve 'X_df', si no null. */
function dfAssignTarget(line) {
  const m = line.match(/^\s*([A-Za-z_]\w*_df)\s*=\s*/);
  return m ? m[1] : null;
}

/** Cuenta cuantas veces cada *_df se usa como FUENTE (lado derecho). */
function countSourceUsage(lines) {
  const usage = Object.create(null);
  for (const line of lines) {
    const s = line.trim();
    if (!s || s.startsWith("#")) continue;
    const target = dfAssignTarget(line);
    const rhs = line.includes("=") && target ? line.split("=").slice(1).join("=") : line;
    const seen = new Set();
    const re = /\b([A-Za-z_]\w*_df)\b/g;
    let m;
    while ((m = re.exec(rhs)) !== null) seen.add(m[1]);
    for (const df of seen) {
      if (df !== target) usage[df] = (usage[df] || 0) + 1;
    }
  }
  return usage;
}

function looksSmall(dfName) {
  const n = dfName.toLowerCase();
  return SMALL_HINTS.some((h) => n.includes(h));
}

function isImportLine(line) {
  const s = line.trim();
  return s.startsWith("import ") || s.startsWith("from ");
}

/** Nombre local que introduce un import simple y seguro, o null. */
function importedName(line) {
  const s = line.trim();
  if (s.includes(",") || s.includes("*")) return null;
  let m = s.match(/^import\s+([\w.]+)(?:\s+as\s+(\w+))?\s*$/);
  if (m) return m[2] || m[1].split(".")[0];
  m = s.match(/^from\s+[\w.]+\s+import\s+(\w+)(?:\s+as\s+(\w+))?\s*$/);
  if (m) return m[2] || m[1];
  return null;
}

/** Fase de REDUCCION/limpieza. Devuelve { lines, changes, removed }. */
function reduceCode(lines) {
  const changes = [];

  // R2: 'X_df = Y_df.select("*")' -> 'X_df = Y_df' (para que R1 lo capture).
  const selStarRe = /^(\s*)([A-Za-z_]\w*_df)\s*=\s*([A-Za-z_]\w*_df)\.(?:select|selectExpr)\(\s*["']\*["']\s*\)\s*$/;
  lines = lines.map((line) => {
    const m = line.match(selStarRe);
    if (m) return `${m[1]}${m[2]} = ${m[3]}`;
    return line;
  });

  // R1: passthroughs 'X_df = Y_df' (solo colapsamos alias en minuscula).
  const passthroughRe = /^\s*([A-Za-z_]\w*_df)\s*=\s*([A-Za-z_]\w*_df)\s*(#.*)?$/;
  const aliasMap = Object.create(null);
  let removed = 0;
  let out = [];
  for (let line of lines) {
    const m = line.match(passthroughRe);
    if (m) {
      const tgt = m[1];
      let src = m[2];
      src = aliasMap[src] || src;
      if (tgt[0] === tgt[0].toLowerCase() && tgt[0] !== tgt[0].toUpperCase()) {
        aliasMap[tgt] = src;
        removed += 1;
        continue;
      }
    }
    const aliasKeys = Object.keys(aliasMap);
    if (aliasKeys.length && line.includes("=")) {
      const idx = line.indexOf("=");
      const lhs = line.slice(0, idx);
      let rhs = line.slice(idx + 1);
      for (const a of aliasKeys) {
        rhs = rhs.replace(new RegExp(`\\b${reEscape(a)}\\b`, "g"), aliasMap[a]);
      }
      line = lhs + "=" + rhs;
    } else if (aliasKeys.length) {
      for (const a of aliasKeys) {
        line = line.replace(new RegExp(`\\b${reEscape(a)}\\b`, "g"), aliasMap[a]);
      }
    }
    out.push(line);
  }
  lines = out;
  if (removed) {
    changes.push({
      rule: "dead_code",
      target: `${removed} alias`,
      detail: `${removed} asignacion(es) passthrough (X_df = Y_df, select('*')) eliminadas; usos reescritos`,
      count: removed,
    });
  }

  // R5: asignaciones IDENTICAS duplicadas consecutivas.
  const dedup = [];
  let dupRemoved = 0;
  let prevCode = null;
  for (const line of lines) {
    const s = line.trim();
    if (s && !s.startsWith("#") && s.includes("=") && s === prevCode) {
      dupRemoved += 1;
      continue;
    }
    if (s && !s.startsWith("#")) prevCode = s;
    dedup.push(line);
  }
  lines = dedup;
  if (dupRemoved) {
    changes.push({
      rule: "dead_code",
      target: `${dupRemoved} duplicada(s)`,
      detail: `${dupRemoved} linea(s) de asignacion identicas consecutivas eliminadas`,
      count: dupRemoved,
    });
    removed += dupRemoved;
  }

  // R6: imports NO usados (simples y seguros).
  const PROTECTED = ["import *", "SparkSession", "functions as F",
    "from pyspark.sql import", "SparkContext", "GlueContext"];
  const body = lines.filter((l) => !isImportLine(l)).join("\n");
  let importsRemoved = 0;
  const kept = [];
  for (const line of lines) {
    const name = importedName(line);
    if (name && !PROTECTED.some((p) => line.includes(p))) {
      if (!new RegExp(`\\b${reEscape(name)}\\b`).test(body)) {
        importsRemoved += 1;
        continue;
      }
    }
    kept.push(line);
  }
  lines = kept;
  if (importsRemoved) {
    changes.push({
      rule: "dead_code",
      target: `${importsRemoved} import(s)`,
      detail: `${importsRemoved} import(s) no usado(s) eliminado(s)`,
      count: importsRemoved,
    });
    removed += importsRemoved;
  }

  // R3: colapsar lineas en blanco consecutivas.
  const collapsed = [];
  let blank = false;
  for (const line of lines) {
    if (line.trim() === "") {
      if (blank) continue;
      blank = true;
    } else {
      blank = false;
    }
    collapsed.push(line);
  }
  lines = collapsed;

  return { lines, changes, removed };
}

/** Optimiza el PySpark por reglas. Puro texto, sin dependencias ni red. */
function optimizePyspark(code, includeCoalesce) {
  if (includeCoalesce === undefined) includeCoalesce = true;
  if (!code || !code.trim()) {
    return {
      code: code || "", changes: [], total_changes: 0,
      original_lines: 0, optimized_lines: 0,
      summary: { cache_reused: 0, broadcast_join: 0, coalesce_write: 0 },
    };
  }

  let lines = code.split("\n");
  const originalLines = lines.length;
  const changes = [];

  // Fase 0: REDUCCION.
  const red = reduceCode(lines);
  lines = red.lines;
  for (const c of red.changes) changes.push(c);
  const deadRemoved = red.removed;

  const usage = countSourceUsage(lines);

  // DataFrames producidos por una asignacion.
  const producedBy = Object.create(null);
  for (const line of lines) {
    const tgt = dfAssignTarget(line);
    if (tgt) producedBy[tgt] = line;
  }

  // Candidatos a cache: reusados 2+ y linaje COSTOSO (join/groupBy/agg/distinct/Window).
  const costlyRe = /\.(join|groupBy|agg|dropDuplicates|distinct)\(|row_number\(|Window\./;
  const cacheCandidates = new Set();
  for (const df of Object.keys(usage)) {
    const n = usage[df];
    if (n >= 2 && producedBy[df]) {
      const rhs = producedBy[df].split("=").slice(1).join("=").trim();
      const isPassthrough = /^[A-Za-z_]\w*_df\s*(#.*)?$/.test(rhs);
      if (isPassthrough) continue;
      if (!costlyRe.test(producedBy[df])) continue;
      cacheCandidates.add(df);
    }
  }

  // Regla 2: broadcast en joins con lado derecho pequeno.
  const joinRe = /^(\s*)([A-Za-z_]\w*_df)\s*=\s*([A-Za-z_]\w*_df)\.join\(\s*([A-Za-z_]\w*_df)\s*,\s*(.*)$/;
  let out = [];
  let joinBroadcastCount = 0;
  for (const line of lines) {
    const m = line.match(joinRe);
    if (m && !line.includes("broadcast(")) {
      const [, indent, tgt, left, right, rest] = m;
      if (looksSmall(right)) {
        out.push(`${indent}${tgt} = ${left}.join(broadcast(${right}), ${rest}`);
        joinBroadcastCount += 1;
        changes.push({
          rule: "broadcast_join",
          target: tgt,
          detail: `broadcast(${right}): join con catalogo/lookup pequeno evita el shuffle del lado grande`,
          count: 1,
        });
        continue;
      }
    }
    out.push(line);
  }
  lines = out;

  // Regla 3: coalesce(1) antes de escrituras.
  const writeRe = /^(\s*)([A-Za-z_]\w*_df)(\.write\b.*)$/;
  out = [];
  let coalesceCount = 0;
  for (const line of lines) {
    const m = line.match(writeRe);
    if (includeCoalesce && m && !line.includes(".coalesce(") && !line.includes("_bnx_save_output")) {
      const [, indent, df, rest] = m;
      out.push(`${indent}${df}.coalesce(1)${rest}`);
      coalesceCount += 1;
      changes.push({
        rule: "coalesce_write",
        target: df,
        detail: "coalesce(1) antes de escribir: reduce archivos de salida y overhead de I/O",
        count: 1,
      });
      continue;
    }
    out.push(line);
  }
  lines = out;

  // Regla 1: cache() en DataFrames reusados.
  out = [];
  const cacheApplied = new Set();
  for (const line of lines) {
    out.push(line);
    const tgt = dfAssignTarget(line);
    if (tgt && cacheCandidates.has(tgt) && !cacheApplied.has(tgt)) {
      if (line.includes(".cache(") || line.includes(".persist(")) {
        cacheApplied.add(tgt);
        continue;
      }
      const indent = line.slice(0, line.length - line.trimStart().length);
      out.push(`${indent}${tgt} = ${tgt}.cache()  # BNX-PERF: reusado ${usage[tgt]}x, se materializa una sola vez`);
      cacheApplied.add(tgt);
    }
  }

  const cacheCount = cacheApplied.size;
  if (cacheCount) {
    const names = [...cacheApplied].sort().slice(0, 6).join(", ") + (cacheCount > 6 ? " ..." : "");
    changes.unshift({
      rule: "cache_reused",
      target: names,
      detail: `${cacheCount} DataFrame(s) reusados por varios nodos se cachean para no recomputar el linaje`,
      count: cacheCount,
    });
  }

  const optimized = out.join("\n");
  const total = cacheCount + joinBroadcastCount + coalesceCount + deadRemoved;

  return {
    code: optimized,
    changes,
    total_changes: total,
    original_lines: originalLines,
    optimized_lines: out.length,
    lines_removed: Math.max(originalLines - out.length, 0),
    summary: {
      cache_reused: cacheCount,
      broadcast_join: joinBroadcastCount,
      coalesce_write: coalesceCount,
      dead_code_removed: deadRemoved,
    },
  };
}

module.exports = { optimizePyspark };
