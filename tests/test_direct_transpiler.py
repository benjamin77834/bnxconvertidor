# tests/test_direct_transpiler.py
"""Tests del traductor DIRECTO fuente -> PySpark (sin grafo) para COBOL/ALGOL
grandes. El objetivo es que SIEMPRE compile y capture las operaciones de datos
(MOVE/:=, COMPUTE, PERFORM, llamadas), sin TODOs que rompan."""
import py_compile

from src.direct_transpiler import transpile_direct


def _compiles(code, tmp_path):
    f = tmp_path / "out.py"
    f.write_text(code)
    py_compile.compile(str(f), doraise=True)  # lanza si no compila
    return True


def test_cobol_directo_compila_y_captura(tmp_path):
    cobol = (
        "       IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. SAMP.\n"
        "       ENVIRONMENT DIVISION.\n"
        "       INPUT-OUTPUT SECTION.\n"
        "       FILE-CONTROL.\n"
        "           SELECT CLIENTES ASSIGN TO DISK.\n"
        "       PROCEDURE DIVISION.\n"
        "       0100-INICIO.\n"
        "           MOVE ZERO TO WS-TOTAL\n"
        "           MOVE 'A' TO WS-TIPO\n"
        "           PERFORM 0200-CALCULA.\n"
        "       0200-CALCULA.\n"
        "           COMPUTE WS-TOTAL = WS-A + WS-B\n"
        "           IF WS-TOTAL > 100\n"
        "               MOVE 1 TO WS-FLAG\n"
        "           END-IF.\n"
    )
    out = transpile_direct(cobol, "cobol")
    code = out["code"]
    assert _compiles(code, tmp_path)
    # Funciones por parrafo (0100 -> prefijo p_ por empezar con digito).
    assert "def p_0100_inicio(ctx):" in code
    assert "def p_0200_calcula(ctx):" in code
    # Asignaciones MOVE traducidas sobre ctx.
    assert "ctx['ws_total'] = 0" in code
    assert "ctx['ws_tipo'] = 'A'" in code
    # COMPUTE -> expresion con coercion numerica tolerante (_n evita str-str).
    assert "ctx['ws_total'] = _n(ctx['ws_a']) + _n(ctx['ws_b'])" in code
    # PERFORM -> llamada a la funcion.
    assert "p_0200_calcula(ctx)" in code
    # Lectura del archivo de entrada.
    assert "clientes.csv" in code
    assert out["stats"]["assigns"] >= 3


def test_algol_directo_compila(tmp_path):
    algol = (
        " $SET SHARING = PRIVATE\n"
        " BEGIN\n"
        "   FILE CLIENTES (KIND=DISK);\n"
        "   INTEGER PROCEDURE VALIDA;\n"
        "   BEGIN\n"
        "     RESULTADO := 0;\n"
        "     NOMBRE := \"JUAN\";\n"
        "     IF EDAD GTR 18 THEN ADULTO := 1;\n"
        "   END;\n"
        " END.\n"
    )
    out = transpile_direct(algol, "algol")
    code = out["code"]
    assert _compiles(code, tmp_path)
    assert "def valida(ctx):" in code
    assert "ctx['resultado'] = 0" in code
    assert "ctx['nombre'] = 'JUAN'" in code


def test_directo_nunca_emite_todo_no_traducible(tmp_path):
    """El traductor NO debe emitir 'TODO: no traducible' que rompa; lo complejo
    va como comentario de guia y el modulo igual compila."""
    cobol = (
        "       PROCEDURE DIVISION.\n"
        "       0100-X.\n"
        "           MOVE TABLA(IDX) TO SALIDA\n"      # subindice: no soportado
        "           STRING A B DELIMITED BY SIZE INTO C\n"  # STRING: no soportado
        "           MOVE 5 TO WS-OK.\n"
    )
    out = transpile_direct(cobol, "cobol")
    code = out["code"]
    assert _compiles(code, tmp_path)
    # Lo soportado SI se traduce.
    assert "ctx['ws_ok'] = 5" in code
    # Lo no soportado queda como comentario, no como codigo roto.
    assert "no traducible" not in code.lower()
