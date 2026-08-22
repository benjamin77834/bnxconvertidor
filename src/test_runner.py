# src/test_runner.py
"""
Ejecutor de prueba local para código PySpark generado (BNX).

Toma el código PySpark producido por el convertidor y lo ejecuta localmente
usando datos de entrada sintéticos (los generados por Data Redactada), para
comprobar si el job corre correctamente sin necesidad de AWS/S3.

Estrategia (solo target PySpark, no Glue):
  1. Neutraliza las lecturas externas: `spark.read.<fmt>(...)` → DataFrame
     sintético inyectado por nombre de variable (X_df) desde BNX_INPUTS.
  2. Neutraliza las escrituras: `X.write...(...)` → registra un resumen
     (count + esquema) en lugar de escribir a S3.
  3. Ejecuta en un subproceso aislado con timeout y captura stdout/stderr.
"""
import re
import os
import io
import csv
import json
import sys
import tempfile
import subprocess


def _csv_to_records(content, delimiter=","):
    """Convierte contenido CSV a lista de dicts (todo string, se castea en Spark)."""
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    return [dict(r) for r in reader]


def _normalize_inputs(datasets):
    """Normaliza los datasets de entrada a {nombre_nodo_lower: [records]}.

    datasets: lista de {"node", "io", "format", "content"|"rows", "columns"}
    Solo se usan los de io == "input" (o todos si ninguno trae io).
    """
    inputs = {}
    any_input = any(d.get("io") == "input" for d in datasets)
    for d in datasets:
        if any_input and d.get("io") != "input":
            continue
        node = (d.get("node") or "").strip()
        if not node:
            continue
        rows = d.get("rows")
        if rows is None and d.get("content"):
            if d.get("format") == "json":
                try:
                    rows = json.loads(d["content"])
                except Exception:
                    rows = []
            else:
                rows = _csv_to_records(d["content"])
        inputs[node.lower()] = rows or []
    return inputs


def build_test_script(pyspark_code, inputs):
    """Construye un script PySpark ejecutable localmente.

    - Inyecta BNX_INPUTS (dict nodo→registros) al inicio.
    - Reemplaza lecturas spark.read.<fmt>(...) por _bnx_read("<var>").
    - Reemplaza escrituras X.write... por _bnx_write(X, "<var>").
    """
    lines = pyspark_code.split("\n")
    out = []

    # 1. Reemplazar asignaciones de lectura:
    #    Nombre_df = spark.read.<fmt>(...)   →   Nombre_df = _bnx_read("Nombre_df")
    read_re = re.compile(r'^(\s*)(\w+)\s*=\s*spark\.read\.[\w.]+\(.*\)\s*$')
    # 2. Reemplazar escrituras:
    #    X_df.write.mode(...).<fmt>(...)     →   _bnx_write(X_df, "X_df")
    #    X_df.write.<fmt>(...)               →   _bnx_write(X_df, "X_df")
    write_re = re.compile(r'^(\s*)(\w+)\.write\b.*$')

    for ln in lines:
        m_read = read_re.match(ln)
        if m_read:
            indent, var = m_read.group(1), m_read.group(2)
            out.append(f'{indent}{var} = _bnx_read("{var}")')
            continue
        m_write = write_re.match(ln)
        if m_write:
            indent, var = m_write.group(1), m_write.group(2)
            out.append(f'{indent}_bnx_write({var}, "{var}")')
            continue
        out.append(ln)

    body = "\n".join(out)

    # Harness que se antepone. Define _bnx_read/_bnx_write y BNX_INPUTS.
    # _bnx_read intenta emparejar por nombre de variable (Nombre_df → nombre del nodo).
    harness = f'''# ===== BNX TEST HARNESS (auto-generado) =====
import json as _json
from pyspark.sql import SparkSession as _SS
from pyspark.sql import Row as _Row

_BNX_INPUTS = _json.loads({json.dumps(json.dumps(inputs))})
_BNX_WRITES = []

def _bnx_spark():
    return _SS.builder.master("local[1]").appName("BNX_Test").getOrCreate()

_bnx_session = _bnx_spark()

def _bnx_match_key(var):
    # var suele ser "NombreNodo_df" → buscamos "nombrenodo"
    base = var[:-3].lower() if var.lower().endswith("_df") else var.lower()
    if base in _BNX_INPUTS:
        return base
    # match laxo por prefijo/contains
    for k in _BNX_INPUTS:
        if k == base or base.startswith(k) or k.startswith(base):
            return k
    return None

def _bnx_read(var):
    key = _bnx_match_key(var)
    records = _BNX_INPUTS.get(key, []) if key else []
    if not records:
        # DataFrame vacío con una columna dummy para no romper el flujo
        print(f"[BNX-TEST] WARN: sin datos de entrada para {{var}} (nodo '{{key}}'), uso vacío")
        return _bnx_session.createDataFrame([_Row(_bnx_placeholder="")])
    rows = [_Row(**{{k: (v if v is not None else None) for k, v in rec.items()}}) for rec in records]
    df = _bnx_session.createDataFrame(rows)
    print(f"[BNX-TEST] READ {{var}} (nodo '{{key}}'): {{df.count()}} filas, cols={{df.columns}}")
    return df

def _bnx_write(df, var):
    try:
        n = df.count()
        cols = df.columns
        _BNX_WRITES.append({{"var": var, "rows": n, "columns": cols}})
        print(f"[BNX-TEST] WRITE {{var}}: {{n}} filas, cols={{cols}}")
        df.show(5, truncate=False)
    except Exception as _e:
        print(f"[BNX-TEST] WRITE {{var}} ERROR: {{_e}}")
        raise

# Alias de spark para el código generado
spark = _bnx_session
# ===== FIN HARNESS =====

'''

    # El código generado crea su propio spark = SparkSession...getOrCreate().
    # Como local[1] ya tiene una sesión activa, getOrCreate reutiliza la misma.
    # Neutralizamos spark.stop() para no cortar la sesión antes de tiempo si aparece.
    body = body.replace("spark.stop()", "# spark.stop()  # neutralizado por BNX-TEST")

    return harness + body


def run_pyspark_test(pyspark_code, datasets, timeout=120):
    """Ejecuta el código PySpark con datos sintéticos y devuelve el resultado.

    Devuelve dict:
      {"ok": bool, "exit_code": int, "stdout": str, "stderr": str,
       "timed_out": bool, "writes": [...], "reads": [...], "summary": str}
    """
    inputs = _normalize_inputs(datasets)
    script = build_test_script(pyspark_code, inputs)

    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix="_bnx_test.py", mode="w", encoding="utf-8"
    )
    tmp.write(script)
    tmp.close()

    env = dict(os.environ)
    # Silenciar logs verbosos de Spark
    env.setdefault("PYSPARK_PYTHON", sys.executable)

    timed_out = False
    try:
        proc = subprocess.run(
            [sys.executable, tmp.name],
            capture_output=True, text=True, timeout=timeout, env=env,
        )
        exit_code = proc.returncode
        stdout, stderr = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        timed_out = True
        exit_code = -1
        stdout = e.stdout or ""
        stderr = (e.stderr or "") + f"\n[BNX-TEST] Timeout tras {timeout}s"
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    # Parsear resúmenes de READ/WRITE desde stdout
    reads = re.findall(r"\[BNX-TEST\] READ (\S+) \(nodo '([^']*)'\): (\d+) filas", stdout)
    writes = re.findall(r"\[BNX-TEST\] WRITE (\S+): (\d+) filas", stdout)

    ok = (not timed_out) and exit_code == 0
    if ok:
        summary = f"Ejecución OK · {len(reads)} lectura(s), {len(writes)} escritura(s)"
    elif timed_out:
        summary = f"Timeout tras {timeout}s — el job tardó demasiado"
    else:
        summary = "Falló la ejecución — revisa el error abajo"

    return {
        "ok": ok,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout": _tail(stdout, 20000),
        "stderr": _tail(stderr, 20000),
        "reads": [{"var": r[0], "node": r[1], "rows": int(r[2])} for r in reads],
        "writes": [{"var": w[0], "rows": int(w[1])} for w in writes],
        "summary": summary,
    }


def _tail(text, max_chars):
    """Recorta texto largo dejando el final (donde suelen estar los errores)."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return "...[truncado]...\n" + text[-max_chars:]
