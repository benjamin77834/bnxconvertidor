# src/codegen/glue_codegen.py
import re
from datetime import datetime
from src.codegen.spark_codegen import _translate_dml_expr, _map_date_functions, _map_string_functions


# Local functions removed — using improved versions from spark_codegen


def _translate_abinitio_expr(raw_expr):
    """Translate a complete Ab Initio DML expression to Spark SQL.
    
    Handles: string_*, if/else, date_*, lookup(), type casts, etc.
    Returns a valid Spark SQL expression string.
    """
    if not raw_expr:
        return raw_expr
    
    expr = raw_expr.strip()
    
    # Delegate to _translate_dml_expr for expressions that start with type-cast patterns
    # e.g. (date("YYYY-MM-DD")) (string("|")) field_name
    # The _translate_dml_expr handles these correctly by stripping all casts first
    if re.match(r'\([a-z]+\(', expr):
        result = _translate_dml_expr(expr)
        if result != expr:
            return result
    
    # Translate Ab Initio type casts to Spark SQL CAST
    # (string(N))expr → CAST(expr AS STRING)
    # (decimal(N))expr → CAST(expr AS DECIMAL)
    # (integer(N))expr → CAST(expr AS INT)
    # (date("fmt"))expr → to_date(expr, "fmt")  
    # (datetime("fmt"))expr → to_timestamp(expr, "fmt")
    # Pattern: (type(arg))followed_by_expression
    def _replace_cast(m):
        cast_type = m.group(1)
        cast_arg = m.group(2)
        following = m.group(3)
        if cast_type == 'string':
            return f'CAST({following} AS STRING)'
        elif cast_type == 'decimal':
            return f'CAST({following} AS DECIMAL({cast_arg}))'
        elif cast_type == 'integer':
            return f'CAST({following} AS INT)'
        elif cast_type == 'date':
            return f'to_date({following}, {cast_arg})'
        elif cast_type == 'datetime':
            return f'to_timestamp({following}, {cast_arg})'
        return following
    
    # Match (type(arg))expression — expression is the next token (word, function call, or quoted string)
    # We need to capture what follows the cast. It can be: field_name, function(...), or "literal"
    # Simple approach: remove the cast wrapper, keep the value — but wrap with CAST when it's string/decimal
    expr = re.sub(r'\(string\((\d+)\)\)(\w[\w.]*)', r'CAST(\2 AS STRING)', expr)
    expr = re.sub(r'\(decimal\((\d+)\)\)(\w[\w.]*)', r'CAST(\2 AS DECIMAL(\1))', expr)
    expr = re.sub(r'\(integer\(\d+\)\)(\w[\w.]*)', r'CAST(\1 AS INT)', expr)
    # For function calls after cast: (string(10))some_func(...) → CAST(some_func(...) AS STRING)
    expr = re.sub(r'\(string\(\d+\)\)([\w]+\([^)]*\))', r'CAST(\1 AS STRING)', expr)
    expr = re.sub(r'\(decimal\((\d+)\)\)([\w]+\([^)]*\))', r'CAST(\2 AS DECIMAL(\1))', expr)
    # Date casts with format → to_date/to_timestamp
    expr = re.sub(r'\(date\("([^"]+)"\)\)(\w[\w.]*)', r'to_date(\2, "\1")', expr)
    expr = re.sub(r'\(datetime\("([^"]+)"\)\)(\w[\w.]*)', r'to_timestamp(\2, "\1")', expr)
    # Fallback: just remove unmatched cast wrappers
    expr = re.sub(r'\(date\("[^"]*"\)\)', '', expr)
    expr = re.sub(r'\(datetime\("[^"]*"\)\)', '', expr)
    expr = re.sub(r'\(string\(\d+\)\)', '', expr)
    expr = re.sub(r'\(decimal\(\d+\)\)', '', expr)
    expr = re.sub(r'\(integer\(\d+\)\)', '', expr)
    
    # Strip "in." and "in0." and "in1." prefixes
    expr = re.sub(r'\bin\d*\.(\w+)', r'\1', expr)
    
    # Map Ab Initio functions to Spark SQL
    expr = _map_string_functions(expr)
    expr = _map_date_functions(expr)
    
    # date_difference_days(d1, d2) → datediff(d1, d2)
    expr = re.sub(r'date_difference_days\(', 'datediff(', expr)
    # date_week_of_year(date) → weekofyear(date)
    expr = re.sub(r'date_week_of_year\(', 'weekofyear(', expr)
    # date_day_of_month(date) → dayofmonth(date)
    expr = re.sub(r'date_day_of_month\(', 'dayofmonth(', expr)
    # date_year(date) → year(date)
    expr = re.sub(r'date_year\(', 'year(', expr)
    # date_month(date) → month(date)
    expr = re.sub(r'date_month\(', 'month(', expr)
    
    # !is_null(field) → field IS NOT NULL (must be before is_null)
    expr = re.sub(r'!is_null\((\w+)\)', r'\1 IS NOT NULL', expr)
    # is_null(field) → field IS NULL
    expr = re.sub(r'is_null\((\w+)\)', r'\1 IS NULL', expr)
    
    # Ab Initio if/else → Spark CASE WHEN
    # Pattern: if(cond) value1 else if(cond2) value2 else value3
    if re.search(r'\bif\s*\(', expr):
        expr = _translate_if_else_to_case(expr)
    
    # Remove lookup() calls — these need broadcast join, mark with comment
    if 'lookup(' in expr:
        # Extract: lookup("Name", key).field → NULL /* lookup: Name.field */
        expr = re.sub(
            r'lookup\("([^"]+)"\s*,\s*[^)]+\)\.(\w+)',
            r'NULL /* TODO: lookup \1.\2 */',
            expr
        )
    
    # Clean up double spaces
    expr = re.sub(r'\s+', ' ', expr).strip()
    
    # Remove trailing semicolons
    expr = expr.rstrip(';').strip()
    
    return expr


def _translate_if_else_to_case(expr):
    """Convert Ab Initio if/else if/else chain to Spark SQL CASE WHEN.
    
    Input:  if(cond1) val1 else if(cond2) val2 else val3
    Output: CASE WHEN cond1 THEN val1 WHEN cond2 THEN val2 ELSE val3 END
    """
    result = "CASE"
    remaining = expr.strip()
    
    max_iterations = 20
    iteration = 0
    
    while remaining and iteration < max_iterations:
        iteration += 1
        remaining = remaining.strip()
        
        # Match: if(condition) or if (condition)
        m = re.match(r'if\s*\(', remaining)
        if not m:
            # This is the final ELSE value
            remaining = remaining.strip().rstrip(';').strip()
            if remaining:
                result += f" ELSE {remaining}"
            break
        
        # Find the matching closing parenthesis for the if(
        start_paren = remaining.index('(')
        paren_depth = 0
        cond_end = -1
        for i in range(start_paren, len(remaining)):
            if remaining[i] == '(':
                paren_depth += 1
            elif remaining[i] == ')':
                paren_depth -= 1
                if paren_depth == 0:
                    cond_end = i
                    break
        
        if cond_end < 0:
            # Malformed — just return original
            return expr
        
        condition = remaining[start_paren + 1:cond_end].strip()
        rest = remaining[cond_end + 1:].strip()
        
        # Now extract the THEN value: everything until we hit ' else ' at top level
        # We need to handle quoted strings and nested parens
        value = ""
        else_pos = -1
        depth = 0
        in_str = False
        str_char = None
        i = 0
        while i < len(rest):
            c = rest[i]
            if c in ('"', "'") and not in_str:
                in_str = True
                str_char = c
            elif c == str_char and in_str:
                in_str = False
            elif not in_str:
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                elif depth == 0 and rest[i:i+5] == ' else' and (i + 5 >= len(rest) or not rest[i+5].isalnum()):
                    else_pos = i
                    break
            i += 1
        
        if else_pos >= 0:
            value = rest[:else_pos].strip().rstrip(';').strip()
            after_else = rest[else_pos + 5:].strip()  # skip ' else'
            # Check if next token is 'if' (else if chain)
            if after_else.startswith('if'):
                remaining = after_else
            else:
                # Final else value
                remaining = after_else
                # Map == to = in condition
                condition = condition.replace('==', '=')
                result += f" WHEN {condition} THEN {value}"
                # The remaining is the ELSE value
                final_val = remaining.strip().rstrip(';').strip()
                if final_val:
                    result += f" ELSE {final_val}"
                remaining = ""
                break
        else:
            # No else found — this is the last branch
            value = rest.strip().rstrip(';').strip()
            remaining = ""
        
        # Map == to = in condition for SQL
        condition = condition.replace('==', '=')
        result += f" WHEN {condition} THEN {value}"
    
    result += " END"
    return result


def _find_else_keyword(text):
    """Find the position of 'else' keyword not inside quotes or nested if().
    DEPRECATED: Use the inline logic in _translate_if_else_to_case instead.
    """
    idx = text.find(' else ')
    return idx if idx >= 0 else text.find(' else\n')

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
        
        import re as _re
        
        # Extract join keys from lookup_count("name", in.key1, in.key2)
        join_keys_match = _re.findall(r'lookup_count\("[^"]+"\s*,\s*in\.(\w+)(?:\s*,\s*in\.(\w+))?', raw)
        join_keys = []
        if join_keys_match:
            for m in join_keys_match:
                join_keys.extend([k for k in m if k])
        
        # Generate PySpark code
        lines = []
        lines.append(f'# Lookup Join: {lookup_name} (translated from Ab Initio lookup_count/lookup_next)')
        
        if join_keys:
            join_expr = ", ".join(f'"{k}"' for k in join_keys)
            lines.append(f'{var_id}_df = {src_df}.join(')
            lines.append(f'    broadcast({lookup_name}_df),')
            lines.append(f'    on=[{join_expr}],')
            lines.append(f'    how="left"')
            lines.append(f')')
        else:
            lines.append(f'{var_id}_df = {src_df}  # Could not parse lookup keys')
        
        return "\n".join(lines)
    
    # --- RAW TRANSFORM (complete Ab Initio DML body) ---
    raw_transform = rule.get("raw_transform")
    if raw_transform and not rule.get("select") and not rule.get("dml_fields"):
        # Parse field assignments from raw DML: out.field :: expression;
        field_matches = re.findall(r'out\.(\w+)\s*::\s*(.+?);', raw_transform)
        if field_matches:
            lines = [f'{var_id}_df = {src_df}']
            where = rule.get("where")
            if where:
                where = _translate_abinitio_expr(where)
                lines.append(f'{var_id}_reject_df = {var_id}_df.where("NOT ({where})")')
                lines.append(f'{var_id}_df = {var_id}_df.where("{where}")')
            else:
                lines.append(f'{var_id}_reject_df = spark.createDataFrame([], {var_id}_df.schema)')
            
            for field_name, raw_expr in field_matches:
                if field_name in ("newline", "*", "V_FILLER"):
                    continue
                raw_expr = raw_expr.strip()
                # Skip pure passthrough: in.field_name
                if re.match(r'^in\d*\.' + re.escape(field_name) + r'$', raw_expr):
                    continue
                
                spark_expr = _translate_abinitio_expr(raw_expr)
                
                # Generate PySpark-native API when possible instead of expr()
                # Pattern: CAST(field AS TYPE) → col("field").cast("type")
                cast_match = re.match(r'^CAST\((\w+)\s+AS\s+(\w+)\)$', spark_expr)
                # Pattern: trim(CAST(field AS STRING)) → F.trim(col("field").cast("string"))
                trim_cast_match = re.match(r'^trim\(CAST\((\w+)\s+AS\s+(\w+)\)\)$', spark_expr)
                # Pattern: CAST(trim(field) AS TYPE) → F.trim(col("field")).cast("type")
                cast_trim_match = re.match(r'^CAST\(trim\((\w+)\)\s+AS\s+(\w+)\)$', spark_expr)
                # Pattern: trim(field) → F.trim(col("field"))
                trim_match = re.match(r'^trim\((\w+)\)$', spark_expr)
                # Pattern: substring(field, start, len) → F.substring(col("field"), start, len)
                substr_match = re.match(r'^substring\((\w+),\s*(\d+),\s*(\d+)\)$', spark_expr)
                # Pattern: lpad(substring(field, s, l), n, c) → F.lpad(F.substring(...), n, c)
                lpad_substr_match = re.match(r'^lpad\(substring\((\w+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*"([^"]*)"\)$', spark_expr)
                
                if trim_cast_match:
                    src_col = trim_cast_match.group(1)
                    cast_type = trim_cast_match.group(2).lower()
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", F.trim(F.col("{src_col}").cast("{cast_type}")))')
                elif cast_trim_match:
                    src_col = cast_trim_match.group(1)
                    cast_type = cast_trim_match.group(2).lower()
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", F.trim(F.col("{src_col}")).cast("{cast_type}"))')
                elif cast_match:
                    src_col = cast_match.group(1)
                    cast_type = cast_match.group(2).lower()
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", F.col("{src_col}").cast("{cast_type}"))')
                elif trim_match:
                    src_col = trim_match.group(1)
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", F.trim(F.col("{src_col}")))')
                elif substr_match:
                    src_col = substr_match.group(1)
                    start = substr_match.group(2)
                    length = substr_match.group(3)
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", F.substring(F.col("{src_col}"), {start}, {length}))')
                elif lpad_substr_match:
                    src_col = lpad_substr_match.group(1)
                    s = lpad_substr_match.group(2)
                    l = lpad_substr_match.group(3)
                    n = lpad_substr_match.group(4)
                    c = lpad_substr_match.group(5)
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", F.lpad(F.substring(F.col("{src_col}"), {s}, {l}), {n}, "{c}"))')
                else:
                    # General case: use expr() — but wrap with F. functions where possible
                    spark_expr_escaped = spark_expr.replace('"', '\\"')
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", expr("{spark_expr_escaped}"))')
            
            return "\n".join(lines)
    
    # --- DML FIELDS (parsed from external .xfr with Ab Initio DML) ---
    dml_fields = rule.get("dml_fields")
    if dml_fields:
        lines = [f'{var_id}_df = {src_df}']
        for f in dml_fields:
            fname = f["field"]
            expr_val = f["expr"]
            lines.append(f'{var_id}_df = {var_id}_df.withColumn("{fname}", {expr_val})')
        return "\n".join(lines)
    
    # --- TRANSFORM EXPRESSIONS (withColumn from reformat) ---
    transform_exprs = rule.get("transform_exprs")
    literals = rule.get("literals")
    if transform_exprs or literals:
        lines = [f'{var_id}_df = {src_df}']
        where = rule.get("where")
        if where:
            where = _translate_abinitio_expr(where)
            lines.append(f'{var_id}_df = {var_id}_df.where("{where}")')
        if transform_exprs:
            for expr_str in transform_exprs:
                if " as " in expr_str.lower():
                    parts = expr_str.rsplit(" as ", 1)
                    spark_expr = _translate_abinitio_expr(parts[0].strip())
                    spark_expr_escaped = spark_expr.replace('"', '\\"')
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{parts[1].strip()}", expr("{spark_expr_escaped}"))')
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

    # NOTE: Do NOT translate the full select string here — it contains multiple
    # comma-separated expressions that must be translated individually after splitting.
    # Only translate for group_by aggregation (which expects already-split parts).
    if where:
        where = _translate_abinitio_expr(where)

    if group_by:
        # Deduplicate keys preserving order
        group_by = list(dict.fromkeys(group_by))
        keys = ", ".join(f'"{k}"' for k in group_by)
        # Parse "SUM(amount) as total_spent" → sum("amount").alias("total_spent")
        agg_exprs = []
        for col_expr in select.split(","):
            col_expr = col_expr.strip()
            m = re.match(r"(\w+)\((\w+)\)\s+as\s+(\w+)", col_expr, re.I)
            if m:
                fn, field, alias = m.group(1).lower(), m.group(2), m.group(3)
                agg_exprs.append(f'{fn}("{field}").alias("{alias}")')
            else:
                agg_exprs.append(f'col("{col_expr}")')
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
                raw_expr = m.group(1).strip()
                alias = m.group(2)
                # Apply DML→Spark translation
                translated = _translate_dml_expr(raw_expr)
                translated_escaped = translated.replace('"', '\\"')
                lines.append(f'{var_id}_df = {var_id}_df.withColumn("{alias}", expr("{translated_escaped}"))')
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

    # Pre-scan: determine which helpers are needed
    needs_filter_hdr_trl = False
    needs_is_valid = False
    needs_output_split = False
    for node in dag.execution_order:
        rule = xfr_rules.get(node.id.lower()) or xfr_rules.get(node.name.lower())
        if node.type.upper() == "FILTER" and rule and rule.get("where"):
            where = rule["where"]
            if re.search(r"string_substring\(\w+,\s*\d+,\s*\d+\)\s*!=\s*'", where):
                needs_filter_hdr_trl = True
            if "is_valid" in where:
                needs_is_valid = True
        if (node.type.upper() in ("TRANSFORM", "XFR") and len(node.children) > 2
            and not rule and ("reformat" in node.name.lower() or "rfmt" in node.name.lower())):
            needs_output_split = True

    with open(output_path, "w") as f:
        f.write(f'"""\n[*] BNX V54 GENERATED GLUE JOB\n? Generated at: {datetime.now()}\n"""\n\n')
        f.write("import os\n")
        f.write("from awsglue.context import GlueContext\n")
        f.write("from pyspark.context import SparkContext\n")
        f.write("from pyspark.sql.functions import *\n")
        f.write("from pyspark.sql import functions as F\n\n")
        f.write("sc = SparkContext()\nglueContext = GlueContext(sc)\nspark = glueContext.spark_session\n\n")
        f.write('# =========================\n# PARAMETERS\n# =========================\n')
        f.write('class PARAMS:\n')
        f.write('    BASE_PATH = os.environ.get("BNX_BASE_PATH", "s3://datalake-bnx-scripts-dev")\n\n')
        f.write('print("[*] BNX Glue Job V54 Started")\n\n')
        
        # Emit only the helpers that are actually used in this graph
        if needs_filter_hdr_trl or needs_is_valid or needs_output_split:
            f.write("# =========================\n# HELPER FUNCTIONS\n# =========================\n\n")
        
        if needs_filter_hdr_trl:
            f.write("def filter_by_expression_hdr_trl(df, field, start, length, exclude_values):\n")
            f.write('    """Filter rows where substring(field, start, length) is NOT in exclude_values."""\n')
            f.write("    return df.filter(~F.substring(F.col(field), start, length).isin(exclude_values))\n\n\n")
        
        if needs_is_valid:
            f.write("def is_valid_record(df, validation_rules=None):\n")
            f.write('    """Validate records. Returns tuple: (valid_df, invalid_df)"""\n')
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
            f.write('    return df.filter(condition), df.filter(~condition)\n\n\n')
        
        if needs_output_split:
            f.write("def output_indexes_split(df, index_expr, num_outputs):\n")
            f.write('    """Split DataFrame into N outputs based on index expression."""\n')
            f.write('    return [df.filter(F.expr(f"{index_expr} = {i}")) for i in range(num_outputs)]\n\n\n')
        
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
                path = rule.get("path") if rule else None
                fmt = rule.get("format", "parquet") if rule else "parquet"
                topic = rule.get("topic") if rule else None
                table = rule.get("table") if rule else None
                conn = rule.get("connection") if rule else None

                # Check for db_source (Input_Table from Teradata/Oracle/etc.)
                node_data = next((n for n in dag.execution_order if n.id == var_id), None)
                db_src = getattr(node_data, 'db_source', None) if node_data else None
                if not db_src and rule:
                    db_src = rule.get("db_source")

                if db_src:
                    dbms = db_src.get("dbms", "unknown")
                    query = db_src.get("query", "")
                    # Clean up Ab Initio variable references in query
                    import re as _re
                    query_clean = _re.sub(r'\$\\\{([^}]+)\\\}', r'${\1}', query)
                    query_clean = _re.sub(r'\$\{([^}]+)\}', r'${\1}', query_clean)
                    f.write(f'# Original DB: {dbms}\n')
                    f.write(f'# Original Query: {query_clean[:200]}\n')
                    f.write(f'{var_id}_df = spark.read.parquet(f"{{PARAMS.BASE_PATH}}/landing/{var_id.lower()}")\n')
                    # Apply WHERE clause from original query if present
                    where_match = _re.search(r'where\s+(.+)', query_clean, _re.IGNORECASE | _re.DOTALL)
                    if where_match:
                        where_clause = where_match.group(1).strip().rstrip(';')
                        f.write(f'# Applying original WHERE filter:\n')
                        f.write(f'# {var_id}_df = {var_id}_df.where("{where_clause}")\n')
                elif src_type == "kafka" and topic:
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
                    path_resolved = rule.get("path_resolved") if rule else False
                    if path and path_resolved:
                        # Path from Layout, use PARAMS.BASE_PATH + relative path
                        if fmt == "csv":
                            f.write(f'{var_id}_df = spark.read.format("csv").option("header", "true").option("inferSchema", "true").load(f"{{PARAMS.BASE_PATH}}/raw/{path}")\n')
                        else:
                            f.write(f'{var_id}_df = spark.read.parquet(f"{{PARAMS.BASE_PATH}}/raw/{path}")\n')
                    elif path:
                        # Explicit full path (e.g. s3://...)
                        if fmt == "csv":
                            f.write(f'{var_id}_df = spark.read.format("csv").option("header", "true").option("inferSchema", "true").load("{path}")\n')
                        else:
                            f.write(f'{var_id}_df = spark.read.parquet("{path}")\n')
                    else:
                        if fmt == "csv":
                            f.write(f'{var_id}_df = spark.read.format("csv").option("header", "true").option("inferSchema", "true").load(f"{{PARAMS.BASE_PATH}}/raw/{src_name}")\n')
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

            # TRANSFORM / XFR / ROLLUP
            elif ntype in ("TRANSFORM", "XFR", "ROLLUP"):
                label = "ROLLUP" if ntype == "ROLLUP" else "TRANSFORM"
                f.write(f'# [.] {label}: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    # Detect Run_Program components (shell commands)
                    is_run_program = ("run_program" in log_name.lower() or 
                                      "run_program" in var_id.lower())
                    # Detect multi-output Reformat with output_indexes
                    # Only true multi-output splits have >2 children (out0+out1+...+reject != multi-output)
                    # A reformat with 2 children where one goes to SINK (reject file) is NOT multi-output
                    has_multi_output = False
                    if (len(node.children) > 2 and not rule and
                        ("reformat" in log_name.lower() or "rfmt" in log_name.lower())):
                        has_multi_output = True
                    elif (len(node.children) == 2 and not rule and
                          ("reformat" in log_name.lower() or "rfmt" in log_name.lower())):
                        # Check if BOTH children are non-SINK (true split) vs one is SINK (out+reject pattern)
                        child_types = [dag.nodes[c].type.upper() for c in node.children if c in dag.nodes]
                        if "SINK" not in child_types:
                            has_multi_output = True
                    if is_run_program and rule and rule.get("raw_transform"):
                        # Extract commandline from raw_transform
                        raw_cmd = rule.get("raw_transform", "")
                        # Clean Ab Initio variables: $AI_SERIAL -> PARAMS paths
                        cmd_clean = re.sub(r'\$AI_SERIAL_BKP', f'{{PARAMS.BASE_PATH}}/backup', raw_cmd)
                        cmd_clean = re.sub(r'\$AI_SERIAL', f'{{PARAMS.BASE_PATH}}/raw', cmd_clean)
                        cmd_clean = re.sub(r'\$\{?AI_SERIAL_BKP\}?', f'{{PARAMS.BASE_PATH}}/backup', cmd_clean)
                        cmd_clean = re.sub(r'\$\{?AI_SERIAL\}?', f'{{PARAMS.BASE_PATH}}/raw', cmd_clean)
                        # Replace other $VAR references with {PARAMS.VAR}
                        cmd_clean = re.sub(r'\$\{?(\w+)\}?', r'{PARAMS.\1}', cmd_clean)
                        f.write(f'# Run_Program: shell command from Ab Initio\n')
                        f.write(f'{var_id}_df = {src}  # passthrough data\n')
                        f.write(f'os.system(f"{cmd_clean}")\n')
                    elif is_run_program:
                        f.write(f'# Run_Program: no commandline extracted\n')
                        f.write(f'{var_id}_df = {src}  # passthrough (Run_Program)\n')
                        f.write(f'# os.system(f"{{PARAMS.BASE_PATH}}/scripts/{var_id.lower()}.sh")\n')
                    elif has_multi_output and not rule:
                        # Multi-output Reformat with output_indexes: split into N outputs
                        num_outputs = len(node.children)
                        f.write(f'# Multi-output Reformat (output_indexes): splits into {num_outputs} streams\n')
                        f.write(f'{var_id}_df = {src}  # el nodo en si (por si se referencia)\n')
                        f.write(f'_{var_id}_splits = output_indexes_split({var_id}_df, "output_port_index", {num_outputs})\n')
                        for idx, child_id in enumerate(node.children):
                            f.write(f'{child_id}_df = _{var_id}_splits[{idx}]  # port {idx}\n')
                    elif rule:
                        f.write(_build_transform(var_id, src, rule) + "\n")
                    else:
                        f.write(f'{var_id}_df = {src}.selectExpr("*")  # passthrough\n')
                else:
                    # No parents — check if Run_Program
                    is_run_program_nop = ("run_program" in log_name.lower() or
                                          "run_program" in var_id.lower())
                    if is_run_program_nop and rule and rule.get("raw_transform"):
                        raw_cmd = rule.get("raw_transform", "")
                        cmd_clean = re.sub(r'\$AI_SERIAL_BKP', f'{{PARAMS.BASE_PATH}}/backup', raw_cmd)
                        cmd_clean = re.sub(r'\$AI_SERIAL', f'{{PARAMS.BASE_PATH}}/raw', cmd_clean)
                        cmd_clean = re.sub(r'\$\{?AI_SERIAL_BKP\}?', f'{{PARAMS.BASE_PATH}}/backup', cmd_clean)
                        cmd_clean = re.sub(r'\$\{?AI_SERIAL\}?', f'{{PARAMS.BASE_PATH}}/raw', cmd_clean)
                        cmd_clean = re.sub(r'\$\{?(\w+)\}?', r'{PARAMS.\1}', cmd_clean)
                        f.write(f'# Run_Program: shell command (no data dependency)\n')
                        f.write(f'os.system(f"{cmd_clean}")\n')
                        f.write(f'{var_id}_df = None  # Run_Program has no dataframe output\n')
                    elif is_run_program_nop:
                        f.write(f'# Run_Program: no commandline extracted from MP\n')
                        f.write(f'# os.system(f"{{PARAMS.BASE_PATH}}/scripts/{var_id.lower()}.sh")\n')
                        f.write(f'{var_id}_df = None  # Run_Program has no dataframe output\n')
                    else:
                        # Check if this node has a db_source (Input_Table without edges resolved)
                        node_data = next((n for n in dag.execution_order if n.id == var_id), None)
                        db_src = getattr(node_data, 'db_source', None) if node_data else None
                        if db_src:
                            query = db_src.get("query", "").replace("$\\{EDW_TER_DEFAULT_DB\\}", "${EDW_TER_DEFAULT_DB}")
                            f.write(f'# DB Source: {db_src.get("dbms", "unknown")}\n')
                            f.write(f'{var_id}_df = spark.read.parquet(f"{{PARAMS.BASE_PATH}}/landing/{var_id.lower()}")\n')
                        elif rule and rule.get("path"):
                            f.write(f'{var_id}_df = spark.read.parquet("{rule["path"]}")\n')
                        else:
                            f.write(f'{var_id}_df = spark.read.parquet(f"{{PARAMS.BASE_PATH}}/landing/{var_id.lower()}")\n')
                f.write(f'print("[~] {label}: {log_name}")\n\n')

            # JOIN
            elif ntype == "JOIN":
                f.write(f'# [~] JOIN: {log_name}\n')
                if len(parents) >= 2:
                    join_key = rule.get("join_key", None) if rule else None
                    join_type = rule.get("join_type", None) if rule else None
                    
                    # If no explicit key, try to extract from embedded keys_by_vertex
                    if not join_key:
                        node_rule = xfr_rules.get(var_id.lower()) or xfr_rules.get(log_name.lower()) or {}
                        join_key = node_rule.get("join_key", None)
                    
                    # Determine join type from rule or default to "left" (safer than inner)
                    if not join_type:
                        node_rule = xfr_rules.get(var_id.lower()) or xfr_rules.get(log_name.lower()) or {}
                        join_type = node_rule.get("join_type", "left")
                    
                    if not join_key:
                        f.write(f'# ⚠️ WARNING: join key not found in .mp — sube el .xfr o revisa key={{}} en el MP\n')
                    
                    # Generate join
                    if join_key and isinstance(join_key, list):
                        keys_list = "[" + ", ".join(f'"{k}"' for k in join_key) + "]"
                        f.write(f'{var_id}_df = {parents[0]}_df.join({parents[1]}_df, on={keys_list}, how="{join_type}")\n')
                        for ep in parents[2:]:
                            f.write(f'{var_id}_df = {var_id}_df.join({ep}_df, on={keys_list}, how="{join_type}")\n')
                    elif join_key:
                        f.write(f'{var_id}_df = {parents[0]}_df.join({parents[1]}_df, on="{join_key}", how="{join_type}")\n')
                        for ep in parents[2:]:
                            f.write(f'{var_id}_df = {var_id}_df.join({ep}_df, on="{join_key}", how="{join_type}")\n')
                    else:
                        # No key at all — leave placeholder that user must fill
                        f.write(f'{var_id}_df = {parents[0]}_df.join({parents[1]}_df, on=["TODO_JOIN_KEY"], how="{join_type}")  # TODO: specify join key\n')
                        for ep in parents[2:]:
                            f.write(f'{var_id}_df = {var_id}_df.join({ep}_df, on=["TODO_JOIN_KEY"], how="{join_type}")\n')
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

            # FILTER - filter with reject port
            elif ntype == "FILTER":
                f.write(f'# [-] FILTER: {log_name}\n')
                if parents:
                    src = f'{parents[0]}_df'
                    where = rule.get("where") if rule else None
                    if where:
                        # Detect Ab Initio header/trailer filter pattern:
                        # Pattern 1: string_substring(field, 1, N) not member [ vector "X", "Y" ]
                        hdr_trl_match = re.search(
                            r'string_substring\(([^,]+),\s*(\d+),\s*(\d+)\)\s+not\s+member\s*\[\s*vector\s+(.*?)\]',
                            where, re.IGNORECASE
                        )
                        # Pattern 2: if((string_substring(field,1,N)!='HDR' and ...))
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
                            field = hdr_trl_if_match.group(1).strip()
                            field = re.sub(r'^in\d*\.', '', field)
                            all_checks = re.findall(
                                r"string_substring\(\w+,\s*(\d+),\s*(\d+)\)\s*!=\s*'([^']+)'",
                                where
                            )
                            exclude_groups = {}
                            for start, length, val in all_checks:
                                key = (start, length)
                                if key not in exclude_groups:
                                    exclude_groups[key] = []
                                if val not in exclude_groups[key]:
                                    exclude_groups[key].append(val)
                            
                            has_is_valid = "is_valid" in where
                            
                            if exclude_groups:
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
                            f.write(f'{var_id}_reject_df = spark.createDataFrame([], {src}.schema)\n')
                        else:
                            spark_where = _translate_abinitio_expr(where)
                            spark_where_escaped = spark_where.replace('"', '\\"')
                            f.write(f'{var_id}_df = {src}.where("{spark_where_escaped}")\n')
                            f.write(f'{var_id}_reject_df = {src}.where("NOT ({spark_where_escaped})")\n')
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
                    path = rule.get("path") if rule else None
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
                        path_resolved = rule.get("path_resolved") if rule else False
                        # Clean Ab Initio path expressions
                        if path:
                            path = re.sub(r'\$\[\(date\("YYYYMMDD"\)\)now\(\)\]', '{date_str}', path)
                            path = re.sub(r'\$FILE_DATE', '{date_str}', path)
                            path = re.sub(r'\$\{?(\w+)\}?', r'{\1}', path)
                        if path and path_resolved:
                            f.write(f'_date_str = spark.sql("SELECT date_format(current_date(), \'yyyyMMdd\')").collect()[0][0]\n')
                            f.write(f'{src}.write.mode("{mode}").parquet(f"{{PARAMS.BASE_PATH}}/output/{path}")\n')
                        elif path:
                            f.write(f'_date_str = spark.sql("SELECT date_format(current_date(), \'yyyyMMdd\')").collect()[0][0]\n')
                            f.write(f'{src}.write.mode("{mode}").parquet(f"{{PARAMS.BASE_PATH}}/output/{path}")\n')
                        else:
                            f.write(f'{src}.write.mode("{mode}").parquet(f"{{PARAMS.BASE_PATH}}/output/{var_id.lower()}")\n')
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