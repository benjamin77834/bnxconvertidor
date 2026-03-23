from src.parser.mp_ast_parser import parse_mp_ast
from src.dag.builder import build_dag
from src.dag.validator import validate_dag
from src.lineage.tracker import build_lineage
from src.codegen.glue_codegen import generate_glue


def main(mp_path, output_path):

    print("\n🚀 BNX v2 ENTERPRISE COMPILER STARTED\n")

    ast = parse_mp_ast(mp_path)

    dag = build_dag(ast)

    validate_dag(dag)

    build_lineage(dag)

    generate_glue(dag, output_path)

    print("\n✔ DONE")


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--project")
    parser.add_argument("--output")

    args = parser.parse_args()

    main(args.project + "/test.mp", args.output)