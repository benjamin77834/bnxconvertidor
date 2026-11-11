"""Orden de las fuentes del Framework MLOps v2 (main.py generado por src/mlops_pkg.py).

Se extraen las funciones de orden del TEXTO del main.py que viaja en el paquete y se
ejecutan aisladas (sin Spark). El caso clave es la compatibilidad: sin depends_on el
orden debe ser identico al historico 'pivote primero'.
"""
import ast
import json
import os

import pytest

from src.mlops_pkg import _MAIN_PY

_FUNCS = ("_orden_pivote_primero", "_orden_dependencias", "_cargar_orden")


@pytest.fixture(scope="module")
def ns(tmp_path_factory):
    tree = ast.parse(_MAIN_PY)  # el main.py generado debe ser Python valido
    defs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in _FUNCS]
    assert {d.name for d in defs} == set(_FUNCS)
    here = tmp_path_factory.mktemp("pkg")
    space = {"os": os, "json": json, "_here": str(here)}
    exec(compile(ast.Module(body=defs, type_ignores=[]), "main.py", "exec"), space)
    space["_tmp_here"] = here
    return space


def test_compat_sin_depends_on_igual_que_pivote_primero(ns):
    fuentes = ["bureau", "datos_pivote", "saldos", "pivote", "pagos"]
    cfg = {s: {"table_name": s} for s in fuentes}
    viejo = ns["_orden_pivote_primero"](list(fuentes), cfg)
    nuevo, explicitas = ns["_orden_dependencias"](list(fuentes), cfg, {})
    assert nuevo == viejo == ["datos_pivote", "pivote", "bureau", "saldos", "pagos"]
    assert explicitas == {}


def test_compat_sin_pivote_conserva_orden(ns):
    fuentes = ["c", "a", "b"]
    assert ns["_orden_dependencias"](fuentes, {}, {}) == (["c", "a", "b"], {})


def test_compat_pivot_true_en_cfg(ns):
    fuentes = ["a", "base"]
    cfg = {"a": {}, "base": {"pivot": True}}
    assert ns["_orden_dependencias"](fuentes, cfg, {})[0] == ["base", "a"]


def test_depends_on_en_cfg_ordena_varios_niveles(ns):
    fuentes = ["features", "pivote", "agregados", "bureau"]
    cfg = {"features": {"depends_on": ["agregados"]},
           "agregados": {"depends_on": ["pivote", "bureau"]}}
    orden, explicitas = ns["_orden_dependencias"](fuentes, cfg, {})
    assert orden.index("pivote") < orden.index("agregados")
    assert orden.index("bureau") < orden.index("agregados") < orden.index("features")
    assert explicitas == {"features": ["agregados"], "agregados": ["pivote", "bureau"]}


def test_depends_on_vacio_no_espera_al_pivote(ns):
    # depends_on: [] explicito = independiente de verdad (no espera al pivote)
    fuentes = ["libre", "pivote", "otra"]
    cfg = {"libre": {"depends_on": []}}
    orden, _ = ns["_orden_dependencias"](fuentes, cfg, {})
    assert orden == ["pivote", "libre", "otra"]   # pivote sigue teniendo prioridad al empatar
    assert ns["_orden_dependencias"](fuentes, cfg, {})[1] == {"libre": []}


def test_orden_json_aplica_y_cfg_tiene_prioridad(ns):
    fuentes = ["a", "b", "c"]
    orden_json = {"a": {"depends_on": ["c"]}, "b": {"depends_on": ["a"]}}
    cfg = {"b": {"depends_on": []}}           # el cfg.json gana sobre orden.json
    orden, explicitas = ns["_orden_dependencias"](fuentes, cfg, orden_json)
    assert orden.index("c") < orden.index("a")
    assert explicitas == {"a": ["c"], "b": []}


def test_pivot_desde_orden_json(ns):
    assert ns["_orden_dependencias"](["x", "y"], {}, {"y": {"pivot": True}})[0] == ["y", "x"]


def test_ciclo_detiene(ns):
    cfg = {"a": {"depends_on": ["b"]}, "b": {"depends_on": ["a"]}}
    with pytest.raises(SystemExit, match="ciclo"):
        ns["_orden_dependencias"](["a", "b"], cfg, {})


def test_autodependencia_y_tipo_invalido(ns):
    with pytest.raises(SystemExit, match="si misma"):
        ns["_orden_dependencias"](["a"], {"a": {"depends_on": ["a"]}}, {})
    with pytest.raises(SystemExit, match="lista"):
        ns["_orden_dependencias"](["a"], {"a": {"depends_on": "b"}}, {})


def test_dependencia_ausente_se_ignora_con_aviso(ns, capsys):
    orden, explicitas = ns["_orden_dependencias"](["a"], {"a": {"depends_on": ["no_existe"]}}, {})
    assert orden == ["a"] and explicitas == {"a": []}
    assert "no_existe" in capsys.readouterr().out


def test_cargar_orden(ns, tmp_path):
    here = ns["_tmp_here"]
    assert ns["_cargar_orden"]() == {}                      # sin archivo: orden de siempre
    (here / "orden.json").write_text(json.dumps({"sources": {"a": {"pivot": True}}}))
    try:
        assert ns["_cargar_orden"]() == {"a": {"pivot": True}}
    finally:
        (here / "orden.json").unlink()
    p = tmp_path / "otro.json"
    p.write_text(json.dumps({"sources": {"b": {"depends_on": ["a"]}}}))
    assert ns["_cargar_orden"](str(p)) == {"b": {"depends_on": ["a"]}}
    with pytest.raises(SystemExit, match="no existe"):
        ns["_cargar_orden"](str(tmp_path / "nada.json"))
    p.write_text("{}")
    with pytest.raises(SystemExit, match="sources"):
        ns["_cargar_orden"](str(p))
