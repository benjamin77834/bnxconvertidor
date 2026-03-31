# src/codegen/spark_codegen.py
"""
Generates pure PySpark code (no Glue dependencies).
Same logic as glue_codegen but with SparkSession instead of GlueContext.
"""
import re
from datetime import datetime


def _build_transform(var_id, src_df, rule):
    select = rule.get("select", "*")
    where = rule.get("where")
    group_by = rule.get("group_by")

    if group_by:
        keys = ", ".join(f'"{k}"' for k in group_by)
        agg_exprs = []
        for col in select.split(","):
            col = col.strip()
            m = re.match(r"(\w+)\((\w+)\)\s+as\s+(\w+)", col, re.I)
            if m:
                fn, field, alias = m.group(1).lower(), m.group(2), m.group(3)
                agg_exprs.append(f'{fn}("{field}").alias("{alias}")')
            else:
                agg_exprs.append(f'col("{col}")')
        code = f'{var_id}_df = {src_df}.groupBy({keys}).agg({", ".join(agg_exprs)})'
        if where:
            code += f'.where("{where}")'
        return code

    cols = [f'"{c.strip()}"' for c in select.split(",")]
    code = f'{var_id}_df = {src_df}.selectExpr({", ".join(cols)})'
    if where:
        code += f'.where("{where}")'
    return code


def generate_spark(dag, output_path, xfr_rules=None):
    xfr_rules = xfr_rules or {}

    with open(output_path, "w") as f:
        f.write(f'"""\n🚀 BNX V54 GENERATED PYSPARK JOB\n📅 Generated at: {datetime.now()}\n"""\n\n')
        f.write("from pyspark.sql import SparkSession\n")
        f.write("from pyspark.sql.functions import *\n")
        f.write("from pyspark.sql.window import Window\n\n")
        f.write('spark = SparkSession.builder.appName("BNX_Pipeline").getOrCreate()\n\n')
        f.write('print("🚀 BNX PySpark Job Started")\n\n')

        for node in dag.execution_order:
            var_id = node.id
            log_name = node.name
            ntype = node.type.upper()
            parents = node.parents
            rule = xfr_rules.get(var_id.lower()) or xfr_rules.get(log_name.lower())

            if ntype == "SOURCE":
                f.write(f'# 🟢 SOURCE: {log_name}\n')
                src_type = rule.get("source_type", "s3") if rule else "s3"
                path = rule.get("path", f"s3a://bnx/raw/{var_id.lower()}") if rule else f"s3a://bnx/raw/{var_id.lower()}"
                fmt = rule.get("format", "parquet") if rule else "parquet"
                topic = rule.get("topic") if rule else None
                table = rule.get("table") if rule else None
                conn = rule.get("connection") if rule else None

                if src_type == "kafka" and topic:
                    f.write(f'{var_id}_df = spark.readStream.format("kafka")')
                    f.write(f'.option("kafka.bootstrap.servers", "{conn or "localhost:9092"}")')
                    f.write(f'.option("subscribe", "{topic}").load()\n')
                    f.write(f'{var_id}_df = {var_id}_df.selectExpr("CAST(value AS STRING) as json_value")\n')
                elif src_type == "jdbc" and (table or conn):
                    f.write(f'{var_id}_df = spark.read.format("jdbc")')
                    f.write(f'.option("url", "{conn or "jdbc:mysql://localhost:3306/db"}")')
                    f.write(f'.option("dbtable", "{table or var_id.lower()}").load()\n')
                else:
                    f.write(f'{var_id}_df = spark.read.parquet("{path}")\n')
                f.write(f'print("📂 SOURCE: {log_name}")\n\n')

            elif ntype in ("TRANSFORM", "XFR"):
                f.write(f'# 🔹 TRANSFORM: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    if rule:
                        f.write(_build_transform(var_id, src, rule) + "\n")
                    else:
                        f.write(f'{var_id}_df = {src}.selectExpr("*")\n')
                else:
                    f.write(f'{var_id}_df = None\n')
                f.write(f'print("🔄 TRANSFORM: {log_name}")\n\n')

            elif ntype == "JOIN":
                f.write(f'# 🔗 JOIN: {log_name}\n')
                if len(parents) >= 2:
                    jk = rule.get("join_key", "id") if rule else "id"
                    jt = rule.get("join_type", "inner") if rule else "inner"
                    f.write(f'{var_id}_df = {parents[0]}_df.join({parents[1]}_df, on="{jk}", how="{jt}")\n')
                    for ep in parents[2:]:
                        f.write(f'{var_id}_df = {var_id}_df.join({ep}_df, on="{jk}", how="{jt}")\n')
                elif len(parents) == 1:
                    f.write(f'{var_id}_df = {parents[0]}_df\n')
                else:
                    f.write(f'{var_id}_df = None\n')
                f.write(f'print("🔗 JOIN: {log_name}")\n\n')

            elif ntype == "DEDUP":
                f.write(f'# 🧹 DEDUP: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    dk = rule.get("dedup_keys", ["id"]) if rule else ["id"]
                    ob = rule.get("order_by") if rule else None
                    ks = ", ".join(f'"{k}"' for k in dk)
                    if ob:
                        f.write(f'_w_{var_id} = Window.partitionBy({ks}).orderBy(col("{ob}").desc())\n')
                        f.write(f'{var_id}_df = {src}.withColumn("_rn", row_number().over(_w_{var_id})).where("_rn = 1").drop("_rn")\n')
                    else:
                        f.write(f'{var_id}_df = {src}.dropDuplicates([{ks}])\n')
                else:
                    f.write(f'{var_id}_df = None\n')
                f.write(f'print("🧹 DEDUP: {log_name}")\n\n')

            elif ntype == "NORMALIZE":
                f.write(f'# 📐 NORMALIZE: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    ec = rule.get("explode_col") if rule else None
                    sc = rule.get("split_col") if rule else None
                    dl = rule.get("delimiter", ",") if rule else ","
                    if ec:
                        f.write(f'{var_id}_df = {src}.withColumn("{ec}", explode(col("{ec}")))\n')
                    elif sc:
                        f.write(f'{var_id}_df = {src}.withColumn("{sc}", explode(split(col("{sc}"), "{dl}")))\n')
                    else:
                        f.write(f'{var_id}_df = {src}\n')
                else:
                    f.write(f'{var_id}_df = None\n')
                f.write(f'print("📐 NORMALIZE: {log_name}")\n\n')

            elif ntype == "LOOKUP":
                f.write(f'# 🔍 LOOKUP: {log_name}\n')
                if len(parents) >= 2:
                    lk = rule.get("lookup_key", "id") if rule else "id"
                    ls = rule.get("lookup_select") if rule else None
                    if ls:
                        cols = ", ".join(f'"{c.strip()}"' for c in ls.split(","))
                        f.write(f'_lkp_{var_id} = broadcast({parents[1]}_df.select("{lk}", {cols}))\n')
                    else:
                        f.write(f'_lkp_{var_id} = broadcast({parents[1]}_df)\n')
                    f.write(f'{var_id}_df = {parents[0]}_df.join(_lkp_{var_id}, on="{lk}", how="left")\n')
                else:
                    f.write(f'{var_id}_df = None\n')
                f.write(f'print("🔍 LOOKUP: {log_name}")\n\n')

            elif ntype == "SINK":
                f.write(f'# 🏁 SINK: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    sink_type = rule.get("sink_type", "s3") if rule else "s3"
                    path = rule.get("path", f"s3a://bnx/output/{var_id.lower()}") if rule else f"s3a://bnx/output/{var_id.lower()}"
                    fmt = rule.get("format", "parquet") if rule else "parquet"
                    topic = rule.get("topic") if rule else None
                    table = rule.get("table") if rule else None
                    conn = rule.get("connection") if rule else None
                    mode = rule.get("mode", "overwrite") if rule else "overwrite"

                    if sink_type == "kafka" and topic:
                        f.write(f'{src}.selectExpr("to_json(struct(*)) AS value").write.format("kafka")')
                        f.write(f'.option("kafka.bootstrap.servers", "{conn or "localhost:9092"}")')
                        f.write(f'.option("topic", "{topic}").save()\n')
                    elif sink_type == "jdbc" and (table or conn):
                        f.write(f'{src}.write.format("jdbc").mode("{mode}")')
                        f.write(f'.option("url", "{conn or "jdbc:mysql://localhost:3306/db"}")')
                        f.write(f'.option("dbtable", "{table or var_id.lower()}").save()\n')
                    else:
                        f.write(f'{src}.write.mode("{mode}").parquet("{path}")\n')
                f.write(f'print("💾 SINK: {log_name}")\n\n')

            else:
                f.write(f'# 🔹 {ntype}: {log_name}\n')
                if parents:
                    if rule:
                        f.write(_build_transform(var_id, f'{parents[0]}_df', rule) + "\n")
                    else:
                        f.write(f'{var_id}_df = {parents[0]}_df\n')
                else:
                    f.write(f'{var_id}_df = None\n')
                f.write(f'print("🔄 {ntype}: {log_name}")\n\n')

        f.write('spark.stop()\n')
        f.write('print("✅ BNX PySpark Job Finished")\n')
