#!/usr/bin/env bash
# Descarga los drivers JDBC de licencia libre usados por la seccion "Datos Remotos".
# Teradata e Impala NO se descargan aqui (licencia propietaria): consíguelos de
# Teradata / Cloudera y coloca el .jar en esta carpeta.
set -e
cd "$(dirname "$0")"

echo "[*] PostgreSQL..."
curl -sSL -o postgresql.jar \
  "https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar"

echo "[*] MariaDB..."
curl -sSL -o mariadb-java-client.jar \
  "https://repo1.maven.org/maven2/org/mariadb/jdbc/mariadb-java-client/3.4.1/mariadb-java-client-3.4.1.jar"

echo "[*] MySQL..."
curl -sSL -o mysql-connector-j.jar \
  "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/9.0.0/mysql-connector-j-9.0.0.jar"

echo "[*] Hive (standalone, ~69MB)..."
curl -sSL -o hive-jdbc-standalone.jar \
  "https://repo1.maven.org/maven2/org/apache/hive/hive-jdbc/3.1.3/hive-jdbc-3.1.3-standalone.jar"

echo "[ok] Drivers descargados en $(pwd)"
echo "    Teradata (terajdbc4.jar) e Impala (ImpalaJDBC.jar): descargarlos manualmente (licencia)."
