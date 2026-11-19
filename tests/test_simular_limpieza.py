"""Limpieza de simulaciones viejas (src/mlops_simular.py): conserva las N mas recientes
(BNX_SIMULAR_MAX, default 2), nunca borra la que corre, solo toca carpetas de hash."""
import os
import time

import pytest

from src import mlops_simular as sim


def _carpeta(base, h, edad_seg, tam=1000):
    raiz = base / h
    (raiz / "framework_mlops_v2_pkg").mkdir(parents=True)
    (raiz / "framework_mlops_v2_pkg" / "dato.bin").write_bytes(b"x" * tam)
    marca = raiz / ".montado"
    marca.write_text(h)
    t = time.time() - edad_seg
    os.utime(marca, (t, t))
    return raiz


@pytest.fixture
def base(tmp_path, monkeypatch):
    b = tmp_path / "_simular"
    b.mkdir()
    monkeypatch.setenv("BNX_SIMULAR_DIR", str(b))
    monkeypatch.delenv("BNX_SIMULAR_MAX", raising=False)
    return b


def test_conserva_las_dos_mas_recientes_por_defecto(base):
    for i, h in enumerate(["a" * 16, "b" * 16, "c" * 16, "d" * 16]):
        _carpeta(base, h, edad_seg=(i + 1) * 100)          # a es la mas reciente
    r = sim.limpiar_simulaciones()
    assert sorted(r["conservadas"]) == ["a" * 16, "b" * 16]
    assert sorted(r["borradas"]) == ["c" * 16, "d" * 16]
    assert r["liberado"] >= 2000
    assert sorted(os.listdir(base)) == ["a" * 16, "b" * 16]


def test_bnx_simular_max_configurable(base, monkeypatch):
    for i, h in enumerate(["a" * 16, "b" * 16, "c" * 16]):
        _carpeta(base, h, edad_seg=(i + 1) * 100)
    monkeypatch.setenv("BNX_SIMULAR_MAX", "1")
    assert sim.max_simulaciones() == 1
    sim.limpiar_simulaciones()
    assert os.listdir(base) == ["a" * 16]
    monkeypatch.setenv("BNX_SIMULAR_MAX", "basura")
    assert sim.max_simulaciones() == 2


def test_nunca_borra_la_que_esta_corriendo(base):
    for i, h in enumerate(["a" * 16, "b" * 16, "c" * 16]):
        _carpeta(base, h, edad_seg=(i + 1) * 100)
    sim._ACTIVO["c" * 16] = "run-x"            # la mas vieja esta corriendo
    try:
        r = sim.limpiar_simulaciones(conservar=0)
    finally:
        sim._ACTIVO.pop("c" * 16, None)
    assert r["conservadas"] == ["c" * 16]
    assert sorted(os.listdir(base)) == ["c" * 16]


def test_proteger_la_que_se_esta_montando(base):
    for i, h in enumerate(["a" * 16, "b" * 16, "c" * 16]):
        _carpeta(base, h, edad_seg=(i + 1) * 100)
    sim.limpiar_simulaciones(conservar=1, proteger=("c" * 16,))
    assert sorted(os.listdir(base)) == ["a" * 16, "c" * 16]


def test_solo_toca_carpetas_de_hash(base):
    _carpeta(base, "a" * 16, 10)
    (base / "mis_notas").mkdir()
    (base / "mis_notas" / "x.txt").write_text("no borrar")
    (base / "suelto.txt").write_text("no borrar")
    sim.limpiar_simulaciones(conservar=0)
    assert sorted(os.listdir(base)) == ["mis_notas", "suelto.txt"]


def test_espacio_informa_tamano_total_y_carpetas(base):
    _carpeta(base, "a" * 16, 10, tam=5000)
    _carpeta(base, "b" * 16, 20, tam=3000)
    e = sim.espacio_simulaciones()
    assert e["ok"] and e["max"] == 2
    assert e["total"] >= 8000 and [c["hash"] for c in e["carpetas"]] == ["a" * 16, "b" * 16]
    assert not any(c["activo"] for c in e["carpetas"])


def test_iniciar_limpia_automaticamente_y_protege_la_nueva(base, monkeypatch, tmp_path):
    for i, h in enumerate(["a" * 16, "b" * 16, "c" * 16]):
        _carpeta(base, h, edad_seg=(i + 1) * 100)
    nueva = "f" * 16
    monkeypatch.setattr(sim, "entorno_soportado", lambda: (True, "ok"))
    monkeypatch.setattr(sim, "montar", lambda z, b=None: (nueva, str(_carpeta(base, nueva, 0))))
    monkeypatch.setattr(sim, "listar_jobs", lambda pkg: [])        # corta tras limpiar (sin jobs)
    with pytest.raises(sim.SimError):
        sim.iniciar("tok", "x.zip")
    # quedan la nueva y la mas reciente de las viejas (2 en total)
    assert sorted(os.listdir(base)) == sorted([nueva, "a" * 16])


def test_endpoints_espacio_y_limpiar_solo_localhost(base):
    from tests.test_mlops_simular import _handler
    _carpeta(base, "a" * 16, 10)
    h, _ = _handler("10.1.2.3", None, "GET", ruta="/mlops/simular/espacio")
    h._handle_mlops_simular("/mlops/simular/espacio")
    assert h.respuestas[0][0] == 403
    h, _ = _handler("127.0.0.1", "http://localhost:5173", "GET", ruta="/mlops/simular/espacio")
    h._handle_mlops_simular("/mlops/simular/espacio")
    assert h.respuestas[0][0] == 200 and h.respuestas[0][1]["total"] > 0
    h, _ = _handler("127.0.0.1", "http://localhost:5173", "POST", cuerpo=b"{}", ruta="/mlops/simular/limpiar")
    h._handle_mlops_simular("/mlops/simular/limpiar")
    assert h.respuestas[0][0] == 200 and h.respuestas[0][1]["borradas"] == ["a" * 16]
    assert os.listdir(base) == []
