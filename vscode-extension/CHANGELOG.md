# Changelog

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
