"""Lector Parquet en Python puro (sin pyarrow, fastparquet ni Spark).

Para el visor de la GUI cuando el servidor no tiene ningun motor parquet (p.ej. Anaconda en
Windows sin pyarrow ni Java). Solo LECTURA, columnas planas (sin nested), y solo lee del disco
los row groups / paginas necesarios para las filas pedidas.

Soporta:
  - Metadatos: footer Thrift compact (se lee solo el final del archivo).
  - Paginas DATA_PAGE v1 y v2 y DICTIONARY_PAGE.
  - Encodings: PLAIN, PLAIN_DICTIONARY / RLE_DICTIONARY, RLE (niveles y booleanos).
  - Fisicos: BOOLEAN, INT32, INT64, INT96 (timestamp), FLOAT, DOUBLE, BYTE_ARRAY, FIXED_LEN_BYTE_ARRAY.
  - Logicos: STRING/UTF8, DATE, TIMESTAMP (millis/micros/nanos), TIME, DECIMAL, enteros con/sin signo.
  - Nulos (definition levels de columnas planas OPTIONAL).
  - Compresion: UNCOMPRESSED, GZIP (zlib) y SNAPPY (descompresor propio, `snappy_descomprimir`).
No soporta: ZSTD / LZ4 / BROTLI / LZO, columnas nested (struct/list/map), encodings DELTA_*
ni BYTE_STREAM_SPLIT, archivos cifrados. En esos casos lanza `ParquetNoSoportado`.
"""
import struct
import zlib
from datetime import date, datetime, timedelta


class ParquetError(Exception):
    """Archivo parquet ilegible (corrupto, truncado o no es parquet)."""


class ParquetNoSoportado(ParquetError):
    """Caracteristica valida de parquet que este lector puro no implementa."""


_SUGERENCIA = " Instale pyarrow en el entorno del servidor (pip install pyarrow) para leerlo."


def _no_soportado(msg):
    return ParquetNoSoportado(msg + _SUGERENCIA)


# ---------------------------------------------------------------------------
# Snappy (formato en bloque "raw", el que usan Parquet/Spark; no el framing)
# ---------------------------------------------------------------------------
def snappy_descomprimir(data):
    """Descomprime un bloque snappy. Lanza ParquetError si esta corrupto."""
    data = bytes(data)
    n = len(data)
    pos = 0
    total = 0
    shift = 0
    while True:  # varint: longitud descomprimida
        if pos >= n or shift > 35:
            raise ParquetError("snappy: cabecera de longitud invalida")
        b = data[pos]
        pos += 1
        total |= (b & 0x7F) << shift
        if not b & 0x80:
            break
        shift += 7
    out = bytearray()
    while pos < n:
        tag = data[pos]
        pos += 1
        kind = tag & 3
        if kind == 0:  # literal
            ln = tag >> 2
            if ln >= 60:
                nb = ln - 59
                if pos + nb > n:
                    raise ParquetError("snappy: literal truncado")
                ln = int.from_bytes(data[pos:pos + nb], "little")
                pos += nb
            ln += 1
            if pos + ln > n:
                raise ParquetError("snappy: literal truncado")
            out += data[pos:pos + ln]
            pos += ln
            continue
        if kind == 1:  # copia, offset de 11 bits
            ln = ((tag >> 2) & 7) + 4
            if pos >= n:
                raise ParquetError("snappy: copia truncada")
            off = ((tag >> 5) << 8) | data[pos]
            pos += 1
        elif kind == 2:  # copia, offset de 16 bits
            ln = (tag >> 2) + 1
            if pos + 2 > n:
                raise ParquetError("snappy: copia truncada")
            off = int.from_bytes(data[pos:pos + 2], "little")
            pos += 2
        else:  # copia, offset de 32 bits
            ln = (tag >> 2) + 1
            if pos + 4 > n:
                raise ParquetError("snappy: copia truncada")
            off = int.from_bytes(data[pos:pos + 4], "little")
            pos += 4
        if off == 0 or off > len(out):
            raise ParquetError("snappy: offset de copia invalido")
        if off >= ln:
            ini = len(out) - off
            out += out[ini:ini + ln]
        else:  # solapada: repite el patron
            patron = bytes(out[-off:])
            out += (patron * (ln // off + 1))[:ln]
    if len(out) != total:
        raise ParquetError(f"snappy: tamano {len(out)} != esperado {total}")
    return bytes(out)


# ---------------------------------------------------------------------------
# Thrift compact (lector generico: struct -> {id_campo: valor})
# ---------------------------------------------------------------------------
class _Thrift:
    def __init__(self, buf, pos=0):
        self.buf = buf
        self.pos = pos

    def _byte(self):
        b = self.buf[self.pos]
        self.pos += 1
        return b

    def _varint(self):
        r = shift = 0
        while True:
            b = self._byte()
            r |= (b & 0x7F) << shift
            if not b & 0x80:
                return r
            shift += 7
            if shift > 70:
                raise ParquetError("thrift: varint invalido")

    def _zigzag(self):
        n = self._varint()
        return (n >> 1) ^ -(n & 1)

    def _valor(self, t):
        if t == 1:
            return True
        if t == 2:
            return False
        if t == 3:
            b = self._byte()
            return b - 256 if b > 127 else b
        if t in (4, 5, 6):
            return self._zigzag()
        if t == 7:
            v = struct.unpack_from("<d", self.buf, self.pos)[0]
            self.pos += 8
            return v
        if t == 8:
            ln = self._varint()
            if self.pos + ln > len(self.buf):
                raise ParquetError("thrift: binario truncado")
            v = bytes(self.buf[self.pos:self.pos + ln])
            self.pos += ln
            return v
        if t in (9, 10):
            h = self._byte()
            n = h >> 4
            et = h & 0x0F
            if n == 15:
                n = self._varint()
            if n > len(self.buf):
                raise ParquetError("thrift: lista invalida")
            if et in (1, 2):  # bool en lista: un byte por elemento
                return [self._byte() == 1 for _ in range(n)]
            return [self._valor(et) for _ in range(n)]
        if t == 11:
            n = self._varint()
            if n == 0:
                return {}
            kv = self._byte()
            return {self._hashable(self._valor(kv >> 4)): self._valor(kv & 0x0F) for _ in range(n)}
        if t == 12:
            return self.struct()
        raise ParquetError(f"thrift: tipo {t} desconocido")

    @staticmethod
    def _hashable(v):
        return v if isinstance(v, (int, bytes, str, float, bool)) else repr(v)

    def struct(self):
        campos = {}
        last = 0
        while True:
            b = self._byte()
            if b == 0:
                return campos
            t = b & 0x0F
            delta = b >> 4
            fid = last + delta if delta else self._zigzag()
            last = fid
            campos[fid] = self._valor(t)


# ---------------------------------------------------------------------------
# Niveles RLE / bit-packed hybrid
# ---------------------------------------------------------------------------
def _rle_hibrido(buf, pos, fin, bw, n):
    if bw == 0:
        return [0] * n
    out = []
    mask = (1 << bw) - 1
    nb_val = (bw + 7) // 8
    while len(out) < n:
        if pos >= fin:
            raise ParquetError("niveles/indices RLE truncados")
        h = r = shift = 0
        while True:
            b = buf[pos]
            pos += 1
            h |= (b & 0x7F) << shift
            if not b & 0x80:
                break
            shift += 7
        if h & 1:  # grupos de 8 valores empaquetados (LSB primero)
            grupos = h >> 1
            if pos + grupos * bw > fin:
                raise ParquetError("bit-packed truncado")
            for _ in range(grupos):
                g = int.from_bytes(buf[pos:pos + bw], "little")
                pos += bw
                out.extend([(g >> (i * bw)) & mask for i in range(8)])
        else:
            cnt = h >> 1
            v = int.from_bytes(buf[pos:pos + nb_val], "little")
            pos += nb_val
            out.extend([v] * cnt)
    del out[n:]
    return out


# ---------------------------------------------------------------------------
# Valores PLAIN (crudos; la conversion logica se hace solo sobre las filas pedidas)
# ---------------------------------------------------------------------------
_BOOLEAN, _INT32, _INT64, _INT96, _FLOAT, _DOUBLE, _BYTE_ARRAY, _FIXED = range(8)
_FMT = {_INT32: ("i", 4), _INT64: ("q", 8), _FLOAT: ("f", 4), _DOUBLE: ("d", 8)}


def _plain(ptype, data, pos, n, tlen):
    if n == 0:
        return []
    if ptype == _BOOLEAN:
        need = (n + 7) // 8
        if pos + need > len(data):
            raise ParquetError("pagina PLAIN truncada (BOOLEAN)")
        return [bool(data[pos + (i >> 3)] >> (i & 7) & 1) for i in range(n)]
    if ptype in _FMT:
        c, sz = _FMT[ptype]
        if pos + n * sz > len(data):
            raise ParquetError("pagina PLAIN truncada")
        return list(struct.unpack_from(f"<{n}{c}", data, pos))
    if ptype == _INT96:
        if pos + n * 12 > len(data):
            raise ParquetError("pagina PLAIN truncada (INT96)")
        return [bytes(data[pos + i * 12:pos + i * 12 + 12]) for i in range(n)]
    if ptype == _FIXED:
        if not tlen or pos + n * tlen > len(data):
            raise ParquetError("pagina PLAIN truncada (FIXED_LEN_BYTE_ARRAY)")
        return [bytes(data[pos + i * tlen:pos + (i + 1) * tlen]) for i in range(n)]
    if ptype == _BYTE_ARRAY:
        out = []
        for _ in range(n):
            if pos + 4 > len(data):
                raise ParquetError("pagina PLAIN truncada (BYTE_ARRAY)")
            ln = int.from_bytes(data[pos:pos + 4], "little")
            pos += 4
            if pos + ln > len(data):
                raise ParquetError("pagina PLAIN truncada (BYTE_ARRAY)")
            out.append(bytes(data[pos:pos + ln]))
            pos += ln
        return out
    raise ParquetError(f"tipo fisico {ptype} desconocido")


def _descomprimir(data, codec, tam):
    if codec == 0:
        return data
    if codec == 1:
        out = snappy_descomprimir(data)
    elif codec == 2:
        try:
            out = zlib.decompress(bytes(data), 47)  # gzip o zlib
        except zlib.error as e:
            raise ParquetError(f"gzip invalido: {e}")
    else:
        nombre = {3: "LZO", 4: "BROTLI", 5: "LZ4", 6: "ZSTD", 7: "LZ4_RAW"}.get(codec, str(codec))
        raise _no_soportado(f"Compresion {nombre} no soportada por el lector puro.")
    if tam is not None and len(out) != tam:
        raise ParquetError(f"pagina descomprimida de {len(out)} bytes (esperado {tam})")
    return out


# ---------------------------------------------------------------------------
# Esquema y conversion logica
# ---------------------------------------------------------------------------
_EPOCH = datetime(1970, 1, 1)
_T_FIS = {0: "boolean", 1: "int32", 2: "int64", 3: "timestamp(int96)", 4: "float", 5: "double",
          6: "binary", 7: "binary"}


def _decimal_str(unscaled, scale):
    if scale <= 0:
        return str(unscaled * (10 ** -scale)) if scale else str(unscaled)
    neg = unscaled < 0
    d = str(abs(unscaled)).rjust(scale + 1, "0")
    return ("-" if neg else "") + d[:-scale] + "." + d[-scale:]


def _fecha_hora(secs, frac, digitos):
    try:
        dt = _EPOCH + timedelta(seconds=secs)
    except OverflowError:
        return None
    s = dt.isoformat(sep=" ")
    if frac:
        s += "." + str(frac).rjust(digitos, "0")
    return s


def _ts(valor, por_seg):
    secs, rem = divmod(valor, por_seg)
    digitos = {1000: 3, 1000000: 6, 1000000000: 9}[por_seg]
    if digitos == 3:
        rem, digitos = rem * 1000, 6  # como str(datetime): microsegundos
    return _fecha_hora(secs, rem, digitos) or str(valor)


def _flotante(v):
    if v != v:
        return "NaN"
    if v in (float("inf"), float("-inf")):
        return "Infinity" if v > 0 else "-Infinity"
    return v


def _f32(v):
    if v != v or v in (float("inf"), float("-inf")):
        return _flotante(v)
    for p in range(6, 10):  # representacion mas corta que ida y vuelta en float32
        s = f"{v:.{p}g}"
        if struct.unpack("<f", struct.pack("<f", float(s)))[0] == v:
            return float(s)
    return v


def _bin_texto(b):
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return "0x" + b.hex()


def _unidad(lt):
    """Unidades por segundo de un TimeType/TimestampType logico (campo 2: MILLIS|MICROS|NANOS)."""
    for k in (lt.get(2) or {}):
        return {1: 1000, 2: 1000000, 3: 1000000000}.get(k, 1000000)
    return 1000000


class _Columna:
    """Una columna plana del esquema: nombre, tipo legible y conversor de valores crudos."""

    def __init__(self, el):
        self.nombre = el.get(4, b"").decode("utf-8", "replace")
        self.ptype = el.get(1)
        self.tlen = el.get(2)
        self.opcional = el.get(3, 0) != 0
        conv = el.get(6)
        lt = el.get(10) or {}
        self.escala = el.get(7) or 0
        self.precision = el.get(8)
        kind = None
        if 1 in lt:
            kind = "string"
        elif 5 in lt:
            kind = "decimal"
            self.escala = lt[5].get(1, self.escala)
            self.precision = lt[5].get(2, self.precision)
        elif 6 in lt:
            kind = "date"
        elif 7 in lt:
            kind = ("time", _unidad(lt[7]))
        elif 8 in lt:
            kind = ("timestamp", _unidad(lt[8]))
        elif 10 in lt:
            kind = ("int", lt[10].get(1, 32), bool(lt[10].get(2, True)))
        elif conv == 0 or conv in (4, 19):
            kind = "string"
        elif conv == 5:
            kind = "decimal"
        elif conv == 6:
            kind = "date"
        elif conv == 7:
            kind = ("time", 1000)
        elif conv == 8:
            kind = ("time", 1000000)
        elif conv == 9:
            kind = ("timestamp", 1000)
        elif conv == 10:
            kind = ("timestamp", 1000000)
        elif conv in (11, 12, 13, 14):
            kind = ("int", {11: 8, 12: 16, 13: 32, 14: 64}[conv], False)
        elif conv in (15, 16, 17, 18):
            kind = ("int", {15: 8, 16: 16, 17: 32, 18: 64}[conv], True)
        if self.ptype == _INT96:
            kind = "int96"
        self.kind = kind
        self.tipo = self._tipo_legible()
        self.convertir = self._conversor()

    def _tipo_legible(self):
        k = self.kind
        if k == "string":
            return "string"
        if k == "decimal":
            return f"decimal({self.precision or '?'},{self.escala})"
        if k == "date":
            return "date"
        if k == "int96":
            return "timestamp"
        if isinstance(k, tuple):
            if k[0] == "int":
                return ("" if k[2] else "u") + f"int{k[1]}"
            if k[0] == "timestamp":
                return "timestamp"
            return "time"
        return _T_FIS.get(self.ptype, "?")

    def _conversor(self):
        k, pt = self.kind, self.ptype
        if k == "int96":
            def f(b):
                nanos = int.from_bytes(b[:8], "little")
                dias = int.from_bytes(b[8:12], "little") - 2440588
                return (_fecha_hora(dias * 86400 + nanos // 10 ** 9, (nanos % 10 ** 9) // 1000, 6)
                        or b.hex())
            return f
        if k == "date":
            return lambda v: (date(1970, 1, 1) + timedelta(days=v)).isoformat() if -719162 <= v <= 2932896 else str(v)
        if k == "decimal":
            esc = self.escala
            if pt in (_INT32, _INT64):
                return lambda v: _decimal_str(v, esc)
            return lambda b: _decimal_str(int.from_bytes(b, "big", signed=True), esc)
        if isinstance(k, tuple) and k[0] == "timestamp":
            return lambda v, u=k[1]: _ts(v, u)
        if isinstance(k, tuple) and k[0] == "time":
            def ft(v, u=k[1]):
                secs, rem = divmod(v, u)
                h, r = divmod(secs, 3600)
                m, s = divmod(r, 60)
                txt = f"{h:02d}:{m:02d}:{s:02d}"
                if rem:
                    txt += "." + str(rem * 1000000 // u).rjust(6, "0")
                return txt
            return ft
        if isinstance(k, tuple) and k[0] == "int":
            bits, signed = k[1], k[2]
            if not signed and pt in (_INT32, _INT64):
                m = (1 << bits) - 1
                return lambda v: v & m
            return None
        if k == "string" or pt in (_BYTE_ARRAY, _FIXED):
            return _bin_texto
        if pt == _FLOAT:
            return _f32
        if pt == _DOUBLE:
            return _flotante
        return None


def _esquema(fm):
    els = fm.get(2) or []
    if not els:
        raise ParquetError("parquet sin esquema")
    raiz = els[0]
    n = raiz.get(5, 0)
    cols = []
    for el in els[1:]:
        nombre = el.get(4, b"?").decode("utf-8", "replace")
        if el.get(5, 0) or el.get(3, 0) == 2:
            raise _no_soportado(f"Columna anidada/repetida '{nombre}' (struct/list/map) no soportada por el lector puro.")
        cols.append(_Columna(el))
    if len(cols) != n:
        raise _no_soportado("Esquema anidado no soportado por el lector puro.")
    return cols


# ---------------------------------------------------------------------------
# Archivo
# ---------------------------------------------------------------------------
MAX_BYTES_DEFECTO = 128 * 1024 * 1024  # tope de bytes comprimidos de un column chunk


class ParquetPuro:
    """Abre un .parquet leyendo solo el footer. `leer_filas(skip, take)` lee lo justo."""

    def __init__(self, path, max_bytes=MAX_BYTES_DEFECTO):
        self.path = path
        self.max_bytes = max_bytes
        try:
            self._abrir()
        except ParquetError:
            raise
        except (OSError,):
            raise
        except (struct.error, IndexError, KeyError, ValueError, TypeError, AttributeError, OverflowError) as e:
            raise ParquetError(f"archivo parquet corrupto: {type(e).__name__}: {e}")

    def _abrir(self):
        import os
        with open(self.path, "rb") as f:
            size = os.fstat(f.fileno()).st_size
            if size < 12:
                raise ParquetError("no es un archivo parquet (muy pequeno)")
            if f.read(4) not in (b"PAR1",):
                raise ParquetError("no es un archivo parquet (falta la marca PAR1 inicial)")
            f.seek(size - 8)
            cola = f.read(8)
            if cola[4:] == b"PARE":
                raise _no_soportado("Archivo parquet cifrado no soportado por el lector puro.")
            if cola[4:] != b"PAR1":
                raise ParquetError("archivo parquet corrupto o truncado (falta la marca PAR1 final)")
            ln = struct.unpack("<I", cola[:4])[0]
            if ln <= 0 or ln > size - 12:
                raise ParquetError("archivo parquet corrupto (tamano de footer invalido)")
            f.seek(size - 8 - ln)
            meta = f.read(ln)
        fm = _Thrift(meta).struct()
        self.columnas = _esquema(fm)
        self.num_filas = int(fm.get(3) or 0)
        self.row_groups = fm.get(4) or []
        sumadas = sum(int(rg.get(3) or 0) for rg in self.row_groups)
        if sumadas != self.num_filas:
            self.num_filas = sumadas

    # -- lectura ---------------------------------------------------------
    def leer_filas(self, skip=0, take=100):
        """Devuelve hasta `take` filas (listas de valores) a partir de `skip`."""
        try:
            return self._leer(skip, take)
        except ParquetError:
            raise
        except (struct.error, IndexError, KeyError, ValueError, TypeError, AttributeError,
                OverflowError, StopIteration) as e:
            raise ParquetError(f"archivo parquet corrupto: {type(e).__name__}: {e}")

    def _leer(self, skip, take):
        filas = []
        visto = 0
        with open(self.path, "rb") as f:
            for rg in self.row_groups:
                n = int(rg.get(3) or 0)
                if visto + n <= skip:
                    visto += n
                    continue
                ini = skip - visto if skip > visto else 0
                faltan = take - len(filas)
                if faltan <= 0:
                    break
                cols = []
                for cc, col in zip(rg.get(1) or [], self.columnas):
                    vals = self._chunk(f, cc.get(3) or {}, col, ini + faltan)
                    vals = vals[ini:ini + faltan]
                    cols.append(self._convertir(col, vals))
                filas.extend([list(r) for r in zip(*cols)] if cols else [[] for _ in range(min(n - ini, faltan))])
                visto += n
        return filas

    @staticmethod
    def _convertir(col, vals):
        fn = col.convertir
        if fn is None:
            return vals
        return [None if v is None else fn(v) for v in vals]

    def _chunk(self, f, md, col, max_filas):
        if md.get(3) and [p.decode("utf-8", "replace") for p in md[3]] != [col.nombre]:
            raise _no_soportado(f"Columna anidada '{'.'.join(p.decode('utf-8', 'replace') for p in md[3])}' no soportada por el lector puro.")
        total = int(md.get(7) or 0)
        if total > self.max_bytes:
            raise ParquetError(f"column chunk de {total} bytes supera el limite de lectura ({self.max_bytes})")
        dpo, dat = md.get(11), md.get(9)
        ini = dpo if dpo and dpo > 0 and (not dat or dpo < dat) else dat
        if ini is None or total <= 0:
            raise ParquetError("metadatos de column chunk invalidos")
        f.seek(ini)
        buf = f.read(total)
        if len(buf) < total:
            raise ParquetError("archivo parquet truncado (column chunk incompleto)")
        codec = md.get(4, 0)
        ptype = md.get(1)
        pos = 0
        dic = None
        out = []
        while pos < len(buf) and len(out) < max_filas:
            tr = _Thrift(buf, pos)
            ph = tr.struct()
            pos = tr.pos
            comp = ph.get(3)
            if comp is None or comp < 0 or pos + comp > len(buf):
                raise ParquetError("pagina truncada")
            page = buf[pos:pos + comp]
            pos += comp
            t = ph.get(1)
            if t == 2:  # DICTIONARY_PAGE
                dh = ph.get(7) or {}
                if dh.get(2) not in (0, 2):
                    raise _no_soportado("Diccionario con encoding no soportado.")
                data = _descomprimir(page, codec, ph.get(2))
                dic = _plain(ptype, data, 0, dh.get(1, 0), col.tlen)
                continue
            if t == 0:  # DATA_PAGE v1
                h = ph.get(5) or {}
                n, enc = h.get(1, 0), h.get(2)
                data = _descomprimir(page, codec, ph.get(2))
                p = 0
                if col.opcional:
                    if h.get(3) not in (3, None):
                        raise _no_soportado("Niveles de definicion con encoding BIT_PACKED no soportados.")
                    ln = int.from_bytes(data[0:4], "little")
                    defs = _rle_hibrido(data, 4, 4 + ln, 1, n)
                    p = 4 + ln
                else:
                    defs = None
                fin = len(data)
            elif t == 3:  # DATA_PAGE v2
                h = ph.get(8) or {}
                n, enc = h.get(1, 0), h.get(4)
                dl, rl = h.get(5, 0), h.get(6, 0)
                if rl:
                    raise _no_soportado("Columna repetida (nested) no soportada por el lector puro.")
                defs = _rle_hibrido(page, rl, rl + dl, 1, n) if col.opcional and dl else (
                    [1] * n if col.opcional else None)
                resto = page[rl + dl:]
                if h.get(7, True) and codec:
                    resto = _descomprimir(resto, codec, (ph.get(2) or 0) - rl - dl)
                data, p, fin = resto, 0, len(resto)
            elif t == 1:  # INDEX_PAGE: se ignora
                continue
            else:
                raise ParquetError(f"tipo de pagina {t} desconocido")
            nn = sum(defs) if defs is not None else n
            if enc == 0:
                vals = _plain(ptype, data, p, nn, col.tlen)
            elif enc in (2, 8):
                if dic is None:
                    raise ParquetError("pagina con diccionario sin DICTIONARY_PAGE")
                bw = data[p]
                idx = _rle_hibrido(data, p + 1, fin, bw, nn)
                vals = [dic[i] for i in idx]
            elif enc == 3 and ptype == _BOOLEAN:
                ln = int.from_bytes(data[p:p + 4], "little")
                vals = [bool(v) for v in _rle_hibrido(data, p + 4, p + 4 + ln, 1, nn)]
            else:
                nombres = {4: "BIT_PACKED", 5: "DELTA_BINARY_PACKED", 6: "DELTA_LENGTH_BYTE_ARRAY",
                           7: "DELTA_BYTE_ARRAY", 9: "BYTE_STREAM_SPLIT"}
                raise _no_soportado(f"Encoding {nombres.get(enc, enc)} no soportado por el lector puro.")
            if defs is None:
                out.extend(vals)
            else:
                it = iter(vals)
                out.extend([next(it) if d else None for d in defs])
        return out
