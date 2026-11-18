# -*- coding: utf-8 -*-
"""Datos sinteticos deterministas: columnas -> tipo por nombre/uso -> valores que pasan los filtros."""
import calendar
import datetime
import random
import re
import zlib

from . import analisis
from .estado import E

_KEY = re.compile(r"""^(num_?cliente|num_cliente|cliente(_id|_nbr)?|id_cliente|clnt_nbr|crd_acct_nbr|acct_nbr|
cust(omer)?_?(id|nbr|no)|id_cuenta\w*|num_contrato\w*|num_cuenta|num_de_cuenta|contrato|cuenta|
numero_cliente|id|\w+_id|\w+_key)$""", re.X | re.I)
_FECHA = re.compile(r"(^|_)(fe|fec|fecha|dt|date|mis|vintage|periodo|proc|inf)(_|$)|^fec|^fe_|(dt|date|fecha)$", re.I)
_CAT = re.compile(r"^(cve|ncve|cvetran|ind|flag|tipo|cod|status|estatus|segmento|moneda|plan_nbr)|"
                  r"(num_producto|num_instrumento|cve_\w+|sucursal|num_sucdepto)$", re.I)
_NUM = re.compile(r"(sdo|saldo|mon_|monto|imp_|importe|amt|bal|tot_|cnt|cant|prom|tasa|rate|mob|_due|due_|"
                  r"^a\d+$|pago|pay|ingreso|margen|ipab|comis|score|valor|limite|lim_|mop|ratio|avg|sum)", re.I)
_ENTERO = re.compile(r"(mob|due|cnt|cant|count|nbr_|num_)", re.I)
_DATE_STR = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


def _rng(col, i):
    return random.Random(zlib.crc32(("%s|%d|%d" % (col.lower(), i, E["seed"])).encode("utf-8")))


def tipo_por_nombre(col):
    c = col.lower()
    if _KEY.match(c):
        return "key"
    if _FECHA.search(c):
        return "date"
    if _CAT.search(c):
        return "cat"
    if _NUM.search(c):
        return "num"
    return "str"


def _fecha_de(v):
    m = _DATE_STR.match(str(v))
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _mas_meses(d, k):
    m = d.month - 1 + k
    y, mm = d.year + m // 12, m % 12 + 1
    return datetime.date(y, mm, min(d.day, calendar.monthrange(y, mm)[1]))


def ancla():
    c = str(E.get("cohort") or "")
    try:
        d = datetime.date(int(c[:4]), int(c[4:6]), 1)
    except (ValueError, IndexError):
        d = datetime.date.today().replace(day=1)
    return d - datetime.timedelta(days=1)


def especificar(col, hint, usos_sql=None):
    """{'t': tipo, 'h': filtros, 'pool': literales del codigo}."""
    hint = hint or {}
    u = analisis.usos_columna(col)
    flags = set(usos_sql or ())
    t = tipo_por_nombre(col)
    if hint.get("null"):
        return {"t": "null", "h": hint, "pool": []}
    ge, le = hint.get("ge", hint.get("gt")), hint.get("le", hint.get("lt"))
    if t not in ("key", "date") and (_fecha_de(ge) or _fecha_de(le) or any(_fecha_de(x) for x in hint.get("eq", []))):
        t = "date"
    if t in ("str", "num") and ("key" in flags or u["clave"]) and "date" not in flags:
        t = "key"
    if t == "str" and any(isinstance(hint.get(k), (int, float)) for k in ("ge", "gt", "le", "lt")):
        t = "num"
    if t == "str" and hint.get("eq") and all(isinstance(x, (int, float)) for x in hint["eq"]):
        t = "cat"
    if t == "str" and (u["fecha"] or "date" in flags):
        t = "date"
    elif t in ("str", "cat") and ("num" in flags or (u["num"] and not u["str"])):
        t = "num"
    return {"t": t, "h": hint, "pool": u["pool"]}


def _fecha_val(sp, i):
    h = sp["h"]
    lo = _fecha_de(h.get("ge")) or (_fecha_de(h.get("gt")) and
                                    _fecha_de(h.get("gt")) + datetime.timedelta(days=1))
    hi = _fecha_de(h.get("le")) or (_fecha_de(h.get("lt")) and
                                    _fecha_de(h.get("lt")) - datetime.timedelta(days=1))
    if lo and hi and hi >= lo:
        if (hi - lo).days > 40:
            lst, k = [], 0
            while _mas_meses(lo, k) <= hi:
                lst.append(_mas_meses(lo, k))
                k += 1
        else:
            lst = [lo + datetime.timedelta(days=7 * k) for k in range(((hi - lo).days // 7) + 1)]
        return lst[i % len(lst)].isoformat()
    if hi:
        return hi.isoformat()
    if lo:
        return lo.isoformat()
    return (ancla() - datetime.timedelta(days=i % 5)).isoformat()


def _num_val(col, sp, i):
    h = sp["h"]
    ge, gt, le, lt = h.get("ge"), h.get("gt"), h.get("le"), h.get("lt")
    if isinstance(ge, (int, float)) or isinstance(le, (int, float)) or isinstance(gt, (int, float)) \
            or isinstance(lt, (int, float)):
        lo = ge if isinstance(ge, (int, float)) else (gt + 1 if isinstance(gt, (int, float)) else None)
        hi = le if isinstance(le, (int, float)) else (lt - 1 if isinstance(lt, (int, float)) else None)
        if lo is not None and hi is not None and hi >= lo:
            return lo + (i % int(hi - lo + 1))
        return lo if lo is not None else hi
    r = _rng(col, i)
    if r.random() < 0.45:
        return r.randint(0, 4)
    v = round(r.uniform(5, 5000), 2)
    return int(v) if _ENTERO.search(col) else v


def valor(col, sp, i):
    t, h, pool = sp["t"], sp["h"], sp["pool"]
    if t == "null":
        return None
    if h.get("eq"):
        eq = []
        for x in h["eq"]:
            if x not in eq:
                eq.append(x)
        return eq[i % len(eq)]
    if t == "key":
        return i + 1
    if "like" in h and isinstance(h["like"], str):
        return "x%sx%d" % (h["like"].replace("%", ""), i % 3)
    if pool and t != "date":
        # mezcla: la mitad de las filas toma literales del codigo (== / isin), la otra el valor por defecto
        k = i % (2 * len(pool) + 1)
        if k < len(pool):
            return pool[k]
    if t == "date":
        return _fecha_val(sp, i)
    if t == "cat":
        return 1 + (i % 3)
    if t == "num":
        return _num_val(col, sp, i)
    return "S%d" % (i % 3)


def filas(columnas, specs, n):
    return [tuple(valor(c, specs[c], i) for c in columnas) for i in range(n)]


def _tipo_spark(vals):
    from pyspark.sql import types as T
    reales = [v for v in vals if v is not None]
    if reales and all(isinstance(v, int) and not isinstance(v, bool) for v in reales):
        return T.LongType()
    if reales and all(isinstance(v, (int, float)) for v in reales):
        return T.DoubleType()
    return T.StringType()


def datos_py(columnas, hints=None, usos_sql=None, n=None):
    """(columnas sin repetir, specs, filas) en Python puro."""
    n = n or E["filas"]
    hints = hints or {}
    cols, vistos = [], set()
    for c in columnas:
        if c and c.lower() not in vistos:
            vistos.add(c.lower())
            cols.append(c)
    if not cols:
        cols = ["id"]
    specs = dict((c, especificar(c, hints.get(c.lower()), (usos_sql or {}).get(c.lower()))) for c in cols)
    return cols, specs, filas(cols, specs, n)


def generar_df(spark, columnas, hints=None, usos_sql=None, n=None):
    """DataFrame sintetico con esas columnas (deterministas por nombre y fila)."""
    from pyspark.sql import types as T
    cols, specs, datos = datos_py(columnas, hints, usos_sql, n)
    campos, tipos = [], []
    for j, c in enumerate(cols):
        t = _tipo_spark([r[j] for r in datos])
        tipos.append(t)
        campos.append(T.StructField(c, t, True))
    dbl = [j for j, t in enumerate(tipos) if isinstance(t, T.DoubleType)]
    if dbl:
        datos = [tuple(float(v) if j in dbl and v is not None else v for j, v in enumerate(r)) for r in datos]
    return spark.createDataFrame(datos, T.StructType(campos)), specs
