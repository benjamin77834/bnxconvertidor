"""Datos de entrada propios (src/datos_propios.py): CSV subido / ruta / pegado -> parquet en
<base>/raw/<nombre>, validacion de columnas con mapeo, rutas inseguras y que la generacion
sintetica no pise lo propio. Sin red ni Spark."""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src import datos_propios as dp
from src import orquestador as o
from src import parquet_visor as pv

JOB = '''class PARAMS:
    BASE_PATH = os.environ.get("BNX_BASE_PATH", "s3://x")
cli_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/clientes.dat")
x = cli_df.where("edad > 3").select("id", "nombre", "edad")
'''


@pytest.fixture
def caso(tmp_path):
    job = tmp_path / "j_spark.py"
    job.write_text(JOB, encoding="utf-8")
    plan = {"plan": "t", "nombre": "t", "origen": "plan", "direccion": "prior", "enlaces": [],
            "ejecucion": {"modo": "python", "spark_args": [], "base_path": "", "env": {}},
            "steps": [{"id": "t1", "name": "j", "depends_on": [], "dep_flags": {}, "solo_en_fallo": False,
                       "enabled": True, "continue_on_error": False,
                       "action": {"type": "graph", "target": str(job), "status": "ok", "source": "x.mp"}}]}
    base = tmp_path / "base"
    base.mkdir()
    return plan, str(base)


def _leer(base, nombre="clientes.dat"):
    return pv._leer_parquet(pv.archivos_dataset(os.path.join(base, "raw", nombre))[1], 0, 100)


def test_estado_inicial_falta_y_columnas_esperadas(caso):
    plan, base = caso
    (e,) = dp.estado_entradas(plan, base)
    assert e["estado"] == "falta" and e["ruta"] == "raw/clientes.dat"
    assert sorted(c["name"] for c in e["columnas"]) == ["edad", "id", "nombre"]


def test_csv_texto_pegado_a_parquet_y_marca_propio(caso):
    plan, base = caso
    r = dp.importar(plan, base, "raw/clientes.dat",
                    {"tipo": "texto", "texto": "id,nombre,edad\n001,Ana,30\n002,Luis,\n"})
    assert r["filas"] == 2
    info = _leer(base)
    assert [c["nombre"] for c in info["columnas"]] == ["id", "nombre", "edad"]
    assert info["filas"][0][0] == "001"            # el cero inicial se conserva (tipo esperado texto)
    assert info["filas"][1][2] is None
    man = json.load(open(os.path.join(base, "raw", "_origen.json")))
    assert man["clientes.dat"]["origen"] == "propio"
    assert dp.estado_entradas(plan, base)[0]["estado"] == "propio"


def test_csv_detecta_separador_y_encoding_latin1(caso, tmp_path):
    plan, base = caso
    f = tmp_path / "datos.csv"
    f.write_bytes("id;nombre;edad\n1;José Peña;40\n".encode("latin-1"))
    a = dp.analizar(plan, base, "raw/clientes.dat", {"tipo": "ruta", "ruta": str(f)})
    assert a["delimitador"] == ";" and a["codificacion"] == "latin-1" and a["cabecera"] is True
    assert a["validacion"]["ok"] and a["vista"][0][1] == "José Peña"
    dp.importar(plan, base, "raw/clientes.dat", {"tipo": "ruta", "ruta": str(f)})
    assert _leer(base)["filas"][0][1] == "José Peña"


def test_validacion_faltantes_sobrantes_y_mapeo(caso):
    plan, base = caso
    txt = {"tipo": "texto", "texto": "ID,Nom,edad,extra\n1,Ana,3,x\n"}
    a = dp.analizar(plan, base, "raw/clientes.dat", txt)["validacion"]
    assert a["faltantes"] == ["nombre"] and set(a["sobrantes"]) == {"Nom", "extra"}
    assert a["mapeo"]["ID"] == "id"                          # mayusculas se emparejan solas
    # sin mapear y sin aceptar: se rechaza
    with pytest.raises(dp.DatosError, match="faltan columnas") as ei:
        dp.importar(plan, base, "raw/clientes.dat", txt)
    assert ei.value.extra["codigo"] == "validacion"
    # con mapeo del usuario
    r = dp.importar(plan, base, "raw/clientes.dat", txt, mapeo={"Nom": "nombre"})
    assert r["validacion"]["ok"]
    cols = [c["nombre"] for c in _leer(base)["columnas"]]
    assert cols == ["id", "nombre", "edad", "extra"]


def test_seguir_con_aviso_si_faltan_columnas(caso):
    plan, base = caso
    r = dp.importar(plan, base, "raw/clientes.dat", {"tipo": "texto", "texto": "id,edad\n1,2\n"},
                    aceptar_avisos=True)
    assert r["validacion"]["faltantes"] == ["nombre"]
    assert [c["nombre"] for c in _leer(base)["columnas"]] == ["id", "edad"]


def test_csv_sin_cabecera_usa_nombres_esperados_por_posicion(caso):
    plan, base = caso
    a = dp.analizar(plan, base, "raw/clientes.dat", {"tipo": "texto", "texto": "1,Ana,30\n2,Luis,31\n"})
    assert a["cabecera"] is False and a["validacion"]["ok"]
    assert any("sin cabecera" in x for x in a["avisos_lectura"])


def test_json_y_jsonl(caso, tmp_path):
    plan, base = caso
    f = tmp_path / "d.jsonl"
    f.write_text('{"id": 1, "nombre": "A", "edad": 5}\n{"id": 2, "nombre": "B", "edad": 6}\n')
    r = dp.importar(plan, base, "raw/clientes.dat", {"tipo": "ruta", "ruta": str(f)})
    assert r["filas"] == 2


def test_parquet_ruta_carpeta_se_copia_y_renombra(caso, tmp_path):
    plan, base = caso
    src = tmp_path / "mio"
    o.escribir_parquet(str(src), ["ID", "nombre", "edad"], [{"ID": 1, "nombre": "A", "edad": 2}])
    a = dp.analizar(plan, base, "raw/clientes.dat", {"tipo": "ruta", "ruta": str(src)})
    assert a["formato"] == "parquet" and a["validacion"]["ok"]
    dp.importar(plan, base, "raw/clientes.dat", {"tipo": "ruta", "ruta": str(src)})
    assert [c["nombre"] for c in _leer(base)["columnas"]] == ["id", "nombre", "edad"]


def test_excel_sin_openpyxl_avisa(caso, tmp_path, monkeypatch):
    plan, base = caso
    f = tmp_path / "x.xlsx"
    f.write_bytes(b"PK\x03\x04")
    monkeypatch.setitem(sys.modules, "openpyxl", None)
    with pytest.raises(dp.DatosError, match="openpyxl"):
        dp.analizar(plan, base, "raw/clientes.dat", {"tipo": "ruta", "ruta": str(f)})


def test_tipos_esperados_numericos_se_convierten():
    esp = [{"name": "n", "type": "integer"}, {"name": "d", "type": "decimal"}, {"name": "s", "type": "string"}]
    assert dp._convertir_col(["1", None, "20"], "integer") == ([1, None, 20], "integer")
    assert dp._convertir_col(["1", "2.5"], "decimal") == ([1.0, 2.5], "double")
    assert dp._convertir_col(["007", "1"], "string") == (["007", "1"], "string")
    assert dp._convertir_col(["a", "1"], "integer")[1] == "string"       # no convertible: texto
    carga = {"columnas": ["n", "d", "s"], "tipos_origen": None,
             "filas": [["x", "1.5", "a"], ["y", "2", "b"]]}
    v = dp.validar(carga, esp)
    assert any(a.startswith("n: se espera numerico") for a in v["avisos"])


def test_rutas_inseguras_rechazadas(caso, tmp_path):
    plan, base = caso
    for malo in ("../x", "/etc/passwd", "a/../../b", "a\\b", "", "a//b", "x\x00y"):
        assert not dp.nombre_valido(malo)
    for ruta in ("raw/../../evil", "raw/otro.dat", "clientes.dat/../x"):
        with pytest.raises(dp.DatosError):
            dp.importar(plan, base, ruta, {"tipo": "texto", "texto": "id\n1\n"})
    assert not os.path.exists(os.path.join(base, "evil"))
    with pytest.raises(dp.DatosError, match="s3"):
        dp.estado_entradas(plan, "s3://b/x")
    for malo in ("../x.csv", "a/b.csv", ".", "sin_ext", "x.exe"):
        assert not dp.nombre_archivo_valido(malo)
    with pytest.raises(dp.DatosError):
        dp.analizar(plan, base, "raw/clientes.dat", {"tipo": "staging", "token": "../../etc"})
    with pytest.raises(dp.DatosError):
        dp.analizar(plan, base, "raw/clientes.dat", {"tipo": "ruta", "ruta": str(tmp_path / "noexiste.csv")})


def test_staging_subida_se_importa_y_limpia(caso):
    plan, base = caso
    tok, d = dp.nueva_subida(base)
    with open(os.path.join(d, "mis.csv"), "w") as f:
        f.write("id,nombre,edad\n1,A,2\n")
    fu = {"tipo": "staging", "token": tok}
    assert dp.analizar(plan, base, "raw/clientes.dat", fu)["total_filas"] == 1
    dp.importar(plan, base, "raw/clientes.dat", fu)
    assert not os.path.exists(d)


def test_sintetico_no_pisa_propio_salvo_confirmacion(caso):
    plan, base = caso
    dp.importar(plan, base, "raw/clientes.dat",
                {"tipo": "texto", "texto": "id,nombre,edad\n1,Propio,9\n"})
    rep = o.generar_datos(plan, base, n_rows=5, sobrescribir=True)
    assert rep[0]["estado"] == "propio"
    assert _leer(base)["filas"][0][1] == "Propio"
    rep = o.generar_datos(plan, base, n_rows=5, sobrescribir=True, sobrescribir_propios=True)
    assert rep[0]["estado"] == "generado"
    assert dp.estado_entradas(plan, base)[0]["estado"] == "sintetico"


def test_importar_sobre_propio_pide_confirmacion_y_sobre_sintetico_no(caso):
    plan, base = caso
    o.generar_datos(plan, base, n_rows=3)
    assert dp.estado_entradas(plan, base)[0]["estado"] == "sintetico"
    t1 = {"tipo": "texto", "texto": "id,nombre,edad\n1,A,2\n"}
    dp.importar(plan, base, "raw/clientes.dat", t1)                   # reemplaza sintetico sin pedir
    with pytest.raises(dp.DatosError) as ei:
        dp.importar(plan, base, "raw/clientes.dat", t1)               # ya es propio
    assert ei.value.extra["codigo"] == "existe"
    dp.importar(plan, base, "raw/clientes.dat", t1, sobrescribir=True)


def test_visor_no_lista_el_manifiesto(caso):
    plan, base = caso
    dp.importar(plan, base, "raw/clientes.dat", {"tipo": "texto", "texto": "id,nombre,edad\n1,A,2\n"})
    nombres = [d["nombre"] for d in pv.listar(base)["datasets"]]
    assert nombres == ["clientes.dat"]
