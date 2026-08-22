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
    # Ab Initio date casting: (date("YYYY-MM-DD"))field → to_date(field, "yyyy-MM-dd")
    # Pattern: (date("FORMAT"))expr or (date("FORMAT"))(type)expr
    expr = re.sub(
        r'\(date\("YYYY-MM-DD"\)\)\s*\(([^)]+)\)\s*(\w+)',
        r'to_date(cast(\2 as string), "yyyy-MM-dd")',
        expr
    )
    expr = re.sub(
        r'\(date\("YYYY-MM-DD"\)\)\s*(\w+)',
        r'to_date(\1, "yyyy-MM-dd")',
        expr
    )
    expr = re.sub(
        r'\(date\("YYYYMMDD"\)\)\s*(\w+)',
        r'date_format(\1, "yyyyMMdd")',
        expr
    )
    # (datetime("YYYY-MM-DDTHH24:MI:SS"))expr → to_timestamp(expr)
    expr = re.sub(
        r'\(datetime\("[^"]+"\)\)\s*(\w+)',
        r'to_timestamp(\1)',
        expr
    )
    # date_add_months(date, N) → add_months(date, N)
    expr = re.sub(r'date_add_months\(', 'add_months(', expr)
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
    # $[(date("YYYYMMDD"))now()] → date_format(current_date(), "yyyyMMdd")
    expr = re.sub(
        r'\$\[\(date\("YYYYMMDD"\)\)now\(\)\]',
        'date_format(current_date(), "yyyyMMdd")',
        expr
    )
    return expr


def _map_string_functions(expr):
    """Map Ab Initio string functions to Spark SQL equivalents."""
    if not expr:
        return expr
    # first_defined(a, b) → coalesce(a, b)
    expr = re.sub(r'first_defined\(', 'coalesce(', expr)
    # length_of(x) → size(x) for arrays, length(x) for strings
    expr = re.sub(r'length_of\(', 'size(', expr)
    # decimal_strip(x) → trim(cast(x as string))  
    expr = re.sub(r'decimal_strip\(([^)]+)\)', r'cast(trim(cast(\1 as string)) as decimal(18,2))', expr)
    # is_null(x) → x IS NULL
    expr = re.sub(r'is_null\(([^)]+)\)', r'\1 IS NULL', expr)
    # is_defined(x) → x IS NOT NULL
    expr = re.sub(r'is_defined\(([^)]+)\)', r'\1 IS NOT NULL', expr)
    # is_valid(x) → (x IS NOT NULL) — Ab Initio valida formato; en Spark aproximamos a no-null.
    # Debe ir ANTES de is_blank para no colisionar. Soporta parentesis anidados (CAST(...)).
    expr = _replace_balanced_call(expr, "is_valid", lambda inner: f"({inner} IS NOT NULL)")
    # is_blank(x) → (x IS NULL OR x = "")
    expr = re.sub(r'is_blank\(([^)]+)\)', r'(\1 IS NULL OR \1 = "")', expr)
    # lookup_match("NAME", key) → true  (simplified — actual lookup resolved at join level)
    expr = re.sub(r'lookup_match\("[^"]+",\s*[^)]+\)', 'true', expr)
    # string_upcase(x) → upper(x)
    expr = re.sub(r'string_upcase\(', 'upper(', expr)
    # string_downcase(x) → lower(x)
    expr = re.sub(r'string_downcase\(', 'lower(', expr)
    # string_lrtrim(x) → trim(x)
    expr = re.sub(r'string_lrtrim\(', 'trim(', expr)
    # string_ltrim(x) → ltrim(x)
    expr = re.sub(r'string_ltrim\(', 'ltrim(', expr)
    # string_rtrim(x) → rtrim(x)
    expr = re.sub(r'string_rtrim\(', 'rtrim(', expr)
    # string_length(x) → length(x)
    expr = re.sub(r'string_length\(', 'length(', expr)
    # string_substring(x, start, len) → substring(x, start, len)
    expr = re.sub(r'string_substring\(', 'substring(', expr)
    # string_replace(x, old, new) → replace(x, old, new)
    expr = re.sub(r'string_replace\(', 'replace(', expr)
    # string_replace_first(x, old, new) → regexp_replace(x, old, new)
    expr = re.sub(r'string_replace_first\(', 'regexp_replace(', expr)
    # string_concat(a, b) → concat(a, b)
    expr = re.sub(r'string_concat\(', 'concat(', expr)
    # string_lpad(x, n, c) → lpad(x, n, c)
    expr = re.sub(r'string_lpad\(', 'lpad(', expr)
    # string_rpad(x, n, c) → rpad(x, n, c)
    expr = re.sub(r'string_rpad\(', 'rpad(', expr)
    # string_index(x, sub) → instr(x, sub)
    expr = re.sub(r'string_index\(', 'instr(', expr)
    # string_like(x, pattern[, escape]) → (x LIKE pattern) (patrones usan % y _)
    # Ab Initio admite un 3er argumento (caracter de escape) que Spark no necesita en LIKE simple.
    # 3 argumentos:
    expr = re.sub(
        r'string_like\(\s*([^,]+?)\s*,\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')\s*,\s*(?:"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')\s*\)',
        r'(\1 LIKE \2)',
        expr,
    )
    # 2 argumentos:
    expr = re.sub(
        r'string_like\(\s*([^,]+?)\s*,\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')\s*\)',
        r'(\1 LIKE \2)',
        expr,
    )
    # string_is_alphabetic(x) → x rlike "^[A-Za-z]*$"
    expr = re.sub(r'string_is_alphabetic\(\s*([^)]+?)\s*\)', r'(\1 rlike "^[A-Za-z]*$")', expr)
    # string_is_numeric(x) → x rlike "^[0-9]*$"
    expr = re.sub(r'string_is_numeric\(\s*([^)]+?)\s*\)', r'(\1 rlike "^[0-9]*$")', expr)
    # string_char(x, n) → substring(x, n, 1)
    expr = re.sub(r'string_char\(\s*([^,]+?)\s*,\s*([^)]+?)\s*\)', r'substring(\1, \2, 1)', expr)
    # string_reverse(x) → reverse(x)
    expr = re.sub(r'string_reverse\(', 'reverse(', expr)
    # string_split(x, delim) → split(x, delim)
    expr = re.sub(r'string_split\(', 'split(', expr)
    # string_filter_out(x, pattern) → regexp_replace(x, pattern, "")
    expr = re.sub(r'string_filter_out\(([^,]+),\s*([^)]+)\)', r'regexp_replace(\1, \2, "")', expr)
    # string_join(arr, sep) → array_join(arr, sep)
    expr = re.sub(r'string_join\(', 'array_join(', expr)
    # (string("|"))expr → cast(expr as string) (Ab Initio type casting)
    expr = re.sub(r'\(string\("[^"]*"\)\)\s*', 'cast(', expr)
    # (decimal("|"))expr → cast(expr as decimal)
    expr = re.sub(r'\(decimal\("[^"]*"\)\)\s*', 'cast(', expr)
    # member [vector ...] → IN (...)
    expr = re.sub(r'\s+member\s+\[vector\s+([^\]]+)\]', r' IN (\1)', expr)
    # Strip "in." and "in0." prefix from field references (Ab Initio uses in.field)
    expr = re.sub(r'\bin\d*\.(\w+)', r'\1', expr)
    # Strip "out." prefix
    expr = re.sub(r'\bout\.(\w+)', r'\1', expr)
    return expr


def _replace_balanced_call(expr, func_name, transform):
    """Reemplaza func_name(...) respetando parentesis anidados.
    transform recibe el contenido interno y devuelve el reemplazo."""
    result = expr
    pattern = re.compile(r'\b' + re.escape(func_name) + r'\s*\(')
    guard = 0
    while guard < 50:
        guard += 1
        m = pattern.search(result)
        if not m:
            break
        open_idx = m.end() - 1  # posicion del '('
        close_idx = _match_paren(result, open_idx)
        if close_idx == -1:
            break
        inner = result[open_idx + 1:close_idx]
        replacement = transform(inner.strip())
        result = result[:m.start()] + replacement + result[close_idx + 1:]
    return result


def _match_paren(s, open_idx):
    """Dado el índice de un '(' devuelve el índice de su ')' balanceado, o -1.
    Respeta comillas simples/dobles para no contar paréntesis dentro de strings."""
    depth = 0
    quote = None
    i = open_idx
    while i < len(s):
        ch = s[i]
        if quote:
            if ch == quote and s[i - 1] != '\\':
                quote = None
        elif ch in ('"', "'"):
            quote = ch
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _split_else(s):
    """Divide 'val1 else val2' respetando parentesis/comillas y anidamiento de if.
    Devuelve (then_part, else_part) o (s, None) si no hay else de nivel superior."""
    depth = 0
    quote = None
    i = 0
    while i < len(s):
        ch = s[i]
        if quote:
            if ch == quote and s[i - 1] != '\\':
                quote = None
        elif ch in ('"', "'"):
            quote = ch
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif depth == 0:
            # Buscar 'else' como palabra completa en nivel superior
            m = re.match(r'\belse\b', s[i:], re.IGNORECASE)
            if m:
                return s[:i].strip(), s[i + m.end():].strip()
        i += 1
    return s.strip(), None


def _translate_if_else(expr):
    """Convierte if(cond) then_val else else_val (posiblemente anidado) a CASE WHEN,
    respetando parentesis balanceados. Soporta cadenas if...else if...else."""
    e = expr.strip()
    m = re.match(r'^if\s*\(', e, re.IGNORECASE)
    if not m:
        return expr

    open_idx = e.index('(', m.start())
    close_idx = _match_paren(e, open_idx)
    if close_idx == -1:
        return expr  # parentesis desbalanceado, no tocar

    cond = e[open_idx + 1:close_idx].strip()
    rest = e[close_idx + 1:].strip()

    then_part, else_part = _split_else(rest)
    if else_part is None:
        # if sin else → CASE WHEN cond THEN then END
        return f'CASE WHEN {cond} THEN {then_part} END'

    # else if... encadenado → traducir recursivamente el else
    if re.match(r'^if\s*\(', else_part, re.IGNORECASE):
        inner = _translate_if_else(else_part)
        return f'CASE WHEN {cond} THEN {then_part} ELSE {inner} END'

    return f'CASE WHEN {cond} THEN {then_part} ELSE {else_part} END'


def _translate_dml_expr(expr_clean):
    """Translate a single Ab Initio DML expression to Spark SQL."""
    mapped = expr_clean
    # Clean up Ab Initio syntax FIRST (before function mapping)
    mapped = re.sub(r'\bin\d*\.', '', mapped)   # remove in./in0./in1. prefix
    mapped = re.sub(r'\bout\.', '', mapped)     # remove out. prefix
    # Variables/parametros Ab Initio: $VAR o ${VAR}. Dentro de una expresion se
    # refieren a un campo/parametro; quitamos el $ para que sea un identificador
    # valido en Spark SQL (evita "Syntax error at or near '$'").
    # NOTA: $[...] (expresion inline con corchetes) se maneja aparte mas abajo.
    mapped = re.sub(r'\$\{(\w+)\}', r'\1', mapped)
    mapped = re.sub(r'\$(?![\[\{])(\w+)', r'\1', mapped)
    # Remove :1: (priority operator in Ab Initio)
    mapped = re.sub(r'\s*:1:\s*', ' ', mapped)
    
    # Handle Ab Initio type casting patterns BEFORE function mapping:
    # Pattern: (date("FORMAT"))(string("delim"))field → to_date(cast(field as string), "spark_fmt")
    # Pattern: (date("YYYY-MM-DD"))field → to_date(field, "yyyy-MM-dd")
    # Pattern: (string("|"))field → cast(field as string)
    # Strategy: remove ALL type cast prefixes, then wrap result appropriately
    
    # Detect if this is a date cast expression (comillas dobles O simples).
    # Puede haber varios casts de fecha encadenados; tomamos el ULTIMO formato,
    # que es el que aplica al campo (p.ej. (date('YYYY-MM-DD'))(date('YYYYMMDD'))campo).
    has_date_cast = bool(re.search(r'''\(date\(['"][^'"]+['"]\)\)''', mapped))
    date_fmt = None
    if has_date_cast:
        fmt_matches = re.findall(r'''\(date\(['"]([^'"]+)['"]\)\)''', mapped)
        if fmt_matches:
            ab_fmt = fmt_matches[-1]  # el ultimo cast es el formato de origen del campo
            date_fmt = ab_fmt.replace("YYYY", "yyyy").replace("MM", "MM").replace("DD", "dd")
    
    # Remove ALL type cast prefixes con delimitador entre comillas (dobles o simples):
    # (type("delim"[, opts]))  o  (type('delim'[, opts]))
    mapped = re.sub(r'''\([a-z]+\(['"][^'"]*['"][^)]*\)\)\s*''', '', mapped)

    # Type casts con LONGITUD numerica: (string(40))x, (decimal(18,2))x, (integer(4))x
    # Ab Initio: (tipo(largo))expr  →  Spark: CAST(expr AS TIPO)
    # expr puede ser: un identificador, o una llamada a funcion (se toma el token siguiente).
    def _cast_num(m):
        tipo = m.group(1)
        args = m.group(2).strip()  # el (largo) o (precision,escala)
        target = m.group(3)
        if tipo == "decimal":
            # (decimal(18,2)) → DECIMAL(18,2); (decimal(18)) → DECIMAL(18,0)
            parts = [p.strip() for p in args.split(",") if p.strip()]
            if len(parts) == 2:
                spark_type = f"DECIMAL({parts[0]},{parts[1]})"
            elif len(parts) == 1:
                spark_type = f"DECIMAL({parts[0]},0)"
            else:
                spark_type = "DECIMAL(38,10)"
        else:
            spark_type = {
                "string": "STRING", "integer": "INT",
                "int": "INT", "long": "BIGINT", "double": "DOUBLE", "real": "DOUBLE",
            }.get(tipo, "STRING")
        return f'CAST({target} AS {spark_type})'

    # (tipo(numeros))seguido_de_identificador_o_funcion
    # Aplicar repetidamente por si hay varios.
    _cast_num_re = re.compile(r'\((string|decimal|integer|int|long|double|real)\(\s*([\d,\s]+)\)\)\s*([A-Za-z_]\w*(?:\([^()]*\))?)')
    prev = None
    while prev != mapped:
        prev = mapped
        mapped = _cast_num_re.sub(_cast_num, mapped)

    # Limpiar cualquier cast numerico remanente sin target claro: (string(40)) → nada
    mapped = re.sub(r'\((?:string|decimal|integer|int|long|double|real)\(\s*[\d,\s]+\)\)\s*', '', mapped)

    mapped = mapped.strip()

    # Notacion record.campo de Ab Initio (p.ej. fechad.FEC_INFO): tomamos el ultimo
    # segmento como nombre de columna. Solo si es un identificador punteado simple.
    if re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+', mapped):
        mapped = mapped.split('.')[-1]

    # If it was a date cast, wrap the remaining expression
    if has_date_cast and date_fmt and mapped and '(' not in mapped:
        mapped = f'to_date({mapped}, "{date_fmt}")'
    
    # Now apply standard function mappings
    mapped = _map_date_functions(mapped)
    mapped = _map_string_functions(mapped)
    
    # Ab Initio if(cond) val1 else val2 → CASE WHEN cond THEN val1 ELSE val2 END
    # Usa un parser con parentesis balanceados (la condicion puede tener funciones
    # anidadas como string_like(x, "% %") cuyo ) NO cierra el if).
    mapped = _translate_if_else(mapped)
    
    # Ab Initio ternary: expr ? val1 : val2 → CASE WHEN expr THEN val1 ELSE val2 END
    ternary = re.match(r'^(.+?)\s*\?\s*([^?:]+?)\s*:\s*([^?]+)$', mapped)
    if ternary and 'CASE' not in mapped:
        cond, then_val, else_val = ternary.group(1).strip(), ternary.group(2).strip(), ternary.group(3).strip()
        mapped = f'CASE WHEN {cond} THEN {then_val} ELSE {else_val} END'
    
    # Clean double spaces
    mapped = re.sub(r'\s+', ' ', mapped).strip()
    # Fix unbalanced parens
    if mapped.count('(') != mapped.count(')'):
        while mapped.endswith(')') and mapped.count(')') > mapped.count('('):
            mapped = mapped[:-1]
        while mapped.startswith('(') and mapped.count('(') > mapped.count(')'):
            mapped = mapped[1:]
    # Fechas tolerantes SIN try_to_date (no existe en Glue 4.0 / Spark 3.3):
    # to_date(campo, fmt) → to_date(nullif(trim(campo), ''), fmt)
    # nullif convierte "" en NULL, y to_date(NULL) = NULL sin romper. Es portable
    # a todas las versiones de Spark. Solo aplica cuando el 1er arg es un identificador.
    mapped = re.sub(
        r'\b(to_date|to_timestamp)\(\s*([A-Za-z_]\w*)\s*,',
        r'\1(nullif(trim(\2), ""),',
        mapped,
    )
    return mapped


def _build_transform(var_id, src_df, rule):
    # --- SORT ---
    sort_by = rule.get("sort_by")
    if sort_by:
        sort_cols = ", ".join(f'"{c}"' for c in sort_by)
        return f'{var_id}_df = {src_df}.orderBy({sort_cols})'
    
    # --- RAW DML TRANSFORM (complex reformat with Ab Initio DML) ---
    raw_transform = rule.get("raw_transform")
    if raw_transform and not rule.get("transform") == "lookup_join":
        lines = []
        lines.append(f'{var_id}_df = {src_df}')
        
        # Detect if this is a complex transform with loops/vectors (not simple field mapping)
        has_loops = 'for(' in raw_transform or 'for (' in raw_transform or 'while(' in raw_transform
        has_let_complex = raw_transform.count('let ') > 3
        has_vector_ops = 'vector_slice' in raw_transform or 'allocate()' in raw_transform
        
        if has_loops or has_vector_ops or has_let_complex:
            # Complex DML with procedural logic — generate TODO with key field extractions
            lines.append(f'# TODO: Complex DML transform with loops/vectors — requires manual Spark UDF translation')
            lines.append(f'# Original Ab Initio DML contains: {"loops" if has_loops else ""} {"vector ops" if has_vector_ops else ""} {"complex logic" if has_let_complex else ""}')
            
            # Still extract simple assignments that don't reference local variables
            field_assigns = re.findall(r'out\.(\w+)\s*::\s*([^;]+);', raw_transform)
            simple_assigns = []
            for field_name, expression in field_assigns:
                if field_name in ("newline", "*", "V_FILLER"):
                    continue
                expr_clean = expression.strip()
                # Skip vector assignments (contain [])
                if '[' in expr_clean and 'vector' in expr_clean.lower():
                    continue
                # Skip assignments referencing local let variables (RISK_SCORES, etc.)
                if re.match(r'^[A-Z_]+\[', expr_clean) or 'vector_slice' in expr_clean:
                    lines.append(f'# {field_name}: {expr_clean[:80]}  # → needs UDF')
                    continue
                # Simple field mappings (in.field, literals, basic functions)
                if re.match(r'^in\d*\.\*$', expr_clean) or expr_clean == 'in.*':
                    continue
                if re.match(r'^in\d*\.' + field_name + r'$', expr_clean):
                    continue
                # Apply mappings to simple expressions
                mapped = _translate_dml_expr(expr_clean)
                if mapped and len(mapped) < 150:
                    simple_assigns.append((field_name, mapped))
                else:
                    lines.append(f'# {field_name}: {expr_clean[:80]}  # → needs manual translation')
            
            for field_name, mapped in simple_assigns:
                mapped_escaped = mapped.replace('"', '\\"')
                lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", expr("{mapped_escaped}"))')
        else:
            # Simple DML — extract all field assignments
            field_assigns = re.findall(r'out\.(\w+)\s*::\s*([^;]+);', raw_transform)
            for field_name, expression in field_assigns:
                if field_name in ("newline", "*", "V_FILLER"):
                    continue
                expr_clean = expression.strip()
                if expr_clean == "in.*" or re.match(r'^in\d*\.\*$', expr_clean):
                    continue
                if re.match(r'^in\d*\.' + field_name + r'$', expr_clean):
                    continue
                mapped = _translate_dml_expr(expr_clean)
                mapped_escaped = mapped.replace('"', '\\"')
                if len(mapped_escaped) < 200:
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", expr("{mapped_escaped}"))')
                else:
                    lines.append(f'# TODO: Complex expression for {field_name}')
                    lines.append(f'# {expr_clean[:100]}...')
        
        if len(lines) == 1:
            lines.append(f'# Raw DML transform — review for manual translation:')
            lines.append(f'# {raw_transform[:150]}...')
        return "\n".join(lines)
    
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

    # Si el 'select' en realidad es DML crudo de Ab Initio (out::reformat(in)= begin...end;
    # o contiene out.FIELD ::), lo tratamos como raw_transform en vez de meterlo en
    # selectExpr (que generaria Python invalido).
    if select and select != "*" and (
        re.search(r'out\s*::\s*\w+\s*\(', select) or
        'begin' in select.lower() and '::' in select or
        re.search(r'out\.\w+\s*::', select)
    ):
        return _build_transform(var_id, src_df, {"raw_transform": select,
                                                 **{k: v for k, v in rule.items() if k != "select"}})

    # NOTE: Do NOT apply _map_date_functions/_map_string_functions to the full select
    # string here — it contains multiple comma-separated expressions and translating
    # them together corrupts expressions like (date("YYYY-MM-DD")) (string("|")) field.
    # Each expression is translated individually after splitting in the has_as branch.
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
                raw_expr, alias = m.group(1).strip(), m.group(2)
                # Apply DML→Spark translation
                translated = _translate_dml_expr(raw_expr)
                translated_escaped = translated.replace('"', '\\"')
                lines.append(f'{var_id}_df = {var_id}_df.withColumn("{alias}", expr("{translated_escaped}"))')
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
        if (node.type.upper() in ("TRANSFORM", "XFR") and len(node.children) > 1
            and not rule and ("reformat" in node.name.lower() or "rfmt" in node.name.lower())):
            needs_output_split = True

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
        f.write('    BASE_PATH = os.environ.get("BNX_BASE_PATH", "s3://datalake-bnx-scripts-dev")\n\n')
        f.write('print("[*] BNX PySpark Job Started")\n\n')
        
        # Emit helpers SIEMPRE: el pre-scan puede no detectar todos los patrones que
        # generan la llamada (hdr_trl_match / hdr_trl_if_match), y faltaria la def.
        # Son funciones pequenas; emitirlas siempre evita NameError.
        f.write("# =========================\n# HELPER FUNCTIONS\n# =========================\n\n")

        f.write("def filter_by_expression_hdr_trl(df, field, start, length, exclude_values):\n")
        f.write('    """Filter rows where substring(field, start, length) is NOT in exclude_values."""\n')
        f.write("    return df.filter(~F.substring(F.col(field), start, length).isin(exclude_values))\n\n\n")

        if True:
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
        
        f.write("def output_indexes_split(df, index_expr, num_outputs):\n")
        f.write('    """Split DataFrame into N outputs based on index expression."""\n')
        f.write('    return [df.filter(F.expr(f"{index_expr} = {i}")) for i in range(num_outputs)]\n\n\n')
        
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
                    path_resolved = rule.get("path_resolved") if rule else False
                    if path and path_resolved:
                        # Layout-derived path, prefix with PARAMS.BASE_PATH
                        if fmt == "csv":
                            f.write(f'{var_id}_df = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{{PARAMS.BASE_PATH}}/raw/{path}")\n')
                        elif fmt == "json":
                            f.write(f'{var_id}_df = spark.read.json(f"{{PARAMS.BASE_PATH}}/raw/{path}")\n')
                        else:
                            f.write(f'{var_id}_df = spark.read.parquet(f"{{PARAMS.BASE_PATH}}/raw/{path}")\n')
                    elif path:
                        # Explicit full path
                        if fmt == "csv":
                            f.write(f'{var_id}_df = spark.read.option("header", "true").option("inferSchema", "true").csv("{path}")\n')
                        elif fmt == "json":
                            f.write(f'{var_id}_df = spark.read.json("{path}")\n')
                        else:
                            f.write(f'{var_id}_df = spark.read.parquet("{path}")\n')
                    else:
                        if fmt == "csv":
                            f.write(f'{var_id}_df = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{{PARAMS.BASE_PATH}}/raw/{src_name}")\n')
                        elif fmt == "json":
                            f.write(f'{var_id}_df = spark.read.json(f"{{PARAMS.BASE_PATH}}/raw/{src_name}")\n')
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
                    # Detect multi-output Reformat
                    has_multi_output = (len(node.children) > 1 and
                                        not rule and
                                        ("reformat" in log_name.lower() or "rfmt" in log_name.lower()))
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
                    elif has_multi_output:
                        num_outputs = len(node.children)
                        f.write(f'# Multi-output Reformat (output_indexes): splits into {num_outputs} streams\n')
                        f.write(f'{var_id}_df = {src}  # el nodo en si (por si se referencia)\n')
                        f.write(f'_{var_id}_splits = output_indexes_split({var_id}_df, "output_port_index", {num_outputs})\n')
                        for idx, child_id in enumerate(node.children):
                            f.write(f'{child_id}_df = _{var_id}_splits[{idx}]  # port {idx}\n')
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
                    jk = rule.get("join_key", None) if rule else None
                    jt = rule.get("join_type", None) if rule else None
                    # Also check xfr_rules for this node
                    if not jk:
                        node_rule = xfr_rules.get(var_id.lower()) or xfr_rules.get(log_name.lower()) or {}
                        jk = node_rule.get("join_key", None)
                    if not jt:
                        node_rule = xfr_rules.get(var_id.lower()) or xfr_rules.get(log_name.lower()) or {}
                        jt = node_rule.get("join_type", "left")
                    
                    if not jk:
                        f.write(f'# ⚠️ WARNING: join key not found in .mp — sube el .xfr o revisa key={{}} en el MP\n')
                    
                    if jk and isinstance(jk, list):
                        keys_list = "[" + ", ".join(f'"{k}"' for k in jk) + "]"
                        f.write(f'{var_id}_df = {parents[0]}_df.join({parents[1]}_df, on={keys_list}, how="{jt}")\n')
                        for ep in parents[2:]:
                            f.write(f'{var_id}_df = {var_id}_df.join({ep}_df, on={keys_list}, how="{jt}")\n')
                    elif jk:
                        f.write(f'{var_id}_df = {parents[0]}_df.join({parents[1]}_df, on="{jk}", how="{jt}")\n')
                        for ep in parents[2:]:
                            f.write(f'{var_id}_df = {var_id}_df.join({ep}_df, on="{jk}", how="{jt}")\n')
                    else:
                        f.write(f'{var_id}_df = {parents[0]}_df.join({parents[1]}_df, on=["TODO_JOIN_KEY"], how="{jt}")  # TODO: specify join key\n')
                        for ep in parents[2:]:
                            f.write(f'{var_id}_df = {var_id}_df.join({ep}_df, on=["TODO_JOIN_KEY"], how="{jt}")\n')
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
                        path_resolved = rule.get("path_resolved") if rule else False
                        # Clean Ab Initio path expressions
                        if path:
                            path = re.sub(r'\$\[\(date\("YYYYMMDD"\)\)now\(\)\]', '{date_format(current_date(), "yyyyMMdd")}', path)
                            path = re.sub(r'\$FILE_DATE', '{PARAMS.FILE_DATE}', path)
                            path = re.sub(r'\$\{?(\w+)\}?', r'{\1}', path)
                        if path and path_resolved:
                            f.write(f'{src}.write.mode("{mode}").parquet(f"{{PARAMS.BASE_PATH}}/output/{path}")\n')
                        elif path:
                            f.write(f'{src}.write.mode("{mode}").parquet(f"{{PARAMS.BASE_PATH}}/output/{path}")\n')
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

    # --- GUARDARRAIL: comentar cualquier linea de DML crudo Ab Initio que se haya
    # colado sin traducir (out::reformat(in)=, out.X ::, begin/end;), para que el
    # codigo generado SIEMPRE sea Python valido. Es un cinturon de seguridad.
    _sanitize_generated_file(output_path)


def _sanitize_generated_file(output_path):
    """Post-proceso de seguridad: comenta lineas de DML crudo Ab Initio que hayan
    quedado sin traducir en el codigo generado, para garantizar Python valido.

    Detecta lineas que empiezan (ignorando indentacion) con patrones de DML nativo:
      out::reformat(in)=, out :: rollup(in)=, begin, end;, out.CAMPO :: ...
    y las convierte en comentarios. Preserva las lineas ya validas (asignaciones,
    withColumn, def, comentarios, etc.).
    """
    try:
        with open(output_path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return

    # Patrones de DML crudo Ab Initio que NO son Python valido
    dml_line = re.compile(
        r'^\s*('
        r'out\s*::\s*\w+\s*\('          # out::reformat(in)= , out :: rollup(in)=
        r'|out\.\w+\s*::'               # out.CAMPO :: expr
        r'|begin\s*$'                   # begin
        r'|end\s*;'                     # end;
        r'|let\s+\w+'                   # let VAR ... (declaracion DML)
        r'|:\s*\w+\s*\(int'             # tipos de retorno DML
        r')'
    )
    changed = False
    out = []
    for ln in lines:
        stripped = ln.rstrip("\n")
        # No tocar comentarios ni lineas ya validas
        if stripped.lstrip().startswith("#"):
            out.append(ln)
            continue
        if dml_line.match(stripped):
            indent = ln[:len(ln) - len(ln.lstrip())]
            out.append(f"{indent}# [BNX] DML crudo sin traducir (revisar): {stripped.strip()}\n")
            changed = True
        else:
            out.append(ln)

    if changed:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.writelines(out)
