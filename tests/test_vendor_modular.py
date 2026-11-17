"""Vendor modular (pyspark / ciencia / banco) sin red: release falso en carpeta (OrigenDir)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import vendor_cache as vc  # noqa: E402
from src import vendor_modular as vm  # noqa: E402


def _whl(d, nombre):
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, nombre)
    with open(p, "wb") as fh:
        fh.write(b"PK-falso-" + nombre.encode())
    return p


@pytest.fixture
def release(tmp_path):
    """Release falso con pyspark 3.11 y ciencia linux/windows 3.11."""
    src = tmp_path / "src"
    out = tmp_path / "rel"
    serie = vc.serie_de("3.11")
    info = vc.SERIES[serie]
    man = {"formato": 3, "tag": "vendor-v3", "piezas": []}
    out.mkdir()

    def pieza(nombre, py, plat, entradas):
        arch = vm.archivo_pieza(nombre, py, plat)
        b, sha = vm.empaquetar_zip(str(out / arch), entradas)
        man["piezas"].append({"nombre": nombre, "python": py, "plataforma": "any" if nombre == "pyspark" else plat,
                              "archivo": arch, "bytes": b, "sha256": sha, "contenido": [], "huecos": []})
    w1 = _whl(str(src), "pyspark-%s-py2.py3-none-any.whl" % info["pyspark"])
    w2 = _whl(str(src), "py4j-%s-py2.py3-none-any.whl" % info["py4j"])
    pieza("pyspark", "3.11", "any", [("pyspark/%s/%s" % (serie, os.path.basename(w)), w) for w in (w1, w2)])
    for plat, tag in (("linux", "manylinux2014_x86_64"), ("windows", "win_amd64")):
        w = _whl(str(src / plat), "numpy-2.0.0-cp311-cp311-%s.whl" % tag)
        pieza("ciencia", "3.11", plat, [("ciencia/3.11/%s/%s" % (plat, os.path.basename(w)), w)])
    vm.escribir_manifiesto_release(str(out), man)
    return str(out)


def test_parse_plataformas():
    assert vm.parse_plataformas("linux, win mac") == ["linux", "windows", "macos"]
    with pytest.raises(ValueError):
        vm.parse_plataformas("solaris")


def test_host_python_mapea_a_11_o_14(monkeypatch):
    monkeypatch.setenv("BNX_FORZAR_PYTHON", "3.9")
    assert vm.host_python() == ("3.9", "3.11")
    monkeypatch.setenv("BNX_FORZAR_PYTHON", "3.14")
    assert vm.host_python() == ("3.14", "3.14")


def test_seleccion_host_mas_linux(monkeypatch):
    monkeypatch.setenv("BNX_FORZAR_PLATAFORMA", "windows")
    s = vm.seleccion(["3.14"])
    assert ("pyspark", "3.14", "any") in s
    assert {p for t, _, p in s if t == "ciencia"} == {"windows", "linux"}
    assert vm.seleccion(["3.14"], con_pyspark=False, con_ciencia=False) == []
    monkeypatch.setenv("BNX_FORZAR_PLATAFORMA", "linux")
    assert [p for t, _, p in vm.seleccion(["3.11"]) if t == "ciencia"] == ["linux"]


def test_baja_solo_piezas_pedidas(tmp_path, release, monkeypatch):
    monkeypatch.setenv("BNX_FORZAR_PLATAFORMA", "windows")
    cache = str(tmp_path / "cache")
    piezas = [("pyspark", "3.11", "any"), ("ciencia", "3.11", "windows")]
    res = vm.bajar_piezas(vm.OrigenDir(release), piezas, cache, log=lambda *_: None)
    assert set(res.values()) == {"ok"}
    est = {(e["pieza"], e["plataforma"]): e for e in vm.estado_piezas(cache, piezas + [("ciencia", "3.11", "linux")])}
    assert est[("pyspark", "any")]["presente"] and est[("ciencia", "windows")]["presente"]
    assert not est[("ciencia", "linux")]["presente"]          # linux no se pidio: no se bajo
    assert not os.path.isdir(os.path.join(cache, "ciencia", "3.11", "linux"))


def test_pieza_no_publicada_y_sha_malo(tmp_path, release):
    cache = str(tmp_path / "cache")
    res = vm.bajar_piezas(vm.OrigenDir(release), [("pyspark", "3.14", "any")], cache, log=lambda *_: None)
    assert "no esta en el manifiesto" in res["pyspark-py3.14.zip"]
    with open(os.path.join(release, "ciencia-linux-py3.11.zip"), "ab") as fh:
        fh.write(b"corrupto")
    res = vm.bajar_piezas(vm.OrigenDir(release), [("ciencia", "3.11", "linux")], cache, log=lambda *_: None)
    assert "sha256" in res["ciencia-linux-py3.11.zip"]
    assert not vm._wheels(vm.dir_pieza(cache, "ciencia", "3.11", "linux"))


def test_origen_sin_manifiesto(tmp_path):
    vacio = tmp_path / "vacio"
    vacio.mkdir()
    assert vm.bajar_piezas(vm.OrigenDir(str(vacio)), [("pyspark", "3.11", "any")], str(tmp_path / "c"),
                           log=lambda *_: None) is None


def test_migrar_layout_viejo_a_nuevo_sin_perder(tmp_path):
    cache = str(tmp_path / "cache")
    serie = vc.serie_de("3.11")
    info = vc.SERIES[serie]
    a = _whl(os.path.join(cache, serie), "pyspark-%s-py2.py3-none-any.whl" % info["pyspark"])
    b = _whl(os.path.join(cache, serie), "py4j-%s-py2.py3-none-any.whl" % info["py4j"])
    vm.migrar(cache, log=lambda *_: None)
    assert os.path.exists(a) and os.path.exists(b)             # el viejo queda intacto
    nuevo = os.path.join(cache, "pyspark", serie)
    assert sorted(os.listdir(nuevo)) == sorted([os.path.basename(a), os.path.basename(b)])


def test_podar_solo_en_seco_no_borra(tmp_path):
    cache = str(tmp_path / "cache")
    _whl(os.path.join(cache, "pyspark", "py314"), "pyspark-4.1.2-py2.py3-none-any.whl")
    _whl(os.path.join(cache, "banco", "wheels"), "mex_libx-1.0-py3-none-any.whl")
    vm.podar_piezas(cache, [("pyspark", "3.11", "any")], aplicar=False, log=lambda *_: None)
    assert os.path.exists(os.path.join(cache, "pyspark", "py314", "pyspark-4.1.2-py2.py3-none-any.whl"))
    vm.podar_piezas(cache, [("pyspark", "3.11", "any")], aplicar=True, log=lambda *_: None)
    assert not os.path.exists(os.path.join(cache, "pyspark", "py314", "pyspark-4.1.2-py2.py3-none-any.whl"))
    assert os.path.exists(os.path.join(cache, "banco", "wheels", "mex_libx-1.0-py3-none-any.whl"))  # banco intacto


# ------------------------------------------------------------ xgboost-cpu por plataforma
def test_dist_xgboost_por_plataforma(monkeypatch):
    monkeypatch.delenv("BNX_XGBOOST_GPU", raising=False)
    assert vm.dist_para("xgboost", "linux") == "xgboost-cpu"
    assert vm.dist_para("xgboost", "windows") == "xgboost-cpu"
    assert vm.dist_para("xgboost", "macos") == "xgboost"
    assert vm.dist_para("xgboost-cpu", "macos") == "xgboost"
    assert vm.dist_para("numpy", "linux") == "numpy"
    assert vm.nombre_logico("xgboost_cpu") == "xgboost"
    assert vm.mapear_requisito("xgboost>=1.7", "linux") == "xgboost-cpu>=1.7"
    assert vm.mapear_requisito("xgboost>=1.7", "macos") == "xgboost>=1.7"


def test_xgboost_gpu_desactiva_el_mapeo(monkeypatch):
    monkeypatch.delenv("BNX_XGBOOST_GPU", raising=False)
    vm.set_xgboost_gpu(True)
    try:
        assert vm.dist_para("xgboost", "linux") == "xgboost"
        assert vm.mapear_requisito("xgboost>=1.7", "windows") == "xgboost>=1.7"
    finally:
        vm.set_xgboost_gpu(False)
    assert vm.dist_para("xgboost", "linux") == "xgboost-cpu"


def test_requirements_paquete_linux_pide_xgboost_cpu(monkeypatch):
    from src import mlops_pkg as mp
    monkeypatch.delenv("BNX_XGBOOST_GPU", raising=False)
    txt = mp._requirements(False, False, ml_libs=["xgboost", "scikit-learn"])
    assert 'xgboost-cpu>=1.7 ; sys_platform != "darwin"' in txt
    assert 'xgboost>=1.7 ; sys_platform == "darwin"' in txt
    lin = mp._reqs_para("3.11", txt.splitlines(), False, plataforma="linux")
    mac = mp._reqs_para("3.11", txt.splitlines(), False, plataforma="macos")
    assert any(r.startswith("xgboost-cpu") for r in lin) and not any(r.startswith("xgboost>") for r in lin)
    assert any(r.startswith("xgboost>") for r in mac) and not any(r.startswith("xgboost-cpu") for r in mac)
    # xgboost declarado a mano (sin markers) tambien se mapea a CPU en Linux/Windows
    assert mp._reqs_para("3.14", ["xgboost>=2"], False, plataforma="windows") == ["xgboost-cpu>=2"]
    # paso extra (scoring)
    assert "xgboost-cpu" in mp._requirements(False, True)


def test_requirements_con_xgboost_gpu(monkeypatch):
    from src import mlops_pkg as mp
    monkeypatch.setenv("BNX_XGBOOST_GPU", "1")
    txt = mp._requirements(False, False, ml_libs=["xgboost", "scikit-learn"])
    assert "xgboost-cpu" not in txt and "xgboost>=1.7" in txt
    assert mp._reqs_para("3.11", txt.splitlines(), False, plataforma="linux")[-1:] != []
    assert not any(r.startswith("xgboost-cpu") for r in mp._reqs_para("3.11", txt.splitlines(), False, "linux"))


def test_pins_linux_se_traducen_por_plataforma(monkeypatch, tmp_path):
    visto = {}

    def falso(reqs, v, plat, dest, cons=None, deps=True, timeout=0):
        visto["cons"] = open(cons).read() if cons else ""
        return True, ""
    monkeypatch.setattr(vm, "_pip_download", falso)
    monkeypatch.delenv("BNX_XGBOOST_GPU", raising=False)
    vm.descargar_con_huecos(["xgboost>=1"], "3.11", "macos", str(tmp_path), pins={"xgboost-cpu": "3.2.0"})
    assert "xgboost==3.2.0" in visto["cons"] and "xgboost-cpu" not in visto["cons"]
