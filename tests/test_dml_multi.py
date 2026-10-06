# tests/test_dml_multi.py
from src.dml_parser import parse_dml

SINGLE = """keys:
  Customers: customer_id

schema:
  Customers:
    customer_id: int
    name: string
"""

DML_A = """schema:
  Customers:
    customer_id: int
    name: string
keys:
  Customers: customer_id
"""

DML_B = """schema:
  Accounts:
    account_id: int
    balance: decimal
keys:
  Accounts: account_id
"""


def test_single_dml(tmp_path):
    p = tmp_path / "s.dml"
    p.write_text(SINGLE)
    out = parse_dml(str(p))
    assert out["schema"]["Customers"]["customer_id"] == "int"
    assert out["keys"]["Customers"] == "customer_id"


def test_multi_dml_merge(tmp_path):
    combined = f"# === a.dml ===\n{DML_A}\n\n# === b.dml ===\n{DML_B}"
    p = tmp_path / "m.dml"
    p.write_text(combined)
    out = parse_dml(str(p))
    # Ambos nodos presentes (se SUMAN, no gana el ultimo).
    assert "Customers" in out["schema"]
    assert "Accounts" in out["schema"]
    assert out["schema"]["Accounts"]["balance"] == "decimal"
    assert out["keys"]["Customers"] == "customer_id"
    assert out["keys"]["Accounts"] == "account_id"


def test_multi_dml_column_collision_first_wins(tmp_path):
    a = "schema:\n  N:\n    col: int\n"
    b = "schema:\n  N:\n    col: string\n    extra: date\n"
    combined = f"# === a.dml ===\n{a}\n\n# === b.dml ===\n{b}"
    p = tmp_path / "c.dml"
    p.write_text(combined)
    out = parse_dml(str(p))
    # En colision de columna gana el primero; la nueva columna se agrega.
    assert out["schema"]["N"]["col"] == "int"
    assert out["schema"]["N"]["extra"] == "date"
