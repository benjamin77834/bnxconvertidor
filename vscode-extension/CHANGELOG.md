# Changelog

## 0.3.0
- OFFLINE: el motor py2spark ahora corre con el **Python local** del usuario
  (empaquetado en el `.vsix`: carpeta `py2spark/` + `run_py2spark.py`). Ya NO
  llama al endpoint `/py2spark` ni requiere el portal BNX corriendo.
- Requisito: Python 3.8+ instalado. Se usa el intérprete de la extensión oficial
  de Python si está, o `python3`/`python`/`py` del PATH; se puede fijar con la
  config `py2spark.pythonPath`.
- Eliminada la configuración `py2spark.serverUrl` (ya no aplica).
- Misma calidad y resultados que el motor del portal (verificado idéntico).

## 0.2.0
- sklearn `Pipeline` + `ColumnTransformer` ahora se traducen a un
  `pyspark.ml.Pipeline` equivalente y runnable (antes se marcaban como "sin
  equivalente"): `SimpleImputer`→`Imputer`/`fillna`, `StandardScaler`→
  `VectorAssembler`+`StandardScaler`, `OneHotEncoder`→`StringIndexer`+
  `OneHotEncoder`, `ColumnTransformer` aplanado en stages, clasificador MLlib
  con hiperparámetros mapeados, split sobre el DataFrame, evaluación y guardado.
- Si el patrón trae algo no soportado, degrada a `# TODO py2spark` honesto.

## 0.1.0
- Primera versión. Comandos "Convertir selección/archivo a PySpark" que llaman
  al endpoint `/py2spark` del portal BNX (pandas → PySpark 3). Configurable
  `py2spark.serverUrl` y `py2spark.openInNewEditor`.
