# -*- coding: utf-8 -*-
"""Settings MINIMOS COMPLETOS del DEMO, inferidos del codigo del banco (analisis estatico con AST).

Sin la carpeta bin/settings del banco, un job que lee su config de negocio (self.config['model_name'],
settings['tables_info'][t]['database'], config_custom['n_mis'], ...) fallaba con KeyError. Aqui se
recorren el job y los modulos locales que importa (utils/, bnmxverse/, toolbox/...) y se buscan los
accesos a la config:
  - raices: nombres settings/config/cfg/job_settings/config_rigid (job.json), config_custom
    (config_custom.json), self.config*, kernel.settings.job[env] / .job.get(env),
    kernel.settings.jobs[env] (jobs.json);
  - X['k'] (y X['a']['b']), X.get('k') cuando se usa encadenado (X.get('k').format(...));
  - claves cuyo nombre solo se usa para PREGUNTAR si existen ('k' in X, X.get('k') is None...) NO se
    inventan: el job tiene otro camino cuando faltan;
  - nombres dinamicos (X['tables_info'][nombre]): se toman los literales que otras llamadas pasan como
    ese parametro (load_tables(kernel, settings, 'crd_portfolio_master')).
El valor se escoge por el uso (se formatea con .format -> texto con {}; se itera -> lista; se indexa
-> dict; aritmetica -> numero) y por el nombre (model_name, *_path, tablas...). Es un RELLENO: sirve
para que el job no muera por una clave ausente, no para reproducir el negocio. Compatible con Python 3.8.
"""
import ast
import os
import re

RAIZ_JOB = ("settings", "config", "cfg", "conf", "job_settings", "job_config", "config_rigid", "job_conf")
RAIZ_CUSTOM = ("config_custom", "custom_config", "config_customs_env")
ESTRELLA = "*"


def _slice_valor(nodo):
    s = nodo.slice
    if s.__class__.__name__ == "Index":          # Python 3.8: ast.Index(value=...)
        s = s.value
    return s


def _cte_str(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if n.__class__.__name__ == "Str":
        return n.s
    return None


def _nombre_attr(n):
    """'a.b.c' de una cadena de Name/Attribute o None."""
    partes = []
    while isinstance(n, ast.Attribute):
        partes.append(n.attr)
        n = n.value
    if isinstance(n, ast.Name):
        partes.append(n.id)
        return ".".join(reversed(partes))
    return None


class _Arbol(object):
    """Claves de la config: nodo = {"hijos": {k: nodo}, "uso": set(), "opcional": bool}."""

    def __init__(self):
        self.raiz = {"job": self._n(), "custom": self._n(), "jobs": self._n()}
        self.param_rutas = {}     # (funcion, indice|nombre) -> ruta de config que le pasan al llamarla
        self.dinamicas = []       # (funcion, indice del parametro, ruta del dict indexado)
        self.iter_vars = {}       # variable de un for/comprehension -> ruta de la lista que recorre
        self.elementos = {}       # ruta de lista -> elementos que el codigo usa como clave (d['lit'])
        self.unpack = {}          # ruta de lista -> N (a, b, c = [... for x in lista])
        self.attr_param = {}      # 'self.source' -> (metodo, parametro)
        self.opcionales = set()   # rutas con presencia consultada

    @staticmethod
    def _n():
        return {"hijos": {}, "uso": set(), "req": False}

    def nodo(self, ruta, crear=True):
        n = self.raiz[ruta[0]]
        for k in ruta[1:]:
            h = n["hijos"]
            if k not in h:
                if not crear:
                    return None
                h[k] = self._n()
            n = h[k]
        return n


class _Analizador(ast.NodeVisitor):
    def __init__(self, arbol, tabla_llamadas):
        self.t = arbol
        self.llamadas = tabla_llamadas       # nombre de funcion -> [Call]
        self.alias = {}                      # nombre local -> ruta
        self.dictcomp = {}                   # dict armado con {k: .. for k in <lista de config>} -> ruta de la lista
        self.params = {}                     # funcion -> [nombres]
        self.func = None
        self.padres = {}

    # -- resolucion de rutas ------------------------------------------------
    def ruta(self, n):
        """Ruta (raiz, k1, k2...) de una expresion o None."""
        if isinstance(n, ast.Name):
            if n.id in self.alias:
                return self.alias[n.id]
            if n.id in RAIZ_CUSTOM:
                return ("custom",)
            if n.id in RAIZ_JOB:
                return ("job",)
            return None
        if isinstance(n, ast.Attribute):
            nombre = _nombre_attr(n)
            if nombre:
                ult = nombre.split(".")[-1]
                if ult in RAIZ_CUSTOM and nombre.startswith("self."):
                    return ("custom",)
                if ult in RAIZ_JOB and nombre.startswith("self."):
                    return ("job",)
            return None
        if isinstance(n, ast.Subscript):
            base = n.value
            nom = _nombre_attr(base)
            if nom and nom.endswith("settings.job"):
                return ("job",)
            if nom and nom.endswith("settings.jobs"):
                return ("jobs",)
            r = self.ruta(base)
            if r is None:
                return None
            k = _cte_str(_slice_valor(n))
            if k is None:
                s = _slice_valor(n)
                if isinstance(s, ast.Name) and self.func:
                    self.t.dinamicas.append((self.func, s.id, r))
                elif isinstance(s, ast.Attribute) and _nombre_attr(s) and _nombre_attr(s).startswith("self.") \
                        and self.func:
                    self.t.dinamicas.append((self.func, _nombre_attr(s), r))
                return r + (ESTRELLA,)
            return r + (k,)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get" and n.args:
            nom = _nombre_attr(n.func.value)
            if nom and nom.endswith("settings.job"):
                return ("job",)
            if nom and nom.endswith("settings.jobs"):
                return ("jobs",)
            r = self.ruta(n.func.value)
            k = _cte_str(n.args[0])
            if r is not None and k is not None:
                return r + (k,)
            if r is not None and isinstance(n.args[0], ast.Name) and self.func:
                self.t.dinamicas.append((self.func, n.args[0].id, r))
                return r + (ESTRELLA,)
        return None

    def _usar(self, ruta, uso, requerido=True):
        if not ruta or len(ruta) < 2:
            return
        n = self.t.nodo(ruta)
        if n is not None:
            n["uso"].add(uso)
            if requerido:
                n["req"] = True

    # -- recorrido ----------------------------------------------------------
    def visit_FunctionDef(self, nodo):
        ant, self.func = self.func, nodo.name
        self.params[nodo.name] = [a.arg for a in nodo.args.args]
        offset = 1 if nodo.args.args and nodo.args.args[0].arg in ("self", "cls") else 0
        for i, a in enumerate(nodo.args.args):         # parametros que reciben una parte de la config
            r = self.t.param_rutas.get((nodo.name, i - offset)) or self.t.param_rutas.get((nodo.name, a.arg))
            if r is not None and a.arg not in RAIZ_JOB and a.arg not in RAIZ_CUSTOM:
                self.alias[a.arg] = r
        for a in nodo.args.args:                     # parametro llamado settings/config -> raiz
            if a.arg in RAIZ_CUSTOM:
                self.alias.setdefault(a.arg, ("custom",))
            elif a.arg in RAIZ_JOB:
                self.alias.setdefault(a.arg, ("job",))
        self.generic_visit(nodo)
        self.func = ant

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_For(self, nodo):
        self._iter(nodo.target, nodo.iter)
        self.generic_visit(nodo)

    def visit_comprehension(self, nodo):
        self._iter(nodo.target, nodo.iter)
        self.generic_visit(nodo)

    def _iter(self, target, it):
        r = self.ruta(it)
        if r is not None and len(r) >= 2 and isinstance(target, ast.Name):
            self.t.iter_vars[target.id] = r
            n = self.t.nodo(r)
            n["uso"].add("lista")

    def visit_Assign(self, nodo):
        # self.attr = <parametro>  -> 'self.attr' se resuelve al parametro de ese metodo
        if self.func and isinstance(nodo.value, ast.Name) and nodo.value.id in self.params.get(self.func, []):
            for t in nodo.targets:
                if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                    self.t.attr_param["self." + t.attr] = (self.func, nodo.value.id)
        # a, b, c = [f(x) for x in LISTA]  -> LISTA trae N elementos
        if len(nodo.targets) == 1 and isinstance(nodo.targets[0], (ast.Tuple, ast.List)) and \
                isinstance(nodo.value, (ast.ListComp, ast.GeneratorExp)):
            g = nodo.value.generators[0]
            r = self.ruta(g.iter)
            if r is not None:
                self.t.unpack[r] = len(nodo.targets[0].elts)
        # d = {k: ... for k in settings['final_parquets']}  -> d['literal'] pide ese elemento a la lista
        if len(nodo.targets) == 1 and isinstance(nodo.targets[0], ast.Name) and \
                isinstance(nodo.value, ast.DictComp):
            rr = self.ruta(nodo.value.generators[0].iter)
            if rr is not None and len(rr) >= 2:
                self.dictcomp[nodo.targets[0].id] = rr
        r = self.ruta(nodo.value)
        if r is not None and len(nodo.targets) == 1:
            t = nodo.targets[0]
            if isinstance(t, ast.Name):
                self.alias[t.id] = r
            elif isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                self.alias["self." + t.attr] = r
        self.generic_visit(nodo)

    def _contexto(self, nodo):
        """Uso del valor segun el padre: format | lista | dict | num | texto."""
        p = self.padres.get(id(nodo))
        if isinstance(p, ast.Attribute):
            if p.attr in ("format", "replace", "split", "strip", "lower", "upper", "startswith", "endswith"):
                return "texto_fmt" if p.attr == "format" else "texto"
            if p.attr in ("keys", "items", "values", "update", "setdefault", "pop"):
                return "dict"
            if p.attr in ("append", "extend", "index", "count"):
                return "lista"
        if isinstance(p, (ast.For, ast.comprehension)) and getattr(p, "iter", None) is nodo:
            return "lista"
        if isinstance(p, ast.Call) and nodo in p.args:
            f = _nombre_attr(p.func) or ""
            if f in ("enumerate", "sorted", "list", "set", "tuple", "len", "zip", "reversed", "sum", "max", "min"):
                return "lista"
            if f in ("int", "float"):
                return "num"
            if f in ("os.path.join", "join_path", "join", "open"):
                return "texto"
        if isinstance(p, ast.BinOp):
            otro = p.right if p.left is nodo else p.left
            if isinstance(otro, ast.Constant) and isinstance(otro.value, (int, float)) and \
                    not isinstance(otro.value, bool):
                return "num"
            if isinstance(p.op, ast.Add) and _cte_str(otro) is not None:
                return "texto"
        if isinstance(p, ast.Compare):
            for o in list(p.comparators) + [p.left]:
                if isinstance(o, ast.Constant) and isinstance(o.value, (int, float)) and o is not nodo:
                    return "num"
        if isinstance(p, ast.Subscript) and p.value is nodo:
            return "dict"
        if isinstance(p, ast.JoinedStr) or isinstance(p, ast.FormattedValue):
            return "texto"
        return ""

    def _presencia(self, nodo):
        """True si el acceso solo sirve para preguntar si existe: 'k' in X / X.get('k') is None / if X.get('k')."""
        p = self.padres.get(id(nodo))
        if isinstance(p, ast.Compare):
            return True
        if isinstance(p, (ast.If, ast.IfExp, ast.While, ast.UnaryOp, ast.BoolOp)):
            return True
        return False

    def visit_Subscript(self, nodo):
        if isinstance(nodo.value, ast.Name) and nodo.value.id in self.dictcomp:
            k = _cte_str(_slice_valor(nodo))
            if k is not None:
                lst = self.t.elementos.setdefault(self.dictcomp[nodo.value.id], [])
                if k not in lst:
                    lst.append(k)
        if isinstance(nodo.ctx, ast.Load):
            r = self.ruta(nodo)
            if r is not None and len(r) >= 2 and not isinstance(self.padres.get(id(nodo)), ast.Subscript):
                self._usar(r, self._contexto(nodo) or "")
            elif r is not None and len(r) >= 2:
                self._usar(r, "dict")
        elif isinstance(nodo.ctx, ast.Store):
            pass
        self.generic_visit(nodo)

    def visit_Call(self, nodo):
        if isinstance(nodo.func, ast.Attribute) and nodo.func.attr == "get" and nodo.args:
            r = self.ruta(nodo)
            if r is not None and len(r) >= 2:
                p = self.padres.get(id(nodo))
                encadenado = isinstance(p, ast.Attribute) or isinstance(p, ast.Subscript)
                ctx = self._contexto(nodo)
                if len(nodo.args) == 1 and not nodo.keywords and encadenado and not self._presencia(nodo):
                    self._usar(r, ctx)
                else:
                    self.t.opcionales.add(r)
        nom = nodo.func.id if isinstance(nodo.func, ast.Name) else (
            nodo.func.attr if isinstance(nodo.func, ast.Attribute) else None)
        if nom:
            for i, a in enumerate(nodo.args):          # f(filter_values) con filter_values = settings['filter_values']
                ra = self.ruta(a)
                if ra is not None and len(ra) >= 2:
                    self.t.param_rutas[(nom, i)] = ra
            for kw in nodo.keywords:
                ra = self.ruta(kw.value)
                if kw.arg and ra is not None and len(ra) >= 2:
                    self.t.param_rutas[(nom, kw.arg)] = ra
            self.llamadas.setdefault(nom, []).append(nodo)
        self.generic_visit(nodo)

    def visit_Compare(self, nodo):
        # 'k' in X  /  'k' in list(X.keys())  /  'k' in X.keys()
        for op, comp in zip(nodo.ops, nodo.comparators):
            if isinstance(op, (ast.In, ast.NotIn)):
                k = _cte_str(nodo.left)
                obj = comp
                if isinstance(obj, ast.Call) and obj.args and _nombre_attr(obj.func) in ("list", "set", "sorted"):
                    obj = obj.args[0]
                if isinstance(obj, ast.Call) and isinstance(obj.func, ast.Attribute) and obj.func.attr == "keys":
                    obj = obj.func.value
                r = self.ruta(obj)
                if k is not None and r is not None:
                    self.t.opcionales.add(r + (k,))
        self.generic_visit(nodo)


def _marcar_padres(arbol_ast, padres):
    for p in ast.walk(arbol_ast):
        for h in ast.iter_child_nodes(p):
            padres[id(h)] = p


# ---------------------------------------------------------------------------
def _leer(ruta):
    try:
        with open(ruta, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def _modulo_a_archivo(modulo, bank_dirs):
    rel = modulo.replace(".", os.sep)
    for d in bank_dirs:
        for c in (os.path.join(d, rel + ".py"), os.path.join(d, rel, "__init__.py")):
            if os.path.isfile(c):
                return c
    return None


def _imports_locales(codigo, bank_dirs):
    try:
        a = ast.parse(codigo)
    except SyntaxError:
        return []
    out = []
    for n in ast.walk(a):
        mods = []
        if isinstance(n, ast.Import):
            mods = [x.name for x in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            mods = [n.module] + ["%s.%s" % (n.module, x.name) for x in n.names]
        for m in mods:
            f = _modulo_a_archivo(m, bank_dirs)
            if f and f not in out:
                out.append(f)
    return out


def archivos_del_job(archivo_job, bank_dirs, limite=60):
    """El job y los modulos locales que importa (transitivo), sin salir de bank_dirs."""
    visto, cola = [], [archivo_job]
    while cola and len(visto) < limite:
        f = cola.pop(0)
        if f in visto or not f or not os.path.isfile(f):
            continue
        visto.append(f)
        cola.extend(_imports_locales(_leer(f), bank_dirs))
    return visto


def _analizar(archivos, param_rutas=None):
    arbol = _Arbol()
    arbol.param_rutas = dict(param_rutas or {})
    llamadas = {}
    pendientes = []
    for f in archivos:
        try:
            a = ast.parse(_leer(f))
        except SyntaxError:
            continue
        an = _Analizador(arbol, llamadas)
        _marcar_padres(a, an.padres)
        an.visit(a)
        pendientes.append(an)
    if param_rutas is None and arbol.param_rutas:       # 2da pasada: ya se sabe que config recibe cada funcion
        return _analizar(archivos, arbol.param_rutas)
    return arbol, llamadas, pendientes


def _nombres_dinamicos(arbol, llamadas, pendientes):
    """Nombres de las claves dinamicas (tables_info[t], config_rigid[self.source]): los literales que otras
    llamadas pasan como ese parametro, o los elementos de la lista que se recorre (for t in lista)."""
    params = {}
    for an in pendientes:
        params.update(an.params)
    for fn, param, ruta in list(arbol.dinamicas):
        if param.startswith("self."):
            if param not in arbol.attr_param:
                continue
            fn, param = arbol.attr_param[param]
        ps = params.get(fn) or []
        if param not in ps:
            continue
        idx = ps.index(param)
        for c in llamadas.get(fn, []):
            es_metodo = isinstance(c.func, ast.Attribute)
            i = idx - (1 if es_metodo and ps and ps[0] == "self" else 0)
            arg = c.args[i] if 0 <= i < len(c.args) else None
            for kw in c.keywords:
                if kw.arg == param:
                    arg = kw.value
            nombres = []
            lit = _cte_str(arg) if arg is not None else None
            if lit:
                nombres = [lit]
            elif isinstance(arg, ast.Name) and arg.id in arbol.iter_vars:
                lista = arbol.iter_vars[arg.id]
                nombres = ["tabla_%d" % (j + 1)
                           for j in range(arbol.unpack.get(lista, 2))]
                nl = arbol.nodo(lista)
                nl["fijo"] = nombres
            plantilla = arbol.nodo(ruta + (ESTRELLA,), crear=False)
            for nm in nombres:
                nuevo = arbol.nodo(ruta + (nm,))
                if plantilla is not None:
                    _copiar(plantilla, nuevo)
                nuevo["req"] = True
                nuevo["uso"].add("dict")
def _renombrar(arbol, viejo, nuevo):
    """Renombra la clave `viejo` por `nuevo` en los dicts de la config (tables_info.tabla_1 -> .portfolio_snapshot_c)."""
    def rec(nodo):
        h = nodo["hijos"]
        if viejo in h and nuevo not in h and viejo.startswith("tabla_"):
            h[nuevo] = h.pop(viejo)
        for x in list(h.values()):
            rec(x)
    for r in arbol.raiz.values():
        rec(r)


def _copiar(origen, destino):
    destino["uso"] |= origen["uso"]
    destino["req"] = destino["req"] or origen["req"]
    for k, h in origen["hijos"].items():
        if k not in destino["hijos"]:
            destino["hijos"][k] = {"hijos": {}, "uso": set(), "req": False}
        _copiar(h, destino["hijos"][k])


# ---------------------------------------------------------------------------
def _valor(clave, nodo, modelo, job, tabla=None):
    """Valor de relleno de una clave segun su uso en el codigo y su nombre."""
    k = clave.lower()
    if k == "columns" and "lista" in nodo["uso"] or k == "columns" and not nodo["hijos"]:
        return ["*"]
    if nodo.get("fijo"):
        return list(nodo["fijo"])
    if k == "final_tables":       # {nombre: {name, format, mode, partitionBy}} (toolbox/write.py)
        return {job or "salida": {"name": "demo_db.%s_%s" % (modelo or "m", job or "salida"),
                                  "format": "hive", "mode": "append", "partitionBy": "proc_dt"}}
    if k == "final_parquets":
        return [job or "salida"]
    hijos = {h: v for h, v in nodo["hijos"].items() if h != ESTRELLA}
    if hijos or "dict" in nodo["uso"]:
        return {h: _valor(h, v, modelo, job, clave) for h, v in sorted(hijos.items())}
    if k == "model_name":
        return modelo or "demo"
    if k in ("database", "db", "schema"):
        return "demo_db"
    if k in ("table", "table_name", "name"):
        return "demo_db.%s" % (tabla or job or "tabla")
    if k in ("email_sender", "sender"):
        return "demo@example.com"
    if k.startswith("email_receivers") or k.endswith("receivers"):
        return ""
    if k in ("where", "query", "sql") or k.startswith("query"):
        return ""
    if k in ("lag", "mob", "risk", "n_mis", "n_threads", "period", "n_time", "year", "step"):
        return 1 if k in ("lag", "mob", "risk") else (3 if k in ("n_mis", "n_time") else (2 if k == "n_threads" else 1))
    if "lista" in nodo["uso"]:
        return ["demo"] if k in ("sources", "final_parquets", "final_tables") else []
    if "num" in nodo["uso"]:
        return 1
    if "threshold" in k or k.endswith(("_pct", "_ratio")):
        return 0.5
    if "write_mode" in k or k == "mode":
        return "overwrite"
    if k.endswith(("_path", "path", "root", "_dir", "_file")) or "path" in k:
        return "demo/%s/{}/" % k.replace("_path", "") if "texto_fmt" in nodo["uso"] else "demo/%s/" % k
    if "texto_fmt" in nodo["uso"]:
        return "demo_{}"
    if k.endswith(("s", "list")) and k not in ("address", "status", "class"):
        return []
    return "demo_%s" % k


def inferir(archivos_job, modelo="", job="", env="uat"):
    """{'job': {...}, 'custom': {...}, 'jobs': {...}, 'inventadas': [rutas]} para un job.
    archivos_job: archivos .py a analizar (el job + sus imports locales)."""
    arbol, llamadas, pend = _analizar(archivos_job)
    # claves que el JOB mismo lee de forma obligatoria (aunque un modulo auxiliar pregunte si existen)
    propio, _l, _p = _analizar(archivos_job[:1])
    propias = set()

    def _recoger(ruta, nodo):
        for k, h in nodo["hijos"].items():
            if h["req"]:
                propias.add(ruta + (k,))
            _recoger(ruta + (k,), h)
    for nom in ("job", "custom", "jobs"):
        _recoger((nom,), propio.raiz[nom])
    _nombres_dinamicos(arbol, llamadas, pend)
    for ruta_l, lits in arbol.elementos.items():
        nl = arbol.nodo(ruta_l)
        n_fijo = len(nl.get("fijo") or [])
        nuevos = list(lits) + ["tabla_%d" % (j + 1) for j in range(max(0, n_fijo - len(lits)))]
        viejos = nl.get("fijo") or []
        nl["fijo"] = nuevos
        # los dict indexados por esos nombres (tables_info[nombre]) pasan a usar los nombres reales
        for nm_v, nm_n in zip(viejos, nuevos):
            _renombrar(arbol, nm_v, nm_n)
    out = {}
    inventadas = []

    def _podar(ruta, nodo):
        for k in list(nodo["hijos"]):
            r = ruta + (k,)
            if (r in arbol.opcionales and r not in propias) or k == ESTRELLA:
                del nodo["hijos"][k]
            else:
                _podar(r, nodo["hijos"][k])
    for nombre in ("job", "custom", "jobs"):
        n = arbol.raiz[nombre]
        _podar((nombre,), n)
        out[nombre] = {h: _valor(h, v, modelo, job) for h, v in sorted(n["hijos"].items())}

        def _rec(pref, d):
            for k, v in d.items():
                inventadas.append("%s.%s%s" % (nombre, pref, k))
                if isinstance(v, dict):
                    _rec(pref + k + ".", v)
        _rec("", out[nombre])
    out["inventadas"] = inventadas
    return out


def mezclar_faltantes(real, relleno):
    """Completa `real` (dict) con las claves de `relleno` que le faltan. Devuelve las claves anadidas."""
    anadidas = []

    def _m(a, b, pref):
        for k, v in b.items():
            if k not in a:
                a[k] = v
                anadidas.append(pref + k)
            elif isinstance(a[k], dict) and isinstance(v, dict):
                _m(a[k], v, pref + k + ".")
    _m(real, relleno, "")
    return anadidas


def _archivo_de_modulo(modulo, bank_dirs):
    return _modulo_a_archivo(modulo, bank_dirs) if modulo else None


def generar(settings_dir, entries, env, root, bank_dirs):
    """Escribe en settings_dir los settings minimos COMPLETOS del demo (spark.json, jobs.json,
    <model>/<job>.json, <model>/config_custom.json) con las claves que el codigo de cada job usa.
    Devuelve {"<model>/<job>": [claves inventadas]} para el reporte del demo."""
    import json

    def _w(rel, obj):
        ruta = os.path.join(settings_dir, rel)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=1)
    jobs_json = {"general_root": root.rstrip("/") + "/", "static": ""}
    por_modelo = {}
    inventadas = {}
    for e in entries:
        modelo, job = e.get("model"), e.get("job")
        if not (modelo and job):
            continue
        f = _archivo_de_modulo(e.get("module"), bank_dirs)
        r = inferir(archivos_del_job(f, bank_dirs), modelo, job, env) if f else \
            {"job": {}, "custom": {}, "jobs": {}, "inventadas": []}
        for k, v in r["jobs"].items():
            jobs_json.setdefault(k, v)
        _w("%s/%s.json" % (modelo, job), {env: r["job"]})
        mc = por_modelo.setdefault(modelo, {})
        mezclar_faltantes(mc, r["custom"])
        inventadas["%s/%s" % (modelo, job)] = r["inventadas"]
    _w("spark.json", {"logging_path": "logs/", "logging_level": "ERROR",
                      "default": {"spark.yarn.queue": "default"}, "spark_queue_uat": "default"})
    _w("jobs.json", {env: jobs_json})
    for modelo, custom in por_modelo.items():
        _w("%s/config_custom.json" % modelo, {"env": {env: {}}, "default": custom})
    return inventadas
