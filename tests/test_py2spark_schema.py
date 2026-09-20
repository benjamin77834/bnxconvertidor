# Tests de inferencia de esquema desde codigo PySpark (para Data Redactada).
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.py2spark import convert_code, infer_input_schema  # noqa: E402


def _schema_of(python_src):
    code = convert_code(python_src)["code"]
    return infer_input_schema(code)


def _cols(schema):
    return {c["name"] for s in schema for c in s["columns"]}


def test_read_csv_source_detected():
    sch = _schema_of('import pandas as pd\ndf = pd.read_csv("v.csv")\ndf = df[df["monto"] > 0]\n')
    assert [s["node"] for s in sch] == ["df"]
    assert "monto" in _cols(sch)


def test_read_excel_maps_to_source():
    # read_excel se mapea a csv (aprox); debe detectarse como fuente igual.
    sch = _schema_of('import pandas as pd\ndf = pd.read_excel("f.xlsx")\ndf = df[df["x"] > 0]\n')
    assert sch, "read_excel deberia producir una fuente detectable"
    assert "x" in _cols(sch)


def test_spark_read_format_load():
    sch = infer_input_schema(
        'df = spark.read.format("csv").load("f.csv")\ndf = df.filter(F.col("x") > 0)\n'
    )
    assert [s["node"] for s in sch] == ["df"]
    assert "x" in _cols(sch)


def test_spark_table_and_select():
    sch = infer_input_schema('df = spark.table("ventas")\ndf = df.select("monto", "region")\n')
    assert [s["node"] for s in sch] == ["df"]
    assert {"monto", "region"} <= _cols(sch)


def test_fallback_when_no_read_but_columns():
    # pandas DataFrame literal (sin read): antes daba 0 fuentes -> bloqueaba Data
    # Redactada. Ahora el fallback genera un dataset 'input' con las columnas.
    sch = _schema_of('import pandas as pd\ndf = pd.DataFrame({"a": [1]})\ndf = df[df["a"] > 0]\n')
    assert sch, "deberia generar un dataset fallback con las columnas referenciadas"
    assert "a" in _cols(sch)


def test_numeric_type_inference():
    sch = infer_input_schema(
        'df = spark.read.csv("v")\ndf = df.filter(F.col("monto") > 100)\n'
    )
    cols = {c["name"]: c["type"] for s in sch for c in s["columns"]}
    assert cols.get("monto") == "decimal"  # comparado con numero => numerico


def test_pii_detection():
    sch = infer_input_schema(
        'df = spark.read.csv("v")\ndf = df.select("nombre", "email", "monto")\n'
    )
    pii = {c["name"]: c["pii"] for s in sch for c in s["columns"]}
    assert pii.get("nombre") is True
    assert pii.get("email") is True
    assert pii.get("monto") is False


def test_never_empty_for_pyspark_job():
    # Un job PySpark generado por py2spark SIEMPRE debe producir >=1 dataset,
    # aunque no tenga fuente clara, para no bloquear Data Redactada.
    sch = _schema_of('import pandas as pd\nx = 1 + 2\nprint("hola")\n')
    assert len(sch) >= 1
    assert sch[0]["node"] == "input"


def test_regex_safety_net_detects_spark_read():
    # Aunque el AST no capture la fuente, el regex de red de seguridad la detecta.
    code = (
        "from pyspark.sql import SparkSession\n"
        "spark = SparkSession.builder.getOrCreate()\n"
        "mi_tabla = spark.read.parquet('/ruta/x')\n"
    )
    sch = infer_input_schema(code)
    assert any(s["node"] == "mi_tabla" for s in sch)
