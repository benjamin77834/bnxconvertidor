# src/codegen/spark_codegen.py
"""
Generates pure PySpark code (no Glue dependencies).
Same logic as glue_codegen but with SparkSession instead of GlueContext.
"""
import re
from datetime import datetime


def _unescape_gde(expr):
    """Des-escapa secuencias del formato serializado GDE de Ab Initio.

    En el .mp serializado los caracteres | y " se guardan escapados con
    backslash (\\| , \\") porque | es el separador de campos. Si no se
    limpian, el codigo generado contiene literales rotos como \\|\\|
    (SyntaxWarning en Python) o comillas escapadas de mas ( \\" ) que dejan
    cadenas SQL sin cerrar.
    """
    if not expr:
        return expr
    # \\  -> \   (primero, para no des-escapar de mas)
    expr = expr.replace('\\\\', '\x00')  # marcador temporal
    expr = expr.replace('\\|', '|')
    expr = expr.replace('\\"', '"')
    expr = expr.replace('\\{', '{').replace('\\}', '}')
    # Ab Initio tambien escapa parentesis y corchetes en el serializado GDE.
    # Si quedan como \( \) \[ \] rompen el SQL (SyntaxWarning "\)" invalido).
    expr = expr.replace('\\(', '(').replace('\\)', ')')
    expr = expr.replace('\\[', '[').replace('\\]', ']')
    expr = expr.replace('\x00', '\\')
    return expr


def _strip_dml_comments(expr):
    """Elimina comentarios de Ab Initio de una expresion DML.

    Soporta /* ... */ (bloque, posible multilinea) y // ... (hasta fin de linea).
    Respeta literales entre comillas simples/dobles para no borrar '//' o '/*'
    que sean parte de un string. Colapsa espacios resultantes.
    """
    if not expr or ('//' not in expr and '/*' not in expr):
        return expr
    out = []
    i = 0
    n = len(expr)
    quote = None
    while i < n:
        ch = expr[i]
        if quote:
            out.append(ch)
            if ch == quote and expr[i - 1:i] != '\\':
                quote = None
            i += 1
            continue
        if ch in ('"', "'"):
            quote = ch
            out.append(ch)
            i += 1
            continue
        # Comentario de bloque /* ... */
        if ch == '/' and expr[i + 1:i + 2] == '*':
            end = expr.find('*/', i + 2)
            if end == -1:
                i = n  # comentario sin cerrar: descartar el resto
            else:
                i = end + 2
            out.append(' ')
            continue
        # Comentario de linea // ... (hasta \n)
        if ch == '/' and expr[i + 1:i + 2] == '/':
            nl = expr.find('\n', i)
            if nl == -1:
                i = n
            else:
                i = nl
            out.append(' ')
            continue
        out.append(ch)
        i += 1
    result = ''.join(out)
    return re.sub(r'\s{2,}', ' ', result).strip()


_AGG_FUNCS = ("sum", "count", "avg", "mean", "min", "max", "stddev", "variance",
              "collect_list", "collect_set", "first", "last")


def _wrap_agg_for_withcolumn(expr):
    """Si la expresion es una funcion de agregacion de nivel superior, la envuelve
    en una ventana global OVER () para que sea valida dentro de un withColumn.

    En Ab Initio un reformat puede tener out.x :: sum(in.y) (agregacion global que
    replica el total en cada fila). En Spark, sum(y) dentro de withColumn sin GROUP BY
    lanza MISSING_GROUP_BY. sum(y) OVER () calcula el total global por fila y es valido.
    Solo aplica cuando TODA la expresion es una unica llamada de agregacion.
    """
    if not expr:
        return expr
    e = expr.strip()
    m = re.match(r'^(\w+)\s*\(', e)
    if not m or m.group(1).lower() not in _AGG_FUNCS:
        return expr
    # Verificar que la llamada abarca toda la expresion (parentesis balanceado al final).
    open_idx = e.index('(')
    depth = 0
    for i in range(open_idx, len(e)):
        if e[i] == '(':
            depth += 1
        elif e[i] == ')':
            depth -= 1
            if depth == 0:
                # Si el ')' de cierre es el ultimo caracter, es una agregacion pura.
                if i == len(e) - 1:
                    return f'{e} OVER ()'
                return expr  # hay algo mas despues (p.ej. sum(a)+sum(b)); no envolver
    return expr


def _is_untranslatable(mapped):
    """True si la expresion SQL traducida sigue conteniendo construcciones Ab Initio
    que NO son SQL de Spark valido y produciran un ParseException.

    Casos: switch(...)/case X:, lookup() sin resolver (requiere join externo),
    'first_defined' con lookup, y el patron malformado 'is_null.campo' que aparece
    cuando is_null(lookup(...).x) se traduce mal. En estos casos es mejor neutralizar
    la columna a lit(None) con un TODO que emitir un expr("...") que rompe el job.
    """
    if not mapped:
        return False
    low = mapped.lower()
    if 'switch' in low:                       # switch(x) case ...: (no existe en Spark SQL)
        return True
    if 'lookup(' in low:                      # lookup no resuelto (necesita join)
        return True
    if re.search(r'\bcase\s+\'', low):        # "case 'VAL' :" estilo Ab Initio (no CASE WHEN)
        return True
    if re.search(r'\bis_null\.', low):        # is_null.campo malformado
        return True
    if re.search(r'\b(is_defined|is_blank|is_valid)\.', low):
        return True
    if re.search(r'\bthen\s+end\b', low):     # CASE WHEN ... THEN END (rama vacia -> roto)
        return True
    return False


def _one_line(text, limit=200):
    """Colapsa un fragmento de texto a UNA sola linea segura para un comentario #.

    El DML crudo de Ab Initio suele tener saltos de linea; si se interpola tal cual
    en un comentario ('# {expr[:100]} ...'), el \\n parte el comentario y lo que sigue
    queda como codigo Python con indentacion -> IndentationError: unexpected indent.
    Aqui se reemplazan \\r\\n y \\t por espacios y se colapsan espacios multiples.
    """
    if text is None:
        return ""
    flat = re.sub(r'[\r\n\t]+', ' ', str(text))
    flat = re.sub(r'\s{2,}', ' ', flat).strip()
    if limit and len(flat) > limit:
        flat = flat[:limit]
    return flat


def _sql_arg(expr):
    """Prepara una expresion SQL para incrustarla en expr("...") de PySpark.

    En Spark SQL los literales de string y los formatos de fecha usan comillas
    SIMPLES. Cuando el traductor deja comillas dobles (p.ej. to_date(x, "yyyy-MM-dd")
    o nullif(trim(x), "")), al meterlas en expr("...") y escaparlas con \\" el
    string Python queda fragil y suele romperse ("unexpected character after line
    continuation"). Convertir esas comillas dobles a simples es semanticamente
    equivalente en SQL y produce codigo robusto: expr('...') sin escapes internos.

    Devuelve el contenido listo para ir dentro de expr("<aqui>") (con las comillas
    dobles ya normalizadas a simples; no requiere escape adicional).
    """
    if expr is None:
        return expr
    # 1) Comillas dobles -> simples (equivalente en SQL, evita escapes fragiles).
    out = expr.replace('"', "'")
    # 2) Barras invertidas residuales de Ab Initio (\n, \|, \t o un '\' colgante
    #    al final del where) rompen el literal Python que envuelve al where:
    #    ...where("divisas == '00' \")  -> la \ escapa la comilla de cierre y
    #    deja el string sin terminar (SyntaxError: unterminated string literal).
    #    En una expresion SQL de Spark esa barra no aporta nada, asi que la
    #    eliminamos por completo.
    out = out.replace("\\", "")
    # 3) Colapsar espacios sobrantes que pudieron quedar tras quitar la barra.
    out = re.sub(r"\s+", " ", out).strip()
    return out


def _normalize_logical_ops(expr):
    """Traduce operadores logicos Ab Initio (|| , &&) a Spark SQL (OR , AND).

    Se aplica sobre la expresion ya des-escapada. No toca | simples (bit-or)
    ni operadores dentro de literales de cadena.
    """
    if not expr:
        return expr
    # Reemplazo fuera de literales entre comillas simples/dobles.
    out = []
    i = 0
    quote = None
    n = len(expr)
    while i < n:
        ch = expr[i]
        if quote:
            out.append(ch)
            if ch == quote and expr[i - 1:i] != '\\':
                quote = None
            i += 1
            continue
        if ch in ('"', "'"):
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == '|' and expr[i + 1:i + 2] == '|':
            out.append(' OR ')
            i += 2
            continue
        if ch == '&' and expr[i + 1:i + 2] == '&':
            out.append(' AND ')
            i += 2
            continue
        out.append(ch)
        i += 1
    result = ''.join(out)
    return re.sub(r'\s{2,}', ' ', result).strip()


def _map_date_functions(expr):
    """Map Ab Initio date functions to Spark SQL equivalents."""
    if not expr:
        return expr
    # Ab Initio date casting: (date("YYYY-MM-DD"))field → to_date(field, "yyyy-MM-dd")
    # Pattern: (date("FORMAT"))expr or (date("FORMAT"))(type)expr
    expr = re.sub(
        r'\(date\("YYYY-MM-DD"\)\)\s*\(([^)]+)\)\s*(\w+)',
        r"to_date(cast(\2 as string), 'yyyy-MM-dd')",
        expr
    )
    expr = re.sub(
        r'\(date\("YYYY-MM-DD"\)\)\s*(\w+)',
        r"to_date(\1, 'yyyy-MM-dd')",
        expr
    )
    expr = re.sub(
        r'\(date\("YYYYMMDD"\)\)\s*(\w+)',
        r"date_format(\1, 'yyyyMMdd')",
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
    expr = re.sub(r'truncate_date\(([^,]+),\s*"MONTH"\)', r"trunc(\1, 'MM')", expr)
    expr = re.sub(r'truncate_date\(([^,]+),\s*"YEAR"\)', r"trunc(\1, 'yyyy')", expr)
    expr = re.sub(r'last_day_of_month\(', 'last_day(', expr)
    # Familia date_*of* de Ab Initio (extraen componentes de una fecha).
    # ORDEN: los mas especificos primero para no romper prefijos comunes.
    expr = re.sub(r'date_week_of_year\(', 'weekofyear(', expr)
    expr = re.sub(r'date_day_of_week\(', 'dayofweek(', expr)
    expr = re.sub(r'date_day_of_year\(', 'dayofyear(', expr)
    expr = re.sub(r'date_day_of_month\(', 'dayofmonth(', expr)
    expr = re.sub(r'date_month_of_year\(', 'month(', expr)
    # Componentes simples (despues de los compuestos)
    expr = re.sub(r'\bdate_year\(', 'year(', expr)
    expr = re.sub(r'\bdate_month\(', 'month(', expr)
    expr = re.sub(r'\bdate_day\(', 'dayofmonth(', expr)
    # $[(date("YYYYMMDD"))now()] → date_format(current_date(), 'yyyyMMdd')
    expr = re.sub(
        r'\$\[\(date\("YYYYMMDD"\)\)now\(\)\]',
        "date_format(current_date(), 'yyyyMMdd')",
        expr
    )
    return expr


def _split_last_arg(inner):
    """Separa 'str_expr, n' en (str_expr, n) por la ultima coma de nivel superior,
    respetando parentesis y comillas. Devuelve (head, last) o (inner, None)."""
    depth = 0
    quote = None
    last_comma = -1
    i = 0
    while i < len(inner):
        ch = inner[i]
        if quote:
            if ch == quote and (i == 0 or inner[i - 1] != '\\'):
                quote = None
        elif ch in ('"', "'"):
            quote = ch
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif ch == ',' and depth == 0:
            last_comma = i
        i += 1
    if last_comma == -1:
        return inner.strip(), None
    return inner[:last_comma].strip(), inner[last_comma + 1:].strip()


def _split_call_args(inner):
    """Divide los argumentos de una llamada por comas de NIVEL SUPERIOR,
    respetando parentesis y comillas. Devuelve lista de args (strings)."""
    args = []
    depth = 0
    quote = None
    buf = []
    i = 0
    while i < len(inner):
        ch = inner[i]
        if quote:
            buf.append(ch)
            if ch == quote and (i == 0 or inner[i - 1] != '\\'):
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            buf.append(ch)
        elif ch == '(':
            depth += 1
            buf.append(ch)
        elif ch == ')':
            depth -= 1
            buf.append(ch)
        elif ch == ',' and depth == 0:
            args.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
        i += 1
    if buf:
        args.append("".join(buf).strip())
    return args


def _rewrite_string_suffix(inner):
    """string_suffix(x, n) → substring(x, -n): ultimos n caracteres."""
    head, n = _split_last_arg(inner)
    if n is None:
        return f"string_suffix({inner})"  # dejar tal cual si no se puede parsear
    n = n.strip()
    # offset negativo = desde el final; si n ya trae signo, respetarlo
    neg = n if n.startswith('-') else f"-{n}"
    return f"substring({head}, {neg})"


def _rewrite_string_prefix(inner):
    """string_prefix(x, n) → substring(x, 1, n): primeros n caracteres."""
    head, n = _split_last_arg(inner)
    if n is None:
        return f"string_prefix({inner})"
    return f"substring({head}, 1, {n.strip()})"


def _rewrite_string_char(inner):
    """string_char(x, n) → substring(x, n, 1): caracter n-esimo."""
    head, n = _split_last_arg(inner)
    if n is None:
        return f"string_char({inner})"
    return f"substring({head}, {n.strip()}, 1)"


def _map_string_functions(expr):
    """Map Ab Initio string functions to Spark SQL equivalents."""
    if not expr:
        return expr
    # first_defined(a, b) → coalesce(a, b)
    expr = re.sub(r'first_defined\(', 'coalesce(', expr)
    # length_of(x): en Ab Initio es polimorfica (vectores -> nro elementos,
    # strings/escalares -> longitud). En estos grafos se usa para validar la
    # longitud de campos escalares (num_cuenta, etc.), por eso length(x) que
    # opera sobre STRING. size() SOLO acepta ARRAY/MAP y rompe con DATATYPE_MISMATCH.
    # Ademas envolvemos en cast(... as string) para tolerar argumentos numericos/decimal.
    expr = _replace_balanced_call(expr, "length_of", lambda inner: f"length(cast({inner} as string))")
    # decimal_strip(x) → cast(trim(cast(x as string)) as decimal(18,2))
    # Usar reemplazo balanceado para soportar argumentos anidados como
    # decimal_strip(first_defined(cve_par,'')) sin desbalancear parentesis.
    expr = _replace_balanced_call(
        expr, "decimal_strip",
        lambda inner: f"cast(trim(cast({inner} as string)) as decimal(18,2))",
    )
    # is_null(x) → (x IS NULL) — balanceado para soportar argumentos anidados
    # como is_null(lookup(...).campo) o is_null(coalesce(a,b)).
    expr = _replace_balanced_call(expr, "is_null", lambda inner: f"({inner} IS NULL)")
    # is_defined(x) → (x IS NOT NULL)
    expr = _replace_balanced_call(expr, "is_defined", lambda inner: f"({inner} IS NOT NULL)")
    # is_valid(x) → (x IS NOT NULL) — Ab Initio valida formato; en Spark aproximamos a no-null.
    # Debe ir ANTES de is_blank para no colisionar. Soporta parentesis anidados (CAST(...)).
    expr = _replace_balanced_call(expr, "is_valid", lambda inner: f"({inner} IS NOT NULL)")
    # is_blank(x) → (x IS NULL OR x = '')  (comillas SIMPLES para SQL)
    expr = _replace_balanced_call(expr, "is_blank", lambda inner: f"({inner} IS NULL OR {inner} = '')")
    # lookup_match(...) → true, lookup_count(...) → 1  (simplificado; el lookup real
    # se resolveria con un join a la tabla, que en la prueba local no existe).
    # Usamos reemplazo BALANCEADO porque los argumentos pueden tener parentesis
    # anidados (p.ej. lookup_match("t", string_lrtrim(campo))); un regex con [^)]*
    # cerraria en el ) interno y dejaria un ) huerfano -> ParseException.
    expr = _replace_balanced_call(expr, "lookup_match", lambda inner: "true")
    expr = _replace_balanced_call(expr, "lookup_count", lambda inner: "1")
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
    # string_suffix(x, n) → substring(x, -n)  (ultimos n caracteres)
    expr = _replace_balanced_call(expr, "string_suffix", _rewrite_string_suffix)
    # string_prefix(x, n) → substring(x, 1, n)  (primeros n caracteres)
    expr = _replace_balanced_call(expr, "string_prefix", _rewrite_string_prefix)
    # string_char(x, n) → substring(x, n, 1)  (caracter n-esimo)
    expr = _replace_balanced_call(expr, "string_char", _rewrite_string_char)
    # string_replace(x, old, new) → replace(x, old, new)
    expr = re.sub(r'string_replace\(', 'replace(', expr)
    # string_replace_first(x, old, new) → regexp_replace(x, old, new)
    expr = re.sub(r'string_replace_first\(', 'regexp_replace(', expr)
    # string_concat(a, b) → concat(a, b)
    expr = re.sub(r'string_concat\(', 'concat(', expr)
    # decimal_lpad(x, n[, c]) → lpad(CAST(x AS STRING), n, c)  (Ab Initio; c por defecto '0')
    def _rewrite_decimal_lpad(inner):
        args = _split_call_args(inner)
        if len(args) >= 3:
            return f"lpad(CAST({args[0]} AS STRING), {args[1].strip()}, {args[2].strip()})"
        if len(args) == 2:
            return f"lpad(CAST({args[0]} AS STRING), {args[1].strip()}, '0')"
        return f"CAST({inner} AS STRING)"
    expr = _replace_balanced_call(expr, "decimal_lpad", _rewrite_decimal_lpad)
    # decimal_strip(x) → CAST(x AS DECIMAL) (quita relleno; en la prueba basta el cast)
    expr = _replace_balanced_call(expr, "decimal_strip", lambda inner: f"CAST({inner} AS DECIMAL(18,2))")
    # datetime_add_months(d, n) → add_months(d, n)
    expr = re.sub(r'datetime_add_months\(', 'add_months(', expr)
    # string_lrepad(x, n, c) → lpad(x, n, c)  (pad izquierda, variante Ab Initio)
    expr = re.sub(r'string_lrepad\(', 'lpad(', expr)
    # string_rrepad(x, n, c) → rpad(x, n, c)  (pad derecha, variante)
    expr = re.sub(r'string_rrepad\(', 'rpad(', expr)
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
    # Operadores logicos Ab Initio → Spark SQL: && → AND, || → OR.
    # Spark SQL no acepta && ni ||. == y != si son validos en Spark, se dejan.
    expr = expr.replace('&&', ' AND ').replace('||', ' OR ')
    # Negacion unaria !expr → NOT (expr). Solo cuando ! NO forma parte de != .
    # (?<!...) evita tocar '!=' ; el ! debe ir seguido de un identificador/parentesis.
    expr = re.sub(r'!(?!=)\s*', ' NOT ', expr)
    # Limpiar espacios multiples que pudieron generarse
    expr = re.sub(r'\s{2,}', ' ', expr)
    # Strip "in." and "in0." prefix from field references (Ab Initio uses in.field)
    expr = re.sub(r'\bin\d*\.(\w+)', r'\1', expr)
    # Strip "_record_." prefix (evita INVALID_EXTRACT_BASE_FIELD_TYPE en Spark)
    expr = re.sub(r'\b_record_\.(\w+)', r'\1', expr)
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


def _abinitio_cast_to_spark(tipo, args, target):
    """Construye CAST(target AS TIPO) desde un cast Ab Initio (tipo(args))target."""
    if tipo == "decimal":
        # (decimal(18,2)) o (decimal(18.2)) → DECIMAL(18,2); (decimal(18)) → DECIMAL(18,0)
        parts = [p.strip() for p in re.split(r'[,.]', args) if p.strip()]
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


def translate_abinitio_casts(expr):
    """Traduce casts Ab Initio con longitud numerica remanentes: (tipo(N[,M]))x → CAST(x AS TIPO).

    Reutilizable como salvaguarda: aplica la misma logica que _translate_dml_expr
    sobre expresiones que pudieron haber quedado con el cast crudo Ab Initio
    (p.ej. substring((decimal(17,2))campo, 0, 17)). Balancea parentesis para
    soportar targets que son llamadas a funcion anidadas.
    """
    if not expr or '(' not in expr:
        return expr
    _cast_prefix_re = re.compile(
        r'\((string|decimal|integer|int|long|double|real)\(\s*([\d,.\s]+)\)\)\s*'
    )
    guard = 0
    while guard < 50:
        guard += 1
        m = _cast_prefix_re.search(expr)
        if not m:
            break
        tipo = m.group(1)
        args = m.group(2).strip()
        rest = expr[m.end():]
        tm = re.match(r'[A-Za-z_][\w.]*', rest)
        if not tm:
            # Sin target claro: eliminar el prefijo de cast y continuar
            expr = expr[:m.start()] + rest
            continue
        target = tm.group(0)
        after = rest[tm.end():]
        if after.startswith('('):
            close = _match_paren(after, 0)
            if close != -1:
                target = target + after[:close + 1]
                after = after[close + 1:]
        cast_sql = _abinitio_cast_to_spark(tipo, args, target)
        expr = expr[:m.start()] + cast_sql + after
    return expr


def _split_else(s):
    """Divide 'val1 else val2' respetando parentesis/comillas y anidamiento de if.
    Devuelve (then_part, else_part) o (s, None) si no hay else de nivel superior.

    Tambien respeta bloques CASE ... END ya construidos: un 'END' de nivel superior
    que cierra un CASE externo (no abierto dentro de 's') detiene la busqueda, para
    no 'consumir de mas' el else que pertenece al CASE externo, no al if actual.
    """
    depth = 0        # parentesis
    case_depth = 0   # niveles CASE...END abiertos DENTRO de s
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
            # Contar CASE ... END como palabras completas para no cruzarlos
            mc = re.match(r'\bCASE\b', s[i:], re.IGNORECASE)
            if mc:
                case_depth += 1
                i += mc.end()
                continue
            me = re.match(r'\bEND\b', s[i:], re.IGNORECASE)
            if me:
                if case_depth == 0:
                    # END de un CASE externo: aqui termina el alcance del if actual
                    return s[:i].strip(), None
                case_depth -= 1
                i += me.end()
                continue
            if case_depth == 0:
                # Buscar 'else' como palabra completa en nivel superior
                m = re.match(r'\belse\b', s[i:], re.IGNORECASE)
                if m:
                    return s[:i].strip(), s[i + m.end():].strip()
        i += 1
    return s.strip(), None


def _read_value(s, i):
    """Lee un 'valor' de expresion a partir de s[i] (nivel superior), deteniendose
    ante 'else' / 'END' de nivel superior o fin de string. Devuelve (valor, fin).
    Respeta parentesis, comillas y bloques CASE...END anidados."""
    n = len(s)
    # saltar espacios iniciales
    while i < n and s[i].isspace():
        i += 1
    start = i
    depth = 0
    case_depth = 0
    quote = None
    while i < n:
        ch = s[i]
        if quote:
            if ch == quote and s[i - 1] != '\\':
                quote = None
            i += 1
            continue
        if ch in ('"', "'"):
            quote = ch
            i += 1
            continue
        if ch == '(':
            depth += 1
            i += 1
            continue
        if ch == ')':
            if depth == 0:
                break  # ')' de un nivel externo
            depth -= 1
            i += 1
            continue
        if depth == 0:
            mc = re.match(r'\bCASE\b', s[i:], re.IGNORECASE)
            if mc:
                case_depth += 1
                i += mc.end()
                continue
            me = re.match(r'\bEND\b', s[i:], re.IGNORECASE)
            if me:
                if case_depth == 0:
                    break
                case_depth -= 1
                i += me.end()
                continue
            if case_depth == 0:
                # 'if' anidado como valor: leerlo completo via _if_span
                mi = re.match(r'\bif\s*\(', s[i:], re.IGNORECASE)
                if mi:
                    _, endpos = _if_span(s, i)
                    i = endpos
                    continue
                mel = re.match(r'\belse\b', s[i:], re.IGNORECASE)
                if mel:
                    break
        i += 1
    return s[start:i].strip(), i


def _if_span(s, start):
    """Dado s y la posicion 'start' de un 'if', traduce ese if completo a CASE WHEN
    y devuelve (case_sql, end_index) donde end_index es la posicion tras el if.
    Maneja if anidados en THEN y en ELSE. Devuelve (None, start) si no es un if."""
    m = re.match(r'if\s*\(', s[start:], re.IGNORECASE)
    if not m:
        return None, start
    open_idx = start + s[start:].index('(')
    close_idx = _match_paren(s, open_idx)
    if close_idx == -1:
        return None, start
    cond = s[open_idx + 1:close_idx].strip()

    # THEN: puede ser un if anidado o un valor simple
    i = close_idx + 1
    while i < len(s) and s[i].isspace():
        i += 1
    if re.match(r'\bif\s*\(', s[i:], re.IGNORECASE):
        then_sql, i = _if_span(s, i)
    else:
        then_sql, i = _read_value(s, i)

    # buscar 'else'
    while i < len(s) and s[i].isspace():
        i += 1
    mel = re.match(r'\belse\b', s[i:], re.IGNORECASE)
    if not mel:
        return f'CASE WHEN {cond} THEN {then_sql} END', i
    i += mel.end()
    while i < len(s) and s[i].isspace():
        i += 1
    if re.match(r'\bif\s*\(', s[i:], re.IGNORECASE):
        else_sql, i = _if_span(s, i)
    else:
        else_sql, i = _read_value(s, i)
    return f'CASE WHEN {cond} THEN {then_sql} ELSE {else_sql} END', i


def _translate_if_else(expr):
    """Convierte if(cond) then else else_val (posiblemente anidado, y aun cuando
    venga EMBEBIDO dentro de un CASE ya construido) a CASE WHEN ... END.

    Recorre el string, localiza cada 'if (' de nivel superior y lo reemplaza por
    su CASE calculando su alcance exacto con _if_span (que respeta parentesis,
    comillas, if anidados en THEN/ELSE y bloques CASE...END externos). Asi no se
    'consume de mas' el else/END que pertenece a un CASE externo.
    """
    if not expr:
        return expr
    result = expr
    guard = 0
    while guard < 100:
        guard += 1
        im = re.search(r'\bif\s*\(', result, re.IGNORECASE)
        if not im:
            break
        start = im.start()
        case_sql, end = _if_span(result, start)
        if case_sql is None or end <= start:
            break  # evitar bucle infinito
        result = result[:start] + case_sql + result[end:]

    # Normalizacion de residuos de sintaxis Ab Initio que quedan cuando el if venia
    # embebido en un CASE mal formado por una traduccion previa:
    #   "END else <val> END"  ->  "END ELSE <val> END"  (else Ab Initio crudo tras un END)
    #   "ENDelse"              ->  "END ELSE"            (pegado sin espacio)
    # El 'else' crudo que queda tras un 'END' es realmente el ELSE del CASE externo.
    result = re.sub(r'\bEND\s*else\b', 'END ELSE', result, flags=re.IGNORECASE)
    # Colapsar un ELSE duplicado accidental: "ELSE <v1> END ELSE <v2> END" al final
    # de un CASE externo cuando el THEN ya cerro su propio CASE. Se deja el ELSE
    # externo (el ultimo antes del END final) y se envuelve el THEN interno.
    return result


def _to_boolean_filter(expr):
    """Normaliza una expresion de FILTRO para que Spark la acepte en .where().

    Spark exige que el argumento de where() sea BOOLEANO. Los filtros de Ab Initio
    a menudo se traducen a expresiones NUMERICAS (p.ej. 'CASE WHEN cond THEN 1 ELSE
    0 END' de un if(cond) 1 else 0), lo que provoca FILTER_NOT_BOOLEAN.
    """
    if not expr:
        return expr
    e = expr.strip()
    m = re.match(
        r'^CASE\s+WHEN\s+(.+?)\s+THEN\s+(-?\d+(?:\.\d+)?)\s+ELSE\s+(-?\d+(?:\.\d+)?)\s+END$',
        e, re.IGNORECASE | re.DOTALL,
    )
    if m:
        cond, then_v, else_v = m.group(1), float(m.group(2)), float(m.group(3))
        if then_v != 0 and else_v == 0:
            return f'({cond})'
        if then_v == 0 and else_v != 0:
            return f'NOT ({cond})'
        return f'({e}) <> 0'
    if re.search(r'(>=|<=|<>|!=|==|=|>|<)\b|\bIS\s+(NOT\s+)?NULL\b|\b(AND|OR|NOT)\b|\bLIKE\b|\bIN\s*\(|\bRLIKE\b|\bBETWEEN\b',
                 e, re.IGNORECASE):
        return e
    return f'({e}) <> 0'


def _translate_dml_expr(expr_clean):
    """Translate a single Ab Initio DML expression to Spark SQL."""
    mapped = expr_clean
    # Des-escapar formato serializado GDE y normalizar operadores logicos
    # antes de cualquier otra transformacion (evita \|\| y comillas rotas).
    mapped = _unescape_gde(mapped)
    # Quitar comentarios Ab Initio antes de cualquier traduccion. El DML usa
    # // (hasta fin de linea) y /* ... */. Si no se quitan, una asignacion
    # comentada como "out.x :: //in.cve_obm;" produce expr("//cve_obm") -> ParseException.
    mapped = _strip_dml_comments(mapped)
    mapped = _normalize_logical_ops(mapped)
    # Clean up Ab Initio syntax FIRST (before function mapping)
    mapped = re.sub(r'\bin\d*\.', '', mapped)   # remove in./in0./in1. prefix
    mapped = re.sub(r'\bout\.', '', mapped)     # remove out. prefix
    # remove _record_. prefix (Ab Initio referencia campos del registro con
    # _record_.CAMPO; en Spark es la columna directa. Sin quitarlo, Spark intenta
    # extraer un subcampo de una columna no-struct -> INVALID_EXTRACT_BASE_FIELD_TYPE).
    mapped = re.sub(r'\b_record_\.', '', mapped)
    # Variables/parametros Ab Initio: $VAR o ${VAR}. Dentro de una expresion se
    # refieren a un campo/parametro; quitamos el $ para que sea un identificador
    # valido en Spark SQL (evita "Syntax error at or near '$'").
    # NOTA: $[...] (expresion inline con corchetes) se maneja aparte mas abajo.
    mapped = re.sub(r'\$\{(\w+)\}', r'\1', mapped)
    mapped = re.sub(r'\$(?![\[\{])(\w+)', r'\1', mapped)
    # Remove :N: (priority operator in Ab Initio: :0: :1: :2: ...)
    mapped = re.sub(r'\s*:\d+:\s*', ' ', mapped)
    
    # Handle Ab Initio type casting patterns BEFORE function mapping:
    # Pattern: (date("FORMAT"))(string("delim"))field → to_date(cast(field as string), "spark_fmt")
    # Pattern: (date("YYYY-MM-DD"))field → to_date(field, "yyyy-MM-dd")
    # Pattern: (string("|"))field → cast(field as string)
    # Strategy: remove ALL type cast prefixes, then wrap result appropriately
    
    # Forma anidada Ab Initio rara que puede llegar cuando el valor ya viene
    # resuelto (p.ej. $V_MISDATE -> '2024-12-12') con un delimitador \x01 de por
    # medio: "(date('YYYY-MM-DD')(\"\\x01\"))('2024-12-12')" o variantes.
    # La normalizamos: extraemos el formato date(...) y el ULTIMO literal entre
    # comillas (el valor) y producimos to_date(valor, fmt). Cubre el caso donde
    # la sintaxis no encaja en el patron estandar (date("FMT"))campo.
    _weird_date = re.search(
        r'''\(?\s*date\(\s*['"]([^'"]+)['"]\s*\)'''      # date('FMT')
        r'''(?:\s*\(\s*"[^"]*"\s*\))?'''                  # opcional (\"\x01\")
        r'''\s*\)?\s*'''
        r'''\(\s*(['"])([^'"]*)\2\s*\)''',                # (VALOR)
        mapped,
    )
    if _weird_date:
        fmt = _weird_date.group(1).replace("YYYY", "yyyy").replace("DD", "dd")
        valor = _weird_date.group(3)
        replacement = f"to_date('{valor}', '{fmt}')"
        mapped = mapped[:_weird_date.start()] + replacement + mapped[_weird_date.end():]
        # limpiar parentesis externos sobrantes que envolvian toda la expresion
        mapped = mapped.strip()
        while mapped.startswith('(') and mapped.endswith(')') and mapped.count('(') > mapped.count('to_date('):
            inner = mapped[1:-1].strip()
            if inner.count('(') == inner.count(')'):
                mapped = inner
            else:
                break

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
            # (decimal(18,2)) o (decimal(18.2)) → DECIMAL(18,2); (decimal(18)) → DECIMAL(18,0)
            # Ab Initio usa coma O punto como separador precision/escala.
            parts = [p.strip() for p in re.split(r'[,.]', args) if p.strip()]
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

    # (tipo(numeros))seguido_de_identificador_o_funcion (incluye llamadas con
    # parentesis ANIDADOS, p.ej. (string(10))string_prefix(trim(x),10)).
    # Detectamos el prefijo de cast y luego tomamos el target balanceando parentesis.
    _cast_prefix_re = re.compile(r'\((string|decimal|integer|int|long|double|real)\(\s*([\d,.\s]+)\)\)\s*')
    guard = 0
    while guard < 50:
        guard += 1
        m = _cast_prefix_re.search(mapped)
        if not m:
            break
        tipo = m.group(1)
        args = m.group(2).strip()
        rest = mapped[m.end():]
        # Tomar el identificador/llamada que sigue, balanceando parentesis anidados
        tm = re.match(r'[A-Za-z_][\w.]*', rest)
        if not tm:
            # No hay target claro: eliminar el prefijo de cast y seguir
            mapped = mapped[:m.start()] + rest
            continue
        target = tm.group(0)
        after = rest[tm.end():]
        # Si es una llamada de funcion, capturar los argumentos balanceados
        if after.startswith('('):
            close = _match_paren(after, 0)
            if close != -1:
                target = target + after[:close + 1]
                after = after[close + 1:]
        # Construir el CAST usando la logica de _cast_num sobre 'target'
        class _M:
            def group(self, i):
                return [None, tipo, args, target][i]
        cast_sql = _cast_num(_M())
        mapped = mapped[:m.start()] + cast_sql + after

    # Limpiar cualquier cast numerico remanente sin target claro: (string(40)) → nada
    mapped = re.sub(r'\((?:string|decimal|integer|int|long|double|real)\(\s*[\d,.\s]+\)\)\s*', '', mapped)

    mapped = mapped.strip()

    # Notacion record.campo de Ab Initio (p.ej. fechad.FEC_INFO): tomamos el ultimo
    # segmento como nombre de columna. Solo si es un identificador punteado simple.
    if re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+', mapped):
        mapped = mapped.split('.')[-1]

    # If it was a date cast, wrap the remaining expression
    if has_date_cast and date_fmt and mapped and '(' not in mapped:
        mapped = f"to_date({mapped}, '{date_fmt}')"
    
    # Now apply standard function mappings
    mapped = _map_date_functions(mapped)
    mapped = _map_string_functions(mapped)

    # Spark no acepta "NOT x IS [NOT] NULL" sin parentesis (viene de !is_valid /
    # !is_defined -> NOT x IS NOT NULL). Envolver el operando: NOT (x IS [NOT] NULL).
    mapped = re.sub(
        r'\bNOT\s+([A-Za-z_][\w.]*)\s+IS\s+(NOT\s+)?NULL',
        lambda m: f'NOT ({m.group(1)} IS {m.group(2) or ""}NULL)',
        mapped,
        flags=re.IGNORECASE,
    )

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
        r"\1(nullif(trim(\2), ''),",
        mapped,
    )
    # Salvaguarda final: si quedo algun cast Ab Initio crudo (tipo(N))x sin resolver
    # (p.ej. anidado en argumentos de substring/lpad), traducirlo a CAST(...).
    mapped = translate_abinitio_casts(mapped)
    return mapped


def _build_transform(var_id, src_df, rule):
    # --- SORT ---
    sort_by = rule.get("sort_by")
    if sort_by:
        sort_cols = ", ".join(f'"{c}"' for c in sort_by)
        return f'{var_id}_df = {src_df}.orderBy({sort_cols})'
    
    # --- DML FIELDS (parsed from external .xfr with Ab Initio DML) ---
    # Sin esta rama, un rule con dml_fields caia en selectExpr("*") y se perdian
    # los campos derivados. Emitimos un withColumn por campo, saneando casts Ab Initio.
    dml_fields = rule.get("dml_fields")
    if dml_fields:
        lines = [f'{var_id}_df = {src_df}']
        for fld in dml_fields:
            fname = fld["field"]
            expr_val = translate_abinitio_casts(fld["expr"])
            lines.append(f'{var_id}_df = {var_id}_df.withColumn("{fname}", {expr_val})')
        where = rule.get("where")
        if where:
            where = _map_date_functions(where)
            where = _map_string_functions(where)
            where = translate_abinitio_casts(where)
            where = _to_boolean_filter(where)
            where_escaped = _sql_arg(where)
            lines.append(f'{var_id}_df = {var_id}_df.where("{where_escaped}")')
        return "\n".join(lines)

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
            field_assigns = re.findall(r'out\.(\w+)\s*:(?:\d+)?:\s*([^;]+);', raw_transform)
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
                    lines.append(f'# {field_name}: {_one_line(expr_clean, 80)}  # → needs UDF')
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
                    lines.append(f'# {field_name}: {_one_line(expr_clean, 80)}  # → needs manual translation')
            
            for field_name, mapped in simple_assigns:
                if _is_untranslatable(mapped):
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", lit(None))  # TODO: Ab Initio no traducible (lookup/switch/case): {_one_line(mapped, 80)}')
                    continue
                mapped = _wrap_agg_for_withcolumn(mapped)
                mapped_escaped = _sql_arg(mapped)
                lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", expr("{mapped_escaped}"))')
        else:
            # Simple DML — extract all field assignments
            field_assigns = re.findall(r'out\.(\w+)\s*:(?:\d+)?:\s*([^;]+);', raw_transform)
            for field_name, expression in field_assigns:
                if field_name in ("newline", "*", "V_FILLER"):
                    continue
                expr_clean = expression.strip()
                if expr_clean == "in.*" or re.match(r'^in\d*\.\*$', expr_clean):
                    continue
                if re.match(r'^in\d*\.' + field_name + r'$', expr_clean):
                    continue
                mapped = _translate_dml_expr(expr_clean)
                # Expresion vacia o no traducible a algo util (p.ej. "..." de un
                # raw reformat): comentar en vez de emitir expr("...") invalido.
                if not mapped or mapped.strip() in ("", "...", "."):
                    lines.append(f'# {field_name}: expresion vacia/no traducible — omitida')
                    continue
                # Construcciones Ab Initio no soportadas en Spark SQL (lookup/switch/
                # case/is_null.campo): neutralizar a lit(None) en vez de romper el job.
                if _is_untranslatable(mapped):
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", lit(None))  # TODO: Ab Initio no traducible (lookup/switch/case): {_one_line(expr_clean, 80)}')
                    continue
                mapped = _wrap_agg_for_withcolumn(mapped)
                mapped_escaped = _sql_arg(mapped)
                if len(mapped_escaped) < 200:
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", expr("{mapped_escaped}"))')
                else:
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{field_name}", lit(None))  # TODO: expresion compleja (truncada): {_one_line(expr_clean, 100)}')
        
        if len(lines) == 1:
            lines.append(f'# Raw DML transform — review for manual translation:')
            lines.append(f'# {_one_line(raw_transform, 150)}...')
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
        re.search(r'out\.\w+\s*:(?:\d+)?:', select)
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
        group_set = set(group_by)
        agg_exprs = []
        for col in select.split(","):
            col = col.strip()
            m = re.match(r"(\w+)\((\w+)\)\s+as\s+(\w+)", col, re.I)
            if m:
                # Agregacion explicita: sum(x) as y -> sum("x").alias("y")
                fn, field, alias = m.group(1).lower(), m.group(2), m.group(3)
                agg_exprs.append(f'{fn}("{field}").alias("{alias}")')
                continue
            # Columnas no agregadas dentro de un Rollup:
            #  - "*" o vacio: no se puede meter en .agg() -> se omite
            #  - clave del group_by: ya esta en groupBy() -> se omite del agg
            #  - cualquier otra: se envuelve en first(...) (valor representativo
            #    del grupo). Spark exige que toda columna fuera del GROUP BY este
            #    agregada; usar col("x") crudo provoca MISSING_AGGREGATION.
            if col in ("", "*") or col in group_set:
                continue
            agg_exprs.append(f'first("{col}").alias("{col}")')
        if not agg_exprs:
            # Sin ninguna expresion agregable: Rollup se reduce a un conteo por grupo.
            agg_exprs.append('count("*").alias("count")')
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
                # Expresion vacia (p.ej. asignacion comentada //...): omitir el campo.
                if not translated or translated.strip() in ("", "...", "."):
                    lines.append(f'# {alias}: expresion vacia/comentada — omitida')
                    continue
                if _is_untranslatable(translated):
                    lines.append(f'{var_id}_df = {var_id}_df.withColumn("{alias}", lit(None))  # TODO: Ab Initio no traducible (lookup/switch/case): {_one_line(raw_expr, 80)}')
                    continue
                translated = _wrap_agg_for_withcolumn(translated)
                translated_escaped = _sql_arg(translated)
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


def generate_spark(dag, output_path, xfr_rules=None, pset_params=None):
    xfr_rules = xfr_rules or {}
    pset_params = pset_params or {}

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

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f'"""\n[*] BNX V54 GENERATED PYSPARK JOB\n? Generated at: {datetime.now()}\n"""\n\n')
        f.write("import os\n")
        f.write("from pyspark.sql import SparkSession\n")
        f.write("from pyspark.sql.functions import *\n")
        f.write("from pyspark.sql import functions as F\n")
        f.write("from pyspark.sql.window import Window\n\n")
        f.write('spark = SparkSession.builder.appName("BNX_Pipeline").getOrCreate()\n\n')
        f.write('# =========================\n# PARAMETERS\n# =========================\n')
        f.write('class PARAMS:\n')
        f.write('    BASE_PATH = os.environ.get("BNX_BASE_PATH", "s3://datalake-bnx-scripts-dev")\n')
        # Parametros del .pset: cada uno resoluble por variable de entorno, con el
        # valor del pset como default. Asi PARAMS.V_MF_FILE_NAME etc. resuelven al
        # valor real en vez de caer al placeholder BNX_PARAM_<VAR>.
        _emit_pset_params(f, pset_params)
        f.write('\n')
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
                if path:  # quitar backslashes de escape Ab Initio ($\{VAR\} -> ${VAR})
                    path = path.replace("\\{", "{").replace("\\}", "}").replace("\\$", "$")
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
                        raw_cmd = raw_cmd.replace("\\{", "{").replace("\\}", "}").replace("\\$", "$")
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
                        raw_cmd = raw_cmd.replace("\\{", "{").replace("\\}", "}").replace("\\$", "$")
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
                            # _translate_dml_expr traduce ademas casts numericos
                            # (decimal(N))x -> CAST(x AS DECIMAL(N)), if/else, etc.
                            mapped = _translate_dml_expr(where)
                            mapped = re.sub(r"is_blank\((\w+)\)", r"\1 IS NULL OR \1 = ''", mapped)
                            mapped = re.sub(r'is_defined\((\w+)\)', r'\1 IS NOT NULL', mapped)
                            mapped = _to_boolean_filter(mapped)
                            mapped_escaped = _sql_arg(mapped)
                            f.write(f'{var_id}_df = {src}.where("{mapped_escaped}")\n')
                            f.write(f'{var_id}_reject_df = {src}.where("NOT ({mapped_escaped})")\n')
                        else:
                            where_mapped = _translate_dml_expr(where)
                            where_mapped = _to_boolean_filter(where_mapped)
                            where_escaped = _sql_arg(where_mapped)
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
                    # Exponer el SINK con su propio nombre de variable. Necesario
                    # cuando el SINK es tambien un lookup/dataset consumido por otro
                    # nodo (p.ej. 'Connections_Lkp' referenciado como
                    # connections_lkp_df en un join posterior). Sin este alias, el
                    # consumidor no encuentra el DataFrame y el join queda vacio.
                    # Emitimos tambien el alias en minusculas porque el codegen del
                    # lookup_join referencia el nombre normalizado (connections_lkp_df).
                    if var_id != parents[0]:
                        f.write(f'{var_id}_df = {src}\n')
                    if var_id.lower() != var_id and var_id.lower() != parents[0].lower():
                        f.write(f'{var_id.lower()}_df = {src}\n')
                    sink_type = rule.get("sink_type", "s3") if rule else "s3"
                    path = rule.get("path") if rule else None
                    fmt = rule.get("format", "parquet") if rule else "parquet"
                    topic = rule.get("topic") if rule else None
                    table = rule.get("table") if rule else None
                    conn = rule.get("connection") if rule else None
                    mode = rule.get("mode", "overwrite") if rule else "overwrite"
                    path_resolved = rule.get("path_resolved") if rule else False

                    # quitar backslashes de escape Ab Initio ($\{VAR\} -> ${VAR})
                    if path:
                        path = path.replace("\\{", "{").replace("\\}", "}").replace("\\$", "$")

                    if sink_type == "kafka" and topic:
                        f.write(f'{src}.selectExpr("to_json(struct(*)) AS value").write.format("kafka")')
                        f.write(f'.option("kafka.bootstrap.servers", "{conn or "localhost:9092"}")')
                        f.write(f'.option("topic", "{topic}").save()\n')
                    elif sink_type == "jdbc" and (table or conn):
                        f.write(f'{src}.write.format("jdbc").mode("{mode}")')
                        f.write(f'.option("url", "{conn or "jdbc:mysql://localhost:3306/db"}")')
                        f.write(f'.option("dbtable", "{table or var_id.lower()}").save()\n')
                    else:
                        # Clean Ab Initio path expressions
                        if path:
                            path = re.sub(r'\$\[\(date\("YYYYMMDD"\)\)now\(\)\]', '{date_format(current_date(), "yyyyMMdd")}', path)
                            path = re.sub(r'\$FILE_DATE', '{PARAMS.FILE_DATE}', path)
                            path = re.sub(r'\$\{?(\w+)\}?', r'{PARAMS.\1}', path)
                        if path:
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


def _emit_pset_params(f, pset_params):
    """Emite los parametros del .pset como atributos de la clase PARAMS.

    Cada parametro se escribe como:
        VAR = os.environ.get("VAR", "<valor del pset>")
    de modo que en AWS/Glue se puede sobreescribir por variable de entorno, pero
    por defecto usa el valor real del pset (no el placeholder BNX_PARAM_<VAR>).

    Se omiten:
      - claves que no son identificadores Python validos
      - BASE_PATH (ya emitido)
      - valores PDL Ab Initio ($[...]) que no son literales resolubles
    """
    import re as _re
    if not pset_params:
        return
    ident = _re.compile(r'^[A-Za-z_]\w*$')
    for k, v in pset_params.items():
        if not k or not ident.match(k):
            continue
        if k == "BASE_PATH":
            continue
        val = "" if v is None else str(v).strip()
        # Valores marcador que NO son un valor real: dejar resoluble por entorno.
        if val in ("", "NOT SET", "NOTSET", "None", "null"):
            f.write(f'    {k} = os.environ.get("{k}", "")\n')
            continue
        # PDL sin resolver ($[...]): dejar como comentario para referencia + default vacio.
        if val.startswith("$["):
            f.write(f'    # {k} = {val!r}  # PDL Ab Initio (no resuelto)\n')
            f.write(f'    {k} = os.environ.get("{k}", "")\n')
            continue
        f.write(f'    {k} = os.environ.get("{k}", {val!r})\n')


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
        r'//'                           # comentario de Ab Initio (// ...)
        r'|out\s*::\s*\w+\s*\('         # out::reformat(in)= , out :: rollup(in)=
        r'|out\.\*\s*::'                # out.* :: in.* (passthrough de todas las columnas)
        r'|out\.\w+\s*:(?:\d+)?:'       # out.CAMPO :: expr  y  out.CAMPO :N: expr (prioridad)
        r'|begin\s*$'                   # begin
        r'|end\s*;'                     # end;
        r'|end\s*$'                     # end (sin ;)
        r'|let\s+\w+'                   # let VAR ... (declaracion DML)
        r'|:\s*\w+\s*\(int'             # tipos de retorno DML
        r'|include\s+["\']'             # include "..."; (inclusion de DML)
        r'|type\s+\w+\s*='              # type NAME = ... (definicion de tipo DML)
        r'|record\b'                    # record ... end; (definicion de registro)
        r'|metadata\b'                  # metadata ...
        r'|(?:decimal|integer|string|date|datetime|void|char|real|double|long)'
        r'\s*(?:\([^)]*\))?\s+\w+\s*;'  # decl. de campo DML: "decimal x;" / "string(10) y;"
        r')'
    )
    # Linea huerfana residual de un comentario partido por un \n (p.ej. el segundo
    # tramo de "# {expr[:100]} (truncado)" cuando expr tenia salto de linea). Queda
    # como texto indentado sin '#' -> IndentationError. La reconocemos y comentamos.
    orphan_line = re.compile(r'^\s+\S.*\(truncado\)\s*$|^\s+\S.*\.\.\.\s*$')
    changed = False
    out = []
    for ln in lines:
        stripped = ln.rstrip("\n")
        # No tocar comentarios ni lineas ya validas
        if stripped.lstrip().startswith("#"):
            out.append(ln)
            continue
        if orphan_line.match(stripped):
            out.append(f"# [BNX] fragmento de comentario huerfano neutralizado: {stripped.strip()}\n")
            changed = True
            continue
        if dml_line.match(stripped):
            indent = ln[:len(ln) - len(ln.lstrip())]
            out.append(f"{indent}# [BNX] DML crudo sin traducir (revisar): {stripped.strip()}\n")
            changed = True
            continue
        out.append(ln)

    if changed:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.writelines(out)
