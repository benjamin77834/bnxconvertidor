# src/transactional_harness.py
"""
Harness de prueba para el PYTHON PURO transaccional (COBOL/ALGOL tipo CICS).

El traductor directo en modo 'pure' genera un modulo con:
  - load_lookups(data_dir) -> carga CSV indexados por su 1a columna
  - procesa_entidad(mensaje_input, lookups) -> dict

Este harness PRUEBA que ese modulo CORRE (no solo que compila):
  1) Extrae el schema de los archivos de lookup del COBOL/ALGOL (FILE SECTION).
  2) Genera CSV sinteticos para cada lookup + N mensajes de entrada sinteticos.
  3) Ejecuta `procesa_entidad(mensaje)` para cada mensaje en un SUBPROCESO
     aislado (con timeout), para no tumbar el servidor si el codigo cuelga.
  4) Devuelve un reporte: cuantos corrieron, errores, claves de respuesta.

Es intencionalmente simple y SIN Spark: valida el flujo transaccional.
"""
import csv
import json
import os
import subprocess
import sys
import tempfile


def _synthetic_value(ftype, i):
    """Valor sintetico por tipo simple del schema (string/int/long/decimal/double)."""
    t = (ftype or "string").lower()
    if t in ("int", "long"):
        return str(100 + i)
    if t in ("decimal", "double"):
        return f"{(100 + i)}.{(i % 100):02d}"
    return f"VAL{i:04d}"


def _extract_lookup_schema(src_code, lang):
    """Devuelve {NOMBRE_FILE_UPPER: {campo: tipo}} de los archivos del programa.
    Reutiliza el parser del lenguaje para no duplicar la logica de PIC/tipos."""
    import tempfile as _tf
    suffix = ".cbl" if lang == "cobol" else ".alg"
    tmp = _tf.NamedTemporaryFile(delete=False, suffix=suffix, mode="w",
                                 encoding="utf-8", errors="replace")
    tmp.write(src_code)
    tmp.close()
    try:
        if lang == "cobol":
            from src.cobol_parser import parse_cobol
            parsed = parse_cobol(tmp.name)
        else:
            from src.algol_parser import parse_algol
            parsed = parse_algol(tmp.name)
    finally:
        os.unlink(tmp.name)
    files = parsed.get("files", {}) or {}
    fields = parsed.get("fields", {}) or {}
    schema = {}
    for fname in files:
        key = fname.upper()
        cols = fields.get(fname) or {}
        if not cols:
            # Sin schema de campos: una tabla minima con una clave generica.
            cols = {"key": "string", "valor": "string"}
        schema[key] = dict(cols)
    return schema


def _write_lookup_csvs(data_dir, schema, rows_per_table=5):
    """Escribe un CSV por tabla de lookup con filas sinteticas. La 1a columna es
    la clave (el modulo generado indexa por la primera columna)."""
    os.makedirs(data_dir, exist_ok=True)
    written = {}
    for name_upper, cols in schema.items():
        colnames = list(cols.keys()) or ["key", "valor"]
        # Garantizar una columna clave al frente.
        path = os.path.join(data_dir, name_upper.lower() + ".csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(colnames)
            for i in range(rows_per_table):
                w.writerow([_synthetic_value(cols.get(c, "string"), i) for c in colnames])
        written[name_upper] = {"path": path, "columns": colnames, "rows": rows_per_table}
    return written


def _synthetic_messages(schema, n=3):
    """Genera N mensajes de entrada sinteticos. Como no conocemos el layout del
    mensaje transaccional, usamos las columnas de la PRIMERA tabla + unos campos
    de control tipicos; y seteamos las claves de lookup (<file>_key) a valores
    que SI existen en los CSV (primera fila), para ejercitar los lookups."""
    msgs = []
    first_cols = next(iter(schema.values()), {"key": "string"}) if schema else {}
    for i in range(n):
        msg = {}
        for c, t in first_cols.items():
            msg[c] = _synthetic_value(t, i)
        # Claves de lookup: apuntan a la primera fila sintetica (VAL0000 / 100).
        for name_upper, cols in schema.items():
            key_col = next(iter(cols.keys()), "key")
            msg[name_upper.lower() + "_key"] = _synthetic_value(cols.get(key_col, "string"), 0)
        msgs.append(msg)
    return msgs


# Script runner que se ejecuta en subproceso: importa el modulo generado y
# corre procesa_entidad por cada mensaje, capturando excepciones por mensaje.
_RUNNER = '''
import json, sys, traceback, importlib.util

mod_path = sys.argv[1]
msgs_path = sys.argv[2]
spec = importlib.util.spec_from_file_location("bnx_gen", mod_path)
mod = importlib.util.module_from_spec(spec)
report = {"import_ok": False, "runs": [], "error": None}
try:
    spec.loader.exec_module(mod)
    report["import_ok"] = True
    # Recargar lookups desde el data_dir del cwd (BNX_DATA_DIR ya apunta ahi).
    lookups = mod.load_lookups() if hasattr(mod, "load_lookups") else None
    with open(msgs_path) as f:
        messages = json.load(f)
    for idx, m in enumerate(messages):
        r = {"i": idx, "ok": False, "resp_keys": [], "resp_sample": {}, "error": None}
        try:
            out = mod.procesa_entidad(m, lookups) if lookups is not None else mod.procesa_entidad(m)
            r["ok"] = True
            if isinstance(out, dict):
                # Campos internos del harness que no son 'salida de negocio'.
                _skip = {"_lookups", "ws_mensaje"}
                keys = [k for k in out.keys() if str(k) not in _skip]
                r["resp_keys"] = [str(k) for k in keys[:40]]
                # Muestra de valores (clave -> valor serializable) para VER que
                # produjo la transaccion, no solo los nombres de campo.
                sample = {}
                for k in keys[:25]:
                    try:
                        v = out[k]
                        sample[str(k)] = str(v)[:60]
                    except Exception:
                        sample[str(k)] = "<no serializable>"
                r["resp_sample"] = sample
        except Exception as e:
            r["error"] = f"{type(e).__name__}: {e}"
        report["runs"].append(r)
except Exception as e:
    report["error"] = f"{type(e).__name__}: {e}\\n{traceback.format_exc()[-800:]}"
print("___BNX_REPORT___" + json.dumps(report))
'''


def run_transactional_test(code, src_code, lang="cobol",
                           num_messages=3, rows_per_table=5, timeout=60):
    """Prueba el modulo Python puro transaccional end-to-end.

    code     : el PySpark/Python puro generado (modo 'pure').
    src_code : el COBOL/ALGOL fuente (para extraer el schema de lookups).
    Devuelve un dict-reporte: {ok, import_ok, total, passed, failed, lookups,
                               messages, runs, error}.
    """
    work = tempfile.mkdtemp(prefix="bnx_tx_")
    data_dir = os.path.join(work, "data")
    try:
        # 1) Schema de lookups desde el fuente.
        try:
            schema = _extract_lookup_schema(src_code, lang)
        except Exception as e:
            schema = {}
            schema_err = f"{type(e).__name__}: {e}"
        else:
            schema_err = None

        # 2) CSVs de lookup + mensajes sinteticos.
        lookups_info = _write_lookup_csvs(data_dir, schema, rows_per_table) if schema else {}
        messages = _synthetic_messages(schema, num_messages)
        msgs_path = os.path.join(work, "messages.json")
        with open(msgs_path, "w") as f:
            json.dump(messages, f)

        # 3) Escribir el modulo generado como main.py en el work dir.
        mod_path = os.path.join(work, "main.py")
        with open(mod_path, "w", encoding="utf-8") as f:
            f.write(code)
        runner_path = os.path.join(work, "_runner.py")
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(_RUNNER)

        # 4) Ejecutar en subproceso aislado (cwd=work para que ./data resuelva,
        #    BNX_DATA_DIR tambien lo apunta por si el modulo usa PARAMS.DATA_DIR).
        env = dict(os.environ)
        env["BNX_DATA_DIR"] = data_dir
        try:
            proc = subprocess.run(
                [sys.executable, runner_path, mod_path, msgs_path],
                cwd=work, env=env, capture_output=True, text=True, timeout=timeout,
            )
            stdout, stderr = proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"timeout tras {timeout}s (posible bucle infinito)",
                    "import_ok": False, "total": 0, "passed": 0, "failed": 0,
                    "lookups": list(lookups_info.keys()), "schema_error": schema_err}

        # 5) Parsear el reporte del runner.
        report = None
        for line in stdout.splitlines():
            if line.startswith("___BNX_REPORT___"):
                report = json.loads(line[len("___BNX_REPORT___"):])
                break
        if report is None:
            return {"ok": False, "import_ok": False, "total": 0, "passed": 0,
                    "failed": 0, "error": "no se pudo ejecutar el modulo",
                    "stderr": (stderr or "")[-1200:],
                    "lookups": list(lookups_info.keys()), "schema_error": schema_err}

        runs = report.get("runs", [])
        passed = sum(1 for r in runs if r.get("ok"))
        return {
            "ok": report.get("import_ok") and passed == len(runs) and len(runs) > 0,
            "import_ok": report.get("import_ok", False),
            "total": len(runs),
            "passed": passed,
            "failed": len(runs) - passed,
            "lookups": list(lookups_info.keys()),
            "lookups_detail": lookups_info,
            "messages": messages,
            "runs": runs,
            "error": report.get("error"),
            "schema_error": schema_err,
            "stderr": (stderr or "")[-800:] if report.get("error") else None,
        }
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)
