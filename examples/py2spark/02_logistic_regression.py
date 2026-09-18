# Ejemplo ML #2 — Regresion logistica (scikit-learn sobre pandas).
# La preparacion de datos (pandas) SE TRADUCE a PySpark; el entrenamiento
# sklearn NO tiene equivalente 1:1 -> py2spark lo marca con TODO sugiriendo
# el equivalente en Spark MLlib (pyspark.ml.classification.LogisticRegression).
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

# --- Preparacion de datos (traducible) ---
df = pd.read_csv("prestamos.csv")
df = df[df["ingreso"] > 0]
df["ratio_deuda"] = df["deuda"] / df["ingreso"]
df = df.dropna()

# --- Split y entrenamiento (sklearn: requiere MLlib en Spark) ---
X = df[["ingreso", "deuda", "ratio_deuda", "edad"]]
y = df["default"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

pred = model.predict(X_test)
score = model.score(X_test, y_test)
print("accuracy:", score)
