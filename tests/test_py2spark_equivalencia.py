"""Equivalencia pandas vs PySpark del conversor py2spark.

Cada caso ejecuta el MISMO snippet con pandas (ORACULO, solo en el test) y su version
CONVERTIDA con PySpark en local[2] sobre datos pequenos, y compara el resultado `out`.
Ademas todo el codigo convertido debe estar libre de pandas/toPandas/pandas_udf/udf.

Se desactiva ANSI para igualar la semantica de nulos/division de pandas (null en vez de error).
"""
import ast
import math
import os
import re
import sys

import pytest

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")
pyspark = pytest.importorskip("pyspark")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from py2spark import convert_code  # noqa: E402

EMP = pd.DataFrame({
    "id": [1, 2, 3, 4, 5, 6, 7, 8],
    "dept": ["A", "B", "A", "C", "B", "A", "C", "B"],
    "region": ["N", "N", "S", "S", "N", "S", "N", "S"],
    "salary": [1000.0, 2500.0, 1800.0, 3200.0, 2100.0, 900.0, 4000.0, 2750.0],
    "bonus": [100.0, None, 50.0, None, 75.0, 20.0, 300.0, None],
    "name": [" ana lopez ", "Bob Smith", None, "carla ruiz", "DAVID  gil", "eva ", "Fer Mora", "gus"],
    "hire": ["2020-01-15", "2021-06-30", "2019-12-31", "2022-03-01", "2018-07-04",
             "2023-11-20", "2020-02-29", "2017-05-05"],
    "flag": [True, False, True, True, False, True, False, True],
})
DEPT = pd.DataFrame({"dept": ["A", "B", "D"], "boss": ["x", "y", "z"], "salary": [1, 2, 3]})
SALES = pd.DataFrame({
    "store": ["s1", "s1", "s1", "s2", "s2", "s2"],
    "month": ["jan", "feb", "mar", "jan", "feb", "mar"],
    "units": [10, 20, 30, 5, 15, 25],
    "price": [1.5, 2.5, 3.5, 1.0, 2.0, 3.0],
})


@pytest.fixture(scope="module")
def spark():
    from pyspark.sql import SparkSession
    s = (SparkSession.builder.master("local[2]").appName("py2spark_equiv")
         .config("spark.ui.enabled", "false")
         .config("spark.sql.shuffle.partitions", "2")
         .config("spark.sql.ansi.enabled", "false")
         .config("spark.sql.session.timeZone", "UTC")
         .config("spark.driver.bindAddress", "127.0.0.1")
         .getOrCreate())
    yield s


# ---------------------------------------------------------------------------
_FORBIDDEN = re.compile(r"\bimport\s+pandas\b|\bfrom\s+pandas\b|\bpd\.|\bpandas\b|toPandas|to_pandas|pandas_udf|"
                        r"applyInPandas|mapInPandas|pyspark\.pandas|pandas_api|(?<![\w.])udf\(|@udf|F\.udf|"
                        r"createDataFrame\(\s*pd|\bimport\s+numpy\b|\bnp\.")


def _code_only(code):
    """Codigo sin comentarios (los TODO citan el original pandas a proposito)."""
    return "\n".join(l for l in code.splitlines() if not l.strip().startswith("#"))


def _norm(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    try:
        if v is pd.NA or v is pd.NaT:
            return None
    except Exception:
        pass
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if np.isnan(v) else float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime().replace(tzinfo=None)
    if isinstance(v, (list, tuple, np.ndarray)):
        return [_norm(x) for x in v]
    return v


def _rows(df):
    cols = list(df.columns)
    out = []
    for r in df.itertuples(index=False, name=None):
        out.append(tuple(_norm(x) for x in r))
    return cols, out


def _sortkey(row):
    return tuple((0, "") if x is None else (1, str(x)) for x in row)


def _eq(a, b):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=1e-6, abs_tol=1e-9)
    if hasattr(a, "isoformat") and hasattr(b, "isoformat"):
        return str(a)[:19] == str(b)[:19]
    return str(a) == str(b)


def run_both(spark, tmp_path, src, ordered=False, data=None, extra_ok=None):
    data = data or {"emp": EMP, "dept": DEPT, "sales": SALES}
    paths = {}
    for k, v in data.items():
        p = tmp_path / (k + ".csv")
        v.to_csv(p, index=False)
        paths[k] = str(p)
    code_src = src.format(out_dir=str(tmp_path / "w"), **paths)
    # --- oraculo pandas
    g = {"pd": pd, "np": np}
    exec(code_src, g)
    pout = g["out"]
    if isinstance(pout, pd.Series):
        pout = pout.to_frame()
    pcols, prows = _rows(pout)
    # --- conversion
    r = convert_code(code_src)
    assert r["ok"], r
    code = r["code"]
    assert not r["unsupported"], r["unsupported"]
    assert not re.search(r"^\s*# TODO py2spark", code, re.M), code
    ast.parse(code, feature_version=(3, 8))
    bad = _FORBIDDEN.findall(_code_only(code))
    assert not bad, (bad, code)
    ns = {}
    exec(code, ns)
    sout = ns["out"]
    if hasattr(sout, "toPandas"):
        sp = sout.toPandas()              # solo en el TEST (oraculo), no en el codigo convertido
        scols, srows = _rows(sp)
    else:
        raise AssertionError("out no es DataFrame de Spark: %r" % (sout,))
    assert scols == pcols, (scols, pcols, code)
    assert len(srows) == len(prows), (len(srows), len(prows), code)
    if not ordered:
        srows = sorted(srows, key=_sortkey)
        prows = sorted(prows, key=_sortkey)
    for i, (a, b) in enumerate(zip(prows, srows)):
        assert all(_eq(x, y) for x, y in zip(a, b)), "fila %d pandas=%r spark=%r\n%s" % (i, a, b, code)
    return code


HEAD = 'import pandas as pd\nimport numpy as np\nemp = pd.read_csv("{emp}")\n'

# (id, snippet, ordered)
CASES = [
    ("fillna_scalar", 'emp["bonus"] = emp["bonus"].fillna(0)\nout = emp[["id", "bonus"]]\n', False),
    ("fillna_mean", 'emp["bonus"] = emp["bonus"].fillna(emp["bonus"].mean())\nout = emp[["id", "bonus"]]\n', False),
    ("isna_notna", 'out = emp[emp["bonus"].isna()]\nout = out[["id", "bonus"]]\n', False),
    ("notna_filter", 'out = emp[emp["bonus"].notna() & (emp["salary"] > 1000)][["id"]]\n', False),
    ("isin_between", 'out = emp[emp["dept"].isin(["A", "B"]) & emp["salary"].between(1000, 2600)]\n', False),
    ("str_basic", 'emp["u"] = emp["name"].str.upper()\nemp["s"] = emp["name"].str.strip()\n'
                  'emp["n"] = emp["name"].str.len()\nout = emp[["id", "u", "s", "n"]]\n', False),
    ("str_contains_replace", 'emp = emp[emp["name"].notna()]\nemp["c"] = emp["name"].str.contains("a")\n'
                             'emp["r"] = emp["name"].str.replace("a", "X", regex=False)\n'
                             'emp["st"] = emp["name"].str.startswith("Bob")\nout = emp[["id", "c", "r", "st"]]\n', False),
    ("str_slice_split", 'emp["p3"] = emp["dept"].str.zfill(3)\nemp["f"] = emp["name"].str.strip().str.split(" ").str[0]\n'
                        'emp["h"] = emp["hire"].str[:4]\nout = emp[["id", "p3", "f", "h"]]\n', False),
    ("dt_parts", 'emp["d"] = pd.to_datetime(emp["hire"])\nemp["y"] = emp["d"].dt.year\nemp["m"] = emp["d"].dt.month\n'
                 'emp["dw"] = emp["d"].dt.dayofweek\nemp["fmt"] = emp["d"].dt.strftime("%Y/%m/%d")\n'
                 'out = emp[["id", "y", "m", "dw", "fmt"]]\n', False),
    ("np_where_select", 'emp["w"] = np.where(emp["salary"] > 2000, "alto", "bajo")\n'
                        'emp["sel"] = np.select([emp["salary"] < 1500, emp["salary"] < 3000], ["l", "m"], default="h")\n'
                        'out = emp[["id", "w", "sel"]]\n', False),
    ("np_math", 'emp["lg"] = np.log(emp["salary"])\nemp["sq"] = np.sqrt(emp["salary"])\n'
                'emp["ab"] = np.abs(emp["bonus"] - 60)\nout = emp[["id", "lg", "sq", "ab"]]\n', False),
    ("round_half_even", 'emp["r"] = (emp["id"] - 0.5).round(0)\nemp["r2"] = np.round(emp["salary"] / 7, 2)\n'
                        'out = emp[["id", "r", "r2"]]\n', False),
    ("clip_where_mask", 'emp["c"] = emp["salary"].clip(1000, 3000)\nemp["w"] = emp["salary"].where(emp["salary"] > 2000)\n'
                        'emp["m"] = emp["salary"].mask(emp["salary"] > 2000, 0)\nout = emp[["id", "c", "w", "m"]]\n', False),
    ("np_nan_replace", 'emp["b"] = emp["bonus"].replace(50.0, np.nan)\nout = emp[["id", "b"]]\n', False),
    ("groupby_agg_dict", 'out = emp.groupby("dept").agg({{"salary": "sum", "bonus": "mean"}}).reset_index()\n', False),
    ("groupby_named_agg", 'out = emp.groupby(["dept", "region"]).agg(total=("salary", "sum"), n=("id", "count"), '
                          'mx=("salary", "max")).reset_index()\n', False),
    ("groupby_sel_sum", 'out = emp.groupby("dept")["salary"].sum().reset_index()\n', False),
    ("groupby_sel_rename", 'out = emp.groupby("dept")["salary"].mean().reset_index(name="avg_sal")\n', False),
    ("groupby_size", 'out = emp.groupby("dept").size().reset_index(name="n")\n', False),
    ("groupby_count_nonnull", 'out = emp.groupby("dept")["bonus"].count().reset_index()\n', False),
    ("groupby_bare_mean", 'out = emp[["dept", "salary", "bonus"]].groupby("dept").mean().reset_index()\n', False),
    ("groupby_agg_list", 'out = emp.groupby("dept")["salary"].agg(["min", "max"]).reset_index()\n', False),
    ("groupby_nunique_std", 'out = emp.groupby("region").agg(nd=("dept", "nunique"), sd=("salary", "std")).reset_index()\n', False),
    ("groupby_var_alias", 'g = emp.groupby("dept")\nout = g["salary"].max().reset_index()\n', False),
    ("transform_mean", 'emp["m"] = emp.groupby("dept")["salary"].transform("mean")\nout = emp[["id", "m"]]\n', False),
    ("transform_lambda_z", 'emp["z"] = emp.groupby("dept")["salary"].transform(lambda x: (x - x.mean()) / x.std())\n'
                           'out = emp[["id", "z"]]\n', False),
    ("groupby_cumsum_shift", 'emp["cs"] = emp.groupby("dept")["salary"].cumsum()\n'
                             'emp["sh"] = emp.groupby("dept")["salary"].shift(1)\nout = emp[["id", "cs", "sh"]]\n', False),
    ("groupby_rank", 'emp["rk"] = emp.groupby("dept")["salary"].rank(ascending=False, method="min")\n'
                     'out = emp[["id", "rk"]]\n', False),
    ("merge_on_suffixes", 'dept = pd.read_csv("{dept}")\nout = emp.merge(dept, on="dept", how="left")\n'
                          'out = out[["id", "dept", "salary_x", "salary_y", "boss"]]\n', False),
    ("merge_inner_explicit_suffix", 'dept = pd.read_csv("{dept}")\n'
                                    'out = emp.merge(dept, on="dept", suffixes=("_emp", "_dept"))\n'
                                    'out = out[["id", "salary_emp", "salary_dept"]]\n', False),
    ("merge_left_on_right_on", 'dept = pd.read_csv("{dept}").rename(columns={{"dept": "d2"}})\n'
                               'out = emp.merge(dept, left_on="dept", right_on="d2", how="inner")\n'
                               'out = out[["id", "d2", "boss"]]\n', False),
    ("merge_outer", 'dept = pd.read_csv("{dept}")\nout = emp[["dept", "id"]].merge(dept[["dept", "boss"]], on="dept", how="outer")\n', False),
    ("pd_merge_func", 'dept = pd.read_csv("{dept}")\nout = pd.merge(emp[["id", "dept"]], dept[["dept", "boss"]], on="dept")\n', False),
    ("pivot_table", 'sales = pd.read_csv("{sales}")\nout = sales.pivot_table(index="store", columns="month", values="units", '
                    'aggfunc="sum").reset_index()\n', False),
    ("pivot_table_fill", 'sales = pd.read_csv("{sales}")\nout = sales.pivot_table(index="store", columns="month", '
                         'values="price", aggfunc="mean", fill_value=0).reset_index()\n', False),
    ("melt", 'sales = pd.read_csv("{sales}")\nout = sales[["store", "month", "units"]].melt(id_vars=["store"], '
             'value_vars=["units"], var_name="k", value_name="v")\n', False),
    ("apply_lambda_ifelse", 'emp["lvl"] = emp["salary"].apply(lambda x: "alto" if x > 2000 else "bajo")\n'
                            'out = emp[["id", "lvl"]]\n', False),
    ("apply_lambda_arith", 'emp["x2"] = emp["salary"].apply(lambda v: v * 2 + 1)\nout = emp[["id", "x2"]]\n', False),
    ("map_dict", 'emp["rn"] = emp["region"].map({{"N": "Norte", "S": "Sur"}})\nout = emp[["id", "rn"]]\n', False),
    ("apply_def_if_chain", 'def seg(x):\n    if x < 1500:\n        return "bajo"\n    elif x < 3000:\n        return "medio"\n'
                           '    return "alto"\nemp["seg"] = emp["salary"].apply(seg)\nout = emp[["id", "seg"]]\n', False),
    ("apply_row_axis1", 'emp["tot"] = emp.apply(lambda r: r["salary"] + r["id"], axis=1)\nout = emp[["id", "tot"]]\n', False),
    ("apply_np_func", 'emp["l"] = emp["salary"].apply(np.log)\nout = emp[["id", "l"]]\n', False),
    ("cut_labels", 'emp["b"] = pd.cut(emp["salary"], bins=[0, 1500, 3000, 10000], labels=["bajo", "medio", "alto"])\n'
                   'out = emp[["id", "b"]]\n', False),
    ("cut_right_false", 'emp["b"] = pd.cut(emp["salary"], bins=[0, 1000, 3000, 10000], labels=False, right=False)\n'
                        'out = emp[["id", "b"]]\n', False),
    ("qcut_labels", 'emp["q"] = pd.qcut(emp["salary"], 4, labels=["q1", "q2", "q3", "q4"])\nout = emp[["id", "q"]]\n', False),
    ("shift_diff_pct", 'emp["s"] = emp["salary"].shift(1)\nemp["d"] = emp["salary"].diff()\n'
                       'emp["p"] = emp["salary"].pct_change()\nout = emp[["id", "s", "d", "p"]]\n', False),
    ("cumsum_rank", 'emp["c"] = emp["salary"].cumsum()\nemp["rk"] = emp["salary"].rank()\n'
                    'emp["rd"] = emp["dept"].rank(method="dense")\nout = emp[["id", "c", "rk", "rd"]]\n', False),
    ("rolling_mean", 'emp["rm"] = emp["salary"].rolling(3).mean()\nemp["rs"] = emp["salary"].rolling(2, min_periods=1).sum()\n'
                     'out = emp[["id", "rm", "rs"]]\n', False),
    ("ffill", 'emp["f"] = emp["bonus"].ffill()\nout = emp[["id", "f"]]\n', False),
    ("sort_multi", 'out = emp.sort_values(["dept", "salary"], ascending=[True, False])[["id", "dept", "salary"]]\n', True),
    ("sort_na_last", 'out = emp.sort_values("bonus")[["id", "bonus"]]\n', True),
    ("sort_desc_head", 'out = emp.sort_values("salary", ascending=False).head(3)[["id", "salary"]]\n', True),
    ("nlargest", 'out = emp.nlargest(3, "salary")[["id", "salary"]]\n', True),
    ("tail", 'out = emp.tail(3)[["id"]]\n', True),
    ("drop_duplicates", 'out = emp[["dept", "region"]].drop_duplicates()\n', False),
    ("value_counts", 'out = emp["dept"].value_counts().reset_index()\nout = out.sort_values(["count", "dept"], ascending=[False, True])\n', True),
    ("unique_nunique", 'out = emp[["dept"]].drop_duplicates()\nn = emp["dept"].nunique()\n', False),
    ("loc_filter_cols", 'out = emp.loc[emp["salary"] > 2000, ["id", "salary"]]\n', False),
    ("loc_assign", 'emp.loc[emp["salary"] > 2000, "region"] = "X"\nout = emp[["id", "region"]]\n', False),
    ("iloc_head", 'out = emp.sort_values("id").iloc[:3][["id"]]\n', True),
    ("columns_rename_drop", 'out = emp.rename(columns={{"salary": "sal"}}).drop(columns=["name", "hire", "flag"])\n', False),
    ("columns_assign", 'out = emp[["id", "dept"]]\nout.columns = ["a", "b"]\n', False),
    ("astype_dict", 'out = emp[["id", "salary"]].astype({{"id": "float", "salary": "int"}})\n', False),
    ("assign_query", 'out = emp.assign(dbl=lambda d: d["salary"] * 2).query("salary > 2000")[["id", "dbl"]]\n', False),
    ("concat_rows", 'out = pd.concat([emp[["id", "dept"]], emp[["id", "dept"]]], ignore_index=True)\n', False),
    ("dropna_inplace", 'x = emp[["id", "bonus"]]\nx.dropna(inplace=True)\nout = x\n', False),
    ("dropna_subset", 'out = emp.dropna(subset=["bonus"])[["id", "bonus"]]\n', False),
    ("augassign", 'emp["salary"] += 100\nout = emp[["id", "salary"]]\n', False),
    ("readcsv_usecols_nrows", 'e2 = pd.read_csv("{emp}", usecols=["id", "dept"], nrows=3)\nout = e2.sort_values("id")\n', True),
    ("to_numeric_astype", 'emp["i"] = pd.to_numeric(emp["salary"]).astype(int)\nout = emp[["id", "i"]]\n', False),
    ("bool_sum_groupby", 'emp["f2"] = emp["flag"].astype(int)\nout = emp.groupby("dept").agg({{"f2": "sum"}}).reset_index()\n', False),
    ("scalar_mean_filter", 'm = emp["salary"].mean()\nout = emp[emp["salary"] > m][["id"]]\n', False),
]


@pytest.mark.parametrize("cid,body,ordered", CASES, ids=[c[0] for c in CASES])
def test_equivalencia(spark, tmp_path, cid, body, ordered):
    run_both(spark, tmp_path, HEAD + body, ordered=ordered)


def test_scalar_reduction_uses_agg_first_not_collect(spark, tmp_path):
    code = run_both(spark, tmp_path, HEAD + 'm = emp["salary"].mean()\nout = emp[emp["salary"] > m][["id"]]\n')
    assert ".agg(" in code and ".first()" in code
    assert "collect(" not in code and "toPandas" not in code


def test_untranslatable_is_todo_with_original_and_alternative():
    src = ('import pandas as pd\n'
           'df = pd.read_csv("f.csv")\n'
           'df["x"] = df["a"].apply(lambda v: my_external_lib(v))\n')
    r = convert_code(src)
    assert r["unsupported"]
    assert "# TODO py2spark" in r["code"]
    assert "Original:" in r["code"] and "my_external_lib" in r["code"]
    assert "Alternativa" in r["code"]
    assert "udf" not in _code_only(r["code"]).lower()


def test_untranslatable_never_leaves_pandas():
    src = ('import pandas as pd\nimport numpy as np\n'
           'df = pd.read_csv("f.csv")\n'
           'df["x"] = df["a"].apply(lambda v: np.polyval([1, 2], v))\n'
           'v = df["a"].tolist()\n'
           'df2 = df.groupby("k").apply(lambda g: g.head(1))\n')
    r = convert_code(src)
    assert _FORBIDDEN.search(_code_only(r["code"])) is None, r["code"]
    assert len(r["unsupported"]) >= 3


def test_real_world_like_pipeline_no_pandas_left(spark, tmp_path):
    code = run_both(spark, tmp_path, HEAD +
                    'dept = pd.read_csv("{dept}")\n'
                    'emp["bonus"] = emp["bonus"].fillna(0)\n'
                    'emp["total"] = emp["salary"] + emp["bonus"]\n'
                    'emp = emp[emp["flag"] == True]\n'
                    'j = emp.merge(dept[["dept", "boss"]], on="dept", how="left")\n'
                    'out = j.groupby("boss", dropna=False).agg(n=("id", "count"), tot=("total", "sum")).reset_index()\n')
    assert "toPandas" not in code
