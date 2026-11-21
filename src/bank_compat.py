# -*- coding: utf-8 -*-
"""bank_compat - diagnostico y capa de compatibilidad GENERICA de las librerias del banco (mex-lib*).

Solo biblioteca estandar y sintaxis de Python 3.8 (el portal corre en 3.8; el paquete generado lleva ESTE
mismo archivo como bank_compat.py junto a main.py).

Dos mitades:
  * ANALISIS (al armar el paquete): para CADA wheel/sdist del banco, sin ejecutar nada (zipfile + ast):
      a) imports a submodulos de la propia libreria que no existen (con archivo:linea, funcion y la condicion
         'solo si la fuente es X' cuando el uso esta bajo un if);   b) alias a paquetes inexistentes ('libs.x'
         -> modulo real de la misma wheel);   c) __init__.py que importan modulos inexistentes;
      d) APIs eliminadas de las dependencias (numpy.source...);   e) firmas: llamadas del codigo del modelo a las
         clases exportadas contra la firma real (AST).
      Resultado por libreria: OK | PARCHEABLE | BLOQUEADO (BLOQUEADO = logica ausente que el modelo SI usa).
      Salida: bank_compat_report.json (viaja en el paquete) y texto legible.
  * RUNTIME (en el paquete): instalar() registra, dirigido por ese reporte, stubs que FALLAN al usarse (nunca
      devuelven datos vacios), paquetes perezosos, alias de modulos movidos, shims y adaptadores de firma; y
      traducir_excepcion()/registrar_faltante() muestran en terminal, log del job, BNX_FALTANTES.json y
      REPORTE_DEMO.json QUE falta, DONDE cargarlo y los PASOS.
"""
import ast
import hashlib
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import io
import json
import os
import re
import sys
import tarfile
import time
import zipfile

REPORTE_NOMBRE = "bank_compat_report.json"
FALTANTES_NOMBRE = "BNX_FALTANTES.json"
OK, PARCHEABLE, BLOQUEADO = "OK", "PARCHEABLE", "BLOQUEADO"
_ORDEN = {OK: 0, PARCHEABLE: 1, BLOQUEADO: 2}

# Fachada mex_lib_cs: (nombre exportado, modulo de origen, paquete pip). Misma tabla que la fachada generada.
FACHADA_EXPORTS = (
    ("Extract", "lib_extract", "mex-libextract"),
    ("GroupBy", "lib_group_by", "mex-libgroupby"),
    ("GeneratePivot", "lib_generate_pivot", "mex-libgeneratepivot"),
    ("GenerateRatios", "lib_generate_ratios", "mex-libgenerateratios"),
    ("ColumnsToVector", "lib_columns2_vector", "mex-libcolumns2vector"),
    ("FeaturesVectorAssembler", "lib_vector_assembler", "mex-libvectorassembler"),
    ("MissingTreatment", "lib_missing_treatment", "mex-libmissingtreatment"),
    ("FeatureEngineering", "lib_feature_engineering", "mex-libfeatureengineering"),
    ("WeeklyTFrom", "toolbox.weeks", "toolbox (modulo de PYTHONPATH / bank_pkg)"),
)

# APIs eliminadas de dependencias (extensible): (paquete, nombre, version en que se elimino, motivo).
APIS_ELIMINADAS = (
    ("numpy", "source", "2.0", "numpy.source se elimino en numpy 2"),
    ("numpy", "float", "1.24", "np.float se elimino en numpy 1.24"),
    ("numpy", "int", "1.24", "np.int se elimino en numpy 1.24"),
    ("numpy", "bool", "1.24", "np.bool se elimino en numpy 1.24"),
    ("numpy", "object", "1.24", "np.object se elimino en numpy 1.24"),
    ("numpy", "str", "1.24", "np.str se elimino en numpy 1.24"),
    ("numpy", "complex", "1.24", "np.complex se elimino en numpy 1.24"),
    ("numpy", "asscalar", "1.23", "np.asscalar se elimino en numpy 1.23"),
    ("numpy", "float_", "2.0", "np.float_ se elimino en numpy 2"),
    ("numpy", "product", "2.0", "np.product se elimino en numpy 2"),
    ("numpy", "cumproduct", "2.0", "np.cumproduct se elimino en numpy 2"),
    ("numpy", "sometrue", "2.0", "np.sometrue se elimino en numpy 2"),
    ("numpy", "alltrue", "2.0", "np.alltrue se elimino en numpy 2"),
    ("numpy", "Inf", "2.0", "np.Inf se elimino en numpy 2"),
    ("numpy", "NaN", "2.0", "np.NaN se elimino en numpy 2"),
    ("pandas", "Panel", "1.0", "pandas.Panel se elimino en pandas 1.0"),
    ("pandas", "Int64Index", "2.0", "pandas.Int64Index se elimino en pandas 2"),
    ("pandas", "Float64Index", "2.0", "pandas.Float64Index se elimino en pandas 2"),
    ("sklearn.externals", "joblib", "0.23", "sklearn.externals.joblib se elimino (usar 'import joblib')"),
)

# Parametros obligatorios que el modelo no pasa y que se pueden completar con un valor NEUTRO (lista blanca).
DEFAULTS_FIRMA = {
    "n_threads": (1, "int", "numero de hilos 1"),
    "number_threads": (1, "int", "numero de hilos 1"),
    "source": ("", "str", "fuente vacia (solo importa para fuentes payroll_*)"),
    "mode": ("overwrite", "str", "modo de escritura 'overwrite'"),
}
# 'source' depende del job en ejecucion (no de una clave fija de la config): nunca se toma de la config del modelo.
SIN_CONFIG = ("source",)
SINONIMOS_CONFIG = {"n_threads": ("number_threads", "threads"), "number_threads": ("n_threads", "threads")}

DONDE_CARGARLO = [
    "(1) en el portal BNX, pestana Framework MLOps v2 -> Librerias / Vendor -> Banco: subir el .whl/.tar.gz "
    "completo de {lib}",
    "(2) o en terminal: python preparar_vendor.py --bank-libs <carpeta|zip>",
    "(3) o actualizar el repo privado bnx-banco (wheels/) y git pull",
]
AVISO_REAL = ("Parches BNX sobre librerias del banco: NO validado contra la salida original. "
              "Pide al equipo duenio las librerias completas.")


def _vt(v):
    out = []
    for p in re.split(r"[.\-+]", str(v or "")):
        m = re.match(r"\d+", p)
        if not m:
            break
        out.append(int(m.group(0)))
    return tuple(out)


def _stdlib_top(top):
    nombres = getattr(sys, "stdlib_module_names", None)
    if nombres is not None:
        return top in nombres
    try:
        spec = importlib.util.find_spec(top)
    except (ImportError, ValueError, AttributeError):
        return False
    if spec is None or not getattr(spec, "origin", None):
        return False
    if spec.origin in ("built-in", "frozen"):
        return True
    return "site-packages" not in spec.origin and "dist-packages" not in spec.origin \
        and os.path.realpath(spec.origin).startswith(os.path.realpath(os.path.dirname(os.__file__)))


def _parse(texto, nombre="<src>"):
    try:
        return ast.parse(texto, filename=nombre)
    except (SyntaxError, ValueError, RecursionError):
        return None


def _padres(tree):
    p = {}
    for n in ast.walk(tree):
        for h in ast.iter_child_nodes(n):
            p[h] = n
    return p


# ---------------------------------------------------------------------------
# Carga de librerias (wheel / sdist) sin ejecutar nada
# ---------------------------------------------------------------------------
class Libreria(object):
    def __init__(self, nombre, version, archivo):
        self.nombre, self.version, self.archivo = nombre, version, archivo
        self.mods = {}            # dotted -> {"rel","texto","pkg"}
        self.tops = set()
        self._cache = {}

    def arbol(self, dotted):
        if dotted not in self._cache:
            m = self.mods.get(dotted)
            self._cache[dotted] = _parse(m["texto"], m["rel"]) if m else None
        return self._cache[dotted]


def _nombre_pip(archivo):
    base = os.path.basename(archivo)
    base = re.sub(r"\.(whl|tar\.gz)$", "", base)
    m = re.match(r"^(.+?)-(\d[^-]*)", base)
    nom, ver = (m.group(1), m.group(2)) if m else (base, "")
    return nom.replace("_", "-"), ver


def _dotted(rel):
    rel = rel.replace(os.sep, "/")
    if not rel.endswith(".py"):
        return None, False
    p = rel[:-3].split("/")
    if p[-1] == "__init__":
        return ".".join(p[:-1]), True
    return ".".join(p), False


def cargar_libreria(ruta):
    """Lee una wheel o sdist del banco. Devuelve Libreria o None."""
    nombre, version = _nombre_pip(ruta)
    lib = Libreria(nombre, version, os.path.basename(ruta))
    archivos = {}
    try:
        if ruta.endswith(".whl"):
            with zipfile.ZipFile(ruta) as zf:
                for n in zf.namelist():
                    if ".dist-info/" in n or ".data/" in n:
                        if n.endswith("METADATA"):
                            txt = zf.read(n).decode("utf-8", "replace")
                            mn = re.search(r"^Name: (.+)$", txt, re.M)
                            mv = re.search(r"^Version: (.+)$", txt, re.M)
                            if mn:
                                lib.nombre = mn.group(1).strip().replace("_", "-")
                            if mv:
                                lib.version = mv.group(1).strip()
                        continue
                    if n.endswith(".py"):
                        archivos[n] = zf.read(n)
        else:
            with tarfile.open(ruta, "r:gz") as tf:
                for m in tf.getmembers():
                    if not m.isfile() or "/" not in m.name:
                        continue
                    rel = m.name.split("/", 1)[1]
                    if rel.endswith(".py") and rel not in ("setup.py",) and ".egg-info" not in rel \
                            and "/" in rel:
                        archivos[rel] = tf.extractfile(m).read()
    except (OSError, zipfile.BadZipFile, tarfile.TarError):
        return None
    for rel, data in archivos.items():
        d, pkg = _dotted(rel)
        if not d:
            continue
        lib.mods[d] = {"rel": rel, "texto": data.decode("utf-8", "replace"), "pkg": pkg}
        lib.tops.add(d.split(".")[0])
    return lib


def cargar_librerias(dirs):
    """Todas las wheels/sdist de las carpetas (wheel gana sobre sdist del mismo nombre)."""
    vistos, libs = {}, []
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith((".whl", ".tar.gz")):
                continue
            nom = _nombre_pip(f)[0].lower()
            if nom in vistos and not f.endswith(".whl"):
                continue
            lib = cargar_libreria(os.path.join(d, f))
            if lib is None or not lib.mods:
                continue
            # solo librerias del banco (mex-lib*, bnx_bank_pkgcode); las deps open source se ignoran
            if not (nom.startswith("mex") or nom.startswith("bnx-bank")):
                continue
            if nom in vistos:
                libs[vistos[nom]] = lib
            else:
                vistos[nom] = len(libs)
                libs.append(lib)
    return libs


# ---------------------------------------------------------------------------
# Utilidades de AST
# ---------------------------------------------------------------------------
def _defs_modulo(tree):
    out = set()
    if tree is None:
        return out
    for n in tree.body:
        if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            out.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out.add(t.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                out.add((a.asname or a.name).split(".")[0])
    return out


def _funcion_de(nodo, padres):
    """'Clase.metodo' o 'funcion' que contiene el nodo ('<modulo>' si esta a nivel de modulo)."""
    partes = []
    n = padres.get(nodo)
    while n is not None:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            partes.append(n.name)
        n = padres.get(n)
    return ".".join(reversed(partes)) or "<modulo>"


def _simbolo_tope(nodo, padres):
    """Nombre de la clase/funcion de NIVEL MODULO que contiene el nodo (o None)."""
    tope = None
    n = padres.get(nodo)
    while n is not None:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and isinstance(
                padres.get(n), ast.Module):
            tope = n.name
        n = padres.get(n)
    return tope


def _lista_const(nodo, tree):
    """Conjunto de str de una lista/tupla/set literal, o de un atributo/nombre que la contenga (clase o modulo)."""
    if isinstance(nodo, (ast.List, ast.Tuple, ast.Set)):
        s = set()
        for e in nodo.elts:
            if isinstance(e, ast.Constant) and isinstance(e.value, str):
                s.add(e.value)
            else:
                return None
        return s
    nombre = nodo.attr if isinstance(nodo, ast.Attribute) else (nodo.id if isinstance(nodo, ast.Name) else None)
    if nombre is None or tree is None:
        return None
    union, hallado = set(), False
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == nombre for t in n.targets):
            s = _lista_const(n.value, None)
            if s is not None:
                union |= s
                hallado = True
    return union if hallado else None


def _literales_test(test, tree):
    """Fuentes (str) que habilitan la rama 'body' de un if, o None si no se puede saber."""
    if isinstance(test, ast.BoolOp):
        partes = [_literales_test(v, tree) for v in test.values]
        buenas = [p for p in partes if p is not None]
        if isinstance(test.op, ast.Or):
            return set().union(*buenas) if buenas and len(buenas) == len(partes) else None
        return set().union(*buenas) if buenas else None
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        op, izq, der = test.ops[0], test.left, test.comparators[0]
        if isinstance(op, ast.Eq):
            for lado in (izq, der):
                if isinstance(lado, ast.Constant) and isinstance(lado.value, str):
                    return {lado.value}
        elif isinstance(op, ast.In):
            return _lista_const(der, tree)
        return None
    return None


def _condicion_nodo(nodo, padres, tree):
    """Fuentes que habilitan la ejecucion de `nodo` (If mas interno con literales, solo si esta en su 'body')."""
    hijo, n = nodo, padres.get(nodo)
    while n is not None:
        if isinstance(n, ast.If) and hijo in n.body:
            s = _literales_test(n.test, tree)
            if s:
                return s
        hijo, n = n, padres.get(n)
    return None


def _txt_cond(literales):
    return "solo si la fuente es " + " o ".join(sorted(literales)) if literales else ""


def _es_local(nodo, nombre, padres):
    """True si `nombre` es un parametro/variable local de alguna funcion que contiene al nodo (no el import global)."""
    n = padres.get(nodo)
    while n is not None:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = n.args
            nombres = [x.arg for x in list(getattr(a, "posonlyargs", [])) + list(a.args) + list(a.kwonlyargs)]
            nombres += [x.arg for x in (a.vararg, a.kwarg) if x is not None]
            if nombre in nombres:
                return True
            for m in ast.walk(n):
                if isinstance(m, ast.Name) and m.id == nombre and isinstance(m.ctx, ast.Store):
                    return True
        n = padres.get(n)
    return False


def _usos_nombres(tree, nombres, padres):
    """Nodos Name(Load) de `nombres` (globales del modulo, no locales de una funcion)."""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and n.id in nombres and isinstance(n.ctx, ast.Load) \
                and not _es_local(n, n.id, padres):
            out.append(n)
    return out


# ---------------------------------------------------------------------------
# Condicion de uso (propaga por los simbolos de la libreria)
# ---------------------------------------------------------------------------
def _metodo_de(nodo, padres):
    """Nombre del metodo (def dentro de una clase) que contiene el nodo, o None."""
    n = padres.get(nodo)
    while n is not None:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and isinstance(padres.get(n), ast.ClassDef):
            return n.name
        n = padres.get(n)
    return None


def _referencias(lib, dotted, u, padres, vistos):
    """Referencias (dotted2, nodo) al metodo o al simbolo de nivel modulo que contiene el nodo `u`.
    Primero por metodo (obj.metodo), si no hay llamadas conocidas, por la clase/funcion de nivel modulo."""
    metodo = _metodo_de(u, padres)
    if metodo and ("m", dotted, metodo) not in vistos:
        vistos.add(("m", dotted, metodo))
        refs = []
        for d2 in lib.mods:
            t2 = lib.arbol(d2)
            if t2 is None:
                continue
            for r in ast.walk(t2):
                if isinstance(r, ast.Attribute) and r.attr == metodo and isinstance(r.ctx, ast.Load):
                    refs.append((d2, r))
        if refs:
            return refs, True
    simbolo = _simbolo_tope(u, padres)
    if simbolo is None:
        return [], False
    if ("s", dotted, simbolo) in vistos:
        return [], True
    vistos.add(("s", dotted, simbolo))
    refs = []
    for d2 in lib.mods:
        t2 = lib.arbol(d2)
        if t2 is None or d2 == dotted:
            continue
        for r in ast.walk(t2):
            if isinstance(r, ast.Name) and r.id == simbolo and isinstance(r.ctx, ast.Load):
                refs.append((d2, r))
    return refs, bool(refs)


def _condicion_uso(lib, dotted, nodos_uso, profundidad=5, _vistos=None):
    """({fuentes}, incondicional:bool, sitios) para los nodos de uso dentro de lib.mods[dotted]. Si el uso no esta
    bajo un if con literales, se sigue a quien llama al metodo (o usa la clase) dentro de la libreria."""
    tree = lib.arbol(dotted)
    padres = _padres(tree) if tree is not None else {}
    literales, incond, sitios = set(), False, []
    vistos = _vistos if _vistos is not None else set()
    for u in nodos_uso:
        cond = _condicion_nodo(u, padres, tree)
        sitios.append({"archivo": lib.mods[dotted]["rel"], "linea": getattr(u, "lineno", 0),
                       "funcion": _funcion_de(u, padres), "condicion": _txt_cond(cond)})
        if cond:
            literales |= cond
            continue
        if profundidad <= 0:
            incond = True
            continue
        refs, hay = _referencias(lib, dotted, u, padres, vistos)
        if not refs:
            incond = incond or not hay
            if not hay and _simbolo_tope(u, padres) is not None:
                incond = True          # sin quien lo llame dentro de la libreria: entrada publica
            continue
        por_mod = {}
        for d2, r in refs:
            por_mod.setdefault(d2, []).append(r)
        for d2, rs in por_mod.items():
            l2, i2, _s2 = _condicion_uso(lib, d2, rs, profundidad - 1, vistos)
            literales |= l2
            incond = incond or i2
        if literales and not sitios[-1]["condicion"]:
            sitios[-1]["condicion"] = _txt_cond(literales)
    return literales, incond, sitios


# ---------------------------------------------------------------------------
# Imports de la propia libreria
# ---------------------------------------------------------------------------
def _destinos_import(nodo, dotted, es_pkg):
    """[(dotted_destino, [nombres importados], relativo)] de un Import/ImportFrom."""
    out = []
    if isinstance(nodo, ast.Import):
        for a in nodo.names:
            out.append((a.name, [], False))
    elif isinstance(nodo, ast.ImportFrom):
        if nodo.level:
            base = dotted.split(".") if es_pkg else dotted.split(".")[:-1]
            if nodo.level - 1 > len(base):
                return out
            base = base[:len(base) - (nodo.level - 1)]
            if nodo.module:
                base = base + nodo.module.split(".")
            elif True:
                return out          # 'from . import x': ambiguo (submodulo o atributo); no se evalua
            out.append((".".join(base), [a.name for a in nodo.names], True))
        elif nodo.module:
            out.append((nodo.module, [a.name for a in nodo.names], False))
    return out


def _existe(lib, d):
    return d in lib.mods


def _buscar_movido(libs, lib, faltante, nombres):
    """Modulo con el mismo nombre base que define todos los `nombres` (misma wheel primero)."""
    base = faltante.rsplit(".", 1)[-1]
    cands = []
    for l2 in [lib] + [x for x in libs if x is not lib]:
        for d, m in l2.mods.items():
            if d.rsplit(".", 1)[-1] != base or d == faltante:
                continue
            defs = _defs_modulo(l2.arbol(d))
            if all(n in defs for n in nombres):
                cands.append((l2, d))
        if cands:
            break
    if len(cands) == 1:
        return cands[0]
    return None


def _analizar_imports(libs, lib, tokens_cfg, hay_cfg, usada):
    """Hallazgos de imports rotos (a, b) y __init__ rotos (c) de una libreria."""
    hall = []
    todos_tops = set()
    for l2 in libs:
        todos_tops |= l2.tops
    for dotted in sorted(lib.mods):
        info = lib.mods[dotted]
        tree = lib.arbol(dotted)
        if tree is None or dotted.rsplit(".", 1)[-1] == "__main__":
            continue          # __main__ no se importa nunca: es un script de la libreria
        padres = _padres(tree)
        es_init = info["rel"].endswith("__init__.py")
        for nodo in ast.walk(tree):
            if not isinstance(nodo, (ast.Import, ast.ImportFrom)):
                continue
            for destino, nombres, rel in _destinos_import(nodo, dotted, info["pkg"]):
                top = destino.split(".")[0]
                if destino in lib.mods:
                    continue
                if not rel and top not in lib.tops:
                    # (b) alias a un paquete inexistente que coincide por nombre con un modulo de la wheel
                    partes = destino.split(".")
                    if top in todos_tops or _stdlib_top(top) or len(partes) < 2:
                        continue
                    try:
                        if importlib.util.find_spec(top) is not None:
                            continue
                    except (ImportError, ValueError, AttributeError):
                        pass
                    base = partes[-1]
                    cands = [d for d, m in lib.mods.items() if d.rsplit(".", 1)[-1] == base and not m["pkg"]
                             and all(n in _defs_modulo(lib.arbol(d)) for n in nombres)]
                    if len(cands) == 1:
                        hall.append({"tipo": "alias_inexistente", "modulo": destino, "destino": cands[0],
                                     "nombres": nombres, "archivo": info["rel"], "linea": nodo.lineno,
                                     "funcion": _funcion_de(nodo, padres), "init": es_init})
                    continue
                if top not in lib.tops and not rel:
                    continue
                # modulo de la propia libreria que NO existe
                mv = _buscar_movido(libs, lib, destino, nombres) if (nombres and not es_init) else None
                loc = [n for n in ([a.asname or a.name for a in nodo.names] if isinstance(nodo, ast.ImportFrom)
                                   else [destino.split(".")[0]])]
                h = {"modulo": destino, "nombres": nombres, "archivo": info["rel"], "linea": nodo.lineno,
                     "funcion": _funcion_de(nodo, padres), "init": es_init, "dotted_origen": dotted}
                if mv is not None:
                    h.update({"tipo": "modulo_movido", "destino": mv[1], "destino_lib": mv[0].nombre})
                    hall.append(h)
                    continue
                if es_init:
                    h["tipo"] = "init_roto"
                    hall.append(h)
                    continue
                usos = _usos_nombres(tree, set(loc), padres) if loc else []
                usos = [u for u in usos if not isinstance(padres.get(u), (ast.Import, ast.ImportFrom))]
                lit, incond, sitios = _condicion_uso(lib, dotted, usos)
                h.update({"tipo": "submodulo_faltante", "fuentes": sorted(lit), "incondicional": bool(incond or not usos),
                          "sitios": sitios})
                hall.append(h)
    return hall


# ---------------------------------------------------------------------------
# (d) APIs eliminadas
# ---------------------------------------------------------------------------
def _analizar_apis(lib, versiones):
    hall = []
    tabla = {}
    for pq, nom, ver, motivo in APIS_ELIMINADAS:
        tabla.setdefault(pq, {})[nom] = (ver, motivo)
    for dotted in sorted(lib.mods):
        tree = lib.arbol(dotted)
        if tree is None:
            continue
        padres = _padres(tree)
        alias = {}
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    if a.name in tabla:
                        alias[a.asname or a.name] = a.name
            elif isinstance(n, ast.ImportFrom) and not n.level and n.module:
                for a in n.names:
                    full = n.module
                    if full in tabla and a.name in tabla[full]:
                        usos = [u for u in _usos_nombres(tree, {a.asname or a.name}, padres)]
                        hall.append(_hall_api(lib, dotted, n, full, a.name, tabla[full][a.name], bool(usos),
                                              versiones, padres))
                    elif (full + "." + a.name) in tabla:
                        alias[a.asname or a.name] = full + "." + a.name
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in alias:
                pq = alias[n.value.id]
                if n.attr in tabla.get(pq, {}):
                    hall.append(_hall_api(lib, dotted, n, pq, n.attr, tabla[pq][n.attr], True, versiones, padres))
    return hall


def _hall_api(lib, dotted, nodo, pq, nom, datos, usado, versiones, padres):
    ver, motivo = datos
    base = pq.split(".")[0]
    vdep = versiones.get(base)
    aplica = None if not vdep else (_vt(vdep) >= _vt(ver))
    return {"tipo": "api_eliminada", "modulo": pq, "nombre": nom, "desde": ver, "motivo": motivo,
            "usada": bool(usado), "aplica_en_target": aplica, "version_target": vdep or "",
            "archivo": lib.mods[dotted]["rel"], "linea": getattr(nodo, "lineno", 0),
            "funcion": _funcion_de(nodo, padres)}


# ---------------------------------------------------------------------------
# (e) firmas
# ---------------------------------------------------------------------------
def _firma_de(fn):
    a = fn.args
    pos = [x.arg for x in getattr(a, "posonlyargs", [])] + [x.arg for x in a.args]
    ndef = len(a.defaults)
    nobl = len(pos) - ndef
    oblig = pos[:nobl]
    kwonly = [x.arg for x in a.kwonlyargs]
    kw_oblig = [x.arg for x, d in zip(a.kwonlyargs, a.kw_defaults) if d is None]
    return {"pos": pos, "oblig": oblig, "kwonly": kwonly, "kw_oblig": kw_oblig,
            "vararg": a.vararg is not None, "varkw": a.kwarg is not None}


def _buscar_clase(lib, nombre):
    """(dotted, ClassDef) de la clase `nombre` en la libreria (la de modulo con nombre afin primero)."""
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", nombre).lower()
    cands = []
    for d in lib.mods:
        t = lib.arbol(d)
        if t is None:
            continue
        for n in t.body:
            if isinstance(n, ast.ClassDef) and n.name == nombre:
                cands.append((0 if d.rsplit(".", 1)[-1] == snake else 1, d, n))
    cands.sort(key=lambda x: (x[0], x[1]))
    return (cands[0][1], cands[0][2]) if cands else (None, None)


def _firma_clase(cn):
    for n in cn.body:
        if isinstance(n, ast.FunctionDef) and n.name == "__init__":
            f = _firma_de(n)
            f["pos"] = f["pos"][1:]
            f["oblig"] = f["oblig"][1:]
            return f
    return None


def _firma_metodo(cn, nombre):
    for n in cn.body:
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            f = _firma_de(n)
            f["pos"], f["oblig"] = f["pos"][1:], f["oblig"][1:]
            return f
    return None


def _evaluar_llamada(firma, call):
    """(faltan, desconocidos) o None si la llamada usa *args/**kwargs (no se puede saber)."""
    if any(isinstance(a, ast.Starred) for a in call.args) or any(k.arg is None for k in call.keywords):
        return None
    npos = len(call.args)
    ligados = set(firma["pos"][:npos])
    kws = [k.arg for k in call.keywords]
    desconocidos = [k for k in kws if k not in firma["pos"] and k not in firma["kwonly"]]
    if firma["varkw"]:
        desconocidos = []
    ligados |= set(k for k in kws if k in firma["pos"] or k in firma["kwonly"])
    faltan = [p for p in firma["oblig"] if p not in ligados] + [p for p in firma["kw_oblig"] if p not in ligados]
    return faltan, desconocidos


def _llamadas_modelo(codigos, extra_tops=()):
    """Llamadas del modelo a nombres importados de mex_lib_cs / lib_*: [{simbolo, call, archivo, linea, funcion,
    metodos:[(metodo, call, ...)]}] y {atributo: [(archivo, linea, funcion)]} de llamadas a metodos."""
    llamadas, por_attr = [], {}
    fach = set(n for n, _m, _p in FACHADA_EXPORTS)
    for archivo, texto in codigos.items():
        tree = _parse(texto, archivo)
        if tree is None:
            continue
        padres = _padres(tree)
        nombres = {}       # local -> (nombre exportado, modulo de origen)
        mods = {}          # alias de modulo -> modulo (mex_lib_cs / lib_x)
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and not n.level and n.module:
                top = n.module.split(".")[0]
                if top == "mex_lib_cs" or top.startswith("lib_") or top in extra_tops:
                    for a in n.names:
                        nombres[a.asname or a.name] = (a.name, n.module)
            elif isinstance(n, ast.Import):
                for a in n.names:
                    top = a.name.split(".")[0]
                    if top == "mex_lib_cs" or top.startswith("lib_") or top in extra_tops:
                        mods[a.asname or top] = a.name
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                f = n.func
                sim, origen = None, None
                if isinstance(f, ast.Name) and f.id in nombres:
                    sim, origen = nombres[f.id]
                elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in mods:
                    sim, origen = f.attr, mods[f.value.id]
                if sim:
                    reg = {"simbolo": sim, "origen": origen, "call": n, "archivo": archivo, "linea": n.lineno,
                           "funcion": _funcion_de(n, padres), "metodos": []}
                    # x = Clase(...); x.metodo(...) en el mismo ambito
                    pa = padres.get(n)
                    if isinstance(pa, ast.Assign) and len(pa.targets) == 1 and isinstance(pa.targets[0], ast.Name):
                        var = pa.targets[0].id
                        ambito = padres.get(pa)
                        while ambito is not None and not isinstance(ambito, (ast.FunctionDef, ast.Module)):
                            ambito = padres.get(ambito)
                        for m in ast.walk(ambito if ambito is not None else tree):
                            if isinstance(m, ast.Call) and isinstance(m.func, ast.Attribute) \
                                    and isinstance(m.func.value, ast.Name) and m.func.value.id == var:
                                reg["metodos"].append((m.func.attr, m))
                    llamadas.append(reg)
                if isinstance(f, ast.Attribute):
                    por_attr.setdefault(f.attr, []).append((archivo, n.lineno, _funcion_de(n, padres)))
    return llamadas, por_attr


def _buscar_valor_config(cfgs, clave):
    """(archivo, valor) de la primera clave `clave` en los JSON del modelo (busqueda recursiva)."""
    def rec(o):
        if isinstance(o, dict):
            if clave in o and not isinstance(o[clave], (dict, list)):
                return o[clave]
            for v in o.values():
                r = rec(v)
                if r is not None:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = rec(v)
                if r is not None:
                    return r
        return None
    for archivo in sorted(cfgs):
        try:
            d = json.loads(cfgs[archivo])
        except ValueError:
            continue
        v = rec(d)
        if v is not None:
            return archivo, v
    return None, None


def _analizar_firmas(libs, lib_por_nombre, codigos, cfgs):
    """Hallazgos de firma por libreria: {pip: [hallazgo]}."""
    out = {}
    tops = set()
    for l in libs:
        tops |= l.tops
    llamadas, _pa = _llamadas_modelo(codigos, tops)
    exp = dict((n, (m, p)) for n, m, p in FACHADA_EXPORTS)
    for reg in llamadas:
        sim = reg["simbolo"]
        if reg["origen"].split(".")[0] == "mex_lib_cs":
            if sim not in exp:
                continue
            modulo, pip = exp[sim]
        else:
            modulo = reg["origen"]
        lib = next((l for l in libs if modulo.split(".")[0] in l.tops), None)
        if lib is None:
            continue
        d, cn = _buscar_clase(lib, sim)
        if cn is None:
            continue
        casos = [(sim + ".__init__", _firma_clase(cn), reg["call"], sim)]
        for met, mc in reg["metodos"]:
            fm = _firma_metodo(cn, met)
            if fm is not None:
                casos.append((sim + "." + met, fm, mc, met))
        for titulo, firma, call, _x in casos:
            if firma is None:
                continue
            ev = _evaluar_llamada(firma, call)
            if ev is None:
                continue
            faltan, desc = ev
            if not faltan and not desc:
                continue
            ad, bloq = [], []
            for p in faltan:
                arch_cfg, val = None, None
                for clave in (() if p in SIN_CONFIG else (p,) + SINONIMOS_CONFIG.get(p, ())):
                    arch_cfg, val = _buscar_valor_config(cfgs, clave)
                    if val is not None:
                        break
                if val is not None:
                    ad.append({"param": p, "fuente": "config", "clave": clave, "archivo_config": arch_cfg,
                               "valor_ejemplo": val, "default": DEFAULTS_FIRMA.get(p, (None,))[0],
                               "tipo": DEFAULTS_FIRMA.get(p, (None, "str"))[1]})
                elif p in DEFAULTS_FIRMA:
                    dv, tipo, desc_ = DEFAULTS_FIRMA[p]
                    ad.append({"param": p, "fuente": "default", "default": dv, "tipo": tipo, "nota": desc_})
                else:
                    bloq.append(p)
            h = {"tipo": "firma", "clase": sim, "metodo": titulo, "libreria": lib.nombre, "modulo": modulo,
                 "modulo_def": d,
                 "faltan": faltan, "desconocidos": desc, "adaptaciones": ad, "sin_adaptar": bloq,
                 "archivo_modelo": reg["archivo"], "linea_modelo": call.lineno,
                 "funcion_modelo": reg["funcion"], "archivo": lib.mods[d]["rel"], "linea": cn.lineno,
                 "funcion": titulo, "estado": BLOQUEADO if (bloq or desc) else PARCHEABLE}
            out.setdefault(lib.nombre, []).append(h)
    return out


# ---------------------------------------------------------------------------
# Orquestacion del analisis
# ---------------------------------------------------------------------------
def _tokens_config(cfgs):
    """Claves y valores str de los JSON de config del modelo (que fuentes/variantes usa de verdad)."""
    tok = set()

    def rec(o):
        if isinstance(o, dict):
            for k, v in o.items():
                tok.add(str(k))
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)
        elif isinstance(o, str):
            tok.add(o)
    for t in cfgs.values():
        try:
            rec(json.loads(t))
        except ValueError:
            continue
    return tok


def _libs_usadas(codigos, libs):
    """Nombres pip de las librerias que el codigo del modelo importa (directo o via mex_lib_cs)."""
    usadas = set()
    por_nombre = dict((n, p) for n, _m, p in FACHADA_EXPORTS)
    por_mod = dict((m.split(".")[0], p) for _n, m, p in FACHADA_EXPORTS)
    for archivo, texto in codigos.items():
        tree = _parse(texto, archivo)
        if tree is None:
            continue
        for n in ast.walk(tree):
            mods, nombres = [], []
            if isinstance(n, ast.ImportFrom) and not n.level and n.module:
                mods, nombres = [n.module], [a.name for a in n.names]
            elif isinstance(n, ast.Import):
                mods = [a.name for a in n.names]
            for m in mods:
                top = m.split(".")[0]
                if top == "mex_lib_cs":
                    for nm in nombres or ():
                        if nm in por_nombre:
                            usadas.add(por_nombre[nm].split(" ")[0])
                    if not nombres:
                        usadas |= set(p.split(" ")[0] for p in por_nombre.values())
                for l in libs:
                    if top in l.tops:
                        usadas.add(l.nombre)
                if top in por_mod:
                    usadas.add(por_mod[top].split(" ")[0])
    return usadas


def _buscar_def(lib, nombre):
    for d in sorted(lib.mods):
        t = lib.arbol(d)
        if t is None:
            continue
        for n in t.body:
            if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name == nombre:
                return d
    return None


def _exports_init(lib, dotted):
    """{nombre: modulo_dotted|None} de lo que exporta un __init__.py (None: no se encontro en la wheel)."""
    tree = lib.arbol(dotted)
    out = {}
    if tree is None:
        return out
    for n in tree.body:
        if isinstance(n, ast.ImportFrom):
            for destino, nombres, _r in _destinos_import(n, dotted, True):
                for a in n.names:
                    loc = a.asname or a.name
                    if destino in lib.mods:
                        out[loc] = destino
                    else:
                        out[loc] = _buscar_def(lib, a.name)
    return out


def _sha1(txt):
    return hashlib.sha1(txt.encode("utf-8")).hexdigest()


def _ruta_subpaquete(lib, modulo):
    return "/".join(modulo.split(".")) + "/"


def analizar(dirs_wheels, codigos_modelo, cfgs_modelo, versiones=None, extras_libs=None):
    """Analiza TODAS las librerias del banco de `dirs_wheels` contra el codigo/config del modelo.
    codigos_modelo: {ruta: texto .py}; cfgs_modelo: {ruta: texto .json}; versiones: {'numpy': '1.26.4', ...}.
    Devuelve el reporte (dict serializable)."""
    versiones = dict(versiones or {})
    libs = cargar_librerias(dirs_wheels)
    codigos = dict((k, v) for k, v in (codigos_modelo or {}).items() if k.endswith(".py"))
    cfgs = dict(cfgs_modelo or {})
    tokens = _tokens_config(cfgs)
    hay_cfg = bool(cfgs)
    usadas = _libs_usadas(codigos, libs)
    _tops_all = set()
    for _l in libs:
        _tops_all |= _l.tops
    llamadas, por_attr = _llamadas_modelo(codigos, _tops_all)
    firmas = _analizar_firmas(libs, dict((l.nombre, l) for l in libs), codigos, cfgs)
    rep_libs, parches = [], {"alias": {}, "stubs": {}, "paquetes_perezosos": {}, "shims": [], "firmas": []}
    contador = [0]

    def nuevo_id():
        contador[0] += 1
        return "H%d" % contador[0]

    exp_lib = {}
    for n, m, p in FACHADA_EXPORTS:
        exp_lib.setdefault(p.split(" ")[0], []).append(n)

    def usos_modelo(lib, funcion):
        met = (funcion or "").split(".")[-1]
        usos = [{"archivo": a, "linea": l, "funcion": f} for a, l, f in por_attr.get(met, [])] if met and \
            not met.startswith("<") and met != "__init__" else []
        if not usos:
            nombres = set(exp_lib.get(lib.nombre, []))
            usos = [{"archivo": r["archivo"], "linea": r["linea"], "funcion": r["funcion"]}
                    for r in llamadas if r["simbolo"] in nombres or r["origen"].split(".")[0] in lib.tops]
        return usos[:5]

    for lib in libs:
        es_usada = lib.nombre in usadas
        base_h = _analizar_imports(libs, lib, tokens, hay_cfg, es_usada)
        hall, vistos_mod = [], {}
        iniciales = {}
        for h in base_h:
            t = h["tipo"]
            if t in ("modulo_movido", "alias_inexistente"):
                if h["modulo"] in parches["alias"]:
                    continue
                hid = nuevo_id()
                destino = h["destino"]
                parches["alias"][h["modulo"]] = destino
                hall.append({"id": hid, "tipo": t, "estado": PARCHEABLE, "modulo": h["modulo"], "destino": destino,
                             "archivo": h["archivo"], "linea": h["linea"], "funcion": h["funcion"],
                             "por_que": ("el modulo %s no esta en el paquete del banco; existe como %s: se usa por alias "
                                         "(codigo del banco, no validado)" % (h["modulo"], destino)
                                         if t == "modulo_movido" else
                                         "importa el paquete inexistente '%s'; los modulos reales estan en %s: se "
                                         "resuelve por alias dentro de esta libreria" % (h["modulo"].split(".")[0], destino)),
                             "parche": "alias %s -> %s" % (h["modulo"], destino)})
            elif t == "init_roto":
                key = h["dotted_origen"]
                iniciales.setdefault(key, []).append(h)
            else:
                m = vistos_mod.setdefault(h["modulo"], {"h": h, "nombres": set(), "sitios": [], "fuentes": set(),
                                                         "incond": False})
                m["nombres"] |= set(h["nombres"])
                m["sitios"] += h["sitios"]
                m["fuentes"] |= set(h["fuentes"])
                m["incond"] = m["incond"] or h["incondicional"]
        for key, hs in sorted(iniciales.items()):
            ex = _exports_init(lib, key)
            rel_ini = lib.mods[key]["rel"]
            sinres = sorted(n for n, d in ex.items() if d is None)
            facade = [n for n in exp_lib.get(lib.nombre, [])]
            falta_fachada = [n for n in facade if n in ex and ex[n] is None]
            est = BLOQUEADO if (falta_fachada and es_usada) else PARCHEABLE
            hid = nuevo_id()
            faltan = sorted(set(x["modulo"] for x in hs))
            parches["paquetes_perezosos"][key] = {"exports": ex, "sha1": _sha1(lib.mods[key]["texto"]),
                                                  "hallazgo": hid}
            hall.append({"id": hid, "tipo": "init_roto", "estado": est, "modulo": key, "archivo": rel_ini,
                         "linea": hs[0]["linea"], "funcion": "<modulo>", "faltan": faltan, "sin_resolver": sinres,
                         "por_que": "el __init__.py de %s importa %d modulo(s) que no existen en el paquete del banco "
                                    "(%s); se carga como paquete perezoso sin ejecutar ese __init__"
                                    % (key, len(faltan), ", ".join(m.rsplit(".", 1)[-1] for m in faltan[:4])
                                       + ("..." if len(faltan) > 4 else "")),
                         "parche": "paquete perezoso %s (exports resueltos por nombre en la wheel)" % key})
        for modulo, m in sorted(vistos_mod.items()):
            h = m["h"]
            fuentes = sorted(m["fuentes"])
            if fuentes and hay_cfg:
                usa = sorted(set(fuentes) & tokens)
                est = BLOQUEADO if usa else PARCHEABLE
                cond_txt = _txt_cond(fuentes)
                detalle = ("el modelo configura la fuente %s" % ", ".join(usa)) if usa else \
                    ("ninguna config del modelo usa la fuente %s" % " ni ".join(fuentes))
            elif fuentes:
                est, cond_txt = BLOQUEADO, _txt_cond(fuentes)
                detalle = "no hay settings del modelo en el paquete: no se puede comprobar que fuentes usa"
            elif m["incond"]:
                est, cond_txt = BLOQUEADO, ""
                detalle = "se usa sin condicion en el codigo de la libreria"
            else:
                est, cond_txt, detalle = PARCHEABLE, "", "no se usa"
            if not es_usada and est == BLOQUEADO:
                est = PARCHEABLE
                detalle += " (la libreria no la usa el codigo del modelo)"
            hid = nuevo_id()
            sitio = (m["sitios"] or [{}])[0]
            nombres = sorted(m["nombres"])
            parches["stubs"][modulo] = {"nombres": nombres, "hallazgo": hid}
            hall.append({"id": hid, "tipo": "submodulo_faltante", "estado": est, "modulo": modulo,
                         "componente": nombres[0] if nombres else modulo.rsplit(".", 1)[-1],
                         "nombres": nombres, "subpaquete": _ruta_subpaquete(lib, modulo.rsplit(".", 1)[0]
                                                                              if "." in modulo else modulo),
                         "archivo": sitio.get("archivo") or h["archivo"], "linea": sitio.get("linea") or h["linea"],
                         "import": {"archivo": h["archivo"], "linea": h["linea"]},
                         "funcion": sitio.get("funcion") or h["funcion"], "fuentes": fuentes,
                         "condicion": cond_txt, "detalle": detalle, "incondicional": bool(m["incond"] and not fuentes),
                         "usos_modelo": usos_modelo(lib, sitio.get("funcion") or h["funcion"]),
                         "por_que": "el .tar.gz/.whl del banco no trae el subpaquete %s (importado en %s:%d)"
                                    % (modulo.rsplit(".", 1)[0] if "." in modulo else modulo, h["archivo"], h["linea"]),
                         "parche": "stub que falla claro al usarse (%s)" % (cond_txt or "uso sin condicion")})
        # (d) APIs eliminadas
        for a in _analizar_apis(lib, versiones):
            hid = nuevo_id()
            if a["usada"]:
                est = OK if a["aplica_en_target"] is False else BLOQUEADO
            else:
                est = OK if a["aplica_en_target"] is False else PARCHEABLE
            if est == BLOQUEADO and not es_usada:
                est = PARCHEABLE
            if not a["usada"]:
                parches["shims"].append({"modulo": a["modulo"], "nombre": a["nombre"], "hallazgo": hid})
            a.update({"id": hid, "estado": est, "componente": "%s.%s" % (a["modulo"], a["nombre"]),
                      "por_que": "API eliminada en %s %s: %s%s" % (
                          a["modulo"].split(".")[0], a["desde"], a["motivo"],
                          "" if a["aplica_en_target"] is not False else
                          " (no aplica en el entorno destino: %s %s)" % (a["modulo"].split(".")[0], a["version_target"])),
                      "parche": ("shim de %s.%s (solo se importa, no se llama)" % (a["modulo"], a["nombre"]))
                      if not a["usada"] else "sin parche: el codigo de la libreria la usa"})
            hall.append(a)
        # (e) firmas
        vf = {}
        for f in firmas.get(lib.nombre, []):
            k = (f["clase"], f["metodo"], tuple(f["faltan"]), tuple(f["desconocidos"]))
            if k in vf:
                vf[k].setdefault("otros_sitios", []).append({"archivo": f["archivo_modelo"], "linea": f["linea_modelo"],
                                                             "funcion": f["funcion_modelo"]})
                continue
            vf[k] = f
        for f in vf.values():
            hid = nuevo_id()
            est = f["estado"]
            if est == BLOQUEADO and not es_usada:
                est = PARCHEABLE
            razon = []
            if f["faltan"]:
                razon.append("falta el parametro %s" % ", ".join(f["faltan"]))
            if f["desconocidos"]:
                razon.append("parametro(s) que la libreria no acepta: %s" % ", ".join(f["desconocidos"]))
            f.update({"id": hid, "estado": est, "componente": f["metodo"],
                      "por_que": "firma distinta: %s (%s:%d llama %s)" % ("; ".join(razon), f["archivo_modelo"],
                                                                         f["linea_modelo"], f["metodo"]),
                      "parche": ("; ".join("%s=%s" % (a["param"], ("config:" + a["clave"]) if a["fuente"] == "config"
                                                      else repr(a["default"])) for a in f["adaptaciones"]))
                      if f["adaptaciones"] else "sin parche"})
            if est != BLOQUEADO or f["adaptaciones"]:
                for a in f["adaptaciones"]:
                    parches["firmas"].append({"clase": f["clase"], "metodo": f["metodo"], "param": a["param"],
                                              "fuente": a["fuente"], "clave": a.get("clave"),
                                              "default": a.get("default"), "tipo": a.get("tipo"),
                                              "nota": a.get("nota", ""), "hallazgo": hid,
                                              "libreria": lib.nombre, "modulo": f["modulo"],
                                              "modulo_def": f.get("modulo_def")})
            hall.append(f)
        mejor = OK
        for h in hall:
            if _ORDEN[h["estado"]] > _ORDEN[mejor]:
                mejor = h["estado"]
        rep_libs.append({"libreria": lib.nombre, "version": lib.version, "archivo": lib.archivo,
                         "paquetes": sorted(lib.tops), "usada_por_modelo": es_usada, "estado": mejor,
                         "hallazgos": hall})
    for l in rep_libs:
        for h in l["hallazgos"]:
            h.setdefault("libreria", l["libreria"])
            h.setdefault("version", l["version"])
    return {"version_reporte": 1, "generado": time.strftime("%Y-%m-%d %H:%M:%S"), "entorno": versiones,
            "dependencias_terceros": _deps_terceros(libs),
            "modelo": {"archivos_py": len(codigos), "archivos_config": len(cfgs), "con_config": hay_cfg},
            "librerias": rep_libs, "parches": parches,
            "resumen": dict((e, sum(1 for l in rep_libs if l["estado"] == e)) for e in (OK, PARCHEABLE, BLOQUEADO))}


def _deps_terceros(libs):
    """Paquetes de terceros (no stdlib, no del banco) que importan las librerias del banco (para el vendor)."""
    propios = set()
    for l in libs:
        propios |= l.tops
    out = set()
    for l in libs:
        if not l.nombre.startswith("mex"):
            continue
        for d in l.mods:
            if d.rsplit(".", 1)[-1] in ("__main__", "install", "develop_mode"):
                continue
            t = l.arbol(d)
            if t is None:
                continue
            for n in ast.walk(t):
                mods = []
                if isinstance(n, ast.Import):
                    mods = [a.name for a in n.names]
                elif isinstance(n, ast.ImportFrom) and not n.level and n.module:
                    mods = [n.module]
                for m in mods:
                    top = m.split(".")[0]
                    if top not in propios and not _stdlib_top(top) and top not in ("libs", "pyspark"):
                        out.add(top)
    return sorted(out)


def reporte_a_json(rep):
    return json.dumps(rep, ensure_ascii=False, indent=1, sort_keys=True, default=str)


def tabla_estados(rep):
    """[{libreria, version, estado, usada, parches, bloqueos, motivos}] para la pantalla / el texto."""
    out = []
    for l in (rep or {}).get("librerias", []):
        hs = l["hallazgos"]
        out.append({"libreria": l["libreria"], "version": l["version"], "estado": l["estado"],
                    "usada": l["usada_por_modelo"],
                    "parches": sum(1 for h in hs if h["estado"] == PARCHEABLE),
                    "bloqueos": sum(1 for h in hs if h["estado"] == BLOQUEADO),
                    "detalle": [{"id": h["id"], "estado": h["estado"], "tipo": h["tipo"],
                                 "que": h.get("componente") or h.get("modulo"), "archivo": h.get("archivo"),
                                 "linea": h.get("linea"), "por_que": h.get("por_que"),
                                 "parche": h.get("parche")} for h in hs if h["estado"] != OK]})
    return out


def resumen_texto(rep):
    """Texto legible: tabla OK/PARCHEABLE/BLOQUEADO por libreria + hallazgos."""
    if not rep:
        return "Compatibilidad de librerias del banco: sin reporte."
    ls = ["Compatibilidad de librerias del banco (analisis estatico, sin ejecutar):"]
    for t in tabla_estados(rep):
        ls.append("  %-11s %-28s %-7s %s" % (t["estado"], t["libreria"], t["version"],
                                           "" if t["usada"] else "(el modelo no la usa)"))
        for d in t["detalle"]:
            ls.append("      - [%s] %s: %s" % (d["estado"], d["que"], d["por_que"]))
    r = rep.get("resumen", {})
    ls.append("  Total: %d OK, %d PARCHEABLE, %d BLOQUEADO." % (r.get(OK, 0), r.get(PARCHEABLE, 0), r.get(BLOQUEADO, 0)))
    if r.get(PARCHEABLE, 0) or r.get(BLOQUEADO, 0):
        ls.append("  Los parches solo se activan en DEMO/SIMULACION (o en real con BNX_BANK_COMPAT=1). " + AVISO_REAL)
    return "\n".join(ls)


# ===========================================================================
# RUNTIME (dentro del paquete generado)
# ===========================================================================
_ESTADO = {"instalado": False, "activo": False, "finder": None, "avisados": set(), "cfg_cache": {}}
_REP_CACHE = {}


def _aqui():
    return os.path.dirname(os.path.abspath(__file__))


def cargar_reporte(ruta=None):
    """bank_compat_report.json (junto a este archivo o en BNX_BANK_COMPAT_REPORT). None si no hay."""
    cand = [ruta, os.environ.get("BNX_BANK_COMPAT_REPORT"), os.path.join(_aqui(), REPORTE_NOMBRE),
            os.path.join(os.getcwd(), REPORTE_NOMBRE)]
    for c in cand:
        if c and os.path.isfile(c):
            try:
                mt = os.path.getmtime(c)
                if c in _REP_CACHE and _REP_CACHE[c][0] == mt:
                    return _REP_CACHE[c][1]
                with io.open(c, "r", encoding="utf-8") as fh:
                    rep = json.load(fh)
                _REP_CACHE[c] = (mt, rep)
                return rep
            except (OSError, ValueError):
                continue
    return None


def modo_demo():
    return os.environ.get("BNX_MODO", "") == "demo" or os.environ.get("BNX_SIMULACION") == "1"


def activo_por_modo():
    """DEMO/SIMULACION: activa por defecto. REAL: solo con BNX_BANK_COMPAT=1. BNX_BANK_COMPAT=0 la apaga siempre."""
    v = os.environ.get("BNX_BANK_COMPAT", "").strip()
    if v == "0":
        return False
    if v == "1":
        return True
    return modo_demo()


def _job():
    return os.environ.get("BNX_JOB_ID") or os.environ.get("JOB_NAME") or os.environ.get("JOB") or "(job)"


def formatear(info, job=None):
    """Mensaje de un faltante (mismo texto en terminal, log, JSON y pantalla)."""
    job = job or info.get("job") or _job()
    n = info.get("necesita") or {}
    lib = info.get("libreria") or "la libreria del banco"
    ver = (" " + info["version"]) if info.get("version") else ""
    if info.get("tipo") == "parcheado":
        return "PARCHEADO: %s (no validado)" % info.get("componente", "")
    donde = [d.format(lib=lib) for d in DONDE_CARGARLO]
    if info.get("tipo") == "dependencia":
        donde = ["(1) agregar la dependencia al vendor del paquete: python preparar_vendor.py --extra "
                 "(o instalarla con pip en el venv del paquete)",
                 "(2) o en el portal BNX, pestana Framework MLOps v2 -> Librerias / Vendor, y volver a generar el paquete"]
    lugar = ""
    if n.get("archivo"):
        lugar = "%s:%s" % (n.get("archivo"), n.get("linea", ""))
    detalle = ", ".join(x for x in (n.get("funcion"), n.get("condicion")) if x)
    ls = ["FALTA %s (modulo %s de la libreria %s%s)" % (info.get("componente", "?"), info.get("modulo", "?"), lib, ver)]
    ls.append("  Lo necesita: %s -> %s%s" % (job, lugar or "(archivo del modelo no identificado)",
                                           (" (%s)" % detalle) if detalle else ""))
    if n.get("archivo_lib"):
        ls[-1] += "  [codigo de la libreria: %s:%s]" % (n["archivo_lib"], n.get("linea_lib", ""))
    ls.append("  Por que: %s" % info.get("por_que", ""))
    ls.append("  Donde cargarlo: " + donde[0])
    for d in donde[1:]:
        ls.append("                  " + d)
    modelo_arch = n.get("archivo") or "su codigo"
    sub = (" (incluyendo %s)" % info["subpaquete"]) if info.get("subpaquete") else ""
    if info.get("tipo") == "dependencia":
        ls.append("  Pasos: 1) agregar %s al vendor del paquete; 2) volver a generar el paquete; 3) bash setup.sh y "
                  "volver a correr %s." % (info.get("modulo", "?"), job))
    else:
        ls.append("  Pasos: 1) pedir al equipo duenio %s completa en la version que usa %s%s; 2) cargarla como arriba; "
                  "3) volver a generar el paquete; 4) bash setup.sh y volver a correr %s." % (lib, modelo_arch, sub, job))
    return "\n".join(ls)


class BNXFaltaComponente(ImportError):
    """Falta un componente de una libreria del banco. str(e) es el mensaje completo en espanol."""

    def __init__(self, info):
        self.info = info
        ImportError.__init__(self, formatear(info))

    def __str__(self):
        return formatear(self.info)


# ---- registro (terminal / log del job / BNX_FALTANTES.json / REPORTE_DEMO.json) ----
def _dir_logs():
    lf = os.environ.get("LOG_FILE_PATH")
    if lf:
        return os.path.dirname(os.path.dirname(os.path.abspath(lf)))
    return os.path.join(os.path.dirname(_aqui()) if os.path.basename(_aqui()) == "src" else _aqui(), "logs")


def ruta_faltantes():
    return os.path.join(os.environ.get("BNX_FALTANTES_DIR") or _dir_logs(), FALTANTES_NOMBRE)


def leer_faltantes(ruta=None):
    try:
        with io.open(ruta or ruta_faltantes(), "r", encoding="utf-8") as fh:
            d = json.load(fh)
        return d.get("faltantes", []) if isinstance(d, dict) else []
    except (OSError, ValueError):
        return []


def _escribir_faltantes(lista, ruta=None):
    ruta = ruta or ruta_faltantes()
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        tmp = ruta + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"version": 1, "faltantes": lista}, ensure_ascii=False, indent=1))
        os.replace(tmp, ruta)
    except OSError:
        pass


def limpiar_faltantes(job=None):
    """Quita los faltantes de `job` (o todos) antes de volver a correrlo."""
    if job is None:
        _escribir_faltantes([])
    else:
        _escribir_faltantes([f for f in leer_faltantes() if f.get("job") != job])


def registrar_faltante(info, job=None, tipo=None, escribir_log=True):
    """Guarda el faltante en BNX_FALTANTES.json y en el log del job. Devuelve el texto (para imprimirlo)."""
    job = job or info.get("job") or _job()
    tipo = tipo or info.get("tipo") or "falta"
    reg = dict(info)
    reg.update({"job": job, "tipo": tipo, "texto": formatear(dict(info, tipo=tipo), job),
                "severidad": "aviso" if tipo == "parcheado" else "error", "ts": time.strftime("%Y-%m-%d %H:%M:%S")})
    lista = [f for f in leer_faltantes() if not (f.get("job") == job and f.get("tipo") == tipo
                                                and f.get("componente") == reg.get("componente")
                                                and f.get("modulo") == reg.get("modulo"))]
    lista.append(reg)
    _escribir_faltantes(lista)
    lf = os.environ.get("LOG_FILE_PATH")
    if escribir_log and lf:
        try:
            with io.open(lf, "a", encoding="utf-8") as fh:
                fh.write(u"[BNX %s] %s\n%s\n" % (reg["ts"], "AVISO" if tipo == "parcheado" else "ERROR", reg["texto"]))
        except OSError:
            pass
    return reg["texto"]


def anexar_a_reporte_demo(ruta_json):
    """Agrega 'faltantes' (los de BNX_FALTANTES.json) a REPORTE_DEMO.json."""
    try:
        with io.open(ruta_json, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        d["faltantes"] = leer_faltantes()
        with io.open(ruta_json, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(d, ensure_ascii=False, indent=1, default=str))
        return True
    except (OSError, ValueError):
        return False


def _rel_modelo(path):
    p = path.replace(os.sep, "/")
    for marca in ("/bank_src/", "/pkgcode/", "/bank_pkg/"):
        i = p.rfind(marca)
        if i >= 0:
            return p[i + len(marca):]
    return os.path.basename(p)


def _es_ruta_ajena(path):
    p = path.replace(os.sep, "/")
    if p == __file__.replace(os.sep, "/") or "site-packages" in p or "dist-packages" in p or "/pyspark/" in p \
            or "importlib" in p or p.startswith("<"):
        return True
    return p.startswith(os.path.dirname(os.__file__).replace(os.sep, "/") + "/") and "site-packages" not in p


def _sitio_modelo():
    """(archivo, linea, funcion) del primer frame del MODELO (no libreria, no stdlib) en la pila."""
    try:
        f = sys._getframe(1)
    except ValueError:
        return None
    while f is not None:
        fn = f.f_code.co_filename
        if not _es_ruta_ajena(fn) and "/lib_" not in fn.replace(os.sep, "/"):
            return {"archivo": _rel_modelo(fn), "linea": f.f_lineno, "funcion": f.f_code.co_name}
        f = f.f_back
    return None


def _version_lib(pip):
    try:
        from importlib import metadata
        return metadata.version(pip)
    except Exception:
        return ""


def info_de_hallazgo(h, rep=None):
    """Dict de mensaje (formatear) a partir de un hallazgo del reporte."""
    uso = (h.get("usos_modelo") or [{}])[0]
    por_que = h.get("por_que", "")
    if h.get("detalle"):
        por_que += " (%s)" % h["detalle"]
    n = {"archivo": uso.get("archivo") or h.get("archivo_modelo"), "linea": uso.get("linea") or h.get("linea_modelo"),
         "funcion": h.get("funcion"), "condicion": h.get("condicion", ""),
         "archivo_lib": h.get("archivo"), "linea_lib": h.get("linea")}
    return {"componente": h.get("componente") or h.get("modulo"), "modulo": h.get("modulo") or h.get("clase"),
            "libreria": h.get("libreria"), "version": h.get("version"), "necesita": n, "por_que": por_que,
            "subpaquete": h.get("subpaquete", ""), "tipo": "falta", "hallazgo": h.get("id"),
            "estado": h.get("estado")}


def _hallazgo_por_modulo(rep, nombre, sitio_import=None):
    """Hallazgo del reporte para el modulo que falta. Si varios cuelgan del mismo paquete, gana el cuyo import
    esta en (archivo, linea) del frame de la libreria que fallo (`sitio_import`)."""
    if not rep or not nombre:
        return None
    mejor, cands = None, []
    for l in rep.get("librerias", []):
        for h in l["hallazgos"]:
            m = h.get("modulo")
            if m and (m == nombre or m.startswith(nombre + ".") or nombre.startswith(m + ".")):
                if h.get("tipo") in ("submodulo_faltante", "modulo_movido", "alias_inexistente", "init_roto"):
                    cands.append(dict(h, libreria=l["libreria"], version=l["version"]))
                    continue
            if h.get("tipo") == "api_eliminada" and h.get("modulo") and (h["modulo"] + "." + h["nombre"]) == nombre:
                mejor = dict(h, libreria=l["libreria"], version=l["version"])
    if cands and sitio_import:
        for h in cands:
            im = h.get("import") or {}
            if im.get("linea") == sitio_import[1] and sitio_import[0].replace(os.sep, "/").endswith(im.get("archivo", "?")):
                return h
    return cands[0] if cands else mejor


def _lib_de_ruta(path, rep):
    p = path.replace(os.sep, "/")
    partes = p.split("/")
    for l in (rep or {}).get("librerias", []):
        if any(t in partes for t in l.get("paquetes", [])):
            return l
    m = re.search(r"/(lib_[A-Za-z0-9_]+)/", p)
    if m:
        top = m.group(1)
        for n, mod, pip in FACHADA_EXPORTS:
            if mod.split(".")[0] == top:
                return {"libreria": pip.split(" ")[0], "version": _version_lib(pip.split(" ")[0]), "paquetes": [top],
                        "hallazgos": []}
        # libreria del banco que no esta en la fachada ni en el reporte: se identifica por el nombre de la carpeta
        return {"libreria": top.replace("_", "-"), "version": "", "paquetes": [top], "hallazgos": []}
    return None


def traducir_excepcion(ex, job=None):
    """Convierte un error originado en una libreria del banco al dict de mensaje (o None si no aplica).
    Cubre BNXFaltaComponente, ImportError/ModuleNotFoundError, TypeError de firma y NotImplementedError."""
    import traceback
    if isinstance(ex, BNXFaltaComponente):
        return ex.info
    rep = cargar_reporte()
    try:
        frames = traceback.extract_tb(ex.__traceback__)
    except Exception:
        frames = []
    lib_f, modelo_f, lib_ent = None, None, None
    for i, fr in enumerate(frames):
        le = _lib_de_ruta(fr.filename, rep)
        if le is not None and lib_f is None:
            lib_f, lib_ent = fr, le
            if i > 0:
                modelo_f = frames[i - 1]
    if modelo_f is None:
        for fr in reversed(frames):
            if not _es_ruta_ajena(fr.filename) and _lib_de_ruta(fr.filename, rep) is None:
                modelo_f = fr
                break
    necesita = {}
    if modelo_f is not None:
        necesita = {"archivo": _rel_modelo(modelo_f.filename), "linea": modelo_f.lineno, "funcion": modelo_f.name}
    if lib_f is not None:
        necesita.update({"archivo_lib": _rel_modelo(lib_f.filename), "linea_lib": lib_f.lineno})
    msg = str(ex)
    if isinstance(ex, ImportError):
        nombre = getattr(ex, "name", None)
        m = re.search(r"cannot import name '([\w.]+)' from '([\w.]+)'", msg)
        if m:
            nombre = m.group(2) + "." + m.group(1)
        if not nombre:
            m = re.search(r"No module named '([\w.]+)'", msg)
            nombre = m.group(1) if m else None
        if not nombre:
            return None
        h = _hallazgo_por_modulo(rep, nombre, (lib_f.filename, lib_f.lineno) if lib_f is not None else None)
        if h is not None:
            inf = info_de_hallazgo(h, rep)
            inf["necesita"] = dict(inf["necesita"], **dict((k, v) for k, v in necesita.items()
                                                           if k in ("archivo", "linea") and not inf["necesita"].get(k)))
            if not activo_por_modo() and h.get("estado") == PARCHEABLE:
                inf["por_que"] += " | Hay un parche BNX disponible pero esta desactivado en modo real: " \
                                  "BNX_BANK_COMPAT=1 lo activa. " + AVISO_REAL
            return inf
        top = nombre.split(".")[0]
        conocido = [(n, mod, pip) for n, mod, pip in FACHADA_EXPORTS if mod.split(".")[0] == top]
        if conocido:
            pip = conocido[0][2].split(" ")[0]
            return {"componente": nombre, "modulo": nombre, "libreria": pip, "version": _version_lib(pip),
                    "necesita": necesita, "tipo": "falta",
                    "por_que": "la libreria %s no esta instalada en este entorno (no viajo en el paquete o setup.sh "
                               "no la instalo)" % pip}
        if lib_ent is not None:
            propio = top in lib_ent.get("paquetes", [])
            if propio:
                return {"componente": nombre.rsplit(".", 1)[-1], "modulo": nombre, "libreria": lib_ent["libreria"],
                        "version": lib_ent.get("version"), "necesita": necesita, "tipo": "falta",
                        "subpaquete": "/".join(nombre.split(".")[:-1]) + "/",
                        "por_que": "el .tar.gz/.whl del banco no trae ese modulo (error: %s)" % msg[:200]}
            return {"componente": nombre, "modulo": nombre, "libreria": lib_ent["libreria"],
                    "version": lib_ent.get("version"), "necesita": necesita, "tipo": "dependencia",
                    "por_que": "falta la dependencia de terceros '%s' que usa la libreria (no esta instalada en el "
                               "entorno)" % nombre}
        return None
    if isinstance(ex, TypeError):
        m = re.search(r"(?:^|\s)([\w.<>]+)\(\) (missing \d+ required (?:positional|keyword-only) arguments?: .+|"
                      r"got an unexpected keyword argument '(\w+)')", msg)
        if not m:
            return None
        sim = m.group(1).replace(".__init__", "").split(".")[-1]
        pip = next((p.split(" ")[0] for n, _m, p in FACHADA_EXPORTS if n == sim), None)
        if pip is None:
            return None
        lib = next((l for l in (rep or {}).get("librerias", []) if l["libreria"] == pip), None)
        modulo = next((mm for n, mm, _p in FACHADA_EXPORTS if n == sim), sim)
        return {"componente": "%s (firma)" % sim, "modulo": modulo, "libreria": pip,
                "version": (lib or {}).get("version") or _version_lib(pip), "necesita": necesita, "tipo": "falta",
                "por_que": "firma distinta: %s" % m.group(2).replace("missing", "falta:", 1)[:200]
                           if m.group(2).startswith("missing") else "firma distinta: parametro '%s' que la libreria "
                           "no acepta" % m.group(3)}
    if isinstance(ex, NotImplementedError) and lib_f is not None:
        return {"componente": lib_f.name, "modulo": _rel_modelo(lib_f.filename), "libreria": lib_ent["libreria"],
                "version": lib_ent.get("version"), "necesita": necesita, "tipo": "falta",
                "por_que": "la libreria del banco no implementa esta ruta (NotImplementedError: %s)" % msg[:160]}
    return None


def bloque_terminal(texto, titulo="ERROR: FALTA UN COMPONENTE DE UNA LIBRERIA DEL BANCO"):
    barra = "!" * 72
    return "\n".join([barra, "[BNX] " + titulo, barra, texto, barra])


def aviso_real():
    barra = "#" * 72
    return "\n".join([barra, "# [BNX] ATENCION: " + AVISO_REAL, "# Activo por BNX_BANK_COMPAT=1 (modo REAL).", barra])


def avisar_parche(que, hallazgo=None, extra=None):
    """Aviso ambar 'PARCHEADO: <que> (no validado)': una vez por parche; terminal + log + BNX_FALTANTES.json."""
    if os.environ.get("BNX_CHECK_ENV"):
        return          # check_env.py solo importa los jobs para verificar: no es una corrida, no se avisa ni se registra
    clave = (_job(), que)
    if clave in _ESTADO["avisados"]:
        return
    _ESTADO["avisados"].add(clave)
    info = {"componente": que, "modulo": que, "tipo": "parcheado", "hallazgo": hallazgo, "por_que": extra or ""}
    texto = registrar_faltante(info, tipo="parcheado")
    try:
        sys.stderr.write("[BNX] " + texto + "\n")
        sys.stderr.flush()
    except Exception:
        pass


# ---- stubs / loaders ----
def _stub_clase(nombre, info_base):
    def _init(self, *a, **k):
        inf = dict(info_base)
        sitio = _sitio_modelo()
        if sitio:
            n = dict(inf.get("necesita") or {})
            n.update(sitio)
            inf["necesita"] = n
        raise BNXFaltaComponente(inf)
    return type(str(nombre), (object,), {"__init__": _init, "__bnx_stub__": True,
                                          "__doc__": "BNX: componente ausente en la libreria del banco"})


class _StubModulo(object):
    pass


def _hacer_modulo_stub(nombre, info_base, nombres):
    import types
    m = types.ModuleType(nombre)
    m.__bnx_stub__ = True
    clases = {}
    for n in nombres:
        clases[n] = _stub_clase(n, info_base)
        setattr(m, n, clases[n])

    def __getattr__(attr):
        if attr.startswith("__"):
            raise AttributeError(attr)
        if attr not in clases:
            clases[attr] = _stub_clase(attr, info_base)
        return clases[attr]
    m.__getattr__ = __getattr__
    return m


class _Cargador(importlib.abc.Loader):
    def __init__(self, tipo, datos):
        self.tipo, self.datos = tipo, datos

    def create_module(self, spec):
        import types
        t, d = self.tipo, self.datos
        if t == "alias":
            mod = importlib.import_module(d["destino"])
            d["orig"] = (getattr(mod, "__spec__", None), getattr(mod, "__loader__", None),
                         getattr(mod, "__package__", None))
            return mod
        if t == "virtual":
            m = types.ModuleType(spec.name)
            m.__path__ = []
            return m
        if t == "stub":
            m = _hacer_modulo_stub(spec.name, d["info"], d["nombres"])
            return m
        if t == "perezoso":
            m = types.ModuleType(spec.name)
            m.__path__ = list(d["ubicaciones"])
            exports = d["exports"]

            def __getattr__(attr):
                if attr in exports:
                    destino = exports[attr]
                    if destino is None:
                        return _stub_clase(attr, d["info"])
                    val = getattr(importlib.import_module(destino), attr)
                    setattr(m, attr, val)
                    return val
                raise AttributeError("module %r has no attribute %r" % (spec.name, attr))
            m.__getattr__ = __getattr__
            return m
        return None

    def exec_module(self, module):
        if self.tipo == "alias" and self.datos.get("orig"):
            sp, ld, pk = self.datos["orig"]
            try:
                module.__spec__, module.__loader__, module.__package__ = sp, ld, pk
            except (AttributeError, TypeError):
                pass


class _Finder(importlib.abc.MetaPathFinder):
    def __init__(self, rep):
        self.rep = rep
        p = rep.get("parches", {})
        libs = dict((l["libreria"], l) for l in rep.get("librerias", []))
        self.hall = {}
        for l in rep.get("librerias", []):
            for h in l["hallazgos"]:
                self.hall[h["id"]] = dict(h, libreria=l["libreria"], version=l["version"])
        self.alias = dict(p.get("alias", {}))
        self.stubs = dict(p.get("stubs", {}))
        self.perezosos = dict(p.get("paquetes_perezosos", {}))
        # alias: no pisar un modulo real homonimo (p.ej. un 'libs' propio del modelo)
        for k in list(self.alias):
            top = k.split(".")[0]
            if top not in set(t for l in libs.values() for t in l.get("paquetes", [])):
                try:
                    real = importlib.util.find_spec(top)
                except (ImportError, ValueError, AttributeError):
                    real = None
                if real is not None and not getattr(real, "_bnx", False):
                    del self.alias[k]
        self.firmas = {}
        for r in p.get("firmas", []):
            if r.get("modulo_def"):
                self.firmas.setdefault(r["modulo_def"], set()).add(r["clase"])
        self.virtuales = set()
        for k in list(self.alias) + list(self.stubs):
            partes = k.split(".")
            for i in range(1, len(partes)):
                pre = ".".join(partes[:i])
                if pre not in self.stubs and pre not in self.perezosos and pre not in self.alias:
                    self.virtuales.add(pre)

    def _real(self, nombre, path):
        try:
            return importlib.machinery.PathFinder.find_spec(nombre, path)
        except (ImportError, ValueError, AttributeError):
            return None

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.perezosos:
            real = self._real(fullname, path)
            if real is None or not real.origin or not os.path.isfile(real.origin):
                return None
            try:
                with io.open(real.origin, "r", encoding="utf-8", errors="replace") as fh:
                    if _sha1(fh.read()) != self.perezosos[fullname]["sha1"]:
                        return None          # la libreria cambio: se usa tal cual
            except OSError:
                return None
            d = self.perezosos[fullname]
            h = self.hall.get(d.get("hallazgo"), {})
            info = info_de_hallazgo(h, self.rep) if h else {"componente": fullname, "modulo": fullname}
            avisar_parche("paquete %s cargado como perezoso (su __init__.py importa modulos inexistentes)" % fullname,
                          d.get("hallazgo"), h.get("por_que"))
            sp = importlib.machinery.ModuleSpec(fullname, _Cargador("perezoso", {
                "exports": d["exports"], "info": dict(info, tipo="falta"),
                "ubicaciones": list(real.submodule_search_locations or [])}), is_package=True)
            sp.submodule_search_locations = list(real.submodule_search_locations or [])
            return sp
        if fullname in self.alias:
            if self._real(fullname, path) is not None:
                return None
            destino = self.alias[fullname]
            avisar_parche("alias de modulo %s -> %s" % (fullname, destino), None,
                          "el modulo no esta en el paquete del banco; se reutiliza el del mismo nombre")
            return importlib.util.spec_from_loader(fullname, _Cargador("alias", {"destino": destino}))
        if fullname in self.stubs:
            if self._real(fullname, path) is not None:
                return None
            d = self.stubs[fullname]
            h = self.hall.get(d.get("hallazgo"), {})
            info = info_de_hallazgo(h, self.rep) if h else {"componente": fullname, "modulo": fullname}
            if not activo_por_modo_demo_or_forzado():
                return None
            avisar_parche("stub de %s (falla claro si se usa)" % fullname, d.get("hallazgo"), h.get("por_que"))
            sp = importlib.machinery.ModuleSpec(fullname, _Cargador("stub", {"info": info,
                                                                          "nombres": d.get("nombres", [])}))
            return sp
        if fullname in self.firmas:
            real = self._real(fullname, path)
            if real is None or real.loader is None:
                return None
            real.loader = _CargadorPost(real.loader, sorted(self.firmas[fullname]), self.rep)
            return real
        if fullname in self.virtuales:
            if self._real(fullname, path) is not None:
                return None
            sp = importlib.machinery.ModuleSpec(fullname, _Cargador("virtual", {}), is_package=True)
            sp.submodule_search_locations = []
            return sp
        return None


def activo_por_modo_demo_or_forzado():
    return _ESTADO["activo"]


def _shim_fn(modulo, nombre, hallazgo):
    def _f(*a, **k):
        raise BNXFaltaComponente({"componente": "%s.%s" % (modulo, nombre), "modulo": modulo,
                                  "libreria": "(dependencia)", "necesita": _sitio_modelo() or {},
                                  "por_que": "%s.%s fue eliminada en la version instalada y el parche BNX solo cubre su "
                                             "import, no su uso" % (modulo, nombre), "tipo": "falta"})
    _f.__name__ = nombre
    return _f


def instalar(reporte=None, forzar=None):
    """Registra los parches del reporte. Idempotente. Devuelve True si quedaron activos."""
    if _ESTADO["instalado"]:
        return _ESTADO["activo"]
    _ESTADO["instalado"] = True
    rep = reporte if reporte is not None else cargar_reporte()
    activo = forzar if forzar is not None else activo_por_modo()
    _ESTADO["activo"] = bool(activo and rep)
    if not rep or not activo:
        return False
    if not modo_demo():
        barra = aviso_real()
        sys.stderr.write(barra + "\n")
        registrar_faltante({"componente": "Parches BNX activos en modo REAL", "modulo": "bank_compat",
                            "libreria": "(todas)", "por_que": AVISO_REAL, "tipo": "parcheado"}, tipo="parcheado")
    f = _Finder(rep)
    _ESTADO["finder"] = f
    sys.meta_path.insert(0, f)
    for s in rep.get("parches", {}).get("shims", []):
        try:
            mod = importlib.import_module(s["modulo"])
        except Exception:
            continue
        if not hasattr(mod, s["nombre"]):
            setattr(mod, s["nombre"], _shim_fn(s["modulo"], s["nombre"], s.get("hallazgo")))
            avisar_parche("%s.%s ausente en la version instalada: shim solo para el import" % (s["modulo"], s["nombre"]),
                          s.get("hallazgo"))
    return True


def desinstalar():
    """Para pruebas: quita el finder y limpia el estado."""
    f = _ESTADO.get("finder")
    if f is not None and f in sys.meta_path:
        sys.meta_path.remove(f)
    _ESTADO.update({"instalado": False, "activo": False, "finder": None, "avisados": set(), "cfg_cache": {}})


# ---- adaptadores de firma ----
def _valor_config(clave):
    base = os.environ.get("CONF_PATH")
    if not base or not os.path.isdir(base):
        return None
    cache = _ESTADO["cfg_cache"]
    if clave in cache:
        return cache[clave]
    val = None
    for r, ds, fs in os.walk(base):
        for fn in sorted(fs):
            if not fn.endswith(".json"):
                continue
            try:
                with io.open(os.path.join(r, fn), "r", encoding="utf-8") as fh:
                    d = json.load(fh)
            except (OSError, ValueError):
                continue
            stack = [d]
            while stack and val is None:
                o = stack.pop()
                if isinstance(o, dict):
                    if clave in o and not isinstance(o[clave], (dict, list)):
                        val = (fn, o[clave])
                    stack.extend(o.values())
                elif isinstance(o, list):
                    stack.extend(o)
            if val is not None:
                break
        if val is not None:
            break
    cache[clave] = val
    return val


def _coerce(v, tipo):
    if tipo == "int":
        try:
            return int(str(v).strip())
        except ValueError:
            return v
    return v


def adaptar_firma(nombre, cls, rep=None):
    """Parcha EN SITIO (idempotente) los metodos de `cls` para completar los parametros obligatorios que el modelo
    no pasa, segun bank_compat_report.json. Sin reglas para `nombre` (o inactivo) no hace nada. Devuelve cls."""
    rep = rep if rep is not None else cargar_reporte()
    if not rep or not _ESTADO["activo"] or not isinstance(cls, type) or getattr(cls, "__bnx_missing__", False):
        return cls
    reglas = {}
    for r in rep.get("parches", {}).get("firmas", []):
        if r["clase"] == nombre:
            reglas.setdefault(r["metodo"].split(".", 1)[1] if "." in r["metodo"] else "__init__", []).append(r)
    if not reglas:
        return cls
    import inspect
    for meth, rs in reglas.items():
        orig = cls.__dict__.get(meth)
        if orig is None or getattr(orig, "__bnx_firma__", False) or not callable(orig):
            continue

        def hacer(orig, rs, meth):
            def envuelto(self, *a, **k):
                try:
                    ligados = inspect.signature(orig).bind_partial(self, *a, **k).arguments
                except (TypeError, ValueError):
                    ligados = dict(k)
                for r in rs:
                    p = r["param"]
                    if p in ligados or p in k:
                        continue
                    val, origen = None, ""
                    if r["fuente"] == "config":
                        hit = _valor_config(r["clave"])
                        if hit is not None:
                            val, origen = _coerce(hit[1], r.get("tipo")), "config %s (%s)" % (r["clave"], hit[0])
                    if val is None and r.get("default") is not None:
                        val, origen = r["default"], "valor neutro %r" % (r["default"],)
                    if val is None:
                        h = [x for l in rep["librerias"] for x in l["hallazgos"] if x["id"] == r.get("hallazgo")]
                        inf = info_de_hallazgo(dict(h[0], libreria=r["libreria"]) if h else {"componente": nombre})
                        sitio = _sitio_modelo()
                        if sitio:
                            inf["necesita"] = dict(inf.get("necesita") or {}, **sitio)
                        inf["por_que"] = "firma distinta: falta el parametro %s y no hay valor en la config del modelo" % p
                        raise BNXFaltaComponente(inf)
                    k[p] = val
                    avisar_parche("%s.%s(%s=%r) completado con %s" % (nombre, meth, p, val, origen), r.get("hallazgo"),
                                  "el modelo no pasa '%s' y la libreria lo exige" % p)
                return orig(self, *a, **k)
            envuelto.__name__ = getattr(orig, "__name__", meth)
            envuelto.__doc__ = getattr(orig, "__doc__", None)
            envuelto.__bnx_firma__ = True
            return envuelto
        setattr(cls, meth, hacer(orig, rs, meth))
    return cls


class _CargadorPost(importlib.abc.Loader):
    """Envuelve el cargador real: tras ejecutar el modulo, parcha en sitio las clases con regla de firma."""

    def __init__(self, real, clases, rep):
        self.real, self.clases, self.rep = real, clases, rep

    def create_module(self, spec):
        cm = getattr(self.real, "create_module", None)
        return cm(spec) if cm else None

    def __getattr__(self, nombre):
        return getattr(self.real, nombre)

    def exec_module(self, module):
        self.real.exec_module(module)
        for c in self.clases:
            cls = getattr(module, c, None)
            if isinstance(cls, type):
                adaptar_firma(c, cls, self.rep)


def placeholder(nombre, modulo, origen, excepcion):
    """Clase 'faltante' de la fachada: al instanciarla lanza BNXFaltaComponente con el mensaje completo."""
    info = None
    try:
        info = traducir_excepcion(excepcion)
    except Exception:
        info = None
    if info is None:
        info = {"componente": nombre, "modulo": modulo, "libreria": str(origen).split(" ")[0], "version": "",
                "necesita": {}, "tipo": "falta",
                "por_que": "no se pudo importar '%s': %s: %s" % (modulo, type(excepcion).__name__, str(excepcion)[:200])}
    info = dict(info)
    info.setdefault("componente", nombre)

    class _Faltante(object):
        __bnx_missing__ = True

        def __init__(self, *args, **kwargs):
            inf = dict(info)
            sitio = _sitio_modelo()
            if sitio:
                inf["necesita"] = dict(inf.get("necesita") or {}, **sitio)
            raise BNXFaltaComponente(inf)
    _Faltante.__name__ = nombre
    _Faltante.__qualname__ = nombre
    return _Faltante


def main(argv=None):
    """python bank_compat.py            -> resumen del bank_compat_report.json de este paquete
    python bank_compat.py --analizar <carpeta_wheels> [--src <carpeta_modelo>] -> analisis y reporte"""
    import argparse
    ap = argparse.ArgumentParser(description=main.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analizar", help="carpeta con wheels/sdist del banco")
    ap.add_argument("--src", help="carpeta del modelo (.py y .json)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.analizar:
        cod, cfg = {}, {}
        for r, ds, fs in os.walk(a.src or "."):
            ds[:] = [d for d in ds if d not in (".git", "__pycache__", "logs", "node_modules")]
            for f in fs:
                p = os.path.join(r, f)
                rel = os.path.relpath(p, a.src or ".")
                if f.endswith(".py"):
                    cod[rel] = io.open(p, encoding="utf-8", errors="replace").read()
                elif f.endswith(".json") and "settings" in rel:
                    cfg[rel] = io.open(p, encoding="utf-8", errors="replace").read()
        rep = analizar([a.analizar], cod, cfg, {})
        print(reporte_a_json(rep) if a.json else resumen_texto(rep))
        return 0
    rep = cargar_reporte()
    print(reporte_a_json(rep) if a.json and rep else resumen_texto(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
