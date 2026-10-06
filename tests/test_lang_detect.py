# tests/test_lang_detect.py
from src.lang_detect import detect_language

COBOL = """
       IDENTIFICATION DIVISION.
       PROGRAM-ID. BATCH.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-TOTAL PIC 9(9) COMP-3.
       PROCEDURE DIVISION.
           MOVE 0 TO WS-TOTAL.
           PERFORM READ-RECORD.
           STOP RUN.
"""

ALGOL = """
BEGIN
  FILE IN(KIND=DISK, TITLE="DATA");
  REAL TOTAL;
  INTEGER I;
  PROCEDURE PROCESS;
    BEGIN
      TOTAL := TOTAL + 1;
    END;
  DO PROCESS UNTIL I = 10;
END.
"""

ABINITIO = """
NODE src : SOURCE
NODE t1 : TRANSFORM
NODE snk : SINK
src -> t1
t1 -> snk
"""


def test_detect_cobol_by_extension():
    lang, _ = detect_language(COBOL, filename="prog.cbl")
    assert lang == "cobol"


def test_detect_algol_by_extension():
    lang, _ = detect_language(ALGOL, filename="prog.alg")
    assert lang == "algol"


def test_detect_abinitio_by_extension():
    lang, _ = detect_language(ABINITIO, filename="graph.mp")
    assert lang == "abinitio"


def test_detect_cobol_by_content_no_extension():
    lang, scores = detect_language(COBOL, filename="prog.txt")
    assert lang == "cobol"
    assert scores["cobol"] > scores["algol"]


def test_detect_algol_by_content_no_extension():
    lang, scores = detect_language(ALGOL, filename="prog.txt")
    assert lang == "algol"
    assert scores["algol"] > scores["cobol"]


def test_detect_unknown_on_garbage():
    lang, _ = detect_language("hello world, this is plain prose.", filename="x.txt")
    assert lang == "unknown"


def test_empty_input_is_unknown():
    lang, _ = detect_language("", filename="")
    assert lang == "unknown"
