"""Presentacion ejecutiva: estimacion, cifras desde reportes de prueba y generacion pptx/pdf (sin red)."""
import io
import json
import os

import pytest

from src import presentacion as pr


def _proyecto(tmp_path, monkeypatch, nombre="proy"):
    """Proyecto de prueba (output + abinitio) en un repo falso."""
    monkeypatch.setattr(pr, "_ROOT", str(tmp_path))
    out = tmp_path / "output" / nombre
    ab = tmp_path / "abinitio" / nombre
    out.mkdir(parents=True)
    ab.mkdir(parents=True)
    (out / "reporte_lote.md").write_text(
        "# Reporte\n| Grafo | OK | Accuracy | Nodos | Pset detectado | Seg | Error |\n|---|---|---|---|---|---|---|\n"
        "| a.mp | si | 90.0 | 3/3 | (ninguno) | 0.1 |  |\n"
        "| 1_b.mp | si | 80.0 | 3/3 | (ninguno) | 0.1 |  |\n"
        "| c.mp | no | 0 | 0/0 | (ninguno) | 0.1 | falla |\n", encoding="utf-8")
    (ab / "a.mp").write_text("NODE Input_File_a : SOURCE\nNODE Reformat : TRANSFORM\nNODE Output_File_b : SINK\n"
                             "Input_File_a -> Reformat\nReformat -> Output_File_b\n", encoding="utf-8")
    (ab / "1_b.mp").write_text("NODE Input_File_a : SOURCE\nNODE Join_x : JOIN\nNODE Output_File_b : SINK\n"
                               "Input_File_a -> Join_x\nJoin_x -> Output_File_b\n", encoding="utf-8")
    (out / "orquestacion_p.json").write_text("{}", encoding="utf-8")
    (out / "datos").mkdir()
    (out / "datos" / "_SUCCESS").write_text("", encoding="utf-8")
    return nombre


def test_cifras_desde_reporte(tmp_path, monkeypatch):
    n = _proyecto(tmp_path, monkeypatch)
    d = pr.recolectar([n])
    t = d["total"]
    assert t["convertidos"] == 2 and t["accuracy"] == 85.0  # el grafo con error no cuenta
    assert t["niveles"]["Medio"] == 1 and t["niveles"]["Simple"] == 1
    assert t["orquestaciones"] == 1 and t["salidas_ok"] == 1


def test_sin_dato_cuando_no_hay_mp_ni_ejecucion(tmp_path, monkeypatch):
    n = _proyecto(tmp_path, monkeypatch)
    os.remove(str(tmp_path / "abinitio" / n / "a.mp"))
    os.remove(str(tmp_path / "output" / n / "datos" / "_SUCCESS"))
    d = pr.recolectar([n])
    assert d["total"]["sin_clasificar"] == 1 and d["total"]["salidas_ok"] == 0
    assert "sin clasificar" in pr.texto_plano(pr.preparar({"proyectos": [n]})[5])


def test_proyecto_invalido(tmp_path, monkeypatch):
    _proyecto(tmp_path, monkeypatch)
    with pytest.raises(pr.PresentacionError):
        pr.recolectar(["../etc"])
    with pytest.raises(pr.PresentacionError):
        pr.recolectar([])


def _est(**kw):
    kw.setdefault("n_alto_plan", 2)
    return pr.estimar(pr.normalizar_params(dict(n_simple=5, n_medio=3, n_alto=2, **kw)))


def test_estimacion_alto_total():
    e = _est(alto_modo="total")
    assert e["horas"] == {"Simple": 10.0, "Medio": 6.0, "Alto": 80.0}
    assert e["horas_total"] == 96.0 and e["semanas_persona"] == 2.4 and e["semanas_calendario"] == 2.4
    assert e["horas_manual_total"] == 5 * 10 + 3 * 10 + 114
    assert e["ahorro_horas"] == 194 - 96


def test_estimacion_alto_por_grafo_y_equipo():
    e = _est(alto_modo="por_grafo", equipo=2)
    assert e["horas"]["Alto"] == 160.0 and e["horas_total"] == 176.0
    assert e["semanas_persona"] == 4.4 and e["semanas_calendario"] == 2.2
    assert e["horas_manual"]["Alto"] == 228.0


def test_estimacion_sin_alto_y_validacion():
    e = pr.estimar(pr.normalizar_params({"n_simple": 1, "n_medio": 0, "n_alto": 0}))
    assert e["horas_total"] == 2.0  # modo total sin grafos Alto no suma las 80 h
    for malo in ({"equipo": 0}, {"horas_semana": 0}, {"auto_alto": 120}, {"alto_modo": "x"}, {"horas_simple": "a"},
                 {"horas_simple": -1}):
        with pytest.raises(pr.PresentacionError):
            pr.normalizar_params(malo)


def test_alto_con_y_sin_plan():
    e = _est(alto_modo="por_grafo", n_alto_plan=1)
    assert (e["alto_plan"], e["alto_sin_plan"]) == (1, 1)
    assert e["horas_alto_plan"] == 80.0 and e["horas_alto_sin_plan"] == 40.0 and e["horas"]["Alto"] == 120.0
    e = _est(alto_modo="por_grafo", n_alto_plan=1, alto_sin_plan_horas=10)
    assert e["horas"]["Alto"] == 90.0
    with pytest.raises(pr.PresentacionError):
        pr.normalizar_params({"n_alto": 1, "n_alto_plan": 2})
    reales = {"niveles": {"Alto": 18}, "alto_con_plan": 16, "alto_sin_dato": 0}
    assert pr.normalizar_params({"n_alto": 5}, reales)["n_alto_plan"] == 5
    assert pr.normalizar_params({}, reales)["n_alto_plan"] == 16


def test_alto_plan_pset_desde_abinitio(tmp_path, monkeypatch):
    n = _proyecto(tmp_path, monkeypatch)
    ab = tmp_path / "abinitio" / n
    (ab / "1_b.mp").write_text("NODE Input_File_a : SOURCE\nNODE Join_x : JOIN\nNODE Output_File_b : SINK\n"
                               "Input_File_a -> Join_x\nJoin_x -> Output_File_b\n", encoding="utf-8")
    (ab / "b.pset").write_text("!prototype|x|||$AI_MP/b.mp\n", encoding="utf-8")
    p = pr._proyecto(n)
    assert dict((g, c) for g, _n, c in p["_graficos"]) == {"a.mp": False, "b.mp": True}
    os.remove(str(ab / "a.mp"))  # sin .mp no se puede clasificar: sin dato
    p = pr._proyecto(n)
    assert dict((g, c) for g, _n, c in p["_graficos"])["a.mp"] is None


def test_parametros_por_defecto_son_los_reales():
    p = pr.normalizar_params({}, {"niveles": {"Simple": 4, "Medio": 2, "Alto": 1}})
    assert (p["n_simple"], p["n_medio"], p["n_alto"]) == (4, 2, 1)


_LOG = """[tool] 37 fuente(s) de x
[tool] con PySpark: /t/a.zip (429 MB) faltan=[]
[tool] sin PySpark: /t/b.zip (126 MB)
[tool] Compatibilidad de librerias del banco (analisis estatico, sin ejecutar):
[tool]   OK          mex-libcolumns2vector        2.2.0   
[tool]   PARCHEABLE  mex-libextract               2.2.0   
[tool]       - [PARCHEABLE] X: algo
[tool]   Total: 1 OK, 1 PARCHEABLE, 0 BLOQUEADO.
    p/bin/jobs/rps/pivot/job.py -> rps_pivot ok=True
    p/bin/jobs/rps/score/job.py -> rps_score ok=True
    p/bin/jobs/ccp/pivot/job.py -> ccp_pivot ok=True
"""


def _mlops_cache(tmp_path, monkeypatch, con_datos=True):
    monkeypatch.setenv("BNX_PRESENTACION_DIR", str(tmp_path / "salida"))
    monkeypatch.setenv("BNX_SIMULAR_DIR", str(tmp_path / "sim"))
    if con_datos:
        (tmp_path / "salida").mkdir()
        d = pr.parsear_log_paquete(_LOG)
        d["generado"] = "2025-01-01 10:00"
        (tmp_path / "salida" / "mlops_datos.json").write_text(json.dumps(d), encoding="utf-8")


def test_parsear_log_paquete():
    d = pr.parsear_log_paquete(_LOG)
    assert d["jobs"] == 3 and d["jobs_rps"] == 2 and d["mb_con"] == 429 and d["mb_sin"] == 126
    assert d["resumen"] == {"OK": 1, "PARCHEABLE": 1, "BLOQUEADO": 0}
    assert [x["estado"] for x in d["librerias"]] == ["OK", "PARCHEABLE"]


def _verificar(lam, tmp_path, tipo):
    assert len(lam) <= 2
    txt = pr.texto_plano(lam).lower()
    if tipo == "grafos":
        for malo in ("mlops", "vendor", "modelo", "yarn"):
            assert malo not in txt
    else:
        for malo in ("grafo", "ab initio", "pset"):
            assert malo not in txt
    for sensible in ("/data", "@", "fid"):
        assert sensible not in txt
    pytest.importorskip("pptx")
    from pptx import Presentation
    assert len(Presentation(io.BytesIO(pr.generar_pptx(lam))).slides) == len(lam)
    pytest.importorskip("reportlab")
    pdf = pr.generar_pdf(lam)
    assert pdf.startswith(b"%PDF")
    assert pdf.count(b"/Type /Page\n") + pdf.count(b"/Type /Page ") == len(lam)


def test_grafos_dos_laminas_y_modo(tmp_path, monkeypatch):
    n = _proyecto(tmp_path, monkeypatch)
    for modo, frase in (("por_grafo", "por cada grafo complejo"), ("total", "en total para todos")):
        *_x, lam = pr.preparar({"tipo": "grafos", "proyectos": [n], "fecha_corte": "2025-01-31",
                                "params": {"alto_modo": modo}})
        txt = pr.texto_plano(lam)
        assert "2025-01-31" in txt and "Ya contamos con un Orquestador" in txt and "1 orquestaciones" in txt
        _verificar(lam, tmp_path, "grafos")
    assert pr.PARAMS_BASE["alto_modo"] == "por_grafo"


def test_mlops_con_y_sin_datos(tmp_path, monkeypatch):
    _mlops_cache(tmp_path, monkeypatch)
    *_x, lam = pr.preparar({"tipo": "mlops", "fecha_corte": "2025-01-31"})
    txt = pr.texto_plano(lam)
    assert "429 / 126 MB" in txt and "mex-libextract" in txt and "sin dato" in txt  # sin simulacion: sin dato
    _verificar(lam, tmp_path, "mlops")
    _mlops_cache(tmp_path, monkeypatch, con_datos=False)
    *_x, lam = pr.preparar({"tipo": "mlops"})
    assert "sin dato" in pr.texto_plano(lam)
    assert len(lam) == 2


def test_mlops_lee_simulacion(tmp_path, monkeypatch):
    _mlops_cache(tmp_path, monkeypatch)
    d = tmp_path / "sim" / "h" / "pkg" / "demo_out"
    d.mkdir(parents=True)
    (d / "REPORTE_DEMO.json").write_text(json.dumps({"jobs": [
        {"job": "a", "escrituras": [{"filas": 5}]}, {"job": "b", "escrituras": []}]}), encoding="utf-8")
    assert pr.recolectar_mlops()["simulacion"]["con_salida"] == 1
    *_x, lam = pr.preparar({"tipo": "mlops"})
    assert "1 de 2" in pr.texto_plano(lam)


def test_handle_descargar_y_errores(tmp_path, monkeypatch):
    n = _proyecto(tmp_path, monkeypatch)
    monkeypatch.setenv("BNX_PRESENTACION_DIR", str(tmp_path / "salida"))
    st, r = pr.handle("proyectos", {})
    assert st == 200 and r["proyectos"][0]["nombre"] == n
    assert pr.handle("vista", {"proyectos": [n], "fecha_corte": "mal"})[0] == 400
    assert pr.handle("vista", {"tipo": "otro"})[0] == 400
    assert pr.handle("descargar", {"proyectos": [n], "fmt": "doc"})[0] == 400
    assert pr.handle("actualizar_mlops", {"fuente": "../x"})[0] == 400
    pytest.importorskip("pptx")
    st, r = pr.handle("descargar", {"proyectos": [n], "fmt": "pptx"})
    assert st == 200 and r["binario"][1].startswith("migracion_grafos_pyspark") and r["binario"][1].endswith(".pptx")
    assert os.listdir(str(tmp_path / "salida"))


def test_falta_libreria(monkeypatch):
    import builtins
    real = builtins.__import__

    def falso(name, *a, **k):
        if name.startswith("pptx"):
            raise ImportError(name)
        return real(name, *a, **k)
    monkeypatch.setattr(builtins, "__import__", falso)
    with pytest.raises(pr.PresentacionError) as e:
        pr.generar_pptx([])
    assert "pip install python-pptx" in str(e.value)
