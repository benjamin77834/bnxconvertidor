from src.transforms.registry import TRANSFORMS


def generate_glue(ir, output_path):

    print("⚙️ CODEGEN START")

    code = []

    code.append("from pyspark.sql import SparkSession")
    code.append("from pyspark.sql.functions import *")
    code.append("")
    code.append("spark = SparkSession.builder.appName('BNX_V8').getOrCreate()")
    code.append("")

    # -------------------------
    # INPUT NODES
    # -------------------------
    for node in ir.nodes.values():

        if node.type == "input":
            code.append(
                f"{node.id} = spark.read.parquet('{node.id}.parquet')"
            )

    code.append("")

    resolved = {}

    # -------------------------
    # BUILD EXECUTION (DAG ORDER SIMPLE)
    # -------------------------
    ordered_nodes = list(ir.nodes.values())

    for node in ordered_nodes:

        # resolve inputs
        inputs = [resolved[i] for i in node.inputs if i in resolved]

        # get transform function
        fn = TRANSFORMS.get(node.type)

        # -------------------------
        # IF TRANSFORM EXISTS
        # -------------------------
        if fn:

            try:
                resolved[node.id] = fn(node, inputs)
            except Exception as e:
                resolved[node.id] = f"None  # ERROR: {str(e)}"

        # -------------------------
        # FALLBACK
        # -------------------------
        else:

            if node.type == "input":
                resolved[node.id] = node.id

            elif len(node.inputs) == 1:
                resolved[node.id] = f"{node.inputs[0]}  # passthrough"

            else:
                resolved[node.id] = "None  # unsupported transform"

    # -------------------------
    # EMIT CODE
    # -------------------------
    for k, v in resolved.items():
        code.append(f"{k} = {v}")

    code.append("\n# BNX V8 PIPELINE COMPLETE")

    with open(output_path, "w") as f:
        f.write("\n".join(code))

    return "\n".join(code)