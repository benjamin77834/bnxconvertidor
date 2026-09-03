# src/codegen/airflow_codegen.py
"""
Generates Apache Airflow DAG Python file from BNX DAG.
Creates tasks per node with proper dependencies.
"""
from datetime import datetime


def generate_airflow(dag, output_path, xfr_rules=None):
    xfr_rules = xfr_rules or {}

    # Group by depth for parallel execution
    depth_map = {}
    def get_depth(nid, visited=None):
        if visited is None: visited = set()
        if nid in visited: return 0
        visited.add(nid)
        node = dag.nodes.get(nid)
        if not node or not node.parents: return 0
        return 1 + max(get_depth(p, set(visited)) for p in node.parents if p in dag.nodes)

    for node in dag.execution_order:
        d = get_depth(node.id)
        if d not in depth_map: depth_map[d] = []
        depth_map[d].append(node)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f'"""\n')
        f.write(f'[*] BNX Generated Airflow DAG\n')
        f.write(f'? Generated at: {datetime.now()}\n')
        f.write(f'[>] Nodes: {len(dag.execution_order)}\n')
        f.write(f'"""\n\n')

        f.write('from datetime import datetime, timedelta\n')
        f.write('from airflow import DAG\n')
        f.write('from airflow.providers.amazon.aws.operators.glue import GlueJobOperator\n')
        f.write('from airflow.providers.amazon.aws.sensors.glue import GlueJobSensor\n')
        f.write('from airflow.operators.python import PythonOperator\n')
        f.write('from airflow.operators.dummy import DummyOperator\n')
        f.write('from airflow.utils.task_group import TaskGroup\n\n')

        f.write('default_args = {\n')
        f.write('    "owner": "bnx-pipeline",\n')
        f.write('    "depends_on_past": False,\n')
        f.write('    "email_on_failure": True,\n')
        f.write('    "email_on_retry": False,\n')
        f.write('    "retries": 2,\n')
        f.write('    "retry_delay": timedelta(minutes=5),\n')
        f.write('}\n\n')

        f.write('with DAG(\n')
        f.write('    dag_id="bnx_pipeline",\n')
        f.write(f'    description="BNX Generated Pipeline - {len(dag.execution_order)} nodes",\n')
        f.write('    default_args=default_args,\n')
        f.write('    schedule_interval="0 1 * * *",  # Daily at 1am\n')
        f.write('    start_date=datetime(2026, 1, 1),\n')
        f.write('    catchup=False,\n')
        f.write('    tags=["bnx", "generated", "etl"],\n')
        f.write(') as dag:\n\n')

        f.write('    start = DummyOperator(task_id="start")\n')
        f.write('    end = DummyOperator(task_id="end")\n\n')

        # Create tasks
        for node in dag.execution_order:
            ntype = node.type.upper()
            rule = xfr_rules.get(node.id.lower()) or xfr_rules.get(node.name.lower()) or {}
            safe_id = node.id.lower().replace('-', '_')

            if ntype == "SOURCE":
                src_type = rule.get("source_type", "s3")
                if src_type == "kafka":
                    f.write(f'    {safe_id} = PythonOperator(\n')
                    f.write(f'        task_id="{safe_id}",\n')
                    f.write(f'        python_callable=lambda: print("Kafka ingestion: {node.name}"),\n')
                    f.write(f'    )\n\n')
                else:
                    f.write(f'    {safe_id} = GlueJobOperator(\n')
                    f.write(f'        task_id="{safe_id}",\n')
                    f.write(f'        job_name="bnx-{safe_id}",\n')
                    f.write(f'        script_location="s3://bnx-scripts/jobs/{safe_id}.py",\n')
                    f.write(f'        iam_role_name="bnx-glue-role",\n')
                    f.write(f'        num_of_dpus=2,\n')
                    f.write(f'    )\n\n')

            elif ntype == "SINK":
                f.write(f'    {safe_id} = GlueJobOperator(\n')
                f.write(f'        task_id="{safe_id}",\n')
                f.write(f'        job_name="bnx-{safe_id}",\n')
                f.write(f'        script_location="s3://bnx-scripts/jobs/{safe_id}.py",\n')
                f.write(f'        iam_role_name="bnx-glue-role",\n')
                f.write(f'        num_of_dpus=2,\n')
                f.write(f'    )\n\n')

            else:
                f.write(f'    {safe_id} = GlueJobOperator(\n')
                f.write(f'        task_id="{safe_id}",\n')
                f.write(f'        job_name="bnx-{safe_id}",\n')
                f.write(f'        script_location="s3://bnx-scripts/jobs/{safe_id}.py",\n')
                f.write(f'        iam_role_name="bnx-glue-role",\n')
                f.write(f'        num_of_dpus=2,\n')
                f.write(f'        script_args={{\n')
                f.write(f'            "--node_type": "{ntype}",\n')
                f.write(f'        }},\n')
                f.write(f'    )\n\n')

        # Dependencies
        f.write('    # ?? Dependencies ??????????????????????????\n')
        roots = [n for n in dag.execution_order if not n.parents]
        leaves = [n for n in dag.execution_order if not n.children]

        for node in roots:
            safe_id = node.id.lower().replace('-', '_')
            f.write(f'    start >> {safe_id}\n')

        for node in dag.execution_order:
            safe_id = node.id.lower().replace('-', '_')
            for child_id in node.children:
                if child_id in dag.nodes:
                    safe_child = child_id.lower().replace('-', '_')
                    f.write(f'    {safe_id} >> {safe_child}\n')

        for node in leaves:
            safe_id = node.id.lower().replace('-', '_')
            f.write(f'    {safe_id} >> end\n')
