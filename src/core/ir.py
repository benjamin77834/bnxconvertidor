def build_ir(ast):
    return {
        "nodes": ast.get("tables", []),
        "joins": ast.get("joins", []),
        "raw": ast
    }