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
