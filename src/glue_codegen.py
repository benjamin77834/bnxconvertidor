def generate_glue(order, nodes, edges, output_path):

    print("[CODEGEN V40 FIX] generating glue job...")

    lines = []

    lines.append("from pyspark.sql import SparkSession")
    lines.append("from pyspark.sql.functions import *\n")

    lines.append("spark = SparkSession.builder.appName('BNX_V40').getOrCreate()")
    lines.append("ctx = {}\n")

    lines.append("print('=== BNX V40 START ===')\n")

    parent_map = {}
    for src, dst in edges:
        parent_map.setdefault(dst, []).append(src)

    for node in order:

        node_def = nodes[node]
        ntype = node_def.get("type", "MAP")
        parents = parent_map.get(node, [])

        if ntype == "SOURCE":
            lines.append(f"ctx['{node}'] = spark.read.parquet('s3://input/{node}')\n")

        elif ntype == "MAP":
            p = parents[0] if parents else None
            lines.append(f"ctx['{node}'] = ctx['{p}'].select('*')\n")

        elif ntype == "FILTER":
            p = parents[0] if parents else None
            lines.append(f"ctx['{node}'] = ctx['{p}'].filter('id IS NOT NULL')\n")

        elif ntype == "AGG":
            p = parents[0] if parents else None
            lines.append(f"ctx['{node}'] = ctx['{p}'].groupBy('id').count()\n")

        elif ntype == "SINK":
            p = parents[0] if parents else None
            lines.append(f"ctx['{node}'] = ctx['{p}']\n")
            lines.append(f"ctx['{node}'].write.mode('overwrite').parquet('s3://output/{node}')\n")

        else:
            p = parents[0] if parents else None
            lines.append(f"ctx['{node}'] = ctx['{p}']\n")

    lines.append("\nprint('=== BNX V40 COMPLETE ===')\n")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    print(f"[CODEGEN V40 FIX] WRITTEN ? {output_path}")