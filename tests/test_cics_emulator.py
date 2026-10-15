# tests/test_cics_emulator.py
"""Tests del emulador CICS: ejecuta el COBOL convertido con trace de flujo y
genera un grafo (Mermaid)."""
from src.direct_transpiler import transpile_direct
from src.cics_emulator import emulate, _mermaid_from_trace


_COBOL = (
    "       IDENTIFICATION DIVISION.\n"
    "       PROGRAM-ID. TX.\n"
    "       ENVIRONMENT DIVISION.\n"
    "       INPUT-OUTPUT SECTION.\n"
    "       FILE-CONTROL.\n"
    "           SELECT CLIENTES ASSIGN TO DISK.\n"
    "       DATA DIVISION.\n"
    "       PROCEDURE DIVISION.\n"
    "       0100-INICIO.\n"
    "           MOVE ZERO TO WS-CONT\n"
    "           PERFORM 0200-VALIDA.\n"
    "       0200-VALIDA.\n"
    "           READ CLIENTES INTO WS-REG INVALID KEY\n"
    "               MOVE 1 TO WS-NOTFOUND\n"
    "           ADD 1 TO WS-CONT.\n"
)


def test_emulate_corre_y_traza():
    code = transpile_direct(_COBOL, "cobol", pure=True)["code"]
    r = emulate(code, _COBOL, "cobol", timeout=30)
    assert r.get("import_ok") is True
    assert r.get("ok") is True
    # Debe haber trazado al menos los parrafos del programa.
    assert r.get("paragraphs_executed", 0) >= 1
    assert "mermaid" in r and r["mermaid"].startswith("flowchart")
    # El orden debe incluir el primer parrafo.
    order = r.get("order", [])
    assert any("0100" in p or "inicio" in p for p in order)


def test_mermaid_from_trace():
    edges = [("START", "p_a"), ("p_a", "p_b"), ("p_b", "p_c")]
    counts = {"p_a": 3, "p_b": 1, "p_c": 1}
    m = _mermaid_from_trace(edges, counts)
    assert m.startswith("flowchart TD")
    assert "-->" in m
    assert "x3" in m  # frecuencia de p_a


def test_emulate_datasets_para_data_sintetica():
    code = transpile_direct(_COBOL, "cobol", pure=True)["code"]
    r = emulate(code, _COBOL, "cobol", timeout=30)
    # Debe exponer los lookups sinteticos (para llevar a Data Sintetica).
    assert "CLIENTES" in (r.get("lookups") or [])
    assert isinstance(r.get("datasets"), dict)
