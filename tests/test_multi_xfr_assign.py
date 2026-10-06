# tests/test_multi_xfr_assign.py
from main import _assign_multi_xfr, _norm_name


def test_norm_name_strips_ext_and_separators():
    assert _norm_name("Join_Cust.xfr") == "joincust"
    assert _norm_name("JOIN-CUST") == "joincust"
    assert _norm_name("calc.dml") == "calc"


def test_assign_by_filename_name_match():
    # Dos .xfr con nombres que coinciden con los nodos del grafo (caso real:
    # la ruta/nombre del archivo es la referencia correcta, no la posicion).
    multi = [
        {"name": "Calcular_Riesgo.xfr", "dml_fields": [{"name": "score", "type": "decimal"}]},
        {"name": "Enriquecer_Cliente.xfr", "dml_fields": [{"name": "segment", "type": "string"}]},
    ]
    transform_nodes = [
        {"id": "Enriquecer_Cliente", "name": "Enriquecer_Cliente"},
        {"id": "Calcular_Riesgo", "name": "Calcular_Riesgo"},
    ]
    xfr_rules = {}
    _assign_multi_xfr(multi, transform_nodes, xfr_rules)
    # Cada .xfr fue a su nodo correcto por NOMBRE, no por orden.
    assert xfr_rules["calcular_riesgo"]["dml_fields"][0]["name"] == "score"
    assert xfr_rules["enriquecer_cliente"]["dml_fields"][0]["name"] == "segment"


def test_name_match_takes_priority_over_position():
    # El orden de los .xfr esta invertido respecto a los nodos: si el match
    # fuera posicional, se asignarian cruzados. El match por nombre lo evita.
    multi = [
        {"name": "nodeB", "dml_fields": [{"name": "b_col", "type": "int"}]},
        {"name": "nodeA", "dml_fields": [{"name": "a_col", "type": "int"}]},
    ]
    transform_nodes = [
        {"id": "nodeA", "name": "nodeA"},
        {"id": "nodeB", "name": "nodeB"},
    ]
    xfr_rules = {}
    _assign_multi_xfr(multi, transform_nodes, xfr_rules)
    assert xfr_rules["nodea"]["dml_fields"][0]["name"] == "a_col"
    assert xfr_rules["nodeb"]["dml_fields"][0]["name"] == "b_col"
