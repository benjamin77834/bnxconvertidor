# -*- coding: utf-8 -*-
"""Tests (sin red) del cache de vendor: ubicacion, estado, importar ZIP y comandos pip."""
import os
import sys
import zipfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("BNX_NO_DOWNLOAD", "1")

from src import vendor_cache as vc  # noqa: E402


@pytest.fixture(autouse=True)
def _limpio(monkeypatch):
    monkeypatch.delenv("BNX_VENDOR_CACHE", raising=False)
    vc._AVISADO.clear()


def _fake_root(monkeypatch, tmp_path):
    monkeypatch.setattr(vc, "ROOT", str(tmp_path))
    monkeypatch.setattr(sys, "prefix", str(tmp_path / ".venv"))
    monkeypatch.setattr(sys, "base_prefix", "/usr")
    return tmp_path


def test_cache_dir_env(monkeypatch, tmp_path):
    monkeypatch.setenv("BNX_VENDOR_CACHE", str(tmp_path / "x"))
    assert vc.cache_dir() == str(tmp_path / "x")


def test_cache_dir_venv_del_proyecto(monkeypatch, tmp_path):
    _fake_root(monkeypatch, tmp_path)
    assert vc.cache_dir() == str(tmp_path / ".venv" / "bnx_vendor_cache")


def test_cache_dir_sin_venv_activo_usa_root_venv(monkeypatch, tmp_path):
    monkeypatch.setattr(vc, "ROOT", str(tmp_path))
    monkeypatch.setattr(sys, "prefix", "/usr")
    monkeypatch.setattr(sys, "base_prefix", "/usr")
    assert vc.cache_dir() == str(tmp_path / ".venv" / "bnx_vendor_cache")


def test_cache_dir_fallback_viejo_y_aviso(monkeypatch, tmp_path, capsys):
    _fake_root(monkeypatch, tmp_path)
    (tmp_path / ".bnx_vendor_cache").mkdir()
    assert vc.cache_dir() == str(tmp_path / ".bnx_vendor_cache")
    assert "mv " in capsys.readouterr().err
    # si ya existe el nuevo, gana el nuevo
    (tmp_path / ".venv" / "bnx_vendor_cache").mkdir(parents=True)
    assert vc.cache_dir() == str(tmp_path / ".venv" / "bnx_vendor_cache")


def _zip(path, nombres):
    with zipfile.ZipFile(path, "w") as z:
        for n in nombres:
            z.writestr(n, "x")


def test_importar_extrae_a_cache_dir(tmp_path):
    z = tmp_path / "v.zip"
    _zip(z, [".bnx_vendor_cache/py38-311/a.whl", ".bnx_vendor_cache/bank_libs/wheels/m.tar.gz",
             "importar_vendor.py"])
    dest = tmp_path / "cache"
    n, _ = vc.importar_zip(str(z), log=lambda *_: None, cache=str(dest))
    assert n == 2
    assert (dest / "py38-311" / "a.whl").is_file()
    assert (dest / "bank_libs" / "wheels" / "m.tar.gz").is_file()


@pytest.mark.parametrize("malo", [".bnx_vendor_cache/../../evil.txt", "otra/ruta.txt",
                                  "/abs/evil.txt", ".bnx_vendor_cache/a\\..\\b"])
def test_importar_rechaza_path_traversal(tmp_path, malo):
    z = tmp_path / "v.zip"
    _zip(z, [".bnx_vendor_cache/ok.whl", malo])
    dest = tmp_path / "cache"
    with pytest.raises(ValueError):
        vc.importar_zip(str(z), log=lambda *_: None, cache=str(dest))
    assert not (dest / "ok.whl").exists()          # no extrae nada si hay una mala
    assert not (tmp_path / "evil.txt").exists()


def test_estado_reporta_faltantes_en_cache_vacio(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("BNX_VENDOR_CACHE", str(tmp_path / "vacio"))
    import preparar_vendor
    # evitar pip real: sin wheels y sin red el resolvedor reportaria igual; lo simulamos
    from src import mlops_pkg as mp
    monkeypatch.setattr(mp, "_seleccionar_wheels",
                        lambda *a, **k: ([], {"3.8": "Could not find pandas"}))
    rc = preparar_vendor.main(["--estado", "--json", "--python", "3.8"])
    assert rc == 3
    import json
    d = json.loads(capsys.readouterr().out)
    e = d["versiones"]["3.8"]
    assert not e["ok"] and not e["pyspark"] and not e["py4j"]
    assert "pyspark==3.5.6" in e["falta"] and e["bank_falta"]


def test_estado_completo(monkeypatch, tmp_path):
    monkeypatch.setenv("BNX_VENDOR_CACHE", str(tmp_path))
    s = tmp_path / "py312plus"
    s.mkdir()
    (s / "pyspark-4.0.0-py2.py3-none-any.whl").write_text("x")
    (s / "py4j-0.10.9.9-py2.py3-none-any.whl").write_text("x")
    from src import mlops_pkg as mp
    monkeypatch.setattr(mp, "_seleccionar_wheels", lambda *a, **k: ([], {}))
    e = vc.estado_version("3.12")
    assert e["ok"] and e["serie"] == "py312plus"


def test_comandos_pip_pyspark():
    d = vc.cmd_pyspark_download("py38-311", "/d")
    assert d[1:3] == ["-m", "pip"] and "download" in d and "--no-deps" in d
    assert d[d.index("--no-binary") + 1] == ":all:" and "pyspark==3.5.6" in d
    assert "pyspark==4.0.0" in vc.cmd_pyspark_download("py312plus", "/d")
    w = vc.cmd_pyspark_wheel("/d/pyspark.tar.gz", "/d")
    assert "wheel" in w and "--no-deps" in w and w[-2:] == ["-w", "/d"]
    p = vc.cmd_py4j("py312plus", "/d")
    assert "py4j==0.10.9.9" in p and "--only-binary" in p


def test_preparar_version_arma_comandos(monkeypatch, tmp_path):
    from src import mlops_pkg as mp
    llamadas = []

    def fake_run(cmd, capture_output=True, text=True, timeout=0):
        llamadas.append(cmd)

        class R:
            returncode, stdout, stderr = 0, "", ""
        if "download" in cmd and "--no-binary" in cmd:
            open(os.path.join(cmd[cmd.index("-d") + 1], "pyspark-4.0.0.tar.gz"), "w").close()
        if "wheel" in cmd:
            open(os.path.join(cmd[cmd.index("-w") + 1], "pyspark-4.0.0-py2.py3-none-any.whl"), "w").close()
        if "py4j==0.10.9.9" in cmd:
            open(os.path.join(cmd[cmd.index("-d") + 1], "py4j-0.10.9.9-py2.py3-none-any.whl"), "w").close()
        return R()
    monkeypatch.setattr(vc.subprocess, "run", fake_run)
    monkeypatch.setattr(mp, "_seleccionar_wheels", lambda *a, **k: ([], {}))
    est = vc.preparar_version("3.12", log=lambda *_: None, cache=str(tmp_path))
    assert est["ok"]
    assert len(llamadas) == 3                                   # py4j, sdist, wheel
    assert not (tmp_path / "py312plus" / "pyspark-4.0.0.tar.gz").exists()   # sdist borrado
    # idempotente: segunda vez no llama a pip
    llamadas.clear()
    vc.preparar_version("3.12", log=lambda *_: None, cache=str(tmp_path))
    assert llamadas == []


# ---- minimo / podar / librerias del banco ----
def _cache_falso(tmp_path):
    for rel in ("py38-311/pyspark-3.5.6-py2.py3-none-any.whl", "py38-311/sobra-1.0-py3-none-any.whl",
                "mlops_deps/py38-311_dl/numpy-1-cp39-cp39-x.whl", "mlops_deps/py38-311/util-1-py3-none-any.whl",
                "bank_libs/wheels/mex-libextract-2.2.0.tar.gz", "bank_libs/wheels/otra-1-py3-none-any.whl",
                "bank_libs/pkgcode/toolbox/kernel.py"):
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x")
    return tmp_path


def test_podar_borra_solo_lo_que_no_es_minimo(monkeypatch, tmp_path):
    c = _cache_falso(tmp_path)
    monkeypatch.setenv("BNX_VENDOR_CACHE", str(c))
    keep = {os.path.realpath(c / "py38-311/pyspark-3.5.6-py2.py3-none-any.whl"),
            os.path.realpath(c / "mlops_deps/py38-311/util-1-py3-none-any.whl")}
    monkeypatch.setattr(vc, "minimo", lambda versiones, extra=False: (keep, {}))
    lista, _ = vc.sobrantes(["3.8"], cache=str(c))
    nombres = {os.path.basename(f) for f, _n in lista}
    assert nombres == {"sobra-1.0-py3-none-any.whl", "numpy-1-cp39-cp39-x.whl", "otra-1-py3-none-any.whl"}
    assert vc.podar(["3.8"], aplicar=False, log=lambda *_: None, cache=str(c)) == (0, 0)   # dry-run
    assert (c / "py38-311/sobra-1.0-py3-none-any.whl").exists()
    assert vc.podar(["3.8"], aplicar=True, confirmar=lambda: False, log=lambda *_: None, cache=str(c)) == (0, 0)
    n, _b = vc.podar(["3.8"], aplicar=True, confirmar=lambda: True, log=lambda *_: None, cache=str(c))
    assert n == 3 and not (c / "mlops_deps/py38-311_dl").exists()
    assert (c / "bank_libs/wheels/mex-libextract-2.2.0.tar.gz").exists()      # sdist del banco intacto
    assert (c / "bank_libs/pkgcode/toolbox/kernel.py").exists()


def test_podar_no_borra_si_el_minimo_esta_incompleto(monkeypatch, tmp_path):
    c = _cache_falso(tmp_path)
    monkeypatch.setenv("BNX_VENDOR_CACHE", str(c))
    monkeypatch.setattr(vc, "minimo", lambda versiones, extra=False: (set(), {"3.8": "Could not find x"}))
    assert vc.podar(["3.8"], aplicar=True, confirmar=lambda: True, log=lambda *_: None, cache=str(c)) == (0, 0)
    assert (c / "py38-311/sobra-1.0-py3-none-any.whl").exists()


def test_importar_bank_libs_carpeta_y_estado(monkeypatch, tmp_path):
    dest = tmp_path / "cache"
    monkeypatch.setenv("BNX_VENDOR_CACHE", str(dest))
    src = tmp_path / "banco"
    (src / "toolbox").mkdir(parents=True)
    (src / "toolbox" / "kernel.py").write_text("x = 1")
    (src / "mex-libextract-2.2.0.tar.gz").write_text("x")
    sd, mods = vc.importar_bank_libs(str(src), log=lambda *_: None, cache=str(dest))
    assert sd == ["mex-libextract-2.2.0.tar.gz"] and mods == ["toolbox"]
    b = vc.estado_banco(str(dest))
    assert b["sdists"] == ["mex-libextract"] and "mex-libgroupby" in b["sdists_faltan"]
    assert b["pkgcode"] == ["toolbox"] and set(b["pkgcode_faltan"]) == {"bnmxverse", "utils"}


def test_desde_github_rechaza_sha_distinto(tmp_path, monkeypatch):
    """sha256 distinto al de SHA256SUMS -> no se importa nada."""
    import zipfile as zf
    from src import vendor_cache as vc
    z = tmp_path / "a.zip"
    with zf.ZipFile(z, "w") as f:
        f.writestr(".bnx_vendor_cache/py38-311/x.whl", "x")

    def fake(url, destino=None, log=print, timeout=60):
        if url.endswith("SHA256SUMS"):
            return b"0" * 64 + b"  bnx_vendor_linux_py3.8.zip\n"
        open(destino, "wb").write(z.read_bytes())
        return "1" * 64
    monkeypatch.setattr(vc, "_http_get", fake)
    cache = tmp_path / "c"
    assert vc.desde_github("3.8", cache=str(cache), log=lambda *_: None) is False
    assert not (cache / "py38-311" / "x.whl").exists()


def test_desde_github_importa_con_sha_ok(tmp_path, monkeypatch):
    import hashlib
    import zipfile as zf
    from src import vendor_cache as vc
    z = tmp_path / "a.zip"
    with zf.ZipFile(z, "w") as f:
        f.writestr(".bnx_vendor_cache/py38-311/x.whl", "x")
    sha = hashlib.sha256(z.read_bytes()).hexdigest()

    def fake(url, destino=None, log=print, timeout=60):
        if url.endswith("SHA256SUMS"):
            return (sha + "  bnx_vendor_linux_py3.8.zip\n").encode()
        open(destino, "wb").write(z.read_bytes())
        return sha
    monkeypatch.setattr(vc, "_http_get", fake)
    cache = tmp_path / "c"
    assert vc.desde_github("3.8", cache=str(cache), log=lambda *_: None) is True
    assert (cache / "py38-311" / "x.whl").exists()
