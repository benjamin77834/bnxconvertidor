"""Expansion de parametros Ab Initio (${X}, $X, $[PDL]) en los jobs generados.

El runtime vive en src/codegen/params_runtime.py y se incrusta tal cual en cada job
(Spark y Glue). Aqui se prueba el mismo codigo que corre en el job, sin Spark.
"""
import io
import os
import py_compile
import subprocess
import sys

import pytest

from src.codegen import params_runtime as rt
from src.codegen.spark_codegen import _emit_filter_pair

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _params(monkeypatch, **vals):
    """Instala una clase PARAMS en el runtime y la resuelve (como hace el job)."""
    monkeypatch.delenv("BNX_STRICT_PARAMS", raising=False)
    P = type("PARAMS", (), dict(vals))
    monkeypatch.setattr(rt, "PARAMS", P, raising=False)
    rt._BNX_WARNED.clear()
    rt._bnx_resolve_params(P)
    return P


def test_expande_llaves_y_simple(monkeypatch):
    _params(monkeypatch, A="uno", B="dos")
    assert rt._bnx_expand("x=${A} y=$B") == "x=uno y=dos"
    # limite de identificador: $B_X es otro nombre y $B/ si es B
    assert rt._bnx_expand("$B/z") == "dos/z"
    assert rt._bnx_expand("${A}_${B}") == "uno_dos"


def test_no_toca_dolar_que_no_es_parametro(monkeypatch):
    _params(monkeypatch, A="uno")
    # $1 (grupo de regex), $ final y $x desconocido se dejan tal cual
    assert rt._bnx_expand("regexp_replace(c,'(a)','$1')") == "regexp_replace(c,'(a)','$1')"
    assert rt._bnx_expand("'^abc$'") == "'^abc$'"
    assert rt._bnx_expand("$nadie") == "$nadie"


def test_anidado(monkeypatch):
    P = _params(monkeypatch, OUT_PATH_FILE="/data/out", OUTPUT_NAME="f.txt",
                OUTPUT_FILE="$OUT_PATH_FILE/$OUTPUT_NAME", OUT2="${OUTPUT_FILE}.bak")
    assert P.OUTPUT_FILE == "/data/out/f.txt"
    assert P.OUT2 == "/data/out/f.txt.bak"


def test_ciclo_no_cuelga(monkeypatch, capsys):
    P = _params(monkeypatch, A="$B", B="$A")
    assert isinstance(P.A, str) and isinstance(P.B, str)
    assert "circular" in capsys.readouterr().out


def test_profundidad_limitada(monkeypatch):
    vals = {"P%d" % i: "$P%d" % (i + 1) for i in range(40)}
    vals["P40"] = "fin"
    P = _params(monkeypatch, **vals)
    assert isinstance(P.P0, str)  # no RecursionError; termina


def test_ai_sin_valor_se_deja_y_avisa(monkeypatch, capsys):
    monkeypatch.delenv("AI_DML", raising=False)
    _params(monkeypatch, PATH_DML="$AI_DML/x")
    assert rt._bnx_expand("${PATH_DML}") == "$AI_DML/x"
    assert "$AI_DML" in capsys.readouterr().out


def test_env_gana_sobre_default(monkeypatch):
    monkeypatch.setenv("FROM_ENV", "desde-env")
    _params(monkeypatch)
    assert rt._bnx_expand("${FROM_ENV}") == "desde-env"


def test_pdl_flag_if_is_blank(monkeypatch):
    pdl = '$[if( (is_blank(FILTER_BY_EXP)) or (FILTER_BY_EXP == "0")) 0 else 1]'
    P = _params(monkeypatch, FILTER_BY_EXP="", FILTER_BY_EXP_FLAG=pdl)
    assert P.FILTER_BY_EXP_FLAG == "0"
    P = _params(monkeypatch, FILTER_BY_EXP="amount > 0", FILTER_BY_EXP_FLAG=pdl)
    assert P.FILTER_BY_EXP_FLAG == "1"
    P = _params(monkeypatch, FILTER_BY_EXP="0", FILTER_BY_EXP_FLAG=pdl)
    assert P.FILTER_BY_EXP_FLAG == "0"


def test_pdl_orden_de_dependencias(monkeypatch):
    # B depende de A y A se declara despues: se resuelve igual
    P = _params(monkeypatch, B="$[A + '-x']", A="$[string_upcase('ab')]")
    assert P.A == "AB" and P.B == "AB-x"


def test_pdl_fecha(monkeypatch):
    P = _params(monkeypatch, TS='$[(datetime("YYYYMMDDTHH24MISS"))now1()]',
                D="$[(date('YYYYMMDD'))datetime_add(now1(),0)]")
    assert len(P.TS) == 15 and P.TS[8] == "T"
    assert len(P.D) == 8 and P.D.isdigit()


def test_pdl_no_soportado_loggea_y_deja_vacio(monkeypatch, capsys):
    P = _params(monkeypatch, X="$[get_vec_split(CONF,2)]")
    assert P.X == ""
    assert "[!] PDL no resuelto: X" in capsys.readouterr().out


def test_pdl_no_usa_eval(monkeypatch, tmp_path, capsys):
    import re
    assert not re.search(r"(?<![\w.])(eval|exec|compile|__import__)\(", rt.runtime_source())
    marca = tmp_path / "pwned"
    P = _params(monkeypatch, X="$[__import__('os').system('touch %s')]" % marca,
                Y="$[open('%s','w')]" % marca)
    assert not marca.exists()
    assert P.X == "" and P.Y == ""


class _DF:
    """DataFrame de mentira: registra los where."""
    def __init__(self, wheres=None):
        self.wheres = wheres or []

    def where(self, c):
        return _DF(self.wheres + [c])

    def limit(self, n):
        return _DF(self.wheres + ["LIMIT %d" % n])


def test_filter_vacio_pass_through(monkeypatch, capsys):
    pdl = '$[if( (is_blank(FILTER_BY_EXP)) or (FILTER_BY_EXP == "0")) 0 else 1]'
    _params(monkeypatch, FILTER_BY_EXP="", FILTER_BY_EXP_FLAG=pdl)
    df = _DF()
    main, rej = rt._bnx_filter_split(df, "(${FILTER_BY_EXP}) <> 0", "Filter_by_Expression")
    assert main is df and rej.wheres == ["LIMIT 0"]
    assert ("[~] Filter_by_Expression deshabilitado: FILTER_BY_EXP vacio "
            "(pass-through como Ab Initio)") in capsys.readouterr().out


def test_filter_con_valor_filtra(monkeypatch):
    _params(monkeypatch, FILTER_BY_EXP="amount > 0", FILTER_BY_EXP_FLAG="1")
    main, rej = rt._bnx_filter_split(_DF(), "(${FILTER_BY_EXP}) <> 0", "F")
    assert main.wheres == ["(amount > 0) <> 0"]
    assert rej.wheres == ["NOT ((amount > 0) <> 0)"]


def test_filter_flag_cero_pass_through(monkeypatch):
    _params(monkeypatch, FILTER_BY_EXP="amount > 0", FILTER_BY_EXP_FLAG="0")
    df = _DF()
    main, rej = rt._bnx_filter_split(df, "(${FILTER_BY_EXP}) <> 0", "F")
    assert main is df


def test_filter_strict_error_claro(monkeypatch):
    _params(monkeypatch, FILTER_BY_EXP="")
    monkeypatch.setenv("BNX_STRICT_PARAMS", "1")
    with pytest.raises(RuntimeError) as e:
        rt._bnx_filter_split(_DF(), "(${FILTER_BY_EXP}) <> 0", "Filter_by_Expression")
    assert "Parámetro FILTER_BY_EXP vacío en Filter_by_Expression".replace("á", "a").replace("í", "i") in str(e.value)
    assert "definelo en el pset o como variable de entorno" in str(e.value)


def test_codegen_filtro_con_parametro_usa_helper():
    f = io.StringIO()
    _emit_filter_pair(f, "F1", "Src_df", "(${P}) <> 0", "F1")
    txt = f.getvalue()
    assert '_bnx_filter_split(Src_df, "(${P}) <> 0", "F1")' in txt
    f = io.StringIO()
    _emit_filter_pair(f, "F1", "Src_df", "a > 0", "F1")
    assert "_bnx_filter_split" not in f.getvalue() and 'Src_df.where("a > 0")' in f.getvalue()


def test_runtime_emitido_compila(tmp_path):
    f = io.StringIO()
    f.write("import os\nfrom pyspark.sql import functions as F\nspark = None\n")
    f.write('class PARAMS:\n    A = os.environ.get("A", "x")\n\n')
    rt.emit_params_runtime(f)
    p = tmp_path / "job.py"
    p.write_text(f.getvalue(), encoding="utf-8")
    py_compile.compile(str(p), doraise=True)
    assert "_bnx_resolve_params(PARAMS)" in f.getvalue()


@pytest.mark.skipif(not os.path.isdir(os.path.join(ROOT, "abinitio", "ejercicio_3_planes")),
                    reason="falta abinitio/ejercicio_3_planes")
@pytest.mark.parametrize("target", ["spark", "glue"])
def test_job_generado_compila_y_trae_runtime(tmp_path, target):
    d = os.path.join(ROOT, "abinitio", "ejercicio_3_planes")
    out = tmp_path / "job.py"
    r = subprocess.run([sys.executable, os.path.join(ROOT, "main.py"), "--project",
                        os.path.join(d, "filtra_transacciones.mp"), "--pset",
                        os.path.join(d, "filtra_transacciones.pset"), "--output", str(out),
                        "--target", target], cwd=ROOT, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    assert r.returncode == 0, r.stderr[-500:]
    py_compile.compile(str(out), doraise=True)
    code = out.read_text(encoding="utf-8")
    assert "def _bnx_expand(" in code and "_bnx_resolve_params(PARAMS)" in code


def test_llaves_escapadas_del_gde(monkeypatch):
    _params(monkeypatch, DIR="/d", BOOK_DATE="20260101")
    assert rt._bnx_expand(r"$\{DIR\}/x/$\{BOOK_DATE\}/f.dat") == "/d/x/20260101/f.dat"


def test_runtime_no_usa_builtins_pisados_por_pyspark():
    # el job hace `from pyspark.sql.functions import *`, que pisa max/min/sum/round/abs...
    import builtins
    import re
    pytest.importorskip("pyspark")
    from pyspark.sql import functions as F
    usados = set(re.findall(r"(?<![\w.])([A-Za-z_]\w*)\(", rt.runtime_source()))
    assert sorted(u for u in usados if hasattr(builtins, u) and u in F.__all__) == []


def test_pdl_substring(monkeypatch):
    P = _params(monkeypatch, S="$[string_substring('abcdef', 2, 3)]")
    assert P.S == "bcd"


@pytest.mark.skipif(__import__("importlib").util.find_spec("pyspark") is None, reason="sin pyspark")
def test_spark_real_expande_antes_del_parser(tmp_path):
    """Con Spark real (en subproceso, porque parchea clases de pyspark): where/groupBy/expr
    reciben las expresiones ya expandidas y Spark ya no blanquea ${X}."""
    f = io.StringIO()
    f.write("import os\nfrom pyspark.sql import SparkSession\nfrom pyspark.sql import functions as F\n"
            "from pyspark.sql.functions import *\n"
            "spark = SparkSession.builder.master('local[1]').config('spark.ui.enabled','false').getOrCreate()\n"
            "class PARAMS:\n    LIM = '1'\n    KEY = 'g'\n    COND = '$KEY > ${LIM}'\n    FILTER_BY_EXP = ''\n")
    rt.emit_params_runtime(f)
    f.write("df = spark.createDataFrame([(0,'a'),(1,'b'),(2,'c')], ['id','g'])\n"
            "print('WHERE', df.where('id > ${LIM}').count())\n"
            "print('EXPR', df.withColumn('x', expr('id + ${LIM}')).agg(F.sum('x')).first()[0])\n"
            "print('GROUP', df.groupBy('$KEY').count().count())\n"
            "m, r = _bnx_filter_split(df, '(${FILTER_BY_EXP}) <> 0', 'Filtro')\n"
            "print('PASS', m.count(), r.count())\n"
            "try:\n    df.groupBy('${FILTER_BY_EXP}')\nexcept RuntimeError as e:\n    print('KEYERR', 'FILTER_BY_EXP' in str(e), 'groupBy' in str(e))\n"
            "try:\n    df.where('(${FILTER_BY_EXP}) <> 0')\n"
            "except Exception as e:\n    print('ERR', type(e).__name__, 'FILTER_BY_EXP' in str(e))\n"
            "spark.stop()\n")
    p = tmp_path / "job.py"
    p.write_text(f.getvalue(), encoding="utf-8")
    r = subprocess.run([sys.executable, str(p)], capture_output=True, text=True, cwd=str(tmp_path),
                       stdin=subprocess.DEVNULL, timeout=180)
    out = r.stdout
    assert r.returncode == 0, r.stderr[-800:]
    assert "WHERE 1" in out and "EXPR 6" in out and "GROUP 3" in out
    assert "PASS 3 0" in out and "deshabilitado" in out
    assert "KEYERR True True" in out  # clave vacia: error claro, no UNRESOLVED_COLUMN ``
    assert "ERR RuntimeError True" in out  # error claro con el nombre del parametro
