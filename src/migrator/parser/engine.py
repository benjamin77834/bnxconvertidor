# src/migrator/compiler/engine.py

from src.migrator.parser.sql_parser import parse_sql
from src.core.ir import build_ir
from src.core.optimizer import optimize
from src.core.dag import build_dag
from src.core.lineage import build_lineage
from src.core.spark_compiler import generate_spark


def compile_sql(sql, output):
    print("? Parsing SQL...")
    ast = parse_sql(sql)

    print("? Building IR...")
    ir = build_ir(ast)

    print("?? Optimizing...")
    ir = optimize(ir)

    print("[>] Building DAG...")
    dag = build_dag(ir)

    print("? Building lineage...")
    build_lineage(dag)

    print("[>] Generating Spark...")
    code = generate_spark(dag)

    with open(output, "w") as f:
        f.write(code)

    print(f"[ok] Generated: {output}")


def compile_graph(sql=None, mp=None, xfr=None, dml=None, output="glue_job.py"):
    if sql:
        return compile_sql(sql, output)

    print("[*] GRAPH MODE (MP/XFR/DML)")

    ast = {
        "mp": mp,
        "xfr": xfr,
        "dml": dml
    }

    ir = build_ir(ast)
    ir = optimize(ir)
    dag = build_dag(ir)
    build_lineage(dag)
    code = generate_spark(dag)

    with open(output, "w") as f:
        f.write(code)

    print(f"[ok] Generated: {output}")
