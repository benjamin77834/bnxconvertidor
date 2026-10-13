# tests/test_direct_pure.py
"""Tests del modo PYTHON PURO del traductor directo (COBOL transaccional CICS).
Verifica: sin Spark, READ->lookup en memoria, funcion procesa_entidad, compila
y corre sin cluster."""
import py_compile

from src.direct_transpiler import transpile_direct


_COBOL_TX = (
    "       IDENTIFICATION DIVISION.\n"
    "       PROGRAM-ID. TX.\n"
    "       ENVIRONMENT DIVISION.\n"
    "       INPUT-OUTPUT SECTION.\n"
    "       FILE-CONTROL.\n"
    "           SELECT SUC-BC ASSIGN TO DISK.\n"
    "       DATA DIVISION.\n"
    "       PROCEDURE DIVISION.\n"
    "       0100-VALIDA.\n"
    "           MOVE ZERO TO SW-NOTFOUND\n"
    "           READ SUC-BC INTO WS-REG-SUC INVALID KEY\n"
    "               MOVE 1 TO SW-NOTFOUND\n"
    "           ADD 1 TO WS-CONTADOR.\n"
)


def test_pure_sin_spark_y_compila(tmp_path):
    out = transpile_direct(_COBOL_TX, "cobol", pure=True)
    code = out["code"]
    assert out["stats"]["mode"] == "pure"
    # Nada de Spark.
    assert "pyspark" not in code
    assert "SparkSession" not in code
    assert "spark.read" not in code
    # Infra de Python puro.
    assert "import pandas as pd" in code
    assert "def load_lookups(" in code
    assert "def procesa_entidad(" in code
    # READ -> lookup en memoria.
    assert "_lookups" in code
    assert "'SUC_BC'" in code
    # ADD 1 -> literal, no ctx['1'].
    assert "ctx['1']" not in code
    assert "+ 1" in code
    # Compila.
    f = tmp_path / "out.py"
    f.write_text(code)
    py_compile.compile(str(f), doraise=True)


def test_pure_procesa_entidad_ejecutable(tmp_path):
    """El modulo generado debe poder importarse y procesar un mensaje sin Spark
    ni CSVs (los lookups quedan vacios -> None, sin romper)."""
    out = transpile_direct(_COBOL_TX, "cobol", pure=True)
    f = tmp_path / "gen_mod.py"
    f.write_text(out["code"])
    import importlib.util
    spec = importlib.util.spec_from_file_location("gen_mod", str(f))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)   # importa (carga lookups vacios: ./data no existe)
    # procesa_entidad corre y devuelve un dict (el ctx o ws_respuesta).
    res = mod.procesa_entidad({"campo1": "x"})
    assert isinstance(res, dict)


def test_spark_mode_sigue_disponible(tmp_path):
    """El modo PySpark (pure=False) debe seguir funcionando para batch."""
    out = transpile_direct(_COBOL_TX, "cobol", pure=False)
    assert out["stats"]["mode"] == "spark"
    assert "SparkSession" in out["code"]
    f = tmp_path / "sp.py"
    f.write_text(out["code"])
    py_compile.compile(str(f), doraise=True)
