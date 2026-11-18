"""Runner de los pasos de tipo 'sql' del orquestador (python -m src.orq_sql ...).

Lo lanza orquestador.build_command como argv (sin shell). Nunca recibe contrasenas: solo el
NOMBRE de la variable de entorno (--password-env) que las contiene, y lo mismo vale para
cualquier ${PARAM} de nombre secreto (pass/pwd/secret/token/key): se expanden aqui desde el
entorno y se enmascaran en lo que se imprime.

Motores:
  spark_sql  spark.sql(...) en un SparkSession local (BNX_SQL_MASTER, defecto local[*]).
  jdbc       java.sql.DriverManager via la JVM de PySpark (--jar en el classpath del driver) o
             jaydebeapi si esta instalado. Sirve para DML/DDL/CALL/NEXTVAL contra cualquier BD.
  beeline    Hive/Spark Thrift (beeline -u URL --hivevar ...); la clave va en un archivo 0600.
  bteq       Teradata BTEQ (host en --url; la clave por stdin).
  sqlplus    Oracle SQL*Plus (conexion host:puerto/servicio en --url; la clave por stdin).
Compatible con Python 3.8.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

_REF = re.compile(r"\$\{([A-Za-z_]\w*)\}")
_SECRETO = re.compile(r"pass|pwd|secret|token|key|credential", re.I)
MOTORES = ("spark_sql", "jdbc", "beeline", "bteq", "sqlplus")


def expandir(texto, env=None, mascara=False):
    """${NOMBRE} -> valor del entorno. Con mascara=True los nombres secretos salen como ****.
    SystemExit si falta alguno."""
    env = os.environ if env is None else env
    faltan = []

    def r(m):
        n = m.group(1)
        if n not in env:
            faltan.append(n)
            return m.group(0)
        return "****" if (mascara and _SECRETO.search(n)) else str(env[n])
    out = _REF.sub(r, texto)
    if faltan:
        raise SystemExit("[x] parametros sin valor (defina %s como parametro del pset/plan o variable de entorno)"
                         % ", ".join(sorted(set(faltan))))
    return out


def dividir(sql):
    """Sentencias separadas por ';' fuera de comillas y comentarios."""
    out, buf, i, n = [], [], 0, len(sql)
    while i < n:
        c = sql[i]
        if c in ("'", '"', "`"):
            j = i + 1
            while j < n:
                if sql[j] == c:
                    if j + 1 < n and sql[j + 1] == c:   # comilla doblada
                        j += 2
                        continue
                    break
                j += 1
            buf.append(sql[i:j + 1])
            i = j + 1
        elif sql.startswith("--", i):
            j = sql.find("\n", i)
            j = n if j < 0 else j
            buf.append(sql[i:j])
            i = j
        elif sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            j = n if j < 0 else j + 2
            buf.append(sql[i:j])
            i = j
        elif c == ";":
            s = "".join(buf).strip()
            if _con_codigo(s):
                out.append(s)
            buf, i = [], i + 1
        else:
            buf.append(c)
            i += 1
    s = "".join(buf).strip()
    if _con_codigo(s):
        out.append(s)
    return out


def _con_codigo(s):
    """False si solo hay comentarios/espacios."""
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"--[^\n]*", "", s)
    return bool(s.strip())


def _es_consulta(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"--[^\n]*", "", s).lstrip().lower()
    return bool(re.match(r"(select|with|show|describe|desc|explain|values|table)\b", s))


def _clave(nombre_env):
    if not nombre_env:
        return None
    v = os.environ.get(nombre_env)
    if v is None:
        raise SystemExit("[x] falta la variable de entorno %s (contrasena del paso)" % nombre_env)
    return v


def _spark(jar=None):
    from pyspark.sql import SparkSession
    b = (SparkSession.builder.master(os.environ.get("BNX_SQL_MASTER", "local[*]"))
         .appName("bnx_sql").config("spark.ui.enabled", "false"))
    if jar:
        b = b.config("spark.jars", jar).config("spark.driver.extraClassPath", jar)
    s = b.getOrCreate()
    s.sparkContext.setLogLevel("ERROR")
    return s


def run_spark_sql(stmts, mostrar):
    spark = _spark()
    try:
        for s in stmts:
            mostrar(s)
            df = spark.sql(s)
            if _es_consulta(s):
                df.show(50, truncate=False)
    finally:
        spark.stop()
    return 0


def run_jdbc(a, stmts, mostrar):
    pw = _clave(a.password_env)
    try:
        import jaydebeapi  # opcional
    except ImportError:
        jaydebeapi = None
    if jaydebeapi is not None and a.driver:
        con = jaydebeapi.connect(a.driver, a.url, [a.usuario, pw] if a.usuario else [],
                                 a.jar or None)
        try:
            cur = con.cursor()
            for s in stmts:
                mostrar(s)
                cur.execute(s)
                if cur.description:
                    for r in cur.fetchmany(50):
                        print("  ", r)
                else:
                    print("   filas afectadas:", cur.rowcount)
            con.commit()
        finally:
            con.close()
        return 0
    spark = _spark(a.jar)
    try:
        jvm = spark._sc._gateway.jvm
        if a.driver:
            jvm.java.lang.Class.forName(a.driver)
        props = jvm.java.util.Properties()
        if a.usuario:
            props.setProperty("user", a.usuario)
        if pw is not None:
            props.setProperty("password", pw)
        con = jvm.java.sql.DriverManager.getConnection(a.url, props)
        try:
            st = con.createStatement()
            for s in stmts:
                mostrar(s)
                if st.execute(s):
                    rs = st.getResultSet()
                    n = rs.getMetaData().getColumnCount()
                    k = 0
                    while rs.next() and k < 50:
                        print("  ", tuple(str(rs.getString(i + 1)) for i in range(n)))
                        k += 1
                    rs.close()
                else:
                    print("   filas afectadas:", st.getUpdateCount())
        finally:
            con.close()
    finally:
        spark.stop()
    return 0


def _archivo_privado(texto):
    fd, p = tempfile.mkstemp(prefix="bnx_sql_")
    with os.fdopen(fd, "w") as f:
        f.write(texto)
    os.chmod(p, 0o600)
    return p


def run_beeline(a, stmts, mostrar):
    pw = _clave(a.password_env)
    tmp = []
    try:
        script = ";\n".join(stmts) + ";\n"
        for s in stmts:
            mostrar(s)
        sf = _archivo_privado(script)
        tmp.append(sf)
        cmd = ["beeline", "-u", a.url, "--silent=true", "--showHeader=true"]
        if a.usuario:
            cmd += ["-n", a.usuario]
        if pw is not None:
            pf = _archivo_privado(pw)
            tmp.append(pf)
            cmd += ["-w", pf]
        for hv in a.hivevar or []:
            cmd += ["--hivevar", hv]
        cmd += ["-f", sf]
        return subprocess.call(cmd)
    except OSError as e:
        raise SystemExit("[x] no se pudo lanzar beeline: %s" % e)
    finally:
        for p in tmp:
            try:
                os.remove(p)
            except OSError:
                pass


def _por_stdin(cmd, texto):
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, universal_newlines=True)
    except OSError as e:
        raise SystemExit("[x] no se pudo lanzar %s: %s" % (cmd[0], e))
    p.communicate(texto)
    return p.returncode


def run_bteq(a, stmts, mostrar):
    pw = _clave(a.password_env)
    L = [".LOGON %s/%s,%s" % (a.url, a.usuario or "", pw or ""), ".IF ERRORCODE <> 0 THEN .QUIT 8"]
    for s in stmts:
        mostrar(s)
        L += [s + ";", ".IF ERRORCODE <> 0 THEN .QUIT 8"]
    L += [".LOGOFF", ".QUIT 0"]
    return _por_stdin(["bteq"], "\n".join(L) + "\n")


def run_sqlplus(a, stmts, mostrar):
    pw = _clave(a.password_env)
    L = [pw or "", "WHENEVER SQLERROR EXIT SQL.SQLCODE", "WHENEVER OSERROR EXIT FAILURE", "SET ECHO OFF"]
    for s in stmts:
        mostrar(s)
        L.append(s + ";")
    L += ["COMMIT;", "EXIT;"]
    cred = "%s@%s" % (a.usuario, a.url) if a.usuario else a.url
    return _por_stdin(["sqlplus", "-S", "-L", cred], "\n".join(L) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m src.orq_sql")
    ap.add_argument("--motor", required=True, choices=MOTORES)
    ap.add_argument("--sentencia", required=True)
    ap.add_argument("--url")
    ap.add_argument("--driver")
    ap.add_argument("--jar")
    ap.add_argument("--usuario")
    ap.add_argument("--password-env", dest="password_env")
    ap.add_argument("--hivevar", action="append")
    a = ap.parse_args(argv)
    texto = expandir(a.sentencia)
    stmts = dividir(texto)
    if not stmts:
        raise SystemExit("[x] la sentencia SQL esta vacia")
    visible = dividir(expandir(a.sentencia, mascara=True))
    it = iter(visible)

    def mostrar(_s):
        print("[sql/%s] %s" % (a.motor, next(it, "")), flush=True)
    if a.motor != "spark_sql" and not a.url:
        raise SystemExit("[x] --url es obligatorio para el motor %s" % a.motor)
    f = {"spark_sql": lambda: run_spark_sql(stmts, mostrar),
         "jdbc": lambda: run_jdbc(a, stmts, mostrar),
         "beeline": lambda: run_beeline(a, stmts, mostrar),
         "bteq": lambda: run_bteq(a, stmts, mostrar),
         "sqlplus": lambda: run_sqlplus(a, stmts, mostrar)}[a.motor]
    rc = f()
    print("[sql] terminado (codigo %s)" % rc, flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
