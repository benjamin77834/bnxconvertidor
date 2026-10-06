# Drivers JDBC — sección "Datos Remotos"

Estos `.jar` los usa la sección **Datos Remotos** para conectarse por JDBC y traer
datos enmascarados. En la GUI, al elegir la fuente, la ruta del driver se autollena.

## Incluidos (licencia libre, se descargan con el script)

Ejecuta:

```bash
./drivers/download_drivers.sh
```

Descarga:

| Fuente     | Archivo                        | Licencia            |
|------------|--------------------------------|---------------------|
| PostgreSQL | `postgresql.jar`               | BSD-2               |
| MariaDB    | `mariadb-java-client.jar`      | LGPL-2.1            |
| MySQL      | `mysql-connector-j.jar`        | GPL-2 + FOSS except |
| Hive       | `hive-jdbc-standalone.jar`     | Apache-2.0 (~69MB)  |

Los `.jar` NO se versionan en git (están en `.gitignore`): el de Hive pesa ~69MB.

## Propietarios (consíguelos tú y colócalos aquí)

| Fuente   | Archivo             | Dónde                                   |
|----------|---------------------|-----------------------------------------|
| Teradata | `terajdbc4.jar`     | Portal de descargas de Teradata (cuenta)|
| Impala   | `ImpalaJDBC.jar`    | Cloudera (ImpalaJDBC)                    |

Una vez colocados, pon la ruta (p.ej. `drivers/terajdbc4.jar`) en el campo
"Ruta del driver JDBC" de la GUI.
