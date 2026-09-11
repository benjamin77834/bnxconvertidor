# tests/test_regression_fixes.py
# Tests de regresion para los fixes de fidelidad/robustez del convertidor
# Ab Initio -> PySpark/Glue. Cada test blinda un bug concreto ya corregido.
import re
import pytest

from src.xfr_parser import parse_xfr
from src.codegen.spark_codegen import (
    _translate_dml_expr,
    _to_boolean_filter,
    _map_string_functions,
    _map_date_functions,
    _emit_join_body_columns,
    _safe_path_fragment,
    _safe_dbtable,
    _extract_local_vars,
)
from src.codegen.glue_codegen import _to_boolean_filter as glue_to_boolean_filter
from src.dag.builder import build_dag


# ---------------------------------------------------------------------------
# BUG 2 — Rollup: keys separadas por ';' dentro de llaves {a; b}
# ---------------------------------------------------------------------------
def test_rollup_group_by_multi_key_semicolon(tmp_path):
    xfr = tmp_path / "t.xfr"
    xfr.write_text(
        "Rollup_1:\n"
        "  group_by {feed_name; output_dataset_name}\n"
        "  select sum(null_count) as null_count\n"
    )
    rules = parse_xfr(str(xfr))
    assert rules["rollup_1"]["group_by"] == ["feed_name", "output_dataset_name"]


def test_dedup_keys_multi_key_semicolon(tmp_path):
    xfr = tmp_path / "t.xfr"
    xfr.write_text("Dedup_1:\n  dedup_keys {tx_id; region}\n")
    rules = parse_xfr(str(xfr))
    assert rules["dedup_1"]["dedup_keys"] == ["tx_id", "region"]


def test_group_by_still_supports_comma(tmp_path):
    # No romper el separador clasico por comas.
    xfr = tmp_path / "t.xfr"
    xfr.write_text("R:\n  group_by a, b, c\n  select sum(x) as x\n")
    rules = parse_xfr(str(xfr))
    assert rules["r"]["group_by"] == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# BUG 1b — where multi-predicado: la condicion completa se conserva
# ---------------------------------------------------------------------------
def test_where_multi_predicate_preserved(tmp_path):
    xfr = tmp_path / "t.xfr"
    xfr.write_text(
        "Reformat_11:\n"
        "  where job_status != 'Fail' and proc_date < '${CAMPAIGN_DATE}'\n"
        "  select in.a as a\n"
    )
    rules = parse_xfr(str(xfr))
    assert rules["reformat_11"]["where"] == "job_status != 'Fail' and proc_date < '${CAMPAIGN_DATE}'"


# ---------------------------------------------------------------------------
# BUG 1a/1c — operador no se invierte y ${VAR} dentro de comillas se conserva
# ---------------------------------------------------------------------------
def test_where_operator_not_inverted_and_var_preserved():
    w = "job_status != 'Fail' and proc_date < '${CAMPAIGN_DATE}'"
    out = _to_boolean_filter(_translate_dml_expr(w))
    # el operador '<' se conserva (no se vuelve '>=')
    assert "proc_date <" in out
    assert ">=" not in out
    # la condicion job_status sigue presente
    assert "job_status" in out
    # ${CAMPAIGN_DATE} dentro del literal se conserva (no degrada a 'CAMPAIGN_DATE')
    assert "${CAMPAIGN_DATE}" in out


def test_dollar_var_outside_quotes_becomes_param_placeholder():
    # Fuera de comillas, $VAR / ${VAR} son PARAMETROS del job, no columnas.
    # Se normalizan a ${VAR} (placeholder de parametro, igual que ${CAMPAIGN_DATE}),
    # NO se degradan al identificador 'VAR' (que Spark tomaria como columna
    # inexistente y compararia columna-contra-columna). Ver Filter_by_Expression_2:
    # op_record_count_difference <= $RECORD_COUNT_DIFFERENCE.
    assert _translate_dml_expr("$MI_CAMPO + 1").strip() == "${MI_CAMPO} + 1"
    assert _translate_dml_expr("${OTRO} * 2").strip() == "${OTRO} * 2"
    # Dentro de comillas tambien se conserva como placeholder.
    assert "${LIT}" in _translate_dml_expr("x == '${LIT}'")


# ---------------------------------------------------------------------------
# _to_boolean_filter — filtros booleanos simples NO caen al fallback (e) <> 0
# (bug del \b tras comparadores simbolicos; aplica a spark y glue)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("fn", [_to_boolean_filter, glue_to_boolean_filter])
def test_boolean_filter_keeps_simple_comparisons(fn):
    assert fn("plan_type != 'cancelled'") == "plan_type != 'cancelled'"
    assert fn("confirmed = true") == "confirmed = true"
    assert fn("results_count > 0") == "results_count > 0"
    # sin '<> 0' espurio
    for expr in ("plan_type != 'cancelled'", "confirmed = true"):
        assert "<> 0" not in fn(expr)


# ---------------------------------------------------------------------------
# Funciones Ab Initio recien mapeadas (barrido tarea #3)
# ---------------------------------------------------------------------------
def test_decimal_truncate_mapped():
    out = _map_string_functions("decimal_truncate(x, 2)")
    assert "cast(" in out and "as bigint" in out and "100" in out


def test_decimal_round_mapped():
    assert _map_string_functions("decimal_round(monto, 2)") == "round(monto, 2)"


def test_string_pad_mapped():
    assert _map_string_functions("string_pad(nombre, 20)") == "rpad(nombre, 20, ' ')"


def test_date_difference_months_mapped():
    assert _map_date_functions("date_difference_months(d1, d2)") == "cast(months_between(d1, d2) as int)"


def test_now1_mapped():
    assert _map_date_functions("now1()") == "current_timestamp()"


# ---------------------------------------------------------------------------
# _safe_path_fragment — resuelve $[string_concat(...)] y $VAR sin romper f-string
# ---------------------------------------------------------------------------
def test_safe_path_string_concat_resuelto():
    p = '$[string_concat(AI_SERIAL_TEMP,"/automation_",product,".dat")]'
    out = _safe_path_fragment(p)
    # sin comillas dobles (romperian el f-string) y con interpolacion PARAMS
    assert '"' not in out
    assert "{PARAMS.AI_SERIAL_TEMP}" in out
    assert "{PARAMS.product}" in out
    assert "/automation_" in out and ".dat" in out


def test_safe_path_simple_var():
    assert _safe_path_fragment("${FEEDS}/file.txt") == "{PARAMS.FEEDS}/file.txt"


def test_safe_dbtable_desescapa_y_colapsa():
    t = _safe_dbtable("select * from $\\{DB\\}.tabla\n where x=1;")
    assert "\\{" not in t and "\\}" not in t
    assert "\n" not in t
    assert not t.endswith(";")


# ---------------------------------------------------------------------------
# _extract_local_vars — no crashea con valores que contienen \x01 (delimitador)
# ---------------------------------------------------------------------------
def test_extract_local_vars_no_crash_backslash_x():
    raw = (
        'out :: reformat(in) = begin\n'
        '  let string("\\x01") v1 = "a";\n'
        '  let string("\\x01") v2 = v1;\n'
        '  out.x :: v2;\n'
        'end;'
    )
    # No debe lanzar re.PatternError (bad escape \x)
    result = _extract_local_vars(raw)
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Cuerpo de JOIN (Fase 2) — first_defined -> coalesce con desambiguacion l/r
# ---------------------------------------------------------------------------
def test_join_body_two_sides_first_defined():
    body = (
        "out :: join(in0, in1) = begin\n"
        "  out.requestor_id :: first_defined(in0.requestor_id, in1.requestor_id);\n"
        "  out.cur :: if(!is_null(in0.record_count)) in0.record_count else NULL;\n"
        "  out.prev :: if(!is_null(in1.record_count)) in1.record_count else NULL;\n"
        "end;"
    )
    items, out_fields, pass_by_side, cols_by_side = _emit_join_body_columns("J", body)
    assert out_fields == ["requestor_id", "cur", "prev"]
    joined = " ".join(items)
    # coalesce entre lados con alias l/r
    assert "coalesce(`l`.`requestor_id`,`r`.`requestor_id`)" in joined.replace(" ", "").replace("coalesce(", "coalesce(") or "coalesce(`l`.`requestor_id`" in joined
    # cur usa el lado izquierdo (l), prev el derecho (r)
    assert "`l`.`record_count`" in joined
    assert "`r`.`record_count`" in joined
    # columnas registradas por lado
    assert "record_count" in cols_by_side.get(0, set())
    assert "record_count" in cols_by_side.get(1, set())


def test_join_body_three_sides():
    body = (
        "out :: join(in0, in1, in2) = begin\n"
        "  out.a :: first_defined(in0.a, in1.a);\n"
        "  out.b :: in2.b;\n"
        "end;"
    )
    items, out_fields, pass_by_side, cols_by_side = _emit_join_body_columns(
        "J", body, aliases=["s0", "s1", "s2"]
    )
    assert out_fields == ["a", "b"]
    joined = " ".join(items)
    assert "`s2`.`b`" in joined
    assert 2 in cols_by_side and "b" in cols_by_side[2]


def test_join_body_passthrough_side():
    body = (
        "out :: join(in0, in1) = begin\n"
        "  out.* :: in0.*;\n"
        "  out.flag :: if(!is_null(in1.x)) in1.x else '';\n"
        "end;"
    )
    items, out_fields, pass_by_side, cols_by_side = _emit_join_body_columns("J", body)
    assert pass_by_side.get(0) is True
    assert out_fields == ["flag"]


# ---------------------------------------------------------------------------
# Deteccion de ciclos (tarea #5)
# ---------------------------------------------------------------------------
def test_cycle_excluded_from_execution_order():
    ast = {
        "nodes": [
            {"id": "A", "type": "TRANSFORM"},
            {"id": "B", "type": "TRANSFORM"},
        ],
        "edges": [{"from": "A", "to": "B"}, {"from": "B", "to": "A"}],
    }
    dag = build_dag(ast)
    assert len(dag.execution_order) < 2
    assert dag.cycle_nodes  # se registraron los nodos en ciclo


def test_acyclic_dag_keeps_all_nodes():
    ast = {
        "nodes": [
            {"id": "A", "type": "SOURCE"},
            {"id": "B", "type": "TRANSFORM"},
            {"id": "C", "type": "SINK"},
        ],
        "edges": [{"from": "A", "to": "B"}, {"from": "B", "to": "C"}],
    }
    dag = build_dag(ast)
    assert len(dag.execution_order) == 3
    assert not dag.cycle_nodes
    order = [n.id for n in dag.execution_order]
    assert order.index("A") < order.index("B") < order.index("C")


# ---------------------------------------------------------------------------
# JOIN: orden de padres por puerto de entrada (in0/in1). El cuerpo DML del join
# referencia inN posicionalmente; node.parents DEBE seguir el ordinal del puerto,
# no el orden arbitrario del set de aristas (que cruzaba current/previous).
# ---------------------------------------------------------------------------
def test_join_parents_ordered_by_input_port():
    # Dos padres que entran por in1 (P_uno) e in0 (P_cero) EN ESE ORDEN de aristas;
    # tras build_dag, parents debe quedar [P_cero(in0), P_uno(in1)].
    ast = {
        "nodes": [
            {"id": "P_uno", "type": "SOURCE"},
            {"id": "P_cero", "type": "SOURCE"},
            {"id": "J", "type": "JOIN"},
        ],
        "edges": [
            {"from": "P_uno", "to": "J", "to_port": 1},
            {"from": "P_cero", "to": "J", "to_port": 0},
        ],
    }
    dag = build_dag(ast)
    parents = dag.nodes["J"].parents
    assert parents == ["P_cero", "P_uno"], parents


def test_join_parents_without_port_preserve_order():
    # Sin to_port (fallback): se conserva el orden de aparicion de las aristas.
    ast = {
        "nodes": [
            {"id": "A", "type": "SOURCE"},
            {"id": "B", "type": "SOURCE"},
            {"id": "J", "type": "JOIN"},
        ],
        "edges": [{"from": "A", "to": "J"}, {"from": "B", "to": "J"}],
    }
    dag = build_dag(ast)
    assert dag.nodes["J"].parents == ["A", "B"]


# ---------------------------------------------------------------------------
# Update_Table (db-update): se clasifica como SINK y se captura el UPDATE SQL.
# Antes caia en TRANSFORM (passthrough) o SOURCE (spark.read), perdiendo el UPDATE.
# ---------------------------------------------------------------------------
def test_update_table_classified_as_sink_with_sql():
    import os
    import main
    mp = "bnx_library/High-08-09/XSell_Automation_Control_Check.mp"
    if not os.path.exists(mp):
        pytest.skip("grafo XSell no disponible")
    ast = main.parse_project(mp)
    ups = [n for n in ast["nodes"] if n["id"].lower().startswith("update_")]
    assert ups, "no se encontraron nodos Update_*"
    for n in ups:
        assert n["type"] == "SINK", f"{n['id']} deberia ser SINK, es {n['type']}"
        dbu = n.get("db_source") or {}
        assert dbu.get("update_sql"), f"{n['id']} sin update_sql capturado"
        # El SQL debe empezar con un comando DML valido (UPDATE/INSERT/MERGE/DELETE).
        assert dbu["update_sql"].strip().upper().startswith(
            ("UPDATE", "INSERT", "MERGE", "DELETE")
        ), dbu["update_sql"][:40]


# ---------------------------------------------------------------------------
# JOIN type: se toma del parametro concreto join_type del PROTO del componente
# (Inner/Full/Explicit), mapeando instancia->proto via XXGobject_proto_object.
# Antes se leia record_match_required (una formula) mapeada por posicion a
# vertices internos equivocados -> el join salia 'left' cuando el GDE decia Inner.
# ---------------------------------------------------------------------------
def test_join_type_from_mp_instance_priority():
    import os
    import main
    mp = "bnx_library/High-08-09/XSell_Automation_Control_Check.mp"
    if not os.path.exists(mp):
        pytest.skip("grafo XSell no disponible")
    ast = main.parse_project(mp)
    raw = open(mp, encoding="utf-8", errors="replace").read().replace("\x00", "")
    emb = main._extract_embedded_transforms(raw)
    node_map = {}
    for nd in ast.get("nodes", []):
        vid = nd.get("vertex_id", nd["id"])
        node_map[vid] = {
            "name": nd["id"],
            "comp_type": nd.get("name", nd["id"]),
            "proto_type": nd.get("type", "TRANSFORM"),
            "is_sort": nd.get("is_sort", False),
        }
    xfr = {}
    main._apply_embedded_transforms(node_map, emb, xfr)
    # Tipos esperados segun la fuente .mp:
    #  - current_feed_stats, join, join_3, join_3_409: join_type Inner del proto.
    #  - join_latest_records_counts y null_s_join: la INSTANCIA declara
    #    join_type=Explicit con record_match_required1=False (iface 3.2.2) ->
    #    in1 opcional -> LEFT (in0 preservado). El tipo de la instancia tiene
    #    prioridad sobre el default 'Inner' del proto/template.
    expected = {
        "current_feed_stats": "inner",
        "join": "inner",
        "join_3": "inner",
        "join_latest_records_counts": "left",
        "null_s_join": "left",
    }
    for jname, exp in expected.items():
        if jname in xfr and xfr[jname].get("join_type"):
            assert xfr[jname]["join_type"] == exp, (jname, xfr[jname]["join_type"], "esperado", exp)


def test_join_type_explicit_legacy_becomes_left():
    # Join Explicit con interfaz legacy: record_required0=False, record_required1=True.
    # Legacy invierte el booleano -> required0=True (obligatorio), required1=False
    # (opcional) -> LEFT. El nombre del nodo ("LoJ" = Left Outer Join) lo confirma.
    import os
    import glob
    import main
    files = glob.glob("bnx_library/**/AMBS_AMED_BAL_EPP_OLA_ACCT_ENCRY_DLY_NEW.mp", recursive=True)
    if not files:
        pytest.skip("grafo AMBS no disponible")
    f = files[0]
    ast = main.parse_project(f)
    raw = open(f, encoding="utf-8", errors="replace").read().replace("\x00", "")
    emb = main._extract_embedded_transforms(raw)
    node_map = {}
    for nd in ast.get("nodes", []):
        vid = nd.get("vertex_id", nd["id"])
        node_map[vid] = {
            "name": nd["id"],
            "comp_type": nd.get("name", nd["id"]),
            "proto_type": nd.get("type", "TRANSFORM"),
            "is_sort": nd.get("is_sort", False),
        }
    xfr = {}
    main._apply_embedded_transforms(node_map, emb, xfr)
    loj = [v for k, v in xfr.items() if "loj" in k and v.get("join_type")]
    assert loj, "no se encontro el join LoJ"
    for v in loj:
        assert v["join_type"] == "left", v["join_type"]


# ---------------------------------------------------------------------------
# JOIN con keys ASIMETRICAS (override_key1) y operador de prioridad :N:.
# raw_tracking_staging / Add_toComponent_Depth_and_Ply:
#   key           = {jobSequenceNumber; toComponentName}   (in0)
#   override_key1 = {jobSequenceNumber; componentName}     (in1)
# El join debe unir por s0.toComponentName == s1.componentName (no NULL-rellenar),
# y la salida debe exponer columnas sin prefijo de alias para nodos posteriores.
# ---------------------------------------------------------------------------
def _compile_spark_via_codegen(mp_path):
    import io
    import contextlib
    import main
    from src.dag.builder import build_dag
    from src.codegen.spark_codegen import generate_spark
    import tempfile
    out = tempfile.mktemp(suffix=".py")
    with contextlib.redirect_stdout(io.StringIO()):
        ast = main.parse_project(mp_path)
        dag = build_dag(ast)
        raw = open(mp_path, encoding="utf-8", errors="replace").read().replace("\x00", "")
        emb = main._extract_embedded_transforms(raw)
        nm = {}
        for nd in ast.get("nodes", []):
            vid = nd.get("vertex_id", nd["id"])
            nm[vid] = {
                "name": nd["id"],
                "comp_type": nd.get("name", nd["id"]),
                "proto_type": nd.get("type", "TRANSFORM"),
                "is_sort": nd.get("is_sort", False),
            }
        xfr = {}
        main._apply_embedded_transforms(nm, emb, xfr)
        generate_spark(dag, out, xfr)
    return open(out).read()


def test_join_asymmetric_keys_and_priority_operator():
    import os
    import glob
    files = glob.glob("bnx_library/**/raw_tracking_staging.mp", recursive=True)
    if not files:
        pytest.skip("grafo raw_tracking_staging no disponible")
    code = _compile_spark_via_codegen(files[0])
    # el codigo generado debe compilar sin errores de sintaxis
    import ast as _ast
    _ast.parse(code)
    # 1) join asimetrico: condicion explicita cruzando toComponentName con componentName
    assert 'col("s0.toComponentName") == col("s1.componentName")' in code
    # 2) operador de prioridad :1:/:2: colapsado a un solo coalesce (no columna duplicada)
    assert 'coalesce(`s1`.`hostAlias`, `s0`.`toHost`)' in code
    # no debe haber dos alias("toCompPartitionHost") en la MISMA linea del select
    for line in code.splitlines():
        if "_sel_Add_ToComponent_Host +=" in line:
            assert line.count('.alias("toCompPartitionHost")') == 1, line


def test_join_body_local_var_neutralized():
    # Get_Job_Path_and_Status: el cuerpo del join calcula variables locales con
    # logica procedural (let sandboxPath/executableName + if/else + re_replace +
    # string_substring) y las usa en out.psetOrGraphName :: executableName. Eso no
    # es traducible a una expr Spark: la columna debe salir como lit(None) con TODO,
    # NO como expr("executableName") (que rompe con UNRESOLVED_COLUMN en runtime).
    import glob
    files = glob.glob("bnx_library/**/raw_tracking_staging.mp", recursive=True)
    if not files:
        pytest.skip("grafo raw_tracking_staging no disponible")
    code = _compile_spark_via_codegen(files[0])
    import ast as _ast
    _ast.parse(code)
    # no debe quedar un expr("executableName") suelto (variable local huerfana)
    assert 'expr("executableName")' not in code
    # la columna psetOrGraphName debe neutralizarse a lit(None)
    assert 'lit(None).alias("psetOrGraphName")' in code


# ---------------------------------------------------------------------------
# Cast de tipo Ab Initio con modificador de ENDIANNESS: (big endian integer(4))x
# -> CAST(x AS INT). El endianness no afecta el tipo SQL de Spark. integer(N) es
# el TAMAÑO EN BYTES (4->INT, 8->BIGINT). Sin esto quedaba crudo -> ParseException.
# ---------------------------------------------------------------------------
def test_big_endian_integer_cast():
    from src.codegen.spark_codegen import _apply_abinitio_casts
    assert _apply_abinitio_casts("(big endian integer(4))x") == "CAST(x AS INT)"
    assert _apply_abinitio_casts("(big endian integer(8))x") == "CAST(x AS BIGINT)"
    assert _apply_abinitio_casts("(little endian real(4))y") == "CAST(y AS FLOAT)"
    assert _apply_abinitio_casts("(integer(4))z") == "CAST(z AS INT)"
    out = _apply_abinitio_casts("(big endian integer(4))(((a - b)/c)*100)")
    assert out == "CAST((((a - b)/c)*100) AS INT)"
    # ya no debe quedar el cast crudo
    assert "endian" not in out


# ---------------------------------------------------------------------------
# JOIN con entradas NOMBRADAS: out :: join(stat, spec) = ... stat.col / spec.col
# Los nombres de entrada mapean por posicion a in0/in1. Antes 'stat.fromPortName'
# se aplanaba a 'stat_fromPortName' (columna inexistente) -> UNRESOLVED_COLUMN.
# ---------------------------------------------------------------------------
def test_join_named_inputs_map_to_positional():
    from src.codegen.spark_codegen import _emit_join_body_columns
    body = (
        "out::join(stat, spec) =\n"
        "begin\n"
        "  out.portName :: stat.fromPortName;\n"
        "  out.totalCpu :: spec.systemCpu + spec.userCpu;\n"
        "end;"
    )
    items, out_fields, _pass, cols_by_side = _emit_join_body_columns(
        "J", body, aliases=["s0", "s1"]
    )
    joined = " ".join(items)
    # stat -> s0, spec -> s1 (por posicion)
    assert "`s0`.`fromPortName`" in joined
    assert "`s1`.`systemCpu`" in joined
    # no debe quedar el nombre de entrada aplanado como columna
    assert "stat_fromPortName" not in joined
    assert 0 in cols_by_side and "fromPortName" in cols_by_side[0]
    assert 1 in cols_by_side and "systemCpu" in cols_by_side[1]
