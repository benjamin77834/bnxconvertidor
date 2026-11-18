"""Datos de entrada PROPIOS para los jobs de un plan (en lugar de los sinteticos).

Una entrada externa del plan es un dataset <base>/raw/<nombre>. Aqui se le puede dar contenido
desde: un archivo subido (CSV/TSV/JSON/JSONL/Parquet/xlsx), una ruta local (archivo o carpeta
parquet) o un CSV pegado como texto. Todo termina como parquet en <base>/raw/<nombre> y queda
marcado "propio" en <base>/raw/_origen.json: generar_datos no lo sobrescribe sin confirmacion.

Seguridad: el destino solo puede ser una entrada externa que el plan realmente lee (nombre
validado, realpath dentro de <base>/raw). Se escribe en una carpeta temporal y se renombra.
No usa PySpark. Compatible con Python 3.8.
"""
import csv
import difflib
import io
import json
import os
import re
import secrets
import shutil

from . import orquestador as _orq
from . import parquet_visor as _pv

MAX_MB = float(os.environ.get("BNX_DATOS_MAX_MB") or 512)
MAX_FILAS = int(os.environ.get("BNX_DATOS_MAX_FILAS") or 2000000)
MAX_TEXTO = 5 * 1024 * 1024
VISTA = 20
EXT_TABULAR = {".csv": "csv", ".tsv": "csv", ".txt": "csv", ".dat": "csv", ".json": "json",
               ".jsonl": "json", ".ndjson": "json", ".parquet": "parquet", ".xlsx": "excel"}
_TOKEN = re.compile(r"^[0-9a-f]{12}$")
_SEG = re.compile(r"^[\w.\-]+$")
_ENT = re.compile(r"^[+-]?(0|[1-9]\d*)$")
_DEC = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")
_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?)?$")


class DatosError(ValueError):
    def __init__(self, msg, extra=None):
        super().__init__(msg)
        self.extra = extra or {}


# ---------------------------------------------------------------------------
# Rutas y nombres
# ---------------------------------------------------------------------------
def _base(base_path, crear=True):
    if not base_path or "://" in str(base_path):
        raise DatosError("los datos propios requieren un base_path local (no s3://)")
    b, err = _orq.validar_base_path(str(base_path), crear=crear)
    if err:
        raise DatosError(f"base_path: {err}")
    return os.path.realpath(b)


def nombre_valido(nombre):
    """Nombre relativo a raw/: segmentos [\\w.-], sin '..', sin absolutos ni '\\'."""
    return (isinstance(nombre, str) and 0 < len(nombre) <= 300 and not nombre.startswith("/")
            and all(_SEG.match(x) and x not in (".", "..") for x in nombre.split("/")))


def _destino(base, nombre):
    if not nombre_valido(nombre):
        raise DatosError(f"nombre de dataset invalido: {nombre!r}")
    raw = os.path.realpath(os.path.join(base, "raw"))
    dest = os.path.realpath(os.path.join(raw, *nombre.split("/")))
    if not dest.startswith(raw + os.sep):
        raise DatosError("la ruta sale de <base>/raw")
    return raw, dest


def _externa(o, ruta_o_nombre):
    """Entrada externa del plan con ese nombre (o raw/<nombre>); DatosError si el plan no la lee."""
    nombre = ruta_o_nombre[4:] if str(ruta_o_nombre).startswith("raw/") else ruta_o_nombre
    for e in _orq.esquemas_entradas(o):
        if e["nombre"] == nombre:
            return e
    raise DatosError(f"{ruta_o_nombre!r} no es una entrada externa de este plan")


# ---------------------------------------------------------------------------
# Estado de las entradas
# ---------------------------------------------------------------------------
def estado_entradas(o, base_path):
    """[{nombre, ruta, paso, columnas, nota, estado: falta|sintetico|propio|existente, detalle}]."""
    base = _base(base_path, crear=False)
    man = _orq.leer_origen(base)
    res = []
    for e in _orq.esquemas_entradas(o):
        _raw, dest = _destino(base, e["nombre"])
        if not os.path.exists(dest):
            est, det = "falta", {}
        else:
            det = man.get(e["nombre"], {})
            est = det.get("origen") if det.get("origen") in ("propio", "sintetico") else "existente"
        res.append({**e, "estado": est, "detalle": det})
    return res


# ---------------------------------------------------------------------------
# Lectura de la fuente
# ---------------------------------------------------------------------------
def _cat(tipo):
    t = str(tipo or "").lower()
    if re.search(r"int|long|short|decimal|numeric|number|double|float|real|bigint", t):
        return "numero"
    if re.search(r"date|time", t):
        return "fecha"
    return "texto"


def _decodificar(b):
    try:
        return b.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        return b.decode("latin-1"), "latin-1"


def _delimitador(texto, forzado=None):
    if forzado:
        return {"tab": "\t", "\\t": "\t"}.get(forzado, forzado)
    muestra = "\n".join(texto.splitlines()[:50])
    try:
        return csv.Sniffer().sniff(muestra, delimiters=",;\t|").delimiter
    except csv.Error:
        cuentas = {d: muestra.count(d) for d in ",;\t|"}
        return max(cuentas, key=cuentas.get) if max(cuentas.values()) else ","


def _tiene_cabecera(filas, esperadas, forzar):
    if forzar is not None:
        return bool(forzar)
    primera = [str(c).strip().lower() for c in filas[0]]
    esp = {e["name"].lower() for e in esperadas}
    if esp and sum(1 for c in primera if c in esp) * 2 >= max(len(esp), 1) and any(c in esp for c in primera):
        return True
    if any(_ENT.match(c) or _DEC.match(c) for c in primera if c):
        return False        # una fila con numeros no es cabecera
    return len(filas) < 2 or len(set(primera)) == len(primera) and all(primera)


def _valores_csv(texto, esperadas, delim, cabecera):
    filas = [r for r in csv.reader(io.StringIO(texto, newline=""), delimiter=delim) if any(c.strip() for c in r)]
    if not filas:
        raise DatosError("el archivo no tiene filas")
    avisos = []
    hdr = _tiene_cabecera(filas, esperadas, cabecera)
    if hdr:
        cols, datos = [c.strip() or f"col{i + 1}" for i, c in enumerate(filas[0])], filas[1:]
    else:
        n = max(len(r) for r in filas)
        if esperadas and len(esperadas) == n:
            cols = [e["name"] for e in esperadas]
            avisos.append("sin cabecera: se asignaron los nombres esperados por posicion")
        else:
            cols = [f"col{i + 1}" for i in range(n)]
            avisos.append("sin cabecera: columnas col1..colN (use el mapeo para nombrarlas)")
        datos = filas
    vistos = {}
    for i, c in enumerate(cols):          # nombres repetidos
        if c in vistos:
            vistos[c] += 1
            cols[i] = f"{c}_{vistos[c]}"
            avisos.append(f"columna repetida {c!r}: renombrada {cols[i]!r}")
        else:
            vistos[c] = 1
    n = len(cols)
    out = [([None if (v is None or v == "") else v for v in (r + [None] * n)[:n]]) for r in datos]
    if any(len(r) > n for r in datos):
        avisos.append("hay filas con mas columnas que la cabecera: se descartaron las sobrantes")
    return cols, out, avisos, hdr


def _valor_json(v):
    return json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v


def _tabla_json(texto):
    try:
        d = json.loads(texto)
        if isinstance(d, dict):
            d = next((v for v in d.values() if isinstance(v, list)), [d])
    except ValueError:
        try:
            d = [json.loads(ln) for ln in texto.splitlines() if ln.strip()]
        except ValueError:
            raise DatosError("JSON invalido (se espera una lista de objetos o JSON lines)")
    if not isinstance(d, list) or not d or not all(isinstance(x, dict) for x in d):
        raise DatosError("el JSON debe ser una lista de objetos")
    cols = []
    for r in d:
        for k in r:
            if k not in cols:
                cols.append(k)
    return cols, [[_valor_json(r.get(c)) for c in cols] for r in d]


def _tabla_excel(path, cabecera):
    try:
        import openpyxl
    except ImportError:
        raise DatosError("para leer Excel (.xlsx) instale openpyxl (pip install openpyxl) "
                         "o guarde la hoja como CSV")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        filas = [list(r) for r in wb.worksheets[0].iter_rows(values_only=True)]
    finally:
        wb.close()
    filas = [r for r in filas if any(c not in (None, "") for c in r)]
    if not filas:
        raise DatosError("la hoja esta vacia")
    n = max(len(r) for r in filas)
    hdr = True if cabecera is None else bool(cabecera)
    cols = [str(c) if c not in (None, "") else f"col{i + 1}" for i, c in enumerate(filas[0] + [None] * (n - len(filas[0])))] \
        if hdr else [f"col{i + 1}" for i in range(n)]
    datos = filas[1:] if hdr else filas
    return cols, [[(None if v == "" else v) for v in (list(r) + [None] * n)[:n]] for r in datos]


def _resolver_fuente(base, fuente):
    """fuente: {tipo: staging, token} | {tipo: ruta, ruta} | {tipo: texto, texto}.
    -> ('archivo'|'carpeta'|'texto', valor, nombre_origen)."""
    if not isinstance(fuente, dict):
        raise DatosError("fuente invalida")
    t = fuente.get("tipo")
    if t == "texto":
        txt = fuente.get("texto")
        if not isinstance(txt, str) or not txt.strip():
            raise DatosError("el texto pegado esta vacio")
        if len(txt.encode("utf-8")) > MAX_TEXTO:
            raise DatosError("el texto pegado es demasiado grande (max 5 MB): suba un archivo")
        return "texto", txt, "texto_pegado.csv"
    if t == "staging":
        tok = fuente.get("token")
        if not isinstance(tok, str) or not _TOKEN.match(tok):
            raise DatosError("token de subida invalido")
        d = os.path.join(base, "_staging", tok)
        fs = [f for f in os.listdir(d)] if os.path.isdir(d) else []
        if len(fs) != 1 or not _SEG.match(fs[0]):
            raise DatosError("la subida ya no existe: vuelva a subir el archivo")
        return "archivo", os.path.join(d, fs[0]), fs[0]
    if t == "ruta":
        r = fuente.get("ruta")
        if not isinstance(r, str) or not r.strip() or "\x00" in r or "://" in r:
            raise DatosError("indique una ruta local")
        p = os.path.realpath(os.path.expanduser(r.strip()))
        if os.path.isdir(p):
            return "carpeta", p, os.path.basename(p)
        if os.path.isfile(p):
            return "archivo", p, os.path.basename(p)
        raise DatosError(f"no existe: {p}")
    raise DatosError("fuente desconocida (staging | ruta | texto)")


def cargar(base, fuente, esperadas, delimitador=None, cabecera=None):
    """Lee la fuente. Devuelve {formato, columnas:[str], tipos_origen:{col: tipo}|None, filas:[[..]]|None,
    parquet:[archivos]|None, total, codificacion, delimitador, cabecera, avisos, origen}."""
    kind, valor, nombre = _resolver_fuente(base, fuente)
    es_texto = kind == "texto"
    res = {"formato": None, "filas": None, "parquet": None, "codificacion": None,
           "delimitador": None, "cabecera": None, "avisos": [], "origen": nombre, "tipos_origen": None}
    if kind == "carpeta":
        fmt, fs = _pv.archivos_dataset(valor)
        if fmt != "parquet":
            raise DatosError("la carpeta no tiene archivos .parquet (use un archivo CSV/JSON/xlsx)")
        kind, valor = "parquet", fs
    elif kind == "archivo":
        ext = EXT_TABULAR.get(os.path.splitext(valor)[1].lower())
        if not ext:
            raise DatosError(f"formato no soportado: {os.path.splitext(valor)[1] or nombre!r} "
                             "(CSV, TSV, JSON, JSONL, Parquet, xlsx)")
        if os.path.getsize(valor) > MAX_MB * 1048576 and ext != "parquet":
            raise DatosError(f"el archivo pesa mas de {MAX_MB:.0f} MB (BNX_DATOS_MAX_MB)")
        if ext == "parquet":
            valor = [valor]
        kind = ext
    else:
        kind = "csv"
    res["formato"] = kind
    if kind == "parquet":
        info = _pv._leer_parquet(valor, 0, VISTA)
        res.update(columnas=[c["nombre"] for c in info["columnas"]],
                   tipos_origen={c["nombre"]: c["tipo"] for c in info["columnas"]},
                   parquet=valor, total=info["total_filas"], vista=info["filas"])
        return res
    if kind == "excel":
        cols, filas = _tabla_excel(valor, cabecera)
    elif kind == "json":
        with open(valor, "rb") as f:
            texto, enc = _decodificar(f.read())
        res["codificacion"] = enc
        cols, filas = _tabla_json(texto)
    else:
        if es_texto:
            texto, enc = valor, "utf-8"
        else:
            with open(valor, "rb") as f:
                texto, enc = _decodificar(f.read())
        res["codificacion"] = enc
        delim = _delimitador(texto, delimitador)
        cols, filas, av, hdr = _valores_csv(texto, esperadas, delim, cabecera)
        res.update(delimitador=delim, cabecera=hdr)
        res["avisos"] += av
    if len(filas) > MAX_FILAS:
        raise DatosError(f"mas de {MAX_FILAS} filas (BNX_DATOS_MAX_FILAS): use Parquet o reduzca el archivo")
    res.update(columnas=cols, filas=filas, total=len(filas), vista=filas[:VISTA])
    return res


# ---------------------------------------------------------------------------
# Tipos, validacion y mapeo
# ---------------------------------------------------------------------------
def _inferir(vals):
    """Tipo de una columna de textos: integer | double | date | string."""
    nn = [v for v in vals if v is not None]
    if not nn:
        return "string"
    if all(not isinstance(v, str) for v in nn):
        return ("integer" if all(isinstance(v, int) and not isinstance(v, bool) for v in nn)
                else "double" if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in nn)
                else "string")
    s = [v for v in nn if isinstance(v, str)]
    if len(s) == len(nn):
        if all(_ENT.match(v.strip()) for v in s):
            return "integer"
        if all(_DEC.match(v.strip()) for v in s):
            return "double"
        if all(_FECHA.match(v.strip()) for v in s):
            return "date"
    return "string"


def _tipos_origen(carga):
    if carga["tipos_origen"] is not None:
        return dict(carga["tipos_origen"])
    cols, filas = carga["columnas"], carga["filas"]
    return {c: _inferir([r[i] for r in filas]) for i, c in enumerate(cols)}


def _norm(n):
    return re.sub(r"[^a-z0-9]", "", str(n).lower())


def mapeo_final(columnas, esperadas, mapeo=None):
    """{col_origen: nombre_esperado}. Primero el mapeo del usuario; luego, por nombre sin
    distinguir mayusculas/separadores. Valida que no haya destinos repetidos."""
    esp = [e["name"] for e in esperadas]
    res, usados = {}, set()
    for src, dst in (mapeo or {}).items():
        if dst in (None, ""):
            continue
        if src not in columnas:
            raise DatosError(f"mapeo: la columna {src!r} no existe en el archivo")
        if dst not in esp:
            raise DatosError(f"mapeo: {dst!r} no es una columna esperada")
        if dst in usados:
            raise DatosError(f"mapeo: {dst!r} se asigno a dos columnas")
        res[src] = dst
        usados.add(dst)
    por_norm = {_norm(e): e for e in esp if e not in usados}
    for c in columnas:
        if c in res:
            continue
        if c in esp and c not in usados:
            res[c] = c
            usados.add(c)
        elif _norm(c) in por_norm and por_norm[_norm(c)] not in usados:
            res[c] = por_norm[_norm(c)]
            usados.add(res[c])
    return res


def validar(carga, esperadas, mapeo=None):
    """Compara columnas/tipos del archivo con los esperados (lo que el job lee)."""
    cols = carga["columnas"]
    mf = mapeo_final(cols, esperadas, mapeo)
    esp = {e["name"]: e["type"] for e in esperadas}
    tipos = _tipos_origen(carga)
    faltantes = [n for n in esp if n not in mf.values()]
    sobrantes = [c for c in cols if c not in mf]
    sugerencias = {}
    for c in sobrantes:
        cand = difflib.get_close_matches(c.lower(), [f.lower() for f in faltantes], n=1, cutoff=0.6)
        if cand:
            sugerencias[c] = next(f for f in faltantes if f.lower() == cand[0])
    avisos = []
    for src, dst in mf.items():
        if src != dst:
            avisos.append(f"{src!r} se usara como {dst!r}")
        ce, co = _cat(esp[dst]), _cat(tipos.get(src))
        if ce == "numero" and co != "numero":
            avisos.append(f"{dst}: se espera numerico ({esp[dst]}) pero el archivo trae {tipos.get(src)}")
        elif ce == "fecha" and co not in ("fecha",) and tipos.get(src) not in ("string", "date"):
            avisos.append(f"{dst}: se espera fecha ({esp[dst]}) pero el archivo trae {tipos.get(src)}")
    return {"ok": not faltantes, "faltantes": faltantes, "sobrantes": sobrantes,
            "coinciden": sorted(mf.values()), "mapeo": mf, "sugerencias": sugerencias,
            "avisos": avisos, "tipos_origen": tipos}


def _convertir_col(vals, esperado):
    """(valores, tipo) segun el tipo esperado; texto si no se puede convertir todo."""
    if esperado and _cat(esperado) != "numero":
        return [None if v is None else (v if isinstance(v, str) else str(v)) for v in vals], "string"
    t = _inferir(vals)
    if t == "integer" and not (esperado and re.search(r"decimal|double|float|real|numeric", str(esperado).lower())):
        return [None if v is None else int(str(v).strip()) for v in vals], "integer"
    if t in ("integer", "double"):
        return [None if v is None else float(str(v).strip()) for v in vals], "double"
    return [None if v is None else (v if isinstance(v, str) else str(v)) for v in vals], "string"


# ---------------------------------------------------------------------------
# Analisis y subida
# ---------------------------------------------------------------------------
def analizar(o, base_path, ruta, fuente, mapeo=None, delimitador=None, cabecera=None):
    """Valida la fuente contra lo que espera el job. Solo lee (no crea carpetas)."""
    base = _base(base_path, crear=False)
    ent = _externa(o, ruta)
    carga = cargar(base, fuente, ent["columnas"], delimitador, cabecera)
    val = validar(carga, ent["columnas"], mapeo)
    tipos = val.pop("tipos_origen")
    return {"ok": True, "nombre": ent["nombre"], "formato": carga["formato"], "origen": carga["origen"],
            "codificacion": carga["codificacion"], "delimitador": carga["delimitador"],
            "cabecera": carga["cabecera"], "total_filas": carga["total"],
            "columnas": [{"nombre": c, "tipo": tipos.get(c)} for c in carga["columnas"]],
            "vista": [[_pv._json_val(v) for v in r] for r in carga["vista"]],
            "esperadas": ent["columnas"], "avisos_lectura": carga["avisos"], "validacion": val}


def nueva_subida(base_path):
    """Carpeta de staging <base>/_staging/<token>. Devuelve (token, carpeta)."""
    base = _base(base_path)
    tok = secrets.token_hex(6)
    d = os.path.join(base, "_staging", tok)
    os.makedirs(d)
    return tok, d


def limpiar_subida(base_path, token):
    if isinstance(token, str) and _TOKEN.match(token):
        shutil.rmtree(os.path.join(_base(base_path), "_staging", token), ignore_errors=True)


def nombre_archivo_valido(n):
    return (isinstance(n, str) and bool(_SEG.match(n)) and n not in (".", "..") and len(n) <= 200
            and os.path.splitext(n)[1].lower() in EXT_TABULAR)


# ---------------------------------------------------------------------------
# Importacion
# ---------------------------------------------------------------------------
def importar(o, base_path, ruta, fuente, mapeo=None, aceptar_avisos=False, sobrescribir=False,
             delimitador=None, cabecera=None):
    """Convierte la fuente a parquet en <base>/raw/<nombre> y lo marca 'propio'.
    Faltan columnas esperadas y no aceptar_avisos -> DatosError (con el detalle en .extra)."""
    base = _base(base_path)
    ent = _externa(o, ruta)
    raw, dest = _destino(base, ent["nombre"])
    previo = _orq.leer_origen(base).get(ent["nombre"], {}).get("origen")
    if os.path.exists(dest) and previo != "sintetico" and not sobrescribir:
        raise DatosError("ya hay datos %s en %s: confirme para sobrescribirlos"
                         % ("propios" if previo == "propio" else "existentes", ent["nombre"]),
                         {"codigo": "existe", "origen": previo or "existente"})
    carga = cargar(base, fuente, ent["columnas"], delimitador, cabecera)
    val = validar(carga, ent["columnas"], mapeo)
    if val["faltantes"] and not aceptar_avisos:
        raise DatosError("faltan columnas que el job lee: " + ", ".join(val["faltantes"])
                         + " (mapee columnas o acepte seguir con el aviso)",
                         {"codigo": "validacion",
                          "validacion": {k: v for k, v in val.items() if k != "tipos_origen"}})
    mf = val["mapeo"]
    esp = {e["name"]: e["type"] for e in ent["columnas"]}
    os.makedirs(raw, exist_ok=True)
    tmp = dest + ".tmp-" + secrets.token_hex(3)
    try:
        if carga["parquet"] is not None:
            motor = _escribir_parquet_existente(carga, mf, tmp, val)
            filas = carga["total"]
        else:
            cols = carga["columnas"]
            salida_cols, datos = [], []
            for i, c in enumerate(cols):
                nombre = mf.get(c, c)
                v, _t = _convertir_col([r[i] for r in carga["filas"]], esp.get(nombre))
                salida_cols.append(nombre)
                datos.append(v)
            filas_t = [dict(zip(salida_cols, vals)) for vals in zip(*datos)] if datos else []
            motor = _orq.escribir_parquet(tmp, salida_cols, filas_t)
            filas = len(filas_t)
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        elif os.path.exists(dest):
            os.remove(dest)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        os.replace(tmp, dest)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    _orq.marcar_origen(base, ent["nombre"], "propio", filas=filas, fuente=carga["origen"],
                       formato=carga["formato"])
    if isinstance(fuente, dict) and fuente.get("tipo") == "staging":
        limpiar_subida(base, fuente.get("token"))
    return {"ok": True, "nombre": ent["nombre"], "ruta": "raw/" + ent["nombre"], "filas": filas,
            "motor": motor, "validacion": {k: v for k, v in val.items() if k != "tipos_origen"}}


def _escribir_parquet_existente(carga, mf, tmp, val):
    """Parquet de origen -> tmp. Sin renombres se copian los archivos tal cual."""
    renombra = {c: n for c, n in mf.items() if c != n}
    os.makedirs(tmp)
    if not renombra:
        for i, f in enumerate(carga["parquet"]):
            shutil.copyfile(f, os.path.join(tmp, "part-%05d.parquet" % i))
        return "copia"
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        for i, f in enumerate(carga["parquet"]):
            t = pq.read_table(f)
            t = t.rename_columns([renombra.get(c, c) for c in t.column_names])
            pq.write_table(t, os.path.join(tmp, "part-%05d.parquet" % i))
        return "pyarrow"
    except ImportError:
        pass
    info = _pv._leer_parquet(carga["parquet"], 0, MAX_FILAS)
    cols = [renombra.get(c["nombre"], c["nombre"]) for c in info["columnas"]]
    shutil.rmtree(tmp)
    return _orq.escribir_parquet(tmp, cols, [dict(zip(cols, r)) for r in info["filas"]])
