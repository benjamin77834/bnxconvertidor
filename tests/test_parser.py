# tests/test_parser.py
import pytest
from src.mp_parser import parse_mp_ast, normalize_id
from src.xfr_parser import parse_xfr
from src.dag.builder import build_dag


# ?? mp_parser ????????????????????????????????????????????????
def test_normalize_id():
    assert normalize_id("Clean Orders") == "Clean_Orders"
    assert normalize_id("node-1") == "node_1"
    assert normalize_id("  A  ") == "A"

def test_parse_nodes(tmp_path):
    mp = tmp_path / "test.mp"
    mp.write_text("NODE Orders : SOURCE\nNODE Customers : SOURCE\n")
    ast = parse_mp_ast(str(mp))
    assert len(ast["nodes"]) == 2
    assert ast["nodes"][0]["type"] == "SOURCE"

def test_parse_edges(tmp_path):
    mp = tmp_path / "test.mp"
    mp.write_text("NODE A : SOURCE\nNODE B : TRANSFORM\nA -> B\n")
    ast = parse_mp_ast(str(mp))
    assert len(ast["edges"]) == 1
    assert ast["edges"][0] == {"from": "A", "to": "B"}

def test_parse_subgraph(tmp_path):
    mp = tmp_path / "test.mp"
    mp.write_text("SUBGRAPH MyGroup {\n  NODE X : TRANSFORM\n}\n")
    ast = parse_mp_ast(str(mp))
    assert "MyGroup" in ast["subgraphs"]
    assert "X" in ast["subgraphs"]["MyGroup"]

def test_ignore_comments(tmp_path):
    mp = tmp_path / "test.mp"
    mp.write_text("# this is a comment\nNODE A : SOURCE\n")
    ast = parse_mp_ast(str(mp))
    assert len(ast["nodes"]) == 1


# ?? xfr_parser ???????????????????????????????????????????????
def test_parse_xfr_select_where(tmp_path):
    xfr = tmp_path / "test.xfr"
    xfr.write_text("CleanOrders:\n  select order_id, amount\n  where amount > 0\n")
    rules = parse_xfr(str(xfr))
    assert "cleanorders" in rules
    assert rules["cleanorders"]["select"] == "order_id, amount"
    assert rules["cleanorders"]["where"] == "amount > 0"

def test_parse_xfr_group_by(tmp_path):
    xfr = tmp_path / "test.xfr"
    xfr.write_text("OrderTotals:\n  group_by customer_id\n  select SUM(amount) as total\n")
    rules = parse_xfr(str(xfr))
    assert rules["ordertotals"]["group_by"] == ["customer_id"]

def test_parse_xfr_join_key(tmp_path):
    xfr = tmp_path / "test.xfr"
    xfr.write_text("MyJoin:\n  join_key customer_id\n  join_type left\n")
    rules = parse_xfr(str(xfr))
    assert rules["myjoin"]["join_key"] == "customer_id"
    assert rules["myjoin"]["join_type"] == "left"


# ?? dag builder ??????????????????????????????????????????????
def test_dag_topo_order(tmp_path):
    mp = tmp_path / "test.mp"
    mp.write_text("NODE A : SOURCE\nNODE B : TRANSFORM\nNODE C : SINK\nA -> B\nB -> C\n")
    ast = parse_mp_ast(str(mp))
    dag = build_dag(ast)
    order = [n.id for n in dag.execution_order]
    assert order.index("A") < order.index("B")
    assert order.index("B") < order.index("C")

def test_dag_parents_assigned(tmp_path):
    mp = tmp_path / "test.mp"
    mp.write_text("NODE A : SOURCE\nNODE B : TRANSFORM\nA -> B\n")
    ast = parse_mp_ast(str(mp))
    dag = build_dag(ast)
    assert "A" in dag.nodes["B"].parents

def test_dag_cycle_detection(tmp_path):
    mp = tmp_path / "test.mp"
    mp.write_text("NODE A : TRANSFORM\nNODE B : TRANSFORM\nA -> B\nB -> A\n")
    ast = parse_mp_ast(str(mp))
    dag = build_dag(ast)
    # Con ciclo el topo sort no incluye todos los nodos
    assert len(dag.execution_order) < 2
