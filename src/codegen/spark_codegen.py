# src/codegen/spark_codegen.py
"""
Generates pure PySpark code (no Glue dependencies).
Same logic as glue_codegen but with SparkSession instead of GlueContext.
"""
import re
from datetime import datetime


def _map_date_functions(expr):
    """Map Ab Initio date functions to Spark SQL equivalents."""
    if not expr:
        return expr
    expr = re.sub(r'date_to_string\(', 'date_format(', expr)
    expr = re.sub(r'string_to_date\(', 'to_date(', expr)
    expr = re.sub(r'string_to_datetime\(', 'to_timestamp(', expr)
    expr = re.sub(r'datetime_to_string\(', 'date_format(', expr)
    expr = re.sub(r'date_diff\(', 'datediff(', expr)
    expr = re.sub(r'date_add_days\(', 'date_add(', expr)
    expr = re.sub(r'date_sub_days\(', 'date_sub(', expr)
    expr = re.sub(r'\btoday\(\)', 'current_date()', expr)
    expr = re.sub(r'\bnow\(\)', 'current_timestamp()', expr)
    expr = re.sub(r'year_of\(', 'year(', expr)
    expr = re.sub(r'month_of\(', 'month(', expr)
    expr = re.sub(r'day_of\(', 'dayofmonth(', expr)
    expr = re.sub(r'truncate_date\(([^,]+),\s*"MONTH"\)', r'trunc(\1, "MM")', expr)
    expr = re.sub(r'truncate_date\(([^,]+),\s*"YEAR"\)', r'trunc(\1, "yyyy")', expr)
    expr = re.sub(r'last_day_of_month\(', 'last_day(', expr)
    return expr


def _map_string_functions(expr):
    """Map Ab Initio string functions to Spark SQL equivalents."""
    if not expr:
        return expr
    # string_upcase(x) -> upper(x)
    expr = re.sub(r'string_upcase\(', 'upper(', expr)
    # string_downcase(x) -> lower(x)
    expr = re.sub(r'string_downcase\(', 'lower(', expr)
    # string_lrtrim(x) -> trim(x)
    expr = re.sub(r'string_lrtrim\(', 'trim(', expr)
    # string_ltrim(x) -> ltrim(x)
    expr = re.sub(r'string_ltrim\(', 'ltrim(', expr)
    # string_rtrim(x) -> rtrim(x)
    expr = re.sub(r'string_rtrim\(', 'rtrim(', expr)
    # string_length(x) -> length(x)
    expr = re.sub(r'string_length\(', 'length(', expr)
    # string_substring(x, start, len) -> substring(x, start, len)
    expr = re.sub(r'string_substring\(', 'substring(', expr)
    # string_replace(x, old, new) -> replace(x, old, new)
    expr = re.sub(r'string_replace\(', 'replace(', expr)
    # string_concat(a, b) -> concat(a, b)
    expr = re.sub(r'string_concat\(', 'concat(', expr)
    # string_lpad(x, n, c) -> lpad(x, n, c)
    expr = re.sub(r'string_lpad\(', 'lpad(', expr)
    # string_rpad(x, n, c) -> rpad(x, n, c)
    expr = re.sub(r'string_rpad\(', 'rpad(', expr)
    # string_index(x, sub) -> instr(x, sub)
    expr = re.sub(r'string_index\(', 'instr(', expr)
    # string_reverse(x) -> reverse(x)
    expr = re.sub(r'string_reverse\(', 'reverse(', expr)
    # Strip "in." prefix from field references (Ab Initio uses in.field)
    expr = re.sub(r'\bin\.(\w+)', r'\1', expr)
    return expr


def _build_transform(var_id, src_df, rule):
    # --- SORT ---
    sort_by = rule.get("sort_by")
    if sort_by:
        sort_cols = ", ".join(f'"{c}"' for c in sort_by)
        return f'{var_id}_df = {src_df}.orderBy({sort_cols})'
    
    # --- LOOKUP JOIN ---
    if rule.get("transform") == "lookup_join":
        lookup_name = rule.get("lookup_name", "lookup")
        raw = rule.get("raw_transform", "")
        
        import re as _re
        join_keys_match = _re.findall(r'lookup_count\("[^"]+"\s*,\s*in\.(\w+)(?:\s*,\s*in\.(\w+))?', raw)
        join_keys = []
        if join_keys_match:
            for m in join_keys_match:
                join_keys.extend([k for k in m if k])
        
        filter_match = _re.search(r'if\(in\.(\w+)\s*(>=|<=|>|<|==)\s*rec\.(\w+)\)', raw)
        sort_match = _re.search(r'vector_sort\(\w+,\s*\\?\{?\s*(\w+)\s+(descending|ascending)', raw)
        out_field_match = _re.search(r'out\.(\w+)\s*::\s*first_without_error\(.*?\[0\]\.(\w+)', raw)
        
        sort_field = sort_match.group(1) if sort_match else ""
        sort_order = "desc" if sort_match and "desc" in sort_match.group(2) else "asc"
        out_field = out_field_match.group(1) if out_field_match else ""
        lookup_field = out_field_match.group(2) if out_field_match else ""
        
        lines = []
        lines.append(f'# Lookup Join: {lookup_name}')
        if join_keys:
            join_expr = ", ".join(f'"{k}"' for k in join_keys)
            lines.append(f'{var_id}_df = {src_df}.join(broadcast({lookup_name}_df), on=[{join_expr}], how="left")')
            if filter_match:
                lines.append(f'{var_id}_df = {var_id}_df.where(col("{filter_match.group(1)}") {filter_match.group(2)} col("{filter_match.group(3)}"))')
            if sort_field:
                order_fn = f'col("{sort_field}").desc()' if sort_order == "desc" else f'col("{sort_field}")'
                lines.append(f'_w = Window.partitionBy({join_expr}).orderBy({order_fn})')
                lines.append(f'{var_id}_df = {var_id}_df.withColumn("_rn", row_number().over(_w)).where("_rn = 1").drop("_rn")')
            if out_field and lookup_field and out_field != lookup_field:
                lines.append(f'{var_id}_df = {var_id}_df.withColumnRenamed("{lookup_field}", "{out_field}")')
        else:
            lines.append(f'{var_id}_df = {src_df}  # Could not parse lookup keys')
        return "\n".join(lines)
    
    # --- TRANSFORM EXPRESSIONS ---
    transform_exprs = rule.get("transform_exprs")
    literals = rule.get("literals")
    if transform_exprs or literals:
        lines = [f'{var_id}_df = {src_df}']
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
        # Deduplicate keys preserving order
        group_by = list(dict.fromkeys(group_by))
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

    # Check if this is a reformat (column transformations that keep other columns)
    # Pattern: "expr as field, expr as field" where fields are being replaced/transformed
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
                # plain column reference, skip (already exists)
                pass
        code = "\n".join(lines)
    else:
        cols = [f'"{c.strip()}"' for c in cols_raw]
        code = f'{var_id}_df = {src_df}.selectExpr({", ".join(cols)})'
    
    if where:
        code += f'\n{var_id}_df = {var_id}_df.where("{where}")'
    return code


def generate_spark(dag, output_path, xfr_rules=None):
    xfr_rules = xfr_rules or {}

    with open(output_path, "w") as f:
        f.write(f'"""\n[*] BNX V54 GENERATED PYSPARK JOB\n? Generated at: {datetime.now()}\n"""\n\n')
        f.write("import os\n")
        f.write("from pyspark.sql import SparkSession\n")
        f.write("from pyspark.sql.functions import *\n")
        f.write("from pyspark.sql import functions as F\n")
        f.write("from pyspark.sql.window import Window\n\n")
        f.write('spark = SparkSession.builder.appName("BNX_Pipeline").getOrCreate()\n\n')
        f.write('# =========================\n# PARAMETERS\n# =========================\n')
        f.write('class PARAMS:\n')
        f.write('    BASE_PATH = "s3://datalake-bnx-scripts-dev"  # Override via spark-submit --conf\n\n')
        f.write('print("[*] BNX PySpark Job Started")\n\n')
        f.write("# =========================\n# HELPER FUNCTIONS\n# =========================\n\n")
        # Generate filter_by_expression helper for header/trailer detection
        f.write("def filter_by_expression_hdr_trl(df, field, start, length, exclude_values):\n")
        f.write('    """Filter rows where substring(field, start, length) is NOT in exclude_values.\n')
        f.write('    Used to remove header/trailer records from flat files.\n')
        f.write('    """\n')
        f.write("    return df.filter(~F.substring(F.col(field), start, length).isin(exclude_values))\n\n\n")
        # Generate is_valid_record helper
        f.write("def is_valid_record(df, validation_rules=None):\n")
        f.write('    """Validate records based on Ab Initio _vrule validation rules.\n')
        f.write('    Returns tuple: (valid_df, invalid_df)\n')
        f.write('    """\n')
        f.write('    if validation_rules is None:\n')
        f.write('        return df, spark.createDataFrame([], df.schema)\n')
        f.write('    condition = None\n')
        f.write('    for rule in validation_rules:\n')
        f.write('        field = rule["field"]\n')
        f.write('        rule_type = rule.get("type", "not_null")\n')
        f.write('        if rule_type == "not_null":\n')
        f.write('            c = F.col(field).isNotNull()\n')
        f.write('        elif rule_type == "length":\n')
        f.write('            c = F.length(F.col(field)) <= rule["max_length"]\n')
        f.write('        elif rule_type == "range":\n')
        f.write('            c = (F.col(field) >= rule["min"]) & (F.col(field) <= rule["max"])\n')
        f.write('        elif rule_type == "in_list":\n')
        f.write('            c = F.col(field).isin(rule["values"])\n')
        f.write('        else:\n')
        f.write('            continue\n')
        f.write('        condition = c if condition is None else condition & c\n')
        f.write('    if condition is None:\n')
        f.write('        return df, spark.createDataFrame([], df.schema)\n')
        f.write('    valid_df = df.filter(condition)\n')
        f.write('    invalid_df = df.filter(~condition)\n')
        f.write('    return valid_df, invalid_df\n\n\n')
        f.write("# =========================\n# DAG EXECUTION V54\n# =========================\n\n")

        # Track graph boundaries for Mega-DAG
        graph_boundaries = getattr(dag, 'graph_boundaries', {})
        node_to_graph = {}
        for gname, nids in graph_boundaries.items():
            if "__" not in gname:
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

            if ntype == "SOURCE":
                f.write(f'# [+] SOURCE: {log_name}\n')
                src_type = rule.get("source_type", "s3") if rule else "s3"
                path = rule.get("path") if rule else None
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
                    src_name = var_id.lower()
                    if path:
                        read_path = path
                    else:
                        read_path = None
                    if fmt == "csv":
                        if read_path:
                            f.write(f'{var_id}_df = spark.read.option("header", "true").option("inferSchema", "true").csv("{read_path}")\n')
                        else:
                            f.write(f'{var_id}_df = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{{PARAMS.BASE_PATH}}/raw/{src_name}")\n')
                    elif fmt == "json":
                        if read_path:
                            f.write(f'{var_id}_df = spark.read.json("{read_path}")\n')
                        else:
                            f.write(f'{var_id}_df = spark.read.json(f"{{PARAMS.BASE_PATH}}/raw/{src_name}")\n')
                    else:
                        if read_path:
                            f.write(f'{var_id}_df = spark.read.parquet("{read_path}")\n')
                        else:
                            f.write(f'{var_id}_df = spark.read.parquet(f"{{PARAMS.BASE_PATH}}/raw/{src_name}")\n')
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

            elif ntype in ("TRANSFORM", "XFR"):
                f.write(f'# [.] TRANSFORM: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    # Detect Run_Program components
                    is_run_program = ("run_program" in log_name.lower() or
                                      "run_program" in var_id.lower())
                    if is_run_program and rule and rule.get("raw_transform"):
                        raw_cmd = rule.get("raw_transform", "")
                        cmd_clean = re.sub(r'\$AI_SERIAL_BKP', f'{{PARAMS.BASE_PATH}}/backup', raw_cmd)
                        cmd_clean = re.sub(r'\$AI_SERIAL', f'{{PARAMS.BASE_PATH}}/raw', cmd_clean)
                        cmd_clean = re.sub(r'\$\{?AI_SERIAL_BKP\}?', f'{{PARAMS.BASE_PATH}}/backup', cmd_clean)
                        cmd_clean = re.sub(r'\$\{?AI_SERIAL\}?', f'{{PARAMS.BASE_PATH}}/raw', cmd_clean)
                        cmd_clean = re.sub(r'\$\{?(\w+)\}?', r'{PARAMS.\1}', cmd_clean)
                        f.write(f'# Run_Program: shell command from Ab Initio\n')
                        f.write(f'{var_id}_df = {src}  # passthrough data\n')
                        f.write(f'os.system(f"{cmd_clean}")\n')
                    elif is_run_program:
                        f.write(f'# Run_Program: no commandline extracted\n')
                        f.write(f'{var_id}_df = {src}  # passthrough (Run_Program)\n')
                        f.write(f'# os.system(f"{{PARAMS.BASE_PATH}}/scripts/{var_id.lower()}.sh")\n')
                    elif rule:
                        f.write(_build_transform(var_id, src, rule) + "\n")
                    else:
                        f.write(f'{var_id}_df = {src}.selectExpr("*")\n')
                else:
                    # No parents — check if Run_Program
                    is_run_program = ("run_program" in log_name.lower() or
                                      "run_program" in var_id.lower())
                    if is_run_program and rule and rule.get("raw_transform"):
                        raw_cmd = rule.get("raw_transform", "")
                        cmd_clean = re.sub(r'\$AI_SERIAL_BKP', f'{{PARAMS.BASE_PATH}}/backup', raw_cmd)
                        cmd_clean = re.sub(r'\$AI_SERIAL', f'{{PARAMS.BASE_PATH}}/raw', cmd_clean)
                        cmd_clean = re.sub(r'\$\{?AI_SERIAL_BKP\}?', f'{{PARAMS.BASE_PATH}}/backup', cmd_clean)
                        cmd_clean = re.sub(r'\$\{?AI_SERIAL\}?', f'{{PARAMS.BASE_PATH}}/raw', cmd_clean)
                        cmd_clean = re.sub(r'\$\{?(\w+)\}?', r'{PARAMS.\1}', cmd_clean)
                        f.write(f'# Run_Program: shell command (no data dependency)\n')
                        f.write(f'os.system(f"{cmd_clean}")\n')
                        f.write(f'{var_id}_df = None  # Run_Program has no dataframe output\n')
                    elif is_run_program:
                        f.write(f'# Run_Program: no commandline extracted from MP\n')
                        f.write(f'# os.system(f"{{PARAMS.BASE_PATH}}/scripts/{var_id.lower()}.sh")\n')
                        f.write(f'{var_id}_df = None  # Run_Program has no dataframe output\n')
                    else:
                        f.write(f'{var_id}_df = None\n')
                f.write(f'print("[~] TRANSFORM: {log_name}")\n\n')

            elif ntype == "FILTER":
                f.write(f'# [-] FILTER: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    where = rule.get("where", "") if rule else ""
                    if where:
                        # Detect header/trailer filter pattern:
                        # Pattern 1: string_substring(field, 1, N) not member [ vector "X", "Y" ]
                        hdr_trl_match = re.search(
                            r'string_substring\(([^,]+),\s*(\d+),\s*(\d+)\)\s+not\s+member\s*\[\s*vector\s+(.*?)\]',
                            where, re.IGNORECASE
                        )
                        # Pattern 2: if((string_substring(field,1,N)!='HDR' and string_substring(field,1,N)!='TRL')...)
                        # This is the same logic expressed as if/else with != comparisons
                        hdr_trl_if_match = None
                        if not hdr_trl_match:
                            hdr_trl_if_match = re.search(
                                r"string_substring\((\w+),\s*(\d+),\s*(\d+)\)\s*!=\s*'([^']+)'",
                                where, re.IGNORECASE
                            )
                        
                        if hdr_trl_match:
                            field = hdr_trl_match.group(1).strip()
                            field = re.sub(r'^in\d*\.', '', field)
                            start = hdr_trl_match.group(2)
                            length = hdr_trl_match.group(3)
                            values_raw = hdr_trl_match.group(4).strip()
                            values_list = re.findall(r'"([^"]*)"', values_raw)
                            values_str = ", ".join(f'"{v}"' for v in values_list)
                            f.write(f'{var_id}_df = filter_by_expression_hdr_trl({src}, "{field}", {start}, {length}, [{values_str}])\n')
                            f.write(f'{var_id}_reject_df = {src}.filter(F.substring(F.col("{field}"), {start}, {length}).isin([{values_str}]))\n')
                        elif hdr_trl_if_match:
                            # Extract all != values from the if expression
                            field = hdr_trl_if_match.group(1).strip()
                            field = re.sub(r'^in\d*\.', '', field)
                            # Find all string_substring(field, start, len)!='VALUE' patterns
                            all_checks = re.findall(
                                r"string_substring\(\w+,\s*(\d+),\s*(\d+)\)\s*!=\s*'([^']+)'",
                                where
                            )
                            # Group by (start, length) and collect excluded values
                            exclude_groups = {}
                            for start, length, val in all_checks:
                                key = (start, length)
                                if key not in exclude_groups:
                                    exclude_groups[key] = []
                                if val not in exclude_groups[key]:
                                    exclude_groups[key].append(val)
                            
                            # Check for is_valid(this_record) pattern
                            has_is_valid = "is_valid" in where
                            
                            if exclude_groups:
                                # Use the most common (start, length) pair
                                main_key = max(exclude_groups, key=lambda k: len(exclude_groups[k]))
                                start, length = main_key
                                values_list = exclude_groups[main_key]
                                values_str = ", ".join(f'"{v}"' for v in values_list)
                                f.write(f'{var_id}_df = filter_by_expression_hdr_trl({src}, "{field}", {start}, {length}, [{values_str}])\n')
                                if has_is_valid:
                                    f.write(f'# is_valid(this_record) — apply record validation\n')
                                    f.write(f'{var_id}_df, {var_id}_reject_df = is_valid_record({var_id}_df)\n')
                                else:
                                    f.write(f'{var_id}_reject_df = {src}.filter(F.substring(F.col("{field}"), {start}, {length}).isin([{values_str}]))\n')
                            else:
                                f.write(f'{var_id}_df = {src}\n')
                                f.write(f'{var_id}_reject_df = spark.createDataFrame([], {src}.schema)\n')
                        elif "next_in_sequence()" in where:
                            f.write(f'# next_in_sequence() filter: no-op for structured formats\n')
                            f.write(f'{var_id}_df = {src}\n')
                        elif re.search(r'\b(string_|decimal_|integer_|is_blank|is_defined)', where):
                            mapped = _map_date_functions(where)
                            mapped = _map_string_functions(mapped)
                            mapped = re.sub(r'is_blank\((\w+)\)', r'\1 IS NULL OR \1 = ""', mapped)
                            mapped = re.sub(r'is_defined\((\w+)\)', r'\1 IS NOT NULL', mapped)
                            mapped_escaped = mapped.replace('"', '\\"')
                            f.write(f'{var_id}_df = {src}.where("{mapped_escaped}")\n')
                            f.write(f'{var_id}_reject_df = {src}.where("NOT ({mapped_escaped})")\n')
                        else:
                            where_mapped = _map_date_functions(where)
                            where_mapped = _map_string_functions(where_mapped)
                            where_escaped = where_mapped.replace('"', '\\"')
                            f.write(f'{var_id}_df = {src}.where("{where_escaped}")\n')
                            f.write(f'{var_id}_reject_df = {src}.where("NOT ({where_escaped})")\n')
                    else:
                        f.write(f'{var_id}_df = {src}\n')
                        f.write(f'{var_id}_reject_df = spark.createDataFrame([], {src}.schema)\n')
                else:
                    f.write(f'{var_id}_df = None\n')
                f.write(f'print("[-] FILTER: {log_name}")\n\n')

            elif ntype == "JOIN":
                f.write(f'# [~] JOIN: {log_name}\n')
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
                f.write(f'print("[~] JOIN: {log_name}")\n\n')

            elif ntype == "DEDUP":
                f.write(f'# [-] DEDUP: {log_name}\n')
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
                f.write(f'print("[-] DEDUP: {log_name}")\n\n')

            elif ntype == "NORMALIZE":
                f.write(f'# [=] NORMALIZE: {log_name}\n')
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
                f.write(f'print("[=] NORMALIZE: {log_name}")\n\n')

            elif ntype == "LOOKUP":
                f.write(f'# [?] LOOKUP: {log_name}\n')
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
                f.write(f'print("[?] LOOKUP: {log_name}")\n\n')

            elif ntype == "SINK":
                f.write(f'# [*] SINK: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    sink_type = rule.get("sink_type", "s3") if rule else "s3"
                    path = rule.get("path") if rule else None
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
                        if path:
                            f.write(f'{src}.write.mode("{mode}").parquet("{path}")\n')
                        else:
                            f.write(f'{src}.write.mode("{mode}").parquet(f"{{PARAMS.BASE_PATH}}/output/{var_id.lower()}")\n')
                else:
                    f.write(f'# [!] SINK {log_name} has no parent\n')
                f.write(f'print("[>] SINK: {log_name}")\n\n')

            else:
                f.write(f'# [.] {ntype}: {log_name}\n')
                if parents:
                    if rule:
                        f.write(_build_transform(var_id, f'{parents[0]}_df', rule) + "\n")
                    else:
                        f.write(f'{var_id}_df = {parents[0]}_df\n')
                else:
                    f.write(f'{var_id}_df = None\n')
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
                src_id = re_edge["from"]
                tgt_id = re_edge["to"]
                sg = re_edge.get("source_graph", "unknown")
                tg = re_edge.get("target_graph", "unknown")
                f.write(f'    # Retroceso: {sg} ? {tg}\n')
                f.write(f'    _staging_path = f"s3a://bnx-staging/{sg}_to_{tg}/iteration_{{_iteration}}"\n')
                f.write(f'    {src_id}_df.write.mode("overwrite").parquet(_staging_path)\n')
                f.write(f'    {tgt_id}_df = spark.read.parquet(_staging_path)\n')
                f.write(f'    print(f"  [>] Checkpoint: {sg} ? {tg} ({{_staging_path}})")\n')
            if convergence:
                f.write(f'    # Convergence check: {convergence}\n')
                f.write(f'    # _delta = compute_delta(...)\n')
                f.write(f'    # if {convergence}: break\n')
            f.write(f'    print(f"  [ok] Iteration {{_iteration + 1}} complete")\n\n')

        f.write('spark.stop()\n')
        f.write('print("[ok] BNX PySpark Job Finished")\n')
