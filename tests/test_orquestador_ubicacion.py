# -*- coding: utf-8 -*-
"""Orquestador: ubicacion en disco del plan/DAG y accion 'abrir_carpeta' (sin abrir nada real)."""
import json
import os
import shutil
import sys
import threading
import urllib.error
import urllib.request
from unittest import mock

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import orquestador as o  # noqa: E402


@pytest.fixture(scope="module")
def srv():
    import socketserver
    import serve_ui

    class S(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        daemon_threads = True

    httpd = S(("127.0.0.1", 0), serve_ui.BNXHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    proy = os.path.join(ROOT, "output", "pytest_ubic_tmp")
    shutil.rmtree(proy, ignore_errors=True)
    f = o.nueva("ubic", "pytest_ubic_tmp", base=os.path.join(ROOT, "output"))
    yield {"url": f"http://127.0.0.1:{httpd.server_address[1]}/orquestador",
           "plan": os.path.relpath(f, ROOT), "carpeta": os.path.dirname(os.path.realpath(f))}
    httpd.shutdown()
    httpd.server_close()
    shutil.rmtree(proy, ignore_errors=True)


def _post(srv, action, body, headers=None):
    req = urllib.request.Request(f"{srv['url']}/{action}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **(headers or {})}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_ubicacion_devuelve_rutas_absolutas(srv):
    st, d = _post(srv, "ubicacion", {"file": srv["plan"]})
    assert st == 200 and d["ok"]
    assert os.path.isabs(d["plan"]) and d["plan"].endswith(os.path.basename(srv["plan"]))
    assert d["carpeta"] == os.path.dirname(d["plan"])
    assert os.path.basename(d["dag"]).startswith("dag_") and d["dag"].endswith(".py")
    assert os.path.dirname(d["dag"]) == d["carpeta"] and d["dag_existe"] is False


def test_abrir_carpeta_invoca_opener_con_lista_de_args(srv):
    with mock.patch("shutil.which", return_value="/usr/bin/opener"), \
            mock.patch("subprocess.run", return_value=mock.Mock(returncode=0)) as run:
        st, d = _post(srv, "abrir_carpeta", {"file": srv["plan"]})
    assert st == 200 and d["ok"] and d["carpeta"] == srv["carpeta"]
    cmd = run.call_args[0][0]
    assert isinstance(cmd, list) and cmd[-1] == srv["carpeta"]
    assert cmd[0] in ("open", "explorer", "xdg-open")
    assert not run.call_args[1].get("shell")


def test_abrir_carpeta_rechaza_origen_no_local(srv):
    with mock.patch("subprocess.run") as run:
        st, d = _post(srv, "abrir_carpeta", {"file": srv["plan"]}, headers={"Origin": "http://evil.example.com"})
    assert st == 403 and d["ok"] is False
    run.assert_not_called()


def test_abrir_carpeta_rechaza_ip_remota():
    import serve_ui
    h = serve_ui.BNXHandler.__new__(serve_ui.BNXHandler)
    h.client_address = ("10.1.2.3", 5555)
    h.headers = {}
    with mock.patch.dict(os.environ, {"BNX_PERMITIR_EJECUCION_REMOTA": "0"}):
        assert "solo se acepta desde esta maquina" in h._orq_local_only()


def test_abrir_carpeta_rechaza_traversal_y_fuera_de_output(srv, tmp_path):
    import serve_ui
    with mock.patch("subprocess.run") as run:
        for malo in (ROOT, os.path.join(ROOT, "src"), str(tmp_path),
                     os.path.join(ROOT, "output", "..", "src"), "", None):
            st, d = serve_ui._orq_abrir_carpeta(ROOT, malo)
            assert st == 400 and d["ok"] is False, malo
        # symlink dentro de output/ que apunta fuera
        enlace = os.path.join(ROOT, "output", "pytest_ubic_tmp", "salida_link")
        try:
            os.symlink(str(tmp_path), enlace)
        except (OSError, NotImplementedError):
            enlace = None
        if enlace:
            st, _ = serve_ui._orq_abrir_carpeta(ROOT, enlace)
            assert st == 400
    run.assert_not_called()
    # archivo plan con ruta fuera de output/ -> 400 antes de llegar al opener
    st, _ = _post(srv, "abrir_carpeta", {"file": "../../etc/passwd"})
    assert st == 400


def test_abrir_carpeta_sin_comando_da_error_claro(srv):
    import serve_ui
    with mock.patch("shutil.which", return_value=None), mock.patch("subprocess.run") as run:
        if os.name == "nt":
            pytest.skip("explorer siempre existe en Windows")
        st, d = serve_ui._orq_abrir_carpeta(ROOT, srv["carpeta"])
    assert st == 501 and d["ok"] is False and "abre la carpeta a mano" in d["error"]
    run.assert_not_called()
