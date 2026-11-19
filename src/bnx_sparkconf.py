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
                 "Python 3.11 con estas librerias; alternativas: reescribir con funciones de Spark SQL, "
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
# Tabla de tiempos
# ---------------------------------------------------------------------------
def tabla_tiempos(filas, master=None, app_id=None):
    """filas: [{"etapa","nombre","seg","particiones","archivos","filas","estado"}] -> texto."""
    def f(v, fmt="%s"):
        return "-" if v is None else fmt % v
    out = ["TABLA DE TIEMPOS  master=%s  applicationId=%s" % (master or "?", app_id or "?"),
           "%-10s %-28s %9s %7s %8s %12s  %s" % ("etapa", "fuente/job", "segundos", "partic.",
                                                 "archivos", "filas", "estado")]
    total = 0.0
    for r in filas:
        total += r.get("seg") or 0.0
        out.append("%-10s %-28s %9s %7s %8s %12s  %s" % (
            r.get("etapa", ""), str(r.get("nombre", ""))[:28], f(r.get("seg"), "%.1f"),
            f(r.get("particiones")), f(r.get("archivos")), f(r.get("filas")), r.get("estado", "")))
    out.append("%-10s %-28s %9.1f" % ("TOTAL", "", total))
    if filas:
        peor = max(filas, key=lambda r: r.get("seg") or 0.0)
        out.append("Lo mas lento: %s '%s' (%.1f s, %.0f%% del total)" % (
            peor.get("etapa"), peor.get("nombre"), peor.get("seg") or 0.0,
            100.0 * (peor.get("seg") or 0.0) / total if total else 0.0))
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI (lo usa run.sh)
# ---------------------------------------------------------------------------
def main(argv=None):
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
        print("[spark-conf] DEMO: local[1], 2 particiones de shuffle (datos sinteticos)")
    else:
        mem, quien = memoria_driver_local(cfg)
        if mem:
            conf["spark.driver.memory"] = mem
            print("[spark-conf] local[*]: spark.driver.memory=%s (%s) se pasa al lanzar (--driver-memory)" % (mem, quien))
    escribir_properties(conf, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
