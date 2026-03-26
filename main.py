# main.py
import argparse
from src.mp_parser import parse_mp_ast
from src.dag.builder import build_dag
from src.xfr_parser import parse_xfr
from src.dml_parser import parse_dml
from src.codegen.glue_codegen import generate_glue
from src.validator.semantic import validate

def main(project_path, output_path, xfr_path=None, dml_path=None):
    print("🚀 BNX V54 START\n")

    ast = parse_mp_ast(project_path)
    dag = build_dag(ast)
    xfr_rules = parse_xfr(xfr_path) if xfr_path else {}
    dml = parse_dml(dml_path) if dml_path else {}
    dml_schema = dml.get("schema", {})

    if dml_schema:
        print(f"📋 DML schema loaded: {list(dml_schema.keys())}\n")

    # Validación semántica
    errors, warnings = validate(dag, xfr_rules, dml_schema)
    for w in warnings:
        print(w)
    if errors:
        print("\n🛑 VALIDATION FAILED:")
        for e in errors:
            print(e)
        print("\nFix the errors above before generating code.")
        return
    print("✅ Validation passed\n")

    print("📊 EXECUTION ORDER:")
    for i, node in enumerate(dag.execution_order, start=1):
        print(f"  {i}. {node.name} ({node.type})")

    generate_glue(dag, output_path, xfr_rules)

    print(f"\n✅ Generated: {output_path}")
    print("🏁 BNX V54 DONE\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--xfr", required=False, default=None)
    parser.add_argument("--dml", required=False, default=None)
    args = parser.parse_args()
    main(args.project, args.output, args.xfr, args.dml)