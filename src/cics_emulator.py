# src/cics_emulator.py
"""
Emulador tipo CICS en Python para el COBOL/ALGOL transaccional convertido.

Ejecuta el modulo Python puro (el que genera direct_transpiler en modo pure)
como lo haria un monitor transaccional de mainframe: procesa UN mensaje a la
vez, con datos sinteticos propios, y TRACEA el flujo real de ejecucion:

  - que parrafos (funciones p_*) se ejecutaron y en que orden
  - la relacion de llamadas (quien llamo a quien) -> grafo del flujo
  - cuantas veces se ejecuto cada parrafo
  - la respuesta (ctx) resultante

De ese trace produce un GRAFO EXPLICATIVO (Mermaid) que muestra que hace el
Python convertido en esa transaccion, y los datos sinteticos usados (para poder
llevarlos a Data Sintetica, igual que el resto del flujo).

Todo corre en un SUBPROCESO aislado con timeout (no tumba el servidor).
"""
import json
import os
import subprocess
import sys
import tempfile

from src.transactional_harness import (
    _extract_lookup_schema, _write_lookup_csvs, _synthetic_messages,
)


# Runner con TRACE: usa sys.settrace para registrar las llamadas a funciones de
# parrafo (p_*/init/file_control/...) durante procesa_entidad. Registra el orden
# de ejecucion y las aristas (caller -> callee) para dibujar el flujo.
_TRACE_RUNNER = r'''
import json, sys, traceback, importlib.util

mod_path = sys.argv[1]
msg_path = sys.argv[2]
max_events = int(sys.argv[3]) if len(sys.argv) > 3 else 20000

spec = importlib.util.spec_from_file_location("bnx_gen", mod_path)
mod = importlib.util.module_from_spec(spec)

report = {"import_ok": False, "error": None, "order": [], "edges": [],
          "counts": {}, "resp_sample": {}, "ok": False, "truncated": False}

# Se consideran "parrafos" (unidades de logica del programa) TODAS las funciones
# definidas a nivel top en el modulo generado, EXCEPTO los helpers de runtime y
# el andamiaje. Esto funciona igual para COBOL (parrafos p_0100_* / nombres) que
# para ALGOL (PROCEDURE con nombres alfabeticos: read_card_tx, filter_approved),
# que antes NO se trazaban porque no empezaban con 'p_'.
_NON_PARA = {
    "_n", "_div", "_guard_depth", "new_ctx", "load_lookups",
    "procesa_entidad", "_run_flow", "main",
}
# Nombres de funciones del propio modulo (se llena tras importar el modulo).
_MODULE_FUNCS = set()

def _is_para(name):
    # Andamiaje y helpers: nunca son parrafos.
    if name in _NON_PARA or name.startswith("__"):
        return False
    # Si ya conocemos las funciones del modulo, exigimos pertenecer a el (evita
    # trazar funciones internas de librerias). Si aun no, caemos al heuristico.
    if _MODULE_FUNCS:
        return name in _MODULE_FUNCS
    return name.startswith(("p_", "init", "file_control", "ws_"))

_events = []
_edges = set()
_counts = {}
_callstack = []
_stop = {"n": 0}

def _tracer(frame, event, arg):
    if event != "call":
        return
    name = frame.f_code.co_name
    # procesa_entidad y _run_flow son el andamiaje: NO se dibujan como parrafos,
    # pero hay que DESCENDER en ellos para ver las llamadas a los parrafos reales.
    if name in ("procesa_entidad", "_run_flow"):
        return _tracer
    if not _is_para(name):
        return None
    _stop["n"] += 1
    if _stop["n"] > max_events:
        report["truncated"] = True
        return None
    caller = _callstack[-1] if _callstack else "START"
    _edges.add((caller, name))
    _events.append(name)
    _counts[name] = _counts.get(name, 0) + 1
    _callstack.append(name)
    def _ret(f, e, a):
        if e == "return" and _callstack and _callstack[-1] == name:
            _callstack.pop()
    return _ret

try:
    spec.loader.exec_module(mod)
    report["import_ok"] = True
    # Descubrir las funciones definidas EN el modulo generado (no importadas),
    # para trazarlas como parrafos aunque no empiecen con 'p_' (caso ALGOL).
    import types as _types
    for _n_name, _n_obj in vars(mod).items():
        if isinstance(_n_obj, _types.FunctionType) and getattr(_n_obj, "__module__", None) == mod.__name__:
            _MODULE_FUNCS.add(_n_name)
    lookups = mod.load_lookups() if hasattr(mod, "load_lookups") else None
    with open(msg_path) as f:
        mensaje = json.load(f)
    sys.settrace(_tracer)
    try:
        out = (mod.procesa_entidad(mensaje, lookups) if lookups is not None
               else mod.procesa_entidad(mensaje))
        report["ok"] = True
    finally:
        sys.settrace(None)
    if isinstance(out, dict):
        _skip = {"_lookups", "ws_mensaje"}
        sample = {}
        for k in list(out.keys()):
            if str(k) in _skip:
                continue
            try:
                sample[str(k)] = str(out[k])[:60]
            except Exception:
                sample[str(k)] = "<?>"
            if len(sample) >= 40:
                break
        report["resp_sample"] = sample
    # Orden de ejecucion (primeras N, sin repetir consecutivos para legibilidad).
    seen_order = []
    for n in _events:
        if not seen_order or seen_order[-1] != n:
            seen_order.append(n)
    report["order"] = seen_order[:400]
    report["edges"] = sorted(list(_edges))[:800]
    report["counts"] = _counts
except Exception as e:
    sys.settrace(None)
    report["error"] = f"{type(e).__name__}: {e}\n{traceback.format_exc()[-800:]}"

print("___BNX_EMU___" + json.dumps(report))
'''


def _mermaid_from_trace(edges, counts, max_nodes=60):
    """Construye un grafo Mermaid (flowchart) del flujo ejecutado.

    edges: lista de (caller, callee). counts: {parrafo: veces}. Limita a los
    parrafos mas ejecutados para que el diagrama sea legible.
    """
    if not edges:
        return "flowchart TD\n    START[Sin trace]"
    # Elegir los nodos mas relevantes (por frecuencia de ejecucion).
    top = set(sorted(counts, key=lambda k: counts[k], reverse=True)[:max_nodes])
    top.add("START")

    def _nid(name):
        # id valido para mermaid (sin caracteres raros).
        return "n_" + "".join(c if c.isalnum() else "_" for c in name)

    def _label(name):
        c = counts.get(name, 0)
        # Nombre interno del programa principal ALGOL -> etiqueta legible.
        disp = "PROGRAMA PRINCIPAL" if name == "_bnx_main" else name
        short = disp[:34]
        return f"{short}" + (f" x{c}" if c > 1 else "")

    lines = ["flowchart TD"]
    emitted = set()
    for a, b in edges:
        if a not in top or b not in top:
            continue
        for n in (a, b):
            if n not in emitted:
                emitted.add(n)
                lines.append(f'    {_nid(n)}["{_label(n)}"]')
        lines.append(f"    {_nid(a)} --> {_nid(b)}")
    return "\n".join(lines)


def emulate(code, src_code, lang="cobol", rows_per_table=5, timeout=60,
            max_events=20000):
    """Emula una transaccion del COBOL/ALGOL convertido y devuelve el reporte +
    grafo del flujo + los datasets sinteticos usados.

    Devuelve dict: {ok, import_ok, order, edges, counts, mermaid, resp_sample,
                    lookups, message, datasets, error}.
    """
    work = tempfile.mkdtemp(prefix="bnx_emu_")
    data_dir = os.path.join(work, "data")
    try:
        try:
            schema = _extract_lookup_schema(src_code, lang)
        except Exception as e:
            schema, schema_err = {}, f"{type(e).__name__}: {e}"
        else:
            schema_err = None

        lookups_info = _write_lookup_csvs(data_dir, schema, rows_per_table) if schema else {}
        messages = _synthetic_messages(schema, 1)
        message = messages[0] if messages else {}
        msg_path = os.path.join(work, "msg.json")
        with open(msg_path, "w") as f:
            json.dump(message, f)

        mod_path = os.path.join(work, "main.py")
        with open(mod_path, "w", encoding="utf-8") as f:
            f.write(code)
        runner_path = os.path.join(work, "_emu_runner.py")
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(_TRACE_RUNNER)

        env = dict(os.environ)
        env["BNX_DATA_DIR"] = data_dir
        try:
            proc = subprocess.run(
                [sys.executable, runner_path, mod_path, msg_path, str(max_events)],
                cwd=work, env=env, capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"timeout tras {timeout}s",
                    "lookups": list(lookups_info.keys()), "message": message,
                    "datasets": _datasets_payload(data_dir, lookups_info)}

        report = None
        for line in (proc.stdout or "").splitlines():
            if line.startswith("___BNX_EMU___"):
                report = json.loads(line[len("___BNX_EMU___"):])
                break
        if report is None:
            return {"ok": False, "error": "no se pudo emular el modulo",
                    "stderr": (proc.stderr or "")[-1000:],
                    "lookups": list(lookups_info.keys()), "message": message,
                    "datasets": _datasets_payload(data_dir, lookups_info)}

        report["mermaid"] = _mermaid_from_trace(
            [tuple(e) for e in report.get("edges", [])], report.get("counts", {}))
        report["lookups"] = list(lookups_info.keys())
        report["message"] = message
        report["schema_error"] = schema_err
        report["paragraphs_executed"] = len(report.get("counts", {}))
        report["total_calls"] = sum(report.get("counts", {}).values())
        # Datasets sinteticos (para llevar a Data Sintetica).
        report["datasets"] = _datasets_payload(data_dir, lookups_info)
        return report
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)


def _datasets_payload(data_dir, lookups_info):
    """Lee los CSV sinteticos generados y los devuelve como {nombre: {columns,
    rows}} para que la UI pueda mostrarlos y enviarlos a Data Sintetica."""
    out = {}
    for name, info in (lookups_info or {}).items():
        path = info.get("path")
        if not path or not os.path.isfile(path):
            continue
        try:
            import csv as _csv
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(_csv.reader(f))
            if rows:
                out[name] = {"columns": rows[0], "rows": rows[1:11]}
        except Exception:
            continue
    return out
