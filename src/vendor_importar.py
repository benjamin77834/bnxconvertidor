# -*- coding: utf-8 -*-
"""
vendor_importar.py — Importa piezas del vendor desde una RUTA LOCAL, sin red y sin pip
(solo zipfile/shutil/hashlib). Detecta el tipo:
  - carpeta tipo release (vendor-manifest.json + ZIPs [+ SHA256SUMS])     = --desde-dir
  - ZIP de pieza ('.bnx_vendor_cache/...': pyspark/ciencia/banco)          = --zip
  - banco: ZIP o carpeta con mex-lib*.tar.gz/.whl y toolbox/bnmxverse/utils = --bank-libs
  - la carpeta (o el ZIP) del paquete interno BNX_interno_v3: usa 3_vendor_py<X> de la version
    elegida + 2_banco.zip
Lo usa `preparar_vendor.py --importar RUTA` (boton 'Importar piezas' y subidas del portal).
"""
import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from src import vendor_cache as vc
from src import vendor_modular as vm
EXT_OK = (".zip", ".whl", ".tar.gz", ".json")
NOMBRES_OK = ("SHA256SUMS",)
def nombre_valido(nombre):
    """Solo un basename con extension conocida (.zip .whl .tar.gz .json) o 'SHA256SUMS'."""
    n = str(nombre or "")
    if not n or n != os.path.basename(n) or "/" in n or "\\" in n or n in (".", "..") or ".." in n:
        return False
    if n.startswith(".") or "\x00" in n or ":" in n:
        return False
    return n in NOMBRES_OK or n.lower().endswith(EXT_OK)
def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for ch in iter(lambda: fh.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()
def leer_sums(carpeta):
    out = {}
    p = os.path.join(carpeta, vm.SUMS)
    if os.path.isfile(p):
        with open(p, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                t = ln.split()
                if len(t) >= 2:
                    out[t[-1].lstrip("*")] = t[0].lower()
    return out
def _sums_manifiesto(carpeta):
    out = {}
    try:
        with open(os.path.join(carpeta, vm.MANIFEST), encoding="utf-8") as fh:
            for p in json.load(fh).get("piezas", []):
                if p.get("archivo") and p.get("sha256"):
                    out[p["archivo"]] = p["sha256"].lower()
    except (OSError, ValueError):
        pass
    return out
def verificar_sha(carpeta, nombres=None):
    """{archivo: 'ok' | 'sha256 no coincide' } para los archivos de la carpeta que aparezcan en
    SHA256SUMS o en el manifiesto. Los que no aparecen no se verifican (no se listan)."""
    esperado = _sums_manifiesto(carpeta)
    esperado.update(leer_sums(carpeta))
    res = {}
    for n, sha in sorted(esperado.items()):
        if nombres is not None and n not in nombres:
            continue
        f = os.path.join(carpeta, n)
        if os.path.isfile(f):
            res[n] = "ok" if _sha256(f) == sha else "sha256 no coincide"
    return res
def tipo_zip(path):
    """'pieza' (entradas .bnx_vendor_cache/), 'banco' (mex-lib / toolbox...), 'interno'
    (3_vendor_py*/ o 2_banco.zip dentro) o None."""
    try:
        with zipfile.ZipFile(path) as z:
            nombres = z.namelist()
    except (OSError, zipfile.BadZipFile):
        return None
    if nombres and all(n.startswith(vc.ZIP_PREFIX) or n == "importar_vendor.py" for n in nombres):
        return "pieza"
    bases = [n.replace("\\", "/") for n in nombres]
    if any(re.search(r"(^|/)3_vendor_py3\.\d+/", n) or re.search(r"(^|/)\d?_?banco\.zip$", n) for n in bases):
        return "interno"
    if any(os.path.basename(n).lower().startswith(("mex-lib", "mex_lib")) for n in bases) or \
            any(("/%s/" % d) in ("/" + n) for n in bases for d in vc.BANK_PATH_DIRS):
        return "banco"
    return None
def _extraer_seguro(zpath, destino):
    with zipfile.ZipFile(zpath) as z:
        for n in z.namelist():
            partes = n.replace("\\", "/").split("/")
            if ".." in partes or n.startswith("/") or os.path.isabs(n) or ":" in partes[0]:
                raise ValueError("el ZIP tiene rutas peligrosas (%r)" % n)
        z.extractall(destino)
def _vendor_dir_interno(raiz, version):
    """3_vendor_py<version>/ dentro de la carpeta del paquete interno (busca 2 niveles)."""
    for r, ds, _fs in os.walk(raiz):
        if r[len(raiz):].count(os.sep) > 2:
            ds[:] = []
            continue
        for d in ds:
            if re.fullmatch(r"\d?_?vendor_py%s" % re.escape(version), d):
                return os.path.join(r, d)
    return None
def _banco_zip_interno(raiz):
    for r, ds, fs in os.walk(raiz):
        if r[len(raiz):].count(os.sep) > 2:
            ds[:] = []
            continue
        for f in fs:
            if re.fullmatch(r"\d?_?banco\.zip", f, re.I):
                return os.path.join(r, f)
    return None
def _es_interno(raiz):
    try:
        hijos = os.listdir(raiz)
    except OSError:
        return False
    return any(re.fullmatch(r"\d?_?vendor_py3\.\d+", h) for h in hijos) or \
        any(re.fullmatch(r"\d?_?banco\.zip", h, re.I) for h in hijos)
def _piezas_de_carpeta(carpeta, version, plataformas, con_pyspark):
    """Piezas (tipo, py, plat) del manifiesto de la carpeta, cuyo ZIP este presente y que entren en
    la seleccion (version + plataformas + pyspark)."""
    try:
        with open(os.path.join(carpeta, vm.MANIFEST), encoding="utf-8") as fh:
            man = json.load(fh)
    except (OSError, ValueError):
        return [], []
    elegidas, saltadas = [], []
    for p in man.get("piezas", []):
        arch = p.get("archivo")
        if not arch or not os.path.isfile(os.path.join(carpeta, arch)):
            continue
        t, v, pl = p["nombre"], p.get("python"), p.get("plataforma")
        ok = (version is None or v == version) and (
            (t == "pyspark" and con_pyspark) or (t == "ciencia" and (plataformas is None or pl in plataformas)))
        (elegidas if ok else saltadas).append((t, v, pl))
    return elegidas, saltadas
_NUMPY_WHL = re.compile(r"(?:^|/)ciencia/(3\.\d+)/[^/]+/numpy-(\d+)\.(\d+)[^/]*\.whl$")
def numpy2_en_zip(path):
    """['numpy 2.4.6 (py3.11)', ...] si la pieza de ciencia ZIP trae numpy >= 2 para Python <= 3.12
    (el rango donde mlops_pkg fija numpy<2); [] si no. Solo lee los nombres del ZIP."""
    try:
        with zipfile.ZipFile(path) as z:
            nombres = z.namelist()
    except (OSError, zipfile.BadZipFile):
        return []
    out = []
    for n in nombres:
        m = _NUMPY_WHL.search(n.replace("\\", "/"))
        if m and int(m.group(2)) >= 2 and tuple(int(x) for x in m.group(1).split(".")) <= (3, 12):
            out.append("%s (py%s)" % (os.path.basename(n).split("-")[0] + " " + os.path.basename(n).split("-")[1], m.group(1)))
    return sorted(set(out))
def avisar_numpy2(path, log=print):
    """Avisa (no bloquea) si la pieza de ciencia trae numpy 2 para Python <= 3.12. Devuelve el aviso o ''.
    numpy 2 quito numpy.source y la libreria del banco mex-libmissingtreatment lo necesita."""
    malas = numpy2_en_zip(path)
    if not malas:
        return ""
    aviso = ("AVISO: %s trae %s. numpy 2 elimino numpy.source, que la libreria del banco "
             "mex-libmissingtreatment necesita: los paquetes generados con esta pieza fallaran en el servidor. "
             "La pieza correcta es ciencia-linux-py3.11.zip del release vendor-v4 (numpy 1.26.4); "
             "reemplacela y vuelva a importar." % (os.path.basename(path), ", ".join(malas)))
    log("[importar] " + aviso)
    return aviso
def importar_carpeta_release(carpeta, cache, version=None, plataformas=None, con_pyspark=True, log=print):
    elegidas, saltadas = _piezas_de_carpeta(carpeta, version, plataformas, con_pyspark)
    for t, v, pl in saltadas:
        log("[importar] omito %s (no elegida: py%s %s)" % (vm.archivo_pieza(t, v, pl), v, pl))
    if not elegidas:
        log("[importar] %s: no hay piezas elegidas para Python %s (%s%s)"
            % (carpeta, version or "-", ",".join(plataformas or []) or "-", ", pyspark" if con_pyspark else ""))
        return {}
    for t, v, pl in elegidas:
        if t == "ciencia":
            avisar_numpy2(os.path.join(carpeta, vm.archivo_pieza(t, v, pl)), log)
    pedidas = [(t, v, "any" if t == "pyspark" else pl) for t, v, pl in elegidas]
    return vm.bajar_piezas(vm.OrigenDir(carpeta), pedidas, cache, log=log) or {}
def importar_ruta(ruta, cache=None, version=None, plataformas=None, con_pyspark=True, log=print, _nivel=0):
    """Importa lo que haya en `ruta` (carpeta o archivo). Devuelve {elemento: 'ok' | motivo}.
    No usa red ni pip (salvo convertir un sdist mex-lib .tar.gz a wheel, que banco.zip ya trae)."""
    cache = os.path.abspath(cache or vc.cache_dir())
    ruta = os.path.abspath(os.path.expanduser(ruta))
    res = {}
    if _nivel > 3:
        return res
    if os.path.isdir(ruta):
        if os.path.isfile(os.path.join(ruta, vm.MANIFEST)):
            log("[importar] carpeta de release: %s" % ruta)
            res.update(importar_carpeta_release(ruta, cache, version, plataformas, con_pyspark, log))
            # ZIPs sueltos que no esten en el manifiesto (banco.zip subido junto a las piezas)
            en_man = {vm.archivo_pieza(t, v, pl) for t, v, pl in sum(_piezas_de_carpeta(ruta, None, None, True), [])}
            for f in sorted(os.listdir(ruta)):
                if f.lower().endswith(".zip") and f not in en_man and tipo_zip(os.path.join(ruta, f)) in ("pieza", "banco"):
                    res.update(importar_ruta(os.path.join(ruta, f), cache, version, plataformas, con_pyspark, log, _nivel + 1))
            if any(f.lower().startswith(("mex-lib", "mex_lib")) for f in os.listdir(ruta)):
                res.update(_importar_banco(ruta, cache, log))
            return res
        if _es_interno(ruta):
            log("[importar] paquete interno: %s" % ruta)
            vd = _vendor_dir_interno(ruta, version or "3.11")
            if vd:
                res.update(importar_ruta(vd, cache, version, plataformas, con_pyspark, log, _nivel + 1))
            else:
                res["3_vendor_py%s" % (version or "3.11")] = "no esta en %s" % ruta
                log("[importar] AVISO: no encontre 3_vendor_py%s en %s" % (version or "3.11", ruta))
            bz = _banco_zip_interno(ruta)
            if bz:
                res.update(importar_ruta(bz, cache, version, plataformas, con_pyspark, log, _nivel + 1))
            return res
        hijos = [h for h in os.listdir(ruta) if not h.startswith((".", "__MACOSX"))]
        if len(hijos) == 1 and os.path.isdir(os.path.join(ruta, hijos[0])):   # ZIP con carpeta raiz
            return importar_ruta(os.path.join(ruta, hijos[0]), cache, version, plataformas, con_pyspark, log, _nivel + 1)
        # carpeta sin manifiesto: ZIPs de piezas sueltos y/o librerias del banco
        hubo = False
        sums = verificar_sha(ruta)
        for f in sorted(os.listdir(ruta)):
            full = os.path.join(ruta, f)
            if f.lower().endswith(".zip") and os.path.isfile(full):
                if sums.get(f, "ok") != "ok":
                    res[f] = sums[f]
                    log("[importar] ERROR: %s: %s; no se importa" % (f, sums[f]))
                    continue
                hubo = True
                res.update(importar_ruta(full, cache, version, plataformas, con_pyspark, log, _nivel + 1))
        if any(f.lower().startswith(("mex-lib", "mex_lib")) for f in os.listdir(ruta)) or \
                any(os.path.isdir(os.path.join(ruta, d)) for d in vc.BANK_PATH_DIRS + ("pkgcode",)):
            hubo = True
            res.update(_importar_banco(ruta, cache, log))
        if not hubo:
            res[os.path.basename(ruta)] = "no reconozco el contenido (ni manifiesto, ni ZIPs, ni mex-lib)"
            log("[importar] ERROR: %s: %s" % (ruta, res[os.path.basename(ruta)]))
        return res
    if not os.path.isfile(ruta):
        res[os.path.basename(ruta)] = "no existe"
        log("[importar] ERROR: no existe %s" % ruta)
        return res
    base = os.path.basename(ruta)
    if base.lower().endswith((".tar.gz", ".whl")) and base.lower().startswith(("mex-lib", "mex_lib")):
        tmp = tempfile.mkdtemp(prefix="bnx_imp_", dir=cache if os.path.isdir(cache) else None)
        try:
            shutil.copy2(ruta, os.path.join(tmp, base))
            return _importar_banco(tmp, cache, log)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    tz = tipo_zip(ruta) if base.lower().endswith(".zip") else None
    if tz == "pieza":
        sums = verificar_sha(os.path.dirname(ruta), {base})
        if sums.get(base, "ok") != "ok":
            log("[importar] ERROR: %s: %s; no se importa" % (base, sums[base]))
            return {base: sums[base]}
        avisar_numpy2(ruta, log)
        vc.importar_zip(ruta, log=log, cache=cache)
        vm.guardar_manifiesto_local(cache)
        return {base: "ok"}
    if tz == "banco":
        return _importar_banco(ruta, cache, log)
    if tz == "interno":
        os.makedirs(cache, exist_ok=True)
        tmp = tempfile.mkdtemp(prefix="bnx_int_", dir=cache)
        try:
            log("[importar] descomprimiendo el paquete interno %s ..." % base)
            _extraer_seguro(ruta, tmp)
            return importar_ruta(tmp, cache, version, plataformas, con_pyspark, log, _nivel + 1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    log("[importar] ERROR: %s no es un ZIP de vendor, de banco ni del paquete interno" % base)
    return {base: "tipo desconocido"}
def _importar_banco(origen, cache, log):
    try:
        sd, mods = vc.importar_bank_libs(origen, log=log, cache=cache)
        return {"banco (%s)" % os.path.basename(origen): "ok" if (sd or mods) else "sin librerias del banco"}
    except ValueError as e:
        log("[importar] ERROR banco: %s" % e)
        return {"banco (%s)" % os.path.basename(origen): str(e)}
