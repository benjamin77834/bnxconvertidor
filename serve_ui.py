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
import tempfile
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from io import BytesIO

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

PORT = 8080
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
            self._handle_library()
        elif "/pipeline/status" in path:
            self._handle_pipeline_status()
        elif "/pipeline" in path:
            self._handle_pipeline()
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

        # Serve static UI files
        if UI_DIR:
            # SPA fallback: serve index.html for all non-file routes
            file_path = os.path.join(UI_DIR, path.lstrip("/"))
            if not os.path.isfile(file_path) and not path.startswith("/api"):
                self.path = "/index.html"
            super().do_GET()
        else:
            self._json_response(200, {"message": "BNX API running", "endpoints": ["/api/health", "/compile (POST)"]})

    def _handle_compile(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        try:
            mp_content = ""
            xfr_content = ""
            dml_content = ""
            pset_content = ""
            target = "glue"

            if "multipart/form-data" in content_type:
                # Parse multipart form data
                import cgi
                environ = {
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": content_type,
                    "CONTENT_LENGTH": str(len(body)),
                }
                fp = BytesIO(body)
                form = cgi.FieldStorage(fp=fp, environ=environ, keep_blank_values=True)
                
                for key in form.keys():
                    item = form[key]
                    if isinstance(item, list):
                        item = item[0]
                    if hasattr(item, 'file') and item.file:
                        file_data = item.file.read()
                        # Keep as bytes for .mp files (may be binary GDE format)
                        if key == "mp" or (hasattr(item, 'filename') and item.filename and item.filename.endswith('.mp')):
                            mp_content = file_data  # keep as bytes
                        elif key == "xfr" or (hasattr(item, 'filename') and item.filename and item.filename.endswith('.xfr')):
                            xfr_content = file_data.decode("utf-8", errors="replace") if isinstance(file_data, bytes) else file_data
                        elif key == "dml" or (hasattr(item, 'filename') and item.filename and item.filename.endswith('.dml')):
                            dml_content = file_data.decode("utf-8", errors="replace") if isinstance(file_data, bytes) else file_data
                        elif key == "pset" or (hasattr(item, 'filename') and item.filename and item.filename.endswith('.pset')):
                            pset_content = file_data.decode("utf-8", errors="replace") if isinstance(file_data, bytes) else file_data
                    elif hasattr(item, 'value'):
                        val = item.value if isinstance(item.value, str) else item.value.decode()
                        if key == "target":
                            target = val
                        elif key == "mp":
                            mp_content = val
            else:
                # JSON body
                try:
                    data = json.loads(body.decode("utf-8"))
                    mp_content = data.get("mp", "")
                    xfr_content = data.get("xfr", "")
                    dml_content = data.get("dml", "")
                    pset_content = data.get("pset", "")
                    target = data.get("target", "glue")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    self._json_response(400, {"error": "Invalid request format"})
                    return

            if not mp_content:
                self._json_response(400, {"error": "mp file is required"})
                return

            # Save to temp files
            mp_path = self._save_temp(mp_content, ".mp")
            xfr_path = self._save_temp(xfr_content, ".xfr") if xfr_content else None
            dml_path = self._save_temp(dml_content, ".dml") if dml_content else None

            # Parse
            ast = parse_project(mp_path)
            dag = build_dag(ast)
            xfr_rules = parse_xfr(xfr_path) if xfr_path else {}
            dml_data = parse_dml(dml_path) if dml_path else {}
            dml_schema = dml_data.get("schema", {})

            # Extract embedded transforms from GDE format
            from main import _extract_embedded_transforms, _apply_embedded_transforms
            with open(mp_path, "r", errors="replace") as f:
                raw = f.read().replace('\x00', '')
            embedded = _extract_embedded_transforms(raw)
            if embedded["transforms"] or embedded["keys"] or embedded["filters"]:
                node_map = {}
                for nd in ast.get("nodes", []):
                    node_map[nd["id"]] = {"name": nd["id"], "comp_type": nd.get("name", nd["id"])}
                _apply_embedded_transforms(node_map, embedded, xfr_rules)

            # Validate
            errors, warnings = validate(dag, xfr_rules, dml_schema)

            # Generate code
            code = ""
            if not [e for e in errors if "no parent nod" not in e and "nothing to write" not in e]:
                out_path = self._save_temp("", ".py")
                if target == "spark":
                    generate_spark(dag, out_path, xfr_rules)
                elif target == "flink":
                    generate_flink(dag, out_path, xfr_rules)
                elif target == "python":
                    from main import _generate_pandas
                    _generate_pandas(dag, out_path, xfr_rules)
                else:
                    generate_glue(dag, out_path, xfr_rules)
                with open(out_path, "r") as f:
                    code = f.read()
                os.unlink(out_path)

            # Accuracy
            acc = compute_accuracy(dag, xfr_rules, dml_schema)

            # Build response
            nodes = []
            for node in dag.execution_order:
                nodes.append({
                    "id": node.id, "name": node.name, "type": node.type,
                    "parents": node.parents, "children": node.children,
                })
            edges = [{"from": e["from"], "to": e["to"]} for e in ast.get("edges", [])]

            self._json_response(200, {
                "nodes": nodes,
                "edges": edges,
                "errors": errors,
                "warnings": warnings,
                "code": code,
                "accuracy": acc,
                "params": ast.get("abinitio_params", {}),
            })

            # Cleanup
            os.unlink(mp_path)
            if xfr_path: os.unlink(xfr_path)
            if dml_path: os.unlink(dml_path)

        except Exception as e:
            import traceback
            err_msg = str(e)
            traceback.print_exc()
            self._json_response(500, {"error": err_msg})

    def _handle_library(self):
        """Biblioteca de grafos — lee/escribe en carpeta local projects/."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        projects_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects")
        os.makedirs(projects_dir, exist_ok=True)

        # Parse form
        action = "list"
        fields_data = {}
        files_data = {}

        if "multipart/form-data" in content_type:
            import cgi
            environ = {"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type, "CONTENT_LENGTH": str(len(body))}
            fp = BytesIO(body)
            form = cgi.FieldStorage(fp=fp, environ=environ, keep_blank_values=True)
            for key in form.keys():
                item = form[key]
                if isinstance(item, list):
                    item = item[0]
                if hasattr(item, 'file') and item.file:
                    files_data[key] = item.file.read()
                elif hasattr(item, 'value'):
                    val = item.value if isinstance(item.value, str) else item.value.decode()
                    fields_data[key] = val
        else:
            try:
                fields_data = json.loads(body.decode("utf-8"))
            except:
                pass

        action = fields_data.get("action", "list")

        if action == "list":
            # Listar todos los grafos en projects/
            items = []
            for fname in sorted(os.listdir(projects_dir)):
                fpath = os.path.join(projects_dir, fname)
                if fname.endswith(".json") and os.path.isfile(fpath):
                    try:
                        with open(fpath, "r") as f:
                            meta = json.load(f)
                        items.append(meta)
                    except:
                        pass
                elif fname.endswith(".mp") and os.path.isfile(fpath):
                    # Auto-detectar .mp sueltos como grafos
                    with open(fpath, "r", errors="replace") as f:
                        mp_content = f.read()
                    xfr_content = ""
                    xfr_path = fpath.replace(".mp", ".xfr")
                    if os.path.isfile(xfr_path):
                        with open(xfr_path, "r", errors="replace") as f:
                            xfr_content = f.read()
                    items.append({
                        "id": fname.replace(".mp", ""),
                        "name": fname.replace(".mp", ""),
                        "mp": mp_content,
                        "xfr": xfr_content,
                        "savedAt": str(os.path.getmtime(fpath)),
                        "nodes": mp_content.count("\nNODE ") + (1 if mp_content.startswith("NODE ") else 0),
                        "source": "file",
                    })
            items.sort(key=lambda x: x.get("savedAt", ""), reverse=True)
            self._json_response(200, {"graphs": items})

        elif action == "save":
            name = fields_data.get("name", "sin_nombre")
            mp_content = fields_data.get("mp", "")
            xfr_content = fields_data.get("xfr", "")

            # Si viene como file
            if "mp" in files_data:
                mp_content = files_data["mp"].decode("utf-8", errors="replace")
            if "xfr" in files_data:
                xfr_content = files_data["xfr"].decode("utf-8", errors="replace")

            if not mp_content:
                self._json_response(400, {"error": "mp content is required"})
                return

            # Guardar como .mp + .xfr + .json en projects/
            safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in name).strip().replace(" ", "_")
            if not safe_name:
                safe_name = "grafo_" + str(int(__import__("time").time()))

            mp_path = os.path.join(projects_dir, f"{safe_name}.mp")
            with open(mp_path, "w") as f:
                f.write(mp_content)

            if xfr_content:
                xfr_path = os.path.join(projects_dir, f"{safe_name}.xfr")
                with open(xfr_path, "w") as f:
                    f.write(xfr_content)

            # Metadata JSON
            entry = {
                "id": safe_name,
                "name": name,
                "mp": mp_content,
                "xfr": xfr_content,
                "savedAt": str(__import__("datetime").datetime.now().isoformat()),
                "nodes": mp_content.count("\nNODE ") + (1 if mp_content.startswith("NODE ") else 0),
                "source": "local",
            }
            meta_path = os.path.join(projects_dir, f"{safe_name}.json")
            with open(meta_path, "w") as f:
                json.dump(entry, f, indent=2)

            self._json_response(200, {"saved": entry})

        elif action == "delete":
            graph_id = fields_data.get("id", "")
            if not graph_id:
                self._json_response(400, {"error": "id is required"})
                return
            # Borrar .mp, .xfr, .json
            for ext in [".mp", ".xfr", ".json", ".dml"]:
                p = os.path.join(projects_dir, f"{graph_id}{ext}")
                if os.path.isfile(p):
                    os.unlink(p)
            self._json_response(200, {"deleted": graph_id})

        elif action == "upload":
            # Subir archivo(s) directamente a projects/
            saved = []
            for key, data in files_data.items():
                fname = fields_data.get(f"{key}_name", key)
                safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in fname)
                fpath = os.path.join(projects_dir, safe)
                with open(fpath, "wb") as f:
                    f.write(data)
                saved.append(safe)
            self._json_response(200, {"uploaded": saved})

        else:
            self._json_response(400, {"error": "action must be: list, save, delete, upload"})

    def _handle_pipeline(self):
        """Pipeline local — ejecuta el código generado localmente (sin AWS)."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        try:
            import subprocess
            code_content = ""
            target = "spark"

            if "multipart/form-data" in content_type:
                import cgi
                environ = {"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type, "CONTENT_LENGTH": str(len(body))}
                fp = BytesIO(body)
                form = cgi.FieldStorage(fp=fp, environ=environ, keep_blank_values=True)
                for key in form.keys():
                    item = form[key]
                    if isinstance(item, list):
                        item = item[0]
                    val = ""
                    if hasattr(item, 'file') and item.file:
                        val = item.file.read().decode("utf-8", errors="replace")
                    elif hasattr(item, 'value'):
                        val = item.value if isinstance(item.value, str) else item.value.decode()
                    if key == "code": code_content = val
                    elif key == "target": target = val

            if not code_content:
                self._json_response(400, {"error": "code is required"})
                return

            results = {"steps": [], "status": "running"}

            # Step 1: Guardar script en projects/output/
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects", "output")
            os.makedirs(output_dir, exist_ok=True)
            script_path = os.path.join(output_dir, f"{target}_job.py")
            with open(script_path, "w") as f:
                f.write(code_content)
            results["steps"].append({"step": "upload_s3", "status": "done", "detail": f"Guardado: {script_path}"})

            # Step 2: No necesita crear job — ejecucion local
            results["steps"].append({"step": "create_job", "status": "done", "detail": "Ejecucion local (sin Glue)"})

            # Step 3: Ejecutar con Python local
            try:
                proc = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True, text=True, timeout=120,
                    cwd=output_dir,
                )
                if proc.returncode == 0:
                    results["steps"].append({"step": "run_job", "status": "done", "detail": "Ejecutado OK"})
                    results["output"] = proc.stdout[-2000:] if proc.stdout else ""
                    results["status"] = "completed"
                else:
                    error_msg = (proc.stderr or proc.stdout or "Unknown error")[-500:]
                    results["steps"].append({"step": "run_job", "status": "error", "detail": error_msg})
                    results["status"] = "failed"
                    results["error"] = error_msg
            except subprocess.TimeoutExpired:
                results["steps"].append({"step": "run_job", "status": "error", "detail": "Timeout (120s)"})
                results["status"] = "failed"
            except FileNotFoundError:
                # PySpark no disponible, solo guardar
                results["steps"].append({"step": "run_job", "status": "info", "detail": f"Script guardado en {script_path}. Ejecutar manualmente: python3 {script_path}"})
                results["status"] = "saved"

            self._json_response(200, results)

        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_pipeline_status(self):
        """Status local — no hay polling, el resultado ya se devolvio en /pipeline."""
        self._json_response(200, {"status": "COMPLETED", "detail": "Ejecucion local es sincrona"})

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

    with socketserver.TCPServer(("", PORT), BNXHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Stopped")
