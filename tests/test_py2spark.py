# Tests de la libreria py2spark (Python/pandas -> PySpark 3).
import ast
import sys
import os

# La raiz del proyecto al path (NO src/ al frente: eso sombrearia src/main.py
# sobre el main.py de la raiz y romperia otros tests que hacen 'import main').
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.py2spark import convert_code  # noqa: E402


def _conv(src):
    r = convert_code(src)
    assert r["ok"], r
    # el codigo generado SIEMPRE debe ser Python valido
    ast.parse(r["code"])
    return r


def test_read_csv_to_spark():
    r = _conv('import pandas as pd\ndf = pd.read_csv("f.csv")\n')
    assert "spark.read" in r["code"] and ".csv('f.csv')" in r["code"]
    assert "import pandas" not in r["code"]  # se elimina el import de pandas
    assert "SparkSession" in r["code"]       # preambulo inyectado


def test_read_parquet():
    r = _conv('import pandas as pd\ndf = pd.read_parquet("data")\n')
    assert "spark.read.parquet('data')" in r["code"]


def test_boolean_filter():
    r = _conv('import pandas as pd\ndf = pd.read_csv("f.csv")\ndf = df[df["x"] > 0]\n')
    assert "df.filter(F.col('x') > 0)" in r["code"]


def test_column_select_list():
    r = _conv('import pandas as pd\ndf = pd.read_csv("f.csv")\ns = df[["a", "b"]]\n')
    assert "df.select('a', 'b')" in r["code"]


def test_withcolumn_assignment():
    r = _conv('import pandas as pd\ndf = pd.read_csv("f.csv")\ndf["y"] = df["a"] + df["b"]\n')
    assert "df.withColumn('y', F.col('a') + F.col('b'))" in r["code"]


def test_groupby_agg():
    r = _conv('import pandas as pd\ndf = pd.read_csv("f.csv")\ng = df.groupby("k").agg({"a": "sum", "b": "mean"})\n')
    assert "df.groupBy('k')" in r["code"]
    assert "F.sum('a').alias('a')" in r["code"]
    assert "F.avg('b').alias('b')" in r["code"]


def test_merge_to_join():
    r = _conv(
        'import pandas as pd\n'
        'a = pd.read_csv("a.csv")\n'
        'b = pd.read_csv("b.csv")\n'
        'j = a.merge(b, on="id", how="left")\n'
    )
    assert "a.join(b, on='id', how='left')" in r["code"]


def test_sort_values_desc():
    r = _conv('import pandas as pd\ndf = pd.read_csv("f.csv")\ndf = df.sort_values("x", ascending=False)\n')
    assert "df.orderBy(F.col('x').desc())" in r["code"]


def test_head_to_limit():
    r = _conv('import pandas as pd\ndf = pd.read_csv("f.csv")\nt = df.head(10)\n')
    assert "df.limit(10)" in r["code"]


def test_rename_to_withcolumnrenamed():
    r = _conv('import pandas as pd\ndf = pd.read_csv("f.csv")\ndf = df.rename(columns={"a": "b"})\n')
    assert "withColumnRenamed('a', 'b')" in r["code"]


def test_drop_columns():
    r = _conv('import pandas as pd\ndf = pd.read_csv("f.csv")\ndf = df.drop(columns=["a", "b"])\n')
    assert "df.drop('a', 'b')" in r["code"]


def test_to_csv_write():
    r = _conv('import pandas as pd\ndf = pd.read_csv("f.csv")\ndf.to_csv("out.csv")\n')
    assert "df.write.mode('overwrite')" in r["code"]
    assert ".csv('out.csv')" in r["code"]


def test_len_to_count():
    r = _conv('import pandas as pd\ndf = pd.read_csv("f.csv")\nn = len(df)\n')
    assert "df.count()" in r["code"]


def test_iterrows_marked_unsupported():
    r = _conv(
        'import pandas as pd\n'
        'df = pd.read_csv("f.csv")\n'
        'for i, row in df.iterrows():\n'
        '    print(row["x"])\n'
    )
    assert any("iterrows" in u for u in r["unsupported"])
    assert "# TODO py2spark:" in r["code"]


def test_series_apply_marked_unsupported():
    r = _conv('import pandas as pd\ndf = pd.read_csv("f.csv")\ndf["u"] = df["x"].apply(lambda v: v * 2)\n')
    assert any("apply" in u.lower() for u in r["unsupported"])


def test_invalid_python_not_ok():
    r = convert_code("def broken(:\n  pass")
    assert r["ok"] is False
    assert r["code"] == "def broken(:\n  pass"  # no se toca


def test_non_pandas_code_left_mostly_intact():
    src = 'x = 1 + 2\nprint(x)\n'
    r = convert_code(src)
    assert r["ok"]
    assert "print(x)" in r["code"]
    # sin pandas: no se inyecta el preambulo de Spark
    assert "SparkSession" not in r["code"]


def test_full_pipeline_compiles():
    src = (
        'import pandas as pd\n'
        'df = pd.read_csv("ventas.csv")\n'
        'df = df[df["monto"] > 100]\n'
        'df["neto"] = df["monto"] - df["impuesto"]\n'
        'g = df.groupby("region").agg({"monto": "sum"})\n'
        'cli = pd.read_parquet("clientes")\n'
        'j = df.merge(cli, on="cliente_id", how="inner")\n'
        'j = j.sort_values("monto", ascending=False)\n'
        'j.to_parquet("salida")\n'
    )
    r = _conv(src)
    assert "spark.read" in r["code"]
    assert "df.filter(" in r["code"]
    assert "df.groupBy('region')" in r["code"]
    assert "df.join(cli, on='cliente_id', how='inner')" in r["code"]
    assert "j.write.mode('overwrite').parquet('salida')" in r["code"]


def test_sample_n_rows():
    # pandas df.sample(n, random_state=X): Spark no acepta n -> fraction=1.0 + limit(n)
    r = _conv(
        'import pandas as pd\n'
        'df = pd.read_csv("f.csv")\n'
        'x = df.sample(20000, random_state=42)\n'
    )
    assert "df.sample(fraction=1.0, seed=42).limit(20000)" in r["code"]
    assert "random_state" not in r["code"]
    assert any("Spark.sample usa fraccion" in w for w in r["warnings"])


def test_sample_frac():
    # pandas df.sample(frac=..., random_state=X) -> Spark sample(fraction=..., seed=...)
    r = _conv(
        'import pandas as pd\n'
        'df = pd.read_csv("f.csv")\n'
        'x = df.sample(frac=0.1, random_state=7)\n'
    )
    assert "df.sample(fraction=0.1, seed=7)" in r["code"]
    assert ".limit(" not in r["code"]
    assert "random_state" not in r["code"]


def _code_lines(r):
    """Lineas de CODIGO ejecutable del resultado (sin comentarios ni vacias)."""
    return [ln for ln in r["code"].splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")]


def test_loc_index_neutralized():
    # y = y.loc[X.index] usa el indice de fila de pandas: no traducible.
    # Debe neutralizarse a un comentario TODO, NO emitir codigo que rompe.
    r = _conv(
        'import pandas as pd\n'
        'df = pd.read_csv("f.csv")\n'
        'X = df.drop("target", axis=1)\n'
        'y = df["target"]\n'
        'y = y.loc[X.index]\n'
    )
    # el statement roto no debe quedar como codigo ejecutable
    assert not any(".loc[" in ln for ln in _code_lines(r))
    assert "TODO py2spark" in r["code"]         # queda marcado honestamente
    assert any(".loc" in u for u in r["unsupported"])


def test_iloc_neutralized():
    r = _conv(
        'import pandas as pd\n'
        'df = pd.read_csv("f.csv")\n'
        'sub = df.iloc[0:100]\n'
    )
    assert not any(".iloc[" in ln for ln in _code_lines(r))
    assert "TODO py2spark" in r["code"]


def test_reset_index_neutralized():
    r = _conv(
        'import pandas as pd\n'
        'df = pd.read_csv("f.csv")\n'
        'df2 = df.reset_index(drop=True)\n'
    )
    assert not any("reset_index" in ln for ln in _code_lines(r))
    assert "TODO py2spark" in r["code"]


def test_astype_to_cast():
    # col.astype(int) -> col.cast('int'); astype('float64') -> cast('double')
    r = _conv(
        'import pandas as pd\n'
        'df = pd.read_csv("f.csv")\n'
        'df["a"] = df["a"].astype(int)\n'
        'df["b"] = df["b"].astype("float64")\n'
    )
    assert "F.col('a').cast('int')" in r["code"]
    assert "F.col('b').cast('double')" in r["code"]
    assert ".astype(" not in "\n".join(_code_lines(r))


def test_astype_bool_expr():
    # (col == valor).astype(int) -> (col == valor).cast('int')
    r = _conv(
        'import pandas as pd\n'
        'df = pd.read_csv("f.csv")\n'
        'df["flag"] = (df["c"] == ">50K").astype(int)\n'
    )
    assert ".cast('int')" in r["code"]


def test_sklearn_bunch_data_is_dataframe():
    # X = bunch.data -> X = bunch (DataFrame completo)
    r = _conv(
        'import pandas as pd\n'
        'from sklearn.datasets import load_iris\n'
        'iris = load_iris()\n'
        'X = iris.data\n'
    )
    assert "X = iris" in r["code"]
    assert ".data" not in "\n".join(_code_lines(r))


def test_sklearn_bunch_target_neutralized():
    # y = bunch.target -> TODO (no existe en Spark); dependencias posteriores mueren
    r = _conv(
        'import pandas as pd\n'
        'from sklearn.datasets import fetch_openml\n'
        'adult = fetch_openml("adult", as_frame=True)\n'
        'X = adult.data\n'
        'y = adult.target\n'
        'y = (y == ">50K").astype(int)\n'
    )
    lines = _code_lines(r)
    # ni .target ni la reasignacion rota quedan como codigo ejecutable
    assert not any(".target" in ln for ln in lines)
    assert not any("'>50K'" in ln for ln in lines)
    assert "TODO py2spark" in r["code"]
    assert any(".target" in u for u in r["unsupported"])
