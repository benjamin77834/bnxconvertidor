# src/code_review.py
"""Analisis de calidad (estilo Sonar) del PySpark generado, SOLO RECOMENDACIONES.

NO modifica el codigo. Devuelve una lista de hallazgos (bugs, code smells,
seguridad, performance) para mostrarlos en Data Sintetica, donde convergen todos
los flujos (Compiler, py2spark, COBOL, ALGOL).

Cero dependencias obligatorias: el analisis base usa el modulo 'ast' de la
stdlib. Si pyflakes esta instalado, se usa como complemento (import/vars sin
usar). Cada hallazgo trae: rule, severity (info|minor|major|critical), line,
message y category (bug|smell|security|performance).
"""
import ast
import builtins
import keyword
import re


_SEVERITY_ORDER = {"critical": 0, "major": 1, "minor": 2, "info": 3}

# Palabras reservadas de Python (keywords duros). Usarlas como identificador es
# un SyntaxError, pero las detectamos en texto por si vienen de codigo generado
# o de otro lenguaje embebido. Los soft keywords (match/case/type/_) SI pueden
# usarse como nombre, pero hacerlo es confuso -> smell.
_HARD_KEYWORDS = set(keyword.kwlist)
_SOFT_KEYWORDS = set(getattr(keyword, "softkwlist", ["_", "case", "match", "type"]))

# Built-ins de Python que, usados como nombre de variable/parametro/funcion,
# "sombrean" (shadow) el built-in y son fuente clasica de bugs. Es la regla
# estilo SonarLint (builtin shadowing). Se excluyen nombres triviales que casi
# nunca causan dano real para no generar ruido.
_BUILTINS = {b for b in dir(builtins) if not b.startswith("_")}
_SHADOW_IGNORE = {"id", "type", "object", "property"}  # muy comunes, bajo riesgo
_SHADOW_BUILTINS = _BUILTINS - _SHADOW_IGNORE


def review_code(code, language="python"):
    """Analiza 'code' y devuelve {ok, summary, findings[]}. Nunca lanza: si el
    codigo no parsea, lo reporta como un hallazgo critico de sintaxis."""
    findings = []
    if not code or not code.strip():
        return {"ok": True, "findings": [], "summary": _summary([])}

    # 1) Parseo AST. Si falla, es un bug critico (el codigo no es valido).
    tree = None
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        findings.append({
            "rule": "python:SyntaxError", "category": "bug", "severity": "critical",
            "line": e.lineno or 0,
            "message": f"El codigo no parsea: {e.msg}. Debe corregirse antes de ejecutar.",
        })
        return {"ok": False, "findings": findings, "summary": _summary(findings)}

    # 2) Reglas AST (stdlib, sin dependencias).
    findings += _ast_rules(tree, code)

    # 3) Reglas de texto/regex especificas de PySpark.
    findings += _text_rules(code)

    # 4) Complemento opcional con pyflakes (si esta instalado).
    findings += _pyflakes_rules(code)

    # Ordenar por severidad y linea; deduplicar.
    seen = set()
    uniq = []
    for f in sorted(findings, key=lambda x: (_SEVERITY_ORDER.get(x["severity"], 9), x.get("line", 0))):
        key = (f["rule"], f.get("line", 0), f["message"][:60])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(f)
    return {"ok": True, "findings": uniq, "summary": _summary(uniq)}


def _summary(findings):
    s = {"total": len(findings), "critical": 0, "major": 0, "minor": 0, "info": 0,
         "bug": 0, "smell": 0, "security": 0, "performance": 0}
    for f in findings:
        s[f["severity"]] = s.get(f["severity"], 0) + 1
        s[f["category"]] = s.get(f["category"], 0) + 1
    return s


def _ast_rules(tree, code):
    out = []

    # except: desnudo (captura todo, oculta errores) -> smell major.
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            out.append({
                "rule": "python:BareExcept", "category": "smell", "severity": "major",
                "line": node.lineno,
                "message": "'except:' sin tipo captura TODO (incluye KeyboardInterrupt). "
                           "Recomendacion: capturar excepciones especificas.",
            })

    # == None / != None -> deberia ser 'is None' (smell minor).
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(op, (ast.Eq, ast.NotEq)) and _is_none(comp):
                    out.append({
                        "rule": "python:CompareToNone", "category": "smell", "severity": "minor",
                        "line": node.lineno,
                        "message": "Comparar con None usando ==/!=; recomendacion: usar 'is None'/'is not None'.",
                    })

    # funciones muy largas (> 60 lineas) -> smell minor (complejidad).
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body:
                length = (node.body[-1].lineno - node.lineno)
                if length > 60:
                    out.append({
                        "rule": "python:LongFunction", "category": "smell", "severity": "minor",
                        "line": node.lineno,
                        "message": f"Funcion '{node.name}' muy larga (~{length} lineas). "
                                   "Recomendacion: dividir en funciones mas pequenas.",
                    })

    # TODO/FIXME en comentarios ya los capturamos por texto; aqui, 'pass' en except
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                out.append({
                    "rule": "python:SilentExcept", "category": "bug", "severity": "major",
                    "line": node.lineno,
                    "message": "except con solo 'pass' silencia el error. "
                               "Recomendacion: registrar (log) o manejar la excepcion.",
                })

    # Palabras reservadas / shadowing de built-ins (estilo SonarLint).
    out += _reserved_words_rules(tree)
    return out


def _reserved_words_rules(tree):
    """Detecta identificadores problematicos (estilo SonarLint):

    - python:ShadowBuiltin  : una variable/parametro/funcion se llama igual que
      un built-in (list, dict, str, sum, filter, input, ...). Sombrea el built-in
      y es fuente clasica de bugs. -> smell major.
    - python:SoftKeywordName: se usa un soft keyword (match, case, type, _) como
      nombre. Es legal pero confuso. -> smell minor.

    Se reporta cada nombre UNA sola vez (en su primera aparicion) para no inundar.
    """
    out = []
    seen = set()  # (clase, nombre) -> ya reportado

    def report(name, lineno):
        if not name or not isinstance(name, str):
            return
        if name in _SHADOW_BUILTINS:
            key = ("shadow", name)
            if key not in seen:
                seen.add(key)
                out.append({
                    "rule": "python:ShadowBuiltin", "category": "smell", "severity": "major",
                    "line": lineno or 0,
                    "message": f"'{name}' sombrea un built-in de Python; reasignarlo puede "
                               f"romper usos posteriores. Recomendacion: renombrar (p.ej. '{name}_').",
                })
        elif name in _SOFT_KEYWORDS:
            key = ("soft", name)
            if key not in seen:
                seen.add(key)
                out.append({
                    "rule": "python:SoftKeywordName", "category": "smell", "severity": "minor",
                    "line": lineno or 0,
                    "message": f"'{name}' es una palabra reservada 'suave' de Python; usarla como "
                               f"nombre es confuso. Recomendacion: elegir otro identificador.",
                })

    for node in ast.walk(tree):
        # Asignaciones: x = ...
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                for nm in _names_in_target(tgt):
                    report(nm, node.lineno)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            for nm in _names_in_target(node.target):
                report(nm, node.lineno)
        # Bucles: for x in ...
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            for nm in _names_in_target(node.target):
                report(nm, node.lineno)
        # Definiciones de funcion/clase y sus parametros.
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            report(node.name, node.lineno)
            a = node.args
            for arg in (list(a.args) + list(a.posonlyargs) + list(a.kwonlyargs)):
                report(arg.arg, arg.lineno)
            if a.vararg:
                report(a.vararg.arg, a.vararg.lineno)
            if a.kwarg:
                report(a.kwarg.arg, a.kwarg.lineno)
        elif isinstance(node, ast.ClassDef):
            report(node.name, node.lineno)
        # Comprensiones y with/as.
        elif isinstance(node, ast.comprehension):
            for nm in _names_in_target(node.target):
                report(nm, getattr(node.target, "lineno", 0))
        elif isinstance(node, ast.withitem) and node.optional_vars is not None:
            for nm in _names_in_target(node.optional_vars):
                report(nm, getattr(node.optional_vars, "lineno", 0))
    return out


def _names_in_target(node):
    """Extrae los nombres asignables de un target (Name, Tuple/List anidados)."""
    names = []
    if isinstance(node, ast.Name):
        names.append(node.id)
    elif isinstance(node, (ast.Tuple, ast.List)):
        for e in node.elts:
            names.extend(_names_in_target(e))
    elif isinstance(node, ast.Starred):
        names.extend(_names_in_target(node.value))
    return names


def _is_none(node):
    return (isinstance(node, ast.Constant) and node.value is None)


def _text_rules(code):
    """Reglas por linea (regex) especificas de PySpark/ETL."""
    out = []
    lines = code.split("\n")
    for i, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            # TODO/FIXME en comentarios: deuda tecnica (info).
            if re.search(r"\b(TODO|FIXME|XXX)\b", raw):
                out.append({"rule": "python:TodoComment", "category": "smell", "severity": "info",
                            "line": i, "message": "Comentario TODO/FIXME: deuda tecnica pendiente."})
            continue

        # .collect() / .toPandas() en PySpark: trae todo al driver (riesgo OOM).
        if re.search(r"\.collect\(\)", line):
            out.append({"rule": "spark:CollectToDriver", "category": "performance", "severity": "major",
                        "line": i, "message": ".collect() trae TODO el DataFrame al driver; "
                        "riesgo de memoria con volumen alto. Recomendacion: evitar o limitar."})
        if re.search(r"\.toPandas\(\)", line):
            out.append({"rule": "spark:ToPandas", "category": "performance", "severity": "major",
                        "line": i, "message": ".toPandas() materializa todo en el driver; "
                        "usar solo con datos pequenos."})

        # count() dentro de bucle o repetido: accion costosa.
        if re.search(r"\.count\(\)", line) and not line.startswith("#"):
            out.append({"rule": "spark:CountAction", "category": "performance", "severity": "minor",
                        "line": i, "message": ".count() es una accion que recorre el DataFrame; "
                        "evita llamarla repetidamente (cachea o reutiliza el valor)."})

        # print() en codigo de produccion -> usar logging (smell minor).
        if re.match(r"print\s*\(", line):
            out.append({"rule": "python:PrintStatement", "category": "smell", "severity": "info",
                        "line": i, "message": "print() en el job; en produccion es preferible logging."})

        # credenciales/paths hardcodeados (seguridad): claves tipicas.
        if re.search(r"(password|passwd|secret|api_key|access_key|token)\s*=\s*['\"][^'\"]+['\"]", line, re.I):
            out.append({"rule": "security:HardcodedSecret", "category": "security", "severity": "critical",
                        "line": i, "message": "Posible credencial hardcodeada. Recomendacion: usar "
                        "variables de entorno o un gestor de secretos."})

        # .option('password', '...') en lecturas JDBC
        if re.search(r"\.option\(\s*['\"]password['\"]\s*,\s*['\"][^'\"]+['\"]", line, re.I):
            out.append({"rule": "security:JdbcPassword", "category": "security", "severity": "critical",
                        "line": i, "message": "Password JDBC en claro. Recomendacion: externalizar la credencial."})

        # linea muy larga (> 120) -> estilo (info).
        if len(raw) > 120:
            out.append({"rule": "python:LineTooLong", "category": "smell", "severity": "info",
                        "line": i, "message": f"Linea muy larga ({len(raw)} chars > 120). Recomendacion: dividir."})
    return out


def _pyflakes_rules(code):
    """Complemento opcional con pyflakes (imports/variables sin usar). Si no esta
    instalado, se omite en silencio (cero dependencias obligatorias)."""
    out = []
    try:
        from pyflakes.api import check
        from pyflakes.reporter import Reporter
        import io as _io
        err, warn = _io.StringIO(), _io.StringIO()
        check(code, "<generated>", Reporter(warn, err))
        for line in (warn.getvalue().splitlines()):
            m = re.search(r"<generated>:(\d+):\d*:?\s*(.+)$", line)
            if m:
                out.append({"rule": "pyflakes", "category": "smell", "severity": "minor",
                            "line": int(m.group(1)), "message": m.group(2).strip()})
    except Exception:
        pass
    return out
