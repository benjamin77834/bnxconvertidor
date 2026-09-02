# lambda/handler.py
"""
AWS Lambda handler for BNX Compiler API.
Supports: /compile (mp/xfr/dml) and /cobol endpoints.
"""
import json
import os
import sys
import tempfile
import base64
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.mp_parser import parse_mp_ast
from src.dag.builder import build_dag, build_mega_dag
from src.xfr_parser import parse_xfr
from src.dml_parser import parse_dml
from src.validator.semantic import validate
from src.codegen.glue_codegen import generate_glue
from src.codegen.spark_codegen import generate_spark
from src.codegen.stepfunctions_codegen import generate_stepfunctions
from src.codegen.terraform_codegen import generate_terraform
from src.codegen.airflow_codegen import generate_airflow
from src.codegen.flink_codegen import generate_flink
from src.cobol_parser import parse_cobol, cobol_to_graph
from src.plan_parser import parse_plan, parse_pset, plan_to_graph
from src.plan_parser import resolve_graph_references, merge_asts, detect_retrocesos, pretty_print_mega_dag
from src.accuracy import compute_accuracy
from src.refactor_engine import refactor_code
from src.ocr_engine import extract_text_from_image, parse_extracted_text, text_to_mp
from main import parse_project


def _parse_multipart(event):
    import cgi
    # El header puede venir con distinto case segun el gateway.
    headers = event.get("headers", {}) or {}
    content_type = (headers.get("content-type") or headers.get("Content-Type") or "")
    body = event.get("body", "") or ""
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body)
    elif isinstance(body, str):
        body = body.encode()

    # Si el body NO es multipart (p.ej. JSON o vacio), parsear como JSON y exponer
    # sus claves como 'fields'. Evita que cgi.FieldStorage falle con
    # "write() argument must be str, not bytes" ante bodies no-multipart.
    if "multipart/form-data" not in content_type.lower():
        fields = {}
        if body:
            try:
                data = json.loads(body.decode("utf-8", errors="replace"))
                if isinstance(data, dict):
                    fields = {k: v for k, v in data.items()}
            except (ValueError, AttributeError):
                pass
        return {}, fields, set()

    environ = {
        "REQUEST_METHOD": "POST",
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(body)),
    }
    fp = BytesIO(body)
    form = cgi.FieldStorage(fp=fp, environ=environ, keep_blank_values=True)

    files = {}
    fields = {}
    mp_file_keys = set()  # Track keys that came from mp_files field
    for key in form.keys():
        item = form[key]
        # Handle multiple files with same key (e.g., mp_files)
        if isinstance(item, list):
            for i, sub in enumerate(item):
                if hasattr(sub, 'filename') and sub.filename:
                    fkey = sub.filename or f"{key}_{i}"
                    files[fkey] = sub.value
                    if key == "mp_files":
                        mp_file_keys.add(fkey)
                elif hasattr(sub, 'value'):
                    val = sub.value if isinstance(sub.value, str) else sub.value.decode()
                    fields[f"{key}_{i}"] = val
        elif hasattr(item, 'filename') and item.filename:
            # Store with form field key (e.g., "plan", "pset", "xfr")
            files[key] = item.value
            # Also store with original filename for mp_files matching
            if item.filename != key:
                files[item.filename] = item.value
            if key == "mp_files":
                mp_file_keys.add(item.filename)
        elif hasattr(item, 'value'):
            fields[key] = item.value if isinstance(item.value, str) else item.value.decode()
    return files, fields, mp_file_keys


def _save_bytes(data, suffix):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(data if isinstance(data, bytes) else data.encode())
    tmp.close()
    return tmp.name


def _generate_code(dag, xfr_rules, target):
    out = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    out.close()
    if target == "spark":
        generate_spark(dag, out.name, xfr_rules)
    elif target == "flink":
        generate_flink(dag, out.name, xfr_rules)
    else:
        generate_glue(dag, out.name, xfr_rules)
    with open(out.name) as f:
        code = f.read()
    os.unlink(out.name)
    return code


def _build_response(dag, ast, xfr_rules, dml_schema, target):
    errors, warnings = validate(dag, xfr_rules, dml_schema)

    code = None
    stepfunctions_json = None
    terraform_code = None
    airflow_code = None
    if not errors:
        code = _generate_code(dag, xfr_rules, target)

        sf_out = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        sf_out.close()
        generate_stepfunctions(dag, sf_out.name, xfr_rules)
        with open(sf_out.name) as f:
            stepfunctions_json = f.read()
        os.unlink(sf_out.name)

        tf_out = tempfile.NamedTemporaryFile(delete=False, suffix=".tf")
        tf_out.close()
        generate_terraform(dag, tf_out.name, xfr_rules)
        with open(tf_out.name) as f:
            terraform_code = f.read()
        os.unlink(tf_out.name)

        af_out = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
        af_out.close()
        generate_airflow(dag, af_out.name, xfr_rules)
        with open(af_out.name) as f:
            airflow_code = f.read()
        os.unlink(af_out.name)

    acc = compute_accuracy(dag, xfr_rules, dml_schema)

    nodes = []
    for node in dag.execution_order:
        node_rule = xfr_rules.get(node.id.lower()) or xfr_rules.get(node.name.lower()) or {}
        sg = next((sg for sg, ids in ast["subgraphs"].items() if node.id in ids), None)
        nodes.append({
            "id": node.id, "name": node.name, "type": node.type.upper(),
            "subgraph": sg, "parents": node.parents, "children": node.children,
            "rule": node_rule,
        })

    edges = [{"from": e["from"], "to": e["to"]} for e in ast["edges"]]

    return {
        "nodes": nodes, "edges": edges,
        "subgraphs": list(ast["subgraphs"].keys()),
        "errors": errors, "warnings": warnings,
        "code": code,
        "stepfunctions": stepfunctions_json,
        "terraform": terraform_code,
        "airflow": airflow_code,
        "accuracy": acc,
    }


def handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {"statusCode": 200, "headers": _cors_headers(), "body": ""}

    path = event.get("rawPath", "") or event.get("path", "")
    try:
        files, fields, mp_file_keys = _parse_multipart(event)
        target = fields.get("target", "glue")

        # --- /download endpoint (admin) ---
        if "/download" in path:
            import zipfile
            import io
            import glob

            pack = fields.get("pack", "backend")  # backend | frontend | all
            src_dir = os.path.dirname(os.path.dirname(__file__))

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                if pack in ("backend", "all"):
                    # Backend files
                    backend_files = [
                        "main.py",
                        "src/mp_parser.py", "src/xfr_parser.py", "src/dml_parser.py",
                        "src/cobol_parser.py", "src/plan_parser.py", "src/accuracy.py",
                        "src/refactor_engine.py", "src/dag/builder.py",
                        "src/validator/semantic.py",
                        "src/codegen/glue_codegen.py", "src/codegen/spark_codegen.py",
                        "src/codegen/flink_codegen.py", "src/codegen/stepfunctions_codegen.py",
                        "src/codegen/terraform_codegen.py", "src/codegen/airflow_codegen.py",
                        "api/server.py", "lambda/handler.py",
                    ]
                    for f in backend_files:
                        fp = os.path.join(src_dir, f)
                        if os.path.exists(fp):
                            zf.write(fp, f"bnx-backend/{f}")

                    # Sample files
                    for pattern in ["graphs/test_mega/*", "samples/refactor/*", "e2e/*", "cobol/*"]:
                        for fp in glob.glob(os.path.join(src_dir, pattern)):
                            rel = os.path.relpath(fp, src_dir)
                            if os.path.isfile(fp):
                                zf.write(fp, f"bnx-backend/{rel}")

                    # README
                    readme_path = os.path.join(src_dir, "README.md")
                    if os.path.exists(readme_path):
                        zf.write(readme_path, "bnx-backend/README.md")

                    # Requirements
                    zf.writestr("bnx-backend/requirements.txt", "fastapi\nuvicorn\npython-multipart\n")
                    zf.writestr("bnx-backend/run.sh", "#!/bin/bash\npython3 main.py --project graphs/test_mega/ingest.mp --target glue --output output.py\necho 'Done! Check output.py'\n")
                    # Init files
                    zf.writestr("bnx-backend/src/__init__.py", "")
                    zf.writestr("bnx-backend/src/dag/__init__.py", "")
                    zf.writestr("bnx-backend/src/validator/__init__.py", "")
                    zf.writestr("bnx-backend/src/codegen/__init__.py", "")

                if pack in ("frontend", "all"):
                    # Frontend ? just the src files (not node_modules)
                    ui_dir = os.path.join(src_dir, "ui")
                    fe_files = [
                        "package.json", "vite.config.js", "index.html",
                        "src/App.jsx", "src/config.js", "src/index.css", "src/main.jsx",
                    ]
                    # Components
                    comp_dir = os.path.join(ui_dir, "src", "components")
                    if os.path.isdir(comp_dir):
                        for cf in os.listdir(comp_dir):
                            if cf.endswith(".jsx") or cf.endswith(".js"):
                                fe_files.append(f"src/components/{cf}")

                    for f in fe_files:
                        fp = os.path.join(ui_dir, f)
                        if os.path.exists(fp):
                            zf.write(fp, f"bnx-frontend/{f}")

                    zf.writestr("bnx-frontend/install.sh", "#!/bin/bash\nnpm install\nnpm run dev\necho 'Open http://localhost:3000'\n")

            zip_bytes = zip_buffer.getvalue()
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/zip",
                    "Content-Disposition": f"attachment; filename=bnx-{pack}.zip",
                },
                "body": base64.b64encode(zip_bytes).decode(),
                "isBase64Encoded": True,
            }

        # --- /ocr endpoint ---
        if "/ocr" in path:
            if "image" in files:
                # OCR from image
                image_bytes = files["image"]
                text = extract_text_from_image(image_bytes)
                if text and not text.startswith("ERROR"):
                    parsed = parse_extracted_text(text)
                    mp_content = text_to_mp(parsed)
                    return _response(200, {
                        "extracted_text": text,
                        "parsed": parsed,
                        "generated_mp": mp_content,
                    })
                else:
                    return _response(200, {"error": text or "OCR failed ? boto3 not available", "tip": "Paste text directly instead"})
            elif "text" in fields:
                # Direct text paste (no OCR needed)
                text = fields["text"]
                parsed = parse_extracted_text(text)
                mp_content = text_to_mp(parsed)
                return _response(200, {
                    "extracted_text": text,
                    "parsed": parsed,
                    "generated_mp": mp_content,
                })
            else:
                return _response(400, {"error": "image or text field required"})

        # --- /refactor endpoint ---
        if "/refactor" in path:
            if "code" not in files:
                return _response(400, {"error": "code file is required"})
            code_path = _save_bytes(files["code"], ".py")
            try:
                with open(code_path) as f:
                    original = f.read()
                source_version = fields.get("source_version", "all")
                refactored, changes = refactor_code(original, source_version)
                return _response(200, {
                    "original_lines": len(original.splitlines()),
                    "refactored_lines": len(refactored.splitlines()),
                    "changes": changes,
                    "total_changes": sum(c["count"] for c in changes),
                    "code": refactored,
                })
            finally:
                if os.path.exists(code_path):
                    os.unlink(code_path)

        # --- /plan endpoint ---
        if "/plan" in path:
            if "plan" not in files:
                return _response(400, {"error": "plan file is required"})

            plan_path = _save_bytes(files["plan"], ".plan")
            pset_path = _save_bytes(files["pset"], ".pset") if "pset" in files else None
            user_xfr_path = _save_bytes(files["xfr"], ".xfr") if "xfr" in files else None
            mp_path = xfr_path = None
            mp_temp_paths = {}

            # Collect mp_files: from mp_file_keys, mp_file_N fields, or .mp filenames
            for key in mp_file_keys:
                if key in files:
                    tp = _save_bytes(files[key], ".mp")
                    mp_temp_paths[key] = tp
            # Also check for mp_file_0, mp_file_1, etc. (individual field names from UI)
            for key, data in files.items():
                if key.startswith("mp_file_") or (key.endswith(".mp") and key not in ("plan", "pset", "xfr")):
                    if key not in mp_temp_paths:
                        tp = _save_bytes(data, ".mp")
                        # Use original filename if available
                        mp_temp_paths[key] = tp

            try:
                parsed_plan = parse_plan(plan_path)
                parsed_pset = parse_pset(pset_path) if pset_path else {}

                # --- Multi-MP path ---
                if mp_temp_paths:
                    retrocesos = detect_retrocesos(parsed_plan)
                    resolved, resolve_errors, resolve_warnings = resolve_graph_references(
                        parsed_plan, mp_temp_paths, parsed_pset
                    )
                    if resolve_errors:
                        return _response(200, {"errors": resolve_errors, "warnings": resolve_warnings,
                                               "nodes": [], "edges": [], "code": None})

                    dependencies = {g.name: g.depends for g in resolved}
                    merged_ast = merge_asts(resolved, dependencies, retrocesos)
                    dag = build_mega_dag(merged_ast)

                    xfr_rules = {}
                    dml_schema = {}
                    for g in resolved:
                        xfr_rules.update(g.xfr_rules)
                        dml_schema.update(g.dml_schema)
                    if user_xfr_path:
                        user_rules = parse_xfr(user_xfr_path)
                        xfr_rules.update(user_rules)

                    result = _build_response(dag, merged_ast, xfr_rules, dml_schema, target)
                    result["generated_mp"] = pretty_print_mega_dag(merged_ast)
                    result["generated_xfr"] = ""
                    result["plan_name"] = parsed_plan.get("name", "")
                    result["graphs"] = [{"name": g.name, "nodes": len(g.ast["nodes"]),
                                         "is_auto_generated": g.is_auto_generated} for g in resolved]
                    result["cross_graph_edges"] = merged_ast.get("cross_graph_edges", [])
                    result["warnings"] = resolve_warnings + (result.get("warnings") or [])
                    return _response(200, result)

                # --- Legacy single-PLAN path ---
                graph = plan_to_graph(parsed_plan, parsed_pset)

                mp_path = _save_bytes(graph["mp"], ".mp")
                xfr_path = _save_bytes(graph["xfr"], ".xfr")

                ast = parse_mp_ast(mp_path)
                dag = build_dag(ast)
                xfr_rules = parse_xfr(xfr_path)
                if user_xfr_path:
                    user_rules = parse_xfr(user_xfr_path)
                    xfr_rules.update(user_rules)

                result = _build_response(dag, ast, xfr_rules, {}, target)
                result["generated_mp"] = graph["mp"]
                result["generated_xfr"] = graph["xfr"]
                result["plan_name"] = parsed_plan.get("name", "")
                return _response(200, result)
            finally:
                for p in [plan_path, pset_path, user_xfr_path, mp_path, xfr_path]:
                    if p and os.path.exists(p):
                        os.unlink(p)
                for p in mp_temp_paths.values():
                    if p and os.path.exists(p):
                        os.unlink(p)

        # --- /cobol endpoint ---
        if "/cobol" in path:
            if "cobol" not in files:
                return _response(400, {"error": "cobol file is required"})

            cobol_path = _save_bytes(files["cobol"], ".cbl")
            mp_path = xfr_path = dml_path = None
            try:
                parsed = parse_cobol(cobol_path)
                graph = cobol_to_graph(parsed)

                mp_path = _save_bytes(graph["mp"], ".mp")
                xfr_path = _save_bytes(graph["xfr"], ".xfr")
                dml_path = _save_bytes(graph["dml"], ".dml")

                ast = parse_mp_ast(mp_path)
                dag = build_dag(ast)
                xfr_rules = parse_xfr(xfr_path)
                dml_data = parse_dml(dml_path)
                dml_schema = dml_data.get("schema", {})

                result = _build_response(dag, ast, xfr_rules, dml_schema, target)
                result["generated_mp"] = graph["mp"]
                result["generated_xfr"] = graph["xfr"]
                result["generated_dml"] = graph["dml"]
                return _response(200, result)
            finally:
                for p in [cobol_path, mp_path, xfr_path, dml_path]:
                    if p and os.path.exists(p):
                        os.unlink(p)

        # --- /library endpoint (proyectos + grafos como carpetas en S3) ---
        if "/library" in path:
            import boto3

            lib_bucket = "datalake-bnx-scripts-dev"
            lib_prefix = "library/"
            lib_region = "us-east-1"
            action = fields.get("action", "list_projects")

            s3 = boto3.client("s3", region_name=lib_region)

            if action == "list_projects":
                # Listar proyectos (carpetas de primer nivel en library/)
                try:
                    resp = s3.list_objects_v2(Bucket=lib_bucket, Prefix=lib_prefix, Delimiter="/")
                    projects = []
                    for prefix in resp.get("CommonPrefixes", []):
                        proj_name = prefix["Prefix"].replace(lib_prefix, "").rstrip("/")
                        if proj_name:
                            # Contar archivos dentro
                            files_resp = s3.list_objects_v2(Bucket=lib_bucket, Prefix=f"{lib_prefix}{proj_name}/")
                            file_count = len([o for o in files_resp.get("Contents", []) if o["Key"].endswith(".mp")])
                            projects.append({"name": proj_name, "graphs": file_count})
                    return _response(200, {"projects": projects})
                except Exception as e:
                    err = str(e)
                    # Distinguir un problema de permisos (SCP/IAM) de "no hay proyectos".
                    if "AccessDenied" in err or "not authorized" in err or "explicit deny" in err:
                        return _response(200, {
                            "projects": [],
                            "error": err,
                            "error_kind": "access_denied",
                            "hint": ("La Lambda no tiene permiso para listar el bucket S3 "
                                     "(posible explicit deny en una Service Control Policy). "
                                     "Contacta al administrador de la organizacion AWS."),
                        })
                    return _response(200, {"projects": [], "error": err})

            elif action == "create_project":
                # Crear proyecto (carpeta en S3)
                project = fields.get("project", "").strip()
                if not project:
                    return _response(400, {"error": "project name is required"})
                safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in project).strip("_")
                s3.put_object(Bucket=lib_bucket, Key=f"{lib_prefix}{safe}/", Body=b"")
                return _response(200, {"created": safe})

            elif action == "list_files":
                # Listar archivos dentro de un proyecto
                project = fields.get("project", "")
                if not project:
                    return _response(400, {"error": "project is required"})
                try:
                    resp = s3.list_objects_v2(Bucket=lib_bucket, Prefix=f"{lib_prefix}{project}/")
                    files_list = []
                    for obj in resp.get("Contents", []):
                        fname = obj["Key"].replace(f"{lib_prefix}{project}/", "")
                        if fname and not fname.endswith("/"):
                            files_list.append({
                                "name": fname,
                                "size": obj["Size"],
                                "lastModified": str(obj["LastModified"]),
                            })
                    return _response(200, {"project": project, "files": files_list})
                except Exception as e:
                    return _response(200, {"files": [], "error": str(e)})

            elif action == "upload":
                # Subir archivo(s) a un proyecto
                project = fields.get("project", "")
                if not project:
                    return _response(400, {"error": "project is required"})
                uploaded = []
                for key, data in files.items():
                    if key in ("project", "action"):
                        continue
                    # Usar el nombre del campo o filename
                    fname = key
                    if isinstance(data, bytes):
                        s3.put_object(
                            Bucket=lib_bucket,
                            Key=f"{lib_prefix}{project}/{fname}",
                            Body=data,
                            ContentType="text/plain",
                        )
                        uploaded.append(fname)
                # Tambien revisar campos de texto con contenido mp/xfr
                mp_content = fields.get("mp", "")
                xfr_content = fields.get("xfr", "")
                name = fields.get("name", "grafo")
                if mp_content:
                    s3.put_object(Bucket=lib_bucket, Key=f"{lib_prefix}{project}/{name}.mp", Body=mp_content.encode(), ContentType="text/plain")
                    uploaded.append(f"{name}.mp")
                if xfr_content:
                    s3.put_object(Bucket=lib_bucket, Key=f"{lib_prefix}{project}/{name}.xfr", Body=xfr_content.encode(), ContentType="text/plain")
                    uploaded.append(f"{name}.xfr")
                return _response(200, {"uploaded": uploaded, "project": project})

            elif action == "download":
                # Descargar contenido de un archivo
                project = fields.get("project", "")
                file_name = fields.get("file", "")
                if not project or not file_name:
                    return _response(400, {"error": "project and file are required"})
                try:
                    obj = s3.get_object(Bucket=lib_bucket, Key=f"{lib_prefix}{project}/{file_name}")
                    content = obj["Body"].read().decode("utf-8", errors="replace")
                    return _response(200, {"file": file_name, "project": project, "content": content})
                except Exception as e:
                    return _response(200, {"error": str(e)})

            elif action == "delete":
                # Borrar archivo o proyecto
                project = fields.get("project", "")
                file_name = fields.get("file", "")
                if not project:
                    return _response(400, {"error": "project is required"})
                try:
                    if file_name:
                        s3.delete_object(Bucket=lib_bucket, Key=f"{lib_prefix}{project}/{file_name}")
                        return _response(200, {"deleted": f"{project}/{file_name}"})
                    else:
                        # Borrar proyecto completo (todos los archivos)
                        resp = s3.list_objects_v2(Bucket=lib_bucket, Prefix=f"{lib_prefix}{project}/")
                        for obj in resp.get("Contents", []):
                            s3.delete_object(Bucket=lib_bucket, Key=obj["Key"])
                        return _response(200, {"deleted_project": project})
                except Exception as e:
                    return _response(200, {"error": str(e)})

            return _response(400, {"error": "action: list_projects, create_project, list_files, upload, download, delete"})

        # --- /pipeline endpoint (ejecutar código en Glue desde UI) ---
        if "/pipeline" in path and "/pipeline/status" not in path:
            import boto3

            action = fields.get("action", "run")
            code_content = fields.get("code", "")
            if "code" in files:
                code_content = files["code"].decode() if isinstance(files["code"], bytes) else files["code"]

            if not code_content:
                return _response(400, {"error": "code is required (field or file)"})

            pipeline_bucket = fields.get("bucket", "bnx-e2e-test")
            pipeline_region = fields.get("region", "us-east-1")
            pipeline_job = fields.get("job_name", "bnx-e2e-pipeline-ui")
            pipeline_role = fields.get("role", "arn:aws:iam::034711235858:role/lambdarol")
            script_target = fields.get("target", "spark")
            script_key = f"scripts/{script_target}_job.py"

            s3 = boto3.client("s3", region_name=pipeline_region)
            glue = boto3.client("glue", region_name=pipeline_region)

            results = {"steps": [], "status": "running"}

            # Step 0: Replace generic S3 paths with pipeline bucket
            import re as _re
            # Replace s3://bnx/ with s3://pipeline_bucket/ (generic paths from codegen)
            code_content = _re.sub(r's3://bnx/', f's3://{pipeline_bucket}/', code_content)
            
            # Ensure pipeline bucket exists
            try:
                s3.head_bucket(Bucket=pipeline_bucket)
            except Exception:
                try:
                    s3.create_bucket(Bucket=pipeline_bucket)
                    results["steps"].append({"step": "create_bucket", "status": "done", "detail": f"Created s3://{pipeline_bucket}"})
                except Exception as e:
                    results["steps"].append({"step": "create_bucket", "status": "error", "detail": str(e)[:150]})

            # Step 1: Upload script to S3
            try:
                s3.put_object(
                    Bucket=pipeline_bucket,
                    Key=script_key,
                    Body=code_content.encode("utf-8")
                )
                results["steps"].append({"step": "upload_s3", "status": "done",
                    "detail": f"s3://{pipeline_bucket}/{script_key}"})
            except Exception as e:
                results["steps"].append({"step": "upload_s3", "status": "error", "detail": str(e)})
                results["status"] = "failed"
                return _response(200, results)

            # Step 2: Create or update Glue job
            try:
                try:
                    glue.create_job(
                        Name=pipeline_job,
                        Role=pipeline_role,
                        Command={
                            "Name": "glueetl",
                            "ScriptLocation": f"s3://{pipeline_bucket}/{script_key}",
                            "PythonVersion": "3"
                        },
                        DefaultArguments={
                            "--job-language": "python",
                            "--TempDir": f"s3://{pipeline_bucket}/temp/",
                            "--enable-metrics": "true",
                        },
                        GlueVersion="4.0",
                        NumberOfWorkers=2,
                        WorkerType="G.1X",
                    )
                    results["steps"].append({"step": "create_job", "status": "done", "detail": f"Created {pipeline_job}"})
                except Exception as create_err:
                    if "AlreadyExists" in str(create_err) or "Idempotent" in str(create_err):
                        glue.update_job(
                            JobName=pipeline_job,
                            JobUpdate={
                                "Role": pipeline_role,
                                "Command": {
                                    "Name": "glueetl",
                                    "ScriptLocation": f"s3://{pipeline_bucket}/{script_key}",
                                    "PythonVersion": "3"
                                },
                                "DefaultArguments": {
                                    "--job-language": "python",
                                    "--TempDir": f"s3://{pipeline_bucket}/temp/",
                                    "--enable-metrics": "true",
                                },
                                "GlueVersion": "4.0",
                                "NumberOfWorkers": 2,
                                "WorkerType": "G.1X",
                            }
                        )
                        results["steps"].append({"step": "create_job", "status": "done", "detail": f"Updated {pipeline_job}"})
                    else:
                        raise create_err
            except Exception as e:
                results["steps"].append({"step": "create_job", "status": "error", "detail": str(e)})
                results["status"] = "failed"
                return _response(200, results)

            # Step 3: Start job run
            try:
                run = glue.start_job_run(JobName=pipeline_job)
                run_id = run["JobRunId"]
                results["steps"].append({"step": "run_job", "status": "done", "detail": f"RunId: {run_id}"})
                results["run_id"] = run_id
                results["job_name"] = pipeline_job
                results["status"] = "started"
            except Exception as e:
                results["steps"].append({"step": "run_job", "status": "error", "detail": str(e)})
                results["status"] = "failed"

            return _response(200, results)

        # --- /pipeline/status endpoint (check job status) ---
        if "/pipeline/status" in path:
            import boto3

            pipeline_job = fields.get("job_name", "bnx-e2e-pipeline-ui")
            run_id = fields.get("run_id", "")
            pipeline_region = fields.get("region", "us-east-1")

            if not run_id:
                return _response(400, {"error": "run_id is required"})

            glue = boto3.client("glue", region_name=pipeline_region)
            try:
                run = glue.get_job_run(JobName=pipeline_job, RunId=run_id)
                job_run = run["JobRun"]
                return _response(200, {
                    "status": job_run["JobRunState"],
                    "started": str(job_run.get("StartedOn", "")),
                    "completed": str(job_run.get("CompletedOn", "")),
                    "duration": job_run.get("ExecutionTime", 0),
                    "error": job_run.get("ErrorMessage", ""),
                })
            except Exception as e:
                return _response(200, {"status": "UNKNOWN", "error": str(e)})

        # --- /pipeline/logs endpoint (read CloudWatch logs) ---
        if "/pipeline/logs" in path:
            import boto3

            run_id = fields.get("run_id", "")
            pipeline_region = fields.get("region", "us-east-1")

            if not run_id:
                return _response(400, {"error": "run_id is required"})

            logs_client = boto3.client("logs", region_name=pipeline_region)
            all_logs = []
            for log_group in ["/aws-glue/jobs/output", "/aws-glue/jobs/error"]:
                try:
                    resp = logs_client.get_log_events(
                        logGroupName=log_group,
                        logStreamName=run_id,
                        limit=100,
                    )
                    for event in resp.get("events", []):
                        msg = event.get("message", "").strip()
                        if msg:
                            all_logs.append(msg)
                except Exception:
                    pass

            return _response(200, {"logs": all_logs})

        # --- /compile endpoint ---
        if "mp" not in files:
            return _response(400, {"error": "mp file is required"})

        mp_path = _save_bytes(files["mp"], ".mp")
        xfr_path = _save_bytes(files["xfr"], ".xfr") if "xfr" in files else None
        dml_path = _save_bytes(files["dml"], ".dml") if "dml" in files else None

        try:
            ast = parse_project(mp_path)
            dag = build_dag(ast)
            xfr_rules = parse_xfr(xfr_path) if xfr_path else {}
            dml_data = parse_dml(dml_path) if dml_path else {}
            dml_schema = dml_data.get("schema", {})

            return _response(200, _build_response(dag, ast, xfr_rules, dml_schema, target))
        finally:
            for p in [mp_path, xfr_path, dml_path]:
                if p and os.path.exists(p):
                    os.unlink(p)

    except Exception as e:
        return _response(500, {"error": str(e)})


def _cors_headers():
    # CORS lo maneja la configuracion de la Lambda Function URL de AWS.
    # NO agregar Access-Control-* aqui: si el codigo Y la Function URL agregan
    # Access-Control-Allow-Origin, el navegador recibe el valor duplicado '*, *'
    # (invalido) y bloquea la peticion por CORS. Dejamos solo el Content-Type.
    return {
        "Content-Type": "application/json",
    }


def _response(status, body):
    return {
        "statusCode": status,
        "headers": _cors_headers(),
        "body": json.dumps(body, default=str),
    }
