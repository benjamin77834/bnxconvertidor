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
from src.dag.builder import build_dag
from src.xfr_parser import parse_xfr
from src.dml_parser import parse_dml
from src.validator.semantic import validate
from src.codegen.glue_codegen import generate_glue
from src.codegen.spark_codegen import generate_spark
from src.cobol_parser import parse_cobol, cobol_to_graph
from src.accuracy import compute_accuracy


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
    for key in form.keys():
        item = form[key]
        if item.filename:
            files[key] = item.value
        else:
            fields[key] = item.value if isinstance(item.value, str) else item.value.decode()
    return files, fields


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
    else:
        generate_glue(dag, out.name, xfr_rules)
    with open(out.name) as f:
        code = f.read()
    os.unlink(out.name)
    return code


def _build_response(dag, ast, xfr_rules, dml_schema, target):
    errors, warnings = validate(dag, xfr_rules, dml_schema)

    code = None
    if not errors:
        code = _generate_code(dag, xfr_rules, target)

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
        "code": code, "accuracy": acc,
    }


def handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {"statusCode": 200, "headers": _cors_headers(), "body": ""}

    path = event.get("rawPath", "") or event.get("path", "")
    try:
        files, fields = _parse_multipart(event)
        target = fields.get("target", "glue")

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
