"""Orquestador Ab Initio: variantes por pset de plan y plan de planes."""
import json
import os

import pytest

from src import orquestador as o

LOTE = os.path.join(os.path.dirname(__file__), "..", "abinitio", "lote_nov10")


def _plan(tmp_path, nombre, env=None, target=None):
    st = [{"id": "t1", "name": "job", "depends_on": [], "dep_flags": {}, "solo_en_fallo": False,
           "enabled": True, "continue_on_error": False,
           "action": ({"type": "graph", "target": target, "source": "x.mp", "status": "ok"} if target
                      else {"type": "noop", "target": None, "source": None, "status": "no_traducido"})}]
    ej = dict(o.EJECUCION_DEFECTO, env=env or {})
    d = {"plan": nombre + ".plan", "nombre": nombre, "direccion": "prior", "ejecucion": ej,
         "steps": st, "enlaces": []}
    p = tmp_path / f"orquestacion_{nombre}.json"
    p.write_text(json.dumps(d))
    return str(p)


def test_params_a_env_solo_literales():
    env, pend = o.params_a_env({"A": "1", "B": "$AI_DB/x", "C": "${X}y", "D": "$[f()]", "bad-name": "z"})
    assert env == {"A": "1"}
    assert set(pend) == {"B", "C", "D", "bad-name"}


@pytest.mark.skipif(not os.path.isdir(LOTE), reason="sin el lote de ejemplo")
def test_variante_por_pset_con_parametros(tmp_path):
    orchs = o.build(LOTE, str(tmp_path))
    v = orchs["plan_download_teradata_tables_enable__2"]
    assert v["pset"] == "plan_download_teradata_tables_enable_2.pset"
    assert v["ejecucion"]["env"] == {"ENABLE_FLAG": "2"}
    assert "plan_download_teradata_tables_enable" in orchs          # el plan base sigue
    assert orchs["Plan_ffs_lkp_generator__LA1D51CTE"]["ejecucion"]["env"] == {"INTERFACE": "LA1D51CTE"}
    # dag_id distinto por variante
    assert o.dag_id_de(v) != o.dag_id_de(orchs["plan_download_teradata_tables_enable"])


def test_componer_valida(tmp_path):
    a, b = _plan(tmp_path, "a"), _plan(tmp_path, "b")
    with pytest.raises(ValueError, match="al menos 2"):
        o.componer("x", [a])
    with pytest.raises(ValueError, match="repetidos"):
        o.componer("x", [a, a])
    with pytest.raises(ValueError, match="nombre"):
        o.componer("../x", [a, b])
    pp = o.componer("ab", [a, b])
    assert pp["tipo"] == "plan_de_planes" and pp["nombre"] == "PLANES_ab"
    assert [s["depends_on"] for s in pp["steps"]] == [[], ["p1"]]
    assert [s["depends_on"] for s in o.componer("ab", [a, b], en_cadena=False)["steps"]] == [[], []]
    ruta = o.save_all({pp["nombre"]: pp}, str(tmp_path))[0]
    with pytest.raises(ValueError, match="no se anidan"):
        o.componer("y", [ruta, a])


def test_dry_run_anidado_y_fallo_bloquea_en_real(tmp_path, capsys):
    a = _plan(tmp_path, "a", target=str(tmp_path / "no_existe_spark.py"))
    b = _plan(tmp_path, "b")
    pp = o.componer("ab", [a, b])
    assert o.ejecutar(pp, real=False)            # dry-run: todo OK, detalle anidado
    out = capsys.readouterr().out
    assert "    [*] Plan a.plan" in out and "    [*] Plan b.plan" in out
    # real: el job de 'a' no existe -> 'a' falla y 'b' (depende de a) se omite
    assert not o.ejecutar(pp, real=True, base_path=str(tmp_path / "data"))
    out = capsys.readouterr().out
    assert "p2 b: omitido, fallo previo ['p1']" in out


def test_airflow_plan_de_planes(tmp_path):
    a, b = _plan(tmp_path, "a", env={"X": "1"}), _plan(tmp_path, "b")
    dag = o.generar_airflow(o.componer("ab", [a, b]))
    compile(dag, "dag.py", "exec")
    assert "TriggerDagRunOperator" in dag
    assert "trigger_dag_id='bnx_a'" in dag and "trigger_dag_id='bnx_b'" in dag
    assert "wait_for_completion=True" in dag
    # el DAG del sub-plan lleva los parametros del pset en ENV
    with open(a) as fh:
        assert "ENV = {'X': '1'}" in o.generar_airflow(json.load(fh))


EJERCICIO = os.path.join(os.path.dirname(__file__), "..", "abinitio", "ejercicio_3_planes")


@pytest.mark.skipif(not os.path.isdir(EJERCICIO), reason="sin el ejercicio de 3 planes")
def test_paso_script_apunta_al_ksh_de_la_carpeta(tmp_path):
    orchs = o.build(EJERCICIO, str(tmp_path))
    a = next(s["action"] for s in orchs["Plan_ingesta_clientes"]["steps"] if s["action"]["type"] == "script")
    assert a["status"] == "ok" and a["target"].endswith("prepara_directorios.ksh")
    assert os.path.isfile(o._ruta_plan(a["target"]))


# ---- pset con prototipo presente pero sin convertir (rutas Windows, prefijos, mayusculas) ----
def _proyecto_windows(tmp_path, prefijo="", mp_ext=".mp"):
    """Plan -> pset (nombre distinto al mp, !prototype estilo Windows) -> .mp presente."""
    ab = tmp_path / "ab"
    ab.mkdir()
    plan = open(os.path.join(EJERCICIO, "Plan_ingesta_clientes.plan"), encoding="utf-8").read()
    plan = plan.replace("$AI_PSET/ingesta_clientes.pset", "$AI_PSET\\T002_File_To_Dataset_ACCRL_MAST_D.pset")
    (ab / (prefijo + "Plan_x.plan")).write_text(plan, encoding="utf-8")
    (ab / "T002_File_To_Dataset_ACCRL_MAST_D.pset").write_text(
        "!prototype|P|||$AI_MP\\T002_File_To_Dataset.mp\nFECHA||||20250115\n", encoding="utf-8")
    (ab / (prefijo + "T002_File_To_Dataset" + mp_ext)).write_bytes(
        open(os.path.join(EJERCICIO, "ingesta_clientes.mp"), "rb").read())
    out = tmp_path / "out"
    out.mkdir()
    return str(ab), str(out)


def _paso_graph(orchs):
    return next(s["action"] for s in orchs["Plan_x"]["steps"] if s["name"] == "Run_ingesta_clientes")


@pytest.mark.skipif(not os.path.isdir(EJERCICIO), reason="sin el ejercicio de 3 planes")
@pytest.mark.parametrize("prefijo,ext", [("", ".mp"), ("1_", ".mp"), ("", ".MP")])
def test_pset_con_mp_presente_sin_convertir_no_es_faltante(tmp_path, prefijo, ext):
    ab, out = _proyecto_windows(tmp_path, prefijo, ext)
    a = _paso_graph(o.build(ab, out))
    assert a["status"] == "sin_convertir" and a["target"] is None
    assert a["source"].lower() == "t002_file_to_dataset.mp"
    # tras convertir (aqui simulado con el .py) -> ok; el .py puede traer prefijo numerico
    (tmp_path / "out" / "2_T002_File_To_Dataset_spark.py").write_text("x = 1\n")
    a = _paso_graph(o.build(ab, out))
    assert a["status"] == "ok" and a["target"].endswith("2_T002_File_To_Dataset_spark.py")


@pytest.mark.skipif(not os.path.isdir(EJERCICIO), reason="sin el ejercicio de 3 planes")
def test_pset_sin_mp_es_faltante_con_el_mp_en_source(tmp_path):
    ab, out = _proyecto_windows(tmp_path)
    os.remove(os.path.join(ab, "T002_File_To_Dataset.mp"))
    a = _paso_graph(o.build(ab, out))
    assert a["status"] == "faltante" and a["source"] == "T002_File_To_Dataset.mp"


@pytest.mark.skipif(not os.path.isdir(EJERCICIO), reason="sin el ejercicio de 3 planes")
def test_py_con_nombre_del_pset_tambien_vale(tmp_path):
    ab, out = _proyecto_windows(tmp_path)
    (tmp_path / "out" / "T002_File_To_Dataset_ACCRL_MAST_D_spark.py").write_text("x = 1\n")
    assert _paso_graph(o.build(ab, out))["status"] == "ok"


@pytest.mark.skipif(not os.path.isdir(EJERCICIO), reason="sin el ejercicio de 3 planes")
def test_ksh_faltante_no_afecta_al_grafo(tmp_path):
    ab, out = _proyecto_windows(tmp_path)
    orch = o.build(ab, out)["Plan_x"]
    est = {s["name"]: s["action"]["status"] for s in orch["steps"]}
    assert est["Prepara_directorios"] == "faltante"      # el .ksh no esta en la carpeta
    assert est["Run_ingesta_clientes"] == "sin_convertir"


def test_norm_name_acepta_rutas_windows_y_variables():
    from src import pset_map as pm
    assert pm._norm_name("$AI_MP\\2_x.mp") == "x.mp"
    assert pm._norm_name("${AI_MP}/x.mp") == "x.mp"
    assert pm._norm_name("C:\\a\\b\\3_Y.MP") == "Y.MP"


@pytest.mark.skipif(not os.path.isdir(EJERCICIO), reason="sin el ejercicio de 3 planes")
def test_regenerar_conserva_ediciones_y_refresca_accion(tmp_path):
    ab, out = _proyecto_windows(tmp_path)
    assert o.pendientes_de_convertir(ab, out) == ["T002_File_To_Dataset.mp"]
    (r,) = [p for p in o.regenerar(ab, out) if p.endswith("orquestacion_Plan_x.json")]
    d = json.load(open(r))
    sid = next(s["id"] for s in d["steps"] if s["name"] == "Run_ingesta_clientes")
    for s in d["steps"]:
        if s["id"] == sid:
            s["enabled"] = False        # edicion del usuario
    json.dump(d, open(r, "w"))
    (tmp_path / "out" / "T002_File_To_Dataset_spark.py").write_text("x = 1\n")
    assert o.pendientes_de_convertir(ab, out) == []
    o.regenerar(ab, out)
    d = json.load(open(r))
    st = next(s for s in d["steps"] if s["id"] == sid)
    assert st["enabled"] is False and st["action"]["status"] == "ok"
