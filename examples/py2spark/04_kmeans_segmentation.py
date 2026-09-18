# Ejemplo ML #4 — Segmentacion de clientes con KMeans (scikit-learn sobre pandas).
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# --- Preparacion (traducible) ---
df = pd.read_csv("clientes.csv")
df = df[df["saldo"] >= 0]
df["ingreso_mensual"] = df["ingreso_anual"] / 12
rfm = df.groupby("cliente_id").agg({
    "saldo": "mean",
    "num_transacciones": "sum",
    "ingreso_mensual": "max",
})

# --- Escalado + clustering (requiere MLlib) ---
scaler = StandardScaler()
X = scaler.fit_transform(rfm)

km = KMeans(n_clusters=5, random_state=0)
rfm["segmento"] = km.fit_predict(X)

rfm.to_csv("segmentos_cliente.csv")
