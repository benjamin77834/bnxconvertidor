# -*- coding: utf-8 -*-
"""Parser SQL minimo y tolerante (sin dependencias): tablas, columnas por tabla, filtros con literales.
Si sqlglot estuviera instalado no hace falta: este parser cubre SELECT/JOIN/WHERE/CAST/subconsultas."""
import re

KW = set("""select from where and or not in is null like rlike regexp between group by order having join
left right inner outer full cross on as case when then else end distinct limit union all intersect
except cast over partition asc desc interval true false exists with using lateral view natural semi
anti rows range unbounded preceding following current row div mod date timestamp if any some offset
sort cluster distribute window filter nulls first last tablesample insert into table overwrite
values set day days month months year years hour minute second""".split())
TIPOS_NUM = ("int", "integer", "bigint", "smallint", "tinyint", "double", "float", "decimal",
             "numeric", "long", "real", "number")
FN_NUM = ("sum", "avg", "mean", "stddev", "variance", "stddev_samp", "stddev_pop")
OPS = ("=", "==", "<=", ">=", "<", ">", "<>", "!=")

_TOK = re.compile(r"""
 (?P<ws>\s+|--[^\n]*|/\*.*?\*/)
|(?P<str>'(?:[^'\\]|\\.|'')*'|"(?:[^"\\]|\\.)*")
|(?P<num>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?[lLdDfF]?)
|(?P<id>(?:`[^`]+`|[A-Za-z_\u00C0-\uFFFF][\w$\u00C0-\uFFFF]*)(?:\s*\.\s*(?:`[^`]+`|[A-Za-z_\u00C0-\uFFFF][\w$\u00C0-\uFFFF]*|\*))*)
|(?P<op><=>|<>|!=|<=|>=|==|\|\||[(),;=<>+\-*/%.:\[\]{}?])
|(?P<otro>.)
""", re.S | re.X)


class Tok(object):
    __slots__ = ("k", "t", "s", "e")

    def __init__(self, k, t, s, e):
        self.k, self.t, self.s, self.e = k, t, s, e

    @property
    def low(self):
        return self.t.lower()

    def __repr__(self):
        return "Tok(%s,%r)" % (self.k, self.t)


def tokenizar(q):
    out = []
    for m in _TOK.finditer(q):
        k = m.lastgroup
        if k == "ws":
            continue
        out.append(Tok(k, m.group(), m.start(), m.end()))
    return out


def partes_id(t):
    return [p.strip().strip("`") for p in re.split(r"\s*\.\s*", t)]


def es_kw(t):
    return t.k == "id" and "." not in t.t and t.low in KW


def literal(t):
    """Valor Python de un token literal (str/num) o NoLit."""
    if t.k == "str":
        return t.t[1:-1].replace("''", "'")
    if t.k == "num":
        x = t.t.rstrip("lLdDfF")
        try:
            return int(x)
        except ValueError:
            try:
                return float(x)
            except ValueError:
                return None
    return None


def primera_palabra(q):
    m = re.match(r"\s*(?:\(\s*)*([A-Za-z]+)", q or "")
    return m.group(1).lower() if m else ""


def _tablas(toks):
    """[(nombre, alias, tok)] de FROM/JOIN, y nombres de CTE."""
    refs, ctes = [], set()
    n = len(toks)
    pila = []     # (nombre de funcion previa) por parentesis abierto
    hay_with = any(t.k == "id" and t.low == "with" for t in toks)
    i = 0
    while i < n:
        t = toks[i]
        if t.k == "op" and t.t == "(":
            prev = toks[i - 1].low if i and toks[i - 1].k == "id" else ""
            pila.append(prev)
        elif t.k == "op" and t.t == ")":
            if pila:
                pila.pop()
        elif hay_with and t.k == "id" and t.low not in KW and i + 2 < n and toks[i + 1].low == "as" \
                and toks[i + 2].t == "(" and i and (toks[i - 1].low == "with" or toks[i - 1].t == ","):
            ctes.add(t.low)
        elif t.k == "id" and t.low in ("from", "join") and "." not in t.t:
            if t.low == "from" and pila and pila[-1] in ("extract", "substring", "trim", "overlay"):
                i += 1
                continue
            j = i + 1
            while j < n:
                if j >= n or toks[j].t == "(" or toks[j].k != "id" or es_kw(toks[j]):
                    break
                nombre, alias = toks[j].t.replace("`", ""), None
                nombre = re.sub(r"\s+", "", nombre)
                k = j + 1
                if k < n and toks[k].low == "as":
                    k += 1
                if k < n and toks[k].k == "id" and not es_kw(toks[k]) and "." not in toks[k].t \
                        and (k + 1 >= n or toks[k + 1].t != "("):
                    alias = toks[k].t.strip("`")
                    k += 1
                refs.append((nombre, alias, toks[j]))
                if t.low == "from" and k < n and toks[k].t == ",":
                    j = k + 1
                    continue
                break
        i += 1
    return refs, ctes


def analizar(q):
    """Estructura: tablas, ctes, cols (por tabla), ambiguas, estrella, usos, hints."""
    toks = tokenizar(q)
    refs, ctes = _tablas(toks)
    tablas = [{"nombre": n, "alias": a, "tok": t} for n, a, t in refs if n.lower() not in ctes]
    alias_map = {}
    for t in tablas:
        low = t["nombre"].lower()
        alias_map[low] = low
        alias_map[low.split(".")[-1]] = low
        if t["alias"]:
            alias_map[t["alias"].lower()] = low
    reales = []
    for t in tablas:
        if t["nombre"].lower() not in reales:
            reales.append(t["nombre"].lower())
    pos_tabla = set(id(t["tok"]) for t in tablas)
    pos_alias = set()
    for n, a, tk in refs:
        if a:
            idx = toks.index(tk)
            for k in range(idx + 1, min(idx + 3, len(toks))):
                if toks[k].t.strip("`") == a:
                    pos_alias.add(id(toks[k]))
    cols = {}
    ambiguas = []
    estrella = set()
    usos = {}

    def _col(tabla, c):
        c = c.strip("`")
        if not c or c.lower() in KW:
            return
        if tabla is None:
            if len(reales) == 1:
                tabla = reales[0]
            else:
                if c not in ambiguas:
                    ambiguas.append(c)
                return
        lst = cols.setdefault(tabla, [])
        if c not in lst and c.lower() not in [x.lower() for x in lst]:
            lst.append(c)

    n = len(toks)
    for i, t in enumerate(toks):
        if t.k == "op" and t.t == "*" and (i == 0 or toks[i - 1].low in ("select", ",", "distinct") or toks[i - 1].t == "("):
            if i + 1 < n and toks[i + 1].low in ("from", ",") or i + 1 >= n:
                estrella.add("*")
            continue
        if t.k != "id" or id(t) in pos_tabla or id(t) in pos_alias or es_kw(t):
            continue
        sig = toks[i + 1] if i + 1 < n else None
        ant = toks[i - 1] if i else None
        if sig is not None and sig.t == "(" and "." not in t.t:
            continue       # funcion
        if ant is not None and ant.low == "as":
            continue       # alias o tipo
        if ant is not None and ant.low in ("from", "join"):
            continue
        if t.low in ("true", "false", "null"):
            continue
        ps = partes_id(t.t)
        if ps[-1] == "*":
            tab = alias_map.get(ps[0].lower()) or alias_map.get(".".join(ps[:-1]).lower())
            estrella.add(tab or "*")
            continue
        if len(ps) == 1:
            _col(None, ps[0])
            nombre_col, tabla = ps[0], None
        else:
            tabla = alias_map.get(ps[0].lower()) or alias_map.get(".".join(ps[:-1]).lower())
            if tabla is None:
                continue     # struct.campo u otra cosa: no es columna de una tabla conocida
            _col(tabla, ps[-1])
            nombre_col = ps[-1]
        # usos por contexto (CAST(x AS tipo), SUM(x))
        if ant is not None and ant.t == "(" and i >= 2 and toks[i - 2].low in FN_NUM:
            usos.setdefault(nombre_col.lower(), set()).add("num")
        if ant is not None and ant.t == "(" and i >= 2 and toks[i - 2].low == "cast" \
                and i + 2 < n and toks[i + 1].low == "as":
            tipo = toks[i + 2].low
            usos.setdefault(nombre_col.lower(), set()).add("num" if tipo in TIPOS_NUM else
                                                           ("date" if tipo in ("date", "timestamp") else "str"))
    # columnas que se igualan entre si (ON a.k = b.k / WHERE a.k = b.k): claves de join
    for i in range(1, n - 1):
        if toks[i].k == "op" and toks[i].t in ("=", "==") and toks[i - 1].k == "id" and toks[i + 1].k == "id" \
                and not es_kw(toks[i - 1]) and not es_kw(toks[i + 1]) \
                and not (i + 2 < n and toks[i + 2].t == "(") and "." in (toks[i - 1].t + toks[i + 1].t):
            for tk in (toks[i - 1], toks[i + 1]):
                usos.setdefault(partes_id(tk.t)[-1].lower(), set()).add("key")
    return {"toks": toks, "tablas": tablas, "ctes": ctes, "cols": cols, "ambiguas": ambiguas,
            "estrella": estrella, "usos": usos, "alias_map": alias_map, "reales": reales,
            "hints": _hints(toks, alias_map, reales)}


def _sumar(h, op, v):
    if op in ("=", "=="):
        h.setdefault("eq", []).append(v)
    elif op == ">=":
        h["ge"] = v
    elif op == ">":
        h["gt"] = v
    elif op == "<=":
        h["le"] = v
    elif op == "<":
        h["lt"] = v


def _hints(toks, alias_map, reales):
    """Condiciones col <op> literal / IN / BETWEEN / LIKE / IS NULL despues de WHERE (cualquier nivel)."""
    h = {}
    n = len(toks)
    w = next((i for i, t in enumerate(toks) if t.k == "id" and t.low == "where"), None)
    if w is None:
        return h

    def _dest(t):
        ps = partes_id(t.t)
        if len(ps) == 1:
            return (reales[0] if len(reales) == 1 else None), ps[0].lower()
        tab = alias_map.get(ps[0].lower()) or alias_map.get(".".join(ps[:-1]).lower())
        return tab, ps[-1].lower()
    i = w + 1
    while i < n:
        t = toks[i]
        if t.k == "id" and not es_kw(t) and t.low != "null" and not (i + 1 < n and toks[i + 1].t == "("):
            nxt = toks[i + 1] if i + 1 < n else None
            if nxt is not None:
                key = _dest(t)
                d = h.setdefault(key, {})
                if nxt.k == "op" and nxt.t in OPS and i + 2 < n:
                    sgn, k = 1, i + 2
                    if toks[k].t == "-" and k + 1 < n:
                        sgn, k = -1, k + 1
                    v = literal(toks[k])
                    if v is not None:
                        op = {"<>": "ne", "!=": "ne"}.get(nxt.t, nxt.t)
                        if op != "ne":
                            _sumar(d, op, v * sgn if isinstance(v, (int, float)) else v)
                elif nxt.low == "in" and i + 2 < n and toks[i + 2].t == "(":
                    vals, k = [], i + 3
                    while k < n and toks[k].t != ")":
                        v = literal(toks[k])
                        if v is not None:
                            vals.append(v)
                        elif toks[k].t != ",":
                            vals = []
                            break
                        k += 1
                    if vals:
                        d.setdefault("eq", []).extend(vals)
                elif nxt.low == "between" and i + 4 < n and toks[i + 3].low == "and":
                    a, b = literal(toks[i + 2]), literal(toks[i + 4])
                    if a is not None and b is not None:
                        d["ge"], d["le"] = a, b
                elif nxt.low == "like" and i + 2 < n and toks[i + 2].k == "str":
                    d["like"] = literal(toks[i + 2])
                elif nxt.low == "is" and i + 2 < n and toks[i + 2].low == "null":
                    d["null"] = True
                if not d:
                    h.pop(key, None)
        i += 1
    return h


def reescribir(q, reemplazos):
    """Cambia los tokens de tabla por otros nombres. reemplazos: [(Tok, nuevo)]."""
    for tk, nuevo in sorted(reemplazos, key=lambda r: -r[0].s):
        q = q[:tk.s] + nuevo + q[tk.e:]
    return q


def ids_expresion(expr):
    """Columnas (nombres simples) de una expresion SQL suelta ('CAST(x AS INT) as y', 'a + b > 0')."""
    info = analizar("select " + str(expr) + " from __t__")
    out = []
    for c in info["cols"].get("__t__", []):
        out.append(c)
    return out


def separar_select(txt):
    """Divide una lista de select 'a, cast(b as int) as c' por comas de nivel 0."""
    partes, nivel, cur = [], 0, []
    for ch in str(txt):
        if ch == "(":
            nivel += 1
        elif ch == ")":
            nivel -= 1
        if ch == "," and nivel == 0:
            partes.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        partes.append("".join(cur).strip())
    return [p for p in partes if p]
