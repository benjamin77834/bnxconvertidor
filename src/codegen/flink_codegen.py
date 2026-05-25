# src/codegen/flink_codegen.py
"""
Generates PyFlink code (Table API / Flink SQL) from BNX DAG.
Uses StreamTableEnvironment as the main entry point.
Each node generates CREATE TABLE DDL (connectors) or CREATE TEMPORARY VIEW (transforms).
"""
import re
from datetime import datetime


def _build_transform_sql(var_id, src_table, rule, is_streaming=False):
    """Generate Flink SQL for a TRANSFORM node."""
    select = rule.get("select", "*")
    where = rule.get("where")
    group_by = rule.get("group_by")

    if group_by:
        keys = ", ".join(group_by)
        # Parse aggregation expressions: SUM(amount) as total ? SUM(amount) AS total
        agg_parts = []
        for col in select.split(","):
            col = col.strip()
            m = re.match(r"(\w+)\((\w+)\)\s+as\s+(\w+)", col, re.I)
            if m:
                fn, field, alias = m.group(1).upper(), m.group(2), m.group(3)
                agg_parts.append(f'{fn}(`{field}`) AS `{alias}`')
            elif col not in group_by:
                agg_parts.append(f'`{col}`')

        select_clause = f"{keys}, {', '.join(agg_parts)}" if agg_parts else keys

        if is_streaming:
            window_size = rule.get("window_size", "5")
            sql = (f"CREATE TEMPORARY VIEW `{var_id}` AS\n"
                   f"  SELECT {select_clause}, window_start, window_end\n"
                   f"  FROM TABLE(TUMBLE(TABLE `{src_table}`, DESCRIPTOR(event_time), INTERVAL '{window_size}' MINUTES))\n"
                   f"  GROUP BY {keys}, window_start, window_end")
        else:
            sql = (f"CREATE TEMPORARY VIEW `{var_id}` AS\n"
                   f"  SELECT {select_clause}\n"
                   f"  FROM `{src_table}`\n"
                   f"  GROUP BY {keys}")
        return sql

    # Simple transform
    cols = select if select != "*" else "*"
    sql = f"CREATE TEMPORARY VIEW `{var_id}` AS\n  SELECT {cols} FROM `{src_table}`"
    if where:
        sql += f"\n  WHERE {where}"
    return sql


def _is_streaming_upstream(node, dag, xfr_rules):
    """Check if a node has a Kafka SOURCE upstream (streaming)."""
    visited = set()

    def check(nid):
        if nid in visited:
            return False
        visited.add(nid)
        if nid not in dag.nodes:
            return False
        n = dag.nodes[nid]
        if n.type.upper() == "SOURCE":
            rule = xfr_rules.get(nid.lower()) or xfr_rules.get(n.name.lower()) or {}
            return rule.get("source_type") == "kafka"
        for pid in n.parents:
            if check(pid):
                return True
        return False

    for pid in node.parents:
        if check(pid):
            return True
    return False


def generate_flink(dag, output_path, xfr_rules=None):
    xfr_rules = xfr_rules or {}

    with open(output_path, "w") as f:
        # Header
        f.write(f'"""\n[>] BNX V54 GENERATED PYFLINK JOB\n')
        f.write(f'? Generated at: {datetime.now()}\n')
        f.write(f'[>] Nodes: {len(dag.execution_order)}\n')
        f.write(f'"""\n\n')

        f.write('from pyflink.table import EnvironmentSettings, TableEnvironment\n')
        f.write('from pyflink.datastream import StreamExecutionEnvironment\n')
        f.write('from pyflink.table import StreamTableEnvironment\n\n')

        f.write('# Initialize Flink environment\n')
        f.write('env = StreamExecutionEnvironment.get_execution_environment()\n')
        f.write('t_env = StreamTableEnvironment.create(env)\n\n')
        f.write('print("[>] BNX PyFlink Job Started")\n\n')
        f.write('# =========================\n# DAG EXECUTION V54 ? FLINK\n# =========================\n\n')

        # Graph boundaries for Mega-DAG
        graph_boundaries = getattr(dag, 'graph_boundaries', {})
        node_to_graph = {}
        for gname, nids in graph_boundaries.items():
            if "__" not in gname:
                for nid in nids:
                    node_to_graph[nid] = gname
        current_graph = None

        for node in dag.execution_order:
            # Graph boundary comment
            if node_to_graph:
                ng = node_to_graph.get(node.id)
                if ng and ng != current_graph:
                    current_graph = ng
                    f.write(f'\n# === GRAPH: {current_graph} ===\n\n')

            var_id = node.id
            log_name = node.name
            ntype = node.type.upper()
            parents = node.parents
            rule = xfr_rules.get(var_id.lower()) or xfr_rules.get(log_name.lower())

            # ?? SOURCE ??
            if ntype == "SOURCE":
                f.write(f'# [+] SOURCE: {log_name}\n')
                src_type = rule.get("source_type", "s3") if rule else "s3"
                path = rule.get("path", f"s3://bnx/raw/{var_id.lower()}") if rule else f"s3://bnx/raw/{var_id.lower()}"
                fmt = rule.get("format", "parquet") if rule else "parquet"
                topic = rule.get("topic") if rule else None
                table = rule.get("table") if rule else None
                conn = rule.get("connection") if rule else None

                if src_type == "kafka" and topic:
                    f.write(f't_env.execute_sql("""\n')
                    f.write(f'  CREATE TABLE `{var_id}_source` (\n')
                    f.write(f'    `value` STRING\n')
                    f.write(f'  ) WITH (\n')
                    f.write(f"    'connector' = 'kafka',\n")
                    f.write(f"    'topic' = '{topic}',\n")
                    f.write(f"    'properties.bootstrap.servers' = '{conn or 'localhost:9092'}',\n")
                    f.write(f"    'scan.startup.mode' = 'earliest-offset',\n")
                    f.write(f"    'format' = 'raw'\n")
                    f.write(f'  )\n')
                    f.write(f'""")\n')
                    f.write(f'{var_id} = t_env.from_path("`{var_id}_source`")\n')
                    f.write(f't_env.create_temporary_view("`{var_id}`", {var_id})\n')
                elif src_type == "jdbc" and (table or conn):
                    f.write(f't_env.execute_sql("""\n')
                    f.write(f'  CREATE TABLE `{var_id}_source` (\n')
                    f.write(f'    `data` STRING\n')
                    f.write(f'  ) WITH (\n')
                    f.write(f"    'connector' = 'jdbc',\n")
                    f.write(f"    'url' = '{conn or 'jdbc:mysql://localhost:3306/db'}',\n")
                    f.write(f"    'table-name' = '{table or var_id.lower()}',\n")
                    f.write(f"    'driver' = 'com.mysql.cj.jdbc.Driver'\n")
                    f.write(f'  )\n')
                    f.write(f'""")\n')
                    f.write(f'{var_id} = t_env.from_path("`{var_id}_source`")\n')
                    f.write(f't_env.create_temporary_view("`{var_id}`", {var_id})\n')
                else:
                    # Filesystem (S3/local)
                    flink_fmt = "csv" if fmt == "csv" else "parquet" if fmt == "parquet" else fmt
                    f.write(f't_env.execute_sql("""\n')
                    f.write(f'  CREATE TABLE `{var_id}_source` (\n')
                    f.write(f'    `data` STRING\n')
                    f.write(f'  ) WITH (\n')
                    f.write(f"    'connector' = 'filesystem',\n")
                    f.write(f"    'path' = '{path}',\n")
                    f.write(f"    'format' = '{flink_fmt}'")
                    if flink_fmt == "csv":
                        f.write(f",\n    'csv.field-delimiter' = ',',\n")
                        f.write(f"    'csv.ignore-parse-errors' = 'true'\n")
                    else:
                        f.write(f"\n")
                    f.write(f'  )\n')
                    f.write(f'""")\n')
                    f.write(f'{var_id} = t_env.from_path("`{var_id}_source`")\n')
                    f.write(f't_env.create_temporary_view("`{var_id}`", {var_id})\n')
                f.write(f'print("[>] SOURCE: {log_name}")\n\n')

            # ?? TRANSFORM ??
            elif ntype in ("TRANSFORM", "XFR"):
                f.write(f'# [.] TRANSFORM: {log_name}\n')
                if parents:
                    src_table = parents[0]
                    if rule:
                        is_stream = _is_streaming_upstream(node, dag, xfr_rules)
                        sql = _build_transform_sql(var_id, src_table, rule, is_stream)
                        f.write(f't_env.execute_sql("""\n  {sql}\n""")\n')
                    else:
                        f.write(f't_env.execute_sql("""CREATE TEMPORARY VIEW `{var_id}` AS SELECT * FROM `{src_table}`""")\n')
                else:
                    f.write(f'{var_id} = None  # no parent\n')
                f.write(f'print("[~] TRANSFORM: {log_name}")\n\n')

            # ?? JOIN ??
            elif ntype == "JOIN":
                f.write(f'# [~] JOIN: {log_name}\n')
                if len(parents) >= 2:
                    jk = rule.get("join_key", "id") if rule else "id"
                    jt = rule.get("join_type", "inner").upper() if rule else "INNER"
                    # First join
                    sql = (f"CREATE TEMPORARY VIEW `{var_id}` AS\n"
                           f"  SELECT * FROM `{parents[0]}` {jt} JOIN `{parents[1]}`\n"
                           f"  ON `{parents[0]}`.`{jk}` = `{parents[1]}`.`{jk}`")
                    f.write(f't_env.execute_sql("""\n  {sql}\n""")\n')
                    # Chained joins for additional parents
                    for i, ep in enumerate(parents[2:], start=1):
                        prev = var_id if i == 1 else f"{var_id}_j{i-1}"
                        next_name = f"{var_id}_j{i}"
                        sql = (f"CREATE TEMPORARY VIEW `{next_name}` AS\n"
                               f"  SELECT * FROM `{prev}` {jt} JOIN `{ep}`\n"
                               f"  ON `{prev}`.`{jk}` = `{ep}`.`{jk}`")
                        f.write(f't_env.execute_sql("""\n  {sql}\n""")\n')
                    if len(parents) > 2:
                        final = f"{var_id}_j{len(parents)-2}"
                        f.write(f't_env.execute_sql("""CREATE TEMPORARY VIEW `{var_id}_final` AS SELECT * FROM `{final}`""")\n')
                elif len(parents) == 1:
                    f.write(f't_env.execute_sql("""CREATE TEMPORARY VIEW `{var_id}` AS SELECT * FROM `{parents[0]}`""")\n')
                else:
                    f.write(f'{var_id} = None  # no parents\n')
                f.write(f'print("[~] JOIN: {log_name}")\n\n')

            # ?? DEDUP ??
            elif ntype == "DEDUP":
                f.write(f'# [-] DEDUP: {log_name}\n')
                if parents:
                    src_table = parents[0]
                    dk = rule.get("dedup_keys", ["id"]) if rule else ["id"]
                    ob = rule.get("order_by") if rule else None
                    keys_str = ", ".join(f"`{k}`" for k in dk)
                    if ob:
                        sql = (f"CREATE TEMPORARY VIEW `{var_id}` AS\n"
                               f"  SELECT * FROM (\n"
                               f"    SELECT *, ROW_NUMBER() OVER (PARTITION BY {keys_str} ORDER BY `{ob}` DESC) AS _rn\n"
                               f"    FROM `{src_table}`\n"
                               f"  ) WHERE _rn = 1")
                    else:
                        sql = (f"CREATE TEMPORARY VIEW `{var_id}` AS\n"
                               f"  SELECT DISTINCT * FROM `{src_table}`")
                    f.write(f't_env.execute_sql("""\n  {sql}\n""")\n')
                else:
                    f.write(f'{var_id} = None  # no parent\n')
                f.write(f'print("[-] DEDUP: {log_name}")\n\n')

            # ?? NORMALIZE ??
            elif ntype == "NORMALIZE":
                f.write(f'# [=] NORMALIZE: {log_name}\n')
                if parents:
                    src_table = parents[0]
                    ec = rule.get("explode_col") if rule else None
                    sc = rule.get("split_col") if rule else None
                    dl = rule.get("delimiter", ",") if rule else ","
                    if ec:
                        sql = (f"CREATE TEMPORARY VIEW `{var_id}` AS\n"
                               f"  SELECT *, {ec}_item\n"
                               f"  FROM `{src_table}`\n"
                               f"  CROSS JOIN UNNEST(`{src_table}`.`{ec}`) AS T({ec}_item)")
                    elif sc:
                        sql = (f"CREATE TEMPORARY VIEW `{var_id}` AS\n"
                               f"  SELECT *, part\n"
                               f"  FROM `{src_table}`\n"
                               f"  CROSS JOIN UNNEST(STRING_TO_ARRAY(`{src_table}`.`{sc}`, '{dl}')) AS T(part)")
                    else:
                        sql = f"CREATE TEMPORARY VIEW `{var_id}` AS SELECT * FROM `{src_table}`"
                    f.write(f't_env.execute_sql("""\n  {sql}\n""")\n')
                else:
                    f.write(f'{var_id} = None  # no parent\n')
                f.write(f'print("[=] NORMALIZE: {log_name}")\n\n')

            # ?? LOOKUP ??
            elif ntype == "LOOKUP":
                f.write(f'# [?] LOOKUP: {log_name}\n')
                if len(parents) >= 2:
                    lk = rule.get("lookup_key", "id") if rule else "id"
                    ls = rule.get("lookup_select") if rule else None
                    main_t = parents[0]
                    ref_t = parents[1]
                    if ls:
                        ref_cols = ", ".join(f"`{ref_t}`.`{c.strip()}`" for c in ls.split(","))
                        select_clause = f"`{main_t}`.*, {ref_cols}"
                    else:
                        select_clause = "*"
                    sql = (f"CREATE TEMPORARY VIEW `{var_id}` AS\n"
                           f"  SELECT {select_clause}\n"
                           f"  FROM `{main_t}` LEFT JOIN `{ref_t}`\n"
                           f"  ON `{main_t}`.`{lk}` = `{ref_t}`.`{lk}`")
                    f.write(f't_env.execute_sql("""\n  {sql}\n""")\n')
                elif len(parents) == 1:
                    f.write(f't_env.execute_sql("""CREATE TEMPORARY VIEW `{var_id}` AS SELECT * FROM `{parents[0]}`""")\n')
                else:
                    f.write(f'{var_id} = None  # no parents\n')
                f.write(f'print("[?] LOOKUP: {log_name}")\n\n')

            # ?? CONCATENATE ??
            elif ntype == "CONCATENATE":
                f.write(f'# [~] CONCATENATE: {log_name}\n')
                if len(parents) >= 2:
                    unions = " UNION ALL ".join(f"SELECT * FROM `{p}`" for p in parents)
                    sql = f"CREATE TEMPORARY VIEW `{var_id}` AS\n  {unions}"
                    f.write(f't_env.execute_sql("""\n  {sql}\n""")\n')
                elif len(parents) == 1:
                    f.write(f't_env.execute_sql("""CREATE TEMPORARY VIEW `{var_id}` AS SELECT * FROM `{parents[0]}`""")\n')
                else:
                    f.write(f'{var_id} = None  # no parents\n')
                f.write(f'print("[~] CONCATENATE: {log_name}")\n\n')

            # ?? GATHER ??
            elif ntype == "GATHER":
                f.write(f'# ? GATHER: {log_name}\n')
                if len(parents) >= 2:
                    unions = " UNION ALL ".join(f"SELECT * FROM `{p}`" for p in parents)
                    sql = f"CREATE TEMPORARY VIEW `{var_id}` AS\n  {unions}"
                    f.write(f't_env.execute_sql("""\n  {sql}\n""")\n')
                elif len(parents) == 1:
                    f.write(f't_env.execute_sql("""CREATE TEMPORARY VIEW `{var_id}` AS SELECT * FROM `{parents[0]}`""")\n')
                else:
                    f.write(f'{var_id} = None  # no parents\n')
                f.write(f'print("? GATHER: {log_name}")\n\n')

            # ?? PARTITION ??
            elif ntype == "PARTITION":
                f.write(f'# ? PARTITION: {log_name}\n')
                if parents:
                    src_table = parents[0]
                    pk = rule.get("partition_keys", ["id"]) if rule else ["id"]
                    np_ = rule.get("num_partitions", "4") if rule else "4"
                    keys_str = ", ".join(f"`{k}`" for k in pk) if isinstance(pk, list) else f"`{pk}`"
                    f.write(f'# Flink partitioning: configured via parallelism and key-by\n')
                    f.write(f'# Partition keys: {keys_str}, num_partitions: {np_}\n')
                    f.write(f't_env.execute_sql("""CREATE TEMPORARY VIEW `{var_id}` AS SELECT * FROM `{src_table}`""")\n')
                else:
                    f.write(f'{var_id} = None  # no parent\n')
                f.write(f'print("? PARTITION: {log_name}")\n\n')

            # ?? FILTER ??
            elif ntype == "FILTER":
                f.write(f'# ? FILTER: {log_name}\n')
                if parents:
                    src_table = parents[0]
                    where = rule.get("where") if rule else None
                    if where:
                        f.write(f't_env.execute_sql("""CREATE TEMPORARY VIEW `{var_id}` AS SELECT * FROM `{src_table}` WHERE {where}""")\n')
                        f.write(f't_env.execute_sql("""CREATE TEMPORARY VIEW `{var_id}_reject` AS SELECT * FROM `{src_table}` WHERE NOT ({where})""")\n')
                    else:
                        f.write(f't_env.execute_sql("""CREATE TEMPORARY VIEW `{var_id}` AS SELECT * FROM `{src_table}`""")\n')
                else:
                    f.write(f'{var_id} = None  # no parent\n')
                f.write(f'print("? FILTER: {log_name}")\n\n')

            # ?? SINK ??
            elif ntype == "SINK":
                f.write(f'# [*] SINK: {log_name}\n')
                if parents:
                    src_table = parents[0]
                    sink_type = rule.get("sink_type", "s3") if rule else "s3"
                    path = rule.get("path", f"s3://bnx/output/{var_id.lower()}") if rule else f"s3://bnx/output/{var_id.lower()}"
                    fmt = rule.get("format", "parquet") if rule else "parquet"
                    topic = rule.get("topic") if rule else None
                    table_name = rule.get("table") if rule else None
                    conn = rule.get("connection") if rule else None
                    mode = rule.get("mode", "overwrite") if rule else "overwrite"

                    if sink_type == "kafka" and topic:
                        f.write(f't_env.execute_sql("""\n')
                        f.write(f'  CREATE TABLE `{var_id}_sink` (\n')
                        f.write(f'    `value` STRING\n')
                        f.write(f'  ) WITH (\n')
                        f.write(f"    'connector' = 'kafka',\n")
                        f.write(f"    'topic' = '{topic}',\n")
                        f.write(f"    'properties.bootstrap.servers' = '{conn or 'localhost:9092'}',\n")
                        f.write(f"    'format' = 'json'\n")
                        f.write(f'  )\n')
                        f.write(f'""")\n')
                    elif sink_type == "jdbc" and (table_name or conn):
                        f.write(f't_env.execute_sql("""\n')
                        f.write(f'  CREATE TABLE `{var_id}_sink` (\n')
                        f.write(f'    `data` STRING\n')
                        f.write(f'  ) WITH (\n')
                        f.write(f"    'connector' = 'jdbc',\n")
                        f.write(f"    'url' = '{conn or 'jdbc:mysql://localhost:3306/db'}',\n")
                        f.write(f"    'table-name' = '{table_name or var_id.lower()}',\n")
                        f.write(f"    'driver' = 'com.mysql.cj.jdbc.Driver'\n")
                        f.write(f'  )\n')
                        f.write(f'""")\n')
                    else:
                        flink_fmt = fmt if fmt in ("csv", "parquet", "json", "avro") else "parquet"
                        f.write(f't_env.execute_sql("""\n')
                        f.write(f'  CREATE TABLE `{var_id}_sink` (\n')
                        f.write(f'    `data` STRING\n')
                        f.write(f'  ) WITH (\n')
                        f.write(f"    'connector' = 'filesystem',\n")
                        f.write(f"    'path' = '{path}',\n")
                        f.write(f"    'format' = '{flink_fmt}'\n")
                        f.write(f'  )\n')
                        f.write(f'""")\n')
                    f.write(f't_env.execute_sql("INSERT INTO `{var_id}_sink` SELECT * FROM `{src_table}`")\n')
                else:
                    f.write(f'# [!] SINK {log_name} has no parent ? nothing to write\n')
                f.write(f'print("[>] SINK: {log_name}")\n\n')

            # ?? Generic / Unknown ??
            else:
                f.write(f'# [.] {ntype}: {log_name}\n')
                if parents:
                    src_table = parents[0]
                    if rule:
                        sql = _build_transform_sql(var_id, src_table, rule)
                        f.write(f't_env.execute_sql("""\n  {sql}\n""")\n')
                    else:
                        f.write(f't_env.execute_sql("""CREATE TEMPORARY VIEW `{var_id}` AS SELECT * FROM `{src_table}`""")\n')
                else:
                    f.write(f'{var_id} = None  # no parents\n')
                f.write(f'print("[~] {ntype}: {log_name}")\n\n')

        # Retroceso iteration logic (cyclic plans)
        retroceso_edges = getattr(dag, 'retroceso_edges', [])
        if retroceso_edges:
            f.write('\n# =========================\n# CYCLIC PLAN ? RETROCESO ITERATIONS\n# =========================\n\n')
            max_iter = max(e.get("max_iterations", 5) for e in retroceso_edges)
            convergence = next((e.get("convergence") for e in retroceso_edges if e.get("convergence")), None)
            f.write(f'MAX_ITERATIONS = {max_iter}\n')
            f.write(f'for _iteration in range(MAX_ITERATIONS):\n')
            f.write(f'    print(f"[~] Iteration {{_iteration + 1}}/{{MAX_ITERATIONS}}")\n')
            for re_edge in retroceso_edges:
                sg = re_edge.get("source_graph", "unknown")
                tg = re_edge.get("target_graph", "unknown")
                f.write(f'    # Retroceso: {sg} ? {tg}\n')
                f.write(f'    # Checkpoint staging: write to intermediate path and re-read\n')
                f.write(f'    _staging_path = f"s3://bnx-staging/{sg}_to_{tg}/iteration_{{_iteration}}"\n')
                f.write(f'    print(f"  [>] Checkpoint: {sg} ? {tg} ({{_staging_path}})")\n')
            if convergence:
                f.write(f'    # Convergence check: {convergence}\n')
                f.write(f'    # if {convergence}: break\n')
            f.write(f'    print(f"  [ok] Iteration {{_iteration + 1}} complete")\n\n')

        # Footer
        f.write('print("[ok] BNX PyFlink Job Finished")\n')
