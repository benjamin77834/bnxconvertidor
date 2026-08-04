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

        if "/pipeline/status" in path:
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

    def _handle_pipeline(self):
        """Ejecuta código en AWS Glue (sube a S3, crea/actualiza job, ejecuta)."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        try:
            import boto3
            code_content = ""
            bucket = "datalake-bnx-scripts-dev"
            region = "us-east-1"
            job_name = "datalake-bnx-test-spark-dev"
            role_arn = "arn:aws:iam::107094296911:role/datalake-glue-role-dev"
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
                    elif key == "bucket": bucket = val
                    elif key == "region": region = val
                    elif key == "job_name": job_name = val
                    elif key == "role": role_arn = val
                    elif key == "target": target = val

            if not code_content:
                self._json_response(400, {"error": "code is required"})
                return

            script_key = f"scripts/{target}_job.py"
            results = {"steps": [], "status": "running"}

            # Step 1: Upload to S3
            s3 = boto3.client("s3", region_name=region)
            try:
                s3.put_object(Bucket=bucket, Key=script_key, Body=code_content.encode("utf-8"))
                results["steps"].append({"step": "upload_s3", "status": "done", "detail": f"s3://{bucket}/{script_key}"})
            except Exception as e:
                results["steps"].append({"step": "upload_s3", "status": "error", "detail": str(e)})
                results["status"] = "failed"
                self._json_response(200, results)
                return

            # Step 2: Create or update Glue job
            glue = boto3.client("glue", region_name=region)
            try:
                try:
                    glue.create_job(
                        Name=job_name, Role=role_arn,
                        Command={"Name": "glueetl", "ScriptLocation": f"s3://{bucket}/{script_key}", "PythonVersion": "3"},
                        DefaultArguments={"--job-language": "python", "--TempDir": f"s3://{bucket}/temp/", "--enable-metrics": "true"},
                        GlueVersion="4.0", NumberOfWorkers=2, WorkerType="G.1X",
                    )
                    results["steps"].append({"step": "create_job", "status": "done", "detail": f"Created {job_name}"})
                except Exception as create_err:
                    if "AlreadyExists" in str(create_err) or "Idempotent" in str(create_err):
                        glue.update_job(
                            JobName=job_name,
                            JobUpdate={
                                "Role": role_arn,
                                "Command": {"Name": "glueetl", "ScriptLocation": f"s3://{bucket}/{script_key}", "PythonVersion": "3"},
                                "DefaultArguments": {"--job-language": "python", "--TempDir": f"s3://{bucket}/temp/", "--enable-metrics": "true"},
                                "GlueVersion": "4.0", "NumberOfWorkers": 2, "WorkerType": "G.1X",
                            }
                        )
                        results["steps"].append({"step": "create_job", "status": "done", "detail": f"Updated {job_name}"})
                    else:
                        raise create_err
            except Exception as e:
                results["steps"].append({"step": "create_job", "status": "error", "detail": str(e)})
                results["status"] = "failed"
                self._json_response(200, results)
                return

            # Step 3: Start job run
            try:
                run = glue.start_job_run(JobName=job_name)
                run_id = run["JobRunId"]
                results["steps"].append({"step": "run_job", "status": "done", "detail": f"RunId: {run_id}"})
                results["run_id"] = run_id
                results["job_name"] = job_name
                results["status"] = "started"
            except Exception as e:
                results["steps"].append({"step": "run_job", "status": "error", "detail": str(e)})
                results["status"] = "failed"

            self._json_response(200, results)

        except ImportError:
            self._json_response(200, {
                "steps": [{"step": "upload_s3", "status": "error", "detail": "boto3 not installed. Run: pip install boto3"}],
                "status": "failed"
            })
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_pipeline_status(self):
        """Consulta el estado de un Glue job run."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        try:
            import boto3
            job_name = "datalake-bnx-test-spark-dev"
            run_id = ""
            region = "us-east-1"

            if "multipart/form-data" in content_type:
                import cgi
                environ = {"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type, "CONTENT_LENGTH": str(len(body))}
                fp = BytesIO(body)
                form = cgi.FieldStorage(fp=fp, environ=environ, keep_blank_values=True)
                for key in form.keys():
                    item = form[key]
                    if isinstance(item, list):
                        item = item[0]
                    val = item.value if hasattr(item, 'value') else ""
                    if isinstance(val, bytes): val = val.decode()
                    if key == "job_name": job_name = val
                    elif key == "run_id": run_id = val
                    elif key == "region": region = val

            if not run_id:
                self._json_response(400, {"error": "run_id is required"})
                return

            glue = boto3.client("glue", region_name=region)
            run = glue.get_job_run(JobName=job_name, RunId=run_id)
            job_run = run["JobRun"]
            self._json_response(200, {
                "status": job_run["JobRunState"],
                "started": str(job_run.get("StartedOn", "")),
                "completed": str(job_run.get("CompletedOn", "")),
                "duration": job_run.get("ExecutionTime", 0),
                "error": job_run.get("ErrorMessage", ""),
            })

        except ImportError:
            self._json_response(200, {"status": "ERROR", "error": "boto3 not installed"})
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
