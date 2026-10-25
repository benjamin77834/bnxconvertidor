# src/mlops_emulator.py
"""
Emulador del Framework MLOps: corre el PIPELINE (extract -> groupby -> features
-> vector -> scoring -> monitoreo) con DATOS SINTETICOS en Spark local, PASO A
PASO, sin Cloudera/YARN. Es el equivalente del emulador CICS pero para MLOps.

Entrada: una lista ordenada de pasos:
    [{"id","name","code"}]  donde code es pandas o PySpark.
Cada paso opera sobre un `df` de entrada (el output del paso anterior) y debe
dejar el resultado en `df_out`. El PRIMER paso puede leer con pandas/spark.read;
sus lecturas se neutralizan y se alimenta un DataFrame sintetico.

Salida (dict):
    {
      "ok": bool, "error": str|None,
      "steps": [{"id","name","ok","rows_in","cols_in","rows_out","cols_out",
                 "new_cols":[...], "seconds", "error"}],
      "mermaid": "<grafo del pipeline>",
      "final": {"columns":[...], "rows":[...]},   # muestra del resultado
      "metrics": {"dqc": {...}}                   # calidad del resultado
    }

Todo corre en un SUBPROCESO aislado con timeout (no tumba el servidor).
"""
import json
import os
import subprocess
import sys
import tempfile


# Runner: ejecuta los pasos encadenados en Spark local y emite un reporte JSON.
_EMU_RUNNER = r'''
import json, sys, time, traceback

steps_path = sys.argv[1]
with open(steps_path) as f:
    payload = json.load(f)
steps = payload["steps"]
seed_cols = payload["seed_columns"]
n_rows = payload.get("n_rows", 20)

report = {"ok": False, "error": None, "steps": [], "final": {}, "metrics": {}}


def _neutralize(code):
    """Quita lecturas externas (spark.read.* / pd.read_*) del paso: el df
    encadenado es la fuente. Si una linea asigna a df desde una lectura, se
    comenta para no romper (usamos el df que ya viene)."""
    import re
    out = []
    for ln in code.split("\n"):
        s = ln.strip()
        if re.match(r'^\w+\s*=\s*(pd\.read_|spark\.read\.)', s) or \
           re.match(r'^df\s*=\s*(pd\.read_|spark\.read\.)', s):
            out.append("# [emulador] lectura externa neutralizada: " + s)
        else:
            out.append(ln)
    return "\n".join(out)


try:
    from pyspark.sql import SparkSession, functions as F
    from pyspark.sql.types import (StructType, StructField, StringType,
                                   DoubleType, IntegerType)
    spark = (SparkSession.builder.master("local[1]")
             .appName("bnx_mlops_emulator")
             .config("spark.ui.enabled", "false")
             .config("spark.sql.shuffle.partitions", "2")
             .getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")

    # 1) DataFrame sintetico de entrada (seed) a partir de las columnas inferidas.
    import random
    random.seed(7)
    fields, gen = [], {}
    for c in seed_cols:
        name = c["name"]; typ = (c.get("type") or "string").lower()
        if typ in ("int", "integer", "long", "bigint"):
            fields.append(StructField(name, IntegerType(), True)); gen[name] = "int"
        elif typ in ("double", "float", "decimal", "numeric"):
            fields.append(StructField(name, DoubleType(), True)); gen[name] = "double"
        else:
            fields.append(StructField(name, StringType(), True)); gen[name] = "string"
    if not fields:
        fields = [StructField("id", IntegerType(), True),
                  StructField("valor", DoubleType(), True)]
        gen = {"id": "int", "valor": "double"}

    rows = []
    for i in range(n_rows):
        r = []
        for c in fields:
            k = gen[c.name]
            if k == "int":
                r.append(i + 1 if c.name in ("id", "cliente_id") else random.randint(0, 100))
            elif k == "double":
                r.append(round(random.uniform(0, 10000), 2))
            else:
                r.append(random.choice(["A", "B", "C"]))
        rows.append(tuple(r))
    df = spark.createDataFrame(rows, StructType(fields))

    # 2) Ejecutar cada paso encadenado. El paso opera sobre `df` -> `df_out`.
    prev_cols = set(df.columns)
    for st in steps:
        entry = {"id": st["id"], "name": st["name"], "ok": False,
                 "rows_in": None, "cols_in": None, "rows_out": None,
                 "cols_out": None, "new_cols": [], "seconds": None, "error": None}
        try:
            entry["rows_in"] = df.count()
            entry["cols_in"] = len(df.columns)
            t0 = time.time()
            # El codigo del paso usa `df` (entrada) y debe producir `df_out`.
            local_ns = {"df": df, "spark": spark, "F": F}
            code = st["code"]
            # Neutralizar lecturas externas: si el paso reasigna df con spark.read
            # o pd.read_*, lo ignoramos (usamos el df encadenado). Para el PRIMER
            # paso ya venimos del seed; para los demas, el df encadenado manda.
            exec(_neutralize(code), local_ns)
            out = local_ns.get("df_out", local_ns.get("df"))
            if out is None:
                raise ValueError("el paso no produjo 'df_out' ni modifico 'df'")
            entry["seconds"] = round(time.time() - t0, 3)
            entry["rows_out"] = out.count()
            entry["cols_out"] = len(out.columns)
            new = [c for c in out.columns if c not in prev_cols]
            entry["new_cols"] = new[:20]
            prev_cols = set(out.columns)
            df = out
            entry["ok"] = True
        except Exception as e:
            entry["error"] = "%s: %s" % (type(e).__name__, e)
            report["steps"].append(entry)
            report["error"] = "Fallo en el paso '%s': %s" % (st["name"], entry["error"])
            break
        report["steps"].append(entry)
    else:
        report["ok"] = True

    # 3) Muestra del resultado final + DQC (calidad).
    try:
        cols = df.columns[:12]
        sample = [ [str(v) for v in r] for r in df.select(*cols).limit(10).collect() ]
        report["final"] = {"columns": cols, "rows": sample,
                           "total_rows": df.count(), "total_cols": len(df.columns)}
        # DQC simple: % de nulos por columna (primeras 12).
        total = df.count()
        dqc = {}
        for c in cols:
            nn = df.filter(F.col(c).isNull()).count()
            dqc[c] = {"null_pct": round(100.0 * nn / total, 2) if total else 0.0}
        report["metrics"] = {"dqc": dqc}
    except Exception as e:
        report["metrics"] = {"error": str(e)}

except Exception as e:
    report["error"] = "%s: %s\n%s" % (type(e).__name__, e, traceback.format_exc()[-800:])

print("___BNX_MLOPS_EMU___" + json.dumps(report, default=str))
'''


def _mermaid(steps_report):
    """Grafo Mermaid del pipeline con shape por paso."""
    lines = ["flowchart TD", '    SEED["datos sintéticos"]']

    def nid(i):
        return "s%d" % i
    prev = "SEED"
    for i, st in enumerate(steps_report):
        label = st["name"].replace('"', "'")
        shape = ""
        if st.get("rows_out") is not None:
            shape = f" ({st['rows_out']}f × {st['cols_out']}c)"
        ok = st.get("ok")
        lines.append(f'    {nid(i)}["{label}{shape}"]')
        lines.append(f"    {prev} --> {nid(i)}")
        if not ok:
            lines.append(f'    {nid(i)}:::err')
        prev = nid(i)
    lines.append("    classDef err fill:#7f1d1d,stroke:#ef4444,color:#fff")
    return "\n".join(lines)


def emulate_pipeline(steps, convert_fn=None, seed_columns=None, n_rows=20,
                     timeout=120):
    """Emula el pipeline con datos sinteticos. Devuelve el reporte (ver modulo).

    steps: [{"id","name","code"}] (pandas o PySpark). convert_fn: opcional
    pandas->PySpark (py2spark convert_code). seed_columns: columnas del dataset
    de entrada sintetico [{"name","type"}]; si None, se infieren del 1er paso.
    """
    if not steps:
        return {"ok": False, "error": "No hay pasos que emular.", "steps": []}

    # Convertir pasos pandas -> PySpark si se pidio. Detectamos pandas por el uso
    # de 'import pandas' o 'pd.'. Los que ya son PySpark se dejan igual.
    norm_steps = []
    for i, st in enumerate(steps):
        code = st.get("code", "") or ""
        name = st.get("name") or st.get("id") or f"paso_{i+1}"
        sid = st.get("id") or f"paso_{i+1}"
        looks_pandas = ("import pandas" in code) or ("pd." in code)
        if convert_fn and looks_pandas:
            try:
                conv = convert_fn(code)
                if conv and conv.get("ok") is not False and conv.get("code"):
                    code = conv["code"]
            except Exception:
                pass
        norm_steps.append({"id": sid, "name": name, "code": code})

    # Columnas semilla: si no se dan, inferir del primer paso (nombres de columnas
    # referenciadas). Fallback a un esquema generico.
    if not seed_columns:
        seed_columns = _infer_seed_columns(steps[0].get("code", ""))

    work = tempfile.mkdtemp(prefix="bnx_mlops_emu_")
    try:
        steps_path = os.path.join(work, "steps.json")
        with open(steps_path, "w", encoding="utf-8") as f:
            json.dump({"steps": norm_steps, "seed_columns": seed_columns,
                       "n_rows": n_rows}, f)
        runner_path = os.path.join(work, "_emu_runner.py")
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(_EMU_RUNNER)

        try:
            proc = subprocess.run(
                [sys.executable, runner_path, steps_path],
                cwd=work, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"timeout tras {timeout}s", "steps": []}

        report = None
        for line in (proc.stdout or "").splitlines():
            if line.startswith("___BNX_MLOPS_EMU___"):
                report = json.loads(line[len("___BNX_MLOPS_EMU___"):])
                break
        if report is None:
            return {"ok": False,
                    "error": "no se pudo emular (¿PySpark/Java instalado?)",
                    "stderr": (proc.stderr or "")[-800:], "steps": []}
        report["mermaid"] = _mermaid(report.get("steps", []))
        return report
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)


def _infer_seed_columns(code):
    """Columnas de entrada aproximadas a partir de las referencias df['col'] /
    df.col / groupby('col') del primer paso. Fallback generico."""
    import re
    cols = []
    seen = set()

    def add(name, typ="double"):
        if name and name not in seen:
            seen.add(name)
            cols.append({"name": name, "type": typ})

    c = code or ""
    # Llaves de groupby / merge -> enteras.
    for m in re.findall(r"""group_?by\(\s*\[?\s*['"]([A-Za-z_]\w*)['"]""", c, re.I):
        add(m, "int")
    for m in re.findall(r"""\bon\s*=\s*['"]([A-Za-z_]\w*)['"]""", c):
        add(m, "int")
    # Accesos df['col'] / F.col('col') -> por defecto numericas (lo mas comun en
    # agregaciones/ratios); si el nombre sugiere id/fecha/status, ajustamos.
    refs = re.findall(r"""df\[['"]([A-Za-z_]\w*)['"]\]""", c)
    refs += re.findall(r"""F\.col\(\s*['"]([A-Za-z_]\w*)['"]""", c)
    # Columnas dentro de .agg({"col": "..."}) y .groupby(...).agg(...).
    refs += re.findall(r"""['"]([A-Za-z_]\w*)['"]\s*:\s*['"](?:sum|mean|avg|max|min|count|std)['"]""", c)
    for m in refs:
        lm = m.lower()
        if lm.endswith("_id") or lm in ("id", "cliente_id"):
            add(m, "int")
        elif "fecha" in lm or lm.endswith("_dt") or "status" in lm or "tipo" in lm or "canal" in lm:
            add(m, "string")
        else:
            add(m, "double")
    if not cols:
        cols = [{"name": "cliente_id", "type": "int"},
                {"name": "monto", "type": "double"},
                {"name": "saldo", "type": "double"}]
    # Asegurar una llave entera si hay groupby/merge.
    if not any(c["type"] == "int" for c in cols):
        cols.insert(0, {"name": "id", "type": "int"})
    return cols
