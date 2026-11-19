# py2spark.pandas_ops — traducciones NATIVAS pandas -> PySpark (sin pandas, sin UDF).
#
# Todo lo que se emite aqui es PySpark puro: funciones de columna (F.*), Window,
# groupBy/agg/pivot/unpivot/join. NUNCA se emite pandas_udf/udf/toPandas/collect para
# logica fila a fila. Lo que no tiene equivalente nativo lanza `Untr`: el conversor lo
# deja como "# TODO py2spark" con el fragmento original y una alternativa sugerida.
#
# Diferencias INEVITABLES pandas vs Spark (se documentan en los TODO/warnings):
#   * pandas tiene indice de fila y orden; Spark no. Las operaciones que dependen del
#     orden (shift/cumsum/rolling/ffill/rank 'first') usan F.monotonically_increasing_id()
#     como orden de aparicion; sin un orderBy previo el orden de lectura no esta garantizado.
#   * NaN vs null: pandas usa NaN en flotantes; aqui NaN se trata como null (np.nan -> null).
#   * Division entre cero: pandas da inf/NaN; Spark (ANSI off) da null; (ANSI on) error.
#   * merge/join: pandas empareja claves NaN entre si; Spark no.
import ast
import copy
import re


class Untr(Exception):
    """Construccion sin equivalente nativo: se emite como TODO con alternativa."""

    def __init__(self, msg, hint=None):
        Exception.__init__(self, msg)
        self.msg = msg
        self.hint = hint


# --------------------------- constructores de AST ---------------------------

def tpl(src, **sub):
    """Parsea una expresion y sustituye los Name (_c, _w...) por copias de nodos."""
    tree = ast.parse(src, mode="eval").body

    class _R(ast.NodeTransformer):
        def visit_Name(self, n):
            if n.id in sub:
                return copy.deepcopy(sub[n.id])
            return n
    return _R().visit(tree)


def K(v):
    return ast.Constant(v)


def N(i):
    return ast.Name(i, ast.Load())


def call(func, *args, **kw):
    return ast.Call(func=func, args=list(args),
                    keywords=[ast.keyword(arg=k, value=v) for k, v in kw.items()])


def meth(recv, name, *args, **kw):
    return call(ast.Attribute(value=recv, attr=name, ctx=ast.Load()), *args, **kw)


def Fn(name, *args):
    return meth(N("F"), name, *args)


def lit(node):
    """F.lit() solo si es una constante Python; las columnas se dejan."""
    if isinstance(node, ast.Constant):
        return Fn("lit", node)
    return node


def unslice(n):
    """Subscript.slice sin ast.Index (Python 3.8)."""
    s = n.slice
    if s.__class__.__name__ == "Index":
        s = s.value
    return s


def const(node, kinds=(str, int, float, bool, type(None))):
    if isinstance(node, ast.Constant) and isinstance(node.value, kinds):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) \
            and isinstance(node.operand, ast.Constant) and isinstance(node.operand.value, (int, float)):
        return True
    return False


def cval(node):
    if isinstance(node, ast.UnaryOp):
        return -node.operand.value
    return node.value


def win(part, order=None, frame=None):
    """Window.partitionBy(*part)[.orderBy(...)][.rowsBetween(a, b)].
    order: None (sin orden), True (orden de aparicion) o un nodo de columna."""
    w = meth(N("Window"), "partitionBy", *part)
    if order is True:
        w = meth(w, "orderBy", Fn("monotonically_increasing_id"))
    elif order is not None and order is not False:
        w = meth(w, "orderBy", order)
    if frame:
        def _b(x):
            if isinstance(x, str):
                return ast.Attribute(value=N("Window"), attr=x, ctx=ast.Load())
            return K(x)
        w = meth(w, "rowsBetween", _b(frame[0]), _b(frame[1]))
    return w


# --------------------------- tablas ---------------------------

# agregacion pandas -> plantilla F (sobre _c).
RED = {
    "sum": "F.sum(_c)", "mean": "F.avg(_c)", "avg": "F.avg(_c)", "min": "F.min(_c)",
    "max": "F.max(_c)", "std": "F.stddev_samp(_c)", "var": "F.var_samp(_c)",
    "median": "F.median(_c)", "count": "F.count(_c)", "nunique": "F.countDistinct(_c)",
    "prod": "F.product(_c)", "first": "F.first(_c, True)", "last": "F.last(_c, True)",
    "size": "F.count(F.lit(1))",
}
# nombres que aceptan "any"/"all" (bool) en agregacion
RED_BOOL = {"any": "(F.max(_c.cast('int')) == 1)", "all": "(F.min(_c.cast('int')) == 1)"}

# funciones matematicas elementwise numpy/math -> F.
MATH = {"log": "log", "log1p": "log1p", "log10": "log10", "log2": "log2", "exp": "exp",
        "expm1": "expm1", "sqrt": "sqrt", "abs": "abs", "floor": "floor", "ceil": "ceil",
        "sin": "sin", "cos": "cos", "tan": "tan", "arcsin": "asin", "arccos": "acos",
        "arctan": "atan", "tanh": "tanh", "sign": "signum", "fabs": "abs", "asin": "asin",
        "acos": "acos", "atan": "atan"}

# Pandas strftime -> patron Java (date_format)
_STRF = {"%Y": "yyyy", "%y": "yy", "%m": "MM", "%d": "dd", "%H": "HH", "%M": "mm",
         "%S": "ss", "%b": "MMM", "%B": "MMMM", "%a": "EEE", "%A": "EEEE", "%j": "DDD",
         "%f": "SSSSSS", "%p": "a", "%I": "hh"}

DT_PROPS = {
    "year": "F.year(_c)", "month": "F.month(_c)", "day": "F.dayofmonth(_c)",
    "hour": "F.hour(_c)", "minute": "F.minute(_c)", "second": "F.second(_c)",
    "quarter": "F.quarter(_c)", "dayofyear": "F.dayofyear(_c)",
    "weekofyear": "F.weekofyear(_c)", "week": "F.weekofyear(_c)",
    # pandas: lunes=0 .. domingo=6 ; Spark dayofweek: domingo=1 .. sabado=7
    "dayofweek": "((F.dayofweek(_c) + 5) % 7)", "weekday": "((F.dayofweek(_c) + 5) % 7)",
    "date": "F.to_date(_c)",
    "is_month_end": "(F.to_date(_c) == F.last_day(_c))",
    "is_month_start": "(F.dayofmonth(_c) == 1)",
}


def java_regex_repl(repl):
    """Reemplazo de re.sub de Python (\\1) -> Spark (\\$1); escapa $ y \\ literales."""
    out = []
    i = 0
    while i < len(repl):
        ch = repl[i]
        if ch == "\\" and i + 1 < len(repl) and repl[i + 1].isdigit():
            out.append("$" + repl[i + 1])
            i += 2
            continue
        if ch == "$":
            out.append("\\$")
        elif ch == "\\":
            out.append("\\\\")
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def java_literal_repl(repl):
    return repl.replace("\\", "\\\\").replace("$", "\\$")


def strftime_to_java(fmt):
    out, i = [], 0
    while i < len(fmt):
        if fmt[i] == "%" and fmt[i:i + 2] in _STRF:
            out.append(_STRF[fmt[i:i + 2]])
            i += 2
        elif fmt[i] == "%":
            raise Untr("strftime con formato '%s' sin equivalente en date_format" % fmt[i:i + 2],
                       "usa F.date_format(col, 'patron Java') (https://spark.apache.org/docs/latest/sql-ref-datetime-pattern.html)")
        elif fmt[i].isalpha():
            out.append("'" + fmt[i] + "'")
            i += 1
        else:
            out.append(fmt[i])
            i += 1
    return "".join(out)


# --------------------------- mixin ---------------------------

class PandasOps(object):
    """Metodos de traduccion; se mezcla con PandasToSparkTransformer."""

    # ---- helpers de arg ----
    @staticmethod
    def _arg(args, kw, i, name, default=None):
        if len(args) > i:
            return args[i]
        for k in kw:
            if k.arg == name:
                return k.value
        return default

    def _is_col(self, n):
        """True si el nodo (ya convertido) es una expresion de Column de Spark."""
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute):
                if isinstance(f.value, ast.Name) and f.value.id == "F":
                    return True
                return self._is_col(f.value) and not self._is_df(f.value)
            return False
        if isinstance(n, ast.BinOp):
            return self._is_col(n.left) or self._is_col(n.right)
        if isinstance(n, ast.UnaryOp):
            return self._is_col(n.operand)
        if isinstance(n, ast.Compare):
            return self._is_col(n.left) or any(self._is_col(c) for c in n.comparators)
        if isinstance(n, ast.BoolOp):
            return any(self._is_col(v) for v in n.values)
        if isinstance(n, ast.Attribute) and n.attr in ("str", "dt"):
            return self._is_col(n.value)
        if isinstance(n, ast.Subscript):
            return self._is_col(n.value)
        return False

    # =========================== Series ===========================
    def series_method(self, c, m, args, kw, part=None):
        """Traduce <Series>.<m>(...) sobre la columna `c`. part: nodos de particion
        (groupby) o None. Devuelve un nodo Column o lanza Untr."""
        P = list(part or [])
        A = lambda i, n, d=None: self._arg(args, kw, i, n, d)  # noqa: E731

        if m in RED:
            return meth(tpl(RED[m], _c=c), "over", win(P))
        if m in RED_BOOL:
            fn = "max" if m == "any" else "min"
            return tpl("(F.%s(_c.cast('int')).over(_w) == 1)" % fn, _c=c, _w=win(P))
        if m in ("cumsum", "cummax", "cummin", "cumprod"):
            fn = {"cumsum": "sum", "cummax": "max", "cummin": "min", "cumprod": "product"}[m]
            w = win(P, True, ("unboundedPreceding", "currentRow"))
            self.diag.warn("%s -> F.%s(...).over(Window...rowsBetween(unboundedPreceding, currentRow)): "
                           "usa el orden de aparicion (monotonically_increasing_id); ordena antes "
                           "con sort_values si importa." % (m, fn))
            return tpl("F.when(_c.isNotNull(), F.%s(_c).over(_w))" % fn, _c=c, _w=w)
        if m in ("shift", "diff", "pct_change"):
            nn = A(0, "periods", K(1))
            if not const(nn, (int,)):
                raise Untr("%s con periodos no literales" % m)
            n = cval(nn)
            w = win(P, True)
            if m == "shift":
                fv = A(1, "fill_value")
                fn = "lag" if n >= 0 else "lead"
                extra = [fv] if fv is not None else []
                return meth(Fn(fn, c, K(abs(n)), *extra), "over", w)
            lag = meth(Fn("lag", c, K(n)), "over", w)
            if m == "diff":
                return ast.BinOp(left=c, op=ast.Sub(), right=lag)
            return ast.BinOp(left=ast.BinOp(left=c, op=ast.Div(), right=lag), op=ast.Sub(), right=K(1))
        if m in ("ffill", "pad"):
            return meth(Fn("last", c, K(True)), "over", win(P, True, ("unboundedPreceding", "currentRow")))
        if m in ("bfill", "backfill"):
            return meth(Fn("first", c, K(True)), "over", win(P, True, ("currentRow", "unboundedFollowing")))
        if m == "rank":
            return self._rank(c, args, kw, P)
        if m == "fillna":
            v = A(0, "value")
            how = A(99, "method")
            if v is None and how is not None and const(how):
                return self.series_method(c, "ffill" if cval(how) in ("ffill", "pad") else "bfill", [], [], part)
            if v is None:
                raise Untr("fillna sin value")
            return Fn("coalesce", c, lit(v))
        if m in ("isna", "isnull"):
            return meth(c, "isNull")
        if m in ("notna", "notnull"):
            return meth(c, "isNotNull")
        if m == "isin":
            v = A(0, "values")
            return meth(c, "isin", v)
        if m == "between":
            ncl = A(2, "inclusive")
            inc = cval(ncl) if ncl is not None and const(ncl) else "both"
            lo, hi = A(0, "left"), A(1, "right")
            if inc == "both":
                return meth(c, "between", lo, hi)
            ge = ast.Compare(left=c, ops=[ast.GtE() if inc in ("both", "left") else ast.Gt()], comparators=[lo])
            le = ast.Compare(left=c, ops=[ast.LtE() if inc in ("both", "right") else ast.Lt()], comparators=[hi])
            return ast.BinOp(left=ge, op=ast.BitAnd(), right=le)
        if m == "abs":
            return Fn("abs", c)
        if m == "round":
            return Fn("bround", c, A(0, "decimals", K(0)))   # numpy/pandas redondean half-even
        if m == "clip":
            lo, hi = A(0, "lower"), A(1, "upper")
            e = c
            if lo is not None and not (isinstance(lo, ast.Constant) and lo.value is None):
                e = Fn("greatest", e, lit(lo))
            if hi is not None and not (isinstance(hi, ast.Constant) and hi.value is None):
                e = Fn("least", e, lit(hi))
            return e
        if m == "where":
            other = A(1, "other")
            return meth(Fn("when", A(0, "cond"), c), "otherwise", lit(other) if other is not None else Fn("lit", K(None)))
        if m == "mask":
            other = A(1, "other")
            return meth(Fn("when", A(0, "cond"), lit(other) if other is not None else Fn("lit", K(None))), "otherwise", c)
        if m == "replace":
            return self._replace(c, args, kw)
        if m in ("map", "apply", "transform", "applymap"):
            return self._map_apply(c, m, args, kw, P)
        if m in ("eq", "ne", "lt", "le", "gt", "ge"):
            op = {"eq": ast.Eq, "ne": ast.NotEq, "lt": ast.Lt, "le": ast.LtE, "gt": ast.Gt, "ge": ast.GtE}[m]()
            return ast.Compare(left=c, ops=[op], comparators=[args[0]])
        if m in ("add", "sub", "mul", "div", "truediv"):
            op = {"add": ast.Add, "sub": ast.Sub, "mul": ast.Mult, "div": ast.Div, "truediv": ast.Div}[m]()
            return ast.BinOp(left=c, op=op, right=args[0])
        if m == "nlargest" or m == "nsmallest":
            raise Untr("Series.%s" % m, "usa df.orderBy(col.desc()).limit(n)")
        if m in ("tolist", "to_list", "to_numpy", "values"):
            raise Untr("Series.%s() trae la columna completa al driver" % m,
                       "mantén el dato en Spark; si es un escalar pequeño usa df.select(...).first()[0]")
        raise Untr("Series.%s(...) sin traduccion nativa" % m,
                   "reescribe con funciones de columna F.* o F.expr('SQL'); no se emite UDF/pandas_udf")

    # ---- rank ----
    def _rank(self, c, args, kw, P):
        mn = self._arg(args, kw, 0, "method", K("average"))
        asc = self._arg(args, kw, 2, "ascending", K(True))
        pct = self._arg(args, kw, 99, "pct")
        if pct is not None and not (isinstance(pct, ast.Constant) and pct.value is False):
            raise Untr("rank(pct=True)", "usa F.percent_rank().over(Window.orderBy(col))")
        method = cval(mn) if const(mn) else "average"
        asc_v = not (isinstance(asc, ast.Constant) and asc.value is False)
        order = meth(c, "asc_nulls_last" if asc_v else "desc_nulls_last")
        w = win(P, order)
        if method == "dense":
            r = meth(Fn("dense_rank"), "over", w)
        elif method == "first":
            r = meth(Fn("row_number"), "over", win(P, order))
            w2 = meth(win(P, order), "orderBy", order, Fn("monotonically_increasing_id"))
            r = meth(Fn("row_number"), "over", w2)
        else:
            r = meth(Fn("rank"), "over", w)
            if method in ("average", "max"):
                cnt = meth(Fn("count", Fn("lit", K(1))), "over", win(P + [c]))
                add = ast.BinOp(left=cnt, op=ast.Sub(), right=K(1))
                if method == "average":
                    add = ast.BinOp(left=add, op=ast.Div(), right=K(2.0))
                r = ast.BinOp(left=r, op=ast.Add(), right=add)
            elif method != "min":
                raise Untr("rank(method=%r)" % method)
        return meth(Fn("when", meth(c, "isNotNull"), r), "otherwise", Fn("lit", K(None)))

    # ---- replace ----
    def _replace(self, c, args, kw):
        a = self._arg(args, kw, 0, "to_replace")
        b = self._arg(args, kw, 1, "value")
        pairs = []
        if isinstance(a, ast.Dict):
            pairs = list(zip(a.keys, a.values))
        elif isinstance(a, (ast.List, ast.Tuple)) and isinstance(b, (ast.List, ast.Tuple)):
            pairs = list(zip(a.elts, b.elts))
        elif isinstance(a, (ast.List, ast.Tuple)) and b is not None:
            pairs = [(x, b) for x in a.elts]
        elif a is not None and b is not None:
            pairs = [(a, b)]
        else:
            raise Untr("replace con forma no literal")
        return self._when_chain(c, pairs, c)

    def _when_chain(self, c, pairs, otherwise):
        """F.when(c == k1, v1).when(c == k2, v2)....otherwise(...)  (otherwise None = null)."""
        e = None
        for k, v in pairs:
            if isinstance(k, ast.Constant) and k.value is None:
                cond = meth(c, "isNull")
            else:
                cond = ast.Compare(left=c, ops=[ast.Eq()], comparators=[k])
            e = Fn("when", cond, lit(v)) if e is None else meth(e, "when", cond, lit(v))
        if e is None:
            return otherwise
        if otherwise is not None:
            e = meth(e, "otherwise", otherwise)
        return e

    # ---- map / apply con lambdas, dicts o funciones simples ----
    def _map_apply(self, c, m, args, kw, P):
        f = self._arg(args, kw, 0, "arg") if m == "map" else self._arg(args, kw, 0, "func")
        if f is None:
            raise Untr("%s sin funcion" % m)
        if isinstance(f, ast.Dict) and m == "map":
            # Series.map(dict): clave sin match -> NaN (null)
            self.diag.warn("Series.map(dict) -> F.when(...).when(...) (sin otherwise: sin match = null, como NaN en pandas).")
            return self._when_chain(c, list(zip(f.keys, f.values)), None)
        series_mode = (m == "transform")
        if isinstance(f, ast.Constant) and isinstance(f.value, str) and m == "transform":
            return self.series_method(c, f.value, [], [], P)
        if isinstance(f, ast.Constant) and isinstance(f.value, str) and m == "apply":
            return self.series_method(c, f.value, [], [], P)
        if isinstance(f, ast.Lambda):
            if len(f.args.args) != 1:
                raise Untr("lambda con %d parametros" % len(f.args.args))
            env = {f.args.args[0].arg: c}
            return self.pyx(f.body, env, P, series_mode)
        fd = None
        if isinstance(f, ast.Name):
            fd = getattr(self, "simple_funcs", {}).get(f.id)
        if fd is not None:
            env = {fd[0]: c}
            return self.pyx(fd[1], env, P, series_mode)
        # funcion por nombre: np.log, str, len, abs, float, math.sqrt...
        x = N("__x")
        return self.pyx(ast.Call(func=f, args=[x], keywords=[]), {"__x": c}, P, series_mode)

    def apply_row(self, node_call, df_hint):
        """DataFrame.apply(lambda r: ..., axis=1)."""
        args, kw = node_call.args, node_call.keywords
        axis = self._arg(args, kw, 1, "axis")
        f = self._arg(args, kw, 0, "func")
        if not (axis is not None and const(axis) and cval(axis) in (1, "columns")):
            raise Untr("df.apply sin axis=1", "reescribe con F.* por columna")
        if isinstance(f, ast.Lambda) and len(f.args.args) == 1:
            return self.pyx(f.body, {f.args.args[0].arg: ("ROW",)}, [], False)
        if isinstance(f, ast.Name):
            fd = getattr(self, "simple_funcs", {}).get(f.id)
            if fd is not None:
                return self.pyx(fd[1], {fd[0]: ("ROW",)}, [], False)
        raise Untr("df.apply(axis=1) con funcion no simple")

    # ---- traductor de expresiones Python (cuerpo de lambda/funcion) -> Column ----
    def pyx(self, n, env, P, series_mode):
        T = lambda x: self.pyx(x, env, P, series_mode)  # noqa: E731
        if isinstance(n, ast.Constant):
            return n
        if isinstance(n, ast.Name):
            v = env.get(n.id)
            if v is None:
                return n            # variable libre (constante de cierre)
            if isinstance(v, tuple):
                raise Untr("la fila completa '%s' se usa sin indexar" % n.id)
            return v
        if isinstance(n, ast.BinOp):
            l, r = T(n.left), T(n.right)
            if isinstance(n.op, ast.FloorDiv):
                return Fn("floor", ast.BinOp(left=l, op=ast.Div(), right=r))
            if isinstance(n.op, ast.Pow):
                return Fn("pow", l, r)
            return ast.BinOp(left=l, op=n.op, right=r)
        if isinstance(n, ast.UnaryOp):
            if isinstance(n.op, ast.Not):
                return ast.UnaryOp(op=ast.Invert(), operand=T(n.operand))
            return ast.UnaryOp(op=n.op, operand=T(n.operand))
        if isinstance(n, ast.BoolOp):
            op = ast.BitAnd() if isinstance(n.op, ast.And) else ast.BitOr()
            e = T(n.values[0])
            for v in n.values[1:]:
                e = ast.BinOp(left=e, op=op, right=T(v))
            return e
        if isinstance(n, ast.IfExp):
            return meth(Fn("when", T(n.test), lit(T(n.body))), "otherwise", lit(T(n.orelse)))
        if isinstance(n, ast.Compare):
            if len(n.ops) != 1:
                raise Untr("comparacion encadenada")
            op, rhs = n.ops[0], n.comparators[0]
            l = T(n.left)
            if isinstance(op, (ast.In, ast.NotIn)):
                e = meth(l, "isin", T(rhs) if not isinstance(rhs, (ast.List, ast.Tuple, ast.Set)) else ast.List(elts=list(rhs.elts), ctx=ast.Load()))
                return ast.UnaryOp(op=ast.Invert(), operand=e) if isinstance(op, ast.NotIn) else e
            if isinstance(op, (ast.Is, ast.IsNot)):
                if isinstance(rhs, ast.Constant) and rhs.value is None:
                    return meth(l, "isNull" if isinstance(op, ast.Is) else "isNotNull")
                raise Untr("'is' con valor distinto de None")
            return ast.Compare(left=l, ops=[op], comparators=[T(rhs)])
        if isinstance(n, ast.Subscript):
            base = n.value
            sl = unslice(n)
            if isinstance(base, ast.Name) and isinstance(env.get(base.id), tuple):
                if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                    return Fn("col", sl)
                raise Untr("acceso a fila con clave no literal")
            b = T(base)
            if isinstance(sl, ast.Slice):
                lo = sl.lower.value if isinstance(sl.lower, ast.Constant) else (0 if sl.lower is None else None)
                hi = sl.upper.value if isinstance(sl.upper, ast.Constant) else (None if sl.upper is None else False)
                if lo is None or hi is False or (lo < 0 and hi is not None):
                    raise Untr("slice de cadena no literal")
                return Fn("substring", b, K(lo + 1 if lo >= 0 else lo),
                          K((hi - lo) if hi is not None else 2147483647))
            if isinstance(sl, ast.Constant) and isinstance(sl.value, int) and sl.value >= 0:
                return Fn("substring", b, K(sl.value + 1), K(1))
            raise Untr("indexacion no soportada")
        if isinstance(n, ast.Attribute):
            if isinstance(n.value, ast.Name) and isinstance(env.get(n.value.id), tuple):
                return Fn("col", K(n.attr))
            raise Untr("atributo .%s" % n.attr)
        if isinstance(n, ast.JoinedStr):
            parts = []
            for v in n.values:
                if isinstance(v, ast.Constant):
                    parts.append(Fn("lit", v))
                elif isinstance(v, ast.FormattedValue) and v.format_spec is None and v.conversion in (-1, 115):
                    parts.append(meth(T(v.value), "cast", K("string")))
                else:
                    raise Untr("f-string con formato")
            return Fn("concat", *parts)
        if isinstance(n, ast.Call):
            return self._pyx_call(n, env, P, series_mode)
        raise Untr("expresion %s sin equivalente" % n.__class__.__name__)

    def _pyx_call(self, n, env, P, series_mode):
        T = lambda x: self.pyx(x, env, P, series_mode)  # noqa: E731
        f = n.func
        if isinstance(f, ast.Name):
            nm = f.id
            if nm == "abs" and len(n.args) == 1:
                return Fn("abs", T(n.args[0]))
            if nm == "round" and n.args:
                return Fn("bround", T(n.args[0]), *(n.args[1:2] or [K(0)]))
            if nm == "len" and len(n.args) == 1:
                return Fn("length", T(n.args[0]))
            if nm == "str" and len(n.args) == 1:
                return meth(T(n.args[0]), "cast", K("string"))
            if nm == "int" and len(n.args) == 1:
                return meth(T(n.args[0]), "cast", K("bigint"))
            if nm == "float" and len(n.args) == 1:
                return meth(T(n.args[0]), "cast", K("double"))
            if nm == "bool" and len(n.args) == 1:
                return meth(T(n.args[0]), "cast", K("boolean"))
            if nm in ("min", "max") and len(n.args) >= 2:
                return Fn("least" if nm == "min" else "greatest", *[T(a) for a in n.args])
            fd = getattr(self, "simple_funcs", {}).get(nm)
            if fd is not None and len(n.args) == 1:
                return self.pyx(fd[1], {fd[0]: T(n.args[0])}, P, series_mode)
            raise Untr("llamada a '%s(...)' sin equivalente nativo" % nm)
        if isinstance(f, ast.Attribute):
            # np.log(x), math.sqrt(x), pd.isna(x)
            if isinstance(f.value, ast.Name) and f.value.id in ("np", "numpy", "math") and f.attr in MATH and n.args:
                return Fn(MATH[f.attr], T(n.args[0]))
            if isinstance(f.value, ast.Name) and f.value.id in ("pd", "pandas") and f.attr in ("isna", "isnull") and n.args:
                return meth(T(n.args[0]), "isNull")
            if isinstance(f.value, ast.Name) and f.value.id in ("pd", "pandas") and f.attr in ("notna", "notnull") and n.args:
                return meth(T(n.args[0]), "isNotNull")
            recv = T(f.value)
            if f.attr in ("upper", "lower", "strip", "lstrip", "rstrip", "title", "startswith", "endswith", "replace", "zfill", "isdigit", "capitalize"):
                if not self._is_col(recv):
                    raise Untr("metodo de cadena sobre valor no columna")
                args = [T(a) for a in n.args]
                return self.str_method(recv, {"isdigit": "isdigit"}.get(f.attr, f.attr), args, [], py=True)
            if series_mode and f.attr in set(RED) | {"cumsum", "shift", "rank", "diff"}:
                return self.series_method(recv, f.attr, [T(a) for a in n.args], [], P)
            raise Untr("metodo .%s(...) sin equivalente nativo" % f.attr)
        raise Untr("llamada no soportada")

    # =========================== accesor .str ===========================
    def str_method(self, c, m, args, kw, py=False):
        A = lambda i, n, d=None: self._arg(args, kw, i, n, d)  # noqa: E731
        if m == "upper":
            return Fn("upper", c)
        if m == "lower":
            return Fn("lower", c)
        if m in ("strip", "lstrip", "rstrip"):
            chars = A(0, "to_strip")
            if chars is not None and not (isinstance(chars, ast.Constant) and chars.value is None):
                if not (isinstance(chars, ast.Constant) and isinstance(chars.value, str)):
                    raise Untr("strip con caracteres no literales")
                cls = "[" + re.sub(r"([\]\\^-])", r"\\\1", chars.value) + "]+"
            else:
                cls = "\\s+"
            pat = {"strip": "^%s|%s$" % (cls, cls), "lstrip": "^%s" % cls, "rstrip": "%s$" % cls}[m]
            return Fn("regexp_replace", c, K(pat), K(""))
        if m in ("len",):
            return Fn("length", c)
        if m == "title":
            return Fn("initcap", c)
        if m == "capitalize":
            return Fn("concat", Fn("upper", Fn("substring", c, K(1), K(1))),
                      Fn("lower", Fn("substring", c, K(2), K(2147483647))))
        if m == "contains":
            pat = A(0, "pat")
            case = A(1, "case")
            regex = A(3, "regex")
            na = A(2, "na")
            is_regex = not (isinstance(regex, ast.Constant) and regex.value is False)
            nocase = isinstance(case, ast.Constant) and case.value is False
            if is_regex:
                if nocase:
                    if not (isinstance(pat, ast.Constant) and isinstance(pat.value, str)):
                        raise Untr("contains(case=False) con patron no literal")
                    e = meth(c, "rlike", K("(?i)" + pat.value))
                else:
                    e = meth(c, "rlike", pat)
            else:
                e = meth(Fn("lower", c), "contains", Fn("lower", pat)) if nocase else meth(c, "contains", pat)
            if na is not None and isinstance(na, ast.Constant) and na.value is not None:
                e = Fn("coalesce", e, Fn("lit", na))
            return e
        if m in ("startswith", "endswith"):
            return meth(c, m, A(0, "pat"))
        if m == "replace":
            pat, repl = A(0, "pat"), A(1, "repl")
            regex = A(3, "regex")
            is_regex = isinstance(regex, ast.Constant) and regex.value is True
            if py:      # str.replace de Python: literal
                is_regex = False
            if not (isinstance(pat, ast.Constant) and isinstance(repl, ast.Constant)
                    and isinstance(pat.value, str) and isinstance(repl.value, str)):
                raise Untr("str.replace con patron/reemplazo no literales")
            if is_regex:
                return Fn("regexp_replace", c, pat, K(java_regex_repl(repl.value)))
            return Fn("regexp_replace", c, K(re.escape(pat.value)), K(java_literal_repl(repl.value)))
        if m == "split":
            pat = A(0, "pat")
            regex = A(2, "regex")
            if pat is None:
                return Fn("split", Fn("trim", c), K("\\s+"))
            if isinstance(pat, ast.Constant) and isinstance(pat.value, str):
                is_regex = isinstance(regex, ast.Constant) and regex.value is True
                return Fn("split", c, K(pat.value if (is_regex or len(pat.value) > 1 and False) else re.escape(pat.value)))
            raise Untr("split con patron no literal")
        if m in ("slice",):
            a, b = A(0, "start"), A(1, "stop")
            lo = cval(a) if a is not None and const(a) else 0
            if b is None:
                return Fn("substring", c, K(lo + 1), K(2147483647))
            if const(b) and lo >= 0:
                return Fn("substring", c, K(lo + 1), K(cval(b) - lo))
            raise Untr("str.slice con limites no literales")
        if m == "zfill":
            return Fn("lpad", c, A(0, "width"), K("0"))
        if m == "pad":
            raise Untr("str.pad", "usa F.lpad/F.rpad")
        if m == "extract":
            pat = A(0, "pat")
            return meth(Fn("when", meth(c, "rlike", pat), Fn("regexp_extract", c, pat, K(1))), "otherwise", Fn("lit", K(None)))
        if m == "find":
            return ast.BinOp(left=Fn("instr", c, A(0, "sub")), op=ast.Sub(), right=K(1))
        if m in ("isdigit", "isnumeric"):
            return meth(c, "rlike", K("^[0-9]+$"))
        if m == "cat":
            raise Untr("str.cat", "usa F.concat / F.concat_ws")
        if m in ("get",):
            raise Untr("str.get", "usa col.getItem(i) sobre F.split(...)")
        raise Untr("Series.str.%s(...) sin traduccion nativa" % m, "usa F.regexp_*/F.expr('SQL')")

    # =========================== accesor .dt ===========================
    def dt_prop(self, c, name):
        if name in DT_PROPS:
            return tpl(DT_PROPS[name], _c=c)
        raise Untr("Series.dt.%s sin traduccion nativa" % name, "usa F.date_trunc/F.datediff/F.expr('SQL')")

    def dt_method(self, c, m, args, kw):
        if m == "strftime":
            fmt = self._arg(args, kw, 0, "date_format")
            if not (isinstance(fmt, ast.Constant) and isinstance(fmt.value, str)):
                raise Untr("strftime con formato no literal")
            return Fn("date_format", c, K(strftime_to_java(fmt.value)))
        if m == "normalize":
            return Fn("to_timestamp", Fn("to_date", c))
        if m in ("day_name",):
            return Fn("date_format", c, K("EEEE"))
        if m in ("month_name",):
            return Fn("date_format", c, K("MMMM"))
        raise Untr("Series.dt.%s(...) sin traduccion nativa" % m, "usa F.date_trunc/F.date_add/F.expr('SQL')")

    # =========================== cut / qcut ===========================
    def pd_cut(self, node):
        args, kw = node.args, node.keywords
        x = self._arg(args, kw, 0, "x")
        bins = self._arg(args, kw, 1, "bins")
        labels = self._arg(args, kw, 99, "labels")
        right = self._arg(args, kw, 99, "right")
        low = self._arg(args, kw, 99, "include_lowest")
        if not (isinstance(bins, (ast.List, ast.Tuple)) and all(const(e, (int, float)) for e in bins.elts)):
            raise Untr("pd.cut con bins no literales", "usa Bucketizer(splits=[...]) o F.when(...)")
        edges = [cval(e) for e in bins.elts]
        right_v = not (isinstance(right, ast.Constant) and right.value is False)
        low_v = isinstance(low, ast.Constant) and low.value is True
        n = len(edges) - 1
        if isinstance(labels, (ast.List, ast.Tuple)) and len(labels.elts) == n:
            lbl = list(labels.elts)
        elif isinstance(labels, ast.Constant) and labels.value is False:
            lbl = [K(i) for i in range(n)]
        elif labels is None:
            lbl = [K(("(%r, %r]" if right_v else "[%r, %r)") % (edges[i], edges[i + 1])) for i in range(n)]
            self.diag.warn("pd.cut sin labels: se emite el texto del intervalo (pandas devuelve Interval categorico).")
        else:
            raise Untr("pd.cut con labels no literales")
        e = None
        for i in range(n):
            lo, hi = K(edges[i]), K(edges[i + 1])
            if right_v:
                cl = ast.Compare(left=x, ops=[ast.GtE() if (i == 0 and low_v) else ast.Gt()], comparators=[lo])
                ch = ast.Compare(left=x, ops=[ast.LtE()], comparators=[hi])
            else:
                cl = ast.Compare(left=x, ops=[ast.GtE()], comparators=[lo])
                ch = ast.Compare(left=x, ops=[ast.LtE() if (i == n - 1 and low_v) else ast.Lt()], comparators=[hi])
            cond = ast.BinOp(left=cl, op=ast.BitAnd(), right=ch)
            e = Fn("when", cond, lbl[i]) if e is None else meth(e, "when", cond, lbl[i])
        return e

    def pd_qcut(self, node):
        args, kw = node.args, node.keywords
        x = self._arg(args, kw, 0, "x")
        q = self._arg(args, kw, 1, "q")
        labels = self._arg(args, kw, 2, "labels")
        if isinstance(q, ast.Constant) and isinstance(q.value, int) and q.value > 1:
            fr = [i / float(q.value) for i in range(1, q.value)]
            nb = q.value
        elif isinstance(q, (ast.List, ast.Tuple)) and all(const(e, (int, float)) for e in q.elts):
            allq = [cval(e) for e in q.elts]
            fr = allq[1:-1]
            nb = len(allq) - 1
        else:
            raise Untr("pd.qcut con q no literal", "usa Bucketizer + approxQuantile o percentile_approx")
        edges = meth(Fn("percentile_approx", x, ast.List(elts=[K(f) for f in fr], ctx=ast.Load()), K(1000000)),
                     "over", win([]))
        # indice de cubo = numero de bordes interiores estrictamente menores que x
        idx = None
        for i in range(len(fr)):
            term = Fn("when", ast.Compare(left=x, ops=[ast.Gt()], comparators=[meth(edges, "getItem", K(i))]), K(1))
            term = meth(term, "otherwise", K(0))
            idx = term if idx is None else ast.BinOp(left=idx, op=ast.Add(), right=term)
        self.diag.warn("pd.qcut -> percentile_approx(...) sobre toda la columna (Window sin particion: "
                       "pasa todo por una particion) con indice de cubo; los bordes son aproximados "
                       "(pandas interpola).")
        if isinstance(labels, (ast.List, ast.Tuple)) and len(labels.elts) == nb:
            arr = Fn("array", *[Fn("lit", e) for e in labels.elts])
            res = Fn("element_at", arr, meth(ast.BinOp(left=idx, op=ast.Add(), right=K(1)), "cast", K("int")))
        else:
            res = idx
            if labels is None:
                self.diag.warn("pd.qcut sin labels: se emite el indice del cubo 0..%d (pandas da Interval)." % (nb - 1))
        return meth(Fn("when", meth(x, "isNotNull"), res), "otherwise", Fn("lit", K(None)))
