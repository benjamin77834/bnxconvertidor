def build_lineage(nodes, edges):
    print("🧬 LINEAGE TRACE")

    for src, dst in edges:
        print(f"🔗 {dst} <- [{src}]")