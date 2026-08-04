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
            fields_data, files_data = parse_multipart(body, content_type)
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
        """Pipeline — sube a S3 y ejecuta en Glue via AWS CLI (profile datalab)."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        try:
            import subprocess
            code_content = ""
            target = "spark"
            bucket = "datalake-bnx-scripts-dev"
            job_name = "datalake-bnx-test-spark-dev"
            region = "us-east-1"
            profile = "datalab"

            if "multipart/form-data" in content_type:
                fields, file_parts = parse_multipart(body, content_type)
                target = fields.get("target", "spark")
                bucket = fields.get("bucket", bucket)
                job_name = fields.get("job_name", job_name)
                profile = fields.get("profile", profile)
                if "code" in file_parts:
                    code_content = file_parts["code"].decode("utf-8", errors="replace")
                elif "code" in fields:
                    code_content = fields["code"]

            if not code_content:
                self._json_response(400, {"error": "code is required"})
                return

            results = {"steps": [], "status": "running"}

            # Step 1: Guardar script localmente
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects", "output")
            os.makedirs(output_dir, exist_ok=True)
            script_path = os.path.join(output_dir, f"{target}_job.py")
            with open(script_path, "w") as f:
                f.write(code_content)
            results["steps"].append({"step": "upload_s3", "status": "running", "detail": "Subiendo a S3..."})

            # Step 2: Subir a S3 con AWS CLI
            s3_key = f"scripts/{target}_job.py"
            s3_uri = f"s3://{bucket}/{s3_key}"
            proc = subprocess.run(
                ["aws", "s3", "cp", script_path, s3_uri, "--profile", profile, "--region", region],
                capture_output=True, text=True, timeout=30
            )
            if proc.returncode == 0:
                results["steps"][-1] = {"step": "upload_s3", "status": "done", "detail": s3_uri}
            else:
                results["steps"][-1] = {"step": "upload_s3", "status": "error", "detail": proc.stderr[:200]}
                results["status"] = "failed"
                self._json_response(200, results)
                return

            # Step 3: Ejecutar Glue job
            results["steps"].append({"step": "create_job", "status": "done", "detail": f"Job: {job_name}"})
            proc = subprocess.run(
                ["aws", "glue", "start-job-run", "--job-name", job_name, "--profile", profile, "--region", region, "--query", "JobRunId", "--output", "text"],
                capture_output=True, text=True, timeout=30
            )
            if proc.returncode == 0:
                run_id = proc.stdout.strip()
                results["steps"].append({"step": "run_job", "status": "done", "detail": f"RunId: {run_id}"})
                results["run_id"] = run_id
                results["job_name"] = job_name
                results["status"] = "started"
            else:
                results["steps"].append({"step": "run_job", "status": "error", "detail": proc.stderr[:200]})
                results["status"] = "failed"

            self._json_response(200, results)

        except FileNotFoundError:
            self._json_response(200, {
                "steps": [{"step": "upload_s3", "status": "error", "detail": "AWS CLI no encontrado. Instalar: https://aws.amazon.com/cli/"}],
                "status": "failed"
            })
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_pipeline_status(self):
        """Consulta status del Glue job via AWS CLI."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        import subprocess
        job_name = "datalake-bnx-test-spark-dev"
        run_id = ""
        region = "us-east-1"
        profile = "datalab"

        if "multipart/form-data" in content_type:
            fields, _ = parse_multipart(body, content_type)
            job_name = fields.get("job_name", job_name)
            run_id = fields.get("run_id", "")
            region = fields.get("region", region)
            profile = fields.get("profile", profile)

        if not run_id:
            self._json_response(400, {"error": "run_id is required"})
            return

        try:
            proc = subprocess.run(
                ["aws", "glue", "get-job-run", "--job-name", job_name, "--run-id", run_id,
                 "--profile", profile, "--region", region, "--output", "json"],
                capture_output=True, text=True, timeout=15
            )
            if proc.returncode == 0:
                data = json.loads(proc.stdout)
                jr = data.get("JobRun", {})
                self._json_response(200, {
                    "status": jr.get("JobRunState", "UNKNOWN"),
                    "duration": jr.get("ExecutionTime", 0),
                    "error": jr.get("ErrorMessage", ""),
                })
            else:
                self._json_response(200, {"status": "UNKNOWN", "error": proc.stderr[:200]})
        except Exception as e:
            self._json_response(200, {"status": "UNKNOWN", "error": str(e)})

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
