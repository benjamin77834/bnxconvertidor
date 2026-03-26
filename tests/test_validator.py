# tests/test_validator.py
import pytest
from src.mp_parser import parse_mp_ast
from src.dag.builder import build_dag
from src.xfr_parser import parse_xfr
from src.validator.semantic import validate


def make_dag(mp_text, tmp_path):
    mp = tmp_path / "test.mp"
    mp.write_text(mp_text)
    return build_dag(parse_mp_ast(str(mp)))

def make_xfr(xfr_text, tmp_path):
    xfr = tmp_path / "test.xfr"
    xfr.write_text(xfr_text)
    return parse_xfr(str(xfr))


def test_valid_pipeline(tmp_path):
    dag = make_dag("NODE A : SOURCE\nNODE B : TRANSFORM\nNODE C : SINK\nA -> B\nB -> C\n", tmp_path)
    xfr = make_xfr("B:\n  select *\n  where id IS NOT NULL\n", tmp_path)
    errors, warnings = validate(dag, xfr)
    assert errors == []

def test_join_missing_key_warns(tmp_path):
    dag = make_dag("NODE A : SOURCE\nNODE B : SOURCE\nNODE J : JOIN\nA -> J\nB -> J\n", tmp_path)
    errors, warnings = validate(dag, {})
    assert any("join_key" in w for w in warnings)

def test_sink_no_parent_errors(tmp_path):
    dag = make_dag("NODE A : SOURCE\nNODE S : SINK\n", tmp_path)
    errors, _ = validate(dag, {})
    assert any("SINK" in e and "no parent" in e for e in errors)

def test_transform_no_parent_errors(tmp_path):
    dag = make_dag("NODE T : TRANSFORM\n", tmp_path)
    errors, _ = validate(dag, {})
    assert any("TRANSFORM" in e and "no parent" in e for e in errors)
