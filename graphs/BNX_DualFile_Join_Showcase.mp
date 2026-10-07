# ============================================================
#  ____  _   ___  __    ____  _   _  ___  _    _  ___   __ _ ___  ___
# | __ )| \ | \ \/ /   / ___|| | | |/ _ \| |  | |/ __| / _| / _ \/ __|
# |  _ \|  \| |\  /    \___ \| |_| | | | | |  | | |   | |  | | | \__ \
# | |_) | |\  |/  \     ___) |  _  | |_| | |/\| | |__ | |_ | |_| |__) |
# |____/|_| \_/_/\_\   |____/|_| |_|\___/|_/\/\_|\___| \__| \___/|___/
#
#  BNX SHOWCASE — "Dual-File Join"
#  Patron de referencia del grafo A_DRI_ECMS_AMBS_IMR_D (banco):
#  dos archivos de entrada, cada uno ordenado, unidos por cuenta y escritos.
#
#      ECMS_AMBS_D  ─▶ Sort   ─┐
#                               ├─▶ Join (v_acct, inner) ─▶ Output_File
#      ECMS_AMBSX_D ─▶ Sort_1 ─┘
#
#  Autor: BNX Convertidor  ·  Tipo: ejemplo distintivo (showcase)
# ============================================================

# --- SOURCES (dos archivos de entrada) ---
NODE ECMS_AMBS_D   : SOURCE
NODE ECMS_AMBSX_D  : SOURCE

# --- SORT (ordenar cada entrada por la llave del join) ---
NODE Sort          : TRANSFORM
NODE Sort_1        : TRANSFORM

# --- JOIN (une las dos entradas por V_ACCT) ---
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
