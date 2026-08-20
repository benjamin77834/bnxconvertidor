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

        if "/library" in path or "/pipeline" in path:
            self._proxy_to_datalab(path)
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
                    print(f"  [pset] Loaded {len(pset_params)} parameters from .pset")
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

            self._json_response(200, {
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
                "params": {k: v for k, v in list(ast.get("abinitio_params", {}).items())[:20]},
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
