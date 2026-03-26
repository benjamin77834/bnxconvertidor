from collections import defaultdict

def generate(order, edges, nodes, content, output_path):

    print("[CODEGEN] BNX V28.6 FIXED ENGINE")

    _ = content  # safe ignore

    node_type = {n["id"]: n["type"] for n in nodes}

    parents = defaultdict(list)
    for s, d in edges:
        parents[d].append(s)

    def safe(n):
        return n.replace(".", "_")

    def resolve(n):
        if n not in parents or len(parents[n]) == 0:
            return None
        return parents[n][0]

    lines = []

    lines.append("from pyspark.sql import SparkSession")
    lines.append("from pyspark.sql.functions import *")
    lines.append("")
    lines.append("spark = SparkSession.builder.appName('BNX_V28_6').getOrCreate()")
    lines.append("print('=== BNX V28.6 START ===')")
    lines.append("")
    lines.append("ctx = {}")
    lines.append("")

    lines.append("customers_df = spark.createDataFrame([(1,'A'),(2,'B')], ['id','name'])")
    lines.append("transactions_df = spark.createDataFrame([(1,100),(2,200)], ['id','amount'])")
    lines.append("accounts_df = spark.createDataFrame([(1,'ACC1'),(2,'ACC2')], ['id','account'])")
    lines.append("")

    for n in order:

        t = node_type.get(n, "UNKNOWN")
        s = safe(n)
        p = resolve(n)

        if t == "INPUT":
            if "Customers" in n:
                expr = "customers_df"
            elif "Transactions" in n:
                expr = "transactions_df"
            else:
                expr = "accounts_df"

            lines.append(f"ctx['{s}'] = {expr}")

        elif t == "JOIN":
            ps = parents.get(n, [])
            if len(ps) >= 2:
                a, b = safe(ps[0]), safe(ps[1])
                expr = f"ctx['{a}'].join(ctx['{b}'], 'id')"
            else:
                expr = "None"

            lines.append(f"ctx['{s}'] = {expr}")

        elif t == "TRANSFORM":
            expr = f"ctx['{safe(p)}']" if p else "None"
            lines.append(f"ctx['{s}'] = {expr}")

        elif t == "OUTPUT":
            expr = f"ctx['{safe(p)}']" if p else "None"
            lines.append(f"ctx['{s}'] = {expr}")
            lines.append(f"if ctx['{s}'] is not None: ctx['{s}'].show()")

        else:
            expr = f"ctx['{safe(p)}']" if p else "None"
            lines.append(f"ctx['{s}'] = {expr}")

    lines.append("print('=== BNX COMPLETE ===')")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))