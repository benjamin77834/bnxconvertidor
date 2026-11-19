"""Monitoreo de recursos (src/mlops_demo/monitor.py): parsers de /proc y ps, % normalizado, eficiencia, tabla de
tiempos con columnas de CPU y lectura incremental de muestras (la usa la simulacion). Sin red ni procesos pesados."""
import json
import os
import sys
import time
import pytest
from src import bnx_sparkconf as bs
from src import mlops_simular as sim
from src.mlops_demo import monitor as M
STAT = "4242 (python3 (x) y) S 4000 4242 4000 0 -1 4194304 100 0 0 0 150 50 0 0 20 0 5 0 100 1000000 2500 18446744073709551615"
def test_parse_proc_stat_con_parentesis_en_el_nombre():
    ppid, cpu, rss = M.parse_proc_stat(STAT, clk_tck=100.0, page_kb=4.0)
    assert ppid == 4000 and cpu == pytest.approx(2.0) and rss == 2500 * 4.0     # (150+50)/100 s
    assert M.parse_proc_stat("basura") is None and M.parse_proc_stat("") is None
def test_parse_cputime_de_ps():
    assert M.parse_cputime("0:01.50") == pytest.approx(1.5)
    assert M.parse_cputime("01:02:03.25") == pytest.approx(3723.25)
    assert M.parse_cputime("2-00:00:10") == pytest.approx(172810)
    assert M.parse_cputime("") == 0.0 and M.parse_cputime("x:y") == 0.0
def test_parse_ps_y_arbol_de_hijos():
    t = M.parse_ps("  1     0   0:10.00  1000\n 10     1   0:02.00  2000\n 11    10   0:03.00  3000\n 12    10   0:01.00  500\n 99     1   0:09.00  9000\nbasura\n")
    assert t[11] == (10, 3.0, 3000)
    assert sorted(M.descendientes(t, 10)) == [10, 11, 12]               # raiz + hijos (JVM, workers); no 99
    assert M.descendientes(t, 12345) == []
def test_parse_proc_stat_global_y_meminfo():
    ocupado, total = M.parse_cpu_total("cpu  100 0 50 800 50 0 0 0 0 0\ncpu0 1 1 1 1\n")
    assert (ocupado, total) == (150, 1000)
    usada, tot = M.parse_meminfo("MemTotal: 8192000 kB\nMemFree: 1000 kB\nMemAvailable: 2048000 kB\n")
    assert tot == pytest.approx(8000.0) and usada == pytest.approx(6000.0)
def test_parse_vm_stat_macos():
    vm = "Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free:  1000.\nPages inactive:  1000.\nPages speculative:  0.\n"
    usada, total = M.parse_vm_stat(vm, 16384 * 10000)
    assert total == pytest.approx(16384 * 10000 / 1048576.0)
    assert usada == pytest.approx(16384 * 8000 / 1048576.0)
def test_porcentajes_y_eficiencia():
    assert M.cpu_pct(2.0, 1.0) == 200.0 and M.cpu_pct(1.0, 0) == 0.0          # 100% = un nucleo, puede pasar de 100
    assert M.pct_del_total(200.0, 4) == 50.0 and M.pct_del_total(900.0, 4) == 100.0
    assert M.eficiencia(cpu_seg=8.0, wall_seg=4.0, nucleos=4) == pytest.approx(0.5)
    assert M.eficiencia(1, 0, 4) == 0.0 and M.eficiencia(1, 1, 0) == 0.0
def test_stats_de_un_job():
    ms = [{"t": 10 + i, "dt": 1.0, "cpu": c, "rss": r} for i, (c, r) in enumerate([(100, 500), (300, 800), (200, 700)])]
    s = M.stats_de_muestras(ms, 10, 13, nucleos=4)
    assert s["cpu_prom"] == pytest.approx(200) and s["cpu_pico"] == 300 and s["nuc_prom"] == pytest.approx(2.0)
    assert s["mem_pico"] == 800 and s["cpu_seg"] == pytest.approx(6.0) and s["eficiencia"] == pytest.approx(0.5)
    assert M.stats_de_muestras([], 0, 5, 4)["muestras"] == 0
# --- tabla de tiempos con columnas nuevas ---------------------------------------------------------------
def test_tabla_con_columnas_de_cpu_y_linea_final():
    filas = [{"etapa": "kernel", "nombre": "rps_pivot", "seg": 12.3, "estado": "OK", "cpu_prom": 180.0, "cpu_pico": 390.0,
              "nuc_prom": 1.8, "mem_pico": 1534.0, "tareas": 42, "eficiencia": 0.45},
             {"etapa": "kernel", "nombre": "otro", "seg": 1.0, "estado": "ERROR"}]
    t = bs.tabla_tiempos(filas, "local[4]", "app-1", "CPU: promedio 45% de 4 nucleos (efectivos 1.8)")
    cab = t.splitlines()[1]
    for col in ("segundos", "CPU %prom", "CPU %pico", "nuc.prom", "mem MB", "tareas", "efic."):
        assert col in cab
    assert "180" in t and "390" in t and "1.80" in t and "1534" in t and " 42 " in t and "0.45" in t
    assert t.splitlines()[-1].startswith("CPU: promedio 45%")
def test_tabla_sin_monitor_queda_como_antes():
    t = bs.tabla_tiempos([{"etapa": "kernel", "nombre": "a", "seg": 1.0, "estado": "OK"}], "local[1]", "x")
    assert "CPU %prom" not in t and "etapa" in t and "TOTAL" in t
# --- monitor real, corto ----------------------------------------------------------------------------------
def test_mide_un_job_que_quema_cpu(tmp_path, monkeypatch):
    monkeypatch.setenv("BNX_MONITOR_INTERVALO", "0.25")
    arch = str(tmp_path / "m.jsonl")
    m = M.Monitor(nucleos=4, archivo=arch)
    if m.lector is None:
        pytest.skip("sin lector de procesos en este SO")
    m.iniciar()
    try:
        m.job_inicio("quema")
        t = time.time()
        while time.time() - t < 1.5:
            sum(range(20000))
        s = m.job_fin("quema")
    finally:
        m.detener()
    assert 40 < s["cpu_prom"] < 150 and s["muestras"] >= 3                    # ~1 nucleo ocupado
    assert 0 < s["eficiencia"] < 0.5 and s["mem_pico"] > 5
    evs, off = M.leer_incremental(arch, 0)
    assert any(e.get("ev") == "inicio" for e in evs) and any(e.get("ev") == "fin" and e["job"] == "quema" for e in evs)
    assert off == os.path.getsize(arch)
    assert "CPU: promedio" in m.linea_resumen() and "quema" in m.linea_resumen()
def test_se_apaga_con_bnx_monitor_0(monkeypatch):
    monkeypatch.setenv("BNX_MONITOR", "0")
    M.reset()
    assert M.obtener() is None
    M.reset()
def test_sin_lector_avisa_y_no_falla(monkeypatch):
    monkeypatch.setattr(M, "elegir_lector", lambda: None)
    m = M.Monitor(nucleos=2)
    assert m.lector is None and "psutil" in m.aviso
    m.job_inicio("x")
    assert m.job_fin("x") is None and m.linea_resumen() == ""
# --- lectura incremental (endpoint de estado) -----------------------------------------------------------------
def test_lectura_incremental_ignora_la_linea_incompleta(tmp_path):
    f = tmp_path / "m.jsonl"
    f.write_text(json.dumps({"t": 1, "cpu": 10}) + "\n" + json.dumps({"t": 2, "cpu": 20}) + "\n" + '{"t": 3, "cp')
    a, off = M.leer_incremental(str(f), 0)
    assert [x["t"] for x in a] == [1, 2]
    with open(f, "a") as fh:
        fh.write('u": 30}\n')
    b, off2 = M.leer_incremental(str(f), off)
    assert [x["t"] for x in b] == [3] and off2 == os.path.getsize(f)
    assert M.leer_incremental(str(f), off2) == ([], off2)
    assert M.leer_incremental(str(tmp_path / "no_existe"), 0) == ([], 0)
def test_estado_del_run_entrega_muestras_incrementales_y_recursos(tmp_path):
    r = sim.Run("t", "h" * 16, str(tmp_path), None, 60, "mac")
    ev = {"ev": "fin", "job": "rps_pivot", "stats": {"cpu_prom": 150.0, "cpu_pico": 300.0, "nuc_prom": 1.5,
                                                    "mem_pico": 900.0, "eficiencia": 0.375, "tareas": 7}}
    with open(r.monitor_file, "w") as fh:
        fh.write(json.dumps({"t": 1, "cpu": 100.0, "rss": 500.0, "n": 4}) + "\n")
    d1 = r.a_dict(0, 0)
    assert len(d1["monitor"]) == 1 and d1["monitor_offset"] > 0
    with open(r.monitor_file, "a") as fh:
        fh.write(json.dumps({"t": 2, "cpu": 250.0, "rss": 600.0, "n": 4}) + "\n" + json.dumps(ev) + "\n")
    d2 = r.a_dict(0, d1["monitor_offset"])
    assert [m.get("t") for m in d2["monitor"] if "cpu" in m] == [2]            # solo lo nuevo
    assert d2["recursos"]["rps_pivot"]["cpu_pico"] == 300.0
def test_la_simulacion_pasa_el_archivo_del_monitor(tmp_path, monkeypatch):
    e = sim._env_base(str(tmp_path), "py")
    assert e["BNX_MONITOR_FILE"] == str(tmp_path / ".bnx_monitor.jsonl")
    monkeypatch.setenv("BNX_DEMO_CORES", "6")
    assert sim._env_contenedor()["BNX_DEMO_CORES"] == "6"
    monkeypatch.delenv("BNX_DEMO_CORES")
    assert sim._env_contenedor()["BNX_DEMO_CORES"] == "4"             # VM de 4 CPU
def test_python38():
    import ast
    ast.parse(open(M.__file__, encoding="utf-8").read(), feature_version=(3, 8))
