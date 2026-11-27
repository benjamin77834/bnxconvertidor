# -*- coding: utf-8 -*-
"""Log de diagnostico en la ESCRITURA de cada job del banco (generico, para cualquier modelo).

Al terminar cada escritura (df.write.parquet/save/saveAsTable/insertInto ...) informa, en pantalla y en el log:
  * columnas 100% nulas (y 100% NaN) de lo escrito;
  * columnas cuyo % de nulos SUBIO respecto a las entradas (lecturas del mismo job);
  * unas filas de ejemplo;
  * el modo de las UDF (original en Python vs reemplazo nativo) y los parches de compatibilidad activos.
No cambia datos ni rompe el job: cualquier fallo del diagnostico se traga y se avisa en una linea.

Variables de entorno
  BNX_DIAG_ESCRITURA   1 (por defecto) | 0/off/no/false para apagarlo.
  BNX_DIAG_FILAS       tamano de la muestra (defecto 20000 filas).
  BNX_DIAG_MUESTRA     filas de ejemplo que se imprimen (defecto 3; 0 = no imprimir valores).
  BNX_DIAG_LOG         archivo extra donde anexar el diagnostico (ademas de pantalla y LOG_FILE_PATH).

Por que ENCENDIDO por defecto: el sintoma que motiva este modulo (columnas que salen NULL sin ningun error) no
da ninguna senal si el diagnostico esta apagado, y el costo es acotado: UNA pasada de agregacion sobre una
muestra (limit N) de lo escrito, no un count/collect de la tabla completa.
  - Escritura a ruta con mode overwrite/error y formato parquet/orc: se relee lo escrito (lectura columnar de
    N filas) y no se recalcula el plan del job.
  - Resto (append, tablas Hive, otros formatos): se muestrea el propio DataFrame con limit(N); si el job lo
    dejo materializado (cache/localCheckpoint) es casi gratis, si no Spark evalua solo las particiones que
    necesita para N filas.
  - Entradas: una agregacion mas por cada lectura que comparta columnas con la salida, tambien con limit(N).
  - Maximo de columnas perfiladas por pasada: MAX_COLS. Apagalo con BNX_DIAG_ESCRITURA=0 si una corrida
    concreta no puede pagar ni eso.
La muestra es limit(N) (primeras particiones): es una estimacion, no un conteo exacto. Las filas de ejemplo
muestran datos reales en el log del cluster: BNX_DIAG_MUESTRA=0 las oculta.
Solo stdlib + pyspark (importado al usarse). Compatible con Python 3.8.
"""
import io
import os
import sys

MAX_COLS = 1500          # columnas perfiladas por pasada (anchas: se avisa del recorte)
MAX_ENTRADAS = 10        # ultimas lecturas que se guardan para comparar
UMBRAL_SUBIDA = 5.0      # puntos porcentuales de nulos de mas que la entrada para avisar
MAX_LISTA = 15           # nombres de columnas que se listan por alerta
PREFIJO = "[diag-escritura]"
_APAGADO = ("0", "off", "no", "false", "n")

_E = {"instalado": False, "orig": {}, "entradas": [], "job": None, "nivel": 0, "parches": []}


# ------------------------------------------------------------------ configuracion
def activo():
    return os.environ.get("BNX_DIAG_ESCRITURA", "1").strip().lower() not in _APAGADO


def _entero(nombre, defecto):
    try:
        v = int(os.environ.get(nombre, defecto))
        return v if v >= 0 else defecto
    except (TypeError, ValueError):
        return defecto


def filas_muestra():
    return max(1, _entero("BNX_DIAG_FILAS", 20000))


def filas_ejemplo():
    return _entero("BNX_DIAG_MUESTRA", 3)


# ------------------------------------------------------------------ perfil (una sola pasada)
def perfil(df, cols=None, n=None):
    """(filas, {col: % nulos}, {col: % NaN}) sobre una muestra df.limit(n), con UNA agregacion.
    Mismo calculo que null_report() de framework_mlops_v2.core.quality, pero acotado: aqui no hay count() de
    toda la tabla (en el YARN del banco seria otra lectura completa). Las columnas float/double cuentan los NaN
    aparte: Spark no los trata como null, pero Hive/Impala/pandas los muestran como vacios."""
    from pyspark.sql import functions as F
    n = n or filas_muestra()
    tipos = dict((f.name, f.dataType.simpleString()) for f in df.schema.fields)
    cols = [c for c in (cols if cols is not None else df.columns) if c in tipos][:MAX_COLS]
    if not cols:
        return 0, {}, {}
    exprs = [F.count(F.lit(1)).alias("__n")]
    for i, c in enumerate(cols):
        ref = F.col("`%s`" % c.replace("`", "``"))
        exprs.append(F.sum(ref.isNull().cast("int")).alias("n%d" % i))
        if tipos[c] in ("double", "float"):
            exprs.append(F.sum(F.isnan(ref).cast("int")).alias("x%d" % i))
    fila = df.limit(n).agg(*exprs).collect()[0].asDict()
    total = fila.get("__n") or 0
    if total == 0:
        return 0, {}, {}
    nulos, nans = {}, {}
    for i, c in enumerate(cols):
        nulos[c] = round(100.0 * (fila.get("n%d" % i) or 0) / total, 2)
        if ("x%d" % i) in fila:
            nans[c] = round(100.0 * (fila.get("x%d" % i) or 0) / total, 2)
    return total, nulos, nans


# ------------------------------------------------------------------ evaluacion (pura, sin Spark)
def evaluar(filas, nulos, nans, entradas):
    """entradas: lista de (origen, {col: % nulos}) de las lecturas del job.
    Devuelve {'todo_nulo': [...], 'todo_nan': [...], 'subieron': [(col, pct_ent, pct_sal, origen)]}."""
    if not filas:
        return {"todo_nulo": [], "todo_nan": [], "subieron": []}
    todo_nulo = [c for c, p in nulos.items() if p >= 100.0]
    todo_nan = [c for c, p in nans.items() if p >= 100.0 and c not in todo_nulo]
    subieron = []
    for c, p in nulos.items():
        if c in todo_nulo:
            continue
        for origen, perf in entradas:
            if c in perf:
                if p - perf[c] >= UMBRAL_SUBIDA:
                    subieron.append((c, perf[c], p, origen))
                break
    subieron.sort(key=lambda t: t[2] - t[1], reverse=True)
    return {"todo_nulo": todo_nulo, "todo_nan": todo_nan, "subieron": subieron}


def _lista(cols):
    s = ", ".join(cols[:MAX_LISTA])
    return s + (", ... (+%d mas)" % (len(cols) - MAX_LISTA) if len(cols) > MAX_LISTA else "")


def formatear(destino, fmt, modo, filas, ncols, hall, estado, ejemplo=None, nota=None, ent_cmp=0):
    """Lineas de texto (espanol) del diagnostico de una escritura."""
    L = []
    P = PREFIJO + " "
    L.append("%sjob=%s destino=%s formato=%s modo=%s" % (P, estado.get("job"), destino, fmt or "?", modo or "?"))
    if nota:
        L.append(P + nota)
    if not filas:
        L.append(P + "AVISO: la muestra de la escritura esta vacia (0 filas); no hay nada que perfilar")
    else:
        L.append("%smuestra: %d filas (limite %d), %d columnas; entradas comparadas: %d"
                 % (P, filas, filas_muestra(), ncols, ent_cmp))
    if hall["todo_nulo"]:
        L.append("%sALERTA: %d de %d columnas estan 100%% NULL: %s"
                 % (P, len(hall["todo_nulo"]), ncols, _lista(hall["todo_nulo"])))
    if hall["todo_nan"]:
        L.append("%sALERTA: %d columnas estan 100%% NaN (Spark no las cuenta como null, pero Hive/Impala las muestran "
                 "vacias): %s" % (P, len(hall["todo_nan"]), _lista(hall["todo_nan"])))
    if hall["subieron"]:
        L.append("%sALERTA: %d columnas con MAS nulos que en la entrada:" % (P, len(hall["subieron"])))
        for c, pe, ps, origen in hall["subieron"][:MAX_LISTA]:
            L.append("%s  - %s: %.1f%% -> %.1f%% (entrada: %s)" % (P, c, pe, ps, origen))
    if filas and not (hall["todo_nulo"] or hall["todo_nan"] or hall["subieron"]):
        L.append(P + "OK: ninguna columna 100% nula ni con mas nulos que la entrada (segun la muestra)")
    if hall["todo_nulo"] or hall["subieron"]:
        L.append(P + "PISTA: un left join cuyas llaves no empatan (tipo o valor distinto) deja nulas todas las "
                     "columnas del lado derecho; compara las llaves de las entradas contra las del lado izquierdo.")
    if ejemplo:
        L.append(P + "filas de ejemplo:")
        for r in ejemplo:
            L.append(P + "  " + r)
    udf_n = estado.get("udf_nativas") or []
    if estado.get("udf_nativas_activas"):
        L.append("%smodo UDF: NATIVO (reemplazo por expresiones Spark) activo; reemplazadas: %s; se quedan en Python: %s"
                 % (P, ", ".join(udf_n) or "(ninguna)", ", ".join(estado.get("udf_en_python") or []) or "(ninguna)"))
    else:
        L.append(P + "modo UDF: ORIGINAL (las UDF del banco corren tal cual, en Python en los workers)")
    L.append("%sparches de compatibilidad (bank_compat): %s (modo %s, BNX_BANK_COMPAT=%s); parches aplicados en este "
             "job: %s; BNX_EXECUTOR_PYTHON=%s"
             % (P, "ACTIVOS" if estado.get("compat_activo") else "inactivos", estado.get("modo"),
                estado.get("bank_compat_env"), "; ".join(estado.get("parches") or []) or "(ninguno)",
                estado.get("python_executor")))
    return L


# ------------------------------------------------------------------ salida (pantalla + logs)
def _archivos_log():
    out = []
    for v in (os.environ.get("BNX_DIAG_LOG"), os.environ.get("LOG_FILE_PATH")):
        if v and v not in out:
            out.append(v)
    return out


def emitir(lineas):
    txt = "\n".join(lineas) + "\n"
    try:
        sys.stdout.write(txt)
        sys.stdout.flush()
    except Exception:
        pass
    for ruta in _archivos_log():
        try:
            d = os.path.dirname(os.path.abspath(ruta))
            if not os.path.isdir(d):
                os.makedirs(d)
            with io.open(ruta, "a", encoding="utf-8") as fh:
                fh.write(txt)
        except Exception:
            pass


# ------------------------------------------------------------------ analisis de una escritura
def _estado_compat():
    try:
        import bank_compat as bc
    except Exception:
        try:
            from src import bank_compat as bc
        except Exception:
            bc = None
    if bc is not None:
        try:
            return bc.estado_diagnostico()
        except Exception:
            pass
    return {"job": os.environ.get("BNX_JOB_ID") or "(job)", "modo": "?", "compat_activo": False,
            "bank_compat_env": os.environ.get("BNX_BANK_COMPAT", "") or "(sin definir)",
            "udf_nativas_activas": False, "udf_nativas": [], "udf_en_python": [], "parches": [],
            "python_executor": os.environ.get("BNX_EXECUTOR_PYTHON", "") or "(automatico)"}


def _ejemplo(df, cols, k):
    if k <= 0:
        return None
    cols = cols[:12]
    out = []
    for r in df.select(*[c for c in cols]).limit(k).collect():
        partes = []
        for c in cols:
            v = r[c]
            s = "%r" % (v,) if not isinstance(v, str) else v
            partes.append("%s=%s" % (c, s if len(s) <= 30 else s[:27] + "..."))
        out.append(", ".join(partes) + (" ..." if len(df.columns) > len(cols) else ""))
    return out


def _spark_de(df):
    sp = getattr(df, "sparkSession", None)
    if sp is None:
        sp = getattr(getattr(df, "sql_ctx", None), "sparkSession", None)
    return sp


def _reiniciar_si_otro_job():
    job = os.environ.get("BNX_JOB_ID") or ""
    if job != _E["job"]:
        _E["job"] = job
        _E["entradas"] = []


def _perfiles_de_entradas(cols):
    """[(origen, {col: % nulos})] solo con las columnas de la salida que cada entrada tiene (primera que la tenga)."""
    pend = list(cols)
    res = []
    for origen, df in reversed(_E["entradas"]):
        if not pend:
            break
        comunes = [c for c in pend if c in df.columns]
        if not comunes:
            continue
        try:
            _f, nul, _nan = perfil(df, comunes)
        except Exception:
            continue
        res.append((origen, nul))
        pend = [c for c in pend if c not in nul]
    return res


def analizar_escritura(df, destino, fmt=None, modo=None, releer=None):
    """Perfila lo escrito (muestra), lo compara con las entradas del job y lo emite. Nunca lanza.
    releer: DataFrame ya leido de lo escrito (se usa en vez de recalcular `df`)."""
    if not activo():
        return None
    try:
        _reiniciar_si_otro_job()
        base = releer if releer is not None else df
        nota = None if releer is not None else "(muestra tomada del DataFrame escrito: no se pudo releer el destino; no detecta NULL introducidos por la propia escritura)"
        cacheado = None
        if releer is None:
            # ultimo recurso: materializar la muestra una sola vez (perfil y ejemplo no recalculan el plan del job)
            try:
                cacheado = base = base.limit(filas_muestra()).cache()
            except Exception:
                cacheado = None
        try:
            return _analizar(base, destino, fmt, modo, nota)
        finally:
            if cacheado is not None:
                try:
                    cacheado.unpersist()
                except Exception:
                    pass
    except Exception as e:
        emitir(["%saviso: no se pudo generar el diagnostico de %s (%s: %s); el job no se afecta"
                % (PREFIJO, destino, type(e).__name__, str(e)[:200])])
        return None
def _analizar(base, destino, fmt, modo, nota):
    filas, nulos, nans = perfil(base)
    ent = _perfiles_de_entradas(list(nulos.keys()))
    hall = evaluar(filas, nulos, nans, ent)
    try:
        ejemplo = _ejemplo(base, list(base.columns), filas_ejemplo()) if filas else None
    except Exception:
        ejemplo = None
    lineas = formatear(destino, fmt, modo, filas, len(base.columns), hall, _estado_compat(), ejemplo, nota, len(ent))
    emitir(lineas)
    return {"filas": filas, "nulos": nulos, "nans": nans, "hallazgos": hall, "lineas": lineas}


# ------------------------------------------------------------------ enganches de Spark
def _origen(args, kw):
    for v in list(args) + [kw.get("path"), kw.get("paths"), kw.get("tableName")]:
        if isinstance(v, str):
            return v
        if isinstance(v, (list, tuple)) and v and isinstance(v[0], str):
            return ",".join(v[:2])
    return "(sin ruta)"


def _mk_lector(nombre, orig):
    def f(self, *a, **k):
        r = orig(self, *a, **k)
        try:
            if activo() and hasattr(r, "columns") and hasattr(r, "schema"):
                _reiniciar_si_otro_job()
                _E["entradas"].append((_origen(a, k), r))
                del _E["entradas"][:-MAX_ENTRADAS]
        except Exception:
            pass
        return r
    f.__name__ = nombre
    return f


def _releer(df, fmt, modo, destino, es_ruta, tipo="ruta"):
    """DataFrame con lo ESCRITO (relectura del destino, no el DataFrame en memoria): asi se ve el NULL que mete la
    escritura misma (cast de insertInto/saveAsTable, esquema de la tabla) y no se recalcula el plan del job.
    Tablas: spark.table(destino). Rutas parquet/orc en cualquier modo salvo ignore (con append la muestra
    limit(N) puede venir de lo previo: es una estimacion). None si no corresponde (csv/json/text, ignore)."""
    sp = _spark_de(df)
    if sp is None:
        return None
    if tipo == "tabla":
        return _E["orig"]["r_table"](sp, destino)
    if not es_ruta or (fmt or "parquet").lower() not in ("parquet", "orc"):
        return None
    if (modo or "errorifexists").lower() == "ignore":
        return None
    return _E["orig"]["r_load"](sp.read, destino, format=(fmt or "parquet").lower())
def _mk_escritor(nombre, orig, tipo, fmt_fijo=None):
    """tipo: 'ruta' (parquet/orc/csv/json/text: path es el 1er argumento), 'save' o 'tabla'."""
    def f(self, *a, **k):
        _E["nivel"] += 1
        try:
            r = orig(self, *a, **k)
        except BaseException:
            _E["nivel"] -= 1
            raise
        _E["nivel"] -= 1
        if _E["nivel"] > 0 or not activo():
            return r
        try:
            destino = a[0] if a and isinstance(a[0], str) else (k.get("path") or k.get("name") or k.get("tableName"))
            modo = getattr(self, "_bnx_modo", None)
            fmt = fmt_fijo or getattr(self, "_bnx_fmt", None)
            es_ruta = tipo in ("ruta", "save")
            if tipo == "save":
                fmt = (a[1] if len(a) > 1 and isinstance(a[1], str) else k.get("format")) or fmt
                modo = (a[2] if len(a) > 2 and isinstance(a[2], str) else k.get("mode")) or modo
                es_ruta = isinstance(destino, str)
            elif tipo == "ruta":
                modo = (k.get("mode") or (a[1] if len(a) > 1 and isinstance(a[1], str) else None)) or modo
            elif nombre == "insertInto":
                ow = a[1] if len(a) > 1 else k.get("overwrite")
                modo = "overwrite" if ow else "append"
            else:
                modo = (a[2] if len(a) > 2 and isinstance(a[2], str) else k.get("mode")) or modo
                fmt = (a[1] if len(a) > 1 and isinstance(a[1], str) else k.get("format")) or fmt
            if destino is None:
                destino = "(sin ruta)"
            df = getattr(self, "_df", None)
            if df is None:
                return r
            _E["nivel"] += 1          # lo que lea el diagnostico no se diagnostica a si mismo
            try:
                rel = None
                try:
                    rel = _releer(df, fmt, modo, destino, es_ruta, tipo)
                except Exception:
                    rel = None
                analizar_escritura(df, destino, fmt or ("tabla" if tipo == "tabla" else None), modo, rel)
            finally:
                _E["nivel"] -= 1
        except Exception:
            pass
        return r
    f.__name__ = nombre
    return f


def _mk_marca(nombre, orig, atributo):
    def f(self, valor, *a, **k):
        try:
            if isinstance(valor, str):
                setattr(self, atributo, valor)
        except Exception:
            pass
        return orig(self, valor, *a, **k)
    f.__name__ = nombre
    return f


def instalar():
    """Engancha lecturas y escrituras de PySpark. Idempotente; False si esta apagado o no hay pyspark."""
    if _E["instalado"]:
        return True
    if not activo():
        return False
    try:
        from pyspark.sql import DataFrameReader, DataFrameWriter, SparkSession
    except Exception:
        return False
    O = _E["orig"]
    parches = []

    def p(cls, attr, nuevo_fn):
        orig = cls.__dict__.get(attr)
        if orig is None:
            return None
        parches.append((cls, attr, orig))
        setattr(cls, attr, nuevo_fn(orig))
        return orig

    for fn in ("parquet", "orc", "csv", "json", "table"):
        p(DataFrameReader, fn, lambda o, fn=fn: _mk_lector(fn, o))
    p(DataFrameReader, "load", lambda o: _mk_lector("load", o))
    p(SparkSession, "table", lambda o: _mk_lector("table", o))
    for fn, fmt in (("parquet", "parquet"), ("orc", "orc"), ("csv", "csv"), ("json", "json"), ("text", "text")):
        p(DataFrameWriter, fn, lambda o, fn=fn, fmt=fmt: _mk_escritor(fn, o, "ruta", fmt))
    p(DataFrameWriter, "save", lambda o: _mk_escritor("save", o, "save"))
    p(DataFrameWriter, "saveAsTable", lambda o: _mk_escritor("saveAsTable", o, "tabla"))
    p(DataFrameWriter, "insertInto", lambda o: _mk_escritor("insertInto", o, "tabla"))
    p(DataFrameWriter, "mode", lambda o: _mk_marca("mode", o, "_bnx_modo"))
    p(DataFrameWriter, "format", lambda o: _mk_marca("format", o, "_bnx_fmt"))
    # r_load: el load ORIGINAL (sin enganche) para releer lo escrito sin registrarlo como entrada
    for cls, attr, orig in parches:
        if cls is DataFrameReader and attr == "load":
            O["r_load"] = orig
        if cls is SparkSession and attr == "table":
            O["r_table"] = orig
    _E["parches"] = parches
    _E["instalado"] = True
    return True


def desinstalar():
    for cls, attr, orig in reversed(_E.get("parches") or []):
        setattr(cls, attr, orig)
    _E.update({"instalado": False, "orig": {}, "entradas": [], "job": None, "nivel": 0, "parches": []})
