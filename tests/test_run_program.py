"""Run_Program seguro y opcional: argv sin shell, traduccion a Python portable, omitido por
defecto, variables sin resolver no ejecutan. Se prueba el mismo runtime que se incrusta en
los jobs (src/codegen/params_runtime.py)."""
import ast
import io
import os
import subprocess

import pytest

from src.codegen import params_runtime as rt
from src.codegen.spark_codegen import _emit_os_system


@pytest.fixture
def rp(monkeypatch, tmp_path):
    """Runtime con PARAMS minimo y sin subprocess real (falla si se intenta)."""
    monkeypatch.delenv("BNX_RUN_PROGRAMS", raising=False)
    monkeypatch.delenv("BNX_RUN_PROGRAMS_ESTRICTO", raising=False)
    monkeypatch.delenv("BNX_STRICT_PARAMS", raising=False)
    P = type("PARAMS", (), {"BASE_PATH": str(tmp_path), "AI_BIN": ""})
    monkeypatch.setattr(rt, "PARAMS", P, raising=False)
    rt._BNX_WARNED.clear()
    rt._bnx_resolve_params(P)
    llamadas = []

    def _no(*a, **k):
        llamadas.append(a)
        raise AssertionError("subprocess.run no debia llamarse: %r" % (a,))
    monkeypatch.setattr(subprocess, "run", _no)
    return P, tmp_path, llamadas


def _on(monkeypatch):
    monkeypatch.setenv("BNX_RUN_PROGRAMS", "1")


def test_omitido_por_defecto(rp, capsys):
    P, tmp, _ = rp
    (tmp / "raw").mkdir()
    (tmp / "raw" / "f.dat").write_text("x")
    rc = rt._bnx_run_program(["mv", "$BASE_PATH/raw/f.dat", "$BASE_PATH/f.bak"], "Run_Program")
    assert rc is None
    assert (tmp / "raw" / "f.dat").exists() and not (tmp / "f.bak").exists()
    out = capsys.readouterr().out
    assert "[~] Run_Program Run_Program omitido (activa BNX_RUN_PROGRAMS=1):" in out
    assert str(tmp / "raw" / "f.dat") in out          # comando ya expandido


def test_flag_de_linea_de_comandos(rp, monkeypatch):
    monkeypatch.setattr(rt.sys, "argv", ["job.py", "--run-programs"])
    assert rt._bnx_rp_on()


def test_mv_cp_mkdir_con_shutil_sin_subprocess(rp, monkeypatch, capsys):
    P, tmp, llamadas = rp
    _on(monkeypatch)
    (tmp / "raw").mkdir()
    (tmp / "raw" / "f.dat").write_text("hola")
    assert rt._bnx_run_program(["mkdir", "-p", "$BASE_PATH/backup/sub"], "p") == 0
    assert rt._bnx_run_program(["cp", "$BASE_PATH/raw/f.dat", "$BASE_PATH/backup/copia.dat"], "p") == 0
    assert rt._bnx_run_program(["mv", "$BASE_PATH/raw/f.dat", "$BASE_PATH/backup/sub/f.dat"], "p") == 0
    assert not (tmp / "raw" / "f.dat").exists()
    assert (tmp / "backup" / "sub" / "f.dat").read_text() == "hola"
    assert (tmp / "backup" / "copia.dat").read_text() == "hola"
    assert llamadas == []


def test_touch_rm_cat_gzip(rp, monkeypatch):
    P, tmp, llamadas = rp
    _on(monkeypatch)
    b = "$BASE_PATH"
    assert rt._bnx_run_program(["touch", b + "/a.txt"], "p") == 0
    assert rt._bnx_run_program(["echo", "uno", ">", b + "/b.txt"], "p") == 0
    assert rt._bnx_run_program(["cat", b + "/a.txt", b + "/b.txt", ">", b + "/c.txt"], "p") == 0
    assert (tmp / "c.txt").read_text() == "uno\n"
    assert rt._bnx_run_program(["gzip", b + "/c.txt"], "p") == 0
    assert (tmp / "c.txt.gz").exists() and not (tmp / "c.txt").exists()
    assert rt._bnx_run_program(["gzip", "-d", b + "/c.txt.gz"], "p") == 0
    assert (tmp / "c.txt").read_text() == "uno\n"
    assert rt._bnx_run_program(["rm", "-f", b + "/a.txt", b + "/nada"], "p") == 0
    assert not (tmp / "a.txt").exists()
    assert llamadas == []


def test_rm_rechaza_raiz_y_home(rp, monkeypatch):
    _on(monkeypatch)
    assert rt._bnx_run_program(["rm", "-rf", "/"], "p") == 1
    assert rt._bnx_run_program(["rm", "-rf", os.path.expanduser("~")], "p") == 1


def test_inyeccion_imposible_un_solo_token(rp, monkeypatch):
    P, tmp, llamadas = rp
    _on(monkeypatch)
    monkeypatch.setenv("V_EVIL", "x; touch pwned && rm -rf / | cat")
    rt._bnx_resolve_params(P)
    rt._BNX_RAW["V_EVIL"] = os.environ["V_EVIL"]
    rt._BNX_DONE.clear()
    assert rt._bnx_expand("$V_EVIL") == "x; touch pwned && rm -rf / | cat"
    # el mismo valor, en una plantilla de un comando, sigue siendo UN argumento (nombre de archivo)
    rc = rt._bnx_run_program(["echo", "$V_EVIL", ">", "$BASE_PATH/eco.txt"], "p")
    assert rc == 0
    assert (tmp / "eco.txt").read_text() == "x; touch pwned && rm -rf / | cat\n"
    assert not (tmp / "pwned").exists() and not os.path.exists("pwned")
    assert llamadas == []


def test_valor_con_operadores_no_corta_comandos(rp, monkeypatch):
    P, tmp, _ = rp
    _on(monkeypatch)
    rt._BNX_RAW["EVIL"] = "a ; touch " + str(tmp / "pwned")
    rt._BNX_DONE.clear()
    visto = []
    monkeypatch.setattr(rt, "_bnx_rp_exec", lambda cmd, plant, nombre, extra_env=None: visto.append(cmd) or 0)
    rt._bnx_run_program(["mkdir", "$EVIL"], "p")
    assert visto == [["mkdir", "a ; touch " + str(tmp / "pwned")]]


def test_operadores_de_la_plantilla_si_separan(rp, monkeypatch):
    P, tmp, _ = rp
    _on(monkeypatch)
    rc = rt._bnx_run_program(["mkdir", "$BASE_PATH/x", "&&", "mkdir", "$BASE_PATH/y", ";",
                              "mkdir", "$BASE_PATH/x", "||", "mkdir", "$BASE_PATH/z"], "p")
    assert rc == 0 and (tmp / "y").is_dir() and (tmp / "z").is_dir()


def test_variable_sin_resolver_no_ejecuta(rp, monkeypatch, capsys):
    P, tmp, _ = rp
    _on(monkeypatch)
    (tmp / "raw").mkdir()
    (tmp / "raw" / "$ECS_FILE").write_text("x")
    rc = rt._bnx_run_program(["mv", "$BASE_PATH/raw/$ECS_FILE", "$BASE_PATH/dest"], "Run_Program")
    assert rc is None
    assert (tmp / "raw" / "$ECS_FILE").exists() and not (tmp / "dest").exists()
    out = capsys.readouterr().out
    assert "NO se ejecuta" in out and "$ECS_FILE" in out


def test_variable_vacia_no_ejecuta(rp, monkeypatch, capsys):
    _on(monkeypatch)
    rc = rt._bnx_run_program(["ksh", "-x", "${AI_BIN}/File_validation.ksh"], "Run_Program_1")
    assert rc is None
    assert "NO se ejecuta" in capsys.readouterr().out


def test_ksh_usa_interprete_sin_shell(rp, monkeypatch, tmp_path):
    P, tmp, _ = rp
    _on(monkeypatch)
    script = tmp / "s.ksh"
    script.write_text("echo hola\n")
    visto = {}

    class R:
        returncode = 0

    def _run(argv, shell=False, **kw):
        visto["argv"], visto["shell"] = argv, shell
        return R()
    monkeypatch.setattr(subprocess, "run", _run)
    monkeypatch.setattr(rt, "_bnx_rp_find_shell", lambda name, **k: "/bin/bash")
    rt._bnx_run_program(["ksh", "-x", "$BASE_PATH/s.ksh"], "p")
    assert visto["argv"] == ["/bin/bash", "-x", str(script)] and visto["shell"] is False


def test_ksh_c_con_parametros_se_rechaza(rp, monkeypatch, capsys):
    _on(monkeypatch)
    monkeypatch.setattr(rt, "_bnx_rp_find_shell", lambda name, **k: "/bin/bash")
    rc = rt._bnx_run_program(["bash", "-c", "echo $BASE_PATH"], "p")
    assert rc == 1
    assert "evita inyeccion" in capsys.readouterr().out


def test_windows_sin_bash_se_omite(rp, monkeypatch, capsys):
    P, tmp, llamadas = rp
    _on(monkeypatch)
    assert rt._bnx_rp_find_shell("ksh", nt=True, which=lambda n: None, exists=lambda p: False) is None
    (tmp / "s.ksh").write_text("x")
    monkeypatch.setattr(rt, "_bnx_rp_find_shell", lambda name, **k: None)
    rc = rt._bnx_run_program(["ksh", "$BASE_PATH/s.ksh"], "p")
    assert rc == 0 and llamadas == []
    assert "omitido: no hay interprete ksh" in capsys.readouterr().out


def test_windows_con_git_bash(monkeypatch):
    monkeypatch.setenv("ProgramFiles", r"C:\Program Files")
    git = os.path.join(r"C:\Program Files", "Git\\bin\\bash.exe")
    assert rt._bnx_rp_find_shell("ksh", nt=True, which=lambda n: None, exists=lambda p: p == git) == git
    assert rt._bnx_rp_find_shell("ksh", nt=True, which=lambda n: "C:\\x\\bash.exe") == "C:\\x\\bash.exe"


def test_posix_ksh_cae_a_bash(monkeypatch):
    disp = {"bash": "/bin/bash"}
    assert rt._bnx_rp_find_shell("ksh", nt=False, which=lambda n: disp.get(n)) == "/bin/bash"


def test_codigo_de_retorno_distinto_de_cero(rp, monkeypatch, capsys):
    _on(monkeypatch)
    rc = rt._bnx_run_program(["mv", "$BASE_PATH/no_existe", "$BASE_PATH/otro"], "p")
    assert rc == 1                                    # aviso y sigue
    assert "termino con codigo 1" in capsys.readouterr().out
    monkeypatch.setenv("BNX_RUN_PROGRAMS_ESTRICTO", "1")
    with pytest.raises(RuntimeError):
        rt._bnx_run_program(["mv", "$BASE_PATH/no_existe", "$BASE_PATH/otro"], "p")


def test_pipe_no_soportado_no_usa_shell(rp, monkeypatch, capsys):
    _on(monkeypatch)
    rc = rt._bnx_run_program(["cat", "$BASE_PATH/a", "|", "wc"], "p")
    assert rc == 1 and "no soportado" in capsys.readouterr().out


def test_generador_emite_lista_de_tokens_sin_os_system():
    f = io.StringIO()
    _emit_os_system(f, "mv {PARAMS.BASE_PATH}/raw/{PARAMS.V_FILE} {PARAMS.BASE_PATH}/backup/{PARAMS.V_FILE}.{PARAMS.V_DATE}",
                    "Run_Program")
    linea = f.getvalue().strip()
    assert "os.system" not in linea
    call = ast.parse(linea, feature_version=(3, 8)).body[0].value
    assert call.func.id == "_bnx_run_program"
    assert ast.literal_eval(call.args[0]) == [
        "mv", "${BASE_PATH}/raw/${V_FILE}", "${BASE_PATH}/backup/${V_FILE}.${V_DATE}"]
    assert ast.literal_eval(call.args[1]) == "Run_Program"


def test_generador_solo_interprete_no_emite_llamada():
    f = io.StringIO()
    _emit_os_system(f, "ksh", "RP")
    assert "_bnx_run_program" not in f.getvalue()


def test_runtime_compatible_python38():
    ast.parse(rt.runtime_source(), feature_version=(3, 8))
