# ============================================================
# BNX ejemplo: dos archivos -> Sort -> Join -> Output File
# Replica el patron del grafo A_DRI_ECMS_AMBS_IMR_D (banco):
#   ECMS_AMBS_D  -> Sort   \
#                            Join -> Output File
#   ECMS_AMBSX_D -> Sort_1 /
# ============================================================

# --- SOURCES (dos archivos de entrada) ---
NODE ECMS_AMBS_D   : SOURCE
NODE ECMS_AMBSX_D  : SOURCE

# --- SORT (ordenar cada entrada por la llave del join) ---
NODE Sort          : TRANSFORM
NODE Sort_1        : TRANSFORM

# --- JOIN (une las dos entradas por V_ACCT; MIS_DATE) ---
NODE Join          : JOIN

# --- SINK (archivo de salida) ---
NODE Output_File   : SINK

# ============================================================
# EDGES
# ============================================================
ECMS_AMBS_D   -> Sort
ECMS_AMBSX_D  -> Sort_1
Sort          -> Join
Sort_1        -> Join
Join          -> Output_File
