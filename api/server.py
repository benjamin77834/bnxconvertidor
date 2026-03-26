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
from src.dag.builder import build_dag
from src.xfr_parser import parse_xfr
from src.dml_parser import parse_dml
from src.validator.semantic import validate
from src.codegen.glue_codegen import generate_glue

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
    xfr: UploadFile = File(None),
    dml: UploadFile = File(None),
):
    """
    Compila el grafo y retorna:
    - nodes: lista de nodos con tipo y subgraph
    - edges: lista de edges
    - errors / warnings de validación
    - code: Glue job generado
    """
    mp_path  = _save_upload(mp)
    xfr_path = _save_upload(xfr) if xfr else None
    dml_path = _save_upload(dml) if dml else None

    try:
        ast      = parse_mp_ast(mp_path)
        dag      = build_dag(ast)
        xfr_rules = parse_xfr(xfr_path) if xfr_path else {}
        dml_data  = parse_dml(dml_path) if dml_path else {}
        dml_schema = dml_data.get("schema", {})

        errors, warnings = validate(dag, xfr_rules, dml_schema)

        # Generar código aunque haya warnings (solo bloquear en errores)
        code = None
        if not errors:
            out = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
            out.close()
            generate_glue(dag, out.name, xfr_rules)
            with open(out.name) as f:
                code = f.read()
            os.unlink(out.name)

        # Construir respuesta del grafo
        nodes = []
        for node in dag.execution_order:
            nodes.append({
                "id":       node.id,
                "name":     node.name,
                "type":     node.type.upper(),
                "subgraph": ast["subgraphs"].get(
                    next((sg for sg, ids in ast["subgraphs"].items() if node.id in ids), None),
                    None
                ),
                "parents":  node.parents,
                "children": node.children,
            })

        edges = [
            {"from": e["from"], "to": e["to"]}
            for e in ast["edges"]
        ]

        return {
            "nodes":    nodes,
            "edges":    edges,
            "subgraphs": list(ast["subgraphs"].keys()),
            "errors":   errors,
            "warnings": warnings,
            "code":     code,
        }

    finally:
        for p in [mp_path, xfr_path, dml_path]:
            if p and os.path.exists(p):
                os.unlink(p)
