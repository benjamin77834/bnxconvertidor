"""Edicion de planes generados desde .plan: accion de cada paso (incl. noop/no_traducido), tipo
'sql', restaurar la accion original, params override -> env, .pset editado y que regenerar no
pise las ediciones. Sin red."""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src import orq_sql
from src import orquestador as o


def _paso(sid, nombre, deps=(), **accion):
    a = accion or {"type": "noop", "target": None, "source": None, "status": "no_traducido",
                   "nota": "tarea de programa/script de Ab Initio sin traduccion automatica"}
    return {"id": sid, "name": nombre, "action": a, "depends_on": list(deps), "dep_flags": {},
            "solo_en_fallo": False, "enabled": True, "continue_on_error": False}


def _plan():
    return {"plan": "x.plan", "nombre": "x", "origen": "plan", "direccion": "prior", "enlaces": [],
            "ejecucion": {**o.EJECUCION_DEFECTO, "env": {"SCHEMA": "dev", "DB_PASSWORD": "s3cr3t"}},
            "steps": [_paso("t1", "Log_status_running"), _paso("t2", "Print parameters", ["t1"])]}


def _ent(plan, **cambios):
    e = json.loads(json.dumps(plan))
    for sid, c in cambios.items():
        next(s for s in e["steps"] if s["id"] == sid).update(c)
    return e


SQL = {"type": "sql", "motor": "spark_sql",
       "sentencia": "INSERT INTO ${SCHEMA}.log VALUES ('${DB_PASSWORD}');\nSELECT 1"}


# ---------------------------------------------------------------------------
# tipo sql: validacion
# ---------------------------------------------------------------------------
def test_sql_normaliza_y_calcula_ubicacion():
    a = o.normalizar_accion(SQL)
    assert a["motor"] == "spark_sql" and a["ubicacion"] == "local" and "url" not in a
    j = o.normalizar_accion({"type": "sql", "motor": "jdbc", "sentencia": "CALL p()",
                             "url": "jdbc:oracle:thin:@h:1521/S", "driver": "oracle.jdbc.OracleDriver",
                             "jar": "libs/ojdbc.jar", "usuario": "etl", "password_env": "ORA_PW", "x": 1})
    assert j["ubicacion"] == "remoto" and "x" not in j and j["password_env"] == "ORA_PW"


@pytest.mark.parametrize("malo", [
    {"motor": "mongo"},
    {"sentencia": "  "},
    {"motor": "jdbc"},                                                  # falta url
    {"motor": "jdbc", "url": "mysql://h/db"},                           # no es JDBC
    {"motor": "jdbc", "url": "jdbc:mysql://h/db?password=abc"},         # clave en la url
    {"motor": "jdbc", "url": "jdbc:mysql://h/db", "password_env": "mi clave"},
    {"motor": "jdbc", "url": "jdbc:mysql://h/db", "password_env": "Abc123$xyz!"},
    {"motor": "jdbc", "url": "jdbc:mysql://h/db", "driver": "x; rm -rf /"},
    {"motor": "bteq", "url": "td.host"},                                # requiere password_env
    {"motor": "spark_sql", "hivevar": {"a": "b"}},
])
def test_sql_invalido(malo):
    with pytest.raises(ValueError):
        o.normalizar_accion({"type": "sql", "motor": "spark_sql", "sentencia": "SELECT 1", **malo})


def test_sql_beeline_hivevar_valida():
    a = o.normalizar_accion({"type": "sql", "motor": "beeline", "sentencia": "SELECT 1",
                             "url": "jdbc:hive2://h:10000/default", "hivevar": {"fecha": "${F}"}})
    assert a["hivevar"] == {"fecha": "${F}"}
    with pytest.raises(ValueError):
        o.normalizar_accion({**a, "hivevar": {"a b": "x"}})


# ---------------------------------------------------------------------------
# argv, expansion de ${PARAM}, secretos
# ---------------------------------------------------------------------------
def test_argv_sql_expande_params_y_no_expone_secretos():
    plan = _plan()
    st = {"id": "t1", "action": o.normalizar_accion(SQL)}
    cmd = o.build_command(st, o._ej(plan))
    assert cmd[:3] == [sys.executable, "-m", "src.orq_sql"] and "--motor=spark_sql" in cmd
    sent = next(x for x in cmd if x.startswith("--sentencia="))
    assert "INSERT INTO dev.log" in sent                      # ${SCHEMA} expandido
    assert "s3cr3t" not in " ".join(cmd) and "${DB_PASSWORD}" in sent   # secreto: lo resuelve el runner
    # override del plan y del paso (el del paso gana)
    plan["ejecucion"]["params"] = {"SCHEMA": "qa"}
    assert "INSERT INTO qa.log" in o.build_command(st, o._ej(plan))[4]
    st["params"] = {"SCHEMA": "prod"}
    assert "INSERT INTO prod.log" in o.build_command(st, o._ej(plan))[4]


def test_argv_jdbc_lleva_solo_el_nombre_de_la_variable():
    a = o.normalizar_accion({"type": "sql", "motor": "jdbc", "sentencia": "VALUES NEXT VALUE FOR s",
                             "url": "jdbc:derby:/tmp/x", "usuario": "u", "password_env": "MI_PW",
                             "jar": "a.jar", "driver": "org.apache.derby.jdbc.EmbeddedDriver"})
    cmd = o.build_command({"id": "t", "action": a}, o._ej(_plan()))
    assert "--password-env=MI_PW" in cmd and "--url=jdbc:derby:/tmp/x" in cmd and "--jar=a.jar" in cmd
    cmd_air = o.build_command({"id": "t", "action": a}, o._ej(_plan()), portable=True)
    assert cmd_air[0] == "python3"


def test_dry_run_muestra_sentencia_expandida_con_secretos_enmascarados(capsys):
    plan = _plan()
    plan["steps"][0]["action"] = {**o.normalizar_accion(SQL), "status": "editado"}
    plan["steps"][0]["editado"] = True
    assert o.ejecutar(plan, real=False)
    out = capsys.readouterr().out
    assert "INSERT INTO dev.log VALUES ('****');" in out and "s3cr3t" not in out


def test_shell_expande_params():
    a = o.normalizar_accion({"type": "shell", "comando": "echo ${SCHEMA} ${DB_PASSWORD}"})
    cmd = o.build_command({"id": "t", "action": a}, o._ej(_plan()))
    assert cmd == ["echo", "dev", "${DB_PASSWORD}"]


def test_runner_expandir_dividir_y_mascara(monkeypatch):
    monkeypatch.setenv("DB_PASSWORD", "abc")
    monkeypatch.setenv("TBL", "t")
    assert orq_sql.expandir("select '${DB_PASSWORD}' from ${TBL}") == "select 'abc' from t"
    assert orq_sql.expandir("select '${DB_PASSWORD}' from ${TBL}", mascara=True) == "select '****' from t"
    with pytest.raises(SystemExit, match="NOPE"):
        orq_sql.expandir("${NOPE}")
    assert orq_sql.dividir("a; b -- c;d\n; 'x;y'; /* ; */ ;") == ["a", "b -- c;d", "'x;y'"]


def test_params_override_llegan_como_env():
    plan = _plan()
    plan["ejecucion"]["params"] = {"SCHEMA": "qa", "OTRO": "1"}
    plan["steps"][0]["params"] = {"SCHEMA": "prod", "MALO": "$X"}   # con '$': expresion sin resolver
    env = o._job_env(o._ej(plan), plan["steps"][0])
    assert env["SCHEMA"] == "prod" and env["OTRO"] == "1" and "MALO" not in env
    assert o._job_env(o._ej(plan), plan["steps"][1])["SCHEMA"] == "qa"
    assert o._job_env(o._ej(plan))["SCHEMA"] == "qa"


def test_params_invalidos_rechazados():
    plan = _plan()
    plan["ejecucion"]["params"] = {"1MAL": "x"}
    with pytest.raises(ValueError, match="parametro invalido"):
        o.validar_plan(plan)
    plan["ejecucion"]["params"] = {"A": "uno\ndos"}
    with pytest.raises(ValueError, match="valor invalido"):
        o.validar_plan(plan)
    plan["ejecucion"].pop("params")
    plan["steps"][0]["params"] = {"A": 1}
    o.validar_plan(plan)


# ---------------------------------------------------------------------------
# editar, restaurar y refrescar
# ---------------------------------------------------------------------------
def test_editar_paso_noop_a_sql_y_restaurar():
    plan = _plan()
    ent = _ent(plan, t1={"editado": True, "action": SQL})
    nuevo = o.fusionar_edicion(plan, ent)
    s = nuevo["steps"][0]
    assert s["editado"] is True and s["action"]["type"] == "sql" and s["action"]["status"] == "editado"
    assert s["accion_original"]["status"] == "no_traducido" and s["accion_original"]["type"] == "noop"
    # el cliente no puede falsear accion_original
    ent2 = _ent(nuevo, t1={"accion_original": {"type": "shell", "comando": "rm -rf /"}})
    assert o.fusionar_edicion(nuevo, ent2)["steps"][0]["accion_original"]["type"] == "noop"
    # re-editar conserva la PRIMERA original
    ent3 = _ent(nuevo, t1={"action": {"type": "shell", "comando": "echo hola"}})
    n3 = o.fusionar_edicion(nuevo, ent3)
    assert n3["steps"][0]["action"]["type"] == "shell" and n3["steps"][0]["accion_original"]["type"] == "noop"
    # restaurar
    ent4 = _ent(n3, t1={"editado": False})
    n4 = o.fusionar_edicion(n3, ent4)
    s4 = n4["steps"][0]
    assert s4["action"]["type"] == "noop" and s4["action"]["status"] == "no_traducido"
    assert "editado" not in s4 and "accion_original" not in s4


def test_editar_accion_sin_marca_editado_se_ignora():
    plan = _plan()
    nuevo = o.fusionar_edicion(plan, _ent(plan, t1={"action": {"type": "shell", "comando": "x"}}))
    assert nuevo["steps"][0]["action"]["type"] == "noop"


def test_editar_con_accion_invalida_o_graph_fuera_de_output_falla():
    plan = _plan()
    with pytest.raises(ValueError):
        o.fusionar_edicion(plan, _ent(plan, t1={"editado": True, "action": {"type": "sql", "sentencia": ""}}))
    with pytest.raises(ValueError, match="output"):
        o.fusionar_edicion(plan, _ent(plan, t1={"editado": True,
                                                "action": {"type": "graph", "target": "/etc/x_spark.py"}}))


def test_agregar_y_borrar_pasos_exige_estructura():
    plan = _plan()
    ent = _ent(plan)
    ent["steps"].append({"id": "t9", "name": "nuevo", "depends_on": ["t2"],
                         "action": {"type": "shell", "comando": "echo hi", "evil": 1}})
    with pytest.raises(ValueError, match="no coinciden"):
        o.fusionar_edicion(plan, ent)
    ent["estructura"] = True
    n = o.fusionar_edicion(plan, ent)
    assert [s["id"] for s in n["steps"]] == ["t1", "t2", "t9"]
    assert n["steps"][2]["agregado"] is True and "evil" not in n["steps"][2]["action"]
    # borrar t2 (quitando la dependencia de t9) y el enlace que lo tocaba
    n["enlaces"] = [{"id": "e1", "desde": "t1", "salida": "output/a", "hacia": "t2", "entrada": "raw/a",
                     "origen": "manual", "habilitado": True}]
    ent2 = _ent(n)
    ent2["steps"] = [s for s in ent2["steps"] if s["id"] != "t2"]
    ent2["steps"][1]["depends_on"] = ["t1"]
    ent2["estructura"] = True
    n2 = o.fusionar_edicion(n, ent2)
    assert [s["id"] for s in n2["steps"]] == ["t1", "t9"] and n2["enlaces"] == []
    # ids invalidos
    ent3 = _ent(plan)
    ent3["steps"].append({"id": "../x", "name": "n", "depends_on": [], "action": SQL})
    ent3["estructura"] = True
    with pytest.raises(ValueError):
        o.fusionar_edicion(plan, ent3)


def test_params_se_guardan_en_el_plan_y_el_paso():
    plan = _plan()
    ent = _ent(plan, t1={"params": {"SCHEMA": "qa"}})
    ent["ejecucion"] = {"params": {"FECHA": "2024-01-01"}}
    n = o.fusionar_edicion(plan, ent)
    assert n["steps"][0]["params"] == {"SCHEMA": "qa"} and n["ejecucion"]["params"] == {"FECHA": "2024-01-01"}
    ent2 = _ent(n, t1={"params": {}})
    ent2["ejecucion"] = {"params": {}}
    n2 = o.fusionar_edicion(n, ent2)
    assert "params" not in n2["steps"][0] and "params" not in n2["ejecucion"]
    assert n2["ejecucion"]["env"]["SCHEMA"] == "dev"            # env del pset intacto


def test_refrescar_no_pisa_editados_ni_params():
    alm = o.fusionar_edicion(_plan(), _ent(_plan(), t1={"editado": True, "action": SQL, "params": {"A": "1"}}))
    alm["ejecucion"]["params"] = {"B": "2"}
    nuevo = _plan()
    nuevo["steps"][0]["action"] = {"type": "script", "target": "p.ksh", "source": "p.ksh", "status": "ok"}
    nuevo["steps"][1]["action"] = {"type": "script", "target": "q.ksh", "source": "q.ksh", "status": "ok"}
    r = o.refrescar_acciones(alm, nuevo)
    assert r["steps"][0]["action"]["type"] == "sql" and r["steps"][0]["params"] == {"A": "1"}
    assert r["steps"][0]["accion_original"]["type"] == "script"       # restaurar devuelve lo vigente
    assert r["steps"][1]["action"]["type"] == "script"                # sin editar: se refresca
    assert r["ejecucion"]["params"] == {"B": "2"}
    # restaurar tras refrescar
    n = o.fusionar_edicion(r, _ent(r, t1={"editado": False}))
    assert n["steps"][0]["action"]["target"] == "p.ksh"


def test_regenerar_conserva_ediciones(tmp_path):
    ab = os.path.join(ROOT, "abinitio", "demo_plan_pset_mp")
    out = os.path.join(ROOT, "output", "demo_plan_pset_mp")
    if not (os.path.isdir(ab) and os.path.isdir(out)):
        pytest.skip("sin el proyecto demo_plan_pset_mp")
    dst = tmp_path / "out"
    shutil.copytree(out, dst)
    f = dst / "orquestacion_demo_plan_obfuscated__pset.json"
    plan = json.load(open(f, encoding="utf-8"))
    sid = next(s["id"] for s in plan["steps"] if s["name"] == "Log_status_running")
    ent = json.loads(json.dumps(plan))
    next(s for s in ent["steps"] if s["id"] == sid).update({"editado": True, "action": SQL, "params": {"X": "1"}})
    ent["ejecucion"]["params"] = {"ENABLE_FLAG": "9"}
    plan = o.fusionar_edicion(plan, ent)
    json.dump(plan, open(f, "w", encoding="utf-8"))
    o.regenerar(ab, str(dst))
    despues = json.load(open(f, encoding="utf-8"))
    st = next(s for s in despues["steps"] if s["id"] == sid)
    assert st["editado"] and st["action"]["type"] == "sql" and st["params"] == {"X": "1"}
    assert despues["ejecucion"]["params"] == {"ENABLE_FLAG": "9"}
    assert st["accion_original"]["type"] == "noop"


# ---------------------------------------------------------------------------
# .pset editado
# ---------------------------------------------------------------------------
def test_exportar_pset_formato_nativo_sin_tocar_original(tmp_path):
    ab = tmp_path / "ab"
    ab.mkdir()
    txt = "!prototype|P|||$AI_PLAN/x.plan\nENABLE_FLAG||||2\nPATH|$|||$AI_X/y\n"
    (ab / "x.pset").write_text(txt)
    plan = _plan()
    plan["pset"] = "x.pset"
    plan["ejecucion"]["params"] = {"ENABLE_FLAG": "7", "NUEVO": "v"}
    info = o.params_pset(plan, str(ab))
    assert info["params"]["ENABLE_FLAG"] == "2" and info["overrides"]["ENABLE_FLAG"] == "7"
    ruta, texto = o.exportar_pset(plan, str(ab), str(tmp_path / "out" / "psets_editados"))
    assert texto == "!prototype|P|||$AI_PLAN/x.plan\nENABLE_FLAG||||7\nPATH|$|||$AI_X/y\nNUEVO||||v\n"
    assert open(ruta).read() == texto and (ab / "x.pset").read_text() == txt
    from src import pset_map as pm
    assert pm.parse_pset_file(ruta)["params"]["ENABLE_FLAG"] == "7"
    # por paso: usa el pset del paso (action.source) y params del paso
    plan["steps"][1]["action"] = {"type": "graph", "target": None, "source": "x.pset", "status": "faltante"}
    plan["steps"][1]["params"] = {"PATH": "/nuevo"}
    _r, t2 = o.exportar_pset(plan, str(ab), str(tmp_path / "o2"), paso="t2")
    assert "PATH|$|||/nuevo" in t2 and "ENABLE_FLAG||||2" in t2
    with pytest.raises(ValueError):
        o.exportar_pset(plan, str(ab), str(tmp_path / "o3"), paso="t1")      # t1 no tiene pset


# ---------------------------------------------------------------------------
# Airflow
# ---------------------------------------------------------------------------
def test_airflow_con_sql_y_params():
    plan = o.fusionar_edicion(_plan(), _ent(_plan(), t1={"editado": True, "action": SQL, "params": {"SCHEMA": "qa"}}))
    plan["ejecucion"]["params"] = {"FECHA": "hoy"}
    code = o.generar_airflow(plan)
    compile(code, "dag.py", "exec")
    assert "src.orq_sql" in code and "'FECHA': 'hoy'" in code and "'SCHEMA': 'qa'" in code
    assert "s3cr3t" not in code.split("bash_command")[1] if "bash_command" in code else True


# ---------------------------------------------------------------------------
# ejecucion real del runner (pyspark local; jdbc contra Derby embebido que trae pyspark)
# ---------------------------------------------------------------------------
def _spark_ok():
    try:
        import pyspark
    except ImportError:
        return None
    if not shutil.which("java"):
        return None
    return os.path.join(os.path.dirname(pyspark.__file__), "jars")


@pytest.mark.skipif(_spark_ok() is None, reason="requiere pyspark y java")
def test_runner_spark_sql_ejecuta_en_local(tmp_path):
    destino = tmp_path / "log"
    plan = _plan()
    plan["ejecucion"]["env"]["DESTINO"] = str(destino)
    plan["steps"][0]["action"] = o.normalizar_accion({
        "type": "sql", "motor": "spark_sql",
        "sentencia": "INSERT OVERWRITE DIRECTORY '${DESTINO}' USING parquet "
                     "SELECT 'running' AS estado, '${SCHEMA}' AS esquema"})
    plan["steps"][1]["enabled"] = False
    assert o.ejecutar(plan, real=True, base_path=str(tmp_path / "b"))
    assert any(f.endswith(".parquet") for f in os.listdir(destino))


@pytest.mark.skipif(_spark_ok() is None, reason="requiere pyspark y java")
def test_runner_jdbc_secuencia_derby(tmp_path):
    jars = _spark_ok()
    derby = sorted(f for f in os.listdir(jars) if f.startswith("derby-") and "tools" not in f)
    if not derby:
        pytest.skip("pyspark sin derby")
    a = o.normalizar_accion({
        "type": "sql", "motor": "jdbc", "url": f"jdbc:derby:{tmp_path}/db;create=true",
        "driver": "org.apache.derby.jdbc.EmbeddedDriver", "jar": os.path.join(jars, derby[0]),
        "sentencia": "CREATE SEQUENCE seq_log START WITH 100;\n"
                     "CREATE TABLE log_status (id INT, estado VARCHAR(20));\n"
                     "INSERT INTO log_status VALUES (NEXT VALUE FOR seq_log, '${ESTADO}');\n"
                     "SELECT id, estado FROM log_status",
        "usuario": "app", "password_env": "BNX_TEST_PW"})
    cmd = o.build_command({"id": "t", "action": a}, o._ej({"ejecucion": {"env": {"ESTADO": "running"}}}))
    env = dict(os.environ, BNX_TEST_PW="x", ESTADO="running", PYTHONPATH=ROOT)
    r = subprocess.run(cmd, env=env, cwd=str(tmp_path), capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "('100', 'running')" in r.stdout
    # falla: la tabla ya existe -> codigo != 0
    r2 = subprocess.run(cmd, env=env, cwd=str(tmp_path), capture_output=True, text=True, timeout=300)
    assert r2.returncode != 0
def test_guardar_quita_params_vacios_pero_no_los_ausentes():
    # La GUI manda params={} para quitar los overrides (si la clave falta, el servidor la conserva)
    base = _plan()
    base["ejecucion"]["params"] = {"A": "1"}
    base["steps"][0]["params"] = {"X": "1"}
    ent = _ent(base)
    ent["ejecucion"] = {"modo": "python"}
    del ent["steps"][0]["params"]
    n = o.fusionar_edicion(base, ent)
    assert n["ejecucion"]["params"] == {"A": "1"} and n["steps"][0]["params"] == {"X": "1"}
    ent["ejecucion"] = {"params": {}}
    ent["steps"][0]["params"] = {}
    n = o.fusionar_edicion(base, ent)
    assert "params" not in n["ejecucion"] and "params" not in n["steps"][0]
