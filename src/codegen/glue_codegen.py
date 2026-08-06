# src/codegen/glue_codegen.py
import re
from datetime import datetime


def _map_date_functions(expr):
    """Map Ab Initio date functions to Spark SQL equivalents."""
    if not expr:
        return expr
    # date_to_string(date, format) ? date_format(date, format)
    expr = re.sub(r'date_to_string\(', 'date_format(', expr)
    # string_to_date(str, format) ? to_date(str, format)
    expr = re.sub(r'string_to_date\(', 'to_date(', expr)
    # string_to_datetime(str, format) ? to_timestamp(str, format)
    expr = re.sub(r'string_to_datetime\(', 'to_timestamp(', expr)
    # datetime_to_string(dt, format) ? date_format(dt, format)
    expr = re.sub(r'datetime_to_string\(', 'date_format(', expr)
    # date_diff(d1, d2) ? datediff(d1, d2)
    expr = re.sub(r'date_diff\(', 'datediff(', expr)
    # date_add_days(date, n) ? date_add(date, n)
    expr = re.sub(r'date_add_days\(', 'date_add(', expr)
    # date_sub_days(date, n) ? date_sub(date, n)
    expr = re.sub(r'date_sub_days\(', 'date_sub(', expr)
    # today() ? current_date()
    expr = re.sub(r'\btoday\(\)', 'current_date()', expr)
    # now() ? current_timestamp()
    expr = re.sub(r'\bnow\(\)', 'current_timestamp()', expr)
    # year_of(date) ? year(date)
    expr = re.sub(r'year_of\(', 'year(', expr)
    # month_of(date) ? month(date)
    expr = re.sub(r'month_of\(', 'month(', expr)
    # day_of(date) ? dayofmonth(date)
    expr = re.sub(r'day_of\(', 'dayofmonth(', expr)
    # truncate_date(date, "MONTH") ? trunc(date, "MM")
    expr = re.sub(r'truncate_date\(([^,]+),\s*"MONTH"\)', r'trunc(\1, "MM")', expr)
    expr = re.sub(r'truncate_date\(([^,]+),\s*"YEAR"\)', r'trunc(\1, "yyyy")', expr)
    # last_day_of_month(date) ? last_day(date)
    expr = re.sub(r'last_day_of_month\(', 'last_day(', expr)
    return expr


def _map_string_functions(expr):
    """Map Ab Initio string functions to Spark SQL equivalents."""
    if not expr:
        return expr
    expr = re.sub(r'string_upcase\(', 'upper(', expr)
    expr = re.sub(r'string_downcase\(', 'lower(', expr)
    expr = re.sub(r'string_lrtrim\(', 'trim(', expr)
    expr = re.sub(r'string_ltrim\(', 'ltrim(', expr)
    expr = re.sub(r'string_rtrim\(', 'rtrim(', expr)
    expr = re.sub(r'string_length\(', 'length(', expr)
    expr = re.sub(r'string_substring\(', 'substring(', expr)
    expr = re.sub(r'string_replace\(', 'replace(', expr)
    expr = re.sub(r'string_concat\(', 'concat(', expr)
    expr = re.sub(r'string_lpad\(', 'lpad(', expr)
    expr = re.sub(r'string_rpad\(', 'rpad(', expr)
    expr = re.sub(r'string_index\(', 'instr(', expr)
    expr = re.sub(r'string_reverse\(', 'reverse(', expr)
    # Strip "in." prefix from field references
    expr = re.sub(r'\bin\.(\w+)', r'\1', expr)
    return expr

def _build_transform(var_id, src_df, rule):
    """Genera codigo PySpark a partir de una regla XFR { select, where, group_by, sort_by, transform }"""
    
    # --- SORT ---
    sort_by = rule.get("sort_by")
    if sort_by:
        sort_cols = ", ".join(f'"{c}"' for c in sort_by)
        return f'{var_id}_df = {src_df}.orderBy({sort_cols})'
    
    # --- LOOKUP JOIN (from Ab Initio lookup_count/lookup_next pattern) ---
    if rule.get("transform") == "lookup_join":
        lookup_name = rule.get("lookup_name", "lookup")
        raw = rule.get("raw_transform", "")
        output_fields = rule.get("output_fields", [])
        
        # Parse the Ab Initio lookup pattern into PySpark
        import re as _re
        
        # Extract join keys from lookup_count("name", in.key1, in.key2)
        join_keys_match = _re.findall(r'lookup_count\("[^"]+"\s*,\s*in\.(\w+)(?:\s*,\s*in\.(\w+))?', raw)
        join_keys = []
        if join_keys_match:
            for m in join_keys_match:
                join_keys.extend([k for k in m if k])
        
        # Extract filter condition (if statement comparing fields)
        filter_match = _re.search(r'if\(in\.(\w+)\s*(>=|<=|>|<|==)\s*rec\.(\w+)\)', raw)
        filter_cond = ""
        if filter_match:
            filter_cond = f'col("{filter_match.group(1)}") {filter_match.group(2)} col("{filter_match.group(3)}")'
        
        # Extract sort field from vector_sort(vec, {field descending/ascending})
        sort_match = _re.search(r'vector_sort\(\w+,\s*\\?\{?\s*(\w+)\s+(descending|ascending)', raw)
        sort_field = ""
        sort_order = "desc"
        if sort_match:
            sort_field = sort_match.group(1)
            sort_order = "desc" if "desc" in sort_match.group(2) else "asc"
        
        # Extract output field assignment: out.field :: first_without_error(...)
        out_field_match = _re.search(r'out\.(\w+)\s*::\s*first_without_error\(.*?\[0\]\.(\w+)', raw)
        out_field = ""
        lookup_field = ""
        if out_field_match:
            out_field = out_field_match.group(1)
            lookup_field = out_field_match.group(2)
        
        # Generate PySpark code
        lines = []
        lines.append(f'# Lookup Join: {lookup_name} (translated from Ab Initio lookup_count/lookup_next)')
        lines.append(f'# Join keys: {join_keys}, Sort: {sort_field} {sort_order}, Output: {out_field}')
        
        if join_keys:
            join_expr = ", ".join(f'"{k}"' for k in join_keys)
            lines.append(f'{var_id}_df = {src_df}.join(')
            lines.append(f'    broadcast({lookup_name}_df),')
            lines.append(f'    on=[{join_expr}],')
            lines.append(f'    how="left"')
            lines.append(f')')
            
            if filter_cond:
                lines.append(f'{var_id}_df = {var_id}_df.where({filter_cond})')
            
            if sort_field:
                order_fn = f'col("{sort_field}").desc()' if sort_order == "desc" else f'col("{sort_field}")'
                lines.append(f'_w = Window.partitionBy({join_expr}).orderBy({order_fn})')
                lines.append(f'{var_id}_df = {var_id}_df.withColumn("_rn", row_number().over(_w)).where("_rn = 1").drop("_rn")')
            
            if out_field and lookup_field and out_field != lookup_field:
                lines.append(f'{var_id}_df = {var_id}_df.withColumnRenamed("{lookup_field}", "{out_field}")')
        else:
            lines.append(f'{var_id}_df = {src_df}  # Could not parse lookup keys')
        
        return "\n".join(lines)
    
    # --- TRANSFORM EXPRESSIONS (withColumn from reformat) ---
    transform_exprs = rule.get("transform_exprs")
    literals = rule.get("literals")
    if transform_exprs or literals:
        lines = [f'{var_id}_df = {src_df}']
        # Apply where filter first if present
        where = rule.get("where")
        if where:
            lines.append(f'{var_id}_df = {var_id}_df.where("{where}")')
        if transform_exprs:
            for expr_str in transform_exprs:
                if " as " in expr_str.lower():
                    parts = expr_str.rsplit(" as ", 1)
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{parts[1].strip()}", expr("{parts[0].strip()}"))')
        if literals:
            for lit_field in literals:
                fname = lit_field["field"]
                val = lit_field["literal"]
                if lit_field.get("literal_type") == "number":
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{fname}", lit({val}))')
                else:
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{fname}", lit("{val}"))')
        return "\n".join(lines)

    select = rule.get("select", "*")
    where = rule.get("where")
    group_by = rule.get("group_by")

    # Map Ab Initio date functions to Spark
    select = _map_date_functions(select)
    select = _map_string_functions(select)
    if where:
        where = _map_date_functions(where)
        where = _map_string_functions(where)

    if group_by:
        # Genera groupBy().agg() para agregaciones
        # Deduplicate keys preserving order
        group_by = list(dict.fromkeys(group_by))
        keys = ", ".join(f'"{k}"' for k in group_by)
        # Convierte "SUM(amount) as total_spent" ? sum("amount").alias("total_spent")
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

    # Check if this is a reformat (column transformations that keep other columns)
    cols_raw = [c.strip() for c in select.split(",")]
    has_as = any(" as " in c.lower() for c in cols_raw)
    
    if has_as:
        # Reformat: use withColumn for each transformed field to preserve all other columns
        lines = []
        lines.append(f'{var_id}_df = {src_df}')
        for c in cols_raw:
            m = re.match(r'(.+?)\s+as\s+(\w+)', c.strip(), re.I)
            if m:
                expr, alias = m.group(1).strip(), m.group(2)
                lines.append(f'{var_id}_df = {var_id}_df.withColumn("{alias}", expr("{expr}"))')
            else:
                pass
        code = "\n".join(lines)
    else:
        cols = [f'"{c.strip()}"' for c in cols_raw]
        code = f'{var_id}_df = {src_df}.selectExpr({", ".join(cols)})'
    
    if where:
        code += f'\n{var_id}_df = {var_id}_df.where("{where}")'
    return code

def generate_glue(dag, output_path, xfr_rules=None):
    xfr_rules = xfr_rules or {}

    with open(output_path, "w") as f:
        f.write(f'"""\n[*] BNX V54 GENERATED GLUE JOB\n? Generated at: {datetime.now()}\n"""\n\n')
        f.write("from awsglue.context import GlueContext\n")
        f.write("from pyspark.context import SparkContext\n")
        f.write("from pyspark.sql.functions import *\n\n")
        f.write("sc = SparkContext()\nglueContext = GlueContext(sc)\nspark = glueContext.spark_session\n\n")
        f.write('print("[*] BNX Glue Job V54 Started")\n\n')
        f.write("# =========================\n# DAG EXECUTION V54\n# =========================\n\n")

        # Track graph boundaries for Mega-DAG
        graph_boundaries = getattr(dag, 'graph_boundaries', {})
        # Build reverse map: node_id ? graph_name
        node_to_graph = {}
        for gname, nids in graph_boundaries.items():
            if "__" not in gname:  # only top-level graph subgraphs
                for nid in nids:
                    node_to_graph[nid] = gname
        current_graph = None

        for node in dag.execution_order:
            # Insert graph boundary comment if graph changed
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

            # SOURCE
            if ntype == "SOURCE":
                f.write(f'# [+] SOURCE: {log_name}\n')
                src_type = rule.get("source_type", "s3") if rule else "s3"
                path = rule.get("path", f"s3://bnx/raw/{var_id.lower()}") if rule else f"s3://bnx/raw/{var_id.lower()}"
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
                    if fmt == "csv":
                        f.write(f'{var_id}_df = spark.read.format("csv").option("header", "true").option("inferSchema", "true").load("{path}")\n')
                    else:
                        f.write(f'{var_id}_df = spark.read.format("{fmt}").load("{path}")\n')
                # Partition filter (Scan with date filter)
                partition_filter = rule.get("partition_filter") if rule else None
                scan_year = rule.get("scan_year") if rule else None
                scan_month = rule.get("scan_month") if rule else None
                if partition_filter:
                    f.write(f'{var_id}_df = {var_id}_df.where("{partition_filter}")\n')
                elif scan_year or scan_month:
                    filters = []
                    if scan_year: filters.append(f'year = {scan_year}')
                    if scan_month: filters.append(f'month = {scan_month}')
                    f.write(f'{var_id}_df = {var_id}_df.where("{" AND ".join(filters)}")\n')
                f.write(f'print("[>] SOURCE: {log_name}")\n\n')

            # TRANSFORM / XFR
            elif ntype in ("TRANSFORM", "XFR"):
                f.write(f'# [.] TRANSFORM: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    if rule:
                        f.write(_build_transform(var_id, src, rule) + "\n")
                    else:
                        f.write(f'{var_id}_df = {src}.selectExpr("*")  # no XFR rule found\n')
                else:
                    f.write(f'{var_id}_df = None  # no parent\n')
                f.write(f'print("[~] TRANSFORM: {log_name}")\n\n')

            # JOIN
            elif ntype == "JOIN":
                f.write(f'# [~] JOIN: {log_name}\n')
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
                f.write(f'print("[~] JOIN: {log_name}")\n\n')

            # DEDUP ? deduplicaci?n por key
            elif ntype == "DEDUP":
                f.write(f'# [-] DEDUP: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    dedup_keys = rule.get("dedup_keys", ["id"]) if rule else ["id"]
                    order_by = rule.get("order_by") if rule else None
                    if dedup_keys:
                        keys_str = ", ".join(f'"{k}"' for k in dedup_keys)
                        if order_by:
                            # Mantener el registro m?s reciente
                            f.write(f'from pyspark.sql.window import Window\n')
                            f.write(f'_w_{var_id} = Window.partitionBy({keys_str}).orderBy(col("{order_by}").desc())\n')
                            f.write(f'{var_id}_df = {src}.withColumn("_rn", row_number().over(_w_{var_id})).where("_rn = 1").drop("_rn")\n')
                        else:
                            f.write(f'{var_id}_df = {src}.dropDuplicates([{keys_str}])\n')
                    else:
                        # Empty key = dedup on all columns (full record deduplication)
                        f.write(f'{var_id}_df = {src}.dropDuplicates()  # full record dedup\n')
                else:
                    f.write(f'{var_id}_df = None  # no parent\n')
                f.write(f'print("[-] DEDUP: {log_name}")\n\n')

            # NORMALIZE ? un registro ? m?ltiples registros (explode)
            elif ntype == "NORMALIZE":
                f.write(f'# [=] NORMALIZE: {log_name}\n')
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
                f.write(f'print("[=] NORMALIZE: {log_name}")\n\n')

            # LOOKUP ? referencia a dataset externo (broadcast join)
            elif ntype == "LOOKUP":
                f.write(f'# [?] LOOKUP: {log_name}\n')
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
                f.write(f'print("[?] LOOKUP: {log_name}")\n\n')

            # CONCATENATE ? union de datasets sin join key
            elif ntype == "CONCATENATE":
                f.write(f'# [~] CONCATENATE: {log_name}\n')
                if len(parents) >= 2:
                    f.write(f'{var_id}_df = {parents[0]}_df.unionByName({parents[1]}_df, allowMissingColumns=True)\n')
                    for ep in parents[2:]:
                        f.write(f'{var_id}_df = {var_id}_df.unionByName({ep}_df, allowMissingColumns=True)\n')
                elif len(parents) == 1:
                    f.write(f'{var_id}_df = {parents[0]}_df\n')
                else:
                    f.write(f'{var_id}_df = None  # no parents\n')
                f.write(f'print("[~] CONCATENATE: {log_name}")\n\n')

            # GATHER ? merge multiple streams into one
            elif ntype == "GATHER":
                f.write(f'# ? GATHER: {log_name}\n')
                if len(parents) >= 2:
                    f.write(f'{var_id}_df = {parents[0]}_df.unionByName({parents[1]}_df, allowMissingColumns=True)\n')
                    for ep in parents[2:]:
                        f.write(f'{var_id}_df = {var_id}_df.unionByName({ep}_df, allowMissingColumns=True)\n')
                elif len(parents) == 1:
                    f.write(f'{var_id}_df = {parents[0]}_df\n')
                else:
                    f.write(f'{var_id}_df = None\n')
                f.write(f'print("? GATHER: {log_name}")\n\n')

            # PARTITION ? repartition by key
            elif ntype == "PARTITION":
                f.write(f'# ? PARTITION: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    part_keys = rule.get("partition_keys", ["id"]) if rule else ["id"]
                    num_parts = rule.get("num_partitions", "4") if rule else "4"
                    keys_str = ", ".join(f'"{k}"' for k in part_keys) if isinstance(part_keys, list) else f'"{part_keys}"'
                    f.write(f'{var_id}_df = {src}.repartition({num_parts}, {keys_str})\n')
                else:
                    f.write(f'{var_id}_df = None\n')
                f.write(f'print("? PARTITION: {log_name}")\n\n')

            # FILTER ? filter with reject port
            elif ntype == "FILTER":
                f.write(f'# [-] FILTER: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    where = rule.get("where") if rule else None
                    if where:
                        # Translate Ab Initio functions to Spark equivalents
                        if "next_in_sequence()" in where:
                            # next_in_sequence() > 1 skips header rows in raw files.
                            # No-op for structured formats (CSV/parquet with header).
                            f.write(f'# next_in_sequence() filter: no-op for structured formats\n')
                            f.write(f'{var_id}_df = {src}\n')
                            f.write(f'{var_id}_reject_df = spark.createDataFrame([], {src}.schema)\n')
                        elif re.search(r'\b(string_|decimal_|integer_|is_blank|is_defined)', where):
                            mapped = _map_date_functions(where)
                            mapped = re.sub(r'is_blank\((\w+)\)', r'\1 IS NULL OR \1 = ""', mapped)
                            mapped = re.sub(r'is_defined\((\w+)\)', r'\1 IS NOT NULL', mapped)
                            f.write(f'{var_id}_df = {src}.where("{mapped}")\n')
                            f.write(f'{var_id}_reject_df = {src}.where("NOT ({mapped})")\n')
                        else:
                            where = _map_date_functions(where)
                            f.write(f'{var_id}_df = {src}.where("{where}")\n')
                            f.write(f'{var_id}_reject_df = {src}.where("NOT ({where})")\n')
                    else:
                        f.write(f'{var_id}_df = {src}\n')
                        f.write(f'{var_id}_reject_df = spark.createDataFrame([], {src}.schema)\n')
                else:
                    f.write(f'{var_id}_df = None\n')
                f.write(f'print("[-] FILTER: {log_name}")\n\n')

            # SINK
            elif ntype == "SINK":
                f.write(f'# [*] SINK: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    sink_type = rule.get("sink_type", "s3") if rule else "s3"
                    path = rule.get("path", f"s3://bnx/output/{var_id.lower()}") if rule else f"s3://bnx/output/{var_id.lower()}"
                    fmt = rule.get("format", "parquet") if rule else "parquet"
                    topic = rule.get("topic") if rule else None
                    table = rule.get("table") if rule else None
                    conn = rule.get("connection") if rule else None
                    mode = rule.get("mode", "overwrite") if rule else "overwrite"

                    if sink_type == "kafka" and topic:
                        f.write(f'{src}.selectExpr("to_json(struct(*)) AS value")')
                        f.write(f'.write.format("kafka")')
                        f.write(f'.option("kafka.bootstrap.servers", "{conn or "localhost:9092"}")')
                        f.write(f'.option("topic", "{topic}").save()\n')
                    elif sink_type == "jdbc" and (table or conn):
                        f.write(f'{src}.write.format("jdbc").mode("{mode}")')
                        f.write(f'.option("url", "{conn or "jdbc:mysql://localhost:3306/db"}")')
                        f.write(f'.option("dbtable", "{table or var_id.lower()}").save()\n')
                    else:
                        f.write(f'{src}.write.mode("{mode}").format("{fmt}").save("{path}")\n')
                else:
                    f.write(f'# [!] SINK {log_name} has no parent\n')
                f.write(f'print("[>] SINK: {log_name}")\n\n')

            # DML gen?rico
            else:
                f.write(f'# [.] DML ({ntype}): {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    if rule:
                        f.write(_build_transform(var_id, src, rule) + "\n")
                    else:
                        f.write(f'{var_id}_df = {src}  # no rule for {ntype}\n')
                else:
                    f.write(f'{var_id}_df = None  # no parents\n')
                f.write(f'print("[~] DML: {log_name}")\n\n')

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
                src_id = re_edge["from"]
                tgt_id = re_edge["to"]
                sg = re_edge.get("source_graph", "unknown")
                tg = re_edge.get("target_graph", "unknown")
                f.write(f'    # Retroceso: {sg} ? {tg}\n')
                f.write(f'    _staging_path = f"s3://bnx-staging/{sg}_to_{tg}/iteration_{{_iteration}}"\n')
                f.write(f'    {src_id}_df.write.mode("overwrite").parquet(_staging_path)\n')
                f.write(f'    {tgt_id}_df = spark.read.parquet(_staging_path)\n')
                f.write(f'    print(f"  [>] Checkpoint: {sg} ? {tg} ({{_staging_path}})")\n')
            if convergence:
                f.write(f'    # Convergence check: {convergence}\n')
                f.write(f'    # _delta = compute_delta(...)  # implement convergence logic\n')
                f.write(f'    # if {convergence}: break\n')
            f.write(f'    print(f"  [ok] Iteration {{_iteration + 1}} complete")\n\n')

        f.write('print("[ok] BNX Glue Job V54 Finished")\n')