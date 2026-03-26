# dag_graphviz.py
from graphviz import Digraph

dot = Digraph('BNX_GlueJob_V54', format='png')
dot.attr(rankdir='LR', size='10')

# -------------------------
# Nodos XFR (raw)
# -------------------------
xfr_nodes = [
    'RawCustomers',
    'RawOrders',
    'RawTransactions',
    'RawProducts',
    'RawSuppliers',
    'RawRegions',
    'RawPromotions'
]

for n in xfr_nodes:
    dot.node(n, n, shape='box', style='filled', color='lightblue')

# -------------------------
# Nodos DML (clean, join, agg)
# -------------------------
dml_nodes = [
    'CleanCustomers',
    'CleanOrders',
    'JoinOrdersProducts',
    'AggProductSales',
    'JoinCustomersTransactions',
    'AggCustomerOrders',
    'JoinProductsSuppliers',
    'AggSupplierProducts',
    'JoinOrdersRegions',
    'AggRegionOrders',
    'JoinPromotionsOrders',
    'AggPromoOrders',
    'MasterReport'
]

for n in dml_nodes:
    dot.node(n, n, shape='ellipse', style='filled', color='lightgreen')

# -------------------------
# Conexiones típicas ETL
# -------------------------

# Raw -> Clean
dot.edge('RawCustomers', 'CleanCustomers')
dot.edge('RawOrders', 'CleanOrders')
dot.edge('RawTransactions', 'JoinCustomersTransactions')
dot.edge('RawProducts', 'JoinOrdersProducts')
dot.edge('RawSuppliers', 'JoinProductsSuppliers')
dot.edge('RawRegions', 'JoinOrdersRegions')
dot.edge('RawPromotions', 'JoinPromotionsOrders')

# Clean -> Join / Agg
dot.edge('CleanOrders', 'JoinOrdersProducts')
dot.edge('CleanCustomers', 'JoinCustomersTransactions')

# Joins -> Aggs
dot.edge('JoinOrdersProducts', 'AggProductSales')
dot.edge('JoinCustomersTransactions', 'AggCustomerOrders')
dot.edge('JoinProductsSuppliers', 'AggSupplierProducts')
dot.edge('JoinOrdersRegions', 'AggRegionOrders')
dot.edge('JoinPromotionsOrders', 'AggPromoOrders')

# Aggs -> MasterReport
agg_nodes = [
    'AggProductSales',
    'AggCustomerOrders',
    'AggSupplierProducts',
    'AggRegionOrders',
    'AggPromoOrders'
]
for n in agg_nodes:
    dot.edge(n, 'MasterReport')

# -------------------------
# Guardar gráfico
# -------------------------
dot.render('BNX_GlueJob_V54_DAG', view=True)
print("✅ DAG generado: BNX_GlueJob_V54_DAG.png")
