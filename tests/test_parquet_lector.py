"""Lector parquet puro-python (src/parquet_lector.py) y visor (src/parquet_visor.py + endpoints
`datasets` / `leer_parquet` de serve_ui.py). Los .parquet de tests/fixtures/parquet los escribio
Spark 4.1 (snappy / INT96+gzip / zstd) con 300 filas: fila k -> id=k, nom=None si k%5==0, ..."""
import json
import os
import shutil
import struct
import threading
import urllib.error
import urllib.request
import pytest
from src import parquet_lector as pl
from src import parquet_puro
from src import parquet_visor as pv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, "tests", "fixtures", "parquet")

def _fix(n):
    return os.path.join(FIX, n)


def _val(v):
    return pv._json_val(v)


# ---------------------------------------------------------------------------
# snappy
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("comprimido,esperado", [
    (b"\x00", b""),
    (b"\x05\x10hello", b"hello"),
    (b"\x0c\x08abc\x22\x03\x00", b"abcabcabcabc"),          # copia de 2 bytes de offset, solapada
    (b"\x08\x08abc\x05\x03", b"abcabcab"),                   # copia de 1 byte de offset
    (b"\x64\xf0\x63" + bytes(range(100)), bytes(range(100))),  # literal largo (len en 1 byte extra)
    (b"\x07\x00a" + bytes([((6 - 1) << 2) | 3]) + struct.pack("<I", 1), b"a" * 7),  # offset de 4 bytes
])
def test_snappy_vectores_conocidos(comprimido, esperado):
    assert pl.snappy_descomprimir(comprimido) == esperado


@pytest.mark.parametrize("malo", [
    b"",                                  # sin cabecera
    b"\x05\x10hel",                       # literal truncado
    b"\x04\x00a\x0d\x00",                 # offset 0
    b"\x04\x00a\x0d\x09",                 # offset mayor que lo escrito
    b"\x09\x10hello",                     # longitud declarada distinta
])
def test_snappy_corrupto(malo):
    with pytest.raises(pl.ParquetError):
        pl.snappy_descomprimir(malo)


def test_snappy_contra_pyarrow():
    pytest.importorskip("pyarrow")
    import pyarrow as pa_
    datos = b"".join(b"fila %d de datos repetidos;" % (i % 17) for i in range(5000))
    datos += os.urandom(3000)
    comp = pa_.compress(datos, codec="snappy", asbytes=True)
    assert pl.snappy_descomprimir(comp) == datos


# ---------------------------------------------------------------------------
# archivos escritos por Spark 4.1
# ---------------------------------------------------------------------------
def _esperado(k):
    return {"id": k, "nom": None if k % 5 == 0 else f"nombre ñ {k}", "cat": ["A", "B", "C"][k % 3],
            "b": None if k % 4 == 0 else k % 2 == 0, "dt": None, "sh": k % 100, "by": k % 100 - 50}


@pytest.mark.parametrize("nombre", ["spark_snappy.parquet", "spark_int96_gzip.parquet"])
def test_spark_tipos_nulos_y_diccionario(nombre):
    pf = pl.ParquetPuro(_fix(nombre))
    assert pf.num_filas == 300
    cols = {c.nombre: c.tipo for c in pf.columnas}
    assert cols["id"] == "int64" and cols["i"] == "int32" and cols["nom"] == "string"
    assert cols["dec"] == "decimal(12,2)" and cols["dt"] == "date" and cols["ts"] == "timestamp"
    assert cols["b"] == "boolean" and cols["d"] == "double" and cols["f"] == "float"
    assert cols["sh"] == "int16" and cols["by"] == "int8" and cols["bin"] == "binary"
    nombres = [c.nombre for c in pf.columnas]
    filas = pf.leer_filas(0, 1000)
    assert len(filas) == 300
    for k in (0, 1, 5, 7, 20, 299):
        r = dict(zip(nombres, filas[k]))
        e = _esperado(k)
        assert r["id"] == k and r["nom"] == e["nom"] and r["cat"] == e["cat"] and r["b"] == e["b"]
        assert r["sh"] == e["sh"] and r["by"] == e["by"]
        assert r["i"] == (None if k % 7 == 0 else k - 150)
        assert r["d"] == (k * 1.5 if k % 11 else None)
        assert r["dt"] == str(__import__("datetime").date(2020, 1, 1) + __import__("datetime").timedelta(days=k))
        assert r["dec"] == (f"{k}.{k % 100:02d}" if k % 9 else None)
        assert r["dec_big"] == f"-{k}.12345"
        assert r["bin"] == f"ab{k}"
        assert r["f"] == (round(k / 10, 1) if k % 13 else None)
    # timestamps: 12:00 + k*3601s + k us, almacenados en UTC (zona local del que escribio)
    assert len({r[nombres.index("ts")] for r in filas}) == 300


def test_spark_int96_igual_que_micros():
    a = pl.ParquetPuro(_fix("spark_snappy.parquet")).leer_filas(0, 300)
    b = pl.ParquetPuro(_fix("spark_int96_gzip.parquet")).leer_filas(0, 300)
    assert a == b  # mismo contenido: TIMESTAMP_MICROS+snappy vs INT96+gzip


def test_limite_y_offset():
    pf = pl.ParquetPuro(_fix("spark_snappy.parquet"))
    todas = pf.leer_filas(0, 300)
    assert pf.leer_filas(0, 10) == todas[:10]
    assert pf.leer_filas(290, 100) == todas[290:]
    assert pf.leer_filas(100, 25) == todas[100:125]
    assert pf.leer_filas(300, 10) == []
    assert pf.leer_filas(5000, 10) == []


def test_zstd_no_soportado_sugiere_pyarrow():
    pf = pl.ParquetPuro(_fix("spark_zstd.parquet"))
    with pytest.raises(pl.ParquetNoSoportado) as e:
        pf.leer_filas(0, 5)
    assert "ZSTD" in str(e.value) and "pyarrow" in str(e.value)


def test_archivo_corrupto(tmp_path):
    datos = open(_fix("spark_snappy.parquet"), "rb").read()
    casos = {
        "vacio.parquet": b"",
        "texto.parquet": b"esto no es parquet, solo texto largo largo largo",
        "truncado.parquet": datos[:len(datos) // 2],
        "sin_pie.parquet": datos[:-4] + b"XXXX",
        "footer_malo.parquet": datos[:-8] + struct.pack("<I", 10 ** 8) + b"PAR1",
        "footer_basura.parquet": datos[:-40] + os.urandom(32) + datos[-8:],
    }
    for n, c in casos.items():
        p = tmp_path / n
        p.write_bytes(c)
        with pytest.raises(pl.ParquetError):
            pl.ParquetPuro(str(p)).leer_filas(0, 5)
    # cuerpo corrupto con footer valido -> ParquetError, no una excepcion cruda
    mal = bytearray(datos)
    for i in range(4, 400):
        mal[i] ^= 0xFF
    p = tmp_path / "cuerpo.parquet"
    p.write_bytes(bytes(mal))
    with pytest.raises(pl.ParquetError):
        pl.ParquetPuro(str(p)).leer_filas(0, 300)


# ---------------------------------------------------------------------------
# contra pyarrow (si esta instalado) y contra parquet_puro (nuestro escritor)
# ---------------------------------------------------------------------------
def _comparar(path, **kw):
    pq = pytest.importorskip("pyarrow.parquet")
    pf = pl.ParquetPuro(path)
    t = pq.read_table(path)
    ref = [[_val(x) for x in r] for r in zip(*[c.to_pylist() for c in t.columns])]
    assert pf.num_filas == t.num_rows
    assert pf.leer_filas(0, 10 ** 6) == ref
    n = t.num_rows
    assert pf.leer_filas(n // 3, 7) == ref[n // 3:n // 3 + 7]
    return pf


@pytest.mark.parametrize("comp", ["none", "snappy", "gzip"])
@pytest.mark.parametrize("dic", [True, False])
@pytest.mark.parametrize("version", ["1.0", "2.0"])
def test_pyarrow_variantes(tmp_path, comp, dic, version):
    pa_ = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    import datetime as dt
    import decimal
    n = 523
    t = pa_.table({
        "id": pa_.array(range(n), pa_.int64()),
        "i32": pa_.array([None if i % 6 == 0 else i - 100 for i in range(n)], pa_.int32()),
        "txt": pa_.array([None if i % 4 == 0 else f"t{i % 9}-é" for i in range(n)]),
        "dbl": pa_.array([None if i % 8 == 0 else i / 3 for i in range(n)]),
        "ok": pa_.array([None if i % 5 == 0 else i % 3 == 0 for i in range(n)]),
        "dec": pa_.array([decimal.Decimal(f"{i}.50") if i % 7 else None for i in range(n)], pa_.decimal128(10, 2)),
        "dia": pa_.array([dt.date(2021, 1, 1) + dt.timedelta(days=i) for i in range(n)]),
        "ts": pa_.array([dt.datetime(2022, 5, 5, 1, 2, 3, i) for i in range(n)], pa_.timestamp("us")),
        "ts_ms": pa_.array([dt.datetime(2022, 5, 5, 1, 2, 3, i * 1000) for i in range(n)], pa_.timestamp("ms")),
        "u8": pa_.array([i % 256 for i in range(n)], pa_.uint8()),
        "u64": pa_.array([2 ** 63 + i for i in range(n)], pa_.uint64()),
        "bin": pa_.array([b"\x00\xff%d" % i for i in range(n)]),
    })
    p = str(tmp_path / "x.parquet")
    pq.write_table(t, p, compression=comp, use_dictionary=dic, data_page_version=version,
                   row_group_size=100, data_page_size=512)
    pf = pl.ParquetPuro(p)
    assert len(pf.row_groups) > 1
    ref = [[_val(x) for x in r] for r in zip(*[c.to_pylist() for c in t.columns])]
    filas = pf.leer_filas(0, 10 ** 6)
    # uint64 no cabe en INT64 con signo en el ref de pyarrow: se compara igual (python int)
    assert filas == ref
    assert pf.leer_filas(95, 120) == ref[95:215]
    assert pf.leer_filas(500, 100) == ref[500:]


def test_pyarrow_booleano_dictionary_vacio_y_todo_nulo(tmp_path):
    pa_ = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    t = pa_.table({"a": pa_.array([None] * 30, pa_.string()), "b": pa_.array([1] * 30, pa_.int64())})
    p = str(tmp_path / "n.parquet")
    pq.write_table(t, p)
    assert pl.ParquetPuro(p).leer_filas(0, 5) == [[None, 1]] * 5
    pq.write_table(t.slice(0, 0), str(tmp_path / "v.parquet"))
    assert pl.ParquetPuro(str(tmp_path / "v.parquet")).leer_filas(0, 5) == []


def test_pyarrow_anidado_no_soportado(tmp_path):
    pa_ = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    p = str(tmp_path / "nest.parquet")
    pq.write_table(pa_.table({"l": pa_.array([[1, 2], [3]])}), p)
    with pytest.raises(pl.ParquetNoSoportado) as e:
        pl.ParquetPuro(p)
    assert "pyarrow" in str(e.value)


def test_parquet_puro_escritor_roundtrip(tmp_path):
    filas = [{"a": i, "b": None if i % 3 == 0 else f"x{i}", "c": i / 2, "d": i % 2 == 0} for i in range(250)]
    p = str(tmp_path / "w.parquet")
    parquet_puro.escribir(p, ["a", "b", "c", "d"], filas)
    pf = pl.ParquetPuro(p)
    assert [(c.nombre, c.tipo) for c in pf.columnas] == [("a", "int64"), ("b", "string"), ("c", "double"), ("d", "boolean")]
    got = pf.leer_filas(0, 1000)
    assert got == [[r["a"], r["b"], r["c"], r["d"]] for r in filas]
    try:
        import pyarrow.parquet  # noqa: F401
    except ImportError:
        return
    _comparar(p)


# ---------------------------------------------------------------------------
# visor: listado, validacion de rutas, motores
# ---------------------------------------------------------------------------
@pytest.fixture()
def base(tmp_path):
    b = tmp_path / "ej"
    d1 = b / "raw" / "entrada"
    d2 = b / "output" / "salida_$X.tmp"
    d1.mkdir(parents=True)
    d2.mkdir(parents=True)
    shutil.copy(_fix("spark_snappy.parquet"), d1 / "part-00000.snappy.parquet")
    shutil.copy(_fix("spark_snappy.parquet"), d2 / "part-00000-abc-c000.snappy.parquet")
    shutil.copy(_fix("spark_snappy.parquet"), d2 / "part-00001-abc-c000.snappy.parquet")
    (d2 / "_SUCCESS").write_text("")
    (d2 / ".part-00000.crc").write_bytes(b"crc")
    (b / "output" / "suelto.parquet").write_bytes(open(_fix("spark_int96_gzip.parquet"), "rb").read())
    (b / "output" / "datos.csv").write_text("a,b\n1,x\n2,y\n3,z\n")
    (b / "output" / "vacia").mkdir()
    return str(b)


@pytest.fixture()
def motor_puro(monkeypatch):
    monkeypatch.setenv("BNX_PARQUET_MOTOR", "puro")


def test_listar(base):
    r = pv.listar(base)
    por = {(d["zona"], d["nombre"]): d for d in r["datasets"]}
    assert set(por) == {("raw", "entrada"), ("output", "salida_$X.tmp"), ("output", "suelto.parquet"),
                        ("output", "datos.csv")}
    assert por[("output", "salida_$X.tmp")]["archivos"] == 2 and por[("output", "salida_$X.tmp")]["formato"] == "parquet"
    assert por[("output", "datos.csv")]["formato"] == "csv"
    assert por[("raw", "entrada")]["bytes"] > 0 and por[("raw", "entrada")]["modificado"]


def test_leer_motor_puro_nombres_con_dolar_y_puntos(base, motor_puro):
    r = pv.leer(base, "output", "salida_$X.tmp", 50, 0)
    assert r["motor"] == "puro-python" and r["total_filas"] == 600 and len(r["filas"]) == 50
    assert r["columnas"][0] == {"nombre": "id", "tipo": "int64"}
    # offset que cruza al segundo archivo del dataset
    r2 = pv.leer(base, "output", "salida_$X.tmp", 20, 290)
    assert [f[0] for f in r2["filas"]] == list(range(290, 300)) + list(range(10))
    json.dumps(r2)  # serializable


def test_leer_limites(base, motor_puro):
    assert len(pv.leer(base, "raw", "entrada", 99999, 0)["filas"]) == 300  # tope 1000, hay 300
    assert pv.leer(base, "raw", "entrada", 0, 0)["limite"] == 1
    assert pv.leer(base, "raw", "entrada", 5000, 0)["limite"] == pv.LIMITE_MAX
    assert pv.leer(base, "raw", "entrada", 10, -5)["offset"] == 0
    with pytest.raises(pv.VisorError):
        pv.leer(base, "raw", "entrada", "abc", 0)
    assert pv.leer(base, "raw", "entrada")["limite"] == pv.LIMITE_DEFECTO


def test_leer_csv_y_archivo_suelto(base, motor_puro):
    c = pv.leer(base, "output", "datos.csv", 2, 1)
    assert c["motor"] == "csv" and c["total_filas"] == 3 and c["filas"] == [["2", "y"], ["3", "z"]]
    s = pv.leer(base, "output", "suelto.parquet", 5, 0)
    assert s["total_filas"] == 300 and s["archivos"] == 1


def test_leer_error_zstd_y_corrupto(base, motor_puro, monkeypatch):
    shutil.copy(_fix("spark_zstd.parquet"), os.path.join(base, "output", "zstd.parquet"))
    with pytest.raises(pv.VisorError) as e:
        pv.leer(base, "output", "zstd.parquet")
    assert e.value.codigo == "no_soportado" and "pyarrow" in str(e.value)
    open(os.path.join(base, "output", "roto.parquet"), "wb").write(b"PAR1basura" * 10)
    with pytest.raises(pv.VisorError) as e:
        pv.leer(base, "output", "roto.parquet")
    assert e.value.codigo == "corrupto"


def test_leer_pyarrow_igual_que_puro(base, monkeypatch):
    pytest.importorskip("pyarrow")
    monkeypatch.setenv("BNX_PARQUET_MOTOR", "pyarrow")
    a = pv.leer(base, "output", "salida_$X.tmp", 1000, 100)
    monkeypatch.setenv("BNX_PARQUET_MOTOR", "puro")
    b = pv.leer(base, "output", "salida_$X.tmp", 1000, 100)
    assert a["motor"] == "pyarrow" and b["motor"] == "puro-python"
    assert a["total_filas"] == b["total_filas"] and len(a["filas"]) == len(b["filas"])
    idx = [c["nombre"] for c in a["columnas"]]
    for ra, rb in zip(a["filas"], b["filas"]):
        for n, x, y in zip(idx, ra, rb):
            if n == "f" and x is not None:
                assert abs(x - y) < 1e-6
            elif n == "ts" and x is not None:
                assert str(x).startswith(str(y))  # pyarrow agrega +00:00
            else:
                assert x == y


@pytest.mark.parametrize("zona,nombre", [
    ("raw", ".."), ("raw", "../output"), ("output", "../raw/entrada"), ("raw", "a/b"), ("raw", "a\\b"),
    ("raw", "/etc/passwd"), ("raw", ""), ("raw", None), ("raw", "x..y"), ("output", "C:evil"),
    ("tmp", "entrada"), ("", "entrada"), (None, "entrada"), ("../raw", "entrada"), ("raw/", "entrada"),
])
def test_validacion_nombre_y_zona(base, zona, nombre):
    with pytest.raises(pv.VisorError):
        pv.leer(base, zona, nombre)


@pytest.mark.parametrize("bp", ["", None, "relativa/ruta", "../x", "s3://bucket/pre", "/", "/no/existe/jamas"])
def test_validacion_base(bp):
    with pytest.raises(pv.VisorError):
        pv.listar(bp)
    with pytest.raises(pv.VisorError):
        pv.leer(bp, "raw", "x")


def test_s3_mensaje_claro():
    with pytest.raises(pv.VisorError) as e:
        pv.listar("s3://bucket/pre")
    assert "s3" in str(e.value) and e.value.codigo == "no_soportado"


@pytest.mark.skipif(os.name == "nt", reason="symlinks")
def test_symlink_fuera_de_la_zona(base, tmp_path):
    fuera = tmp_path / "fuera"
    fuera.mkdir()
    shutil.copy(_fix("spark_snappy.parquet"), fuera / "a.parquet")
    os.symlink(str(fuera), os.path.join(base, "raw", "escape"))
    with pytest.raises(pv.VisorError):
        pv.leer(base, "raw", "escape")
    assert "escape" not in {d["nombre"] for d in pv.listar(base)["datasets"]}


# ---------------------------------------------------------------------------
# endpoints HTTP
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def srv():
    import socketserver
    import serve_ui

    class S(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        daemon_threads = True
    httpd = S(("127.0.0.1", 0), serve_ui.BNXHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}/api/orquestador"
    httpd.shutdown()
    httpd.server_close()


def _post(srv, action, body):
    req = urllib.request.Request(f"{srv}/{action}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_endpoint_datasets_y_leer(srv, base, monkeypatch):
    monkeypatch.setenv("BNX_PARQUET_MOTOR", "puro")
    st, d = _post(srv, "datasets", {"base_path": base})
    assert st == 200 and d["ok"] and len(d["datasets"]) == 4
    st, d = _post(srv, "leer_parquet", {"base_path": base, "zona": "raw", "nombre": "entrada", "limite": 10, "offset": 5})
    assert st == 200 and d["total_filas"] == 300 and len(d["filas"]) == 10 and d["filas"][0][0] == 5
    assert d["motor"] == "puro-python" and d["columnas"][0]["nombre"] == "id"


def test_endpoint_validacion(srv, base):
    casos = [
        ("leer_parquet", {"base_path": base, "zona": "raw", "nombre": "../output"}),
        ("leer_parquet", {"base_path": base, "zona": "raw", "nombre": "a/b"}),
        ("leer_parquet", {"base_path": base, "zona": "etc", "nombre": "entrada"}),
        ("leer_parquet", {"base_path": "relativa", "zona": "raw", "nombre": "entrada"}),
        ("leer_parquet", {"base_path": "s3://b/p", "zona": "raw", "nombre": "entrada"}),
        ("leer_parquet", {"base_path": base, "zona": "raw", "nombre": "no_existe"}),
        ("leer_parquet", {"base_path": base, "zona": "raw", "nombre": "entrada", "limite": "abc"}),
        ("datasets", {"base_path": "relativa"}),
        ("datasets", {"base_path": ""}),
        ("datasets", {}),
    ]
    for accion, body in casos:
        st, d = _post(srv, accion, body)
        assert st == 400 and d["ok"] is False and d["error"], (accion, body, st, d)


def test_visor_dataset_anidado_ruta_absoluta_del_banco(tmp_path):
    """INPUT_FILE=/opt/c230/.../MX_ACCT_CLEAR_KEYS.txt deja el dataset en
    raw/opt/c230/.../MX_ACCT_CLEAR_KEYS.txt/part-00000.parquet: el visor debe listarlo
    con su ruta relativa y poder leerlo, sin permitir escapar de la zona."""
    import pytest
    from src import parquet_puro, parquet_visor as V
    d = tmp_path / "raw" / "opt" / "c230" / "inbox" / "MX_KEYS.txt"
    d.mkdir(parents=True)
    parquet_puro.escribir(str(d / "part-00000.parquet"), ["a"], [{"a": "x"}, {"a": "y"}])
    (tmp_path / "output").mkdir()
    nombres = [x["nombre"] for x in V.listar(str(tmp_path))["datasets"]]
    assert "opt/c230/inbox/MX_KEYS.txt" in nombres
    r = V.leer(str(tmp_path), "raw", "opt/c230/inbox/MX_KEYS.txt")
    assert r["total_filas"] == 2
    for malo in ("opt/../../output", "/opt/c230", "opt//c230", "opt\\c230", "C:/x"):
        with pytest.raises(V.VisorError):
            V.resolver(str(tmp_path), "raw", malo)
