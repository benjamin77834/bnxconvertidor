# -*- coding: utf-8 -*-
"""vendor_banco.py — pieza 'banco' (INTERNA, nunca publica) como WHEELS.

  mex-lib*.tar.gz (sdist)            -> mex_lib*-2.2.0-py3-none-any.whl   (pip wheel --no-deps)
  toolbox/ bnmxverse/ utils/ (codigo) -> bnx_bank_pkgcode-1.0.0-py3-none-any.whl (setup.py generado al vuelo)

Decision sobre 'utils': va DENTRO del wheel pkgcode. Evidencia: main.py agrega bank_src/ (modulos de
apoyo subidos) al FINAL de sys.path y antes ya ganaba bank_pkg/ (que llevaba utils/ con __init__.py);
en site-packages el wheel gana igual sobre bank_src/, asi que la precedencia no cambia. No choca con
el stdlib (no existe 'utils') ni con paquetes del stack de ciencia. Si un paquete viejo usa bank_pkg/,
run.sh/main.py lo siguen leyendo.
"""
import glob
import os
import shutil
import subprocess
import tempfile
import zipfile

from src import vendor_cache as vc

PKGCODE_WHEEL = "bnx_bank_pkgcode"
SETUP_PKGCODE = (
    "from setuptools import setup, find_packages\n"
    "setup(name='bnx-bank-pkgcode', version='1.0.0', packages=find_packages(), python_requires='>=3.8',\n"
    "      description='toolbox / bnmxverse / utils del banco (generado por BNX)')\n")

LEEME_BANCO = (
    "BANCO (pieza INTERNA: no publicar, no subir a GitHub)\n"
    "=====================================================\n"
    "banco.zip lleva SOLO wheels (.whl) + SHA256SUMS:\n"
    "  banco/wheels/mex_lib*-2.2.0-py3-none-any.whl       las mex-lib del banco (Python puro: valen para 3.11 y 3.14)\n"
    "  banco/wheels/bnx_bank_pkgcode-1.0.0-py3-none-any.whl   toolbox/, bnmxverse/, utils/ (antes carpetas en bank_pkg/)\n\n"
    "Sus dependencias open source (cytoolz, toolz, Unidecode, cloudpickle, joblib, pandas...) NO van aqui:\n"
    "viajan en la pieza publica 'ciencia' de cada version/plataforma.\n\n"
    "Instalar en el generador (BNX):\n"
    "    .venv/bin/python preparar_vendor.py --zip banco.zip\n"
    "  o desde las librerias originales (carpeta/ZIP con mex-lib*.tar.gz y toolbox/bnmxverse/utils):\n"
    "    .venv/bin/python preparar_vendor.py --bank-libs <carpeta|zip>      (las convierte a wheel)\n"
    "Queda en <venv>/bnx_vendor_cache/banco/wheels/. No depende de la version de Python ni del SO.\n"
    "En el paquete generado: pip install --no-index --find-links vendor/bank/ (igual que el resto).\n")


def _pip_wheel(src, outdir, cache=None):
    """pip wheel --no-deps de un sdist/carpeta. Primero SIN internet (setuptools del cache), luego con
    el indice. Devuelve (ruta_wheel | None, error)."""
    cache = cache or vc.cache_dir()
    os.makedirs(outdir, exist_ok=True)
    antes = set(os.listdir(outdir))
    links = []
    for d in sorted({os.path.dirname(w) for w in glob.glob(os.path.join(cache, "**", "setuptools-*.whl"), recursive=True)}):
        links += ["--find-links", d]
    intentos = [["--no-index"] + links] if links else []
    try:
        import setuptools  # noqa: F401
        intentos.append(["--no-index", "--no-build-isolation"])
    except ImportError:
        pass
    if os.environ.get("BNX_NO_DOWNLOAD") != "1":
        intentos.append(["--retries", "1", "--timeout", "15"])
    err = "sin setuptools para construir (cache/entorno) y sin permiso de bajarlo"
    for extra in intentos:
        r = subprocess.run(vc.pip_cmd() + ["wheel", "--no-deps", "--quiet", "--disable-pip-version-check"] + extra
                           + [src, "-w", outdir], capture_output=True, text=True, timeout=600)
        nuevos = [f for f in os.listdir(outdir) if f.endswith(".whl") and f not in antes]
        if r.returncode == 0 and nuevos:
            return os.path.join(outdir, nuevos[0]), ""
        err = vc.limpiar_stderr_pip(r.stderr, maximo=160)
    return None, err


def pkgcode_a_wheel(pkgcode_dir, outdir, cache=None):
    """toolbox/bnmxverse/utils (carpeta de codigo) -> UN wheel 'bnx-bank-pkgcode'. No toca el original:
    trabaja en una copia con __init__.py en cada carpeta con .py."""
    tmp = tempfile.mkdtemp(prefix="bnx_pkgcode_")
    try:
        mods = []
        for n in sorted(os.listdir(pkgcode_dir)):
            d = os.path.join(pkgcode_dir, n)
            if os.path.isdir(d) and any(f.endswith(".py") for _r, _d, fs in os.walk(d) for f in fs):
                shutil.copytree(d, os.path.join(tmp, n), ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", ".keep"))
                mods.append(n)
        if not mods:
            return None, "sin modulos en %s" % pkgcode_dir
        for r, _ds, fs in os.walk(tmp):
            if any(f.endswith(".py") for f in fs) and "__init__.py" not in fs:
                with open(os.path.join(r, "__init__.py"), "w") as fh:
                    fh.write("# BNX: paquete normal (no namespace) para que no lo tape otro modulo homonimo\n")
        with open(os.path.join(tmp, "setup.py"), "w") as fh:
            fh.write(SETUP_PKGCODE)
        return _pip_wheel(tmp, outdir, cache)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def wheel_es_pura(whl):
    return os.path.basename(whl).endswith("-none-any.whl")


def archivos_pkgcode_en_wheel(bdir):
    """Rutas 'toolbox/kernel.py' ... dentro del wheel pkgcode del banco."""
    out = set()
    for w in glob.glob(os.path.join(bdir, "wheels", PKGCODE_WHEEL + "-*.whl")):
        try:
            with zipfile.ZipFile(w) as z:
                out |= {n for n in z.namelist() if n.endswith(".py")}
        except (OSError, zipfile.BadZipFile):
            pass
    return out


def modulos_pkgcode(bdir):
    """Modulos de path presentes: carpetas en pkgcode/ o dentro del wheel pkgcode."""
    out = set()
    pc = os.path.join(bdir, "pkgcode")
    if os.path.isdir(pc):
        out |= {m for m in os.listdir(pc) if os.path.isdir(os.path.join(pc, m))
                and any(f.endswith(".py") for _r, _d, fs in os.walk(os.path.join(pc, m)) for f in fs)}
    out |= {n.split("/")[0] for n in archivos_pkgcode_en_wheel(bdir) if "/" in n}
    return out


def convertir_a_wheels(origen_wheels, pkgcode_dir, destino, cache=None):
    """sdists mex-lib (carpeta origen_wheels; los .whl ya hechos se copian) + carpeta pkgcode -> wheels en
    destino. Devuelve {'wheels', 'fallos': {nombre: error}, 'nativos'}."""
    res = {"wheels": [], "fallos": {}, "nativos": []}
    os.makedirs(destino, exist_ok=True)
    if origen_wheels and os.path.isdir(origen_wheels):
        for f in sorted(os.listdir(origen_wheels)):
            if not f.lower().startswith(("mex-lib", "mex_lib")):
                continue
            src = os.path.join(origen_wheels, f)
            if f.endswith(".whl"):
                dst = os.path.join(destino, f)
                if os.path.abspath(src) != os.path.abspath(dst):
                    shutil.copy2(src, dst)
                w = dst
            elif f.endswith(".tar.gz"):
                w, err = _pip_wheel(src, destino, cache)
                if not w:
                    res["fallos"][f] = err
                    continue
            else:
                continue
            res["wheels"].append(w)
            if not wheel_es_pura(w):
                res["nativos"].append(os.path.basename(w))
    if pkgcode_dir and os.path.isdir(pkgcode_dir):
        w, err = pkgcode_a_wheel(pkgcode_dir, destino, cache)
        if w:
            res["wheels"].append(w)
        else:
            res["fallos"]["pkgcode"] = err
    return res


def construir_banco(cache, outdir, log=print):
    """banco.zip (interno): SOLO wheels (mex-lib + bnx-bank-pkgcode) + SHA256SUMS + LEEME."""
    from src.vendor_modular import SUMS, _sha256, empaquetar_zip
    bd = vc.banco_dir(cache)
    wh = os.path.join(bd, "wheels")
    tmpw = tempfile.mkdtemp(prefix="bnx_banco_")
    try:
        res = convertir_a_wheels(wh, os.path.join(bd, "pkgcode"), tmpw, cache)
        for f in glob.glob(os.path.join(wh, "*.whl")):      # wheels ya presentes en el cache
            if os.path.basename(f).lower().startswith(("mex", PKGCODE_WHEEL)) and not os.path.exists(os.path.join(tmpw, os.path.basename(f))):
                shutil.copy2(f, tmpw)
        ws = sorted(glob.glob(os.path.join(tmpw, "*.whl")))
        os.makedirs(outdir, exist_ok=True)
        leeme = os.path.join(outdir, "LEEME.txt")
        with open(leeme, "w", encoding="utf-8") as fh:
            fh.write(LEEME_BANCO)
        entradas = [("banco/wheels/" + os.path.basename(w), w) for w in ws] + [("banco/LEEME.txt", leeme)]
        b, sha = empaquetar_zip(os.path.join(outdir, "banco.zip"), entradas)
        lineas = ["%s  wheels/%s" % (_sha256(w), os.path.basename(w)) for w in ws] + ["%s  banco.zip" % sha]
        with open(os.path.join(outdir, SUMS), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lineas) + "\n")
        log("[banco] %d wheels, %.2f MB (fallos: %s, nativos: %s)" % (
            len(ws), b / 1048576.0, res["fallos"] or "-", res["nativos"] or "-"))
        return {"archivo": "banco.zip", "bytes": b, "sha256": sha, "wheels": [os.path.basename(w) for w in ws],
                "fallos": res["fallos"], "nativos": res["nativos"]}
    finally:
        shutil.rmtree(tmpw, ignore_errors=True)
