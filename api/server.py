# api/server.py
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

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

app = FastAPI(title="BNX Compiler API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _save_upload(upload: UploadFile) -> str:
    """Guarda un UploadFile en un temp file y retorna el path."""
    suffix = os.path.splitext(upload.filename)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(upload.file.read())
    tmp.close()
    return tmp.name


@app.post("/compile")
async def compile_graph(
    mp:  UploadFile = File(...),
    xfr: Optional[UploadFile] = File(None),
    dml: Optional[UploadFile] = File(None),
    target: str = "glue",
):
    """
    Compila el grafo y retorna:
    - nodes: lista de nodos con tipo y subgraph
    - edges: lista de edges
    - errors / warnings de validación
    - code: Glue job generado
    """
    mp_path  = _save_upload(mp)
    xfr_path = _save_upload(xfr) if xfr and xfr.filename else None
    dml_path = _save_upload(dml) if dml and dml.filename else None

    try:
        ast      = parse_mp_ast(mp_path)
        dag      = build_dag(ast)
        xfr_rules = parse_xfr(xfr_path) if xfr_path else {}
        dml_data  = parse_dml(dml_path) if dml_path else {}
        dml_schema = dml_data.get("schema", {})

        errors, warnings = validate(dag, xfr_rules, dml_schema)

        # Generar código según target
        code = None
        stepfunctions_json = None
        terraform_code = None
        airflow_code = None
        if not errors:
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

            # Step Functions
            sf_out = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
            sf_out.close()
            generate_stepfunctions(dag, sf_out.name, xfr_rules)
            with open(sf_out.name) as f:
                stepfunctions_json = f.read()
            os.unlink(sf_out.name)

            # Terraform
            tf_out = tempfile.NamedTemporaryFile(delete=False, suffix=".tf")
            tf_out.close()
            generate_terraform(dag, tf_out.name, xfr_rules)
            with open(tf_out.name) as f:
                terraform_code = f.read()
            os.unlink(tf_out.name)

            # Airflow
            af_out = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
            af_out.close()
            generate_airflow(dag, af_out.name, xfr_rules)
            with open(af_out.name) as f:
                airflow_code = f.read()
            os.unlink(af_out.name)

        # Construir respuesta del grafo
        nodes = []
        for node in dag.execution_order:
            node_rule = xfr_rules.get(node.id.lower()) or xfr_rules.get(node.name.lower()) or {}
            sg = next((sg for sg, ids in ast["subgraphs"].items() if node.id in ids), None)
            nodes.append({
                "id":       node.id,
                "name":     node.name,
                "type":     node.type.upper(),
                "subgraph": sg,
                "parents":  node.parents,
                "children": node.children,
                "rule":     node_rule,
            })

        edges = [
            {"from": e["from"], "to": e["to"]}
            for e in ast["edges"]
        ]

        # Accuracy
        acc = compute_accuracy(dag, xfr_rules, dml_schema)

        return {
            "nodes":    nodes,
            "edges":    edges,
            "subgraphs": list(ast["subgraphs"].keys()),
            "errors":   errors,
            "warnings": warnings,
            "code":     code,
            "stepfunctions": stepfunctions_json,
            "terraform": terraform_code,
            "airflow": airflow_code,
            "accuracy": acc,

    finally:
        for p in [mp_path, xfr_path, dml_path]:
            if p and os.path.exists(p):
                os.unlink(p)


@app.post("/cobol")
async def convert_cobol(
    cobol: UploadFile = File(...),
    target: str = "glue",
):
    """Converts a COBOL file to .mp + .xfr + .dml, then compiles."""
    cobol_path = _save_upload(cobol)

    try:
        parsed = parse_cobol(cobol_path)
        graph = cobol_to_graph(parsed)

        # Save generated files to temp
        mp_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp", mode="w")
        mp_tmp.write(graph["mp"])
        mp_tmp.close()

        xfr_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xfr", mode="w")
        xfr_tmp.write(graph["xfr"])
        xfr_tmp.close()

        dml_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".dml", mode="w")
        dml_tmp.write(graph["dml"])
        dml_tmp.close()

        ast = parse_mp_ast(mp_tmp.name)
        dag = build_dag(ast)
        xfr_rules = parse_xfr(xfr_tmp.name)
        dml_data = parse_dml(dml_tmp.name)
        dml_schema = dml_data.get("schema", {})

        errors, warnings = validate(dag, xfr_rules, dml_schema)

        code = None
        if not errors:
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
            "generated_mp": graph["mp"],
            "generated_xfr": graph["xfr"],
            "generated_dml": graph["dml"],
        }

    finally:
        for p in [cobol_path, mp_tmp.name, xfr_tmp.name, dml_tmp.name]:
            if p and os.path.exists(p):
                os.unlink(p)


@app.post("/refactor")
async def refactor(
    code: UploadFile = File(...),
    source_version: str = "all",
    target_version: str = "spark3",
):
    """Refactors legacy code: Spark 2→3, Python 2→3, Glue 2→4."""
    code_path = _save_upload(code)
    try:
        with open(code_path) as f:
            original = f.read()
        refactored, changes = refactor_code(original, source_version, target_version)
        return {
            "original_lines": len(original.splitlines()),
            "refactored_lines": len(refactored.splitlines()),
            "changes": changes,
            "total_changes": sum(c["count"] for c in changes),
            "code": refactored,
        }
    finally:
        if os.path.exists(code_path):
            os.unlink(code_path)


@app.post("/plan")
async def convert_plan(
    plan: UploadFile = File(...),
    pset: Optional[UploadFile] = File(None),
    xfr: Optional[UploadFile] = File(None),
    mp_files: list[UploadFile] = File(default=[]),
    target: str = "glue",
):
    """Converts Ab Initio PLAN + PSET to .mp + .xfr, then compiles.
    Supports multi-MP: upload .mp files referenced by the PLAN."""
    plan_path = _save_upload(plan)
    pset_path = _save_upload(pset) if pset and pset.filename else None
    user_xfr_path = _save_upload(xfr) if xfr and xfr.filename else None
    mp_path = xfr_path = None
    mp_temp_paths = {}

    try:
        parsed_plan = parse_plan(plan_path)
        parsed_pset = parse_pset(pset_path) if pset_path else {}

        # Save uploaded mp_files to temp
        for mf in mp_files:
            if mf and mf.filename:
                tp = _save_upload(mf)
                mp_temp_paths[mf.filename] = tp

        # --- Multi-MP path (Grafo de Grafos) ---
        if mp_temp_paths:
            retrocesos = detect_retrocesos(parsed_plan)
            resolved, resolve_errors, resolve_warnings = resolve_graph_references(
                parsed_plan, mp_temp_paths, parsed_pset
            )

            if resolve_errors:
                return {"errors": resolve_errors, "warnings": resolve_warnings,
                        "nodes": [], "edges": [], "code": None}

            dependencies = {g.name: g.depends for g in resolved}
            merged_ast = merge_asts(resolved, dependencies, retrocesos)
            dag = build_mega_dag(merged_ast)

            # Merge all XFR rules (namespaced)
            xfr_rules = {}
            dml_schema = {}
            for g in resolved:
                xfr_rules.update(g.xfr_rules)
                dml_schema.update(g.dml_schema)

            if user_xfr_path:
                user_rules = parse_xfr(user_xfr_path)
                xfr_rules.update(user_rules)

            errors, warnings = validate(dag, xfr_rules, dml_schema)
            warnings = resolve_warnings + warnings

            code = None
            stepfunctions_json = None
            terraform_code = None
            airflow_code = None
            if not errors:
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
                sg = next((sg for sg, ids in merged_ast["subgraphs"].items() if node.id in ids), None)
                nodes.append({
                    "id": node.id, "name": node.name, "type": node.type.upper(),
                    "subgraph": sg, "parents": node.parents, "children": node.children,
                    "rule": node_rule,
                })

            edges = [{"from": e["from"], "to": e["to"]} for e in merged_ast["edges"]]

            return {
                "nodes": nodes, "edges": edges,
                "subgraphs": list(merged_ast["subgraphs"].keys()),
                "errors": errors, "warnings": warnings,
                "code": code,
                "stepfunctions": stepfunctions_json,
                "terraform": terraform_code,
                "airflow": airflow_code,
                "accuracy": acc,
                "generated_mp": pretty_print_mega_dag(merged_ast),
                "generated_xfr": "",
                "plan_name": parsed_plan["name"],
                "pset_params": parsed_pset,
                "graphs": [{"name": g.name, "nodes": len(g.ast["nodes"]),
                            "is_auto_generated": g.is_auto_generated} for g in resolved],
                "cross_graph_edges": merged_ast.get("cross_graph_edges", []),
            }

        # --- Legacy single-PLAN path (backward compatible) ---
        graph = plan_to_graph(parsed_plan, parsed_pset)

        mp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp", mode="w")
        mp_path.write(graph["mp"])
        mp_path.close()
        mp_path = mp_path.name

        xfr_path = tempfile.NamedTemporaryFile(delete=False, suffix=".xfr", mode="w")
        xfr_path.write(graph["xfr"])
        xfr_path.close()
        xfr_path = xfr_path.name

        ast = parse_mp_ast(mp_path)
        dag = build_dag(ast)

        # Merge: PLAN-generated XFR + user XFR (user wins)
        xfr_rules = parse_xfr(xfr_path)
        if user_xfr_path:
            user_rules = parse_xfr(user_xfr_path)
            xfr_rules.update(user_rules)  # user rules override generated ones

        errors, warnings = validate(dag, xfr_rules)

        code = None
        if not errors:
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

        acc = compute_accuracy(dag, xfr_rules)

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
            "generated_mp": graph["mp"],
            "generated_xfr": graph["xfr"],
            "plan_name": parsed_plan["name"],
            "pset_params": graph.get("pset", {}),
        }

    finally:
        for p in [plan_path, pset_path, mp_path, xfr_path]:
            if p and isinstance(p, str) and os.path.exists(p):
                os.unlink(p)
        for p in mp_temp_paths.values():
            if p and os.path.exists(p):
                os.unlink(p)
