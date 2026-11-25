# -*- coding: utf-8 -*-
"""Orquestador: exportar / importar un PROYECTO completo (output/<proyecto>/) como un ZIP.

Sirve para mover un proyecto entre maquinas (macOS, Windows, Linux) en ambos sentidos.
- exportar(): empaqueta todo output/<proyecto>/ (planes, __pset, PySpark, shell, SQL, DAGs, params...).
- importar(): el ZIP es una frontera de confianza. Se valida (zip-slip, rutas absolutas, letras de
  unidad, symlinks, cifrado, cantidad/tamano/razon de compresion), se extrae SOLO a un proyecto NUEVO
  dentro de output/ (nunca pisa nada; si el nombre existe agrega _2, _3...), se validan los planes y
  se reescriben las rutas del origen (target, ruta, script, args, comando...) a las de este equipo.
  Nada de lo importado se ejecuta.
"""
import json
import os
import re
import shutil
import stat
import tempfile
import time
import zipfile

MAX_ARCHIVOS = 5000
MAX_ARCHIVO = 512 * 1024 * 1024        # bytes descomprimidos por archivo
MAX_TOTAL = 2 * 1024 * 1024 * 1024     # bytes descomprimidos en total
MAX_RAZON = 200                        # descomprimido / comprimido (solo archivos > 1 MB)
MAX_PLAN = 20 * 1024 * 1024            # un plan JSON mas grande que esto no es un plan
MANIFIESTO = "bnx_proyecto.json"
PROJ_RE = re.compile(r"[A-Za-z0-9][\w.\-]{0,63}")
ORQ_RE = re.compile(r"orquestacion_[\w.\-()]+\.json")
_IGNORAR_DIRS = {"__pycache__", "__MACOSX", "_staging"}
_IGNORAR_ARCH = {".DS_Store", "Thumbs.db", "desktop.ini"}
_UNIDAD = re.compile(r"^[A-Za-z]:")
_CTRL = re.compile(r"[\x00-\x1f\x7f]")
_RUTA_CLAVES = {"target", "ruta", "script", "jar", "origen", "destino"}
_TEXTO_CLAVES = {"comando", "sentencia"}
_LISTA_CLAVES = {"args", "spark_args"}


class ZipError(ValueError):
    """Error de validacion del ZIP o del proyecto (el mensaje va a la GUI, en espanol)."""


def _ignorado(nombre):
    return nombre in _IGNORAR_ARCH or nombre.startswith("._") or nombre.endswith(".pyc")


def nombre_proyecto(texto, defecto="importado"):
    n = re.sub(r"[^\w.\-]", "_", str(texto or "")).lstrip("._-")[:60]
    return n if PROJ_RE.fullmatch(n or "") else defecto


# ---------------------------------------------------------------------------
# Exportar
# ---------------------------------------------------------------------------
def listar_proyecto(carpeta):
    """[(ruta_absoluta, ruta_relativa_posix)] de todo el proyecto, sin symlinks ni basura."""
    out = []
    for d, dirs, files in os.walk(carpeta, followlinks=False):
        dirs[:] = sorted(x for x in dirs if x not in _IGNORAR_DIRS and not x.startswith(".")
                         and not os.path.islink(os.path.join(d, x)))
        for f in sorted(files):
            p = os.path.join(d, f)
            if _ignorado(f) or os.path.islink(p) or not os.path.isfile(p):
                continue
            out.append((p, os.path.relpath(p, carpeta).replace(os.sep, "/")))
    return out


def exportar(carpeta, proyecto, destino_zip):
    """ZIP de TODO output/<proyecto>/ (entradas '<proyecto>/<ruta>' + manifiesto). Devuelve el resumen."""
    if not os.path.isdir(carpeta):
        raise ZipError(f"el proyecto '{proyecto}' no existe en output/")
    archivos = listar_proyecto(carpeta)
    if not archivos:
        raise ZipError(f"el proyecto '{proyecto}' no tiene archivos")
    if len(archivos) > MAX_ARCHIVOS:
        raise ZipError(f"el proyecto tiene {len(archivos)} archivos (maximo {MAX_ARCHIVOS})")
    total = sum(os.path.getsize(p) for p, _ in archivos)
    if total > MAX_TOTAL:
        raise ZipError(f"el proyecto pesa {total // 1048576} MB (maximo {MAX_TOTAL // 1048576} MB)")
    import platform
    manifiesto = {"formato": "bnx-proyecto-1", "proyecto": proyecto, "so_origen": platform.system(),
                  "fecha": time.strftime("%Y-%m-%d %H:%M:%S"), "archivos": [r for _, r in archivos]}
    with zipfile.ZipFile(destino_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{proyecto}/{MANIFIESTO}", json.dumps(manifiesto, indent=2, ensure_ascii=False))
        for p, rel in archivos:
            zf.write(p, f"{proyecto}/{rel}")
    return {"proyecto": proyecto, "archivos": len(archivos), "bytes": total}


# ---------------------------------------------------------------------------
# Importar: validacion del ZIP
# ---------------------------------------------------------------------------
def _limpiar_nombre(nombre):
    """Nombre de entrada -> ruta POSIX relativa segura, o ZipError."""
    if _CTRL.search(nombre):
        raise ZipError(f"nombre de archivo con caracteres de control en el ZIP: {nombre!r}")
    n = nombre.replace("\\", "/")
    if n.startswith("/") or _UNIDAD.match(n):
        raise ZipError(f"ruta absoluta o con letra de unidad en el ZIP: {nombre!r}")
    partes = [p for p in n.split("/") if p not in ("", ".")]
    if not partes:
        raise ZipError(f"nombre vacio en el ZIP: {nombre!r}")
    for p in partes:
        if p == ".." or ":" in p or len(p) > 255:
            raise ZipError(f"ruta no permitida en el ZIP (path traversal o nombre invalido): {nombre!r}")
    return partes


def _entradas_validas(zf):
    """[(info, partes)] de los archivos del ZIP tras validar limites y tipos."""
    infos = zf.infolist()
    if len(infos) > MAX_ARCHIVOS:
        raise ZipError(f"el ZIP tiene {len(infos)} entradas (maximo {MAX_ARCHIVOS})")
    out, total = [], 0
    for i in infos:
        partes = _limpiar_nombre(i.filename)
        modo = i.external_attr >> 16
        if modo and stat.S_IFMT(modo) not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise ZipError(f"el ZIP contiene un enlace simbolico o archivo especial: {i.filename!r}")
        if i.is_dir():
            continue
        if i.flag_bits & 0x1:
            raise ZipError(f"el ZIP esta cifrado ({i.filename!r}); no se admite")
        if partes[0] in _IGNORAR_DIRS or any(p in _IGNORAR_DIRS for p in partes[:-1]) or _ignorado(partes[-1]):
            continue
        if i.file_size > MAX_ARCHIVO:
            raise ZipError(f"{i.filename!r} pesa {i.file_size // 1048576} MB (maximo {MAX_ARCHIVO // 1048576} MB)")
        if i.file_size > 1048576 and i.file_size > MAX_RAZON * max(i.compress_size, 1):
            raise ZipError(f"{i.filename!r} tiene una razon de compresion sospechosa (posible zip bomb)")
        total += i.file_size
        if total > MAX_TOTAL:
            raise ZipError(f"el ZIP descomprimido pesa mas de {MAX_TOTAL // 1048576} MB")
        out.append((i, partes))
    if not out:
        raise ZipError("el ZIP no contiene archivos")
    return out


def _quitar_prefijo(entradas):
    """Quita 'output/' y/o la carpeta unica de nivel superior (el ZIP exportado trae <proyecto>/).
    Devuelve (entradas_sin_prefijo, nombre_de_la_carpeta_quitada o None)."""
    carpeta = None
    for _ in range(2):
        tops = {p[0] for _, p in entradas}
        if len(tops) == 1 and all(len(p) > 1 for _, p in entradas):
            top = next(iter(tops))
            entradas = [(i, p[1:]) for i, p in entradas]
            if top.lower() != "output":
                carpeta = top
                break
        else:
            break
    return entradas, carpeta


def _copiar(zf, info, destino):
    """Extrae una entrada contando los bytes REALES (la cabecera puede mentir)."""
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    n = 0
    with zf.open(info) as src, open(destino, "xb") as dst:
        while True:
            b = src.read(1 << 16)
            if not b:
                break
            n += len(b)
            if n > MAX_ARCHIVO or (n > 1048576 and n > MAX_RAZON * max(info.compress_size, 1)):
                raise ZipError(f"{info.filename!r} excede los limites al descomprimir (posible zip bomb)")
            dst.write(b)
    return n


# ---------------------------------------------------------------------------
# Importar: reescritura de rutas del origen
# ---------------------------------------------------------------------------
class _Indice:
    """Archivos del proyecto importado por nombre, para resolver rutas de OTRA maquina."""

    def __init__(self, rels, proyecto_nuevo, origen):
        self.por_nombre = {}
        for r in rels:
            self.por_nombre.setdefault(r.rsplit("/", 1)[-1], []).append(r)
        self.nuevo = proyecto_nuevo
        self.origen = origen

    def resolver(self, texto):
        """Ruta de otra maquina (Windows o POSIX) -> 'output/<nuevo>/<rel>' o None."""
        if not isinstance(texto, str) or "://" in texto:
            return None
        partes = [p for p in _UNIDAD.sub("", texto.strip().replace("\\", "/")).split("/") if p not in ("", ".")]
        if not partes:
            return None
        cands = self.por_nombre.get(partes[-1])
        if not cands:
            return None
        low = [p.lower() for p in partes]
        if self.origen and "output" in low[:-1]:
            j = len(low) - 2 - low[-2::-1].index("output")
            if j + 1 < len(low) - 1 and low[j + 1] != self.origen.lower():
                return None  # apunta a OTRO proyecto de output/ que no viene en el ZIP

        def puntaje(rel):
            c = rel.split("/")
            n = 0
            while n < min(len(c), len(partes)) and c[-1 - n] == partes[-1 - n]:
                n += 1
            return (n, -len(c))
        mejor = max(cands, key=puntaje)
        return f"output/{self.nuevo}/{mejor}"

    def en_texto(self, texto):
        """Reescribe las rutas (con separador) incluidas en un comando/lista de argumentos."""
        def sub(m):
            tok = m.group(0)
            q = tok[0] if tok[0] in "\"'" and len(tok) > 1 and tok[-1] == tok[0] else ""
            cuerpo = tok[1:-1] if q else tok
            if "/" not in cuerpo and "\\" not in cuerpo:
                return tok
            nuevo = self.resolver(cuerpo)
            if not nuevo:
                return tok
            if not q and re.search(r"\s", nuevo):
                q = '"'
            return f"{q}{nuevo}{q}"
        return re.sub(r"\"[^\"]*\"|'[^']*'|\S+", sub, texto)


def _reescribir(nodo, idx, avisos, ctx, cuenta):
    if isinstance(nodo, dict):
        for k in list(nodo):
            v = nodo[k]
            if k == "io":
                continue
            if k in _RUTA_CLAVES and isinstance(v, str):
                nuevo = idx.resolver(v)
                if nuevo:
                    if nuevo != v:
                        cuenta[0] += 1
                    nodo[k] = nuevo
                    if nodo.get("status") == "faltante":
                        nodo["status"] = "ok"
                elif k == "target":
                    avisos.append(f"{ctx}: no se encontro en el ZIP el archivo de {v!r}")
            elif k in _TEXTO_CLAVES and isinstance(v, str):
                nuevo = idx.en_texto(v)
                cuenta[0] += nuevo != v
                nodo[k] = nuevo
            elif k in _LISTA_CLAVES and isinstance(v, list):
                nuevos = [idx.en_texto(x) if isinstance(x, str) else x for x in v]
                cuenta[0] += nuevos != v
                nodo[k] = nuevos
            else:
                _reescribir(v, idx, avisos, ctx, cuenta)
    elif isinstance(nodo, list):
        for x in nodo:
            _reescribir(x, idx, avisos, ctx, cuenta)


def _es_abs(p):
    return p.startswith("/") or bool(_UNIDAD.match(p)) or p.startswith("\\\\")


def _ajustar_ejecucion(plan, avisos, ctx):
    """base_path / spark_submit del origen: si son rutas absolutas que no existen aqui, se
    dejan al valor por defecto de este equipo (el usuario los define en el Orquestador)."""
    ej = plan.get("ejecucion")
    if not isinstance(ej, dict):
        return
    bp = ej.get("base_path")
    if isinstance(bp, str) and bp and "://" not in bp and _es_abs(bp.strip()) and not os.path.isdir(bp):
        avisos.append(f"{ctx}: base_path del origen ({bp}) no existe aqui; quedo vacio, defina la carpeta de datos")
        ej["base_path"] = ""
    ss = ej.get("spark_submit")
    if isinstance(ss, str) and _es_abs(ss.strip()) and not os.path.exists(ss):
        ej["spark_submit"] = re.split(r"[\\/]", ss.strip())[-1] or "spark-submit"


def _es_plan(obj):
    return isinstance(obj, dict) and isinstance(obj.get("steps"), list)


# ---------------------------------------------------------------------------
# Importar
# ---------------------------------------------------------------------------
def importar(zip_path, root, nombre=None, defecto=None):
    """Importa el ZIP a un proyecto NUEVO de <root>/output/. Devuelve el resumen (dict).
    nombre: nombre pedido; defecto: se usa si el ZIP no trae nombre de proyecto. ZipError con el motivo si el ZIP o algun plan no es valido; en ese caso no queda nada escrito."""
    from src import orquestador as orq
    out_dir = os.path.join(root, "output")
    os.makedirs(out_dir, exist_ok=True)
    try:
        zf = zipfile.ZipFile(zip_path)
    except (zipfile.BadZipFile, OSError):
        raise ZipError("el archivo no es un ZIP valido")
    with zf:
        entradas, carpeta = _quitar_prefijo(_entradas_validas(zf))
        rels, vistos = [], set()
        for i, p in entradas:
            rel = "/".join(p)
            if rel.lower() in vistos:
                raise ZipError(f"el ZIP repite el archivo {rel!r}")
            vistos.add(rel.lower())
            rels.append(rel)
        manifiesto, origen = None, carpeta
        for (i, _), rel in zip(entradas, rels):
            if rel == MANIFIESTO and i.file_size < MAX_PLAN:
                try:
                    manifiesto = json.loads(zf.read(i).decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    manifiesto = None
        if isinstance(manifiesto, dict) and isinstance(manifiesto.get("proyecto"), str):
            origen = manifiesto["proyecto"]
        base = nombre_proyecto(nombre or origen or defecto or os.path.splitext(os.path.basename(zip_path))[0])
        final, k = base, 1
        while os.path.exists(os.path.join(out_dir, final)):
            k += 1
            final = f"{base[:60]}_{k}"
        stage = tempfile.mkdtemp(prefix=".import_", dir=out_dir)
        try:
            n, total = 0, 0
            for (i, _), rel in zip(entradas, rels):
                if rel == MANIFIESTO:
                    continue
                destino = os.path.join(stage, *rel.split("/"))
                if os.path.commonpath([os.path.realpath(destino), os.path.realpath(stage)]) != os.path.realpath(stage):
                    raise ZipError(f"ruta fuera del proyecto: {rel!r}")
                total += _copiar(zf, i, destino)
                if total > MAX_TOTAL:
                    raise ZipError("el ZIP excede el tamano total permitido al descomprimir")
                n += 1
            res = _procesar(stage, final, origen, orq, root)
            os.chmod(stage, 0o755)
            os.rename(stage, os.path.join(out_dir, final))
            stage = None
        finally:
            if stage:
                shutil.rmtree(stage, ignore_errors=True)
    return {"ok": True, "proyecto": final, "archivos": n,
            "planes": [f"output/{final}/{r}" for r in res["planes"]],
            "reescritas": res["reescritas"], "avisos": res["avisos"]}


def _listar_rel(stage):
    out = []
    for d, _, files in os.walk(stage):
        for f in files:
            out.append(os.path.relpath(os.path.join(d, f), stage).replace(os.sep, "/"))
    return sorted(out)


def _procesar(stage, proyecto, origen, orq, root):
    """Detecta planes, los valida y reescribe sus rutas hacia output/<proyecto>/. Escribe en stage."""
    planes, avisos, cuenta = [], [], [0]
    for rel in _listar_rel(stage):
        if not rel.lower().endswith(".json") or rel == MANIFIESTO:
            continue
        ruta = os.path.join(stage, *rel.split("/"))
        base = rel.rsplit("/", 1)[-1]
        orq_nombre = bool(ORQ_RE.fullmatch(base))
        if os.path.getsize(ruta) > MAX_PLAN:
            if orq_nombre:
                raise ZipError(f"{rel}: el plan es demasiado grande")
            continue
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except (ValueError, UnicodeDecodeError):
            if orq_nombre:
                raise ZipError(f"{rel}: no es un JSON valido")
            continue
        if not orq_nombre and not _es_plan(obj):
            continue
        if not _es_plan(obj):
            raise ZipError(f"{rel}: no es una orquestacion (falta la lista 'steps')")
        try:
            orq.validar_plan(obj)
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            raise ZipError(f"{rel}: plan invalido ({e})")
        if not orq_nombre:      # JSON suelto con forma de plan: se vuelve visible al Orquestador
            stem = nombre_proyecto(os.path.splitext(base)[0], "plan")
            nuevo = f"orquestacion_{stem}.json"
            k = 1
            while os.path.exists(os.path.join(os.path.dirname(ruta), nuevo)):
                k += 1
                nuevo = f"orquestacion_{stem}_{k}.json"
            os.rename(ruta, os.path.join(os.path.dirname(ruta), nuevo))
            rel = rel[:len(rel) - len(base)] + nuevo
        planes.append(rel)
    rels = _listar_rel(stage)
    idx = _Indice(rels, proyecto, origen)
    for rel in planes:
        ruta = os.path.join(stage, *rel.split("/"))
        with open(ruta, "r", encoding="utf-8") as f:
            plan = json.load(f)
        ctx = rel.rsplit("/", 1)[-1]
        _reescribir(plan, idx, avisos, ctx, cuenta)
        _ajustar_ejecucion(plan, avisos, ctx)
        if "proyecto" in plan:
            plan["proyecto"] = proyecto
        try:
            orq.validar_plan(plan)
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            raise ZipError(f"{ctx}: el plan quedo invalido al reescribir rutas ({e})")
        orq._write(ruta, plan)
        dag = os.path.join(os.path.dirname(ruta),
                           re.sub(r"[^\w.\-]", "_", "dag_" + orq.dag_id_de(plan)[len("bnx_"):] + ".py"))
        if os.path.isfile(dag):     # el DAG del origen tiene rutas del origen: se regenera
            try:
                texto = orq.generar_airflow(plan, root)
                with open(dag, "w", encoding="utf-8", newline="\n") as f:
                    f.write(texto)
            except (ValueError, KeyError, TypeError, OSError):
                avisos.append(f"{os.path.basename(dag)}: no se pudo regenerar; revise sus rutas")
    return {"planes": planes, "reescritas": cuenta[0], "avisos": avisos[:50]}
