#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preparar_vendor.py — Baja/genera el cache de vendor DENTRO del venv (.venv/bnx_vendor_cache/).

USO:
    .venv/bin/python preparar_vendor.py --python 3.11             # default (3.11 o 3.14; 3.8/3.12 = legado)
    .venv/bin/python preparar_vendor.py --python 3.11 --python 3.14
    .venv/bin/python preparar_vendor.py --desde-github --python 3.14 [--tag vendor-v3]
    .venv/bin/python preparar_vendor.py --zip ~/Downloads/ciencia-linux-py3.11.zip   (o banco.zip)
    .venv/bin/python preparar_vendor.py --estado [--json] [--python 3.14]

Al bajar (--python) se prefiere el GitHub Release publico (rapido, sin build de PySpark; no trae
las libs del banco); si falla, cae a pip. --desde-github = solo GitHub; --sin-github = solo pip.

Por version: PySpark (sdist -> wheel) + py4j + dependencias open source (manylinux x86_64).
Las mex-lib del banco NO estan en PyPI: se reportan como faltantes (usa --zip o copialas).
Es idempotente: no vuelve a bajar lo que ya esta.

VENDOR MODULAR (3 piezas independientes, ver src/vendor_modular.py)
    pyspark  (por version)                 cache/pyspark/<serie>/
    ciencia  (por version y plataforma)    cache/ciencia/<py>/<linux|windows|macos>/
    banco    (interna, NO publica)         cache/banco/            (preparar_vendor.py --zip banco.zip)
Por defecto baja SOLO: ciencia del SO del host + ciencia linux (paquetes para el servidor) + pyspark.
    --plataformas linux,windows,macos   explicito (reemplaza host+linux)
    --solo-host / --para-linux          no bajar / bajar la ciencia linux ademas de la del host
    --sin-pyspark / --con-pyspark       --sin-ciencia / --con-ciencia
    --desde-dir CARPETA                 carpeta con vendor-manifest.json + ZIPs (hace de GitHub; pruebas/offline)
    --migrar [--quitar-viejo]           reorganiza el cache viejo al layout nuevo (hardlinks; nada se borra)
    --construir-release DIR             arma los ZIP publicos + manifiesto + SHA256SUMS (--pyspark-slim: experimental)
    --construir-banco DIR               banco.zip (interno) + LEEME
Pruebas: BNX_FORZAR_PLATAFORMA=windows|macos|linux y BNX_FORZAR_PYTHON=3.14 simulan otro host.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("BNX_NO_DOWNLOAD", "1")   # solo preparar() baja (ver vendor_cache)

from src import vendor_cache as vc  # noqa: E402
from src import vendor_modular as vm  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description="Prepara el cache de vendor (dentro del venv).")
    ap.add_argument("--python", action="append", metavar="3.X",
                    help="Version de Python del servidor Linux (3.11 o 3.14; 3.8/3.12 legado). Repetible. Default 3.11.")
    ap.add_argument("--zip", metavar="RUTA", help="Importar un ZIP de vendor (exportar_vendor.py).")
    ap.add_argument("--desde-github", action="store_true",
                    help="Bajar solo del GitHub Release publico (sin pip). Es el metodo preferido por defecto.")
    ap.add_argument("--sin-github", action="store_true", help="No intentar GitHub: usar pip directo.")
    ap.add_argument("--tag", default=vc.GH_TAG, help="Tag del Release (default %s)." % vc.GH_TAG)
    ap.add_argument("--estado", action="store_true", help="Solo reporta que falta.")
    ap.add_argument("--json", action="store_true", help="Con --estado: salida JSON.")
    ap.add_argument("--extra", "--ciencia", dest="extra", action="store_true",
                    help="Incluir tambien las deps de los pasos extra (scoring). La pila de ciencia de "
                         "datos (xgboost, lightgbm, scikit-learn, ...) ya va SIEMPRE.")
    ap.add_argument("--bank-libs", metavar="RUTA",
                    help="Importar las librerias del banco (mex-lib*.tar.gz o .whl, toolbox/bnmxverse/utils) "
                         "desde una carpeta o ZIP; se convierten a WHEELS en banco/wheels/.")
    ap.add_argument("--podar", action="store_true",
                    help="Quitar del cache todo lo que no sea el minimo para las --python elegidas "
                         "(nunca toca los sdist mex-lib de bank_libs/). Pide confirmacion en tty.")
    ap.add_argument("--plataformas", metavar="LISTA",
                    help="Plataformas de la pieza 'ciencia': linux,windows,macos (macos-intel experimental). "
                         "Reemplaza el default (host + linux).")
    ap.add_argument("--solo-host", action="store_true", help="No bajar la ciencia linux (solo la del host).")
    ap.add_argument("--para-linux", dest="para_linux", action="store_true", default=True,
                    help="Bajar tambien la ciencia linux para generar paquetes del servidor (default).")
    ap.add_argument("--con-pyspark", dest="con_pyspark", action="store_true", default=True)
    ap.add_argument("--sin-pyspark", dest="con_pyspark", action="store_false",
                    help="No bajar la pieza pyspark (~300-420 MB).")
    ap.add_argument("--con-ciencia", dest="con_ciencia", action="store_true", default=True)
    ap.add_argument("--sin-ciencia", dest="con_ciencia", action="store_false")
    ap.add_argument("--desde-dir", metavar="CARPETA",
                    help="Origen local con vendor-manifest.json + ZIPs (actua como el Release de GitHub).")
    ap.add_argument("--importar", metavar="RUTA",
                    help="Importa desde una ruta local (sin red ni pip): carpeta de release (manifiesto + ZIPs), "
                         "ZIP de pieza, banco.zip / carpeta con mex-lib, o la carpeta/ZIP BNX_interno (usa "
                         "3_vendor_py<X> de --python y 2_banco.zip). Respeta --plataformas / --sin-pyspark.")
    ap.add_argument("--borrar-origen", action="store_true",
                    help="Con --importar: borra la RUTA al terminar (subidas temporales del portal).")
    ap.add_argument("--migrar", action="store_true", help="Reorganiza el cache viejo al layout modular nuevo.")
    ap.add_argument("--quitar-viejo", action="store_true",
                    help="Con --migrar: mueve el layout viejo a _layout_viejo/ (no borra).")
    ap.add_argument("--construir-release", metavar="DIR",
                    help="Arma los ZIP publicos (sin banco) + vendor-manifest.json + SHA256SUMS en DIR.")
    ap.add_argument("--construir-banco", metavar="DIR", help="Arma banco.zip (interno) + LEEME en DIR.")
    ap.add_argument("--pyspark-slim", action="store_true",
                    help="EXPERIMENTAL (apagado por defecto): con --construir-release, wheel de PySpark sin "
                         "jars de RocksDB/Mesos/K8s/REPL ni examples (ver informe de la prueba local).")
    ap.add_argument("--mostrar", action="store_true", help="Con --podar: solo muestra (dry-run).")
    ap.add_argument("--si", action="store_true", help="Con --podar: borrar sin preguntar (no interactivo).")
    ap.add_argument("--xgboost-gpu", action="store_true",
                    help="Usar 'xgboost' con CUDA (Linux/Windows) en vez de 'xgboost-cpu' (por defecto, ~5 MB "
                         "sin nvidia-nccl). Aumenta MUCHO el tamano (Linux: +150-430 MB).")
    args = ap.parse_args(argv)
    if args.xgboost_gpu:
        vm.set_xgboost_gpu(True)
    try:
        sys.stdout.reconfigure(line_buffering=True)   # progreso en vivo (log de la UI)
    except Exception:
        pass
    try:
        versiones = [vc.norm_version(v) for v in (args.python or [])]
    except ValueError as e:
        print("ERROR: %s" % e)
        return 2

    if args.desde_github and args.sin_github:
        print("ERROR: --desde-github y --sin-github son excluyentes.")
        return 2
    try:
        plats = vm.parse_plataformas(args.plataformas) if args.plataformas else None
    except ValueError as e:
        print("ERROR: %s" % e)
        return 2
    cache = vc.cache_dir()
    if args.estado:
        vs = versiones or list(vc.VERSIONES_DEFAULT)
        piezas_e = vm.seleccion(vs, plats, args.con_pyspark, args.con_ciencia, args.para_linux, args.solo_host)
        est = vc.estado(vs, extra=args.extra)
        pz = vm.estado_piezas(cache, piezas_e)
        est["piezas"] = pz
        est["host"] = {"plataforma": vm.host_plataforma(), "python": vm.host_python()[0]}
        if args.json:
            print(json.dumps(est, ensure_ascii=False, indent=2))
        else:
            print("Host: %s, Python %s" % (est["host"]["plataforma"], est["host"]["python"]))
            print(vc.formatear_estado(est))
            print(vm.formatear_piezas(pz))
        return 0 if all(e["presente"] for e in pz) else 3

    print("Cache: %s" % cache)
    if args.construir_release or args.construir_banco:
        if args.construir_release:
            man = vm.construir_release(cache, os.path.abspath(args.construir_release),
                                       versiones or list(vm.PY_VERSIONES),
                                       tuple(plats or ("linux", "windows", "macos")),
                                       pyspark_slim=args.pyspark_slim)
            print("OK release en %s: %d piezas" % (args.construir_release, len(man["piezas"])))
        if args.construir_banco:
            vm.construir_banco(cache, os.path.abspath(args.construir_banco))
        return 0
    if args.migrar:
        res = vm.migrar(cache, quitar_viejo=args.quitar_viejo)
        print("Migrado: pyspark %d, ciencia %d, banco %d archivos" % (
            len(res["pyspark"]), len(res["ciencia"]), len(res["banco"])))
        for v, hs in res["huecos"].items():
            for h in hs:
                print("   [hueco py%s] %s" % (v, h))
        return 0
    if args.importar:
        from src import vendor_importar as vi
        v_imp = versiones[0] if versiones else "3.11"
        plats_imp = plats or ["linux"]     # el paquete es para el servidor Linux: solo ciencia linux
        if not args.con_ciencia:
            plats_imp = []
        print("Importar desde %s (Python %s; ciencia: %s; pyspark: %s)" % (
            args.importar, v_imp, ",".join(plats_imp) or "no", "si" if args.con_pyspark else "no"))
        try:
            res = vi.importar_ruta(args.importar, cache, v_imp, plats_imp, args.con_pyspark)
        except Exception as e:   # ZIP corrupto, disco lleno, ...
            print("ERROR: %s" % str(e)[:300])
            res = {"importar": str(e)[:300]}
        finally:
            if args.borrar_origen:
                import shutil
                if os.path.isdir(args.importar):
                    shutil.rmtree(args.importar, ignore_errors=True)
        vm.guardar_manifiesto_local(cache)
        malos = {k: m for k, m in res.items() if m != "ok"}
        for k, m in malos.items():
            print("ERROR: %s: %s" % (k, m))
        print("")
        print(vm.formatear_piezas(vm.estado_piezas(cache, vm.seleccion([v_imp], plats_imp or None,
                                                                       args.con_pyspark, bool(plats_imp)))))
        b = vc.estado_banco(cache)
        print("Banco: mex-lib %d/%d, modulos de path %d/%d" % (
            len(b["sdists"]), len(b["sdists"]) + len(b["sdists_faltan"]),
            len(b["pkgcode"]), len(b["pkgcode"]) + len(b["pkgcode_faltan"])))
        if not res:
            print("ERROR: no se importo nada de %s" % args.importar)
            return 1
        return 1 if malos else 0
    if args.bank_libs:
        try:
            vc.importar_bank_libs(args.bank_libs)
        except ValueError as e:
            print("ERROR: %s" % e)
            return 1
        if not versiones and not args.zip and not args.podar:
            print(vc.formatear_estado(vc.estado([], extra=args.extra)))
            return 0
    if args.zip:
        try:
            vc.importar_zip(os.path.expanduser(args.zip))
        except ValueError as e:
            print("ERROR: %s" % e)
            return 1
        vm.guardar_manifiesto_local(cache)
        if not versiones:
            return 0

    versiones = versiones or ["3.11"]
    piezas = vm.seleccion(versiones, plats, args.con_pyspark, args.con_ciencia, args.para_linux, args.solo_host)
    if args.podar:
        def _confirmar():
            if args.si:
                return True
            if not (sys.stdin.isatty() and sys.stdout.isatty()):
                print("Sin terminal interactiva: no se borra (usa --si para confirmar).")
                return False
            return input("¿Borrar estos archivos? [s/N] ").strip().lower() in ("s", "si", "sí", "y", "yes")
        aplicar = not args.mostrar
        hubo_error = []

        def _log(msg):
            print(msg)
            if str(msg).startswith("ERROR"):
                hubo_error.append(msg)
        if vm.tiene_layout_nuevo(cache) and not os.path.isdir(os.path.join(cache, "mlops_deps")):
            # layout nuevo: se conservan SOLO las piezas elegidas (el banco nunca se toca)
            print("Podar por piezas: se conservan %s" % ", ".join("%s/py%s/%s" % p for p in piezas))
            if aplicar and not _confirmar():
                print("Cancelado: no se borro nada.")
                return 0
            vm.podar_piezas(cache, piezas, aplicar=aplicar, log=_log)
            return 0
        vc.podar(versiones, extra=args.extra, aplicar=aplicar,
                 confirmar=_confirmar if aplicar else None, log=_log)
        return 1 if hubo_error else 0     # que la UI no diga "Listo" si no se pudo podar

    # --- que piezas faltan (el layout viejo cuenta como presente para linux / pyspark)
    est_p = vm.estado_piezas(cache, piezas)
    faltan_p = [(e["pieza"], e["python"], e["plataforma"]) for e in est_p if not e["presente"]]
    print("Host: %s, Python %s" % (vm.host_plataforma(), vm.host_python()[0]))
    print(vm.formatear_piezas(est_p))
    if faltan_p and (args.desde_dir or not args.sin_github):
        if args.desde_dir:
            origen = vm.OrigenDir(args.desde_dir)
        else:
            origen = vm.OrigenGithub(args.tag if args.tag != vc.GH_TAG else None)
        sin_red = None
        try:
            res = vm.bajar_piezas(origen, faltan_p, cache)
        except vm.ErrorRed as e:  # sin internet / DNS / proxy / timeout: NO es "falta el manifiesto"
            sin_red = str(e)
            res = None
        except ValueError as e:
            print("ERROR: %s" % e)
            res = {}
        except Exception as e:
            print("[origen] no pude leer %s: %s" % (origen.nombre, str(getattr(e, "reason", None) or e)[:150]))
            res = None
        if res is None and args.desde_dir:
            print("ERROR: %s no tiene vendor-manifest.json" % args.desde_dir)
            return 1
        if sin_red is not None:
            print("ERROR: No pude conectar a github.com: %s" % sin_red)
            print("       Sin red no se puede bajar nada (tampoco por pip). Importa las piezas: boton 'Importar piezas'")
            print("       de la pagina Framework MLOps v2 (subir los ZIP o indicar la carpeta), o")
            print("       preparar_vendor.py --importar <carpeta BNX_interno | 3_vendor_py%s | pieza.zip>."
                  % (versiones[0] if versiones else "3.11"))
            print("       Si hay proxy corporativo define HTTPS_PROXY/HTTP_PROXY.")
            return 1
        if res is None:
            # Release modular aun no publicado: se usa el monolito anterior (linux + pyspark)
            print("[github] sin release modular (%s); pruebo el release anterior %s ..." % (vm.GH_TAG_MODULAR, vc.GH_TAG))
            for v in sorted({v for t, v, p in faltan_p if t == "pyspark" or p == "linux"}):
                vc.desde_github(v, tag=vc.GH_TAG)
        else:
            for k, m in res.items():
                if m != "ok":
                    print("[%s] %s" % (k, m))
        est_p = vm.estado_piezas(cache, piezas)
        faltan_p = [(e["pieza"], e["python"], e["plataforma"]) for e in est_p if not e["presente"]]
        if args.desde_github or args.desde_dir:
            print("")
            print(vm.formatear_piezas(est_p))
            return 0 if not faltan_p else 1
    if faltan_p:
        if not vc.hay_internet():
            print("ERROR: no hay internet (no se alcanza pypi.org; si hay proxy corporativo define HTTPS_PROXY/HTTP_PROXY).")
            print("       Alternativa: baja las piezas en otra maquina y usa --desde-dir <carpeta> o --zip <pieza.zip>.")
            return 1
        vm.preparar_pip(faltan_p, cache)
    est_p = vm.estado_piezas(cache, piezas)
    vm.guardar_manifiesto_local(cache)
    print("")
    print(vm.formatear_piezas(est_p))
    b = vc.estado_banco(cache)
    if b["sdists_faltan"] or b["pkgcode_faltan"]:
        print("Banco (interno): faltan %s. NO estan en PyPI: preparar_vendor.py --zip banco.zip"
              % ", ".join(b["sdists_faltan"] + b["pkgcode_faltan"]))
    return 0 if all(e["presente"] for e in est_p) else 3


if __name__ == "__main__":
    sys.exit(main())
