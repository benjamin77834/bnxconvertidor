"""Visor de datasets (parquet / csv) de una ejecucion: lista <base>/raw y <base>/output y lee filas.

Solo LECTURA y solo rutas locales. Motor de lectura: pyarrow -> fastparquet -> lector puro
(src/parquet_lector.py). BNX_PARQUET_MOTOR=puro|fastparquet|pyarrow fuerza uno (p.ej. para probar
el entorno sin pyarrow). Nunca usa PySpark (sin Java colgaria el servidor).
"""
import csv
import datetime as _dt
import decimal
import os
import re

from . import orquestador as _orq
from . import parquet_lector as _pl

ZONAS = ("raw", "output")
LIMITE_DEFECTO, LIMITE_MAX = 100, 1000
MAX_BYTES = int(os.environ.get("BNX_VISOR_MAX_BYTES", _pl.MAX_BYTES_DEFECTO))
_CSV_MAX_CONTAR = 50 * 1024 * 1024  # mas grande: no se cuenta el total de filas


class VisorError(Exception):
    def __init__(self, msg, codigo="invalido"):
        super().__init__(msg)
        self.codigo = codigo


# ---------------------------------------------------------------------------
# Validacion de rutas
# ---------------------------------------------------------------------------
def validar_base(base_path):
    """Ruta local absoluta existente (s3:// no se puede leer aqui). Devuelve la ruta normalizada."""
    bp = str(base_path or "").strip()
    if "://" in bp:
        raise VisorError("el visor solo lee rutas locales; s3:// no esta soportado (descargue los "
                         "datos o use una ruta local)", "no_soportado")
    n, err = _orq.validar_base_path(bp, crear=False)
    if err and not err.startswith("sin permiso de escritura"):  # lectura: no hace falta escribir
        raise VisorError(f"base_path: {err}")
    if not os.path.isdir(n):
        raise VisorError(f"base_path no existe: {n}", "no_existe")
    return n


def _dir_zona(base, zona):
    if zona not in ZONAS:
        raise VisorError("zona invalida (raw | output)")
    d = os.path.realpath(os.path.join(base, zona))
    return d if os.path.isdir(d) else None


def resolver(base_path, zona, nombre):
    """Ruta real del dataset <base>/<zona>/<nombre>, garantizada dentro de esa zona."""
    base = validar_base(base_path)
    if zona not in ZONAS:
        raise VisorError("zona invalida (raw | output)")
    # nombre RELATIVO a la zona; '/' permitido para datasets anidados (raw/opt/.../X.txt),
    # nunca absoluto, '..', '\\' ni unidad de Windows.
    if (not isinstance(nombre, str) or not nombre or nombre.startswith("/")
            or any(seg in ("", ".", "..") for seg in nombre.split("/"))
            or any(c in nombre for c in "\\\x00\r\n") or re.match(r"^[A-Za-z]:", nombre)):
        raise VisorError("nombre de dataset invalido")
    zdir = _dir_zona(base, zona)
    if not zdir:
        raise VisorError(f"no existe {zona}/ en {base}", "no_existe")
    p = os.path.realpath(os.path.join(zdir, *nombre.split("/")))
    if not p.startswith(zdir + os.sep):
        raise VisorError("nombre de dataset invalido")
    if not os.path.exists(p):
        raise VisorError(f"no existe el dataset {zona}/{nombre}", "no_existe")
    return p


# ---------------------------------------------------------------------------
# Listado
# ---------------------------------------------------------------------------
def _oculto(n):
    return n.startswith(".") or n.startswith("_")


def archivos_dataset(p, prof=3):
    """(formato, [archivos ordenados]) de un dataset: .parquet (o .csv si no hay parquet)."""
    if os.path.isfile(p):
        e = os.path.splitext(p)[1].lower()
        return ("parquet" if e == ".parquet" else "csv" if e == ".csv" else None), [p]
    pq, cs = [], []
    base_n = p.rstrip(os.sep).count(os.sep)
    for raiz, dirs, files in os.walk(p):
        dirs[:] = sorted(d for d in dirs if not _oculto(d))
        if raiz.count(os.sep) - base_n >= prof:
            dirs[:] = []
        for n in sorted(files):
            if _oculto(n):
                continue
            e = os.path.splitext(n)[1].lower()
            (pq if e == ".parquet" else cs if e == ".csv" else []).append(os.path.join(raiz, n))
    if pq:
        return "parquet", pq
    if cs:
        return "csv", cs
    return None, []


_EXT_DATOS = (".parquet", ".csv")


def _candidatos(zdir, max_prof=8):
    """Datasets dentro de una zona, con su nombre RELATIVO ('a/b/c.txt' si esta anidado).
    Un dataset es una carpeta con part-*.parquet/.csv directos (formato Spark) o un archivo
    .parquet/.csv suelto. Los jobs con rutas absolutas del banco (INPUT_FILE=/opt/...) dejan
    el dataset en raw/opt/.../ARCHIVO.txt, por eso se busca en profundidad."""
    out = []
    base_n = zdir.rstrip(os.sep).count(os.sep)
    for raiz, dirs, files in os.walk(zdir):
        dirs[:] = sorted(d for d in dirs if not _oculto(d))
        visibles = [f for f in files if not _oculto(f)]
        datos = [f for f in visibles if os.path.splitext(f)[1].lower() in _EXT_DATOS]
        if raiz != zdir and datos and all(f.startswith("part-") for f in datos):
            out.append(os.path.relpath(raiz, zdir))  # carpeta Spark = un dataset
            dirs[:] = []
            continue
        for f in sorted(datos):
            out.append(os.path.relpath(os.path.join(raiz, f), zdir))
        if raiz.count(os.sep) - base_n >= max_prof:
            dirs[:] = []
    return [n.replace(os.sep, "/") for n in out]


def listar(base_path):
    base = validar_base(base_path)
    res = []
    for zona in ZONAS:
        zdir = _dir_zona(base, zona)
        if not zdir:
            continue
        for n in _candidatos(zdir):
            p = os.path.join(zdir, *n.split("/"))
            if not os.path.realpath(p).startswith(zdir + os.sep):
                continue  # symlink que escapa de la zona
            fmt, fs = archivos_dataset(p)
            if not fmt:
                continue
            tam = mt = 0
            for f in fs:
                try:
                    st = os.stat(f)
                except OSError:
                    continue
                tam += st.st_size
                mt = max(mt, st.st_mtime)
            res.append({"zona": zona, "nombre": n, "formato": fmt, "archivos": len(fs), "bytes": tam,
                        "modificado": _dt.datetime.fromtimestamp(mt).isoformat(timespec="seconds") if mt else ""})
    return {"ok": True, "base_path": base, "datasets": res}


# ---------------------------------------------------------------------------
# Motores
# ---------------------------------------------------------------------------
def _json_val(v):
    """Valor serializable en JSON y legible."""
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, float):
        return v if v == v and v not in (float("inf"), float("-inf")) else str(v)
    if isinstance(v, (_dt.datetime, _dt.date, _dt.time)):
        return v.isoformat(sep=" ") if isinstance(v, _dt.datetime) else v.isoformat()
    if isinstance(v, decimal.Decimal):
        return format(v, "f")
    if isinstance(v, (bytes, bytearray)):
        try:
            return bytes(v).decode("utf-8")
        except UnicodeDecodeError:
            return "0x" + bytes(v).hex()
    if isinstance(v, (list, tuple)):
        return [_json_val(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _json_val(x) for k, x in v.items()}
    return str(v)


class _Puro:
    nombre = "puro-python"

    def abrir(self, path):
        pf = _pl.ParquetPuro(path, MAX_BYTES)
        return ([{"nombre": c.nombre, "tipo": c.tipo} for c in pf.columnas], pf.num_filas, pf)

    def filas(self, pf, skip, take):
        return pf.leer_filas(skip, take)


class _Arrow:
    nombre = "pyarrow"

    def __init__(self):
        import pyarrow.parquet as pq  # noqa: F401
        self.pq = pq

    def abrir(self, path):
        pf = self.pq.ParquetFile(path)
        cols = [{"nombre": f.name, "tipo": str(f.type)} for f in pf.schema_arrow]
        return cols, pf.metadata.num_rows, pf

    def filas(self, pf, skip, take):
        md, visto, out = pf.metadata, 0, []
        for i in range(md.num_row_groups):
            n = md.row_group(i).num_rows
            if visto + n <= skip:
                visto += n
                continue
            if len(out) >= take:
                break
            if md.row_group(i).total_byte_size > MAX_BYTES * 4:
                raise VisorError("row group demasiado grande para el visor", "demasiado_grande")
            tabla = pf.read_row_group(i)
            ini = max(skip - visto, 0)
            tabla = tabla.slice(ini, take - len(out))
            cols = [c.to_pylist() for c in tabla.columns]
            out.extend([_json_val(v) for v in r] for r in zip(*cols))
            visto += n
        return out


class _Fast:
    nombre = "fastparquet"

    def __init__(self):
        import fastparquet  # noqa: F401
        self.fp = fastparquet

    def abrir(self, path):
        pf = self.fp.ParquetFile(path)
        cols = [{"nombre": c, "tipo": str(pf.dtypes.get(c, ""))} for c in pf.columns]
        return cols, pf.count(), pf

    def filas(self, pf, skip, take):
        out, visto = [], 0
        for i, rg in enumerate(pf.row_groups):
            n = rg.num_rows
            if visto + n <= skip:
                visto += n
                continue
            if len(out) >= take:
                break
            df = pf[i].to_pandas()
            ini = max(skip - visto, 0)
            df = df.iloc[ini:ini + take - len(out)]
            out.extend([_json_val(None if v != v else v) if not isinstance(v, (list, dict)) else _json_val(v)
                        for v in r] for r in df.itertuples(index=False, name=None))
            visto += n
        return out


def _motores():
    pref = os.environ.get("BNX_PARQUET_MOTOR", "").strip().lower()
    orden = [pref] if pref in ("pyarrow", "fastparquet", "puro") else ["pyarrow", "fastparquet", "puro"]
    for m in orden:
        if m == "puro":
            yield _Puro()
            continue
        try:
            yield _Arrow() if m == "pyarrow" else _Fast()
        except Exception:  # noqa: BLE001 - no instalado o roto: siguiente motor
            continue


def _leer_parquet(archivos, skip, take):
    ultimo = None
    for motor in _motores():
        try:
            return _leer_con(motor, archivos, skip, take)
        except VisorError:
            raise
        except _pl.ParquetNoSoportado as e:
            ultimo = e
        except Exception as e:  # noqa: BLE001 - archivo ilegible para este motor: probar otro
            if ultimo is None or not isinstance(ultimo, _pl.ParquetNoSoportado):
                ultimo = e
    if isinstance(ultimo, _pl.ParquetError):
        raise VisorError(str(ultimo), "no_soportado" if isinstance(ultimo, _pl.ParquetNoSoportado) else "corrupto")
    raise VisorError(f"no se pudo leer el parquet: {type(ultimo).__name__}: {ultimo}", "corrupto")


def _leer_con(motor, archivos, skip, take):
    cols, total, filas, visto = None, 0, [], 0
    for a in archivos:
        c, n, h = motor.abrir(a)
        if cols is None:
            cols = c
        elif [x["nombre"] for x in c] != [x["nombre"] for x in cols]:
            raise VisorError("los archivos del dataset tienen columnas distintas", "esquema")
        total += n
        if len(filas) < take and visto + n > skip:
            filas.extend(motor.filas(h, max(skip - visto, 0), take - len(filas)))
        visto += n
    return {"columnas": cols or [], "filas": filas, "total_filas": total, "motor": motor.nombre}


def _leer_csv(archivos, skip, take):
    cols, filas, total, visto = None, [], 0, 0
    contar = sum(os.path.getsize(a) for a in archivos) <= _CSV_MAX_CONTAR
    for a in archivos:
        with open(a, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
            rd = csv.reader(f)
            hdr = next(rd, None)
            if hdr is None:
                continue
            if cols is None:
                cols = hdr
            for r in rd:
                if skip <= visto < skip + take:
                    filas.append(r)
                visto += 1
                if not contar and visto >= skip + take:
                    break
        if not contar and visto >= skip + take:
            break
    return {"columnas": [{"nombre": c, "tipo": "string"} for c in (cols or [])], "filas": filas,
            "total_filas": visto if contar else None, "motor": "csv"}


def leer(base_path, zona, nombre, limite=LIMITE_DEFECTO, offset=0):
    try:
        limite = int(limite if limite not in (None, "") else LIMITE_DEFECTO)
        offset = int(offset if offset not in (None, "") else 0)
    except (TypeError, ValueError):
        raise VisorError("limite/offset deben ser enteros")
    limite = min(max(limite, 1), LIMITE_MAX)
    offset = max(offset, 0)
    p = resolver(base_path, zona, nombre)
    fmt, archivos = archivos_dataset(p)
    if not fmt:
        raise VisorError("el dataset no tiene archivos .parquet ni .csv", "vacio")
    r = _leer_parquet(archivos, offset, limite) if fmt == "parquet" else _leer_csv(archivos, offset, limite)
    r.update({"ok": True, "zona": zona, "nombre": nombre, "formato": fmt, "archivos": len(archivos),
              "limite": limite, "offset": offset})
    return r
