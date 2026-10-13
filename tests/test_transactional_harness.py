# tests/test_transactional_harness.py
"""Prueba el harness transaccional: genera lookups + mensajes sinteticos y
ejecuta procesa_entidad del modulo Python puro, reportando si corre."""
from src.direct_transpiler import transpile_direct
from src.transactional_harness import run_transactional_test


_COBOL = (
    "       IDENTIFICATION DIVISION.\n"
    "       PROGRAM-ID. TX.\n"
    "       ENVIRONMENT DIVISION.\n"
    "       INPUT-OUTPUT SECTION.\n"
    "       FILE-CONTROL.\n"
    "           SELECT CLIENTES ASSIGN TO DISK.\n"
    "       DATA DIVISION.\n"
    "       FILE SECTION.\n"
    "       FD  CLIENTES.\n"
    "       01  REG-CLI.\n"
    "           05 CLI-ID      PIC 9(6).\n"
    "           05 CLI-SALDO   PIC 9(7)V99.\n"
    "       PROCEDURE DIVISION.\n"
    "       0100-PROC.\n"
    "           MOVE ZERO TO WS-CONT\n"
    "           READ CLIENTES INTO WS-REG INVALID KEY\n"
    "               MOVE 1 TO WS-NOTFOUND\n"
    "           ADD 1 TO WS-CONT\n"
    "           IF WS-SALDO > 100\n"
    "               MOVE 'A' TO WS-TIPO.\n"
)


def test_harness_corre_y_reporta():
    code = transpile_direct(_COBOL, "cobol", pure=True)["code"]
    rep = run_transactional_test(code, _COBOL, "cobol", num_messages=2, timeout=30)
    assert rep["import_ok"] is True
    assert rep["total"] == 2
    # Debe ejecutar sin excepcion fatal (lookups vacios/sinteticos no rompen).
    assert rep["passed"] == 2
    assert rep["ok"] is True
    # Genero el lookup CLIENTES.
    assert "CLIENTES" in rep["lookups"]


def test_harness_sin_spark():
    """El codigo probado por el harness no debe tener Spark (modo puro)."""
    code = transpile_direct(_COBOL, "cobol", pure=True)["code"]
    assert "pyspark" not in code
    rep = run_transactional_test(code, _COBOL, "cobol", num_messages=1, timeout=30)
    assert rep["ok"] is True
