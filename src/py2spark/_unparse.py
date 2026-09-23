# py2spark._unparse — compatibilidad de ast.unparse para Python < 3.9.
#
# ast.unparse() solo existe desde Python 3.9. En entornos con Python 3.8 (p.ej.
# algunas instalaciones Windows del banco) lanzaba
#   AttributeError: module 'ast' has no attribute 'unparse'
# y la conversion py2spark fallaba por completo. Aqui proveemos un unparse que
# funciona en 3.9+ (usa el nativo) y cae a alternativas en 3.8:
#   1) ast.unparse (Python >= 3.9)
#   2) astor.to_source (si el paquete esta instalado)
#   3) un unparser minimo propio para los nodos que py2spark genera
#      (Call/Attribute/Name/Constant/BinOp/Compare/etc.), suficiente para
#      regenerar el codigo PySpark que produce el converter.

import ast


def unparse(node):
    """Devuelve el codigo fuente de un nodo AST, compatible con Python 3.8+."""
    # 1) Nativo (3.9+): la ruta normal.
    _native = getattr(ast, "unparse", None)
    if _native is not None:
        return _native(node)
    # 2) astor si esta disponible.
    try:
        import astor  # type: ignore
        return astor.to_source(node).strip()
    except Exception:
        pass
    # 3) Fallback minimo propio (solo los nodos que genera py2spark).
    return _MiniUnparser().visit(node)


# Precedencia de operadores (mayor numero = mas fuerte). Se usa para decidir
# cuando parentizar un sub-nodo al reconstruir el codigo, imitando ast.unparse.
_PREC_ATOM = 100      # atomos: Name, Constant, Call, Attribute, List, etc.
_PREC_POW = 15        # **
_PREC_UNARY = 14      # -x, +x, ~x
_PREC_MULT = 13       # * / % // @
_PREC_ADD = 12        # + -
_PREC_SHIFT = 11      # << >>
_PREC_BITAND = 10     # &
_PREC_BITXOR = 9      # ^
_PREC_BITOR = 8       # |
_PREC_CMP = 7         # comparaciones
_PREC_NOT = 6         # not x
_PREC_AND = 5         # and
_PREC_OR = 4          # or
_PREC_IFEXP = 3       # x if c else y
_PREC_LOWEST = 0

_BINOP_PREC = {
    ast.Pow: _PREC_POW,
    ast.Mult: _PREC_MULT, ast.Div: _PREC_MULT, ast.Mod: _PREC_MULT,
    ast.FloorDiv: _PREC_MULT, ast.MatMult: _PREC_MULT,
    ast.Add: _PREC_ADD, ast.Sub: _PREC_ADD,
    ast.LShift: _PREC_SHIFT, ast.RShift: _PREC_SHIFT,
    ast.BitAnd: _PREC_BITAND, ast.BitXor: _PREC_BITXOR, ast.BitOr: _PREC_BITOR,
}


class _MiniUnparser:
    """Unparser reducido para Python 3.8. Cubre el subconjunto de AST que emite
    py2spark: modulos, asignaciones, expresiones, llamadas, atributos, nombres,
    constantes, operaciones binarias/booleanas, comparaciones, listas/tuplas/dicts,
    subscripts, if-exp, comprensiones y starred. No pretende ser completo.

    Maneja precedencia de operadores para parentizar correctamente (imita
    ast.unparse), de modo que `((a) & (b)).cast('int')` no se serialice como
    `(a) & (b).cast('int')`."""

    def visit(self, node):
        m = getattr(self, "_" + type(node).__name__, None)
        if m is None:
            # ultimo recurso: representacion segura
            return "None"
        return m(node)

    def _prec(self, node):
        """Precedencia del nodo como expresion (para decidir parentesis)."""
        if isinstance(node, ast.BinOp):
            return _BINOP_PREC.get(type(node.op), _PREC_ATOM)
        if isinstance(node, ast.BoolOp):
            return _PREC_AND if isinstance(node.op, ast.And) else _PREC_OR
        if isinstance(node, ast.UnaryOp):
            return _PREC_NOT if isinstance(node.op, ast.Not) else _PREC_UNARY
        if isinstance(node, ast.Compare):
            return _PREC_CMP
        if isinstance(node, ast.IfExp):
            return _PREC_IFEXP
        if isinstance(node, (ast.Lambda,)):
            return _PREC_LOWEST
        return _PREC_ATOM

    def _wrap(self, node, min_prec):
        """Visita el nodo y lo envuelve en parentesis si su precedencia es
        menor que la minima requerida por el contexto."""
        s = self.visit(node)
        if self._prec(node) < min_prec:
            return "(" + s + ")"
        return s

    # ---- modulo / statements ----
    def _Module(self, n):
        return "\n".join(self.visit(s) for s in n.body)

    def _Expr(self, n):
        return self.visit(n.value)

    def _Assign(self, n):
        targets = ", ".join(self.visit(t) for t in n.targets)
        return f"{targets} = {self.visit(n.value)}"

    def _Import(self, n):
        names = ", ".join(a.name + (f" as {a.asname}" if a.asname else "") for a in n.names)
        return f"import {names}"

    def _ImportFrom(self, n):
        names = ", ".join(a.name + (f" as {a.asname}" if a.asname else "") for a in n.names)
        return f"from {n.module or ''} import {names}"

    # ---- expresiones ----
    def _Name(self, n):
        return n.id

    def _Constant(self, n):
        return repr(n.value)

    # Python 3.8 aun usa Str/Num/NameConstant en algunos casos.
    def _Str(self, n):
        return repr(n.s)

    def _Num(self, n):
        return repr(n.n)

    def _NameConstant(self, n):
        return repr(n.value)

    def _Attribute(self, n):
        # El "value" de un atributo debe ir entre parentesis si es una expresion
        # compuesta: p.ej. (a & b).cast('int'), (a + b).alias('x').
        return f"{self._wrap(n.value, _PREC_ATOM)}.{n.attr}"

    def _Call(self, n):
        args = [self.visit(a) for a in n.args]
        for kw in n.keywords:
            if kw.arg is None:
                args.append("**" + self.visit(kw.value))
            else:
                args.append(f"{kw.arg}={self.visit(kw.value)}")
        # El "func" tambien puede ser una expresion compuesta.
        return f"{self._wrap(n.func, _PREC_ATOM)}({', '.join(args)})"

    def _Starred(self, n):
        return "*" + self.visit(n.value)

    def _List(self, n):
        return "[" + ", ".join(self.visit(e) for e in n.elts) + "]"

    def _Tuple(self, n):
        if len(n.elts) == 1:
            return "(" + self.visit(n.elts[0]) + ",)"
        return "(" + ", ".join(self.visit(e) for e in n.elts) + ")"

    def _Dict(self, n):
        items = ", ".join(f"{self.visit(k)}: {self.visit(v)}"
                          for k, v in zip(n.keys, n.values))
        return "{" + items + "}"

    def _Subscript(self, n):
        return f"{self._wrap(n.value, _PREC_ATOM)}[{self.visit(n.slice)}]"

    def _Index(self, n):  # 3.8: Subscript.slice es un Index
        return self.visit(n.value)

    def _Slice(self, n):
        lo = self.visit(n.lower) if n.lower else ""
        hi = self.visit(n.upper) if n.upper else ""
        st = f":{self.visit(n.step)}" if n.step else ""
        return f"{lo}:{hi}{st}"

    def _BinOp(self, n):
        prec = _BINOP_PREC.get(type(n.op), _PREC_ATOM)
        if isinstance(n.op, ast.Pow):
            # ** es asociativo a la derecha: left necesita prec+1, right prec.
            left = self._wrap(n.left, prec + 1)
            right = self._wrap(n.right, prec)
        else:
            # asociativo a la izquierda: left prec, right prec+1.
            left = self._wrap(n.left, prec)
            right = self._wrap(n.right, prec + 1)
        return f"{left} {self._op(n.op)} {right}"

    def _UnaryOp(self, n):
        prec = _PREC_NOT if isinstance(n.op, ast.Not) else _PREC_UNARY
        operand = self._wrap(n.operand, prec)
        sep = " " if isinstance(n.op, ast.Not) else ""
        return f"{self._op(n.op)}{sep}{operand}"

    def _BoolOp(self, n):
        prec = _PREC_AND if isinstance(n.op, ast.And) else _PREC_OR
        op = " and " if isinstance(n.op, ast.And) else " or "
        # Cada operando de mayor precedencia que el propio BoolOp; parentiza si menor.
        return op.join(self._wrap(v, prec + 1) for v in n.values)

    def _Compare(self, n):
        parts = [self._wrap(n.left, _PREC_CMP + 1)]
        for op, comp in zip(n.ops, n.comparators):
            parts.append(self._op(op))
            parts.append(self._wrap(comp, _PREC_CMP + 1))
        return " ".join(parts)

    def _IfExp(self, n):
        return f"({self.visit(n.body)} if {self.visit(n.test)} else {self.visit(n.orelse)})"

    def _JoinedStr(self, n):
        # f-string: reconstruccion aproximada.
        out = []
        for v in n.values:
            if isinstance(v, ast.Constant):
                out.append(str(v.value))
            elif hasattr(ast, "Str") and isinstance(v, ast.Str):
                out.append(v.s)
            elif isinstance(v, ast.FormattedValue):
                out.append("{" + self.visit(v.value) + "}")
        return "f'" + "".join(out).replace("'", "\\'") + "'"

    def _FormattedValue(self, n):
        return "{" + self.visit(n.value) + "}"

    def _ListComp(self, n):
        gens = " ".join(self._comprehension(g) for g in n.generators)
        return f"[{self.visit(n.elt)} {gens}]"

    def _GeneratorExp(self, n):
        gens = " ".join(self._comprehension(g) for g in n.generators)
        return f"({self.visit(n.elt)} {gens})"

    def _comprehension(self, g):
        ifs = "".join(f" if {self.visit(i)}" for i in g.ifs)
        return f"for {self.visit(g.target)} in {self.visit(g.iter)}{ifs}"

    def _op(self, op):
        return {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
            ast.Mod: "%", ast.Pow: "**", ast.FloorDiv: "//",
            ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
            ast.Gt: ">", ast.GtE: ">=", ast.Is: "is", ast.IsNot: "is not",
            ast.In: "in", ast.NotIn: "not in",
            ast.And: "and", ast.Or: "or", ast.Not: "not",
            ast.USub: "-", ast.UAdd: "+", ast.Invert: "~",
            ast.BitAnd: "&", ast.BitOr: "|", ast.BitXor: "^",
        }.get(type(op), "?")
