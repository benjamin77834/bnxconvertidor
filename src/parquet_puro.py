"""Escritor Parquet minimo en Python puro (sin pyarrow, fastparquet ni Spark).

Solo para los datos sinteticos del orquestador cuando el servidor no tiene ningun motor
parquet (p.ej. Anaconda en Windows del banco): un row group, una pagina por columna,
codificacion PLAIN, sin compresion, columnas OPTIONAL. Spark, pyarrow y pandas lo leen.

Tipos: bool -> BOOLEAN, int -> INT64, float (o int+float) -> DOUBLE, el resto -> texto UTF8.
"""
import struct

# --- Thrift compact protocol (lo justo para los metadatos de Parquet) ---
_T_I32, _T_I64, _T_BIN, _T_LIST, _T_STRUCT = 5, 6, 8, 9, 12


def _varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _zigzag(n):
    return _varint((n << 1) ^ (n >> 63))


class _Struct:
    """Escribe los campos de un struct Thrift compact en orden de id creciente."""

    def __init__(self):
        self.buf = bytearray()
        self.last = 0

    def _hdr(self, fid, ttype):
        delta = fid - self.last
        if 0 < delta <= 15:
            self.buf.append((delta << 4) | ttype)
        else:
            self.buf.append(ttype)
            self.buf += _zigzag(fid)
        self.last = fid

    def i32(self, fid, v):
        self._hdr(fid, _T_I32)
        self.buf += _zigzag(v)

    def i64(self, fid, v):
        self._hdr(fid, _T_I64)
        self.buf += _zigzag(v)

    def string(self, fid, s):
        raw = s.encode("utf-8")
        self._hdr(fid, _T_BIN)
        self.buf += _varint(len(raw)) + raw

    def struct(self, fid, st):
        self._hdr(fid, _T_STRUCT)
        self.buf += st.done()

    def list_(self, fid, etype, items):
        """items: ya serializados (bytes) segun etype."""
        self._hdr(fid, _T_LIST)
        n = len(items)
        self.buf.append(((n << 4) | etype) if n < 15 else (0xF0 | etype))
        if n >= 15:
            self.buf += _varint(n)
        for it in items:
            self.buf += it

    def done(self):
        return bytes(self.buf) + b"\x00"


def _bits_def_levels(presentes):
    """Niveles de definicion (ancho 1) como una corrida bit-packed RLE/hybrid."""
    n = len(presentes)
    grupos = (n + 7) // 8
    datos = bytearray(grupos)
    for i, p in enumerate(presentes):
        if p:
            datos[i // 8] |= 1 << (i % 8)
    cuerpo = _varint((grupos << 1) | 1) + bytes(datos)
    return struct.pack("<I", len(cuerpo)) + cuerpo


def _tipo_columna(vals):
    vs = [v for v in vals if v is not None]
    if vs and all(isinstance(v, bool) for v in vs):
        return "bool"
    if vs and all(isinstance(v, int) and not isinstance(v, bool) for v in vs):
        return "int"
    if vs and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vs):
        return "double"
    return "str"


# tipo -> (Type de Parquet, converted_type o None)
_PARQUET_TYPE = {"bool": (0, None), "int": (2, None), "double": (5, None), "str": (6, 0)}


def _valores_plain(tipo, vals):
    if tipo == "bool":
        n = len(vals)
        out = bytearray((n + 7) // 8)
        for i, v in enumerate(vals):
            if v:
                out[i // 8] |= 1 << (i % 8)
        return bytes(out)
    if tipo == "int":
        return b"".join(struct.pack("<q", v) for v in vals)
    if tipo == "double":
        return b"".join(struct.pack("<d", float(v)) for v in vals)
    out = bytearray()
    for v in vals:
        raw = str(v).encode("utf-8")
        out += struct.pack("<I", len(raw)) + raw
    return bytes(out)


def escribir(path, columnas, filas):
    """Escribe `filas` (lista de dicts) con las `columnas` (nombres) en `path`."""
    n = len(filas)
    cuerpo = bytearray(b"PAR1")
    chunks, esquema = [], []
    for c in columnas:
        vals = [r.get(c) for r in filas]
        tipo = _tipo_columna(vals)
        if tipo == "str":
            vals = [None if v is None else str(v) for v in vals]
        ptype, conv = _PARQUET_TYPE[tipo]
        no_nulos = [v for v in vals if v is not None]
        pagina = _bits_def_levels([v is not None for v in vals]) + _valores_plain(tipo, no_nulos)
        dph = _Struct()
        dph.i32(1, n)
        dph.i32(2, 0)   # PLAIN
        dph.i32(3, 3)   # niveles de definicion: RLE
        dph.i32(4, 3)   # niveles de repeticion: RLE
        ph = _Struct()
        ph.i32(1, 0)    # DATA_PAGE
        ph.i32(2, len(pagina))
        ph.i32(3, len(pagina))
        ph.struct(5, dph)
        cabecera = ph.done()
        offset = len(cuerpo)
        cuerpo += cabecera + pagina
        total = len(cabecera) + len(pagina)
        cm = _Struct()
        cm.i32(1, ptype)
        cm.list_(2, _T_I32, [_zigzag(0), _zigzag(3)])
        cm.list_(3, _T_BIN, [_varint(len(c.encode("utf-8"))) + c.encode("utf-8")])
        cm.i32(4, 0)    # sin compresion
        cm.i64(5, n)
        cm.i64(6, total)
        cm.i64(7, total)
        cm.i64(9, offset)
        cc = _Struct()
        cc.i64(2, offset)
        cc.struct(3, cm)
        chunks.append((cc.done(), total))
        el = _Struct()
        el.i32(1, ptype)
        el.i32(3, 1)    # OPTIONAL
        el.string(4, c)
        if conv is not None:
            el.i32(6, conv)
        esquema.append(el.done())
    raiz = _Struct()
    raiz.string(4, "schema")
    raiz.i32(5, len(columnas))
    rg = _Struct()
    rg.list_(1, _T_STRUCT, [cc for cc, _ in chunks])
    rg.i64(2, sum(t for _, t in chunks))
    rg.i64(3, n)
    fm = _Struct()
    fm.i32(1, 1)
    fm.list_(2, _T_STRUCT, [raiz.done()] + esquema)
    fm.i64(3, n)
    fm.list_(4, _T_STRUCT, [rg.done()])
    fm.string(6, "bnx parquet_puro")
    meta = fm.done()
    cuerpo += meta + struct.pack("<I", len(meta)) + b"PAR1"
    with open(path, "wb") as f:
        f.write(cuerpo)
