# main.py
import argparse
from src.mp_parser import parse_mp_ast
from src.dag.builder import build_dag
from src.codegen.glue_codegen import generate_glue

def main(project_path, output_path):
    print("🚀 BNX V54 START\n")
    
    ast = parse_mp_ast(project_path)
    dag = build_dag(ast)
    
    print("\n📊 EXECUTION ORDER:")
    for i, node in enumerate(dag.execution_order, start=1):
        print(f"{i}. {node.name} ({node.type})")
    
    generate_glue(dag, output_path)
    
    print(f"\n✅ Glue job generado en: {output_path}\n")
    print("✅ BNX V54 FINISHED\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    main(args.project, args.output)