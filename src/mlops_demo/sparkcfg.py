# -*- coding: utf-8 -*-
"""Configuracion de Spark SOLO para el DEMO/simulacion (nunca para datos reales).

Antes: local[1] y 2 particiones; un job que hace repartition(1000) o joins con spark.sql.shuffle.partitions
grande lanzaba stages de 1000 tareas en UN nucleo (ccp_datapull tardaba 65 s con 50 filas). Ahora:
  - master local[N], N = BNX_DEMO_CORES o min(4, max(1, cpu_count-1)) (Mac y contenedor Linux: 4 como maximo);
  - spark.sql.shuffle.partitions = max(4, N), spark.default.parallelism = N;
  - AQE: coalescePartitions con initialPartitionNum = 2N y advisoryPartitionSize 1m (colapsa particiones vacias);
  - df.repartition(n)/coalesce(n)/repartitionByRange(n) con n > 2N se limita a 2N (log '[demo] repartition(1000) -> 20');
  - spark.driver.memory = BNX_DEMO_MEM (default 4g) (se fija al crear la JVM);
  - autoBroadcastJoinThreshold = 10m aunque el spark.json del banco diga -1;
  - spark.ui.showConsoleProgress=false: sin barras [Stage ...] en el terminal.
Compatible con Python 3.8.
"""
import os
import re
from .estado import E, log

MAX_NUCLEOS = 32
DEFECTO_NUCLEOS = 4          # default del demo: min(4, max(1, cpu_count-1)); BNX_DEMO_CORES lo cambia


def nucleos():
    try:
        n = int(os.environ.get("BNX_DEMO_CORES") or 0)
    except ValueError:
        n = 0
    if n <= 0:
        n = min(DEFECTO_NUCLEOS, max(1, (os.cpu_count() or 2) - 1))
    return max(1, min(n, MAX_NUCLEOS))


def memoria():
    m = (os.environ.get("BNX_DEMO_MEM") or "4g").strip().lower()
    return m if re.match(r"^\d+[mg]$", m) else "4g"


def config(nuc=None, mem=None):
    """(master, {conf}) del demo."""
    n = nuc or nucleos()
    mem = mem or memoria()
    conf = {
        "spark.ui.enabled": "false",
        "spark.ui.showConsoleProgress": "false",
        "spark.sql.shuffle.partitions": str(max(4, n)),
        "spark.default.parallelism": str(n),
        "spark.sql.adaptive.enabled": "true",
        "spark.sql.adaptive.coalescePartitions.enabled": "true",
        "spark.sql.adaptive.coalescePartitions.initialPartitionNum": str(n * 2),
        "spark.sql.adaptive.advisoryPartitionSizeInBytes": "1m",
        "spark.sql.autoBroadcastJoinThreshold": "10m",
        "spark.driver.memory": mem,
    }
    return "local[%d]" % n, conf


def resumen(nuc=None, mem=None):
    """'demo: local[4] de 10 nucleos | shuffle 4 | AQE on | driver 4g'."""
    master, conf = config(nuc, mem)
    return "demo: %s de %d nucleos | shuffle %s | AQE on | driver %s" % (
        master, os.cpu_count() or 1, conf["spark.sql.shuffle.partitions"], conf["spark.driver.memory"])


def aplicar_a(builder, nuc=None, mem=None):
    """Aplica la config al SparkSession.builder (antes de crear la JVM, para que driver.memory surta efecto)."""
    master, conf = config(nuc, mem)
    builder = builder.master(master)
    for k, v in conf.items():
        builder = builder.config(k, v)
    return builder


def limite_particiones():
    return nucleos() * 2


def limitar(n):
    """n limitado a 2N (o n si ya es menor / no es int)."""
    if isinstance(n, bool) or not isinstance(n, int):
        return n
    return min(n, limite_particiones())


_ORIG = {}   # (df, clase, metodo) -> funcion original; fuera de E: estado.reset() no debe perderlas


def _clases_df():
    """DataFrame de pyspark.sql y, en PySpark 4, tambien la clase 'classic' que es la que lleva repartition()."""
    from pyspark.sql import DataFrame
    out = [DataFrame]
    try:
        from pyspark.sql.classic.dataframe import DataFrame as _Classic
        if _Classic is not DataFrame:
            out.append(_Classic)
    except Exception:
        pass
    return out


def parchear_particiones():
    """df.repartition / coalesce / repartitionByRange con un numero enorme de particiones (solo demo)."""
    O = _ORIG
    if O:
        return                       # ya parcheado: no apilar parches
    for cls in _clases_df():
        for n in ("repartition", "coalesce", "repartitionByRange"):
            if n not in cls.__dict__:
                continue
            orig = cls.__dict__[n]
            O[("df", cls, n)] = orig

            def _w(self, *args, __o=orig, __n=n, **k):
                if args and isinstance(args[0], int) and not isinstance(args[0], bool):
                    nuevo = limitar(args[0])
                    if nuevo != args[0]:
                        log("%s(%d) -> %d (demo: %d nucleos; el codigo del banco no se modifica)" % (
                            __n, args[0], nuevo, nucleos()))
                        args = (nuevo,) + tuple(args[1:])
                return __o(self, *args, **k)
            _w.__name__ = n
            setattr(cls, n, _w)


def quitar_particiones():
    O = _ORIG
    for clave in [k for k in O if isinstance(k, tuple) and k and k[0] == "df"]:
        setattr(clave[1], clave[2], O.pop(clave))
