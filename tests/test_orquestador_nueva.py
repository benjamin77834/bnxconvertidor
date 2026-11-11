"""Orquestaciones desde cero y pasos local / remoto / nube (sin llamar a AWS, SSH ni HTTP reales)."""
import json
import os
import py_compile
import sys
from unittest import mock

import pytest

from src import orquestador as o


@pytest.fixture
def orq(tmp_path):
    ruta = o.nueva("demo", "proy", base=str(tmp_path))
    with open(ruta, encoding="utf-8") as f:
        return ruta, json.load(f)


def _paso(plan, tipo, nombre="p", deps=None, **campos):
    return o.agregar_paso(plan, tipo, nombre, deps, **campos)


def test_nueva_produce_json_valido(tmp_path):
    ruta = o.nueva("demo", "proy", base=str(tmp_path))
    assert ruta == str(tmp_path / "proy" / "orquestacion_demo.json")
    plan = json.load(open(ruta, encoding="utf-8"))
    assert plan["origen"] == "manual" and plan["steps"] == [] and plan["enlaces"] == []
    # mismo esquema que las generadas desde planes
    assert {"plan", "nombre", "direccion", "ejecucion", "steps", "enlaces"} <= set(plan)
    o.validar_plan(plan)
    assert o.topo_order(plan["steps"]) == []
    assert o.ejecutar(plan, real=False)
    compile(o.generar_airflow(plan), "dag.py", "exec")
    with pytest.raises(ValueError, match="ya existe"):
        o.nueva("demo", "proy", base=str(tmp_path))
    for malo in ("../x", "a b", ""):
        with pytest.raises(ValueError):
            o.nueva(malo, "proy", base=str(tmp_path))
    with pytest.raises(ValueError):
        o.nueva("ok", "../proy", base=str(tmp_path))


def test_plan_no_manual_sigue_exigiendo_pasos():
    with pytest.raises(ValueError, match="sin pasos"):
        o.validar_plan({"plan": "x", "steps": []})


# tipo, campos, argv esperado
CASOS = [
    ("python", {"target": "job.py", "args": ["--a", "1"]}, [sys.executable, "job.py", "--a", "1"]),
    ("shell", {"comando": "ls -l 'mi dir'"}, ["ls", "-l", "mi dir"]),
    ("shell", {"comando": "prepara.ksh x"}, ["ksh", "prepara.ksh", "x"]),
    ("spark_submit", {"target": "j.py", "master": "local[2]", "spark_args": ["--conf", "a=b"], "args": ["x"]},
     ["spark-submit", "--master", "local[2]", "--conf", "a=b", "j.py", "x"]),
    ("ssh", {"host": "srv.local", "usuario": "etl", "puerto": 2222, "identidad": "~/.ssh/id", "comando": "ls /data"},
     ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-p", "2222", "-i", "~/.ssh/id",
      "etl@srv.local", "ls /data"]),
    ("http", {"metodo": "post", "url": "https://x.io/hook", "body": {"a": 1}, "headers": {"X-Env": "dev"}},
     ["curl", "-sS", "--fail", "--max-time", "30", "-X", "POST", "-H", "X-Env: dev",
      "-H", "Content-Type: application/json", "--data-binary", '{"a": 1}', "https://x.io/hook"]),
    ("http", {"url": "https://x.io", "token_env": "MI_TOKEN"},
     ["curl", "-sS", "--fail", "--max-time", "30", "-X", "GET", "-H", "@-", "https://x.io"]),
    ("esperar_archivo", {"ruta": "/tmp/listo.ok", "timeout_s": 60, "intervalo_s": 5},
     [sys.executable, "-m", "src.orquestador", "esperar", "/tmp/listo.ok", "--timeout", "60", "--intervalo", "5"]),
    ("glue_job", {"job_name": "mi-job", "args": {"--fecha": "2024-01-01"}, "profile": "dev", "region": "us-east-1"},
     ["aws", "--profile", "dev", "--region", "us-east-1", "glue", "start-job-run", "--job-name", "mi-job",
      "--arguments", '{"--fecha": "2024-01-01"}']),
    ("emr_step", {"cluster_id": "j-ABC123", "script": "s3://b/job.py", "args": ["x"]},
     ["aws", "emr", "add-steps", "--cluster-id", "j-ABC123", "--steps",
      json.dumps([{"Type": "Spark", "Name": "bnx-step", "ActionOnFailure": "CONTINUE",
                   "Args": ["--deploy-mode", "cluster", "s3://b/job.py", "x"]}])]),
    ("lambda", {"function_name": "fn", "payload": {"k": "v"}},
     ["aws", "lambda", "invoke", "--function-name", "fn", "--cli-binary-format", "raw-in-base64-out",
      "--payload", '{"k": "v"}', os.devnull]),
    ("s3_copy", {"origen": "/tmp/out", "destino": "s3://b/p/", "recursivo": True},
     ["aws", "s3", "cp", "--recursive", "/tmp/out", "s3://b/p/"]),
]


@pytest.mark.parametrize("tipo,campos,esperado", CASOS)
def test_build_command_argv(orq, tipo, campos, esperado):
    _, plan = orq
    st = _paso(plan, tipo, **campos)
    ej = o._ej(plan)
    with mock.patch.object(o, "_spark_submit_bin", return_value="spark-submit"):
        assert o.build_command(st, ej) == esperado


def test_aws_toma_profile_region_global_y_el_paso_manda(orq):
    _, plan = orq
    plan["ejecucion"]["aws"] = {"profile": "global", "region": "eu-west-1"}
    o.validar_plan(plan)
    g = _paso(plan, "glue_job", job_name="j")
    assert o.build_command(g, o._ej(plan))[:5] == ["aws", "--profile", "global", "--region", "eu-west-1"]
    h = _paso(plan, "glue_job", job_name="j", profile="otro")
    assert o.build_command(h, o._ej(plan))[1:3] == ["--profile", "otro"]
    plan["ejecucion"]["aws"] = {"profile": "mal perfil"}
    with pytest.raises(ValueError):
        o.validar_plan(plan)


def test_esperar_s3_pasa_profile_y_es_nube(orq):
    _, plan = orq
    st = _paso(plan, "esperar_archivo", ruta="s3://b/listo.ok", profile="dev")
    assert st["action"]["ubicacion"] == "nube"
    assert o.build_command(st, o._ej(plan))[-2:] == ["--profile", "dev"]
    assert _paso(plan, "esperar_archivo", ruta="/x/y")["action"]["ubicacion"] == "local"


INVALIDOS = [
    ("python", {}), ("python", {"target": "-x.py"}), ("shell", {"comando": ""}),
    ("shell", {"comando": "echo 'sin cerrar"}), ("spark_submit", {}),
    ("ssh", {"host": "-oProxyCommand=x", "comando": "ls"}), ("ssh", {"host": "h"}),
    ("ssh", {"host": "h", "comando": "ls", "usuario": "a b"}),
    ("ssh", {"host": "h", "comando": "ls", "identidad": "-----BEGIN PRIVATE KEY-----"}),
    ("ssh", {"host": "h", "comando": "ls", "puerto": 70000}),
    ("http", {}), ("http", {"url": "ftp://x"}), ("http", {"url": "https://x", "metodo": "TRACE"}),
    ("http", {"url": "https://x", "headers": {"Authorization": "Bearer abc"}}),
    ("http", {"url": "https://x", "headers": {"X-Api-Key": "k"}}),
    ("http", {"url": "https://x", "token_env": "no es env"}),
    ("http", {"url": "https://x", "body": "@/etc/passwd"}),
    ("esperar_archivo", {}), ("esperar_archivo", {"ruta": "s3:///x"}),
    ("esperar_archivo", {"ruta": "/x", "timeout_s": 0}),
    ("glue_job", {}), ("glue_job", {"job_name": "a b"}), ("glue_job", {"job_name": "j", "args": {"x": "1"}}),
    ("emr_step", {"cluster_id": "j-ABC"}), ("emr_step", {"cluster_id": "mal", "script": "s3://b/x.py"}),
    ("emr_step", {"cluster_id": "j-ABC", "script": "/local/x.py"}),
    ("lambda", {}), ("lambda", {"function_name": "-x"}),
    ("s3_copy", {"origen": "/a"}), ("s3_copy", {"origen": "/a", "destino": "/b"}),
    ("s3_copy", {"origen": "--x", "destino": "s3://b/c"}),
    ("glue_job", {"job_name": "j", "region": "ZZ"}),
]


@pytest.mark.parametrize("tipo,campos", INVALIDOS)
def test_validacion_de_campos(orq, tipo, campos):
    _, plan = orq
    with pytest.raises(ValueError):
        _paso(plan, tipo, **campos)
    assert plan["steps"] == []          # el paso rechazado no queda


def test_validar_plan_detecta_accion_mala_editada_a_mano(orq):
    _, plan = orq
    st = _paso(plan, "glue_job", job_name="j")
    st["action"]["job_name"] = "a; rm -rf /"
    with pytest.raises(ValueError, match=st["id"]):
        o.validar_plan(plan)


def test_sin_inyeccion_el_argumento_es_un_solo_elemento(orq):
    _, plan = orq
    st = _paso(plan, "ssh", host="h", comando="ls; rm -rf /")
    assert o.build_command(st, o._ej(plan))[-1] == "ls; rm -rf /"
    st = _paso(plan, "python", target="j.py", args=["$(whoami)", "a b"])
    assert o.build_command(st, o._ej(plan))[2:] == ["$(whoami)", "a b"]


def test_dry_run_no_ejecuta_nada(orq, capsys, monkeypatch):
    _, plan = orq
    monkeypatch.setenv("MI_TOKEN", "secreto-123")
    a = _paso(plan, "esperar_archivo", "espera", ruta="/tmp/x.ok")
    b = _paso(plan, "s3_copy", "sube", [a["id"]], origen="/tmp/o", destino="s3://b/p")
    _paso(plan, "glue_job", "glue", [b["id"]], job_name="j")
    _paso(plan, "http", "notifica", None, url="https://x.io", token_env="MI_TOKEN")
    _paso(plan, "ssh", "remoto", None, host="srv", comando="uptime")
    with mock.patch("subprocess.run") as run, mock.patch("subprocess.Popen") as popen:
        assert o.ejecutar(plan, real=False)
    run.assert_not_called()
    popen.assert_not_called()
    out = capsys.readouterr().out
    assert "DRY-RUN" in out
    for frag in ("[local/esperar_archivo]", "[nube/s3_copy]", "aws s3 cp /tmp/o s3://b/p",
                 "glue start-job-run --job-name j", "[remoto/http]", "curl -sS --fail", "ssh -o BatchMode=yes"):
        assert frag in out
    assert "secreto-123" not in out          # el token nunca se imprime


def test_real_usa_argv_sin_shell_y_token_por_stdin(orq, monkeypatch):
    _, plan = orq
    monkeypatch.setenv("MI_TOKEN", "tok-abc")
    _paso(plan, "http", url="https://x.io", token_env="MI_TOKEN")
    _paso(plan, "glue_job", job_name="j")
    with mock.patch("subprocess.run", return_value=mock.Mock(returncode=0)) as run:
        assert o.ejecutar(plan, real=True)
    llamadas = {c.args[0][0]: c for c in run.call_args_list}
    curl = llamadas["curl"]
    assert "tok-abc" not in " ".join(curl.args[0])
    assert curl.kwargs["input"] == "Authorization: Bearer tok-abc\n"
    assert not curl.kwargs.get("shell")
    assert not llamadas["aws"].kwargs.get("shell")


def test_real_sin_token_falla_sin_ejecutar(orq, monkeypatch):
    _, plan = orq
    monkeypatch.delenv("MI_TOKEN", raising=False)
    _paso(plan, "http", url="https://x.io", token_env="MI_TOKEN")
    with mock.patch("subprocess.run") as run:
        assert not o.ejecutar(plan, real=True)
    run.assert_not_called()


def test_real_fallo_bloquea_dependientes(orq):
    _, plan = orq
    a = _paso(plan, "ssh", "a", host="h", comando="false")
    _paso(plan, "glue_job", "b", [a["id"]], job_name="j")
    with mock.patch("subprocess.run", return_value=mock.Mock(returncode=255)) as run:
        assert not o.ejecutar(plan, real=True)
    assert run.call_count == 1


def test_sensor_local_y_s3(tmp_path):
    f = tmp_path / "listo.ok"
    assert not o.esperar_archivo(str(f), timeout=0, intervalo=1, sleep=lambda s: None)
    f.write_text("x")
    assert o.esperar_archivo(str(tmp_path / "*.ok"), timeout=5, intervalo=1)
    corridas = []

    def run(cmd, **kw):
        corridas.append(cmd)
        return mock.Mock(returncode=0, stdout="")
    assert o.esperar_archivo("s3://b/dir/k.ok", timeout=5, intervalo=1, profile="dev", run=run)
    assert corridas[0] == ["aws", "--profile", "dev", "s3api", "head-object", "--bucket", "b", "--key", "dir/k.ok"]


def test_airflow_compila_con_todos_los_tipos(orq, tmp_path):
    _, plan = orq
    prev = None
    for tipo, campos, _ in CASOS:
        prev = _paso(plan, tipo, f"paso_{tipo}", [prev["id"]] if prev else None, **campos)
    _paso(plan, "shell", "sh", None, comando="/x/script.sh")
    dag = o.generar_airflow(plan)
    py = tmp_path / "dag.py"
    py.write_text(dag)
    py_compile.compile(str(py), doraise=True)
    assert "aws" in dag and "glue" in dag and "curl" in dag and "ssh" in dag
    assert "MI_TOKEN:?" in dag and "Authorization: Bearer" in dag
    assert "tok" not in dag.replace("token", "")
    assert "spark-submit --master 'local[2]'" in dag and "python3 job.py" in dag
    assert "script.sh'" not in dag      # termina con espacio para no ser plantilla .sh


def test_componer_acepta_manuales(orq, tmp_path):
    ruta, plan = orq
    _paso(plan, "shell", comando="echo hola")
    o._write(ruta, plan)
    ruta2 = o.nueva("otra", "proy", base=str(tmp_path))
    p2 = json.load(open(ruta2))
    _paso(p2, "shell", comando="echo chao")
    o._write(ruta2, p2)
    pp = o.componer("juntas", [ruta, ruta2])
    assert [s["action"]["pasos"] for s in pp["steps"]] == [1, 1]
    assert pp["steps"][1]["depends_on"] == ["p1"]
    assert o.ejecutar(pp, real=False)
    compile(o.generar_airflow(pp), "dag.py", "exec")


def test_fusionar_edicion_manual_agrega_edita_y_borra(orq):
    _, plan = orq
    a = _paso(plan, "shell", "a", comando="echo a")
    entrante = json.loads(json.dumps(plan))
    entrante["steps"].append({"id": "t9", "name": "nube", "depends_on": [a["id"]],
                              "action": {"type": "glue_job", "job_name": "j", "evil": "x", "status": "ok"}})
    nuevo = o.fusionar_edicion(plan, entrante)
    assert [s["id"] for s in nuevo["steps"]] == ["t1", "t9"]
    assert "evil" not in nuevo["steps"][1]["action"]            # lista blanca de campos
    # editar y borrar el primero
    ent2 = json.loads(json.dumps(nuevo))
    ent2["steps"] = [ent2["steps"][1]]
    ent2["steps"][0]["depends_on"] = []
    assert [s["id"] for s in o.fusionar_edicion(nuevo, ent2)["steps"]] == ["t9"]
    # dependencia a un paso inexistente / ciclo se rechazan
    ent3 = json.loads(json.dumps(nuevo))
    ent3["steps"][0]["depends_on"] = ["t9"]
    with pytest.raises(ValueError):
        o.fusionar_edicion(nuevo, ent3)


def test_fusionar_edicion_graph_solo_dentro_de_output(orq):
    _, plan = orq
    ent = json.loads(json.dumps(plan))
    ent["steps"] = [{"id": "t1", "name": "g", "depends_on": [],
                     "action": {"type": "graph", "target": "/etc/passwd.py"}}]
    with pytest.raises(ValueError, match="output"):
        o.fusionar_edicion(plan, ent)


def test_planes_normales_no_aceptan_pasos_nuevos_desde_la_gui(tmp_path):
    st = [{"id": "t1", "name": "j", "depends_on": [], "dep_flags": {}, "solo_en_fallo": False,
           "enabled": True, "continue_on_error": False,
           "action": {"type": "noop", "target": None, "source": None, "status": "no_traducido"}}]
    base = {"plan": "x.plan", "nombre": "x", "direccion": "prior", "ejecucion": dict(o.EJECUCION_DEFECTO),
            "steps": st, "enlaces": []}
    ent = json.loads(json.dumps(base))
    ent["steps"].append({"id": "t2", "name": "n", "depends_on": [], "action": {"type": "shell", "comando": "x"}})
    with pytest.raises(ValueError, match="no coinciden"):
        o.fusionar_edicion(base, ent)


def test_paso_graph_manual_resuelve_estado_y_io(orq, tmp_path):
    _, plan = orq
    job = tmp_path / "x_spark.py"
    job.write_text('class PARAMS:\n    BASE_PATH = os.environ.get("BNX_BASE_PATH", "s3://b")\n'
                   'df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/clientes")\n'
                   'df.write.parquet(f"{PARAMS.BASE_PATH}/output/salida")\n')
    ok = _paso(plan, "graph", "g", target=str(job))
    assert ok["action"]["status"] == "ok"
    assert ok["action"]["io"]["lee"][0]["ruta"] == "raw/clientes"
    falta = _paso(plan, "graph", "g2", target=str(tmp_path / "no_spark.py"))
    assert falta["action"]["status"] == "faltante"


def test_cli_nueva_paso_add_rm_y_mostrar(tmp_path, capsys):
    assert o.main(["nueva", "cli", "--proyecto", "p", "--out", str(tmp_path)]) == 0
    ruta = str(tmp_path / "p" / "orquestacion_cli.json")
    assert o.main(["paso-add", ruta, "--tipo", "shell", "--nombre", "uno", "--campo", "comando=echo hola"]) == 0
    assert o.main(["paso-add", ruta, "--tipo", "glue_job", "--nombre", "dos", "--despues-de", "uno",
                   "--campo", "job_name=j", "--campo", 'args={"--k": "v"}']) == 0
    plan = json.load(open(ruta))
    assert [s["depends_on"] for s in plan["steps"]] == [[], ["t1"]]
    assert plan["steps"][1]["action"]["args"] == {"--k": "v"}
    capsys.readouterr()
    assert o.main(["ejecutar", ruta]) == 0
    assert "aws glue start-job-run" in capsys.readouterr().out
    assert o.main(["paso-rm", ruta, "uno"]) == 0
    plan = json.load(open(ruta))
    assert [s["id"] for s in plan["steps"]] == ["t2"] and plan["steps"][0]["depends_on"] == []
