"""Recursos no Python del proyecto del banco (bin/static/*.xgb, bin/opt/*.sh...) dentro del paquete MLOps v2:
se copian EXACTOS a bank_src/<ruta bajo bin/> y el runner fija BIN_PATH ahi. Sin red."""
import ast
import base64
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src import mlops_pkg as mp  # noqa: E402

JOB = '''
def run(kernel):
    return 1
'''
BIN = bytes(range(256)) * 8 + b"\x00\xff\x00"


def _convert(code):
    return {"ok": True, "code": "df_out = df", "warnings": [], "unsupported": []}


def test_ruta_recurso_clasifica():
    f = mp._ruta_recurso
    assert f("p/bin/static/m.xgb") == "static/m.xgb"
    assert f("p/bin/opt/profile.sh") == "opt/profile.sh"
    assert f("p/bin/static/v2/tabla.csv") == "static/v2/tabla.csv"
    assert f("static/m.pkl") == "static/m.pkl"                      # carpeta subida sin 'bin/'
    assert f("p/bin/settings/spark.json") is None                    # config: va a bank_src/settings
    assert f("p/bin/jobs/rps/score/job.py") is None                  # codigo
    assert f("p/bin/jobs/rps/score/x.json") is None                  # dentro de jobs/
    assert f("p/bin/static/../x.xgb") is None
    assert f("p/bin/static/leeme.exe") is None                       # extension no admitida
    assert f("m.xgb") is None                                        # sin carpeta


def test_paquete_incluye_recursos_exactos_y_reporta(tmp_path):
    fuentes = [
        {"name": "p/bin/jobs/m1/a/job.py", "code": JOB},
        {"name": "p/bin/static/modelo.xgb", "b64": base64.b64encode(BIN).decode()},
        {"name": "p/bin/opt/profile.sh", "code": "export BIN_PATH=$ROOT_LOCAL/bin\n"},
    ]
    out = tmp_path / "p.zip"
    _, _, rep = mp.build_package_from_sources(fuentes, convert_fn=_convert, include_bank_libs=False,
                                              out_path=str(out), py_target="py3.11")
    z = zipfile.ZipFile(out)
    assert z.read("framework_mlops_v2_pkg/bank_src/static/modelo.xgb") == BIN
    assert z.read("framework_mlops_v2_pkg/bank_src/opt/profile.sh").decode().startswith("export BIN_PATH")
    meta = next(r for r in rep if r.get("_meta"))
    assert sorted(r["file"] for r in meta["recursos"]) == ["bank_src/opt/profile.sh", "bank_src/static/modelo.xgb"]
    assert meta["recursos_mb"] >= 0
    assert [r["role"] for r in rep if r.get("file") == "bank_src/static/modelo.xgb"] == ["recurso"]
    # un recurso no es job ni entra al REGISTRY
    router = z.read("framework_mlops_v2_pkg/framework_mlops_v2/aggregates/router.py").decode()
    assert "modelo" not in router


def test_recurso_sobre_el_limite_se_omite_con_motivo(tmp_path):
    fuentes = [
        {"name": "p/bin/jobs/m1/a/job.py", "code": JOB},
        {"name": "p/bin/static/grande.xgb", "b64": base64.b64encode(b"x" * 3 * 1048576).decode()},
    ]
    out = tmp_path / "p.zip"
    _, _, rep = mp.build_package_from_sources(fuentes, convert_fn=_convert, include_bank_libs=False,
                                              out_path=str(out), py_target="py3.11", max_recurso_mb=1)
    assert "framework_mlops_v2_pkg/bank_src/static/grande.xgb" not in zipfile.ZipFile(out).namelist()
    r = next(r for r in rep if r.get("role") == "recurso")
    assert r["ok"] is False and "limite" in r["reason"]


def _bin_path_fn(bank_src):
    """_bin_path_recursos tal como viaja en el main.py generado."""
    tree = ast.parse(mp._MAIN_PY)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_bin_path_recursos")
    ns = {"os": os, "_bank_src": str(bank_src)}
    exec(compile(ast.Module([fn], []), "main.py", "exec"), ns)
    return ns["_bin_path_recursos"]


def test_runner_bin_path_prefiere_bin_del_banco_y_cae_a_bank_src(tmp_path):
    bank_src = tmp_path / "bank_src"
    (bank_src / "static").mkdir(parents=True)
    f = _bin_path_fn(bank_src)
    # --settings fuera del paquete, sin recursos a su lado (p.ej. /bnx_settings en el contenedor: padre '/'):
    sett = tmp_path / "ext" / "settings"
    sett.mkdir(parents=True)
    assert f(str(sett), True) == str(bank_src)
    assert f("/bnx_settings", True) == str(bank_src)      # /opt existe en Linux pero no es el bin/ del banco
    # --settings dentro del bin/ real del banco con static/: manda ese bin/
    (tmp_path / "ext" / "static").mkdir()
    assert f(str(sett), True) == str(tmp_path / "ext")
    # DEMO: bank_src
    assert f(None, False) == str(bank_src)


def test_runner_bin_path_sin_recursos_conserva_comportamiento_previo(tmp_path):
    bank_src = tmp_path / "bank_src"
    bank_src.mkdir()
    f = _bin_path_fn(bank_src)
    sett = tmp_path / "bin" / "settings"
    sett.mkdir(parents=True)
    assert f(str(sett), True) == str(tmp_path / "bin")
    assert f(None, False) == str(bank_src)


def test_tool_leer_fuentes_sube_recursos_y_respeta_limite(tmp_path):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import construir_paquete_mlops as t
    proy = tmp_path / "proy"
    (proy / "bin" / "static").mkdir(parents=True)
    (proy / "bin" / "jobs" / "m" / "a").mkdir(parents=True)
    (proy / "bin" / "static" / "m.xgb").write_bytes(BIN)
    (proy / "bin" / "static" / "grande.pkl").write_bytes(b"x" * 2 * 1048576)
    (proy / "bin" / "jobs" / "m" / "a" / "job.py").write_text(JOB)
    avisos = []
    fs = t.leer_fuentes(str(proy), max_mb=1, avisos=avisos)
    por = {f["name"]: f for f in fs}
    assert base64.b64decode(por["proy/bin/static/m.xgb"]["b64"]) == BIN
    assert "proy/bin/static/grande.pkl" not in por and any("grande.pkl" in a for a in avisos)
    assert "proy/bin/jobs/m/a/job.py" in por
    assert not any("b64" in f for f in t.leer_fuentes(str(proy), con_recursos=False))


def test_main_py_python38():
    ast.parse(mp._MAIN_PY, feature_version=(3, 8))
    ast.parse(open(mp.__file__, encoding="utf-8").read(), feature_version=(3, 8))
