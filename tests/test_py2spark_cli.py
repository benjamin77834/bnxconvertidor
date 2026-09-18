# Tests de la CLI de py2spark (python -m py2spark convert ...).
import io
import os
import sys

# Raiz del proyecto al path (NO src/ al frente, para no sombrear src/main.py).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.py2spark.cli import main  # noqa: E402


def _run(argv, stdin_text=None, capsys=None, monkeypatch=None):
    if stdin_text is not None:
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
    rc = main(argv)
    out = capsys.readouterr()
    return rc, out.out, out.err


def test_cli_stdin_to_stdout(capsys, monkeypatch):
    rc, out, err = _run(
        ["convert"], stdin_text='import pandas as pd\ndf = pd.read_csv("f.csv")\n',
        capsys=capsys, monkeypatch=monkeypatch,
    )
    assert rc == 0
    assert "spark.read" in out
    assert "SparkSession" in out


def test_cli_file_to_file(tmp_path, capsys, monkeypatch):
    inp = tmp_path / "in.py"
    outp = tmp_path / "out.py"
    inp.write_text('import pandas as pd\ndf = pd.read_csv("f.csv")\ndf = df[df["x"] > 0]\n')
    rc, out, err = _run(["convert", str(inp), "-o", str(outp)], capsys=capsys, monkeypatch=monkeypatch)
    assert rc == 0
    generated = outp.read_text()
    assert "df.filter(F.col('x') > 0)" in generated
    assert "escrito" in err  # aviso a stderr


def test_cli_json_mode(capsys, monkeypatch):
    import json
    rc, out, err = _run(
        ["convert", "--json"], stdin_text='import pandas as pd\ndf = pd.read_csv("f.csv")\n',
        capsys=capsys, monkeypatch=monkeypatch,
    )
    assert rc == 0
    data = json.loads(out)
    assert data["ok"] is True
    assert "code" in data and "warnings" in data and "unsupported" in data


def test_cli_invalid_python_exit_1(capsys, monkeypatch):
    rc, out, err = _run(
        ["convert"], stdin_text="def broken(:\n  pass",
        capsys=capsys, monkeypatch=monkeypatch,
    )
    assert rc == 1
    assert "error:" in err


def test_cli_no_command_returns_2(capsys):
    rc = main([])
    assert rc == 2
