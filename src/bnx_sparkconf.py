# -*- coding: utf-8 -*-
"""bnx_sparkconf - configuracion de recursos de Spark del Framework MLOps v2.

Solo libreria estandar (Python 3.8+). Viaja dentro del paquete generado (raiz) y
tambien lo usa el portal. Lo llama run.sh ANTES de arrancar Spark:

    python bnx_sparkconf.py --modo cluster --out .bnx_spark_conf.properties -- <args de run.sh>

Que hace
  * cluster (YARN): arma la conf de LANZAMIENTO (spark.executor.*, spark.yarn.queue,
    spark.dynamicAllocation.*, spark.driver.memory ...) y la escribe como k=v, una por
    linea. run.sh la pasa al spark-submit con un --conf por clave (NO con
    --properties-file: eso reemplazaria el spark-defaults.conf del cluster).
    Prioridad (de menor a mayor):
      1. valores por defecto de este modulo (DEFAULTS_CLUSTER)
      2. spark.conf del cfg JSON del framework  ({"spark": {"conf": {...}}})
      3. spark.json del banco (--settings / $CONF_PATH): bloque 'default' o el de
         'spark_config'; el de un modelo con BNX_SPARK_MODELO; y la cola
         'spark_queue_uat' si --env uat (igual que toolbox/settings.py)
      4. BNX_DRIVER_MEMORY (solo spark.driver.memory)
      5. BNX_SPARK_CONF="k=v;k2=v2" (lo ultimo que dice el usuario)
  * local: solo calcula spark.driver.memory (en local[*] la JVM ya esta corriendo
    cuando Python crea la sesion, asi que la memoria hay que pasarla al lanzar).
  * Tambien: deteccion demo/real, deteccion de Python en workers y tabla de tiempos.
"""
import argparse
import json
import os
import re
import sys

# Valores por defecto (YARN) cuando ni el spark.json del banco ni el cfg dicen nada.
# Sin cola (usa la del usuario/cluster), asignacion dinamica y 200 particiones de shuffle.
DEFAULTS_CLUSTER = {
    "spark.dynamicAllocation.enabled": "true",
    "spark.dynamicAllocation.shuffleTracking.enabled": "true",
    "spark.sql.shuffle.partitions": "200",
}
# Claves que NUNCA se pasan: el master lo manda run.sh (--master / BNX_MASTER).
_PROHIBIDAS = ("spark.master", "spark.submit.deployMode")


def _s(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def _leer_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def es_demo(config=None, settings=None, demo_flag=False, env=None, cohort=None, fid=None):
    """DEMO = --demo, o no se pidio nada real (ni --config/--settings ni --env/--cohort/--fid).
    Todo lo demas son datos REALES."""
    return bool(demo_flag) or not (config or settings or env or cohort or fid)


def modo_ejecucion(config=None, settings=None, demo_flag=False, env=None, cohort=None, fid=None,
                   conf_path=None):
    """(demo, motivo) para los jobs de kernel. DEMO solo con --demo explicito o cuando no se
    pidio nada real; con --config/--settings/--env/--cohort/--fid/CONF_PATH es REAL."""
    if demo_flag:
        return True, "--demo explicito"
    pedidos = [n for n, v in (("--config", config), ("--settings", settings), ("CONF_PATH", conf_path),
                              ("--env", env), ("--cohort", cohort), ("--fid", fid)) if v]
    if pedidos:
        return False, "se indico " + ", ".join(pedidos) + " (y no --demo)"
    return True, "sin --config ni --settings (ni --env/--cohort/--fid)"


def dir_settings(settings=None, config=None, env=None):
    """Carpeta bin/settings del banco: --settings > $CONF_PATH > junto al --config."""
    env = os.environ if env is None else env
    d = settings or env.get("CONF_PATH")
    if not d and config:
        p = os.path.dirname(os.path.abspath(config))
        for _ in range(3):
            if os.path.isfile(os.path.join(p, "spark.json")):
                return p
            p = os.path.dirname(p)
    return d


def buscar_settings(settings=None, config=None, environ=None, bases=None, cwd=None):
    """Busca bin/settings del banco -> (carpeta o None, motivo, lugares_probados).
    Orden: --settings > $CONF_PATH > $BIN_PATH/settings > <base>/bank_src/settings (base = raiz
    del paquete) > carpeta del --config y 3 padres (con spark.json, o su subcarpeta settings/)
    > ./settings > <base>/bin/settings. Lo explicito (--settings/CONF_PATH) se devuelve tal cual
    (quien llama valida que exista); lo demas solo cuenta si trae spark.json."""
    environ = os.environ if environ is None else environ
    if settings:
        return settings, "--settings", [settings]
    if environ.get("CONF_PATH"):
        return environ["CONF_PATH"], "$CONF_PATH", [environ["CONF_PATH"]]
    cands = []
    if environ.get("BIN_PATH"):
        cands.append((os.path.join(environ["BIN_PATH"], "settings"), "$BIN_PATH/settings"))
    for b in (bases or []):
        cands.append((os.path.join(b, "bank_src", "settings"), "bank_src/settings del paquete"))
    if config:
        p = os.path.dirname(os.path.abspath(config))
        for i in range(4):
            cands.append((p, "carpeta del --config" if i == 0 else "carpeta padre del --config"))
            cands.append((os.path.join(p, "settings"), "settings/ junto al --config"))
            p = os.path.dirname(p)
    cwd = cwd or os.getcwd()
    cands.append((os.path.join(cwd, "settings"), "./settings"))
    for b in (bases or []):
        cands.append((os.path.join(b, "bin", "settings"), "bin/settings del paquete"))
    probados = []
    for d, motivo in cands:
        if d not in probados:
            probados.append(d)
        if os.path.isfile(os.path.join(d, "spark.json")):
            return d, motivo, probados
    return None, "no encontrado", probados


def leer_spark_json(settings_dir, env_banco=None, modelo=None):
    """Conf de Spark del spark.json del banco -> (dict, origen) o ({}, None).
    Bloque: el de 'spark_config' (nombre de bloque, p.ej. "default", o dict); con
    `modelo`, el 'spark_config' de ese modelo. Con --env uat, la cola es 'spark_queue_uat'."""
    if not settings_dir:
        return {}, None
    path = os.path.join(settings_dir, "spark.json")
    top = _leer_json(path)
    if top is None:
        return {}, None
    bloque, nombre = None, "default"
    if modelo and isinstance(top.get(modelo), dict) and isinstance(top[modelo].get("spark_config"), dict):
        bloque, nombre = top[modelo]["spark_config"], modelo
    else:
        sel = top.get("spark_config", "default")
        if isinstance(sel, dict):
            bloque, nombre = sel, "spark_config"
        elif isinstance(sel, str) and isinstance(top.get(sel), dict):
            bloque, nombre = top[sel], sel
        elif isinstance(top.get("default"), dict):
            bloque = top["default"]
    if not isinstance(bloque, dict):
        return {}, None
    conf = {str(k): _s(v) for k, v in bloque.items() if str(k).startswith("spark.")}
    if (env_banco or "").lower() == "uat" and top.get("spark_queue_uat"):
        conf["spark.yarn.queue"] = _s(top["spark_queue_uat"])
    return conf, "%s [%s]" % (path, nombre)


def parse_extra(texto):
    """BNX_SPARK_CONF: pares k=v separados por ';' o saltos de linea."""
    out = {}
    for tok in re.split(r"[;\n]+", texto or ""):
        tok = tok.strip()
        if "=" in tok:
            k, v = tok.split("=", 1)
            if k.strip():
                out[k.strip()] = v.strip()
    return out


def conf_cluster(settings_dir=None, env_banco=None, cfg=None, modelo=None, environ=None):
    """Conf de lanzamiento para YARN -> (dict, {clave: origen})."""
    environ = os.environ if environ is None else environ
    conf, origen = {}, {}

    def aplicar(d, quien):
        for k, v in d.items():
            if k in _PROHIBIDAS:
                continue
            conf[k] = _s(v)
            origen[k] = quien
    aplicar(DEFAULTS_CLUSTER, "defecto")
    cfg_spark = (cfg or {}).get("spark") if isinstance(cfg, dict) else None
    if isinstance(cfg_spark, dict):
        if isinstance(cfg_spark.get("conf"), dict):
            aplicar(cfg_spark["conf"], "cfg")
        aplicar(dict((k, v) for k, v in cfg_spark.items() if str(k).startswith("spark.")), "cfg")
    sj, ruta = leer_spark_json(settings_dir, env_banco, modelo)
    if sj:
        aplicar(sj, "spark.json")
    if environ.get("BNX_DRIVER_MEMORY"):
        aplicar({"spark.driver.memory": environ["BNX_DRIVER_MEMORY"]}, "BNX_DRIVER_MEMORY")
    aplicar(parse_extra(environ.get("BNX_SPARK_CONF")), "BNX_SPARK_CONF")
    return conf, origen


def nucleos(master=None):
    """Nucleos de un master local[N] / local[*] (None -> todos los del nodo)."""
    m = re.match(r"local\[(\d+|\*)\]", master or "local[*]")
    if m and m.group(1).isdigit():
        return int(m.group(1))
    return os.cpu_count() or 1


def shuffle_local(cores):
    return max(8, 2 * int(cores))


def memoria_driver_local(cfg=None, environ=None):
    """spark.driver.memory para local[*]: BNX_DRIVER_MEMORY > cfg > 50% de la RAM (1g..32g)."""
    environ = os.environ if environ is None else environ
    if environ.get("BNX_DRIVER_MEMORY"):
        return environ["BNX_DRIVER_MEMORY"], "BNX_DRIVER_MEMORY"
    cc = (((cfg or {}).get("spark") or {}).get("conf") or {}) if isinstance(cfg, dict) else {}
    if cc.get("spark.driver.memory"):
        return str(cc["spark.driver.memory"]), "cfg"
    try:
        ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        gb = max(1, min(32, int(ram / 2 / (1024 ** 3))))
        return "%dg" % gb, "50% de la RAM del nodo"
    except (ValueError, OSError, AttributeError):
        return None, None


def escribir_properties(conf, path):
    with open(path, "w", encoding="utf-8") as fh:
        for k in sorted(conf):
            fh.write("%s=%s\n" % (k, conf[k]))


def resumen_conf(conf, origen=None):
    """Lineas legibles con lo que importa para el rendimiento."""
    g = conf.get
    origen = origen or {}

    def o(k):
        return " (%s)" % origen[k] if k in origen else ""
    din = str(g("spark.dynamicAllocation.enabled", "")).lower() == "true"
    if din:
        ex = "dinamicos min=%s initial=%s max=%s" % (
            g("spark.dynamicAllocation.minExecutors", "0"),
            g("spark.dynamicAllocation.initialExecutors", g("spark.dynamicAllocation.minExecutors", "0")),
            g("spark.dynamicAllocation.maxExecutors", "sin limite"))
    else:
        ex = "fijos instances=%s" % g("spark.executor.instances", "(defecto del cluster)")
    return [
        "cola=%s%s" % (g("spark.yarn.queue", "(defecto del usuario)"), o("spark.yarn.queue")),
        "executors: %s" % ex,
        "por executor: cores=%s memoria=%s overhead=%s" % (
            g("spark.executor.cores", "(defecto)"), g("spark.executor.memory", "(defecto)"),
            g("spark.executor.memoryOverhead", "(defecto)")),
        "driver.memory=%s%s" % (g("spark.driver.memory", "(defecto)"), o("spark.driver.memory")),
        "sql.shuffle.partitions=%s%s" % (g("spark.sql.shuffle.partitions", "(defecto)"),
                                         o("spark.sql.shuffle.partitions")),
    ]


# ---------------------------------------------------------------------------
# Python en los WORKERS (aviso estatico)
# ---------------------------------------------------------------------------
_PATRONES_WORKERS = (
    ("udf", re.compile(r"(?<![\w.])(?:F\.|functions\.|sf\.)?udf\s*\(|@\s*(?:F\.|functions\.)?udf\b|\.udf\.register\s*\(")),
    ("pandas_udf", re.compile(r"\bpandas_udf\b")),
    ("applyInPandas/mapInPandas/mapInArrow",
     re.compile(r"\.(applyInPandasWithState|applyInPandas|mapInPandas|mapInArrow|applyInArrow)\s*\(")),
    (".rdd", re.compile(r"\.rdd\b")),
    ("rdd.map/flatMap/foreach/mapPartitions",
     re.compile(r"\b\w*rdd\w*\.(map|flatMap|filter|reduceByKey|mapValues|groupByKey|foreach\w*|mapPartitions\w*)\s*\(")),
    ("foreach/foreachPartition/mapPartitions/foreachBatch",
     re.compile(r"\.(foreachPartition|foreachBatch|mapPartitions|mapPartitionsWithIndex)\s*\(|\bdf\w*\.foreach\s*\(")),
    ("sparkContext.parallelize", re.compile(r"\.parallelize\s*\(")),
    ("pandas_api/pyspark.pandas",
     re.compile(r"pyspark\.pandas|from\s+pyspark\s+import\s+pandas|\.pandas_api\s*\(|to_pandas_on_spark")),
    ("xgboost.spark/SparkXGB", re.compile(r"xgboost\.spark|\bSparkXGB\w*")),
    ("mlflow spark_udf", re.compile(r"\bspark_udf\s*\(")),
)
_ML_IMPORT = re.compile(r"^\s*(?:import|from)\s+(sklearn|xgboost|lightgbm|scipy|statsmodels)\b", re.M)
AVISO_WORKERS = ("este job ejecuta Python en los workers: en YARN fallara si los nodos no tienen "
                 "Python 3.11 con estas librerias (run.sh en modo cluster las envia con el job: BNX_DEPS_EXECUTORS=1, "
                 "BNX_EXECUTOR_PYTHON=/ruta/python3.11); alternativas: reescribir con funciones de Spark SQL, "
                 "o hacer el calculo en el driver tras agregar (toPandas sobre un resultado pequeno)")


def detectar_python_en_workers(code):
    """Usos que lanzan Python en los executors -> [{"patron","linea","codigo"}] (vacio si no hay).
    Analisis por lineas (no falla con codigo Python 2 o incompleto); ignora comentarios."""
    hallazgos, vistos = [], set()
    usa_ml = sorted(set(_ML_IMPORT.findall(code or "")))
    for n, linea in enumerate((code or "").splitlines(), 1):
        txt = linea.split("#", 1)[0]
        if not txt.strip():
            continue
        for patron, rx in _PATRONES_WORKERS:
            if rx.search(txt) and (patron, n) not in vistos:
                vistos.add((patron, n))
                h = {"patron": patron, "linea": n, "codigo": linea.strip()[:160]}
                if patron in ("udf", "pandas_udf") and usa_ml:
                    h["nota"] = "el archivo importa %s: si se usan dentro de la udf, cada worker las necesita" % ", ".join(usa_ml)
                hallazgos.append(h)
    return hallazgos


# ---------------------------------------------------------------------------
# Dependencias Python para los EXECUTORS (sin instalar nada en los otros nodos)
# ---------------------------------------------------------------------------
# Si el job ejecuta Python en los workers (UDF...), cloudpickle importa en CADA executor los
# modulos que usa la funcion (numpy, unidecode...). run.sh empaqueta el site-packages del venv
# (sin interprete, sin pyspark/py4j) en un .tar.gz, lo envia con --archives <tgz>#bnxdeps y pone
# spark.executorEnv.PYTHONPATH=./bnxdeps. Solo sirve si el Python de los executors es de la
# MISMA version menor que el del venv: antes se hace un PROBE (mini job en YARN).
_EXCLUIR_DEPS = ("pyspark", "py4j")
DEPS_ALIAS = "bnxdeps"
def _es_excluido(nombre):
    if nombre == "__pycache__" or nombre.endswith(".pyc"):
        return True
    return nombre.lower().replace("_", "-").split("-")[0].split(".")[0] in _EXCLUIR_DEPS
def site_packages():
    import sysconfig
    return os.environ.get("BNX_DEPS_SITE_PACKAGES") or sysconfig.get_paths()["purelib"]
def minor_actual():
    return "%d.%d" % sys.version_info[:2]
def hash_venv(sp=None):
    """Hash estable del contenido instalado (nombre-version de cada dist-info + version menor de Python)."""
    import hashlib
    sp = sp or site_packages()
    h = hashlib.sha1(minor_actual().encode())
    for n in sorted(os.listdir(sp)):
        if n.endswith((".dist-info", ".egg-info")) and not _es_excluido(n):
            h.update(n.encode())
    return h.hexdigest()[:12]
def empaquetar_deps(destino, sp=None):
    """Crea (o reutiliza) <destino>/bnxdeps-<hash>.tar.gz con el CONTENIDO de site-packages en la raiz,
    sin pyspark/py4j/__pycache__. Devuelve (ruta, hash, mb, reutilizado)."""
    import tarfile
    sp = sp or site_packages()
    hv = hash_venv(sp)
    os.makedirs(destino, exist_ok=True)
    ruta = os.path.join(destino, "bnxdeps-%s.tar.gz" % hv)
    if os.path.isfile(ruta) and os.path.getsize(ruta) > 0:
        return ruta, hv, os.path.getsize(ruta) / 1048576.0, True
    def filtro(ti):
        return None if any(_es_excluido(parte) for parte in ti.name.split("/")) else ti
    tmp = ruta + ".tmp"
    with tarfile.open(tmp, "w:gz") as tf:
        for n in sorted(os.listdir(sp)):
            if not _es_excluido(n):
                tf.add(os.path.join(sp, n), arcname=n, filter=filtro)
    os.replace(tmp, ruta)
    for viejo in os.listdir(destino):
        if viejo.startswith("bnxdeps-") and viejo.endswith(".tar.gz") and viejo != os.path.basename(ruta):
            try:
                os.remove(os.path.join(destino, viejo))
            except OSError:
                pass
    return ruta, hv, os.path.getsize(ruta) / 1048576.0, False
def escanear_workers(raices=(), wheels_dir=None):
    """Busca Python en workers en el codigo del modelo/bank_src (raices) y dentro de las wheels del banco.
    -> [{"archivo","linea","patron","codigo"}]. Archivos de wheels: 'wheel.whl!ruta/interna.py'."""
    import zipfile
    out = []
    try:
        import bank_compat as _bcn          # junto a este archivo en el paquete: analisis de UDF nativizables
        _udfs = getattr(_bcn, "analizar_udfs_fuente", None)
    except Exception:
        _udfs = None
    def agregar(nombre, texto):
        hs = detectar_python_en_workers(texto)
        nat = {}
        if hs and _udfs is not None:
            try:
                nat = dict((u["linea"], u) for u in _udfs(texto))
            except Exception:
                nat = {}
        for h in hs:
            r = {"archivo": nombre, "linea": h["linea"], "patron": h["patron"], "codigo": h["codigo"]}
            u = nat.get(h["linea"])
            r["nativa"] = bool(u and u.get("nativa") and h["patron"] == "udf")
            if u:
                r["udf"] = u.get("nombre")
                if not u.get("nativa"):
                    r["motivo"] = u.get("motivo")
            out.append(r)
    for raiz in raices:
        for base, dirs, files in os.walk(raiz):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".venv", ".git", "logs")]
            for f in sorted(files):
                if f.endswith(".py"):
                    fp = os.path.join(base, f)
                    try:
                        with open(fp, encoding="utf-8", errors="replace") as fh:
                            agregar(os.path.relpath(fp), fh.read())
                    except OSError:
                        pass
    if wheels_dir and os.path.isdir(wheels_dir):
        for w in sorted(os.listdir(wheels_dir)):
            if not w.endswith(".whl"):
                continue
            try:
                with zipfile.ZipFile(os.path.join(wheels_dir, w)) as z:
                    for n in sorted(z.namelist()):
                        if n.endswith(".py"):
                            agregar("%s!%s" % (w, n), z.read(n).decode("utf-8", "replace"))
            except (OSError, zipfile.BadZipFile):
                pass
    return out
_RX_VERSION_WORKER = re.compile(r"Python in worker has different version\D*([\d.]+)\D+than that in driver\D*([\d.]+)")
def _mensaje_opciones(minor_venv, motivo, detalle=""):
    ej = ("from pyspark.sql import functions as F\n"
          "        ORIG, DEST = 'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN'\n"
          "        df = df.withColumn(c, F.lower(F.translate(F.coalesce(F.col(c), F.lit('')), ORIG, DEST)))\n"
          "        # en SQL: lower(translate(coalesce(col, ''), 'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN'))")
    return "\n".join([
        "!" * 72,
        "[BNX] LOS EXECUTORS NO PUEDEN EJECUTAR LAS UDF DE ESTE PAQUETE: " + motivo,
        detalle,
        "El paquete trae Python %s; los workers de YARN deben tener la MISMA version menor." % minor_venv,
        "No se corre el job a ciegas (fallaria a mitad con 'No module named ...'). Opciones:",
        "  (i)   Si los nodos tienen Python %s:  BNX_EXECUTOR_PYTHON=/usr/bin/python%s BNX_SPARK=cluster bash run.sh ..." % (minor_venv, minor_venv),
        "  (ii)  Correr ese job en el edge, sin YARN:  BNX_SPARK=local bash run.sh ...   (local[*])",
        "  (iii) Reescribir la UDF con funciones de Spark SQL. quita_acentos:",
        "        " + ej,
        "  (iv)  BNX_UDF_NATIVAS=1 cambia las UDF simples por expresiones nativas de Spark (run.sh lo hace solo",
        "        si TODAS las detectadas se pueden cambiar; ver la lista de arriba)",
        "  (forzar, bajo tu riesgo: BNX_PROBE_IGNORAR=1; desactivar todo: BNX_DEPS_EXECUTORS=0)",
        "!" * 72]).replace("\n\n", "\n")
def evaluar_probe(res, minor_venv, mods=()):
    """res = {"ok":bool, "workers":[{python,version,mods}], "error": str} -> (estado, mensaje).
    estado: True (usable), False (NO usable), None (no se pudo saber)."""
    if res.get("workers"):
        w = res["workers"][0]
        vers = ".".join(str(x) for x in w.get("version", [])[:2])
        if vers != minor_venv:
            return False, _mensaje_opciones(minor_venv, "Python %s en los workers (%s)" % (vers, w.get("python")))
        falta = [m for m in mods if not (w.get("mods") or {}).get(m)]
        if falta:
            return False, _mensaje_opciones(minor_venv, "Python %s en los workers pero no importa %s con bnxdeps"
                                            % (vers, ", ".join(falta)), "python de los workers: %s" % w.get("python"))
        return True, "executors OK: %s (Python %s), importan %s con ./%s" % (w.get("python"), vers, ", ".join(mods) or "-", DEPS_ALIAS)
    err = res.get("error") or ""
    m = _RX_VERSION_WORKER.search(err)
    if m:
        return False, _mensaje_opciones(minor_venv, "Python %s en los workers, %s en el driver" % (m.group(1), m.group(2)))
    return None, "no se pudo comprobar el Python de los executors: %s" % (err.strip().splitlines()[-1][:200] if err.strip() else "sin detalle")
def ejecutar_probe(salida, mods, minor_venv):
    """Corre DENTRO de spark-submit (driver): mini job que reporta el Python de los executors."""
    res = {"minor_venv": minor_venv, "mods_pedidos": list(mods), "ts": __import__("time").time()}
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.appName("bnx_probe_executors").getOrCreate()
        mods_l = list(mods)
        def _w(_):
            import sys, importlib, socket
            r = {"python": sys.executable, "version": list(sys.version_info[:3]), "host": socket.gethostname(), "mods": {}}
            for m in mods_l:
                try:
                    r["mods"][m] = getattr(importlib.import_module(m), "__file__", None) or "ok"
                except Exception as e:
                    r["mods"][m] = None
                    r["err_" + m] = repr(e)[:200]
            return r
        res["workers"] = spark.sparkContext.parallelize(range(2), 2).map(_w).collect()
        spark.stop()
    except Exception as e:
        res["error"] = str(e)[-3000:]
    estado, msg = evaluar_probe(res, minor_venv, mods)
    res["estado"], res["mensaje"] = estado, msg
    if estado is not None:   # lo desconocido no se cachea
        try:
            with open(salida, "w", encoding="utf-8") as fh:
                json.dump(res, fh, ensure_ascii=False, indent=1)
        except OSError:
            pass
    print("[probe] " + msg)
    return 0 if estado is not False else 3
def _cli_deps(argv):
    """Modos de run.sh: --scan-workers | --empaquetar-deps | --probe | --probe-estado | --workers-nativos."""
    ap = argparse.ArgumentParser(description="Dependencias Python para los executors")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scan-workers", action="store_true")
    g.add_argument("--empaquetar-deps", action="store_true")
    g.add_argument("--probe", action="store_true")
    g.add_argument("--probe-estado", action="store_true")
    g.add_argument("--workers-nativos", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--wheels")
    ap.add_argument("--dir", default=".bnx_deps")
    ap.add_argument("--mods", default="")
    ap.add_argument("raices", nargs="*")
    a = ap.parse_args(argv)
    mods = [m for m in a.mods.split(",") if m]
    if a.scan_workers:
        hs = escanear_workers([r for r in a.raices if os.path.isdir(r)], a.wheels)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump({"hallazgos": hs}, fh, ensure_ascii=False, indent=1)
        archivos = sorted(set(h["archivo"] for h in hs))
        print("[deps] Python en workers: %d uso(s) en %d archivo(s)" % (len(hs), len(archivos)))
        for h in hs[:4]:
            print("[deps]   %s:%d (%s)" % (h["archivo"], h["linea"], h["patron"]))
        return 10 if hs else 0
    if a.empaquetar_deps:
        import shlex
        sp = site_packages()
        ruta, hv, mb, reus = empaquetar_deps(a.dir, sp)
        presentes = [m for m in (mods or ["numpy"]) if os.path.exists(os.path.join(sp, m)) or os.path.exists(os.path.join(sp, m + ".py"))]
        with open(a.out, "w", encoding="utf-8") as fh:
            for k, v in (("BNX_DEPS_TGZ", ruta), ("BNX_DEPS_HASH", hv), ("BNX_DEPS_MINOR", minor_actual()),
                         ("BNX_DEPS_MB", "%.0f" % mb), ("BNX_DEPS_MODS", ",".join(presentes)),
                         ("BNX_DEPS_REUSO", "1" if reus else "0")):
                fh.write("%s=%s\n" % (k, shlex.quote(v)))
        return 0
    if a.probe:
        return ejecutar_probe(a.out, mods, minor_actual())
    if a.workers_nativos:
        try:
            with open(a.out, encoding="utf-8") as fh:
                hs = json.load(fh).get("hallazgos", [])
        except (OSError, ValueError):
            return 2
        nat = [h for h in hs if h.get("nativa")]
        resto = [h for h in hs if not h.get("nativa")]
        print("[deps] UDF que se cambian por expresiones nativas de Spark (BNX_UDF_NATIVAS=1): %d" % len(nat))
        for h in nat[:8]:
            print("[deps]   %s %s:%d" % (h.get("udf") or "", h["archivo"], h["linea"]))
        if resto:
            print("[deps] Python en workers que NO se puede cambiar por expresiones nativas: %d" % len(resto))
            for h in resto[:8]:
                print("[deps]   %s:%d (%s%s)" % (h["archivo"], h["linea"], h["patron"],
                                              (": " + h["motivo"]) if h.get("motivo") else ""))
        return 0 if not resto else 4
    try:
        with open(a.out, encoding="utf-8") as fh:
            res = json.load(fh)
    except (OSError, ValueError):
        return 2
    print("[probe] (cache) " + res.get("mensaje", ""))
    return 3 if res.get("estado") is False else 0
# ---------------------------------------------------------------------------
# Tabla de tiempos
# ---------------------------------------------------------------------------
def tabla_tiempos(filas, master=None, app_id=None, resumen_cpu=None):
    """filas: [{"etapa","nombre","seg","particiones","archivos","filas","estado"} (+ cpu_prom, cpu_pico, nuc_prom,
    mem_pico, tareas, eficiencia si el monitor de recursos esta activo)] -> texto."""
    def f(v, fmt="%s"):
        return "-" if v is None else fmt % v
    con_cpu = any(r.get("cpu_prom") is not None for r in filas)
    out = ["TABLA DE TIEMPOS  master=%s  applicationId=%s" % (master or "?", app_id or "?")]
    if con_cpu:
        out.append("%-10s %-24s %9s %8s %8s %7s %9s %7s %6s %7s %8s %12s  %s" % (
            "etapa", "fuente/job", "segundos", "CPU %prom", "CPU %pico", "nuc.prom", "mem MB", "tareas", "efic.",
            "partic.", "archivos", "filas", "estado"))
    else:
        out.append("%-10s %-28s %9s %7s %8s %12s  %s" % ("etapa", "fuente/job", "segundos", "partic.",
                                                         "archivos", "filas", "estado"))
    total = 0.0
    for r in filas:
        total += r.get("seg") or 0.0
        if con_cpu:
            out.append("%-10s %-24s %9s %8s %8s %7s %9s %7s %6s %7s %8s %12s  %s" % (
                r.get("etapa", ""), str(r.get("nombre", ""))[:24], f(r.get("seg"), "%.1f"),
                f(r.get("cpu_prom"), "%.0f"), f(r.get("cpu_pico"), "%.0f"), f(r.get("nuc_prom"), "%.2f"),
                f(r.get("mem_pico"), "%.0f"), f(r.get("tareas")), f(r.get("eficiencia"), "%.2f"),
                f(r.get("particiones")), f(r.get("archivos")), f(r.get("filas")), r.get("estado", "")))
        else:
            out.append("%-10s %-28s %9s %7s %8s %12s  %s" % (
                r.get("etapa", ""), str(r.get("nombre", ""))[:28], f(r.get("seg"), "%.1f"),
                f(r.get("particiones")), f(r.get("archivos")), f(r.get("filas")), r.get("estado", "")))
    out.append("%-10s %-28s %9.1f" % ("TOTAL", "", total))
    if filas:
        peor = max(filas, key=lambda r: r.get("seg") or 0.0)
        out.append("Lo mas lento: %s '%s' (%.1f s, %.0f%% del total)" % (
            peor.get("etapa"), peor.get("nombre"), peor.get("seg") or 0.0,
            100.0 * (peor.get("seg") or 0.0) / total if total else 0.0))
    if resumen_cpu:
        out.append(resumen_cpu)
    return "\n".join(out)
# ---------------------------------------------------------------------------
# CLI (lo usa run.sh)
# ---------------------------------------------------------------------------
def main(argv=None):
    _av = sys.argv[1:] if argv is None else list(argv)
    if _av and _av[0] in ("--scan-workers", "--empaquetar-deps", "--probe", "--probe-estado", "--workers-nativos"):
        return _cli_deps(_av)
    ap = argparse.ArgumentParser(description="Conf de Spark para run.sh")
    ap.add_argument("--modo", choices=("cluster", "local"), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("resto", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    resto = [x for x in a.resto if x != "--"] if a.resto and a.resto[0] == "--" else a.resto
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--config")
    p.add_argument("--settings")
    p.add_argument("--env")
    p.add_argument("--demo", action="store_true")
    args, _ = p.parse_known_args(resto)
    demo = es_demo(args.config, args.settings, args.demo)
    cfg = _leer_json(args.config) if args.config else None
    if a.modo == "cluster":
        base = os.path.dirname(os.path.abspath(__file__))
        sdir, motivo, probados = buscar_settings(args.settings, args.config, bases=[base])
        if sdir and not os.path.isdir(sdir):
            print("[spark-conf] AVISO: la carpeta de settings '%s' (%s) no existe" % (sdir, motivo))
            sdir = None
        conf, origen = conf_cluster(sdir, args.env, cfg, os.environ.get("BNX_SPARK_MODELO") or None)
        escribir_properties(conf, a.out)
        print("[spark-conf] YARN: %d clave(s) de lanzamiento -> %s (un --conf por clave)" % (len(conf), a.out))
        for l in resumen_conf(conf, origen):
            print("[spark-conf]   " + l)
        cuenta = {}
        for k in conf:
            cuenta[origen.get(k, "?")] = cuenta.get(origen.get(k, "?"), 0) + 1
        print("[spark-conf] fuentes: " + ", ".join("%s=%d" % (q, n) for q, n in sorted(cuenta.items())))
        if sdir and leer_spark_json(sdir, args.env)[1]:
            print("[spark-conf] spark.json del banco: %s (settings: %s)" % (leer_spark_json(sdir, args.env)[1], motivo))
        elif not cuenta.get("spark.json"):
            print("[spark-conf] AVISO: sin spark.json del banco (buscado en: %s)" % ", ".join(probados[:6]))
            if not cuenta.get("cfg"):
                print("[spark-conf] AVISO: tampoco hay spark.conf en el --config: solo %d clave(s) por defecto; "
                      "cola y executors los decide el cluster. Para los del banco: --settings <bin/settings> "
                      "--env uat" % len(conf))
        return 0
    conf = {}
    if demo:
        print("[spark-conf] DEMO: local[N] (BNX_DEMO_CORES o min(4, cpus-1)), AQE y particiones acotadas (datos sinteticos)")
    else:
        mem, quien = memoria_driver_local(cfg)
        if mem:
            conf["spark.driver.memory"] = mem
            print("[spark-conf] local[*]: spark.driver.memory=%s (%s) se pasa al lanzar (--driver-memory)" % (mem, quien))
    escribir_properties(conf, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
