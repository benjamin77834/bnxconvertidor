import argparse
from src.parser.mp_parser import parse_mp
from src.dag.builder import build_dag
from src.lineage.tracker import build_lineage
from src.optimizer import optimize
from src.codegen.spark_codegen import generate_glue


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    print("🚀 BNX V9 ULTIMATE STARTED")

    # -------------------------
    # PARSER
    # -------------------------
    print("🔥 PARSER STARTED")

    ir = parse_mp(args.project)

    nodes = ir.nodes
    edges = ir.edges

    print(f"🧬 IR NODES: {len(nodes)}")
    print(f"🔗 EDGES: {len(edges)}")

    # -------------------------
    # DAG
    # -------------------------
    dag = build_dag(nodes, edges)

    if not dag.is_valid():
        print("❌ INVALID DAG")
        return

    print("✔ IR VALID")

    # -------------------------
    # LINEAGE
    # -------------------------
    print("🧬 LINEAGE TRACE")
    build_lineage(nodes, edges)

    # -------------------------
    # OPTIMIZER
    # -------------------------
    print("⚡ OPTIMIZER START")
    optimize(nodes, edges)

    # -------------------------
    # CODEGEN
    # -------------------------
    print("⚙️ CODEGEN START (BNX V9)")
    generate_glue(nodes, edges, args.output)

    print("🔥 DONE:", args.output)


if __name__ == "__main__":
    main()