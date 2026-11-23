"""Migracion de grafos: clasificacion, estados, participantes, resumen y exportacion (sin red)."""
import csv
import io
import json
import os
import zipfile

import pytest

from src import migracion_grafos as mg

EJEMPLO = os.path.join(os.path.dirname(__file__), "..", "abinitio", "ejercicio_3_planes")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def datos(tmp_path, monkeypatch):
    monkeypatch.setenv("BNX_MIGRACION_DATA", str(tmp_path / "datos" / "mig.json"))
    return tmp_path / "datos" / "mig.json"


def _mp(path, *lineas):
    with open(str(path), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")


def _analizar(tmp_path, *lineas, nombre="g.mp"):
    p = tmp_path / nombre
    _mp(p, *lineas)
    an = mg.analizar_grafo(str(p))
    return an, mg.clasificar(an["metricas"])


# ---- clasificacion -------------------------------------------------------

def test_simple(tmp_path):
    an, c = _analizar(tmp_path, "NODE Input_File_a : SOURCE", "NODE Reformat : TRANSFORM",
                      "NODE Output_File_b : SINK", "Input_File_a -> Reformat", "Reformat -> Output_File_b")
    assert c["nivel"] == "Simple" and c["razones"]


def test_medio_join_rollup(tmp_path):
    _, c = _analizar(tmp_path, "NODE A : SOURCE", "NODE Join_x : JOIN", "NODE Rollup_y : TRANSFORM")
    assert c["nivel"] == "Medio"
    assert any("join" in r for r in c["razones"]) and any("rollup" in r for r in c["razones"])


def test_alto_subgrafo_cobol_dinamico(tmp_path):
    _, c = _analizar(tmp_path, "SUBGRAPH Sub1 {", "NODE X : TRANSFORM", "}")
    assert c["nivel"] == "Alto" and "subgrafos" in c["razones"][0]
    _, c = _analizar(tmp_path, "NODE Cobol_Reader : TRANSFORM")
    assert c["nivel"] == "Alto" and any("COBOL" in r for r in c["razones"])
    _, c = _analizar(tmp_path, "# $[ejemplo dinamico]", "NODE A : SOURCE")
    assert c["nivel"] == "Alto" and any("dinamica" in r for r in c["razones"])


def test_alto_subgrafo_nativo(tmp_path):
    _, c = _analizar(tmp_path, "{1|XXGgraph|x}", "Subgraph created from graph foo", "NODE A : SOURCE")
    assert c["nivel"] == "Alto"


def test_alto_plan_que_llama_plan(tmp_path):
    a = tmp_path / "a.plan"
    a.write_text("{18|Type|XXGrepository|Primary_Name|XXGplan|x}\n"
                 "{1|XXGplan|1|}\n{2|XXGtask|2|}\n"
                 "{3|XXGplan_task_task|3|x{@1|T1|}1|2|}\n"
                 "run $AI_PLAN/otro.plan y $AI_MP/g1.mp\n", encoding="utf-8")
    an = mg.analizar_grafo(str(a))
    assert an["metricas"]["planes_anidados"] == 1
    c = mg.clasificar(an["metricas"])
    assert c["nivel"] == "Alto" and c["razones"]


def test_fuente_destino_motores(tmp_path):
    an, _ = _analizar(tmp_path, "NODE Input_File_a : SOURCE", "NODE Input_Teradata_t : SOURCE",
                      "NODE Output_Oracle_o : SINK", "NODE Output_Hive_h : SINK",
                      "NODE Output_Mongo_m : SINK", "NODE Input_Table_z : SOURCE")
    assert set(an["fuente"]) == {"archivo", "Teradata", "tabla (motor no detectado)"}
    assert set(an["destino"]) == {"Oracle", "Cloudera", "Mongo"}
    an, c = _analizar(tmp_path, "NODE Input_File_a : SOURCE", "NODE Input_Oracle_t : SOURCE")
    assert c["nivel"] == "Medio" and any("fuentes" in r for r in c["razones"])


# ---- lotes, estados, notas, participantes -----------------------------------

@pytest.fixture
def lote(datos):
    """Carpeta sintetica bajo abinitio/ (la validacion exige estar ahi); se borra al terminar."""
    nombre = "zz_test_migracion_%d" % os.getpid()
    carpeta = os.path.join(ROOT, "abinitio", nombre)
    os.makedirs(carpeta)
    try:
        _mp(os.path.join(carpeta, "uno.mp"), "NODE Input_File_a : SOURCE", "NODE Output_File_b : SINK")
        _mp(os.path.join(carpeta, "dos.mp"), "NODE A : SOURCE", "NODE Join_x : JOIN")
        _mp(os.path.join(carpeta, "tres.mp"), "SUBGRAPH S {", "NODE X : TRANSFORM", "}")
        with open(os.path.join(carpeta, "uno_1.pset"), "w") as f:
            f.write("!prototype||||$AI_MP/uno.mp\n")
        st, r = mg.handle("cargar", {"carpeta": "abinitio/" + nombre})
        assert st == 200, r
        yield r["lote"]["id"]
    finally:
        for f in os.listdir(carpeta):
            os.remove(os.path.join(carpeta, f))
        os.rmdir(carpeta)


def _grafos(lote_id):
    return {g["archivo"]: g for g in mg.handle("grafos", {"lote": lote_id})[1]["grafos"]}


def test_carga_clasifica_y_psets(lote):
    gs = _grafos(lote)
    assert {k: v["nivel"] for k, v in gs.items()} == {"uno.mp": "Simple", "dos.mp": "Medio", "tres.mp": "Alto"}
    assert all(v["razones"] for v in gs.values())
    assert gs["uno.mp"]["psets"] == ["uno_1.pset"]
    assert gs["uno.mp"]["fuente"] == ["archivo"] and gs["uno.mp"]["destino"] == ["archivo"]


def test_estados_historial(lote):
    gid = _grafos(lote)["uno.mp"]["id"]
    st, r = mg.handle("estado", {"id": gid, "estado": "en migracion", "nota": "arranca"})
    assert st == 200 and r["grafo"]["estado"] == "en migracion"
    mg.handle("estado", {"id": gid, "estado": "validado"})
    st, r = mg.handle("estado", {"id": gid, "estado": "pendiente", "nota": "retroceso"})  # retroceder se permite
    assert st == 200
    h = r["grafo"]["historial"]
    assert [x["a"] for x in h] == ["en migracion", "validado", "pendiente"]
    assert h[0]["nota"] == "arranca" and h[0]["fecha"] and h[0]["de"] == "pendiente"
    st, r = mg.handle("estado", {"id": gid, "estado": "inventado"})
    assert st == 400 and r["ok"] is False
    assert _grafos(lote)["uno.mp"]["estado"] == "pendiente"


def test_clasificacion_manual_y_rescan(lote):
    gs = _grafos(lote)
    gid = gs["uno.mp"]["id"]
    mg.handle("clasificar", {"id": gid, "nivel": "Alto", "nota": "por regla de negocio"})
    mg.handle("estado", {"id": gid, "estado": "convertido", "nota": "ok"})
    mg.handle("nota", {"id": gid, "texto": "una nota"})
    mg.handle("asignar", {"id": gid, "rol": "qa", "nombre": "Persona Ficticia", "correo": "ficticia@example.com"})
    carpeta = mg.cargar()["lotes"][lote]["carpeta"]
    st, r = mg.handle("cargar", {"carpeta": carpeta})
    assert st == 200 and r["nuevos"] == 0
    g = _grafos(lote)["uno.mp"]
    assert g["nivel"] == "Alto" and g["es_manual"] is True
    assert g["razones"] and g["estado"] == "convertido" and len(g["notas"]) == 1
    assert len(g["participantes"]) == 1 and len(g["historial"]) == 1
    mg.handle("clasificar", {"id": gid, "nivel": None})
    assert _grafos(lote)["uno.mp"]["nivel"] == "Simple"
    assert mg.handle("clasificar", {"id": gid, "nivel": "Raro"})[0] == 400


def test_participantes_y_personas(lote):
    gs = _grafos(lote)
    g1, g2 = gs["uno.mp"]["id"], gs["dos.mp"]["id"]
    for rol in mg.ROLES:
        st, _ = mg.handle("asignar", {"id": g1, "rol": rol, "nombre": "Ana Ficticia", "correo": "ana@example.com"})
        assert st == 200
    mg.handle("asignar", {"id": g2, "rol": "responsable", "nombre": "A. Ficticia", "correo": "ANA@example.com"})
    personas = mg.handle("personas", {})[1]["personas"]
    assert len(personas) == 1  # reutilizada por correo
    pid = personas[0]["id"]
    assert mg.handle("asignar", {"id": g1, "rol": "jefe", "persona_id": pid})[0] == 400
    assert mg.handle("asignar", {"id": g1, "rol": "qa", "persona_id": "p_nope"})[0] == 400
    # el grafo solo guarda persona_id
    raw = mg.cargar()["grafos"][g1]["participantes"]
    assert all(set(p) == {"persona_id", "rol"} for p in raw)
    st, r = mg.handle("persona_borrar", {"id": pid})
    assert st == 400
    mg.handle("persona_guardar", {"id": pid, "nombre": "Ana Corregida", "correo": "ana@example.com"})
    assert _grafos(lote)["dos.mp"]["participantes"][0]["nombre"] == "Ana Corregida"
    mg.handle("quitar", {"id": g1, "persona_id": pid})
    mg.handle("quitar", {"id": g2, "persona_id": pid})
    assert mg.handle("persona_borrar", {"id": pid})[0] == 200
    # asignar por persona_id del catalogo
    p2 = mg.handle("persona_guardar", {"nombre": "Beto Ficticio", "correo": "beto@example.com"})[1]["persona"]
    assert mg.handle("asignar", {"id": g1, "rol": "revisor", "persona_id": p2["id"]})[0] == 200


def test_resumen(lote):
    gs = _grafos(lote)
    mg.handle("asignar", {"id": gs["uno.mp"]["id"], "rol": "dueno", "nombre": "Ana Ficticia"})
    mg.handle("asignar", {"id": gs["dos.mp"]["id"], "rol": "responsable", "nombre": "Ana Ficticia"})
    mg.handle("estado", {"id": gs["dos.mp"]["id"], "estado": "en produccion"})
    r = mg.handle("resumen", {"lote": lote})[1]
    assert r["total"] == 3
    assert r["niveles"]["Simple"]["porcentaje"] == 33.3 and r["niveles"]["Simple"]["meta"] == 50
    assert r["niveles"]["Simple"]["diferencia"] == -16.7
    assert r["estados"]["pendiente"]["cantidad"] == 2 and r["estados"]["en produccion"]["cantidad"] == 1
    p = r["personas"][0]
    assert p["total"] == 2 and p["abiertos"] == 1 and p["roles"] == {"dueno": 1, "responsable": 1}


def test_exportar_csv_y_xlsx(lote):
    gs = _grafos(lote)
    gid = gs["uno.mp"]["id"]
    mg.handle("asignar", {"id": gid, "rol": "qa", "nombre": "=cmd Ñandú", "correo": "n@example.com"})
    mg.handle("clasificar", {"id": gid, "nivel": "Medio"})
    st, r = mg.handle("exportar", {"lote": lote, "fmt": "csv"})
    cont, nombre, ctype = r["binario"]
    assert nombre.endswith(".csv") and "csv" in ctype and cont.startswith(b"\xef\xbb\xbf")
    filas = list(csv.reader(io.StringIO(cont.decode("utf-8-sig"))))
    assert filas[0] == mg._COLUMNAS and len(filas) == 4
    uno = next(f for f in filas if f[0] == "uno.mp")
    assert "qa: =cmd Ñandú" in uno[9] and uno[3] == "si"
    assert [mg._celda(x) for x in ("=1+1", "+x", "-x", "@x", "ok")] == ["'=1+1", "'+x", "'-x", "'@x", "ok"]
    st, r = mg.handle("exportar", {"lote": lote, "fmt": "xlsx"})
    z = zipfile.ZipFile(io.BytesIO(r["binario"][0]))
    assert z.testzip() is None
    hoja = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert "uno.mp" in hoja and "Ñandú" in hoja
    assert mg.handle("exportar", {"lote": lote, "fmt": "pdf"})[0] == 400


def test_persistencia(lote, datos):
    gid = _grafos(lote)["dos.mp"]["id"]
    mg.handle("estado", {"id": gid, "estado": "en revision", "nota": "x"})
    d = json.loads(datos.read_text(encoding="utf-8"))
    assert d["grafos"][gid]["estado"] == "en revision" and d["version"] == 1
    assert not os.path.exists(str(datos) + ".tmp")


def test_carpeta_fuera_de_abinitio(datos, tmp_path):
    assert mg.handle("cargar", {"carpeta": str(tmp_path)})[0] == 400
    assert mg.handle("cargar", {"carpeta": "abinitio/../src"})[0] == 400
    assert mg.handle("cargar", {})[0] == 400
    assert mg.handle("grafos", {"lote": "l_nope"})[0] == 400
    assert mg.handle("nada", {})[0] == 404


@pytest.mark.skipif(not os.path.isdir(EJEMPLO), reason="sin la carpeta de ejemplo")
def test_ejercicio_3_planes_real(datos):
    st, r = mg.handle("cargar", {"carpeta": "abinitio/ejercicio_3_planes"})
    assert st == 200 and r["grafos"] >= 3
    gs = mg.handle("grafos", {"lote": r["lote"]["id"]})[1]["grafos"]
    assert any(g["tipo"] == "plan" for g in gs) and any(g["tipo"] == "grafo" for g in gs)
    assert all(g["razones"] and g["nivel"] in mg.NIVELES for g in gs)
    ing = next(g for g in gs if g["archivo"] == "ingesta_clientes.mp")
    assert ing["fuente"] and ing["destino"] and ing["psets"]
