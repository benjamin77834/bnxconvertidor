// reviewer.js — Analisis de calidad (estilo Sonar) del PySpark, 100% OFFLINE.
//
// Port a JavaScript de src/code_review.py (BNX). NO se conecta a ningun servidor
// ni requiere Python. Como JavaScript no tiene el modulo `ast` de Python, las
// reglas estructurales (except desnudo, except: pass, == None, funciones largas,
// print) se detectan por TEXTO/regex por linea — equivalentes practicos. Las
// reglas de texto de PySpark/seguridad se portan 1:1. Se conserva el modelo
// SonarQube completo (type, severidad, rule_key, deuda tecnica, ratings, gate).
//
// reviewCode(code) -> { ok, findings[], summary, sonar }

const SEVERITY_ORDER = { critical: 0, major: 1, minor: 2, info: 3 };

// built-ins de Python de alto riesgo si se usan como nombre (shadowing).
const BUILTINS = [
  "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes", "callable",
  "chr", "classmethod", "compile", "complex", "delattr", "dict", "dir", "divmod",
  "enumerate", "eval", "exec", "filter", "float", "format", "frozenset",
  "getattr", "globals", "hasattr", "hash", "help", "hex", "input", "int",
  "isinstance", "issubclass", "iter", "len", "list", "locals", "map", "max",
  "memoryview", "min", "next", "oct", "open", "ord", "pow", "print", "range",
  "repr", "reversed", "round", "set", "setattr", "slice", "sorted",
  "staticmethod", "str", "sum", "super", "tuple", "vars", "zip",
];
const SHADOW_IGNORE = new Set(["id", "type", "object", "property"]);
const SHADOW_BUILTINS = new Set(BUILTINS.filter((b) => !SHADOW_IGNORE.has(b)));
const SOFT_KEYWORDS = new Set(["_", "case", "match", "type"]);

// ---- Modelo Sonar ----
const CATEGORY_TO_TYPE = {
  bug: "BUG", security: "VULNERABILITY", performance: "CODE_SMELL", smell: "CODE_SMELL",
};
const SEVERITY_TO_SONAR = {
  critical: "BLOCKER", major: "CRITICAL", minor: "MAJOR", info: "MINOR",
};
const EFFORT_MIN = { critical: 30, major: 15, minor: 10, info: 5 };
const HOTSPOT_RULES = new Set(["security:HardcodedSecret", "security:JdbcPassword"]);
const SONAR_KEY = {
  "python:SyntaxError": "python:S2201",
  "python:BareExcept": "python:S5754",
  "python:SilentExcept": "python:S1066",
  "python:CompareToNone": "python:S5727",
  "python:LongFunction": "python:S138",
  "python:ShadowBuiltin": "python:S5806",
  "python:SoftKeywordName": "python:S1542",
  "python:PrintStatement": "python:S106",
  "python:LineTooLong": "python:S103",
  "python:TodoComment": "python:S1135",
  "spark:CollectToDriver": "python:S5042",
  "spark:ToPandas": "python:S5042",
  "spark:CountAction": "python:S3776",
  "security:HardcodedSecret": "python:S2068",
  "security:JdbcPassword": "python:S2068",
  "pyflakes": "python:S1481",
};

/** Indentacion (num. de espacios/tabs al inicio) de una linea. */
function indentOf(line) {
  const m = line.match(/^[ \t]*/);
  return m ? m[0].length : 0;
}

/** Reglas estructurales aproximadas por texto (sin AST). */
function structuralRules(lines) {
  const out = [];
  const shadowSeen = new Set();
  const funcStack = []; // { name, line, indent }

  const flushFunc = (f, endLine) => {
    const length = endLine - f.line;
    if (length > 60) {
      out.push({
        rule: "python:LongFunction", category: "smell", severity: "minor",
        line: f.line,
        message: `Funcion '${f.name}' muy larga (~${length} lineas). Recomendacion: dividir en funciones mas pequenas.`,
      });
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const lineNo = i + 1;
    const s = raw.trim();
    const ind = indentOf(raw);

    // Cierre de funciones cuyo cuerpo termino (linea no vacia con indent <=).
    if (s && !s.startsWith("#")) {
      while (funcStack.length && ind <= funcStack[funcStack.length - 1].indent
             && !/^\s*(def|async\s+def)\b/.test(raw)) {
        flushFunc(funcStack.pop(), lineNo - 1);
      }
    }

    // def / async def -> abrir funcion.
    const defM = raw.match(/^(\s*)(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(/);
    if (defM) {
      while (funcStack.length && ind <= funcStack[funcStack.length - 1].indent) {
        flushFunc(funcStack.pop(), lineNo - 1);
      }
      funcStack.push({ name: defM[2], line: lineNo, indent: ind });
    }

    // except: desnudo -> smell major.
    if (/^except\s*:/.test(s)) {
      out.push({
        rule: "python:BareExcept", category: "smell", severity: "major", line: lineNo,
        message: "'except:' sin tipo captura TODO (incluye KeyboardInterrupt). Recomendacion: capturar excepciones especificas.",
      });
    }

    // except ...: pass (en la misma linea o la siguiente no vacia).
    const excM = s.match(/^except\b.*:\s*(.*)$/);
    if (excM) {
      let bodyStr = excM[1].trim();
      if (bodyStr === "") {
        // mirar la siguiente linea no vacia
        for (let j = i + 1; j < lines.length; j++) {
          const ns = lines[j].trim();
          if (ns === "" || ns.startsWith("#")) continue;
          bodyStr = ns;
          break;
        }
      }
      if (/^pass\b/.test(bodyStr)) {
        out.push({
          rule: "python:SilentExcept", category: "bug", severity: "major", line: lineNo,
          message: "except con solo 'pass' silencia el error. Recomendacion: registrar (log) o manejar la excepcion.",
        });
      }
    }

    // == None / != None.
    if (/[=!]=\s*None\b/.test(s) || /\bNone\s*[=!]=/.test(s)) {
      out.push({
        rule: "python:CompareToNone", category: "smell", severity: "minor", line: lineNo,
        message: "Comparar con None usando ==/!=; recomendacion: usar 'is None'/'is not None'.",
      });
    }

    // shadowing de built-ins / soft keywords en asignaciones y for.
    if (!s.startsWith("#")) {
      const assignM = raw.match(/^\s*([A-Za-z_]\w*)\s*(?::[^=]+)?=(?!=)/);
      const forM = raw.match(/^\s*for\s+([A-Za-z_]\w*)\s+in\b/);
      const name = (assignM && assignM[1]) || (forM && forM[1]);
      if (name) {
        if (SHADOW_BUILTINS.has(name) && !shadowSeen.has("shadow:" + name)) {
          shadowSeen.add("shadow:" + name);
          out.push({
            rule: "python:ShadowBuiltin", category: "smell", severity: "major", line: lineNo,
            message: `'${name}' sombrea un built-in de Python; reasignarlo puede romper usos posteriores. Recomendacion: renombrar (p.ej. '${name}_').`,
          });
        } else if (SOFT_KEYWORDS.has(name) && !shadowSeen.has("soft:" + name)) {
          shadowSeen.add("soft:" + name);
          out.push({
            rule: "python:SoftKeywordName", category: "smell", severity: "minor", line: lineNo,
            message: `'${name}' es una palabra reservada 'suave' de Python; usarla como nombre es confuso. Recomendacion: elegir otro identificador.`,
          });
        }
      }
    }
  }
  // cerrar funciones abiertas al final del archivo.
  while (funcStack.length) flushFunc(funcStack.pop(), lines.length);
  return out;
}

/** Reglas por linea (regex) especificas de PySpark/ETL/seguridad. */
function textRules(code) {
  const out = [];
  const lines = code.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const lineNo = i + 1;
    const line = raw.trim();

    if (!line || line.startsWith("#")) {
      if (/\b(TODO|FIXME|XXX)\b/.test(raw)) {
        out.push({ rule: "python:TodoComment", category: "smell", severity: "info",
          line: lineNo, message: "Comentario TODO/FIXME: deuda tecnica pendiente." });
      }
      continue;
    }

    if (/\.collect\(\)/.test(line)) {
      out.push({ rule: "spark:CollectToDriver", category: "performance", severity: "major",
        line: lineNo, message: ".collect() trae TODO el DataFrame al driver; riesgo de memoria con volumen alto. Recomendacion: evitar o limitar." });
    }
    if (/\.toPandas\(\)/.test(line)) {
      out.push({ rule: "spark:ToPandas", category: "performance", severity: "major",
        line: lineNo, message: ".toPandas() materializa todo en el driver; usar solo con datos pequenos." });
    }
    if (/\.count\(\)/.test(line)) {
      out.push({ rule: "spark:CountAction", category: "performance", severity: "minor",
        line: lineNo, message: ".count() es una accion que recorre el DataFrame; evita llamarla repetidamente (cachea o reutiliza el valor)." });
    }
    if (/^print\s*\(/.test(line)) {
      out.push({ rule: "python:PrintStatement", category: "smell", severity: "info",
        line: lineNo, message: "print() en el job; en produccion es preferible logging." });
    }
    if (/(password|passwd|secret|api_key|access_key|token)\s*=\s*['"][^'"]+['"]/i.test(line)) {
      out.push({ rule: "security:HardcodedSecret", category: "security", severity: "critical",
        line: lineNo, message: "Posible credencial hardcodeada. Recomendacion: usar variables de entorno o un gestor de secretos." });
    }
    if (/\.option\(\s*['"]password['"]\s*,\s*['"][^'"]+['"]/i.test(line)) {
      out.push({ rule: "security:JdbcPassword", category: "security", severity: "critical",
        line: lineNo, message: "Password JDBC en claro. Recomendacion: externalizar la credencial." });
    }
    if (raw.length > 120) {
      out.push({ rule: "python:LineTooLong", category: "smell", severity: "info",
        line: lineNo, message: `Linea muy larga (${raw.length} chars > 120). Recomendacion: dividir.` });
    }
  }
  return out;
}

function sonarize(findings) {
  for (const f of findings) {
    const cat = f.category || "smell";
    const sev = f.severity || "info";
    const rule = f.rule || "";
    f.type = HOTSPOT_RULES.has(rule) ? "SECURITY_HOTSPOT" : (CATEGORY_TO_TYPE[cat] || "CODE_SMELL");
    f.sonar_severity = SEVERITY_TO_SONAR[sev] || "MINOR";
    f.rule_key = SONAR_KEY[rule] || rule;
    f.effort_min = EFFORT_MIN[sev] || 5;
  }
}

function fmtDebt(totalMin) {
  if (totalMin <= 0) return "0min";
  const days = Math.floor(totalMin / (8 * 60));
  const rem = totalMin % (8 * 60);
  const hours = Math.floor(rem / 60);
  const mins = rem % 60;
  const parts = [];
  if (days) parts.push(`${days}d`);
  if (hours) parts.push(`${hours}h`);
  if (mins) parts.push(`${mins}min`);
  return parts.length ? parts.join(" ") : "0min";
}

function rating(badCount, thresholds) {
  const letters = ["A", "B", "C", "D", "E"];
  const t = thresholds || [1, 2, 5, 10];
  if (badCount === 0) return "A";
  for (let i = 0; i < t.length; i++) {
    if (badCount < t[i]) return letters[Math.min(i + 1, 4)];
  }
  return "E";
}

function sonarReport(findings) {
  const byType = { BUG: 0, CODE_SMELL: 0, VULNERABILITY: 0, SECURITY_HOTSPOT: 0 };
  const bySev = { BLOCKER: 0, CRITICAL: 0, MAJOR: 0, MINOR: 0, INFO: 0 };
  let debtMin = 0;
  for (const f of findings) {
    const tp = f.type || "CODE_SMELL";
    byType[tp] = (byType[tp] || 0) + 1;
    const sv = f.sonar_severity || "MINOR";
    bySev[sv] = (bySev[sv] || 0) + 1;
    debtMin += f.effort_min || 0;
  }
  const bugs = byType.BUG, vulns = byType.VULNERABILITY;
  const hotspots = byType.SECURITY_HOTSPOT, smells = byType.CODE_SMELL;
  const blockers = bySev.BLOCKER;

  const conditions = [
    { metric: "bugs", op: "=", threshold: 0, actual: bugs, passed: bugs === 0 },
    { metric: "vulnerabilities", op: "=", threshold: 0, actual: vulns, passed: vulns === 0 },
    { metric: "blocker_issues", op: "=", threshold: 0, actual: blockers, passed: blockers === 0 },
  ];
  const gatePassed = conditions.every((c) => c.passed);

  return {
    quality_gate: gatePassed ? "PASSED" : "FAILED",
    quality_gate_conditions: conditions,
    counts: {
      bugs, vulnerabilities: vulns, security_hotspots: hotspots,
      code_smells: smells, total: findings.length,
    },
    by_severity: bySev,
    technical_debt: fmtDebt(debtMin),
    technical_debt_min: debtMin,
    ratings: {
      reliability: rating(bugs),
      security: rating(vulns),
      maintainability: debtMin <= 60 ? "A" : debtMin <= 240 ? "B" : debtMin <= 480 ? "C" : debtMin <= 960 ? "D" : "E",
      security_review: rating(hotspots),
    },
  };
}

function summary(findings) {
  const s = { total: findings.length, critical: 0, major: 0, minor: 0, info: 0,
    bug: 0, smell: 0, security: 0, performance: 0 };
  for (const f of findings) {
    s[f.severity] = (s[f.severity] || 0) + 1;
    s[f.category] = (s[f.category] || 0) + 1;
  }
  return s;
}

/** Analiza 'code' y devuelve { ok, findings, summary, sonar }. Nunca lanza. */
function reviewCode(code) {
  if (!code || !code.trim()) {
    return { ok: true, findings: [], summary: summary([]) };
  }
  const lines = code.split("\n");
  let findings = [];
  findings = findings.concat(structuralRules(lines));
  findings = findings.concat(textRules(code));

  // Ordenar por severidad y linea; deduplicar.
  findings.sort((a, b) => {
    const sa = SEVERITY_ORDER[a.severity] ?? 9;
    const sb = SEVERITY_ORDER[b.severity] ?? 9;
    if (sa !== sb) return sa - sb;
    return (a.line || 0) - (b.line || 0);
  });
  const seen = new Set();
  const uniq = [];
  for (const f of findings) {
    const key = `${f.rule}|${f.line || 0}|${(f.message || "").slice(0, 60)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    uniq.push(f);
  }
  sonarize(uniq);
  return { ok: true, findings: uniq, summary: summary(uniq), sonar: sonarReport(uniq) };
}

module.exports = { reviewCode };
