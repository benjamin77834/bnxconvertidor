# Ejemplo ML #3 — Random Forest + escalado + one-hot (scikit-learn sobre pandas).
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# --- Preparacion (traducible a PySpark) ---
df = pd.read_parquet("clientes_scoring")
df = df[df["antiguedad_meses"] >= 0]
df["gasto_promedio"] = df["gasto_total"] / (df["num_compras"] + 1)

# one-hot de una categorica (pandas get_dummies -> en Spark: StringIndexer+OneHotEncoder)
df = pd.get_dummies(df, columns=["segmento"])

# escalado de features numericas (sklearn StandardScaler -> Spark: ml.feature.StandardScaler)
num_cols = ["gasto_promedio", "antiguedad_meses", "saldo"]
scaler = StandardScaler()
df[num_cols] = scaler.fit_transform(df[num_cols])

# --- Modelo (requiere MLlib) ---
X = df.drop(columns=["churn", "cliente_id"])
y = df["churn"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25)

rf = RandomForestClassifier(n_estimators=100, max_depth=8)
rf.fit(X_train, y_train)
proba = rf.predict_proba(X_test)
