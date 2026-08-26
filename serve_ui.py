"""
BNX Convertidor - Servidor local (Python puro, sin Amplify)
Sirve la UI React compilada + API backend en un solo proceso.

Uso:
  py -3 serve_ui.py

Abre: http://localhost:8080

Prerequisitos:
  1. Compilar la UI una vez: cd ui && npm run build
  2. O usar la UI pre-compilada en ui/dist/
"""
import os
import sys
import json
import re
import tempfile
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from io import BytesIO


def parse_multipart(body, content_type):
    """Parse multipart/form-data sin dependencia de cgi (removido en Python 3.13+)."""
    fields = {}
    files = {}

    if "boundary=" not in content_type:
        return fields, files

    boundary = content_type.split("boundary=")[1].strip()
    if boundary.startswith('"') and boundary.endswith('"'):
        boundary = boundary[1:-1]

    parts = body.split(f"--{boundary}".encode())

    for part in parts[1:]:  # skip preamble
        if part.strip() == b"--" or part.strip() == b"":
            continue

        # Split headers from body
        if b"\r\n\r\n" in part:
            header_data, file_data = part.split(b"\r\n\r\n", 1)
        elif b"\n\n" in part:
            header_data, file_data = part.split(b"\n\n", 1)
        else:
            continue

        # Remove trailing \r\n
        if file_data.endswith(b"\r\n"):
            file_data = file_data[:-2]
        elif file_data.endswith(b"\n"):
            file_data = file_data[:-1]

        headers = header_data.decode("utf-8", errors="replace")
        name = None
        filename = None

        for line in headers.split("\n"):
            line = line.strip()
            if "name=" in line:
                # Extract name
                name_part = line.split("name=")[1].split(";")[0].strip().strip('"')
                name = name_part
            if "filename=" in line:
                fn_part = line.split("filename=")[1].split(";")[0].strip().strip('"')
                filename = fn_part

        if name:
            if filename:
                files[name] = file_data
                fields[f"{name}_filename"] = filename
            else:
                fields[name] = file_data.decode("utf-8", errors="replace")

    return fields, files

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from main import parse_project
from src.dag.builder import build_dag
from src.xfr_parser import parse_xfr
from src.dml_parser import parse_dml
from src.plan_parser import parse_pset
from src.codegen.glue_codegen import generate_glue
from src.codegen.spark_codegen import generate_spark
from src.codegen.flink_codegen import generate_flink
from src.validator.semantic import validate
from src.accuracy import compute_accuracy
from src.perf_optimizer import optimize_pyspark
from src.datagen import (
    infer_schema_from_graph,
    build_synthetic_data,
    detect_pii,
    normalize_type,
)
from src.test_runner import (
    run_pyspark_test,
    stream_pyspark_test,
    build_aws_selfcontained_code,
    BNX_LOCAL_OUTPUT_DIR,
    _describe_graph,
)

PORT = int(os.environ.get("BNX_PORT", 8081))
UI_DIR = os.path.join(os.path.dirname(__file__), "ui", "dist")

# Check if UI is built
if not os.path.isdir(UI_DIR):
    print(f"[!] UI not built. Run: cd ui && npm run build")
    print(f"    Or create ui/dist/ with index.html")
    print(f"    Starting API-only mode on port {PORT}...")
    UI_DIR = None


class BNXHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        if UI_DIR:
            super().__init__(*args, directory=UI_DIR, **kwargs)
        else:
            super().__init__(*args, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path

        if "/library" in path:
            # Biblioteca de grafos LOCAL (no depende del bucket S3 de DataLab,
            # que esta bloqueado por una SCP). Se guarda en ./bnx_library/.
            self._handle_library()
        elif "/pipeline" in path:
            self._proxy_to_datalab(path)
        elif "/datagen/awscode" in path:
            self._handle_awscode()
        elif "/datagen" in path:
            self._handle_datagen()
        elif "/runtest/graph" in path:
            self._handle_runtest_graph()
        elif "/runtest/stream" in path:
            self._handle_runtest_stream()
        elif "/runtest" in path:
            self._handle_runtest()
        elif "/optimize/compare" in path:
            self._handle_optimize_compare()
        elif "/optimize" in path:
            self._handle_optimize()
        elif "/compile" in path or "/api" in path:
            self._handle_compile()
        else:
            self.send_error(404, "Not found")

    def do_GET(self):
        path = urlparse(self.path).path

        # API health check
        if path == "/api/health":
            self._json_response(200, {"status": "ok", "version": "V54"})
            return

        # Descarga de resultados de la prueba LOCAL (CSV generados por el runner).
        if path == "/download" or path == "/api/download":
            self._handle_download()
            return

        # Serve static UI files
        if UI_DIR:
            # SPA fallback: serve index.html for all non-file routes
            file_path = os.path.join(UI_DIR, path.lstrip("/"))
            if not os.path.isfile(file_path) and not path.startswith("/api"):
                self.path = "/index.html"
            super().do_GET()
        else:
            self._json_response(200, {"message": "BNX API running", "endpoints": ["/api/health", "/compile (POST)"]})

    def end_headers(self):
        # No-cache headers for all responses
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()
    def _proxy_to_datalab(self, path):
        """Proxy requests to DataLab API Gateway (for pipeline/library when firewall blocks direct access)."""
        import urllib.request
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        datalab_url = f"https://6lewkixco1.execute-api.us-east-1.amazonaws.com/prod{path}"
        try:
            req = urllib.request.Request(datalab_url, data=body, method="POST")
            req.add_header("Content-Type", content_type)
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = resp.read()
                self.send_response(resp.status)
                self._cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(result)
        except Exception as e:
            self._json_response(502, {"error": f"Proxy error: {str(e)}"})

    def _handle_library(self):
        """Biblioteca de grafos LOCAL en disco (./bnx_library/).

        No depende de AWS/S3 (el bucket de DataLab esta bloqueado por una SCP de
        la organizacion). Soporta los dos contratos que usa la UI:
          - GraphLibrary.jsx: action = list | save | delete   (grafos planos)
          - GrafosPage.jsx:   action = list_projects | create_project |
                              list_files | download | upload | delete  (por proyecto)

        Estructura en disco:
          bnx_library/
            _flat/<id>.mp, <id>.xfr        (grafos planos de GraphLibrary)
            <proyecto>/<archivo>.mp/.xfr   (proyectos de GrafosPage)
        """
        import glob as _glob

        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bnx_library")
        flat_dir = os.path.join(root, "_flat")
        os.makedirs(flat_dir, exist_ok=True)

        # Parsear el body (multipart FormData o JSON). Usamos el parse_multipart
        # propio del modulo (cgi fue removido en Python 3.13+).
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""
        fields = {}
        if "multipart/form-data" in content_type:
            parsed_fields, file_parts = parse_multipart(body, content_type)
            fields = dict(parsed_fields)
            # Los archivos (mp/xfr) pueden venir como file_parts (bytes): decodificar.
            for k, v in (file_parts or {}).items():
                if k not in fields:
                    fields[k] = v.decode("utf-8", errors="replace") if isinstance(v, bytes) else v
        else:
            try:
                fields = json.loads(body.decode("utf-8", errors="replace")) if body else {}
            except (json.JSONDecodeError, UnicodeDecodeError):
                fields = {}

        action = fields.get("action", "list")

        def _safe(name):
            return "".join(c if (c.isalnum() or c in "-_.") else "_" for c in str(name)).strip("_") or "item"

        try:
            # ---- Contrato GraphLibrary.jsx (grafos planos) ----
            if action == "list":
                graphs = []
                for mp_path in sorted(_glob.glob(os.path.join(flat_dir, "*.mp"))):
                    gid = os.path.splitext(os.path.basename(mp_path))[0]
                    with open(mp_path, "r", errors="replace") as f:
                        mp = f.read()
                    xfr_path = os.path.join(flat_dir, gid + ".xfr")
                    xfr = ""
                    if os.path.exists(xfr_path):
                        with open(xfr_path, "r", errors="replace") as f:
                            xfr = f.read()
                    graphs.append({"id": gid, "name": gid, "mp": mp, "xfr": xfr})
                self._json_response(200, {"graphs": graphs})
                return

            if action == "save":
                name = _safe(fields.get("name", "grafo"))
                mp = fields.get("mp", "") or ""
                xfr = fields.get("xfr", "") or ""
                with open(os.path.join(flat_dir, name + ".mp"), "w") as f:
                    f.write(mp)
                if xfr:
                    with open(os.path.join(flat_dir, name + ".xfr"), "w") as f:
                        f.write(xfr)
                self._json_response(200, {"saved": {"id": name, "name": name, "mp": mp, "xfr": xfr}})
                return

            # ---- Contrato GrafosPage.jsx (proyectos) ----
            if action == "list_projects":
                projects = []
                for d in sorted(os.listdir(root)):
                    dp = os.path.join(root, d)
                    if os.path.isdir(dp) and d != "_flat":
                        mp_count = len(_glob.glob(os.path.join(dp, "*.mp")))
                        projects.append({"name": d, "graphs": mp_count})
                self._json_response(200, {"projects": projects})
                return

            if action == "create_project":
                proj = _safe(fields.get("project", ""))
                os.makedirs(os.path.join(root, proj), exist_ok=True)
                self._json_response(200, {"created": proj})
                return

            if action == "list_files":
                proj = _safe(fields.get("project", ""))
                dp = os.path.join(root, proj)
                files_list = []
                if os.path.isdir(dp):
                    for fn in sorted(os.listdir(dp)):
                        fp = os.path.join(dp, fn)
                        if os.path.isfile(fp):
                            files_list.append({"name": fn, "size": os.path.getsize(fp)})
                self._json_response(200, {"files": files_list})
                return

            if action == "download":
                proj = _safe(fields.get("project", ""))
                fname = _safe(fields.get("file", ""))
                fp = os.path.join(root, proj, fname)
                if os.path.isfile(fp):
                    with open(fp, "r", errors="replace") as f:
                        content = f.read()
                    self._json_response(200, {"file": fname, "project": proj, "content": content})
                else:
                    self._json_response(200, {"error": "file not found", "content": ""})
                return

            if action == "upload":
                proj = _safe(fields.get("project", "default"))
                os.makedirs(os.path.join(root, proj), exist_ok=True)
                name = _safe(fields.get("name", "grafo"))
                uploaded = []
                mp = fields.get("mp", "") or ""
                xfr = fields.get("xfr", "") or ""
                if mp:
                    with open(os.path.join(root, proj, name + ".mp"), "w") as f:
                        f.write(mp)
                    uploaded.append(name + ".mp")
                if xfr:
                    with open(os.path.join(root, proj, name + ".xfr"), "w") as f:
                        f.write(xfr)
                    uploaded.append(name + ".xfr")
                self._json_response(200, {"uploaded": uploaded, "project": proj})
                return

            # ---- delete (ambos contratos) ----
            if action == "delete":
                gid = fields.get("id")
                if gid is not None:  # GraphLibrary plano
                    gid = _safe(gid)
                    for ext in (".mp", ".xfr"):
                        p = os.path.join(flat_dir, gid + ext)
                        if os.path.exists(p):
                            os.unlink(p)
                    self._json_response(200, {"deleted": gid})
                    return
                proj = _safe(fields.get("project", ""))
                fname = fields.get("file")
                if fname:
                    p = os.path.join(root, proj, _safe(fname))
                    if os.path.exists(p):
                        os.unlink(p)
                    self._json_response(200, {"deleted": f"{proj}/{fname}"})
                else:
                    import shutil
                    dp = os.path.join(root, proj)
                    if os.path.isdir(dp):
                        shutil.rmtree(dp)
                    self._json_response(200, {"deleted_project": proj})
                return

            self._json_response(400, {"error": f"accion desconocida: {action}"})
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._json_response(500, {"error": str(e)})

    def _handle_runtest_graph(self):
        """Regenera el PySpark DESDE el grafo y lo ejecuta con datos sinteticos.

        A diferencia de /runtest (que ejecuta el 'code' que manda el cliente y puede
        estar desactualizado), este endpoint recibe el grafo (.mp/.xfr/.dml/.pset) y
        REGENERA el PySpark en el servidor con la version actual del generador, luego
        lo prueba. Asi la prueba siempre usa codigo fresco.

        Acepta multipart/form-data (campos mp/xfr/dml/pset) o JSON con esas claves.
        Los datasets pueden venir en el campo 'datasets' (JSON string en multipart).
        Respuesta: igual que /runtest, mas 'code' (el PySpark regenerado) y 'warnings'.
        """
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")
        try:
            # Extraer grafo + datasets segun el tipo de contenido.
            datasets = []
            timeout = 120
            job_name = None
            if "multipart/form-data" in content_type:
                try:
                    mp_content, xfr_content, dml_content, pset_content, _target = \
                        self._parse_compile_request(body, content_type)
                except ValueError as ve:
                    self._json_response(400, {"error": str(ve)})
                    return
                fields, _fp = parse_multipart(body, content_type)
                ds_raw = fields.get("datasets", "")
                if ds_raw:
                    try:
                        datasets = json.loads(ds_raw)
                    except (json.JSONDecodeError, TypeError):
                        datasets = []
                timeout = int(fields.get("timeout", 120) or 120)
                job_name = fields.get("job_name") or fields.get("graph_name")
            else:
                try:
                    data = json.loads(body.decode("utf-8", errors="replace"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    self._json_response(400, {"error": "Invalid JSON body"})
                    return
                mp_content = data.get("mp", "")
                xfr_content = data.get("xfr", "")
                dml_content = data.get("dml", "")
                pset_content = data.get("pset", "")
                datasets = data.get("datasets", []) or []
                timeout = int(data.get("timeout", 120) or 120)
                job_name = data.get("job_name") or data.get("graph_name")
                if not mp_content:
                    self._json_response(400, {"error": "mp file is required"})
                    return

            # Regenerar el PySpark (target 'spark' SIEMPRE para poder ejecutarlo local).
            compiled = self._compile_graph(
                mp_content, xfr_content, dml_content, pset_content, target="spark"
            )
            code = compiled.get("code", "")
            if not (code or "").strip():
                self._json_response(200, {
                    "ok": False,
                    "error": "No se pudo generar codigo PySpark del grafo (revisa errores).",
                    "errors": compiled.get("errors", []),
                    "warnings": compiled.get("warnings", []),
                    "code": code,
                })
                return

            timeout = max(10, min(timeout, 600))
            if not job_name:
                job_name = compiled.get("graph_name") or None

            result = run_pyspark_test(code, datasets, timeout=timeout, job_name=job_name)
            # Adjuntar el codigo regenerado y warnings para que la UI pueda mostrarlos.
            result["code"] = code
            result["warnings"] = compiled.get("warnings", [])
            result["graph_name"] = compiled.get("graph_name", "")
            self._json_response(200, result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._json_response(500, {"error": str(e)})

    def _handle_runtest(self):
        """Ejecuta una prueba local del código PySpark con datos sintéticos.

        Body JSON:
        {
          "code": "<codigo pyspark>",          # requerido (target spark)
          "datasets": [{"node","io","rows"|"content","format"}],  # datos de entrada
          "timeout": 120                         # opcional
        }
        Respuesta: {ok, exit_code, timed_out, stdout, stderr, reads, writes, summary}
        """
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            try:
                data = json.loads(body.decode("utf-8", errors="replace"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._json_response(400, {"error": "Invalid JSON body"})
                return

            code = data.get("code", "")
            if not code.strip():
                self._json_response(400, {"error": "Falta 'code' (PySpark)"})
                return

            # Guardar de correr codigo Glue: requiere awsglue/AWS, no ejecutable local
            if "awsglue" in code or "GlueContext" in code:
                self._json_response(400, {
                    "error": "Solo se puede ejecutar localmente el target PySpark. "
                             "El código Glue necesita AWS. Compila con target 'spark'."
                })
                return

            datasets = data.get("datasets", []) or []
            timeout = int(data.get("timeout", 120))
            timeout = max(10, min(timeout, 600))
            job_name = data.get("job_name") or data.get("graph_name")

            result = run_pyspark_test(code, datasets, timeout=timeout, job_name=job_name)
            self._json_response(200, result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._json_response(500, {"error": str(e)})

    def _handle_runtest_stream(self):
        """Ejecuta el PySpark de prueba y transmite el output en vivo (SSE).

        Cada evento SSE es una linea JSON:
          data: {"type":"line","text":"..."}
          data: {"type":"done","ok":true,"summary":"...","reads":[...],"writes":[...]}
        """
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode("utf-8", errors="replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._json_response(400, {"error": "Invalid JSON body"})
            return

        code = data.get("code", "")
        # Si el cliente envia el grafo (.mp), REGENERAMOS el PySpark fresco en el
        # servidor con la version actual del generador. Asi la prueba nunca usa
        # codigo viejo cacheado en el navegador (que puede tener bugs ya corregidos).
        mp_content = data.get("mp", "")
        regen_warning = None
        if mp_content.strip():
            try:
                compiled = self._compile_graph(
                    mp_content,
                    data.get("xfr", ""),
                    data.get("dml", ""),
                    data.get("pset", ""),
                    target="spark",
                )
                fresh = compiled.get("code", "")
                if fresh.strip():
                    code = fresh
                    if not (data.get("job_name") or data.get("graph_name")):
                        data["job_name"] = compiled.get("graph_name") or None
            except Exception as e:
                regen_warning = f"No se pudo regenerar desde el grafo ({e}); se usa el codigo recibido."

        if not code.strip():
            self._json_response(400, {"error": "Falta 'code' (PySpark) o 'mp' (grafo)"})
            return
        if "awsglue" in code or "GlueContext" in code:
            self._json_response(400, {
                "error": "Solo se puede ejecutar localmente el target PySpark. "
                         "Compila con target 'spark'."
            })
            return

        datasets = data.get("datasets", []) or []
        timeout = int(data.get("timeout", 180))
        timeout = max(10, min(timeout, 600))
        job_name = data.get("job_name") or data.get("graph_name")

        # Cabeceras SSE
        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        def _send(obj):
            payload = "data: " + json.dumps(obj, default=str) + "\n\n"
            self.wfile.write(payload.encode("utf-8"))
            self.wfile.flush()

        try:
            if mp_content.strip() and not regen_warning:
                _send({"type": "line", "text": "[*] PySpark regenerado desde el grafo (codigo fresco)"})
            if regen_warning:
                _send({"type": "line", "text": f"[!] {regen_warning}"})
            for event in stream_pyspark_test(code, datasets, timeout=timeout, job_name=job_name):
                _send(event)
        except BrokenPipeError:
            # El cliente cerró la conexión
            return
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                _send({"type": "done", "ok": False, "summary": f"Error interno: {e}",
                       "reads": [], "writes": []})
            except Exception:
                pass

    def _handle_download(self):
        """Sirve un archivo de resultado de la prueba local para descargarlo.

        Query: ?f=<nombre.csv>  (solo el nombre del archivo, no rutas).
        El archivo debe existir DENTRO de BNX_LOCAL_OUTPUT_DIR. Se valida contra
        path-traversal comparando la ruta real resuelta con la carpeta permitida.
        """
        qs = parse_qs(urlparse(self.path).query)
        fname = (qs.get("f") or qs.get("file") or [""])[0].strip()
        if not fname:
            self._json_response(400, {"error": "Falta parametro 'f' (archivo)"})
            return

        base = os.path.realpath(BNX_LOCAL_OUTPUT_DIR)
        # Solo permitimos el nombre base del archivo (sin separadores de ruta).
        safe_name = os.path.basename(fname)
        target = os.path.realpath(os.path.join(base, safe_name))

        # Anti path-traversal: el objetivo debe quedar dentro de la carpeta base.
        if os.path.commonpath([base, target]) != base or not os.path.isfile(target):
            self._json_response(404, {"error": "Archivo no encontrado"})
            return

        try:
            with open(target, "rb") as fh:
                data = fh.read()
        except OSError as e:
            self._json_response(500, {"error": f"No se pudo leer: {e}"})
            return

        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header(
            "Content-Disposition", f'attachment; filename="{safe_name}"'
        )
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle_awscode(self):
        """Genera el código PySpark AUTOCONTENIDO (datos sintéticos embebidos)
        listo para subir al pipeline AWS.

        Body JSON: {"code": "<pyspark>", "datasets": [...], "keep_writes": true}
        Respuesta: {"code": "<pyspark autocontenido>"}
        """
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode("utf-8", errors="replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._json_response(400, {"error": "Invalid JSON body"})
            return

        code = data.get("code", "")
        # Si el cliente envia el grafo (.mp), REGENERAMOS el PySpark fresco para que
        # el codigo enviado a AWS use siempre la version actual del generador (evita
        # que el navegador mande codigo viejo con bugs ya corregidos).
        mp_content = data.get("mp", "")
        if mp_content.strip():
            try:
                compiled = self._compile_graph(
                    mp_content, data.get("xfr", ""), data.get("dml", ""),
                    data.get("pset", ""), target="spark",
                )
                fresh = compiled.get("code", "")
                if fresh.strip():
                    code = fresh
                    if not data.get("job_name"):
                        data["job_name"] = compiled.get("graph_name") or data.get("job_name")
            except Exception as e:
                print(f"  [awscode] no se pudo regenerar desde grafo: {e}")

        if not code.strip():
            self._json_response(400, {"error": "Falta 'code' (PySpark) o 'mp' (grafo)"})
            return
        if "awsglue" in code or "GlueContext" in code:
            self._json_response(400, {
                "error": "El código autocontenido solo se genera para target PySpark. "
                         "Compila con target 'spark'."
            })
            return

        datasets = data.get("datasets", []) or []
        keep_writes = bool(data.get("keep_writes", True))
        bucket = data.get("bucket")
        job_name = data.get("job_name")
        try:
            result = build_aws_selfcontained_code(
                code, datasets, keep_writes=keep_writes, bucket=bucket, job_name=job_name,
            )
            self._json_response(200, {
                "code": result["code"],
                "output_paths": result["output_paths"],
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._json_response(500, {"error": str(e)})

    def _handle_datagen(self):
        """Genera datos sintéticos redactados.

        Acepta JSON con dos modos:
        1. Desde grafo:  {"mp": "...", "xfr": "...", "dml": "...",
                          "n_rows": 10, "format": "csv"|"json"}
           → infiere el esquema por nodo y genera datos para cada nodo con columnas.
        2. Manual:       {"columns": [{"name","type","pii"?}, ...],
                          "n_rows": 10, "format": "csv"|"json"}
           → genera datos directamente para el esquema provisto.

        Respuesta:
        {
          "schema": [{"node","node_type","columns":[{"name","type","pii"}]}],
          "datasets": [{"node","format","content","columns","rows"}],
          "mode": "graph"|"manual"
        }
        """
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            try:
                data = json.loads(body.decode("utf-8", errors="replace"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._json_response(400, {"error": "Invalid JSON body"})
                return

            n_rows = int(data.get("n_rows", 10))
            n_rows = max(1, min(n_rows, 10000))  # límite de seguridad
            fmt = data.get("format", "csv")
            seed = data.get("seed")
            delimiter = data.get("delimiter", ",")

            # --- MODO MANUAL: columnas provistas directamente ---
            manual_columns = data.get("columns")
            if manual_columns:
                gen = build_synthetic_data(
                    manual_columns, n_rows=n_rows, fmt=fmt, seed=seed, delimiter=delimiter
                )
                manual_io = data.get("io", "output")
                self._json_response(200, {
                    "mode": "manual",
                    "schema": [{
                        "node": data.get("node_name", "manual"),
                        "node_type": "MANUAL",
                        "io": manual_io,
                        "columns": gen["columns"],
                    }],
                    "datasets": [{
                        "node": data.get("node_name", "manual"),
                        "node_type": "MANUAL",
                        "io": manual_io,
                        "format": gen["format"],
                        "content": gen["content"],
                        "columns": gen["columns"],
                        "rows": gen["rows"],
                    }],
                })
                return

            # --- MODO GRAFO: inferir esquema del grafo ---
            mp_content = data.get("mp", "")
            if not mp_content:
                self._json_response(400, {
                    "error": "Provide either 'columns' (manual) or 'mp' (graph)"
                })
                return

            xfr_content = data.get("xfr", "")
            dml_content = data.get("dml", "")

            mp_path = self._save_temp(mp_content, ".mp")
            xfr_path = self._save_temp(xfr_content, ".xfr") if xfr_content else None
            dml_path = self._save_temp(dml_content, ".dml") if dml_content else None

            try:
                ast = parse_project(mp_path)
                xfr_rules = parse_xfr(xfr_path) if xfr_path else {}
                # Desempaquetar reglas especiales (igual que en /compile)
                xfr_rules = self._prepare_xfr_rules(xfr_rules, ast, mp_path)
                dml_data = parse_dml(dml_path) if dml_path else {}
                dml_schema = dml_data.get("schema", {})

                schema = infer_schema_from_graph(ast, xfr_rules, dml_schema)

                # Filtrar solo nodos objetivo (opcional): por defecto todos con columnas
                target_node = data.get("target_node")
                if target_node:
                    schema = [s for s in schema
                              if s["node"].lower() == target_node.lower()]

                datasets = []
                for node_schema in schema:
                    gen = build_synthetic_data(
                        node_schema["columns"], n_rows=n_rows, fmt=fmt,
                        seed=seed, delimiter=delimiter,
                    )
                    datasets.append({
                        "node": node_schema["node"],
                        "node_type": node_schema.get("node_type"),
                        "io": node_schema.get("io", "output"),
                        "format": gen["format"],
                        "content": gen["content"],
                        "columns": gen["columns"],
                        "rows": gen["rows"],
                    })

                resp = {
                    "mode": "graph",
                    "schema": schema,
                    "datasets": datasets,
                }
                if not datasets:
                    resp["message"] = (
                        "No se pudo inferir el esquema de ningun nodo. "
                        "Este grafo no incluye definiciones de campos (.dml o transformaciones "
                        "con columnas). Usa el modo Manual para definir el esquema, "
                        "o adjunta un .dml/.xfr con los campos."
                    )
                self._json_response(200, resp)
            finally:
                os.unlink(mp_path)
                if xfr_path:
                    os.unlink(xfr_path)
                if dml_path:
                    os.unlink(dml_path)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self._json_response(500, {"error": str(e)})

    def _prepare_xfr_rules(self, xfr_rules, ast, mp_path):
        """Desempaqueta _multi_xfr / _raw_dml / _global_dml_fields y aplica
        embedded transforms, igual que /compile, para que la inferencia de
        esquema vea las mismas reglas que el codegen."""
        if "_multi_xfr" in xfr_rules:
            multi = xfr_rules.pop("_multi_xfr")
            transform_nodes = [n for n in ast.get("nodes", [])
                               if n["type"].upper() == "TRANSFORM"]
            from main import _assign_multi_xfr
            _assign_multi_xfr(multi, transform_nodes, xfr_rules)
        elif "_raw_dml" in xfr_rules:
            raw_rule = xfr_rules.pop("_raw_dml")
            if raw_rule.get("dml_fields"):
                xfr_rules["_global_dml_fields"] = raw_rule["dml_fields"]
            else:
                xfr_rules["_global_raw_dml"] = raw_rule

        if "_global_dml_fields" in xfr_rules:
            dml_fields_list = xfr_rules.pop("_global_dml_fields")
            for nd in ast.get("nodes", []):
                if nd["type"].upper() == "TRANSFORM":
                    nid = nd["id"].lower()
                    if nid not in xfr_rules:
                        xfr_rules[nid] = {"dml_fields": dml_fields_list}
                        break

        # Embedded transforms (GDE)
        try:
            from main import _extract_embedded_transforms, _apply_embedded_transforms
            with open(mp_path, "r", errors="replace") as f:
                raw = f.read().replace('\x00', '')
            embedded = _extract_embedded_transforms(raw)
            if (embedded.get("transforms") or embedded.get("keys")
                    or embedded.get("keys_by_vertex") or embedded.get("filters")
                    or embedded.get("filters_by_vertex") or embedded.get("keeps")
                    or embedded.get("record_by_vertex")):
                node_map = {}
                for nd in ast.get("nodes", []):
                    vid = nd.get("vertex_id", nd["id"])
                    node_map[vid] = {
                        "name": nd["id"],
                        "comp_type": nd.get("name", nd["id"]),
                        "proto_type": nd.get("type", "TRANSFORM"),
                        "is_sort": nd.get("is_sort", False),
                    }
                _apply_embedded_transforms(node_map, embedded, xfr_rules)
        except Exception as e:
            print(f"  [datagen] embedded transforms skipped: {e}")

        return xfr_rules

    def _compile_graph(self, mp_content, xfr_content="", dml_content="",
                       pset_content="", target="glue"):
        """Genera el codigo (PySpark/Glue/Flink/Python) desde el grafo Ab Initio.

        Reune todo el pipeline grafo->codigo (parseo .mp/.xfr/.dml/.pset, embedded
        transforms, resolucion de paths, validacion y generacion). Devuelve un dict
        con: code, nodes, edges, errors, warnings, accuracy, graph_name, description,
        extractor_code, params. Reutilizable tanto por /compile como por /runtest/graph
        (asi la prueba SIEMPRE usa codigo recien generado, no el que este en pantalla).
        """
        mp_path = xfr_path = dml_path = None
        try:
            # Save to temp files
            mp_path = self._save_temp(mp_content, ".mp")
            xfr_path = self._save_temp(xfr_content, ".xfr") if xfr_content else None
            dml_path = self._save_temp(dml_content, ".dml") if dml_content else None

            # Parse
            ast = parse_project(mp_path)
            dag = build_dag(ast)
            xfr_rules = parse_xfr(xfr_path) if xfr_path else {}
            
            # Parse PSET and merge into abinitio_params
            pset_params = {}
            if pset_content:
                pset_path_tmp = self._save_temp(pset_content, ".pset")
                try:
                    pset_params = parse_pset(pset_path_tmp)
                    # Merge pset params into ast abinitio_params
                    if "abinitio_params" not in ast:
                        ast["abinitio_params"] = {}
                    ast["abinitio_params"].update(pset_params)
                    print(f"  [pset] Loaded {len(pset_params)} parameters from .pset: {list(pset_params.keys())[:20]}")
                except Exception as e:
                    print(f"  [pset] Warning: could not parse pset: {e}")
                finally:
                    os.unlink(pset_path_tmp)
            # Remove placeholder entries and handle raw DML
            if "_multi_xfr" in xfr_rules:
                multi = xfr_rules.pop("_multi_xfr")
                transform_nodes = [n for n in ast.get("nodes", []) if n["type"].upper() == "TRANSFORM"]
                from main import _assign_multi_xfr
                _assign_multi_xfr(multi, transform_nodes, xfr_rules)
            elif "_raw_dml" in xfr_rules:
                raw_rule = xfr_rules.pop("_raw_dml")
                if raw_rule.get("dml_fields"):
                    xfr_rules["_global_dml_fields"] = raw_rule["dml_fields"]
                else:
                    xfr_rules["_global_raw_dml"] = raw_rule
            xfr_rules = {k: v for k, v in xfr_rules.items()
                         if not (v.get("select") == "*" and v.get("where") is None and len(v) == 2)}
            
            # Apply _global_dml_fields to first TRANSFORM without rules
            if "_global_dml_fields" in xfr_rules:
                dml_fields_list = xfr_rules.pop("_global_dml_fields")
                for nd in ast.get("nodes", []):
                    if nd["type"].upper() == "TRANSFORM":
                        nid = nd["id"].lower()
                        if nid not in xfr_rules:
                            xfr_rules[nid] = {"dml_fields": dml_fields_list}
                            break
            dml_data = parse_dml(dml_path) if dml_path else {}
            dml_schema = dml_data.get("schema", {})

            # Extract embedded transforms from GDE format
            from main import _extract_embedded_transforms, _apply_embedded_transforms
            with open(mp_path, "r", errors="replace") as f:
                raw = f.read().replace('\x00', '')
            embedded = _extract_embedded_transforms(raw)
            if embedded["transforms"] or embedded["keys"] or embedded.get("keys_by_vertex") or embedded["filters"] or embedded.get("filters_by_vertex") or embedded.get("keeps"):
                node_map = {}
                for nd in ast.get("nodes", []):
                    vid = nd.get("vertex_id", nd["id"])
                    node_map[vid] = {
                        "name": nd["id"],
                        "comp_type": nd.get("name", nd["id"]),
                        "proto_type": nd.get("type", "TRANSFORM"),
                        "is_sort": nd.get("is_sort", False),
                    }
                _apply_embedded_transforms(node_map, embedded, xfr_rules)

            # Apply data_path from GDE nodes to xfr_rules (SOURCE/SINK path resolution)
            for nd in ast.get("nodes", []):
                if "data_path" in nd:
                    ntype = nd["type"].upper()
                    nid_lower = nd["id"].lower()
                    # Clean the path: extract just the filename/relative part
                    raw_path = nd["data_path"]
                    # Remove system prefixes that shouldn't be in S3 paths
                    clean = raw_path
                    clean = re.sub(r'^file:', '', clean)
                    # Remove unresolved $VAR and $\{VAR\} references (system dirs like AI_SERIAL)
                    clean = re.sub(r'\$\\?\{?\w+\\?\}?/', '', clean)
                    # Normalize double slashes
                    clean = re.sub(r'/+', '/', clean)
                    # Strip leading slash
                    clean = clean.lstrip('/')
                    if not clean:
                        clean = nid_lower
                    if ntype == "SOURCE":
                        if nid_lower not in xfr_rules:
                            xfr_rules[nid_lower] = {}
                        xfr_rules[nid_lower]["path"] = clean  # relative path, codegen adds PARAMS.BASE_PATH
                        xfr_rules[nid_lower]["path_resolved"] = True
                    elif ntype == "SINK":
                        if nid_lower not in xfr_rules:
                            xfr_rules[nid_lower] = {}
                        xfr_rules[nid_lower]["path"] = clean
                        xfr_rules[nid_lower]["path_resolved"] = True

            # Detect missing external .xfr references and add warnings
            missing_xfr = []
            with open(mp_path, "r", errors="replace") as f_mp:
                mp_raw = f_mp.read().replace('\x00', '')
            for m in re.finditer(r'XXparameter\|transform\d*\|\$([^|]+\.xfr)\|', mp_raw):
                xfr_ref = m.group(1)
                # Check if any xfr content was provided that might cover this
                if not xfr_content:
                    missing_xfr.append(xfr_ref)
            # Deduplicate
            missing_xfr = list(dict.fromkeys(missing_xfr))

            # Validate
            errors, warnings = validate(dag, xfr_rules, dml_schema)
            
            # Add missing xfr warnings
            if missing_xfr and not xfr_content:
                for xf in missing_xfr[:5]:
                    warnings.insert(0, f"⚠️ XFR externo no proporcionado: {xf}")
                if len(missing_xfr) > 5:
                    warnings.insert(0, f"⚠️ {len(missing_xfr)} archivos .xfr externos referenciados — sube los .xfr para generar transforms completos")

            # Generate code
            code = ""
            blocking = [e for e in errors if "no parent nod" not in e and "nothing to write" not in e and "has no parent" not in e and "needs 2 parents" not in e]
            if blocking:
                print(f"  [!] Blocking errors: {blocking[:3]}")
            if not blocking:
                out_path = self._save_temp("", ".py")
                # Parametros para la clase PARAMS: graph params del .mp (abinitio_params)
                # con el pset mergeado encima (ya se hizo el .update mas arriba).
                all_params_for_codegen = dict(ast.get("abinitio_params", {}))
                print(f"  [params] {len(all_params_for_codegen)} params para PARAMS: {list(all_params_for_codegen.keys())[:20]}")
                if target == "spark":
                    generate_spark(dag, out_path, xfr_rules, pset_params=all_params_for_codegen)
                elif target == "flink":
                    generate_flink(dag, out_path, xfr_rules)
                elif target == "python":
                    from main import _generate_pandas
                    _generate_pandas(dag, out_path, xfr_rules)
                else:
                    generate_glue(dag, out_path, xfr_rules, pset_params=all_params_for_codegen)
                with open(out_path, "r") as f:
                    code = f.read()
                os.unlink(out_path)

            # Accuracy
            acc = compute_accuracy(dag, xfr_rules, dml_schema)

            # Build response
            nodes = []
            node_ids = set()
            for node in dag.execution_order:
                nodes.append({
                    "id": node.id, "name": node.name, "type": node.type,
                    "parents": node.parents, "children": node.children,
                })
                node_ids.add(node.id)
            # Filter edges: only include edges where both endpoints exist as nodes
            all_edges = ast.get("edges", [])
            edges = [{"from": e["from"], "to": e["to"]} for e in all_edges
                     if e["from"] in node_ids and e["to"] in node_ids]
            print(f"  [resp] Returning {len(nodes)} nodes, {len(edges)} edges (from {len(all_edges)} raw)")
            if len(edges) != len(all_edges):
                bad = [e for e in all_edges if e["from"] not in node_ids or e["to"] not in node_ids]
                for b in bad[:5]:
                    print(f"  [resp] DROPPED edge: {b['from']} -> {b['to']}")

            # Detect DB sources → generate extractor program
            db_nodes = [n for n in ast.get("nodes", []) if n.get("db_source")]
            extractor_code = ""
            if db_nodes:
                from datetime import datetime
                ext_lines = []
                ext_lines.append(f'"""\n[*] BNX EXTRACTOR — Database to S3\nGenerated at: {datetime.now()}\nThis program extracts data from DB sources and lands it in S3.\nRun this BEFORE the transform job.\n"""\n')
                ext_lines.append("import boto3")
                ext_lines.append("from pyspark.sql import SparkSession\n")
                ext_lines.append("spark = SparkSession.builder.appName('BNX_Extractor').getOrCreate()\n")
                ext_lines.append('print("[*] BNX Extractor Started")\n')
                ext_lines.append("# " + "=" * 50)
                ext_lines.append("# CONFIGURE: Update connection details below")
                ext_lines.append("# " + "=" * 50)
                ext_lines.append('JDBC_URL = "jdbc:teradata://YOUR_HOST/DATABASE=YOUR_DB"')
                ext_lines.append('JDBC_USER = "YOUR_USER"  # Use AWS Secrets Manager in production')
                ext_lines.append('JDBC_PASSWORD = "YOUR_PASSWORD"  # Use AWS Secrets Manager in production')
                ext_lines.append(f'S3_LANDING = "s3://datalake-bnx-scripts-dev/landing/"\n')
                
                for db_node in db_nodes:
                    name = db_node["id"]
                    db = db_node["db_source"]
                    dbms = db.get("dbms", "unknown")
                    query = db.get("query", f"SELECT * FROM {name}")
                    safe_name = name.lower()
                    
                    ext_lines.append(f'# [{dbms.upper()}] {name}')
                    ext_lines.append(f'{safe_name}_df = spark.read.format("jdbc") \\')
                    ext_lines.append(f'    .option("url", JDBC_URL) \\')
                    ext_lines.append(f'    .option("user", JDBC_USER) \\')
                    ext_lines.append(f'    .option("password", JDBC_PASSWORD) \\')
                    ext_lines.append(f'    .option("query", """{query}""") \\')
                    ext_lines.append(f'    .load()')
                    ext_lines.append(f'{safe_name}_df.write.mode("overwrite").parquet(f"{{S3_LANDING}}{safe_name}/")')
                    ext_lines.append(f'print(f"[>] Extracted {{name}}: {{{safe_name}_df.count()}} rows")\n')
                
                ext_lines.append('print("[ok] BNX Extractor Finished")')
                extractor_code = "\n".join(ext_lines)

            # Extract graph name from params
            graph_params = ast.get("abinitio_params", {})
            graph_name = graph_params.get("AI_JOBNAME", "") or graph_params.get("PLAN_NAME", "") or ""

            # Descripcion en lenguaje natural del grafo (determinística) a partir
            # del orden de ejecucion del DAG. reads/writes van vacios porque en el
            # Compiler aun no se ejecuto con datos (solo describimos la estructura).
            desc_steps = [{"type": n.type.upper(), "name": n.name} for n in dag.execution_order]
            graph_description = _describe_graph(desc_steps, [], [], job_name=(graph_name or "grafo"))

            return {
                "nodes": nodes,
                "edges": edges,
                "errors": errors,
                "warnings": warnings,
                "code": code,
                "extractor_code": extractor_code,
                "has_db_sources": bool(db_nodes),
                "db_sources_count": len(db_nodes),
                "accuracy": acc,
                "graph_name": graph_name,
                "description": graph_description,
                "params": {k: v for k, v in list(ast.get("abinitio_params", {}).items())[:20]},
            }
        finally:
            # Cleanup temp files
            try:
                os.unlink(mp_path)
            except OSError:
                pass
            if xfr_path:
                try:
                    os.unlink(xfr_path)
                except OSError:
                    pass
            if dml_path:
                try:
                    os.unlink(dml_path)
                except OSError:
                    pass

    def _parse_compile_request(self, body, content_type):
        """Extrae mp/xfr/dml/pset/target de un request (multipart o JSON).

        Devuelve (mp_content, xfr_content, dml_content, pset_content, target) o
        lanza ValueError con un mensaje si el request es invalido / falta el .mp.
        """
        mp_content = ""
        xfr_content = ""
        dml_content = ""
        pset_content = ""
        target = "glue"

        if "multipart/form-data" in content_type:
            fields, file_parts = parse_multipart(body, content_type)
            target = fields.get("target", "glue")
            if "mp" in file_parts:
                mp_content = file_parts["mp"]  # keep as bytes for GDE
            elif "mp" in fields:
                mp_content = fields["mp"]
            if "xfr" in file_parts:
                xfr_content = file_parts["xfr"].decode("utf-8", errors="replace")
            elif "xfr" in fields:
                xfr_content = fields["xfr"]
            if "dml" in file_parts:
                dml_content = file_parts["dml"].decode("utf-8", errors="replace")
            elif "dml" in fields:
                dml_content = fields["dml"]
            if "pset" in file_parts:
                pset_content = file_parts["pset"].decode("utf-8", errors="replace")
            elif "pset" in fields:
                pset_content = fields["pset"]
        else:
            try:
                data = json.loads(body.decode("utf-8", errors="replace"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise ValueError("Invalid request format")
            mp_content = data.get("mp", "")
            xfr_content = data.get("xfr", "")
            dml_content = data.get("dml", "")
            pset_content = data.get("pset", "")
            target = data.get("target", "glue")

        if not mp_content:
            raise ValueError("mp file is required")
        return mp_content, xfr_content, dml_content, pset_content, target

    def _handle_optimize(self):
        """Optimiza el PySpark por REGLAS (sin IA) para mejorar performance.

        Body JSON:
          {"code": "<pyspark>"}                      # optimiza el codigo recibido
          {"mp": "...", "xfr": "...", ...}           # regenera fresco y optimiza
        Respuesta:
          {"ok": true, "code": <optimizado>, "original_code": <base>,
           "changes": [...], "total_changes": N, "summary": {...},
           "original_lines": N, "optimized_lines": N}
        """
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode("utf-8", errors="replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._json_response(400, {"error": "Invalid JSON body"})
            return

        code = data.get("code", "")
        # Si viene el grafo, regeneramos PySpark fresco (target spark) antes de optimizar.
        mp_content = data.get("mp", "")
        if mp_content.strip():
            try:
                compiled = self._compile_graph(
                    mp_content, data.get("xfr", ""), data.get("dml", ""),
                    data.get("pset", ""), target="spark",
                )
                fresh = compiled.get("code", "")
                if fresh.strip():
                    code = fresh
            except Exception as e:
                print(f"  [optimize] no se pudo regenerar desde grafo: {e}")

        if not code.strip():
            self._json_response(400, {"error": "Falta 'code' (PySpark) o 'mp' (grafo)"})
            return
        if "awsglue" in code or "GlueContext" in code:
            self._json_response(400, {
                "error": "La optimizacion de performance aplica al target PySpark. "
                         "Compila con target 'spark'."
            })
            return

        try:
            result = optimize_pyspark(code)
            result["ok"] = True
            result["original_code"] = code
            self._json_response(200, result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._json_response(500, {"error": str(e)})

    def _handle_optimize_compare(self):
        """Corre el PySpark ORIGINAL y el OPTIMIZADO con los MISMOS datos, mide
        tiempos y compara salidas para demostrar la mejora de performance.

        Body JSON:
          {"mp": "...", "xfr": "...", "datasets": [...], "timeout": 180}
          (o {"code": "<pyspark>"} si no se envia el grafo)
        Respuesta:
          {"ok": bool,
           "original": {"seconds","ok","writes":[...]},
           "optimized": {"seconds","ok","writes":[...]},
           "speedup": float,          # original/optimizado (>1 = mas rapido)
           "faster_pct": float,       # % de mejora
           "equivalent": bool,        # mismas salidas (nodos+filas)
           "changes": [...], "total_changes": N, "summary": {...}}
        """
        import time as _time

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode("utf-8", errors="replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._json_response(400, {"error": "Invalid JSON body"})
            return

        code = data.get("code", "")
        mp_content = data.get("mp", "")
        if mp_content.strip():
            try:
                compiled = self._compile_graph(
                    mp_content, data.get("xfr", ""), data.get("dml", ""),
                    data.get("pset", ""), target="spark",
                )
                fresh = compiled.get("code", "")
                if fresh.strip():
                    code = fresh
            except Exception as e:
                print(f"  [optimize/compare] no se pudo regenerar desde grafo: {e}")

        if not code.strip():
            self._json_response(400, {"error": "Falta 'code' (PySpark) o 'mp' (grafo)"})
            return

        datasets = data.get("datasets", []) or []
        timeout = max(10, min(int(data.get("timeout", 180) or 180), 600))

        # Optimizar. 'opt' (con coalesce) es lo que se reporta/descarga.
        # 'bench_code' (sin coalesce) es lo que se MIDE: el coalesce(1) con volumen
        # alto fuerza 1 particion y ralentiza, distorsionando el benchmark.
        opt = optimize_pyspark(code)
        bench_code = optimize_pyspark(code, include_coalesce=False).get("code", code)

        # --- Simulacion tipo nube: 2 workers (local[2]) + datos amplificados ---
        # Con pocos datos en local[1] las optimizaciones no se notan (domina el
        # overhead de arranque). Amplificamos el volumen y usamos 2 cores para que
        # cache/broadcast/coalesce muestren su efecto, como en un cluster real.
        SIM_MASTER = "local[2]"
        SIM_WORKERS = 2
        TARGET_ROWS = 60000  # volumen objetivo del benchmark
        try:
            base_rows = max(
                (len(json.loads(d.get("content", "[]"))) if isinstance(d.get("content"), str) else len(d.get("content", [])))
                for d in datasets
            ) if datasets else 10
        except Exception:
            base_rows = 10
        base_rows = max(1, base_rows)
        amplify = max(1, min(2000, TARGET_ROWS // base_rows))
        sim_rows = base_rows * amplify

        def _run_timed(src):
            t0 = _time.perf_counter()
            res = run_pyspark_test(src, datasets, timeout=timeout,
                                   job_name=data.get("job_name") or "bnx-compare",
                                   master=SIM_MASTER, amplify=amplify)
            secs = _time.perf_counter() - t0
            return {
                "seconds": round(secs, 2),
                "ok": res.get("ok", False),
                "writes": res.get("writes", []),
                "reads": res.get("reads", []),
                "summary": res.get("summary", ""),
                "stderr_tail": (res.get("stderr", "") or "")[-1200:] if not res.get("ok") else "",
            }

        try:
            original = _run_timed(code)
            optimized = _run_timed(bench_code)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._json_response(500, {"error": str(e)})
            return

        # Equivalencia de salidas: mismos nodos con mismas filas.
        def _writes_map(w):
            return {x.get("var"): x.get("rows") for x in (w or [])}
        equivalent = _writes_map(original["writes"]) == _writes_map(optimized["writes"])

        so, sp = original["seconds"], optimized["seconds"]
        speedup = round(so / sp, 2) if sp > 0 else None
        faster_pct = round((so - sp) / so * 100, 1) if so > 0 else None

        self._json_response(200, {
            "ok": original["ok"] and optimized["ok"],
            "original": original,
            "optimized": optimized,
            "speedup": speedup,
            "faster_pct": faster_pct,
            "equivalent": equivalent,
            "changes": opt.get("changes", []),
            "total_changes": opt.get("total_changes", 0),
            "summary": opt.get("summary", {}),
            "optimized_code": opt.get("code", code),
            # Info de la simulacion tipo nube (para mostrar en la UI).
            "sim_workers": SIM_WORKERS,
            "sim_rows": sim_rows,
            "sim_amplify": amplify,
        })

    def _handle_compile(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        try:
            try:
                mp_content, xfr_content, dml_content, pset_content, target = \
                    self._parse_compile_request(body, content_type)
            except ValueError as ve:
                self._json_response(400, {"error": str(ve)})
                return

            result = self._compile_graph(
                mp_content, xfr_content, dml_content, pset_content, target
            )
            self._json_response(200, result)

        except Exception as e:
            import traceback
            err_msg = str(e)
            traceback.print_exc()
            self._json_response(500, {"error": err_msg})

    def _save_temp(self, content, suffix):
        if isinstance(content, bytes):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb")
            tmp.write(content)
        else:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="w", encoding="utf-8", errors="replace")
            tmp.write(content)
        tmp.close()
        return tmp.name

    def _json_response(self, status, data):
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format, *args):
        # Quieter logging
        if "/api" in str(args[0]) or "POST" in str(args[0]):
            print(f"  [{args[1]}] {args[0]}")


if __name__ == "__main__":
    print(f"[*] BNX Convertidor - Local Server")
    print(f"[*] Port: {PORT}")
    if UI_DIR:
        print(f"[*] UI: {UI_DIR}")
    print(f"[*] API: http://localhost:{PORT}/compile (POST)")
    print(f"[*] Open: http://localhost:{PORT}")
    print()

    class _BNXServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True  # evita "Address already in use" al reiniciar
        daemon_threads = True

    with _BNXServer(("", PORT), BNXHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Stopped")
