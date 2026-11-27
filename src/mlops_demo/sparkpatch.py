# -*- coding: utf-8 -*-
"""Parches de PySpark para el DEMO: spark.sql / table / read.* / write.* / jdbc."""
import os
import re

from . import datos, escritor, lector, rutas, sqlmini
from .estado import E, log

_SIMULAR = ("create", "drop", "alter", "msck", "refresh", "invalidate", "use", "compute", "analyze",
            "truncate", "grant", "revoke", "load", "comment", "unset")
_VISTA_TEMP = re.compile(r"^\s*create\s+(or\s+replace\s+)?(global\s+)?(temp|temporary)\s+view", re.I)


def _comando(job, cmd, tipo="sql"):
    E["comandos"].append({"job": job, "cmd": cmd, "tipo": tipo})


def _sql(self, sqlQuery, *a, **k):
    O = E["orig"]["sql"]
    if E["enproceso"] or not isinstance(sqlQuery, str):
        return O(self, sqlQuery, *a, **k)
    pal = sqlmini.primera_palabra(sqlQuery)
    st = lector.sitio(2)
    if pal in ("select", "with"):
        return lector.ejecutar_select(self, sqlQuery, O, a, k, st)
    if pal == "insert" or (pal == "create" and not _VISTA_TEMP.match(sqlQuery)
                           and re.search(r"\bas\s+(select|with)\b", sqlQuery, re.I)):
        r = escritor.insertar_sql(
            self, sqlQuery, lambda body: lector.ejecutar_select(self, body, O, a, k, st))
        if r is not None:
            return r
    if pal in _SIMULAR and not _VISTA_TEMP.match(sqlQuery):
        _comando(E["job"], " ".join(sqlQuery.split())[:120])
        log("sentencia SQL simulada: %s" % " ".join(sqlQuery.split())[:90])
        return self.range(0)
    return O(self, sqlQuery, *a, **k)


def _table(self, tableName):
    if E["enproceso"] or not isinstance(tableName, str):
        return E["orig"]["table"](self, tableName)
    return lector.ejecutar_select(self, "select * from " + tableName, E["orig"]["sql"], (), {},
                                  lector.sitio(2))


# ---------------------------------------------------------------- lecturas por ruta
_LLAVES = ("numcliente", "vintage")
def _llaves_del_job(sp):
    """Llaves (numcliente, vintage) de la ultima lectura del job que las trae (p. ej. el pivot que score lee antes de
    sus fuentes). None si el job no ha leido ninguna."""
    for l in reversed(E["lecturas"]):
        if l.get("job") != E["job"] or not str(l.get("origen", "")).startswith(("producida", "local")):
            continue
        nombre = str(l.get("nombre", ""))
        if nombre.rstrip("/\\").endswith("vector_assembler") or not all(c in (l.get("cols") or []) for c in _LLAVES):
            continue
        try:
            return E["orig"]["r_parquet"](sp.read, rutas.redirigir(nombre)).select(*_LLAVES).distinct()
        except Exception:
            continue
    return None
def _vector_features(sp, paths, cols):
    """Salida tipo VectorAssembler (numcliente, vintage, features_vector con metadata de nombres)
    para lecturas de 'vector_assembler' que no produjo ningun job (p. ej. el datapull no corrio)."""
    from pyspark.ml.feature import VectorAssembler
    from pyspark.sql import functions as F
    partes = [x for x in re.split(r"[\\/]+", paths[0]) if x]
    fuentes = E["features"]
    nombres = []
    for p in partes:
        if p in fuentes:
            nombres = fuentes[p]
    if not nombres:
        nombres = [n for lst in fuentes.values() for n in lst]
    if not nombres:
        return None
    base = [c for c in cols if c != "features_vector"]
    for c in ("numcliente", "vintage"):
        if c not in base:
            base.append(c)
    df, _s = datos.generar_df(sp, base + nombres, usos_sql=dict((n.lower(), {"num"}) for n in nombres))
    num = df.select(*[F.col(c) for c in base],
                    *[F.coalesce(F.col(n).cast("double"), F.lit(0.0)).alias(n) for n in nombres])
    llaves = _llaves_del_job(sp)
    if llaves is not None:
        # Las llaves al azar no empatan con las del pivot: el left join del score dejaba TODAS las features en NULL.
        # Se reparten las filas sinteticas sobre las llaves reales que el job ya leyo.
        from pyspark.sql import Window
        w = Window.orderBy(F.monotonically_increasing_id())
        k = llaves.withColumn("__i", F.row_number().over(w))
        f = num.drop(*_LLAVES).withColumn("__i", F.row_number().over(w))
        num = k.join(f, "__i", "left").drop("__i")
        num = num.select(*base, *[F.coalesce(F.col(n), F.lit(0.0)).alias(n) for n in nombres])
        log("vector_assembler sintetico: llaves (%s) tomadas de lo que el job ya leyo, para que los joins empaten"
            % ", ".join(_LLAVES))
    else:
        log("AVISO: vector_assembler sintetico con llaves al azar (el job no ha leido antes un parquet con %s): "
            "un join con otra fuente dejara estas columnas en NULL; corre antes el job que produce esa salida "
            "(p. ej. el datapull del mismo modelo)" % ", ".join(_LLAVES))
    va = VectorAssembler(inputCols=nombres, outputCol="features_vector")
    return va.transform(num).select(*base, "features_vector")


def _sintetica_ruta(paths, st, esquema=None):
    sp = lector.spark_activa()
    cols = [f.name for f in esquema.fields] if esquema is not None and hasattr(esquema, "fields") \
        else lector.columnas_sitio(st)
    if esquema is None:     # columnas que los settings declaran para esa tabla (p. ej. bloque de agregacion)
        cols = lector._unir(cols, E["registro"].get(re.split(r"[\\/]+", paths[0].rstrip("/\\"))[-1].lower(), []))
    cols = [c for c in cols if c] or ["id", "valor", "fecha"]
    if "features_vector" in cols or paths[0].rstrip("/\\").endswith("vector_assembler"):
        df = _vector_features(sp, paths, cols)
        if df is not None:
            lector._anotar(E["job"], paths[0], "sintetica (vector_assembler)", list(df.columns), E["filas"])
            return df
    df, _s = datos.generar_df(sp, cols)
    lector._anotar(E["job"], paths[0], "sintetica", list(df.columns), E["filas"])
    return df


def _leer_rutas(fn, self, paths, a, k):
    O = E["orig"]["r_" + fn]
    if E["enproceso"] or not paths or not all(isinstance(p, str) for p in paths):
        return O(self, *paths, *a, **k) if paths else O(self, *a, **k)
    dests = [rutas.redirigir(p) for p in paths]
    st = lector.sitio(3)
    if all(lector.existe_ruta(d) for d in dests):
        prod = [E["rutas_prod"].get(os.path.abspath(d)) for d in dests]
        origen = "producida:" + prod[0]["job"] if prod and prod[0] else "local"
        r = O(self, *dests, *a, **k)
        lector._anotar(E["job"], paths[0], origen, list(r.columns),
                       prod[0]["filas"] if prod and prod[0] else None)
        return r
    dd = lector.buscar_demo_data(paths[0])
    if dd:
        r = lector.leer_archivo(lector.spark_activa(), dd)
        lector._anotar(E["job"], paths[0], "demo_data", list(r.columns), None)
        return r
    return _sintetica_ruta(paths, st, getattr(self, "_bnx_schema", None))


def _mk_lector(fn):
    def f(self, *args, **k):
        if fn == "parquet":
            return _leer_rutas(fn, self, list(args), (), k)
        if not args:
            return E["orig"]["r_" + fn](self, **k)
        p = args[0]
        return _leer_rutas(fn, self, list(p) if isinstance(p, list) else [p], args[1:], k)
    return f


def _load(self, path=None, format=None, schema=None, **options):
    fmt = (format or getattr(self, "_bnx_fmt", "") or "").lower()
    opts = dict(getattr(self, "_bnx_opts", {}))
    opts.update(options)
    if fmt in ("jdbc", "teradata", "odbc") or ("url" in opts and ("dbtable" in opts or "query" in opts)):
        return _jdbc_df(opts.get("query") or opts.get("dbtable") or path or "")
    if path is None:
        return E["orig"]["r_load"](self, path, format, schema, **options)
    if fmt in ("hive", "table"):
        return lector.ejecutar_select(lector.spark_activa(), "select * from " + path,
                                      E["orig"]["sql"], (), {}, lector.sitio(2))
    ps = path if isinstance(path, list) else [path]
    fn = {"csv": "csv", "json": "json", "orc": "orc"}.get(fmt, "parquet")
    return _leer_rutas(fn, self, ps, (), {})


def _jdbc_df(consulta):
    """Teradata/JDBC/ODBC: no se conecta; df sintetico con las columnas de la consulta."""
    sp = lector.spark_activa()
    q = str(consulta).strip()
    q = re.sub(r"^\((.*)\)\s*(as\s+)?\w*\s*$", r"\1", q, flags=re.S | re.I)
    if not re.match(r"(?is)^\s*(select|with)\b", q):
        q = "select * from " + q
    _comando(E["job"], "jdbc: " + " ".join(q.split())[:100], "jdbc")
    log("conexion JDBC/Teradata simulada: %s" % " ".join(q.split())[:90])
    try:
        return lector.ejecutar_select(sp, q, E["orig"]["sql"], (), {}, lector.sitio(3))
    except Exception:
        info = sqlmini.analizar(q)
        cols = [c for lst in info["cols"].values() for c in lst] + info["ambiguas"]
        df, _s = datos.generar_df(sp, cols or ["id"], usos_sql=info["usos"])
        return df


def _jdbc(self, url, table, *a, **k):
    return _jdbc_df(table)


def _table_reader(self, tableName):
    return _table(lector.spark_activa(), tableName)


def _marca(nombre):
    def f(self, *a, **k):
        r = E["orig"][nombre](self, *a, **k)
        if nombre == "r_format":
            self._bnx_fmt = a[0] if a else k.get("source", "")
        elif nombre == "r_schema":
            self._bnx_schema = a[0] if a else k.get("schema")
        else:
            o = dict(getattr(self, "_bnx_opts", {}))
            if nombre == "r_option" and len(a) >= 2:
                o[str(a[0]).lower()] = a[1]
            elif nombre == "r_options":
                o.update(dict((str(x).lower(), y) for x, y in k.items()))
            self._bnx_opts = o
        return r
    return f


# ---------------------------------------------------------------- escrituras
def _mk_escritor(fn):
    def f(self, path, *a, **k):
        if E["enproceso"] or not isinstance(path, str):
            return E["orig"]["w_" + fn](self, path, *a, **k)
        return escritor.escribir_ruta(E["orig"]["w_" + fn], self, path, *a, fmt=fn, **k)
    return f


def _save(self, path=None, format=None, mode=None, partitionBy=None, **options):
    if E["enproceso"]:
        return E["orig"]["w_save"](self, path, format, mode, partitionBy, **options)
    if isinstance(path, str):
        return escritor.escribir_ruta(E["orig"]["w_save"], self, path, format, mode, partitionBy,
                                      fmt=str(format or getattr(self, "_bnx_fmt", "") or "parquet").lower(),
                                      **options)
    _comando(E["job"], "write sin ruta (%s)" % (format or ""), "write")
    log("escritura sin ruta simulada (%s)" % (format or ""))


def _save_as_table(self, name, format=None, mode=None, partitionBy=None, **options):
    if E["enproceso"]:
        return E["orig"]["w_saveAsTable"](self, name, format, mode, partitionBy, **options)
    escritor.escribir_tabla(self._df, name, mode or getattr(self, "_bnx_mode", None), partitionBy,
                            orig_parquet=E["orig"]["w_parquet"])


def _insert_into(self, tableName, overwrite=None):
    if E["enproceso"]:
        return E["orig"]["w_insertInto"](self, tableName, overwrite)
    escritor.escribir_tabla(self._df, tableName, "overwrite" if overwrite else "append",
                            orig_parquet=E["orig"]["w_parquet"])


def _w_jdbc(self, url, table, mode=None, properties=None):
    _comando(E["job"], "jdbc write: %s" % table, "jdbc")
    log("escritura JDBC simulada: %s" % table)


def _w_mode(self, saveMode):
    self._bnx_mode = saveMode
    return E["orig"]["w_mode"](self, saveMode)


def _text_file(self, name, *a, **k):
    return E["orig"]["tf"](self, rutas.redirigir(name) if isinstance(name, str) else name, *a, **k)


def aplicar():
    from pyspark import SparkContext
    from pyspark.sql import DataFrameReader, DataFrameWriter, SparkSession
    O = E["orig"]
    O["sql"], O["table"] = SparkSession.sql, SparkSession.table
    SparkSession.sql, SparkSession.table = _sql, _table
    for fn in ("parquet", "csv", "json", "orc", "text"):
        O["r_" + fn] = getattr(DataFrameReader, fn)
        setattr(DataFrameReader, fn, _mk_lector(fn))
        O["w_" + fn] = getattr(DataFrameWriter, fn)
        setattr(DataFrameWriter, fn, _mk_escritor(fn))
    O["r_load"], O["r_table"], O["r_jdbc"] = DataFrameReader.load, DataFrameReader.table, DataFrameReader.jdbc
    DataFrameReader.load, DataFrameReader.table, DataFrameReader.jdbc = _load, _table_reader, _jdbc
    for n in ("format", "schema", "option", "options"):
        O["r_" + n] = getattr(DataFrameReader, n)
        setattr(DataFrameReader, n, _marca("r_" + n))
    O["w_save"], O["w_saveAsTable"] = DataFrameWriter.save, DataFrameWriter.saveAsTable
    O["w_insertInto"], O["w_jdbc"], O["w_mode"] = DataFrameWriter.insertInto, DataFrameWriter.jdbc, DataFrameWriter.mode
    DataFrameWriter.save, DataFrameWriter.saveAsTable = _save, _save_as_table
    DataFrameWriter.insertInto, DataFrameWriter.jdbc, DataFrameWriter.mode = _insert_into, _w_jdbc, _w_mode
    O["tf"] = SparkContext.textFile
    SparkContext.textFile = _text_file
    from . import sparkcfg
    sparkcfg.parchear_particiones()


def quitar():
    from pyspark import SparkContext
    from pyspark.sql import DataFrameReader, DataFrameWriter, SparkSession
    O = E["orig"]
    if "sql" not in O:
        return
    SparkSession.sql, SparkSession.table = O["sql"], O["table"]
    for fn in ("parquet", "csv", "json", "orc", "text"):
        setattr(DataFrameReader, fn, O["r_" + fn])
        setattr(DataFrameWriter, fn, O["w_" + fn])
    DataFrameReader.load, DataFrameReader.table, DataFrameReader.jdbc = O["r_load"], O["r_table"], O["r_jdbc"]
    for n in ("format", "schema", "option", "options"):
        setattr(DataFrameReader, n, O["r_" + n])
    DataFrameWriter.save, DataFrameWriter.saveAsTable = O["w_save"], O["w_saveAsTable"]
    DataFrameWriter.insertInto, DataFrameWriter.jdbc, DataFrameWriter.mode = O["w_insertInto"], O["w_jdbc"], O["w_mode"]
    SparkContext.textFile = O["tf"]
    from . import sparkcfg
    sparkcfg.quitar_particiones()
