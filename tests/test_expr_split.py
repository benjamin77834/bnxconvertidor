# tests/test_expr_split.py
# Regresion: division de reglas 'expr as campo' por comas de NIVEL SUPERIOR,
# decimal_lrepad/decimal_rpad, if/else anidado y guardarrail de SQL truncado.
# (Bug benja1/Fuse: expr("3) else 0") -> ParseException en runtime.)
import re

from src.codegen.spark_codegen import (
    _build_transform,
    _guard_invalid_sql,
    _split_call_args,
    _sql_syntax_problem,
    _translate_dml_expr,
    _wrap_reformat_safe_col,
)

RULE_LREPAD = (
    "if (is_defined(in1.dprin01.num_contrato)) "
    "decimal_lpad(in1.dprin01.num_contrato,12)+"
    "decimal_lrepad(decimal_strip(in1.dprin01.num_folio),3) else 0"
)


def test_split_call_args_respeta_parentesis_comillas_y_llaves():
    assert _split_call_args("a as x, f(b, 3) as y, 'c,d' as z") == ["a as x", "f(b, 3) as y", "'c,d' as z"]
    assert _split_call_args("g(h(1,2),3), $\\{P,Q\\}, [a,b]") == ["g(h(1,2),3)", "$\\{P,Q\\}", "[a,b]"]


def test_select_con_comas_en_llamadas_no_deja_fragmentos():
    select = f"{RULE_LREPAD} as key_decrypt, in0.flag as otro"
    code = _build_transform("Fuse", "Src_df", {"select": select})
    assert '"3) else 0"' not in code
    assert 'withColumn("key_decrypt"' in code
    # una sola columna key_decrypt, completa y balanceada
    sqls = re.findall(r'withColumn\("key_decrypt", expr\("(.*)"\)\)', code)
    assert len(sqls) == 1
    assert sqls[0].count("(") == sqls[0].count(")")
    assert _sql_syntax_problem(sqls[0]) is None


def test_decimal_lrepad_y_variantes():
    out = _translate_dml_expr("decimal_lrepad(decimal_strip(in.num_folio),3)")
    assert "decimal_lrepad" not in out
    assert out.startswith("lpad(CAST(")
    assert out.endswith(", 3, '0')")
    assert _translate_dml_expr("decimal_lrepad(in.x, 5, '*')") == "lpad(CAST(x AS STRING), 5, '*')"
    assert _translate_dml_expr("decimal_rpad(in.x, 5)") == "rpad(CAST(x AS STRING), 5, '0')"
    assert _translate_dml_expr("decimal_lpad(in.x, 5)") == "lpad(CAST(x AS STRING), 5, '0')"


def test_if_else_con_is_defined_y_columnas_con_punto():
    out = _translate_dml_expr(RULE_LREPAD)
    assert out.startswith("CASE WHEN (dprin01_num_contrato IS NOT NULL) THEN ")
    assert out.endswith(" ELSE 0 END")
    assert "decimal_lrepad" not in out
    assert _sql_syntax_problem(out) is None


def test_if_else_anidado():
    out = _translate_dml_expr("if (a == 1) 'x' else if (a == 2) 'y' else 'z'")
    assert out.count("CASE") == out.count("END") >= 2
    assert _sql_syntax_problem(out) is None


def test_regla_comentada_no_genera_columna():
    raw = (
        "out::fuse(in0,in1)=\nbegin\n"
        "  //out.k :: if (is_defined(in1.a)) f(in1.a,12)+g(in1.b,3) else 0;\n"
        "  out.k :: if (is_defined(in1.a)) 7 else 0;\n"
        "end;"
    )
    code = _build_transform("Fuse", "Src_df", {"raw_transform": raw})
    assert code.count('withColumn("k"') == 1
    assert "3) else 0" not in code


def test_reglas_multiples_mismo_campo_se_combinan_en_coalesce():
    select = "in.a as k, in.b as k"
    code = _build_transform("T", "S_df", {"select": select})
    assert code.count('withColumn("k"') == 1
    assert "coalesce(" in code


def test_sql_syntax_problem_detecta_truncados():
    for bad in ("3) else 0", ")x", ", a", "else 0", "then 1", "end", "a +", "a AND", "f((a)", "a = 'x",
                "CASE WHEN a THEN 1", "x)"):
        assert _sql_syntax_problem(bad), bad
    for ok in ("a + 1", "CASE WHEN a THEN 1 ELSE 0 END", "count(*)", "'a,b(' || x", "*",
               "cast(trim(cast(x as string)) as decimal(18,2))", "x IS NOT NULL"):
        assert _sql_syntax_problem(ok) is None, ok


def test_guardarrail_expr_truncada_a_lit_none():
    lines = [
        'A_df = A_df.withColumn("k", expr("3) else 0"))\n',
        'A_df = A_df.withColumn("ok", expr("x + 1"))\n',
        'A_df = _bnx_safe_col(A_df, "j", "field) else 0")\n',
        'A_df = A_df.where("a = 1 AND")\n',
    ]
    out = "".join(_guard_invalid_sql(lines))
    assert 'withColumn("k", lit(None))  # [BNX] expresion truncada/invalida (3) else 0): revisar' in out
    assert 'print("[!] BNX: expresion truncada/invalida omitida' in out
    assert 'expr("x + 1")' in out                       # la valida queda intacta
    assert 'A_df = A_df.withColumn("j", lit(None))' in out
    assert 'A_df.where("true")' in out
    compile(out, "<guard>", "exec")                      # sigue siendo Python valido


def test_wrap_reformat_safe_col_tambien_neutraliza_invalidas():
    lines = ['A_df = A_df.withColumn("k", expr("field) else 0"))\n']
    out = "".join(_wrap_reformat_safe_col(lines))
    assert "_bnx_safe_col" not in out
    assert 'withColumn("k", lit(None))' in out and "[BNX]" in out
    compile(out, "<wrap>", "exec")
