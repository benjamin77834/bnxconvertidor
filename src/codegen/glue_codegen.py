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