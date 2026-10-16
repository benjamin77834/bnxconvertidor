# tests/test_data_quality.py
"""Pruebas del comparador de calidad de datos (src/data_quality.py)."""
import csv
import io
import json

from src.data_quality import (
    load_table, column_stats, compare, report_to_csv, report_to_html,
)


A_CSV = (
    "id,amount,status\n"
    "1,100.5,OK\n"
    "2,200.0,OK\n"
    "3,150.25,FAIL\n"
    "4,99.99,OK\n"
    "5,300.0,OK\n"
)
B_CSV = (
    "id,amount,status\n"
    "1,100.5,OK\n"
    "2,200.0,OK\n"
    "3,150.30,FAIL\n"
    "4,99.99,OK\n"
    "5,305.0,OK\n"
)


def test_load_table_csv():
    cols, rows = load_table(A_CSV.encode("utf-8"), "a.csv")
    assert cols == ["id", "amount", "status"]
    assert len(rows) == 5
    assert rows[0] == ["1", "100.5", "OK"]


def test_load_table_delimiter_detection():
    data = "a;b;c\n1;2;3\n4;5;6\n"
    cols, rows = load_table(data.encode("utf-8"), "x.csv")
    assert cols == ["a", "b", "c"]
    assert rows[1] == ["4", "5", "6"]


def test_column_stats_numeric():
    s = column_stats(["10", "20", "30", "40", ""])
    assert s["numeric"] is True
    assert s["count"] == 5
    assert s["nulls"] == 1
    assert s["mean"] == 25.0
    assert s["min"] == 10.0
    assert s["max"] == 40.0
    assert s["p50"] == 25.0


def test_column_stats_categorical():
    s = column_stats(["OK", "OK", "FAIL", "OK"])
    assert s["numeric"] is False
    assert s["distinct"] == 2
    top = {d["value"]: d["count"] for d in s["top_values"]}
    assert top["OK"] == 3
    assert top["FAIL"] == 1


def test_compare_identical_is_grade_a():
    cols, rows = load_table(A_CSV.encode("utf-8"), "a.csv")
    rep = compare(cols, rows, cols, [r[:] for r in rows], key="id")
    v = rep["verdict"]
    assert v["grade"] == "A"
    assert v["quality_pct"] == 100.0
    assert v["columns_drift"] == 0
    assert v["only_in_a"] == []
    assert v["only_in_b"] == []
    # Apareo por llave: todas las celdas idénticas.
    kc = rep["key_compare"]
    assert kc["matched_rows"] == 5
    for c in kc["columns"]:
        assert c["match_pct"] == 100.0


def test_compare_within_tolerance_still_ok():
    cA, rA = load_table(A_CSV.encode("utf-8"), "a.csv")
    cB, rB = load_table(B_CSV.encode("utf-8"), "b.csv")
    rep = compare(cA, rA, cB, rB, key="id", tol_pct=5.0)
    # Diferencias chicas: dentro de tolerancia -> sin drift.
    assert rep["verdict"]["columns_drift"] == 0
    assert rep["verdict"]["grade"] == "A"


def test_compare_detects_drift():
    cA, rA = load_table(A_CSV.encode("utf-8"), "a.csv")
    # B con amount muy inflado -> drift en la media.
    big = (
        "id,amount,status\n"
        "1,1000,OK\n2,2000,OK\n3,1500,FAIL\n4,9999,OK\n5,3000,OK\n"
    )
    cB, rB = load_table(big.encode("utf-8"), "b.csv")
    rep = compare(cA, rA, cB, rB, key="id", tol_pct=5.0)
    amount = next(e for e in rep["columns"] if e["column"] == "amount")
    assert amount["status"] == "drift"
    assert rep["verdict"]["columns_drift"] >= 1
    assert rep["verdict"]["grade"] != "A"


def test_compare_only_in_columns():
    cA, rA = load_table("id,x\n1,2\n".encode("utf-8"), "a.csv")
    cB, rB = load_table("id,y\n1,3\n".encode("utf-8"), "b.csv")
    rep = compare(cA, rA, cB, rB)
    assert rep["verdict"]["only_in_a"] == ["x"]
    assert rep["verdict"]["only_in_b"] == ["y"]


def test_report_to_csv_roundtrip():
    cols, rows = load_table(A_CSV.encode("utf-8"), "a.csv")
    rep = compare(cols, rows, cols, [r[:] for r in rows])
    out = report_to_csv(rep)
    reader = list(csv.reader(io.StringIO(out)))
    assert reader[0][0] == "column"
    # una fila de encabezado + una por columna comun (3)
    assert len(reader) == 1 + 3


def test_report_to_html_contains_grade():
    cols, rows = load_table(A_CSV.encode("utf-8"), "a.csv")
    rep = compare(cols, rows, cols, [r[:] for r in rows])
    html = report_to_html(rep, title="T")
    assert "<html" in html.lower()
    assert "amount" in html
    assert rep["verdict"]["grade"] in html


def test_report_is_json_serializable():
    cols, rows = load_table(A_CSV.encode("utf-8"), "a.csv")
    rep = compare(cols, rows, cols, [r[:] for r in rows], key="id")
    # No debe lanzar.
    json.dumps(rep, default=str)
