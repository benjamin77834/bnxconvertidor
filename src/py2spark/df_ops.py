# py2spark.df_ops — traducciones de DataFrame / groupby / funciones pd.* y np.* a PySpark
# NATIVO (ver pandas_ops.py para Series). Mixin de PandasToSparkTransformer.
import ast
import copy

from .pandas_ops import (DT_PROPS, strftime_to_java, Untr, K, N, Fn, meth, tpl, unslice, const, cval, win, lit, RED,
                         MATH, call)
from ._unparse import unparse as _unparse

_SERIES_ONLY = {"cumsum", "cummax", "cummin", "cumprod", "shift", "diff", "pct_change", "rank",
                "ffill", "bfill", "fillna", "transform", "apply", "map"}

# pandas -> nombre de funcion de agregacion de plantilla RED
_AGG_ALIAS = {"mean": "mean", "avg": "mean", "sum": "sum", "min": "min", "max": "max", "std": "std",
              "var": "var", "median": "median", "count": "count", "nunique": "nunique",
              "first": "first", "last": "last", "size": "size", "prod": "prod"}

_INPLACE_OK = {"dropna", "drop_duplicates", "fillna", "drop", "rename", "sort_values",
               "reset_index", "set_index", "replace", "astype"}

_RESIDUAL_ATTRS = {"toPandas", "to_pandas", "pandas_api", "applyInPandas", "mapInPandas",
                   "iloc", "loc", "to_numpy", "tolist", "iterrows", "itertuples",
                   "rolling", "expanding", "ewm"}


def _name_is_str(n):
    return isinstance(n, ast.Constant) and isinstance(n.value, str)


def _strs(n):
    """['a','b'] o 'a' -> lista de str; None si no es literal."""
    if _name_is_str(n):
        return [n.value]
    if isinstance(n, (ast.List, ast.Tuple)) and all(_name_is_str(e) for e in n.elts):
        return [e.value for e in n.elts]
    return None


class DfOps(object):

    # ------------------------------------------------------------------
    # envoltura por sentencia: Untr -> TODO; residuos pandas -> TODO
    # ------------------------------------------------------------------
    def visit(self, node):
        if isinstance(node, (ast.Assign, ast.Expr, ast.Return, ast.AugAssign)):
            try:
                orig = _unparse(copy.deepcopy(node))
            except Exception:
                orig = "<statement>"
            try:
                new = self._visit_stmt(node)
            except Untr as e:
                return self._todo_stmt(node, orig, e.msg, e.hint)
            if new is not None and not isinstance(new, list):
                res = self._residual(new)
                if res:
                    return self._todo_stmt(node, orig, "queda uso de pandas/numpy (%s) sin traduccion nativa" % res,
                                           "reescribe con funciones de columna F.* / Window / F.expr('SQL'); "
                                           "no se emite UDF ni pandas_udf")
            return new
        return ast.NodeTransformer.visit(self, node)

    def _visit_stmt(self, node):
        return ast.NodeTransformer.visit(self, node)

    def _residual(self, node):
        names = set(self.pandas_alias) | set(self.numpy_alias)
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and sub.id in names and isinstance(sub.ctx, ast.Load):
                return sub.id
            if isinstance(sub, ast.Attribute) and sub.attr in _RESIDUAL_ATTRS:
                return "." + sub.attr
        return None

    def _todo_stmt(self, node, orig, msg, hint):
        hint = hint or ("reescribe con funciones de columna F.* / Window / F.expr('SQL'); "
                        "no se emite UDF ni pandas_udf")
        self.diag.unsup("%s%s" % (msg, (" Alternativa: " + hint) if hint else ""))
        lines = ["TODO py2spark: no traducible a PySpark nativo: %s." % msg]
        if hint:
            lines.append("Alternativa sugerida: %s." % hint)
        lines.append("Original: %s" % orig.replace("\n", " "))
        if isinstance(node, ast.Assign):
            self._kill_targets(node)
        txt = self._comment_lines(lines)
        if isinstance(node, ast.Return):
            txt += "\nreturn None"
        self._mllib_seq += 1
        pid = "__PY2SPARK_MLLIB_%d__" % self._mllib_seq
        self.mllib_blocks[pid] = txt
        return ast.Expr(value=ast.Name(pid, ast.Load()))

    # ------------------------------------------------------------------
    # helpers df
    # ------------------------------------------------------------------
    def _keys(self, gb):
        by = gb.args[0] if gb.args else None
        if by is None:
            for k in gb.keywords:
                if k.arg in ("by", "level"):
                    by = k.value
        ks = _strs(by) if by is not None else None
        if ks is None:
            raise Untr("groupby por llaves no literales", "usa groupBy('col', ...) con nombres de columna")
        return ks

    def _gb_parse(self, node):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            return None
        base = node.func.value
        sel = None
        if isinstance(base, ast.Subscript):
            sel = unslice(base)
            base = base.value
        gb = None
        if isinstance(base, ast.Call) and isinstance(base.func, ast.Attribute) \
                and base.func.attr == "groupby" and self._is_df(base.func.value):
            gb = base
        elif isinstance(base, ast.Name) and base.id in self.gb_vars:
            gb = self.gb_vars[base.id]
        if gb is None:
            return None
        return gb, sel, node.func.attr, node

    def _agg_one(self, fn, col, alias):
        """F.<fn>(col).alias(alias). sum/avg/std/var castean a double (pandas suma booleanos)."""
        name = _AGG_ALIAS.get(fn)
        if name is None:
            raise Untr("agregacion '%s' sin equivalente nativo" % fn,
                       "usa F.expr('...') o una combinacion de F.* + Window")
        colnode = Fn("col", K(col))
        if name in ("sum", "mean", "std", "var"):
            colnode = meth(colnode, "cast", K("double"))
        return meth(tpl(RED[name], _c=colnode), "alias", K(alias))

    def _gb_translate(self, info, name=None):
        gb, sel, m, c = info
        df = self.visit(gb.func.value)
        keys = self._keys(gb)
        key_nodes = [K(k) for k in keys]
        args = [self.visit(copy.deepcopy(a)) for a in c.args]
        kw = [ast.keyword(arg=k.arg, value=self.visit(copy.deepcopy(k.value))) for k in c.keywords]
        grouped = meth(df, "groupBy", *key_nodes)
        sels = _strs(sel) if sel is not None else None
        if sel is not None and sels is None:
            raise Untr("seleccion de columnas de groupby no literal")

        # --- columna alineada (devuelve Column, para usar en withColumn) ---
        if m in _SERIES_ONLY and m not in ("apply", "map"):
            if not sels or len(sels) != 1:
                raise Untr("groupby(...).%s() sin una columna seleccionada" % m,
                           "selecciona una columna: df.groupby(k)['col'].%s()" % m)
            return self.series_method(Fn("col", K(sels[0])), m, args, kw, key_nodes)
        if m in ("apply", "filter", "pipe", "rolling", "expanding", "ewm", "head", "tail",
                 "nth", "ngroup", "cumcount"):
            raise Untr("groupby(...).%s(...) no tiene traduccion nativa automatica" % m,
                       "usa Window.partitionBy(...) con F.* o groupBy().agg(F.expr('...'))")

        # --- agregacion ---
        if m in ("agg", "aggregate"):
            aggs = self._gb_agg_args(args, kw, c, sels, name)
            return meth(grouped, "agg", *aggs)
        fn = _AGG_ALIAS.get(m)
        if fn is not None:
            if m == "size":
                return meth(grouped, "agg", meth(Fn("count", Fn("lit", K(1))), "alias", K(name or "size")))
            if sels:
                aggs = [self._agg_one(fn, s, (name if (name and len(sels) == 1) else s)) for s in sels]
                return meth(grouped, "agg", *aggs)
            self.needs_groupagg_helper = True
            return call(N("_py2spark_groupagg"), df, ast.List(elts=key_nodes, ctx=ast.Load()), K(fn))
        raise Untr("groupby(...).%s(...)" % m)

    def _gb_agg_args(self, args, kw, orig, sels, name):
        out = []
        spec = args[0] if args else None
        named = [k for k in kw if k.arg not in ("axis",)]
        if spec is not None and isinstance(spec, ast.Dict):
            for k, v in zip(spec.keys, spec.values):
                if not _name_is_str(k):
                    raise Untr("agg con clave no literal")
                fns = [v] if _name_is_str(v) else (v.elts if isinstance(v, (ast.List, ast.Tuple)) else None)
                if fns is None or not all(_name_is_str(x) for x in fns):
                    raise Untr("agg con funcion no literal (lambda/callable)",
                               "usa F.expr('SQL') o agregaciones F.*")
                for x in fns:
                    alias = k.value if (len(fns) == 1 and not isinstance(v, (ast.List, ast.Tuple))) \
                        else "%s_%s" % (k.value, x.value)
                    out.append(self._agg_one(x.value, k.value, alias))
            return out
        if spec is not None and sels:
            fns = [spec] if _name_is_str(spec) else (spec.elts if isinstance(spec, (ast.List, ast.Tuple)) else None)
            if fns is None or not all(_name_is_str(x) for x in fns):
                raise Untr("agg con funcion no literal (lambda/callable)")
            for s in sels:
                for x in fns:
                    alias = (name or s) if (len(fns) == 1 and not isinstance(spec, (ast.List, ast.Tuple))) \
                        else (x.value if len(sels) == 1 else "%s_%s" % (s, x.value))
                    out.append(self._agg_one(x.value, s, alias))
            return out
        if named and spec is None:
            for k in named:
                v = k.value
                if isinstance(v, (ast.Tuple, ast.List)) and len(v.elts) == 2 and _name_is_str(v.elts[0]) \
                        and _name_is_str(v.elts[1]):
                    out.append(self._agg_one(v.elts[1].value, v.elts[0].value, k.arg))
                elif isinstance(v, ast.Call) and isinstance(v.func, (ast.Attribute, ast.Name)) \
                        and getattr(v.func, "attr", getattr(v.func, "id", "")) == "NamedAgg":
                    cc = _strs(v.keywords[0].value) if v.keywords else None
                    vv = [x for x in v.args] + [k2.value for k2 in v.keywords]
                    if len(vv) == 2 and _name_is_str(vv[0]) and _name_is_str(vv[1]):
                        out.append(self._agg_one(vv[1].value, vv[0].value, k.arg))
                    else:
                        raise Untr("NamedAgg no literal")
                else:
                    raise Untr("agregacion nombrada con callable/lambda",
                               "usa F.expr('SQL') o agregaciones F.*")
            return out
        raise Untr("agg con forma no soportada")

    # ------------------------------------------------------------------
    # pre-dispatch de Call (ANTES de visitar hijos)
    # ------------------------------------------------------------------
    def pre_call(self, node):
        f = node.func
        if not isinstance(f, ast.Attribute):
            return None
        # groupby(...)... .reset_index(name=) / .sort_values() sobre el resultado
        if f.attr == "reset_index":
            inner = self._gb_parse(f.value)
            if inner is not None and inner[2] not in _SERIES_ONLY:
                nm = None
                for k in node.keywords:
                    if k.arg == "name" and _name_is_str(k.value):
                        nm = k.value.value
                    if k.arg == "drop" and isinstance(k.value, ast.Constant) and k.value.value:
                        raise Untr("reset_index(drop=True) tras groupby (descarta las llaves)")
                return self._gb_translate(inner, nm)
        if f.attr == "sort_values" and not node.args and not any(k.arg == "by" for k in node.keywords):
            inner = self._gb_parse(f.value)
            if inner is not None and inner[1] is not None and _name_is_str(inner[1]):
                col = inner[1].value
                res = self._gb_translate(inner)
                asc = [k.value for k in node.keywords if k.arg == "ascending"]
                desc = bool(asc and isinstance(asc[0], ast.Constant) and asc[0].value is False)
                o = meth(Fn("col", K(col)), "desc" if desc else "asc_nulls_last")
                return meth(res, "orderBy", o)
        inner = self._gb_parse(node)
        if inner is not None:
            return self._gb_translate(inner)
        # df["x"].value_counts() / unique() / nunique() escalar
        v = f.value
        if isinstance(v, ast.Subscript) and self._is_df(v.value) and _name_is_str(unslice(v)):
            col = unslice(v).value
            df = self.visit(v.value)
            if f.attr == "value_counts":
                dropna = [k.value for k in node.keywords if k.arg == "dropna"]
                norm = [k.value for k in node.keywords if k.arg == "normalize"]
                base = df
                if not (dropna and isinstance(dropna[0], ast.Constant) and dropna[0].value is False):
                    base = meth(df, "filter", meth(Fn("col", K(col)), "isNotNull"))
                res = meth(meth(base, "groupBy", K(col)), "count")
                if norm and isinstance(norm[0], ast.Constant) and norm[0].value is True:
                    res = meth(meth(res, "withColumn", K("proportion"),
                                    tpl("F.col('count') / F.sum('count').over(Window.partitionBy())")), "drop", K("count"))
                    return meth(res, "orderBy", meth(Fn("col", K("proportion")), "desc"), Fn("col", K(col)))
                self.diag.warn("value_counts() -> groupBy(col).count() ordenado por conteo desc y luego por valor "
                               "(pandas conserva el orden de aparicion en empates).")
                return meth(res, "orderBy", meth(Fn("col", K("count")), "desc"), Fn("col", K(col)))
            if f.attr == "unique":
                self.diag.warn("Series.unique() -> df.select(col).distinct() (DataFrame, no array numpy).")
                return meth(meth(df, "select", Fn("col", K(col))), "distinct")
        return None

    # ------------------------------------------------------------------
    # post-dispatch de Call (hijos ya visitados)
    # ------------------------------------------------------------------
    def post_call(self, node):
        f = node.func
        args, kw = node.args, node.keywords
        # ---- pd.<fn>(...) ----
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in self.pandas_alias:
            return self._pd_func(node, f.attr)
        # ---- np.<fn>(...) adicionales ----
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in self.numpy_alias:
            return self._np_extra(node, f.attr)
        if not isinstance(f, ast.Attribute):
            return None
        recv = f.value
        # ---- df.shape / len ya existen; df.columns.tolist() ----
        if f.attr == "tolist" and isinstance(recv, ast.Attribute) and recv.attr == "columns" and self._is_df(recv.value):
            return call(N("list"), recv)
        # ---- rolling(w).<agg>() ----
        if isinstance(recv, ast.Call) and isinstance(recv.func, ast.Attribute) and recv.func.attr == "rolling" \
                and self._is_col(recv.func.value):
            return self._rolling(recv, f.attr, node)
        if f.attr in ("rolling", "expanding", "ewm") and self._is_col(recv):
            return None
        # ---- .str.<m>() / .dt.<m>() ----
        if isinstance(recv, ast.Attribute) and recv.attr in ("str", "dt") and self._is_col(recv.value):
            if recv.attr == "str":
                return self.str_method(recv.value, f.attr, args, kw)
            return self.dt_method(recv.value, f.attr, args, kw)
        # ---- Series.<m>() sobre expresion de columna ----
        if self._is_col(recv) and f.attr not in ("cast", "alias", "over", "otherwise", "when", "isNull",
                                                  "isNotNull", "isin", "between", "desc", "asc", "contains",
                                                  "rlike", "startswith", "endswith", "getItem", "asc_nulls_last",
                                                  "desc_nulls_last", "bround", "substr", "like", "ilike"):
            if f.attr in ("astype",):
                return None
            return self.series_method(recv, f.attr, args, kw)
        return None

    def _rolling(self, rc, agg, node):
        c = rc.func.value
        wn = rc.args[0] if rc.args else None
        for k in rc.keywords:
            if k.arg == "window":
                wn = k.value
        if not (wn is not None and const(wn, (int,))):
            raise Untr("rolling con ventana no entera (offset temporal/dinamica)",
                       "usa Window.orderBy(col).rangeBetween(...) con F.* ")
        n = cval(wn)
        minp = None
        for k in rc.keywords:
            if k.arg == "min_periods":
                minp = k.value
            if k.arg in ("center", "win_type", "closed", "on") :
                raise Untr("rolling(%s=...)" % k.arg)
        fns = {"mean": "F.avg(_c)", "sum": "F.sum(_c)", "min": "F.min(_c)", "max": "F.max(_c)",
               "std": "F.stddev_samp(_c)", "var": "F.var_samp(_c)", "count": "F.count(_c)",
               "median": "F.median(_c)"}
        if agg not in fns:
            raise Untr("rolling(...).%s()" % agg)
        w = win([], True, (-(n - 1), 0))
        a = meth(tpl(fns[agg], _c=c), "over", w)
        if agg == "count":
            return a
        cnt = meth(Fn("count", c), "over", w)
        thr = minp if minp is not None else K(n)
        self.diag.warn("rolling(%d).%s() -> %s over Window.orderBy(monotonically_increasing_id()).rowsBetween(-%d, 0), "
                       "NULL hasta completar min_periods; sin partitionBy todo pasa por una particion."
                       % (n, agg, agg, n - 1))
        return meth(Fn("when", ast.Compare(left=cnt, ops=[ast.GtE()], comparators=[thr]), a), "otherwise", Fn("lit", K(None)))

    # ------------------------------------------------------------------
    # pd.<fn>
    # ------------------------------------------------------------------
    def _pd_func(self, node, fn):
        args, kw = node.args, node.keywords
        A = lambda i, n, d=None: self._arg(args, kw, i, n, d)  # noqa: E731
        if fn in ("to_datetime",):
            x = A(0, "arg")
            fmt = A(1, "format")
            x = x if self._is_col(x) else lit(x)
            self.diag.warn("pd.to_datetime -> F.to_timestamp (valores no parseables = null, como errors='coerce').")
            if fmt is not None and _name_is_str(fmt):
                return Fn("to_timestamp", x, K(strftime_to_java(fmt.value)))
            return Fn("to_timestamp", x)
        if fn == "to_numeric":
            x = A(0, "arg")
            return meth(x if self._is_col(x) else lit(x), "cast", K("double"))
        if fn in ("isna", "isnull"):
            return meth(A(0, "obj"), "isNull")
        if fn in ("notna", "notnull"):
            return meth(A(0, "obj"), "isNotNull")
        if fn == "cut":
            return self.pd_cut(node)
        if fn == "qcut":
            return self.pd_qcut(node)
        if fn == "concat":
            objs = A(0, "objs")
            axis = A(99, "axis")
            if axis is not None and const(axis) and cval(axis) not in (0, "index"):
                raise Untr("pd.concat(axis=1) requiere alineacion por indice", "usa df1.join(df2, on=<clave>)")
            if not isinstance(objs, (ast.List, ast.Tuple)) or len(objs.elts) < 1:
                raise Untr("pd.concat con lista no literal")
            e = objs.elts[0]
            for o in objs.elts[1:]:
                e = meth(e, "unionByName", o, allowMissingColumns=K(True))
            self.diag.warn("pd.concat -> unionByName(allowMissingColumns=True): sin indice; columnas ausentes = null.")
            return e
        if fn == "merge":
            if len(args) < 2:
                raise Untr("pd.merge sin ambos DataFrames")
            return self._merge(args[0], args[1], args[2:], kw)
        if fn == "melt":
            return self._melt(A(0, "frame"), args[1:], kw)
        if fn in ("DataFrame",):
            return None
        return None

    def _np_extra(self, node, fn):
        args, kw = node.args, node.keywords
        if fn == "select" and len(args) >= 2 and isinstance(args[0], (ast.List, ast.Tuple)) \
                and isinstance(args[1], (ast.List, ast.Tuple)) and len(args[0].elts) == len(args[1].elts):
            default = self._arg(args, kw, 2, "default")
            e = None
            for cnd, v in zip(args[0].elts, args[1].elts):
                e = Fn("when", cnd, lit(v)) if e is None else meth(e, "when", cnd, lit(v))
            return meth(e, "otherwise", lit(default) if default is not None else Fn("lit", K(None)))
        if fn == "arange" and args and all(const(a, (int,)) for a in args) and len(args) <= 3:
            return call(N("list"), call(N("range"), *args))
        if fn in ("round", "around") and args:
            return Fn("bround", args[0], *(args[1:2] or [K(0)]))
        if fn == "clip" and len(args) >= 3:
            return Fn("least", Fn("greatest", args[0], lit(args[1])), lit(args[2]))
        if fn == "isnan" and args:
            return Fn("isnan", args[0])
        if fn in ("nanmean", "mean", "nansum", "sum", "nanmax", "max", "nanmin", "min", "std", "nanstd", "median") and args \
                and self._is_col(args[0]):
            name = {"nanmean": "mean", "nansum": "sum", "nanmax": "max", "nanmin": "min", "nanstd": "std"}.get(fn, fn)
            return self.series_method(args[0], name, [], [])
        if fn == "sign" and args:
            return Fn("signum", args[0])
        return None

    # ------------------------------------------------------------------
    # np.nan / np.inf / .dt.prop / .str[...] / loc / iloc
    # ------------------------------------------------------------------
    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            if node.value.id in self.numpy_alias and node.attr in ("nan", "NaN", "NAN", "NA"):
                return meth(Fn("lit", K(None)), "cast", K("double"))
            if node.value.id in self.numpy_alias and node.attr in ("inf", "Inf", "PINF"):
                return Fn("lit", call(N("float"), K("inf")))
            if node.value.id in self.pandas_alias and node.attr in ("NA", "NaT"):
                return Fn("lit", K(None))
        self.generic_visit(node)
        v = node.value
        if isinstance(v, ast.Attribute) and v.attr == "dt" and self._is_col(v.value) and node.attr in DT_PROPS:
            return self.dt_prop(v.value, node.attr)
        return node

    def rewrite_loc(self, node):
        outer = self

        class _Loc(ast.NodeTransformer):
            def visit_Subscript(self, n):
                self.generic_visit(n)
                v = n.value
                if isinstance(v, ast.Attribute) and v.attr in ("loc", "iloc") and outer._is_df(v.value):
                    return outer._loc_read(v.value, v.attr, unslice(n))
                return n
        return _Loc().visit(node)

    def _loc_read(self, df, kind, sl):
        rows, cols = sl, None
        if isinstance(sl, ast.Tuple) and len(sl.elts) == 2:
            rows, cols = sl.elts
        elif isinstance(sl, ast.Tuple):
            raise Untr(".%s con mas de 2 ejes" % kind)
        full = lambda s: isinstance(s, ast.Slice) and s.lower is None and s.upper is None and s.step is None  # noqa: E731
        res = df
        if kind == "loc":
            if not full(rows):
                if isinstance(rows, ast.Slice):
                    raise Untr(".loc[a:b] por etiqueta de indice (Spark no tiene indice)")
                res = meth(res, "filter", rows)
            if cols is not None and not full(cols):
                cs = _strs(cols)
                if cs is None:
                    raise Untr(".loc con columnas no literales")
                res = meth(res, "select", *[K(c) for c in cs])
            return res
        # iloc
        if isinstance(rows, ast.Slice) and rows.lower is None and rows.step is None and rows.upper is not None \
                and const(rows.upper, (int,)):
            res = meth(res, "limit", rows.upper)
            self.diag.warn(".iloc[:n] -> limit(n): sin orderBy previo, Spark no garantiza cuales son las primeras filas.")
        elif not full(rows):
            raise Untr(".iloc posicional por fila (Spark no tiene indice posicional)",
                       "agrega F.row_number().over(Window.orderBy(...)) y filtra por ese numero")
        if cols is not None and not full(cols):
            if isinstance(df, ast.Name):
                idx = cols.elts if isinstance(cols, (ast.List, ast.Tuple)) else [cols]
                if not all(const(i, (int,)) for i in idx):
                    raise Untr(".iloc con columnas no literales")
                res = meth(res, "select", *[tpl("_d.columns[%d]" % cval(i), _d=df) for i in idx])
            else:
                raise Untr(".iloc de columnas sobre expresion compleja")
        return res

    # ------------------------------------------------------------------
    # asignaciones especiales
    # ------------------------------------------------------------------
    def pre_assign(self, node):
        """Devuelve un nodo reemplazo o None. Reescribe asignaciones .loc / .columns /
        reducciones escalares."""
        if len(node.targets) != 1:
            return None
        t = node.targets[0]
        # df.loc[mask, "c"] = v  ->  df["c"] = np.where(mask, v, df["c"])
        if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Attribute) and t.value.attr == "loc" \
                and self._is_df(t.value.value):
            sl = unslice(t)
            if isinstance(sl, ast.Tuple) and len(sl.elts) == 2 and _name_is_str(sl.elts[1]):
                dfn = t.value.value
                tgt = ast.Subscript(value=dfn, slice=sl.elts[1], ctx=ast.Store())
                val = call(ast.Attribute(value=N("np"), attr="where", ctx=ast.Load()), sl.elts[0], node.value,
                           ast.Subscript(value=copy.deepcopy(dfn), slice=sl.elts[1], ctx=ast.Load()))
                self.numpy_alias.add("np")
                self.diag.warn(".loc[mask, col] = v -> withColumn(col, F.when(mask, v).otherwise(F.col(col))): "
                               "si 'col' es nueva, las demas filas quedan con su valor previo (usa F.lit(None) si querias NaN).")
                return ast.Assign(targets=[tgt], value=val)
            raise Untr("asignacion .loc con forma no soportada")
        # df.columns = [...]  ->  df = df.toDF(*[...])
        if isinstance(t, ast.Attribute) and t.attr == "columns" and self._is_df(t.value) and isinstance(t.value, ast.Name):
            return ast.Assign(targets=[ast.Name(t.value.id, ast.Store())],
                              value=meth(t.value, "toDF", ast.Starred(value=node.value, ctx=ast.Load())))
        # m = df["x"].mean()  -> escalar pequeno al driver
        if isinstance(t, ast.Name) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
            fv = node.value.func
            if fv.attr in RED and isinstance(fv.value, ast.Subscript) and self._is_df(fv.value.value) \
                    and _name_is_str(unslice(fv.value)) and not node.value.args:
                df = self.visit(copy.deepcopy(fv.value.value))
                agg = tpl(RED[fv.attr], _c=Fn("col", K(unslice(fv.value).value)))
                expr = meth(meth(df, "agg", agg), "first")
                code = "%s = %s[0]  # escalar pequeno: 1 fila al driver (agg, no collect de datos)" % (
                    t.id, _unparse(expr))
                self._mllib_seq += 1
                pid = "__PY2SPARK_MLLIB_%d__" % self._mllib_seq
                self.mllib_blocks[pid] = code
                self.dead_vars.discard(t.id)
                return ast.Expr(value=ast.Name(pid, ast.Load()))
        return None

    def inplace_expr(self, node):
        """df.dropna(inplace=True) -> df = df.dropna()."""
        v = node.value
        if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr in _INPLACE_OK \
                and isinstance(v.func.value, ast.Name) and self._is_df(v.func.value):
            ip = [k for k in v.keywords if k.arg == "inplace"]
            if ip and isinstance(ip[0].value, ast.Constant) and ip[0].value.value is True:
                v2 = copy.deepcopy(v)
                v2.keywords = [k for k in v2.keywords if k.arg != "inplace"]
                return ast.Assign(targets=[ast.Name(v.func.value.id, ast.Store())], value=v2)
        return None

    # ------------------------------------------------------------------
    # DataFrame methods (extension de _df_method). Devuelve nodo o None.
    # ------------------------------------------------------------------
    def df_method_ext(self, node, f):
        m, recv = f.attr, f.value
        args, kw = node.args, node.keywords
        A = lambda i, n, d=None: self._arg(args, kw, i, n, d)  # noqa: E731
        if m == "merge":
            return self._merge(recv, A(0, "right"), args[1:], kw)
        if m == "melt":
            return self._melt(recv, args, kw)
        if m in ("pivot_table", "pivot"):
            return self._pivot(recv, m, args, kw)
        if m == "tail":
            n = A(0, "n", K(5))
            self.diag.warn("df.tail(n) -> ultimas n filas por orden de aparicion (monotonically_increasing_id).")
            ordered = meth(meth(recv, "withColumn", K("_i"), Fn("monotonically_increasing_id")), "orderBy",
                           meth(Fn("col", K("_i")), "desc"))
            return meth(meth(meth(ordered, "limit", n), "orderBy", K("_i")), "drop", K("_i"))
        if m in ("nlargest", "nsmallest"):
            n = A(0, "n")
            cols = A(1, "columns")
            cs = _strs(cols)
            if cs is None or n is None:
                raise Untr("%s con columnas no literales" % m)
            os_ = [meth(Fn("col", K(c)), "desc" if m == "nlargest" else "asc_nulls_last") for c in cs]
            return meth(meth(recv, "orderBy", *os_), "limit", n)
        if m == "query":
            q = A(0, "expr")
            if not _name_is_str(q):
                raise Untr("query con expresion no literal")
            if "@" in q.value:
                raise Untr("query con variables '@' externas", "usa df.filter(F.col('x') > var)")
            self.diag.warn("df.query('...') -> df.filter('...') (SQL de Spark: usa 'and/or', '==' admitido).")
            return meth(recv, "filter", q)
        if m == "assign":
            cur = recv
            for k in kw:
                if k.arg is None:
                    raise Untr("assign(**dict)")
                v = k.value
                if isinstance(v, ast.Lambda):
                    if len(v.args.args) != 1:
                        raise Untr("assign con lambda de mas de un parametro")
                    v = self.pyx(v.body, {v.args.args[0].arg: ("ROW",)}, [], False)
                cur = meth(cur, "withColumn", K(k.arg), lit(v))
            return cur
        if m == "copy":
            return recv
        if m == "reset_index":
            return recv
        if m == "set_index":
            self.diag.warn("set_index(...) -> sin indice en Spark: las columnas siguen siendo columnas explicitas.")
            return recv
        if m == "astype" and A(0, "dtype") is not None and isinstance(A(0, "dtype"), ast.Dict):
            cur = recv
            from .converter import _astype_to_spark
            for k, v in zip(A(0, "dtype").keys, A(0, "dtype").values):
                st = _astype_to_spark(v)
                if not _name_is_str(k) or st is None:
                    raise Untr("astype(dict) con tipo/columna no reconocido")
                cur = meth(cur, "withColumn", k, meth(Fn("col", k), "cast", K(st)))
            return cur
        if m == "dropna":
            if any(k.arg == "axis" for k in kw) and cval(kw[[k.arg for k in kw].index("axis")].value) in (1, "columns"):
                raise Untr("dropna(axis=1) (columnas con nulos)")
            return None
        if m == "fillna":
            how = A(99, "method")
            if how is not None:
                raise Untr("df.fillna(method=...)", "usa F.last(col, True).over(Window.orderBy(...).rowsBetween(unboundedPreceding, 0))")
            return None
        if m == "drop_duplicates":
            keep = A(1, "keep")
            kv = cval(keep) if keep is not None and const(keep) else "first"
            if kv not in ("first", "last"):
                raise Untr("drop_duplicates(keep=False)", "usa Window con count() over particion y filtra == 1")
            subset = A(0, "subset")
            if subset is not None and not isinstance(subset, ast.List) and _name_is_str(subset):
                subset = ast.List(elts=[subset], ctx=ast.Load())
            self.diag.warn("drop_duplicates -> dropDuplicates: Spark no garantiza cual fila se conserva (keep=%s)." % kv)
            return meth(recv, "dropDuplicates", *([subset] if subset is not None else []))
        if m == "apply":
            return self.apply_row(node, recv)
        if m == "isna" or m == "isnull":
            raise Untr("df.isna() (matriz de booleanos)", "usa F.col(c).isNull() por columna")
        if m == "to_dict" or m == "to_numpy" or m == "values" or m == "tolist":
            raise Untr("df.%s(...) trae todo al driver" % m)
        if m in ("to_sql", "to_excel", "to_pickle", "to_feather", "to_hdf", "to_clipboard", "to_html", "to_markdown", "to_string", "to_latex"):
            raise Untr("df.%s(...)" % m, "usa df.write.format('jdbc')/parquet/csv segun el destino")
        return None

    # ---- merge helper ----
    def _merge(self, left, right, rest, kw):
        pa = {}
        names = ["how", "on", "left_on", "right_on", "left_index", "right_index", "sort", "suffixes", "copy", "indicator", "validate"]
        for i, a in enumerate(rest):
            if i < len(names):
                pa[names[i]] = a
        for k in kw:
            pa[k.arg] = k.value
        for bad in ("left_index", "right_index"):
            if bad in pa and not (isinstance(pa[bad], ast.Constant) and pa[bad].value is False):
                raise Untr("merge(%s=True) usa el indice de pandas" % bad, "usa columnas clave explicitas (on=...)")
        if "indicator" in pa and not (isinstance(pa["indicator"], ast.Constant) and pa["indicator"].value is False):
            raise Untr("merge(indicator=True)", "agrega una columna marca antes del join y usa isNull()")
        how = pa.get("how")
        howv = cval(how) if how is not None and const(how) else "inner"
        if howv not in ("inner", "left", "right", "outer", "cross"):
            raise Untr("merge(how=%r)" % howv)
        kws = {"how": K(howv)}
        for key in ("on", "left_on", "right_on", "suffixes"):
            if key in pa:
                kws[key] = pa[key]
        if "left_on" in kws and "right_on" not in kws or "right_on" in kws and "left_on" not in kws:
            raise Untr("merge con solo uno de left_on/right_on")
        self.needs_merge_helper = True
        self.diag.warn("merge -> _py2spark_merge(...) (join + sufijos _x/_y en columnas repetidas): Spark no "
                       "garantiza el orden de filas y no empareja claves nulas.")
        return call(N("_py2spark_merge"), left, right, **kws)

    def _melt(self, frame, rest, kw):
        pa = {}
        names = ["id_vars", "value_vars", "var_name", "value_name"]
        for i, a in enumerate(rest):
            if i < len(names):
                pa[names[i]] = a
        for k in kw:
            pa[k.arg] = k.value
        ids = pa.get("id_vars")
        ids = ids if ids is not None else ast.List(elts=[], ctx=ast.Load())
        if _name_is_str(ids):
            ids = ast.List(elts=[ids], ctx=ast.Load())
        vals = pa.get("value_vars")
        if vals is not None and _name_is_str(vals):
            vals = ast.List(elts=[vals], ctx=ast.Load())
        vn = pa.get("var_name", K("variable"))
        vl = pa.get("value_name", K("value"))
        self.diag.warn("melt -> DataFrame.unpivot (Spark >= 3.4): las columnas de valor deben tener un tipo comun.")
        return meth(frame, "unpivot", ids, vals if vals is not None else K(None), vn, vl)

    def _pivot(self, recv, m, args, kw):
        pa = {}
        names = ["values", "index", "columns", "aggfunc"] if m == "pivot_table" else ["index", "columns", "values"]
        for i, a in enumerate(args):
            if i < len(names):
                pa[names[i]] = a
        for k in kw:
            pa[k.arg] = k.value
        idx, cols, vals = pa.get("index"), pa.get("columns"), pa.get("values")
        if idx is None or cols is None or vals is None or not _name_is_str(cols) or not _name_is_str(vals):
            raise Untr("%s requiere index, columns y values literales (una sola columna de valores)" % m)
        ik = _strs(idx)
        if ik is None:
            raise Untr("%s con index no literal" % m)
        fn = "mean" if m == "pivot_table" else "first"
        af = pa.get("aggfunc")
        if m == "pivot_table" and af is not None:
            if not _name_is_str(af):
                raise Untr("pivot_table con aggfunc no literal (lista/dict/callable)", "usa groupBy().pivot().agg(F.expr('...'))")
            fn = af.value
        if fn == "first" and m == "pivot":
            agg = tpl("F.first(_c)", _c=Fn("col", K(vals.value)))
        else:
            name = _AGG_ALIAS.get(fn)
            if name is None:
                raise Untr("pivot_table aggfunc=%r" % fn)
            colnode = Fn("col", K(vals.value))
            if name in ("sum", "mean", "std", "var"):
                colnode = meth(colnode, "cast", K("double"))
            agg = tpl(RED[name], _c=colnode)
        res = meth(meth(meth(recv, "groupBy", *[K(i) for i in ik]), "pivot", cols), "agg", agg)
        fv = pa.get("fill_value")
        if fv is not None:
            res = meth(res, "fillna", fv)
        self.diag.warn("%s -> groupBy(index).pivot(columns).agg(...): columnas = valores del pivote (orden ascendente)." % m)
        return res
