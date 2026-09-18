# Ejemplo ML #1 — Preparacion de features (pandas puro).
# Caso 100% traducible: lectura, filtros, columnas derivadas, agregacion.
import pandas as pd

# Carga del dataset transaccional
tx = pd.read_csv("transacciones.csv")

# Limpieza y filtros
tx = tx[tx["monto"] > 0]
tx = tx[tx["estado"] != "cancelada"]

# Features derivadas
tx["monto_neto"] = tx["monto"] - tx["comision"]
tx["es_alto_valor"] = tx["monto"] > 10000

# Agregacion por cliente (features de comportamiento)
feats = tx.groupby("cliente_id").agg({
    "monto": "sum",
    "monto_neto": "mean",
    "es_alto_valor": "sum",
})

# Enriquecer con datos demograficos
clientes = pd.read_parquet("clientes")
dataset = feats.merge(clientes, on="cliente_id", how="left")

dataset.to_parquet("features_cliente")
