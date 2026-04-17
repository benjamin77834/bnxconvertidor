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


def _parse_multipart(event):
    import cgi
    content_type = event.get("headers", {}).get("content-type", "")
    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body)
    elif isinstance(body, str):
        body = body.encode()

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

        # --- /compile endpoint ---
        if "mp" not in files:
            return _response(400, {"error": "mp file is required"})

        mp_path = _save_bytes(files["mp"], ".mp")
        xfr_path = _save_bytes(files["xfr"], ".xfr") if "xfr" in files else None
        dml_path = _save_bytes(files["dml"], ".dml") if "dml" in files else None

        try:
            ast = parse_mp_ast(mp_path)
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
    return {"Content-Type": "application/json"}


def _response(status, body):
    return {
        "statusCode": status,
        "headers": _cors_headers(),
        "body": json.dumps(body, default=str),
    }
