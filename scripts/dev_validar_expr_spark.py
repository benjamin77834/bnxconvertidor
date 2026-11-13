#!/usr/bin/env python3
"""DEV/TESTS: valida con el PARSER REAL de Spark cada expresion SQL de los *_spark.py generados.

Recorre (con ast) los .py y extrae el string literal pasado a expr(...), selectExpr(...),
.where/.filter(...), _bnx_safe_col(df, col, "sql") y _bnx_filter_split(...). Cada uno se
parsea con spark._jsparkSession.sessionState().sqlParser().parseExpression(...) (requiere
pyspark + Java; por eso NO se usa en la conversion, solo aqui).

Uso:
    python scripts/dev_validar_expr_spark.py [carpeta_o_py ...]   (def: output/*/*_spark.py)
    python scripts/dev_validar_expr_spark.py --verbose output/benja1
Salida: por archivo, total de expresiones y las que no parsean (con linea y error corto).
Codigo de salida 1 si alguna no parsea.
"""
import argparse
import ast
import glob
import os
import re
import sys

PLACEHOLDER = "PLACEHOLDER"
_PLACEHOLDER = re.compile(r"\$\{\w+\}")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _const_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def extraer_expresiones(path):
    """Devuelve [(lineno, funcion, sql)] con los SQL literales del .py (ast)."""
    with open(path, encoding="utf-8", errors="replace") as f:
        src = f.read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:  # el .py no compila: reportarlo como hallazgo
        return [(e.lineno or 0, "SyntaxError", f"<<{e.msg}>>")]
    res = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else None
        if name in ("expr",):
            s = _const_str(node.args[0]) if node.args else None
            if s is not None:
                res.append((node.lineno, name, s))
        elif name in ("selectExpr",):
            for a in node.args:
                s = _const_str(a)
                if s is not None:
                    res.append((node.lineno, name, s))
        elif name in ("where", "filter"):
            s = _const_str(node.args[0]) if node.args else None
            if s is not None:
                res.append((node.lineno, name, s))
        elif name == "_bnx_safe_col":
            s = _const_str(node.args[2]) if len(node.args) >= 3 else None
            if s is not None:
                res.append((node.lineno, name, s))
        elif name == "_bnx_filter_split":
            for a in node.args[1:]:
                s = _const_str(a)
                if s is not None:
                    res.append((node.lineno, name, s))
    return sorted(res)


def _spark():
    from pyspark.sql import SparkSession
    spark = (SparkSession.builder.master("local[1]").appName("bnx_dev_validar_expr")
             .config("spark.ui.enabled", "false").config("spark.sql.shuffle.partitions", "1")
             .getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def parsear(spark, sqls):
    """Devuelve {sql: None|error_corto} usando el parser SQL de Spark (sin ejecutar)."""
    parser = spark._jsparkSession.sessionState().sqlParser()
    out = {}
    for s in sqls:
        if s in out:
            continue
        try:
            parser.parseExpression(s)
            out[s] = None
            continue
        except Exception as e:  # py4j.protocol.Py4JJavaError / ParseException
            msg = str(e)
            m = re.search(r"Syntax error at or near [^\n.]*|\[[A-Z_]+\][^\n]*", msg)
            err = (m.group(0) if m else msg.splitlines()[0])[:120]
        # ${PARAM} sin resolver: es un parametro Ab Initio pendiente (el job lo tolera con
        # _bnx_safe_col / _bnx_filter_split). Si con el placeholder sustituido parsea, se
        # clasifica aparte (PLACEHOLDER) y NO cuenta como expresion rota.
        if _PLACEHOLDER.search(s):
            try:
                parser.parseExpression(_PLACEHOLDER.sub("NULL", s))
                out[s] = PLACEHOLDER
                continue
            except Exception:
                pass
        out[s] = err
    return out


def archivos(args):
    pats = args or [os.path.join(ROOT, "output")]
    res = []
    for a in pats:
        if os.path.isdir(a):
            res += glob.glob(os.path.join(a, "**", "*_spark.py"), recursive=True)
        elif os.path.isfile(a):
            res.append(a)
    return sorted(set(res))


def validar(paths, spark=None, verbose=False):
    """Devuelve {path: (total, [(lineno, fn, sql, err)], n_placeholder)}."""
    spark = spark or _spark()
    datos = {p: extraer_expresiones(p) for p in paths}
    todas = {s for exprs in datos.values() for (_l, _f, s) in exprs}
    ok = parsear(spark, sorted(todas))
    res = {}
    for p, exprs in datos.items():
        malas = [(l, f, s, ok[s]) for (l, f, s) in exprs if ok.get(s) and ok[s] != PLACEHOLDER]
        res[p] = (len(exprs), malas, sum(1 for (_l, _f, s) in exprs if ok.get(s) == PLACEHOLDER))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--verbose", "-v", action="store_true")
    a = ap.parse_args()
    paths = archivos(a.paths)
    if not paths:
        print("[!] sin archivos *_spark.py")
        return 0
    res = validar(paths, verbose=a.verbose)
    total_bad = 0
    total_ph = 0
    for p, (n, malas, nph) in res.items():
        rel = os.path.relpath(p, ROOT)
        total_ph += nph
        print(f"{rel}: {n} expresiones, {len(malas)} NO parsean, {nph} con ${{PARAM}} sin resolver")
        total_bad += len(malas)
        for (l, f, s, err) in malas[: (None if a.verbose else 15)]:
            print(f"   l.{l} {f}: {err} :: {s[:110]!r}")
    print(f"[=] total no parsean: {total_bad}  (con ${{PARAM}} sin resolver, aparte: {total_ph})")
    return 1 if total_bad else 0


if __name__ == "__main__":
    sys.exit(main())
