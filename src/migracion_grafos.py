# src/migracion_grafos.py
"""
Migracion de grafos Ab Initio: seguimiento por lote (carpeta de abinitio/).

Cada .mp es una fila "grafo" y cada .plan una fila "plan". Por fila se guarda:
clasificacion de complejidad (automatica, con razones; se puede sobrescribir a mano),
fuente/destino, psets asociados, estado con historial, notas y participantes por rol.

Todo pasa por handle(action, data) -> (status_http, dict), asi se prueba sin servidor.
Datos en data/migracion_grafos.json (ruta sobreescribible con BNX_MIGRACION_DATA).

Modelo: las personas viven SOLO en "personas" (nombre/correo); cada grafo guarda
persona_id + rol. Sirve igual para alta a mano o para un catalogo de participantes.

Clasificacion (ver REGLAS, ajustables). Orden de evaluacion:
  Alto : subgrafos + planes anidados >= subgrafos_alto, o COBOL, o logica dinamica
         ($[...]), o plan con >= plan_grafos_alto grafos, o tablas entrada+salida
         >= tablas_alto, o componentes >= componentes_alto.
  Medio: join/rollup/lookup/dedup/scan, rechazos, o >= fuentes_medio fuentes distintas.
  Simple: el resto.
Compatible con Python 3.8.
"""
import csv
import hashlib
import io
import json
import os
import re
import threading
import uuid
import zipfile
from datetime import datetime
from xml.sax.saxutils import escape as _xml_escape

from src import mp_parser
from src import pset_map

ESTADOS = ["pendiente", "en migracion", "convertido", "en revision", "validado", "en produccion"]
ROLES = ["responsable", "revisor", "dueno", "qa"]
NIVELES = ["Simple", "Medio", "Alto"]
# Meta de distribucion (% de grafos por nivel)
META = {"Simple": 50, "Medio": 30, "Alto": 20}

# Umbrales de clasificacion (ajustar aqui)
REGLAS = {
    "subgrafos_alto": 1,      # subgrafos (o planes anidados) a partir de los cuales es Alto
    "plan_grafos_alto": 5,    # plan que agrupa al menos tantos grafos
    "tablas_alto": 6,         # tablas de entrada + salida
    "componentes_alto": 25,   # total de componentes
    "fuentes_medio": 2,       # fuentes distintas para ser al menos Medio
}

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOCK = threading.RLock()


class MigracionError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Analisis y clasificacion
# ---------------------------------------------------------------------------

_MOTORES = [("Teradata", re.compile(r"teradata|\btd_", re.I)),
            ("Oracle", re.compile(r"oracle", re.I)),
            ("Cloudera", re.compile(r"hive|impala|cloudera", re.I)),
            ("Mongo", re.compile(r"mongo", re.I))]
_TABLA_NO_DET = "tabla (motor no detectado)"


def _texto_nodo(n):
    return " ".join(str(v) for v in n.values() if v is not None and not isinstance(v, (list, dict)))


def detectar_fuente_destino(nodes):
    """(fuente, destino): listas sin duplicados segun prototype/mpname/nombre/data_path."""
    fuente, destino = [], []
    for n in nodes:
        t = _texto_nodo(n)
        tl = t.lower()
        typ = str(n.get("type", "")).upper()
        proto = (str(n.get("prototype", "")) + " " + str(n.get("name", ""))).lower()
        if "input" in proto or typ == "SOURCE":
            lista = fuente
        elif "output" in proto or typ == "SINK":
            lista = destino
        else:
            continue
        motor = next((nm for nm, rx in _MOTORES if rx.search(t)), None)
        if motor is None:
            if "table" in tl:
                motor = _TABLA_NO_DET
            elif "file" in tl or n.get("data_path"):
                motor = "archivo"
            else:
                continue
        if motor not in lista:
            lista.append(motor)
    return fuente, destino


def _metricas_vacias():
    return {"componentes": 0, "join": 0, "dedup": 0, "rollup": 0, "scan": 0, "lookup": 0,
            "rechazos": 0, "subgrafos": 0, "cobol": 0, "dinamico": 0, "tablas_in": 0,
            "tablas_out": 0, "fuentes": 0, "grafos_plan": 0, "planes_anidados": 0}


def _leer(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def analizar_grafo(path):
    """Metricas + fuente/destino de un .mp (o .plan). Devuelve {metricas, fuente, destino}."""
    m = _metricas_vacias()
    if path.lower().endswith(".plan"):
        info = pset_map.parse_plan_tasks(path)
        graficos, planes = set(), set()
        for t in info["tasks"].values():
            for r in t["refs"]:
                k = pset_map._kind_of(r)
                if k in ("graph", "pset"):
                    graficos.add(r.lower())
                elif k == "plan":
                    planes.add(r.lower())
        m["grafos_plan"] = len(graficos)
        m["planes_anidados"] = len(planes)
        return {"metricas": m, "fuente": [], "destino": []}
    texto = _leer(path)
    try:
        ast = mp_parser.parse_mp_ast(path)
    except Exception:  # noqa: BLE001 - un .mp raro no debe tumbar el lote
        ast = {"nodes": [], "subgraphs": {}}
    nodes = ast.get("nodes", [])
    m["componentes"] = len(nodes)
    for n in nodes:
        tl = _texto_nodo(n).lower()
        typ = str(n.get("type", "")).upper()
        if "join" in tl or typ == "JOIN":
            m["join"] += 1
        if "dedup" in tl or typ == "DEDUP":
            m["dedup"] += 1
        if "rollup" in tl or "aggregate" in tl:
            m["rollup"] += 1
        if re.search(r"\bscan\b|\bscan[-_]", tl):
            m["scan"] += 1
        if "lookup" in tl:
            m["lookup"] += 1
        if re.search(r"reject|error|validate", tl):
            m["rechazos"] += 1
        if re.search(r"cobol|copybook|\.cbl", tl):
            m["cobol"] += 1
    m["subgrafos"] = (len(re.findall(r"Subgraph created from graph", texto))
                      + len(ast.get("subgraphs") or {}))
    if re.search(r"cobol|copybook|\.cbl", texto, re.I):
        m["cobol"] = max(m["cobol"], 1)
    m["dinamico"] = texto.count("$[")
    fuente, destino = detectar_fuente_destino(nodes)
    for n in nodes:
        proto = (str(n.get("prototype", "")) + " " + str(n.get("name", ""))).lower()
        if "input_table" in proto or "input table" in proto:
            m["tablas_in"] += 1
        elif "output_table" in proto or "output table" in proto:
            m["tablas_out"] += 1
    m["fuentes"] = len(fuente)
    return {"metricas": m, "fuente": fuente, "destino": destino}


def clasificar(m, reglas=None):
    """{nivel, razones, metricas}. Cada razon dice la regla disparada y su valor."""
    r = reglas or REGLAS
    alto = []
    anid = m["subgrafos"] + m["planes_anidados"]
    if anid >= r["subgrafos_alto"]:
        alto.append("%d subgrafos/planes anidados (>=%d)" % (anid, r["subgrafos_alto"]))
    if m["cobol"]:
        alto.append("usa COBOL/copybook (%d)" % m["cobol"])
    if m["dinamico"]:
        alto.append("logica dinamica $[...] (%d)" % m["dinamico"])
    if m["grafos_plan"] >= r["plan_grafos_alto"]:
        alto.append("plan con %d grafos (>=%d)" % (m["grafos_plan"], r["plan_grafos_alto"]))
    tablas = m["tablas_in"] + m["tablas_out"]
    if tablas >= r["tablas_alto"]:
        alto.append("%d tablas entrada+salida (>=%d)" % (tablas, r["tablas_alto"]))
    if m["componentes"] >= r["componentes_alto"]:
        alto.append("%d componentes (>=%d)" % (m["componentes"], r["componentes_alto"]))
    if alto:
        return {"nivel": "Alto", "razones": alto, "metricas": m}
    medio = []
    for k, nm in (("join", "join"), ("rollup", "rollup"), ("lookup", "lookup"),
                  ("dedup", "dedup"), ("scan", "scan"), ("rechazos", "rechazos")):
        if m[k]:
            medio.append("%d %s" % (m[k], nm))
    if m["fuentes"] >= r["fuentes_medio"]:
        medio.append("%d fuentes distintas (>=%d)" % (m["fuentes"], r["fuentes_medio"]))
    if medio:
        return {"nivel": "Medio", "razones": medio, "metricas": m}
    return {"nivel": "Simple",
            "razones": ["sin join/rollup/lookup/dedup/scan, rechazos, subgrafos ni COBOL; "
                        "%d componentes" % m["componentes"]],
            "metricas": m}


# ---------------------------------------------------------------------------
# Almacenamiento
# ---------------------------------------------------------------------------

def _ruta_datos():
    return os.environ.get("BNX_MIGRACION_DATA") or os.path.join(_ROOT, "data", "migracion_grafos.json")


def _vacio():
    return {"version": 1, "personas": {}, "lotes": {}, "grafos": {}}


def cargar():
    p = _ruta_datos()
    with _LOCK:
        if not os.path.isfile(p):
            return _vacio()
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
    for k, v in _vacio().items():
        d.setdefault(k, v)
    return d


def guardar(d):
    p = _ruta_datos()
    with _LOCK:
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        os.replace(tmp, p)


def _ahora():
    return datetime.now().isoformat(timespec="seconds")


def _hash(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:8]


# ---------------------------------------------------------------------------
# Lotes
# ---------------------------------------------------------------------------

def _carpeta_segura(carpeta):
    """Ruta real de una carpeta bajo <repo>/abinitio o MigracionError."""
    if not isinstance(carpeta, str) or not carpeta.strip():
        raise MigracionError("falta 'carpeta'")
    base = os.path.realpath(os.path.join(_ROOT, "abinitio"))
    p = os.path.realpath(os.path.join(_ROOT, carpeta.strip()))
    if not (p == base or p.startswith(base + os.sep)):
        raise MigracionError("la carpeta debe estar dentro de abinitio/")
    if not os.path.isdir(p):
        raise MigracionError("la carpeta no existe: %s" % carpeta)
    return p


def _conversiones(carpeta):
    """{archivo.mp en minusculas sin prefijo: ruta relativa del *_spark.py} (criterio del orquestador)."""
    from src import orquestador as orq
    idx = orq._index_converted(os.path.join(_ROOT, "output", os.path.basename(carpeta)))
    return {k: os.path.relpath(v, _ROOT) for k, v in idx.items()}


def cargar_lote(carpeta):
    real = _carpeta_segura(carpeta)
    mapa = pset_map.scan(real)
    inst = {k.lower(): v for k, v in mapa["instances"].items()}
    lid = "l_" + _hash(real)
    nuevos = 0
    with _LOCK:
        d = cargar()
        lote = d["lotes"].setdefault(lid, {"id": lid, "nombre": os.path.basename(real),
                                           "carpeta": os.path.relpath(real, _ROOT), "creado": _ahora()})
        vistos = set()
        for fname in sorted(os.listdir(real)):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in (".mp", ".plan"):
                continue
            path = os.path.join(real, fname)
            gid = "g_" + _hash(lid + fname)
            vistos.add(gid)
            an = analizar_grafo(path)
            auto = clasificar(an["metricas"])
            g = d["grafos"].get(gid)
            if g is None:
                nuevos += 1
                g = {"id": gid, "lote": lid, "archivo": fname, "nombre": pset_map._norm_name(fname),
                     "clasif": {"manual": None, "nota_manual": ""}, "estado": ESTADOS[0],
                     "historial": [], "notas": [], "participantes": []}
                d["grafos"][gid] = g
            g["tipo"] = "plan" if ext == ".plan" else "grafo"
            g["psets"] = sorted(inst.get(pset_map._norm_name(fname).lower(), []))
            g["clasif"]["auto"] = auto
            g["fuente"], g["destino"] = an["fuente"], an["destino"]
            g["presente"] = True
        for g in d["grafos"].values():  # no se borra nada de lo registrado
            if g["lote"] == lid and g["id"] not in vistos:
                g["presente"] = False
        guardar(d)
    return {"lote": lote, "grafos": len(vistos), "nuevos": nuevos}


def _vista(g, d, conv):
    v = dict(g)
    manual = g["clasif"].get("manual")
    v["nivel"] = manual or g["clasif"]["auto"]["nivel"]
    v["es_manual"] = bool(manual)
    v["razones"] = g["clasif"]["auto"]["razones"]
    v["conversion"] = (conv.get(pset_map._norm_name(g["archivo"]).lower())
                       if g["tipo"] == "grafo" else None)
    v["participantes"] = [dict(p, **{k: d["personas"].get(p["persona_id"], {}).get(k, "")
                                     for k in ("nombre", "correo")}) for p in g["participantes"]]
    return v


def _lote_de(d, lote):
    if lote not in d["lotes"]:
        raise MigracionError("lote desconocido: %s" % lote)
    return d["lotes"][lote]


def listar_grafos(lote, nivel=None, estado=None, persona=None):
    d = cargar()
    l = _lote_de(d, lote)
    conv = _conversiones(l["carpeta"])
    out = []
    for g in d["grafos"].values():
        if g["lote"] != lote:
            continue
        v = _vista(g, d, conv)
        if nivel and v["nivel"] != nivel:
            continue
        if estado and v["estado"] != estado:
            continue
        if persona and persona not in [p["persona_id"] for p in g["participantes"]]:
            continue
        out.append(v)
    return sorted(out, key=lambda x: x["archivo"].lower())


def _grafo(d, gid):
    g = d["grafos"].get(gid)
    if g is None:
        raise MigracionError("grafo desconocido: %s" % gid)
    return g


# ---------------------------------------------------------------------------
# Mutaciones
# ---------------------------------------------------------------------------

def _mutar(gid, fn):
    with _LOCK:
        d = cargar()
        g = _grafo(d, gid)
        fn(d, g)
        guardar(d)
        return _vista(g, d, {})


def cambiar_estado(gid, estado, nota=""):
    if estado not in ESTADOS:
        raise MigracionError("estado invalido: %s (validos: %s)" % (estado, ", ".join(ESTADOS)))

    def f(d, g):
        g["historial"].append({"fecha": _ahora(), "de": g["estado"], "a": estado, "nota": str(nota or "")})
        g["estado"] = estado
    return _mutar(gid, f)


def agregar_nota(gid, texto):
    if not isinstance(texto, str) or not texto.strip():
        raise MigracionError("la nota esta vacia")

    def f(d, g):
        g["notas"].append({"fecha": _ahora(), "texto": texto.strip()})
    return _mutar(gid, f)


def sobrescribir_clasificacion(gid, nivel, nota=""):
    if nivel is not None and nivel not in NIVELES:
        raise MigracionError("nivel invalido: %s (validos: %s)" % (nivel, ", ".join(NIVELES)))

    def f(d, g):
        g["clasif"]["manual"] = nivel
        g["clasif"]["nota_manual"] = str(nota or "") if nivel else ""
    return _mutar(gid, f)


_CORREO_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _persona_de(d, nombre, correo):
    """Busca por correo o nombre y reutiliza; si no existe, la crea."""
    nombre, correo = str(nombre or "").strip(), str(correo or "").strip()
    if not nombre:
        raise MigracionError("falta el nombre de la persona")
    if correo and not _CORREO_RE.match(correo):
        raise MigracionError("correo invalido")
    for p in d["personas"].values():
        if correo and p["correo"].lower() == correo.lower():
            return p
    for p in d["personas"].values():
        if not correo and p["nombre"].lower() == nombre.lower():
            return p
    pid = "p_" + uuid.uuid4().hex[:8]
    d["personas"][pid] = {"id": pid, "nombre": nombre, "correo": correo}
    return d["personas"][pid]


def asignar(gid, rol, persona_id=None, nombre=None, correo=None):
    if rol not in ROLES:
        raise MigracionError("rol invalido: %s (validos: %s)" % (rol, ", ".join(ROLES)))

    def f(d, g):
        if persona_id:
            if persona_id not in d["personas"]:
                raise MigracionError("persona desconocida: %s" % persona_id)
            pid = persona_id
        else:
            pid = _persona_de(d, nombre, correo)["id"]
        if not any(p["persona_id"] == pid and p["rol"] == rol for p in g["participantes"]):
            g["participantes"].append({"persona_id": pid, "rol": rol})
    return _mutar(gid, f)


def quitar(gid, persona_id, rol=None):
    def f(d, g):
        g["participantes"] = [p for p in g["participantes"]
                              if not (p["persona_id"] == persona_id and (rol is None or p["rol"] == rol))]
    return _mutar(gid, f)


def persona_guardar(pid, nombre, correo):
    with _LOCK:
        d = cargar()
        if pid:
            if pid not in d["personas"]:
                raise MigracionError("persona desconocida: %s" % pid)
            nombre, correo = str(nombre or "").strip(), str(correo or "").strip()
            if not nombre:
                raise MigracionError("falta el nombre de la persona")
            if correo and not _CORREO_RE.match(correo):
                raise MigracionError("correo invalido")
            d["personas"][pid].update(nombre=nombre, correo=correo)
            p = d["personas"][pid]
        else:
            p = _persona_de(d, nombre, correo)
        guardar(d)
        return p


def persona_borrar(pid):
    with _LOCK:
        d = cargar()
        if pid not in d["personas"]:
            raise MigracionError("persona desconocida: %s" % pid)
        if any(p["persona_id"] == pid for g in d["grafos"].values() for p in g["participantes"]):
            raise MigracionError("la persona esta asignada a grafos; quitela primero")
        del d["personas"][pid]
        guardar(d)


# ---------------------------------------------------------------------------
# Resumen y exportacion
# ---------------------------------------------------------------------------

def resumen(lote):
    d = cargar()
    _lote_de(d, lote)
    gs = [g for g in d["grafos"].values() if g["lote"] == lote]
    total = len(gs)

    def pct(n):
        return round(100.0 * n / total, 1) if total else 0.0
    niv = {}
    for n in NIVELES:
        c = sum(1 for g in gs if (g["clasif"].get("manual") or g["clasif"]["auto"]["nivel"]) == n)
        niv[n] = {"cantidad": c, "porcentaje": pct(c), "meta": META[n],
                  "diferencia": round(pct(c) - META[n], 1)}
    est = {}
    for e in ESTADOS:
        c = sum(1 for g in gs if g["estado"] == e)
        est[e] = {"cantidad": c, "porcentaje": pct(c)}
    carga = {}
    for g in gs:
        for p in g["participantes"]:
            pe = d["personas"].get(p["persona_id"])
            if not pe:
                continue
            c = carga.setdefault(p["persona_id"], {"persona_id": p["persona_id"], "nombre": pe["nombre"],
                                                   "correo": pe["correo"], "roles": {}, "total": 0,
                                                   "abiertos": 0})
            c["roles"][p["rol"]] = c["roles"].get(p["rol"], 0) + 1
            c["total"] += 1
            if g["estado"] != "en produccion":
                c["abiertos"] += 1
    return {"total": total, "niveles": niv, "estados": est,
            "personas": sorted(carga.values(), key=lambda x: x["nombre"].lower())}


_COLUMNAS = ["archivo", "tipo", "nivel", "clasificacion_manual", "razones", "fuente", "destino",
             "estado", "psets", "participantes", "notas", "conversion"]


def _celda(v):
    s = "" if v is None else str(v)
    if s[:1] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s  # neutraliza formulas (inyeccion CSV/Excel)
    return s


def _filas(lote):
    gs = listar_grafos(lote)
    filas = []
    for g in gs:
        filas.append([
            g["archivo"], g["tipo"], g["nivel"], "si" if g["es_manual"] else "no",
            "; ".join(g["razones"]), ", ".join(g["fuente"]), ", ".join(g["destino"]),
            g["estado"], ", ".join(g["psets"]),
            "; ".join("%s: %s <%s>" % (p["rol"], p["nombre"], p["correo"]) for p in g["participantes"]),
            len(g["notas"]), g["conversion"] or ""])
    return [_COLUMNAS] + [[_celda(c) for c in f] for f in filas]


def exportar_csv(lote):
    buf = io.StringIO(newline="")
    csv.writer(buf, lineterminator="\r\n").writerows(_filas(lote))
    return buf.getvalue().encode("utf-8-sig")


_XML_BAD = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _col(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def exportar_xlsx(lote):
    filas = _filas(lote)
    rows = []
    for ri, fila in enumerate(filas, 1):
        cs = "".join('<c r="%s%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
                     % (_col(ci), ri, _xml_escape(_XML_BAD.sub("", str(v)))) for ci, v in enumerate(fila))
        rows.append('<row r="%d">%s</row>' % (ri, cs))
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    pk = "http://schemas.openxmlformats.org/package/2006/relationships"
    hdr = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    partes = {
        "[Content_Types].xml": hdr + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.'
        'spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-'
        'officedocument.spreadsheetml.worksheet+xml"/></Types>',
        "_rels/.rels": hdr + '<Relationships xmlns="%s"><Relationship Id="rId1" Type="%s/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>' % (pk, rel),
        "xl/workbook.xml": hdr + '<workbook xmlns="%s" xmlns:r="%s"><sheets><sheet name="Migracion" '
        'sheetId="1" r:id="rId1"/></sheets></workbook>' % (ns, rel),
        "xl/_rels/workbook.xml.rels": hdr + '<Relationships xmlns="%s"><Relationship Id="rId1" '
        'Type="%s/worksheet" Target="worksheets/sheet1.xml"/></Relationships>' % (pk, rel),
        "xl/worksheets/sheet1.xml": hdr + '<worksheet xmlns="%s"><sheetData>%s</sheetData></worksheet>'
        % (ns, "".join(rows)),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for nm, xml in partes.items():
            z.writestr(nm, xml.encode("utf-8"))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Despachador
# ---------------------------------------------------------------------------

ACCIONES_ESCRITURA = ("cargar", "estado", "nota", "clasificar", "asignar", "quitar",
                      "persona_guardar", "persona_borrar")


def _carpetas_disponibles():
    base = os.path.join(_ROOT, "abinitio")
    if not os.path.isdir(base):
        return []
    return sorted("abinitio/" + n for n in os.listdir(base) if os.path.isdir(os.path.join(base, n)))


def _req(data, k):
    v = data.get(k)
    if not v:
        raise MigracionError("falta '%s'" % k)
    return v


def handle(action, data):
    """(status, dict). Errores de uso -> (400, {ok: False, error})."""
    data = data if isinstance(data, dict) else {}
    try:
        if action == "lotes":
            d = cargar()
            return 200, {"ok": True, "lotes": sorted(d["lotes"].values(), key=lambda x: x["nombre"]),
                         "carpetas": _carpetas_disponibles(), "estados": ESTADOS, "roles": ROLES,
                         "niveles": NIVELES, "meta": META}
        if action == "cargar":
            return 200, dict(ok=True, **cargar_lote(_req(data, "carpeta")))
        if action == "grafos":
            return 200, {"ok": True, "grafos": listar_grafos(
                _req(data, "lote"), data.get("nivel") or None, data.get("estado") or None,
                data.get("persona") or None)}
        if action == "grafo":
            d = cargar()
            g = _grafo(d, _req(data, "id"))
            return 200, {"ok": True, "grafo": _vista(g, d, _conversiones(d["lotes"][g["lote"]]["carpeta"]))}
        if action == "estado":
            return 200, {"ok": True, "grafo": cambiar_estado(_req(data, "id"), data.get("estado"),
                                                             data.get("nota", ""))}
        if action == "nota":
            return 200, {"ok": True, "grafo": agregar_nota(_req(data, "id"), data.get("texto"))}
        if action == "clasificar":
            return 200, {"ok": True, "grafo": sobrescribir_clasificacion(
                _req(data, "id"), data.get("nivel") or None, data.get("nota", ""))}
        if action == "asignar":
            return 200, {"ok": True, "grafo": asignar(_req(data, "id"), data.get("rol"),
                                                      data.get("persona_id"), data.get("nombre"),
                                                      data.get("correo"))}
        if action == "quitar":
            return 200, {"ok": True, "grafo": quitar(_req(data, "id"), _req(data, "persona_id"),
                                                     data.get("rol") or None)}
        if action == "personas":
            return 200, {"ok": True, "personas": sorted(cargar()["personas"].values(),
                                                        key=lambda x: x["nombre"].lower())}
        if action == "persona_guardar":
            return 200, {"ok": True, "persona": persona_guardar(data.get("id"), data.get("nombre"),
                                                                data.get("correo"))}
        if action == "persona_borrar":
            persona_borrar(_req(data, "id"))
            return 200, {"ok": True}
        if action == "resumen":
            return 200, dict(ok=True, **resumen(_req(data, "lote")))
        if action == "exportar":
            lote = _req(data, "lote")
            fmt = str(data.get("fmt") or "csv").lower()
            if fmt == "csv":
                cont, ctype = exportar_csv(lote), "text/csv; charset=utf-8"
            elif fmt == "xlsx":
                cont = exportar_xlsx(lote)
                ctype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                raise MigracionError("formato invalido: %s (csv o xlsx)" % fmt)
            nombre = "migracion_%s.%s" % (cargar()["lotes"][lote]["nombre"], fmt)
            return 200, {"ok": True, "binario": (cont, re.sub(r"[^\w.\-]", "_", nombre), ctype)}
        return 404, {"ok": False, "error": "accion desconocida: %s" % action}
    except MigracionError as e:
        return 400, {"ok": False, "error": str(e)}
