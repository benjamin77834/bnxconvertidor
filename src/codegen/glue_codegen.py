# src/codegen/glue_codegen.py
from datetime import datetime

def generate_glue(dag, output_path):
    with open(output_path, "w") as f:
        f.write(f'"""\n🚀 BNX V54 GENERATED GLUE JOB\n📅 Generated at: {datetime.now()}\n"""\n\n')
        f.write("from awsglue.context import GlueContext\n")
        f.write("from pyspark.context import SparkContext\n")
        f.write("from pyspark.sql.functions import *\n\n")
        f.write("sc = SparkContext()\nglueContext = GlueContext(sc)\nspark = glueContext.spark_session\n\n")
        f.write('print("🚀 BNX Glue Job V54 Started")\n\n')
        f.write("# =========================\n# DAG EXECUTION V54\n# =========================\n\n")

        for node in dag.execution_order:
            var_id = node.id  # ID seguro
            log_name = node.name  # Nombre original para logs

            if node.type == "XFR":
                f.write(f'# 🔹 XFR Node: {log_name}\n')
                f.write(f'{var_id}_df = spark.read.format("parquet").load("s3://bnx/raw/{var_id.lower()}")\n')
                f.write(f'print("📥 XFR: {log_name}")\n\n')
            else:
                f.write(f'# 🔹 DML Node: {log_name}\n')
                if node.parents:
                    parent_refs = [f'{p}_df' for p in node.parents]
                    if len(parent_refs) == 1:
                        f.write(f'{var_id}_df = {parent_refs[0]}  # placeholder transformation\n')
                    else:
                        f.write(f'{var_id}_df = {parent_refs[0]}\n')
                        for pr in parent_refs[1:]:
                            f.write(f'{var_id}_df = {var_id}_df.join({pr}, on="id", how="inner")  # placeholder join\n')
                else:
                    f.write(f'{var_id}_df = None  # no parents\n')
                f.write(f'print("🔄 DML: {log_name}")\n\n')

        f.write('print("✅ BNX Glue Job V54 Finished")\n')