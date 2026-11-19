"""Simulacion en Linux RHEL 8 x86_64 con Podman (src/mlops_simular.py): construccion de comandos, disponibilidad,
cancelar -> podman kill, seleccion de imagen y de settings. Sin red y SIN podman (subprocess mockeado)."""
import json
import os
import pytest
from src import mlops_simular as sim
@pytest.fixture
def podman(monkeypatch):
    """Falso `podman`: registra las llamadas y responde segun un dict {prefijo de args: (rc, salida)}."""
    llamadas, resp = [], {}
    monkeypatch.setattr(sim, "podman_bin", lambda: "/usr/local/bin/podman")
    def falso(args, timeout=60, conexion=True):
        llamadas.append((list(args), conexion))
        for k, v in resp.items():
            if list(args)[:len(k)] == list(k):
                return v
        return 0, ""
    monkeypatch.setattr(sim, "_podman", falso)
    return llamadas, resp
# --- construccion del comando ---------------------------------------------------------------------
def test_comando_run_amd64_sin_red_usuario_y_volumenes(monkeypatch):
    monkeypatch.setattr(sim, "podman_bin", lambda: "/usr/local/bin/podman")
    c = sim.comando_podman_run("bnx-sim-x", "bnx-rhel8", "/Users/yo/cache/abc", "bash setup.sh",
                               env={"B": "2", "A": "1"})
    assert c[0] == "/usr/local/bin/podman" and c[1:3] == ["--connection", "bnx-linux"]
    assert c[c.index("--platform") + 1] == "linux/amd64"
    assert c[c.index("--network") + 1] == "none"                   # setup offline: prueba que vendor/ esta completo
    assert c[c.index("--user") + 1] == "bnx"                       # no root
    assert "--rm" in c and c[c.index("--name") + 1] == "bnx-sim-x"
    assert "/Users/yo/cache/abc:/work" in c                        # el paquete se MONTA (no va en la imagen)
    assert c[c.index("-w") + 1] == "/work/framework_mlops_v2_pkg"
    assert any(x.startswith("/work/framework_mlops_v2_pkg/.bnx_tmp:rw,exec") for x in c)   # tmpfs de Spark
    assert c[-4:] == ["bnx-rhel8", "bash", "-c", "bash setup.sh"]
    assert c[c.index("-e") + 1] == "A=1"                           # env ordenado


def test_comando_run_con_red_solo_si_se_pide(monkeypatch):
    monkeypatch.setattr(sim, "podman_bin", lambda: "podman")
    assert "--network" not in sim.comando_podman_run("n", "img", "/Users/x", "true", red=True)
def test_montajes_extra_son_solo_lectura(monkeypatch):
    monkeypatch.setattr(sim, "podman_bin", lambda: "podman")
    c = sim.comando_podman_run("n", "img", "/Users/x", "true", montajes=[("/Users/yo/settings", "/bnx_settings", "ro")])
    assert "/Users/yo/settings:/bnx_settings:ro" in c
def test_script_del_job_es_run_sh_demo_con_pivote_primero_por_orden_del_runner():
    assert sim._linux_script_job("rps_pivot", None) == "bash run.sh --demo --source rps_pivot"
    assert sim._linux_script_job(None, "/bnx_settings") == "bash run.sh --demo --continuar-si-falla --settings /bnx_settings"
    assert sim._linux_script_job("a b; rm -rf /", None).endswith("'a b; rm -rf /'")      # escapado
def test_encabezado_detectado_en_el_contenedor():
    salida = ("Red Hat Enterprise Linux release 8.10 (Ootpa)\nx86_64\nPython 3.11.13\nldd (GNU libc) 2.28\n"
              'openjdk version "17.0.21.1" 2026-11-17 LTS\nbnx\n')
    assert sim.encabezado_linux(salida) == "Linux RHEL 8 x86_64 · Python 3.11.13 · glibc 2.28 · Java 17"
def test_imagen_segun_modo_de_pyspark(tmp_path):
    pkg = tmp_path / "pkg"
    (pkg / "vendor").mkdir(parents=True)
    assert sim.imagen_para(str(pkg)) == "bnx-rhel8"
    (pkg / "vendor" / "PYSPARK_MODE").write_text("incluido\n")
    assert sim.imagen_para(str(pkg)) == "bnx-rhel8"
    (pkg / "vendor" / "PYSPARK_MODE").write_text("servidor\n")
    assert sim.imagen_para(str(pkg)) == "bnx-rhel8-spark"
def test_settings_dentro_del_paquete_y_externos(tmp_path):
    raiz = tmp_path / "h"
    pkg = raiz / "framework_mlops_v2_pkg"
    (pkg / "bank_src" / "settings").mkdir(parents=True)
    ext = tmp_path / "ext"
    ext.mkdir()
    assert sim.settings_contenedor(str(pkg), str(pkg / "bank_src" / "settings")) == \
        ("/work/framework_mlops_v2_pkg/bank_src/settings", None)
    ruta, mont = sim.settings_contenedor(str(pkg), str(ext))
    assert ruta == "/bnx_settings" and mont == (os.path.realpath(str(ext)), "/bnx_settings", "ro")
def test_preparacion_usa_4cpu_6gb_30gb_y_amd64(monkeypatch):
    monkeypatch.setattr(sim, "podman_bin", lambda: "podman")
    c = sim.comandos_preparacion("/repo/tools/linux")
    assert c["init"][:4] == ["podman", "machine", "init", "bnx-linux"]
    assert c["init"][c["init"].index("--cpus") + 1] == "4" and c["init"][c["init"].index("--memory") + 1] == "6144"
    assert c["init"][c["init"].index("--disk-size") + 1] == "30"
    for k in ("build", "build_spark"):
        assert c[k][c[k].index("--platform") + 1] == "linux/amd64"
    assert "PYSPARK=3.5.6" in c["build_spark"] and c["build_spark"][-1] == "/repo/tools/linux"
# --- disponibilidad --------------------------------------------------------------------------------
def test_sin_podman_linux_no_esta_habilitado(monkeypatch):
    monkeypatch.setattr(sim, "podman_bin", lambda: None)
    d = sim.linux_info()
    assert d["podman"] is False and d["habilitado"] is False and "Podman" in d["razon"]
    with pytest.raises(sim.SimError) as e:
        sim.preparar_linux()
    assert "Podman" in str(e.value)
def test_sin_maquina_pide_preparar(podman):
    _, resp = podman
    resp[("machine", "list")] = (0, "[]")
    d = sim.linux_info()
    assert d["maquina_existe"] is False and d["habilitado"] is False and "preparar" in d["razon"].lower()
def test_maquina_detenida_se_habilita_y_arranca_sola(podman):
    _, resp = podman
    resp[("machine", "list")] = (0, json.dumps([{"Name": "bnx-linux*", "Running": False}]))
    d = sim.linux_info()
    assert d["maquina_existe"] and not d["maquina_activa"] and d["habilitado"] is True
def test_activa_requiere_las_dos_imagenes(podman):
    llamadas, resp = podman
    resp[("machine", "list")] = (0, json.dumps([{"Name": "bnx-linux", "Running": True}]))
    resp[("image", "exists", "localhost/bnx-rhel8-spark")] = (1, "")
    d = sim.linux_info()
    assert d["imagenes"] == {"bnx-rhel8": True, "bnx-rhel8-spark": False} and d["habilitado"] is False
    assert "bnx-rhel8-spark" in d["razon"]
    del resp[("image", "exists", "localhost/bnx-rhel8-spark")]
    assert sim.linux_info()["habilitado"] is True
def test_iniciar_en_linux_se_rechaza_si_no_esta_listo(podman, tmp_path):
    _, resp = podman
    resp[("machine", "list")] = (0, "[]")
    with pytest.raises(sim.SimError) as e:
        sim.iniciar("t", str(tmp_path / "x.zip"), None, None, None, "linux")
    assert "Linux no está listo" in str(e.value)
# --- cancelar -> podman kill ------------------------------------------------------------------------
class _Proc(object):
    pid = 99999
    def poll(self):
        return None
def test_cancelar_mata_el_contenedor_con_podman_kill_y_rm(podman, monkeypatch):
    llamadas, _ = podman
    muertos = []
    monkeypatch.setattr(sim, "matar_arbol", lambda p: muertos.append(p))
    r = sim.Run("t", "h" * 16, "/x/pkg", None, 60, "linux")
    r.estado = "corriendo"
    r.contenedor = "bnx-sim-abc-1"
    r.proc = _Proc()
    sim._RUNS[r.id] = r
    try:
        out = sim.cancelar(r.id)
    finally:
        sim._RUNS.pop(r.id, None)
    assert out["estado"] == "cancelando" and r.cancelar_flag
    assert (["kill", "bnx-sim-abc-1"], True) in llamadas
    assert (["rm", "-f", "--ignore", "bnx-sim-abc-1"], True) in llamadas
    assert llamadas.index((["kill", "bnx-sim-abc-1"], True)) < llamadas.index((["rm", "-f", "--ignore", "bnx-sim-abc-1"], True))
    assert len(muertos) == 1                                   # y tambien el cliente podman
def test_cancelar_en_mac_no_toca_podman(podman, monkeypatch):
    llamadas, _ = podman
    monkeypatch.setattr(sim, "matar_arbol", lambda p: None)
    r = sim.Run("t", "h" * 16, "/x/pkg", None, 60, "mac")
    r.estado = "corriendo"
    r.proc = _Proc()
    sim._RUNS[r.id] = r
    try:
        sim.cancelar(r.id)
    finally:
        sim._RUNS.pop(r.id, None)
    assert llamadas == []
def test_stream_limpia_el_contenedor_al_terminar(podman, monkeypatch, tmp_path):
    llamadas, _ = podman
    r = sim.Run("t", "h" * 16, str(tmp_path), None, 60, "linux")
    r.contenedor = "bnx-sim-fin"
    rc = sim._stream(r, [os.sys.executable, "-c", "print('hola')"], str(tmp_path), dict(os.environ), 30)
    assert rc == 0 and "hola" in r.log and r.contenedor is None
    assert (["rm", "-f", "--ignore", "bnx-sim-fin"], True) in llamadas
def test_timeout_mata_el_contenedor(podman, tmp_path):
    llamadas, _ = podman
    r = sim.Run("t", "h" * 16, str(tmp_path), None, 1, "linux")
    r.contenedor = "bnx-sim-lento"
    rc = sim._stream(r, [os.sys.executable, "-c", "import time; time.sleep(30)"], str(tmp_path), dict(os.environ), 1)
    assert rc == -9 and "timeout" in r.log
    assert (["kill", "bnx-sim-lento"], True) in llamadas
# --- estado/UI: el selector se habilita segun linux_info ----------------------------------------------
def test_info_expone_linux_para_el_selector(podman, tmp_path, monkeypatch):
    import zipfile
    _, resp = podman
    resp[("machine", "list")] = (0, "[]")
    monkeypatch.setenv("BNX_SIMULAR_DIR", str(tmp_path / "s"))
    monkeypatch.setattr(sim, "entorno_soportado", lambda: (True, "java"))
    z = tmp_path / "p.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("framework_mlops_v2_pkg/framework_mlops_v2/aggregates/router.py", "_FUENTES = {}\n")
        zf.writestr("framework_mlops_v2_pkg/bank_src/settings/spark.json", "{}")
    d = sim.info(str(z))
    assert d["linux"]["habilitado"] is False and d["linux"]["gb"] == sim.LINUX_GB
    assert d["settings"] is True and d["settings_detectado"].endswith("bank_src/settings")
    assert d["donde"] == "mac"
# --- settings elegidos por el usuario ------------------------------------------------------------------
def test_validar_settings(tmp_path):
    with pytest.raises(sim.SimError):
        sim.validar_settings(str(tmp_path / "no_existe"))
    with pytest.raises(sim.SimError) as e:
        sim.validar_settings(str(tmp_path))
    assert "spark.json" in str(e.value)
    (tmp_path / "spark.json").write_text("{}")
    assert sim.validar_settings(str(tmp_path)) == os.path.realpath(str(tmp_path))
def test_settings_del_paquete_exige_spark_json(tmp_path):
    pkg = tmp_path / "pkg"
    (pkg / "bank_src" / "settings").mkdir(parents=True)
    assert sim.settings_del_paquete(str(pkg)) is None
    (pkg / "bank_src" / "settings" / "spark.json").write_text("{}")
    assert sim.settings_del_paquete(str(pkg)).endswith(os.path.join("bank_src", "settings"))
# --- modo cluster con spark3-submit falso ---------------------------------------------------------------
def test_cluster_falso_monta_solo_lectura_y_arma_el_comando(monkeypatch):
    monkeypatch.setattr(sim, "podman_bin", lambda: "podman")
    c = sim.comando_cluster_fake("n", "bnx-rhel8", "/Users/x/h")
    j = " ".join(c)
    assert "/opt/fake/bin:ro" in j and "/etc/spark3/conf:ro" in j and "/bnx_settings:ro" in j
    script = c[-1]
    assert "BNX_SPARK=cluster" in script and "--settings /bnx_settings --env uat" in script
    assert os.path.isfile(os.path.join(sim._dir_fake(), "bin", "spark3-submit"))
    assert os.access(os.path.join(sim._dir_fake(), "bin", "spark3-submit"), os.X_OK)
    sj = json.load(open(os.path.join(sim._dir_fake(), "settings", "spark.json")))
    assert sj["spark_queue_uat"] == "root.cola_uat_prueba" and sj["default"]["spark.executor.instances"] == "7"
def test_evaluar_cluster_reconoce_la_salida_esperada():
    ok = "\n".join([
        "[run.sh]   el cluster fija: spark.pyspark.python /opt/x", "[run.sh] tmp de la JVM: /work/x",
        "FAKE-SPARK3-SUBMIT: argv (20):", "  ARG: spark.pyspark.driver.python=/work/framework_mlops_v2_pkg/.venv/bin/python",
        "  ARG: spark.yarn.queue=root.cola_uat_prueba", "  ARG: spark.executor.instances=7", "  ARG: spark.executor.memory=6g",
        "  ARG: spark.sql.shuffle.partitions=123", "FAKE-SPARK3-SUBMIT: SPARK_CONF_DIR=/etc/spark3/conf",
        "FAKE-SPARK3-SUBMIT: PYSPARK_PYTHON=(sin definir)"])
    assert all(o for _d, o in sim.evaluar_cluster(ok))
    malo = sim.evaluar_cluster(ok.replace("root.cola_uat_prueba", "root.otra"))
    assert [d for d, o in malo if not o] == ["cola YARN del spark.json (spark_queue_uat con --env uat)"]
def test_python38_compatible():
    import ast
    ast.parse(open(sim.__file__, encoding="utf-8").read(), feature_version=(3, 8))
