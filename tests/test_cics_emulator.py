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


# ALGOL: regresion del flujo Mermaid. Antes los PROCEDURE no se trazaban (nombres
# sin prefijo 'p_') y el programa principal se metia dentro del ultimo PROCEDURE,
# causando recursion (conteos absurdos). Ahora cada proc se ejecuta 1 vez y el
# flujo sale de un parrafo '_bnx_main'.
_ALGOL = (
    "BEGIN\n"
    "  COMMENT batch ALGOL de prueba;\n"
    "  FILE CARDTX (KIND=DISK);\n"
    "  REAL TOTAL;\n"
    "  PROCEDURE READ_TX;\n"
    "  BEGIN\n"
    "    READ (CARDTX, REC);\n"
    "  END;\n"
    "  PROCEDURE COMPUTE_TOTAL;\n"
    "  BEGIN\n"
    "    TOTAL := TOTAL + 1;\n"
    "  END;\n"
    "  PROCEDURE WRITE_OUT;\n"
    "  BEGIN\n"
    "    WRITE (CARDTX, REC);\n"
    "  END;\n"
    "  COMMENT Programa principal;\n"
    "  READ_TX;\n"
    "  COMPUTE_TOTAL;\n"
    "  WRITE_OUT;\n"
    "END.\n"
)


def test_emulate_algol_traza_flujo():
    code = transpile_direct(_ALGOL, "algol", pure=True)["code"]
    r = emulate(code, _ALGOL, "algol", timeout=30)
    assert r.get("ok") is True
    counts = r.get("counts", {})
    # Los tres PROCEDURE deben trazarse y ejecutarse EXACTAMENTE 1 vez (sin
    # recursion). Antes del fix: no aparecian o tenian conteos de miles.
    for proc in ("read_tx", "compute_total", "write_out"):
        assert counts.get(proc) == 1, f"{proc} deberia ejecutarse 1 vez, conteo={counts.get(proc)}"
    # El Mermaid debe tener nodos reales (no 'Sin trace').
    m = r.get("mermaid", "")
    assert m.startswith("flowchart") and "Sin trace" not in m
    assert "-->" in m


def test_algol_programa_principal_no_recursa():
    # El ultimo PROCEDURE NO debe contener las llamadas del programa principal
    # (bug que causaba write_out -> read_tx -> ... recursivo).
    code = transpile_direct(_ALGOL, "algol", pure=True)["code"]
    import re
    m = re.search(r"def write_out\(ctx\):(.*?)(?=\ndef |\Z)", code, re.S)
    assert m is not None
    body = m.group(1)
    assert "read_tx(ctx)" not in body
    assert "write_out(ctx)" not in body  # sin auto-llamada
    # Debe existir el parrafo del programa principal con las 3 llamadas.
    assert "def _bnx_main(ctx):" in code
