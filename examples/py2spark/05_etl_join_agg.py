# Ejemplo ML #5 — ETL de features multi-tabla (pandas puro, 100% traducible).
# Ideal para probar el flujo completo con Data Redactada (todo se ejecuta local).
import pandas as pd

ventas = pd.read_csv("ventas.csv")
productos = pd.read_parquet("productos")
tiendas = pd.read_parquet("tiendas")

# Filtros de calidad
ventas = ventas[ventas["cantidad"] > 0]
ventas = ventas[ventas["precio_unitario"] > 0]

# Feature: importe de linea
ventas["importe"] = ventas["cantidad"] * ventas["precio_unitario"]

# Enriquecer con producto y tienda
v = ventas.merge(productos, on="producto_id", how="left")
v = v.merge(tiendas, on="tienda_id", how="left")

# Agregado por categoria y region
resumen = v.groupby("categoria").agg({
    "importe": "sum",
    "cantidad": "sum",
})
resumen = resumen.sort_values("importe", ascending=False)

resumen.to_parquet("resumen_ventas")
