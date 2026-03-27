# src/codegen/glue_codegen.py
import re
from datetime import datetime

def _build_transform(var_id, src_df, rule):
    """Genera código PySpark a partir de una regla XFR { select, where, group_by }"""
    select = rule.get("select", "*")
    where = rule.get("where")
    group_by = rule.get("group_by")

    if group_by:
        # Genera groupBy().agg() para agregaciones
        keys = ", ".join(f'"{k}"' for k in group_by)
        # Convierte "SUM(amount) as total_spent" → sum("amount").alias("total_spent")
        agg_exprs = []
        for col in select.split(","):
            col = col.strip()
            m = re.match(r"(\w+)\((\w+)\)\s+as\s+(\w+)", col, re.I)
            if m:
                fn, field, alias = m.group(1).lower(), m.group(2), m.group(3)
                agg_exprs.append(f'{fn}("{field}").alias("{alias}")')
            else:
                agg_exprs.append(f'col("{col}")')
        agg_str = ", ".join(agg_exprs)
        code = f'{var_id}_df = {src_df}.groupBy({keys}).agg({agg_str})'
        if where:
            code += f'.where("{where}")'
        return code

    # Transform simple
    cols = [f'"{c.strip()}"' for c in select.split(",")]
    code = f'{var_id}_df = {src_df}.selectExpr({", ".join(cols)})'
    if where:
        code += f'.where("{where}")'
    return code

def generate_glue(dag, output_path, xfr_rules=None):
    xfr_rules = xfr_rules or {}

    with open(output_path, "w") as f:
        f.write(f'"""\n🚀 BNX V54 GENERATED GLUE JOB\n📅 Generated at: {datetime.now()}\n"""\n\n')
        f.write("from awsglue.context import GlueContext\n")
        f.write("from pyspark.context import SparkContext\n")
        f.write("from pyspark.sql.functions import *\n\n")
        f.write("sc = SparkContext()\nglueContext = GlueContext(sc)\nspark = glueContext.spark_session\n\n")
        f.write('print("🚀 BNX Glue Job V54 Started")\n\n')
        f.write("# =========================\n# DAG EXECUTION V54\n# =========================\n\n")

        for node in dag.execution_order:
            var_id = node.id
            log_name = node.name
            ntype = node.type.upper()
            parents = node.parents
            rule = xfr_rules.get(var_id.lower()) or xfr_rules.get(log_name.lower())

            # SOURCE
            if ntype == "SOURCE":
                f.write(f'# 🟢 SOURCE: {log_name}\n')
                f.write(f'{var_id}_df = spark.read.format("parquet").load("s3://bnx/raw/{var_id.lower()}")\n')
                f.write(f'print("📂 SOURCE: {log_name}")\n\n')

            # TRANSFORM / XFR
            elif ntype in ("TRANSFORM", "XFR"):
                f.write(f'# 🔹 TRANSFORM: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    if rule:
                        f.write(_build_transform(var_id, src, rule) + "\n")
                    else:
                        f.write(f'{var_id}_df = {src}.selectExpr("*")  # no XFR rule found\n')
                else:
                    f.write(f'{var_id}_df = None  # no parent\n')
                f.write(f'print("🔄 TRANSFORM: {log_name}")\n\n')

            # JOIN
            elif ntype == "JOIN":
                f.write(f'# 🔗 JOIN: {log_name}\n')
                if len(parents) >= 2:
                    join_key = rule.get("join_key", "id") if rule else "id"
                    join_type = rule.get("join_type", "inner") if rule else "inner"
                    # primer join
                    f.write(f'{var_id}_df = {parents[0]}_df.join({parents[1]}_df, on="{join_key}", how="{join_type}")\n')
                    # joins encadenados para padres adicionales
                    for extra_parent in parents[2:]:
                        f.write(f'{var_id}_df = {var_id}_df.join({extra_parent}_df, on="{join_key}", how="{join_type}")\n')
                elif len(parents) == 1:
                    f.write(f'{var_id}_df = {parents[0]}_df\n')
                else:
                    f.write(f'{var_id}_df = None  # no parents\n')
                f.write(f'print("🔗 JOIN: {log_name}")\n\n')

            # DEDUP — deduplicación por key
            elif ntype == "DEDUP":
                f.write(f'# 🧹 DEDUP: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    dedup_keys = rule.get("dedup_keys", ["id"]) if rule else ["id"]
                    order_by = rule.get("order_by") if rule else None
                    keys_str = ", ".join(f'"{k}"' for k in dedup_keys)
                    if order_by:
                        # Mantener el registro más reciente
                        f.write(f'from pyspark.sql.window import Window\n')
                        f.write(f'_w_{var_id} = Window.partitionBy({keys_str}).orderBy(col("{order_by}").desc())\n')
                        f.write(f'{var_id}_df = {src}.withColumn("_rn", row_number().over(_w_{var_id})).where("_rn = 1").drop("_rn")\n')
                    else:
                        f.write(f'{var_id}_df = {src}.dropDuplicates([{keys_str}])\n')
                else:
                    f.write(f'{var_id}_df = None  # no parent\n')
                f.write(f'print("🧹 DEDUP: {log_name}")\n\n')

            # NORMALIZE — un registro → múltiples registros (explode)
            elif ntype == "NORMALIZE":
                f.write(f'# 📐 NORMALIZE: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    explode_col = rule.get("explode_col") if rule else None
                    if explode_col:
                        f.write(f'{var_id}_df = {src}.withColumn("{explode_col}", explode(col("{explode_col}")))\n')
                    else:
                        # Normalize con split: "col|delimiter"
                        split_col = rule.get("split_col") if rule else None
                        delimiter = rule.get("delimiter", ",") if rule else ","
                        if split_col:
                            f.write(f'{var_id}_df = {src}.withColumn("{split_col}", explode(split(col("{split_col}"), "{delimiter}")))\n')
                        else:
                            f.write(f'{var_id}_df = {src}  # no explode/split config\n')
                else:
                    f.write(f'{var_id}_df = None  # no parent\n')
                f.write(f'print("📐 NORMALIZE: {log_name}")\n\n')

            # LOOKUP — referencia a dataset externo (broadcast join)
            elif ntype == "LOOKUP":
                f.write(f'# 🔍 LOOKUP: {log_name}\n')
                if len(parents) >= 2:
                    main_df = f'{parents[0]}_df'
                    lookup_df = f'{parents[1]}_df'
                    lookup_key = rule.get("lookup_key", "id") if rule else "id"
                    lookup_select = rule.get("lookup_select") if rule else None
                    f.write(f'from pyspark.sql.functions import broadcast\n')
                    if lookup_select:
                        cols = ", ".join(f'"{c.strip()}"' for c in lookup_select.split(","))
                        f.write(f'_lookup_{var_id} = broadcast({lookup_df}.select("{lookup_key}", {cols}))\n')
                    else:
                        f.write(f'_lookup_{var_id} = broadcast({lookup_df})\n')
                    f.write(f'{var_id}_df = {main_df}.join(_lookup_{var_id}, on="{lookup_key}", how="left")\n')
                elif len(parents) == 1:
                    f.write(f'{var_id}_df = {parents[0]}_df\n')
                else:
                    f.write(f'{var_id}_df = None  # no parents\n')
                f.write(f'print("🔍 LOOKUP: {log_name}")\n\n')

            # SINK
            elif ntype == "SINK":
                f.write(f'# 🏁 SINK: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    f.write(f'{src}.write.mode("overwrite").format("parquet").save("s3://bnx/output/{var_id.lower()}")\n')
                else:
                    f.write(f'# ⚠️ SINK {log_name} has no parent\n')
                f.write(f'print("💾 SINK: {log_name}")\n\n')

            # DML genérico
            else:
                f.write(f'# 🔹 DML ({ntype}): {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    if rule:
                        f.write(_build_transform(var_id, src, rule) + "\n")
                    else:
                        f.write(f'{var_id}_df = {src}  # no rule for {ntype}\n')
                else:
                    f.write(f'{var_id}_df = None  # no parents\n')
                f.write(f'print("🔄 DML: {log_name}")\n\n')

        f.write('print("✅ BNX Glue Job V54 Finished")\n')