#!/usr/bin/env python3
"""Genera un COBOL ENORME (~50k nodos) para estresar la GUI.
Cada FILE -> ~3 nodos; cada PARAGRAPH -> 1 nodo. Para ~50k nodos generamos
muchos párrafos (filtros/computes) + varios archivos."""

N_FILES = 60          # archivos de entrada (cada uno: Raw + Clean = 2 nodos)
N_PARAS = 50000       # párrafos de proceso (1 nodo c/u)

out = []
out.append("       IDENTIFICATION DIVISION.")
out.append("       PROGRAM-ID. MEGA-STRESS-50K.")
out.append("       AUTHOR. BNX-MIGRATION.")
out.append("")
out.append("       ENVIRONMENT DIVISION.")
out.append("       INPUT-OUTPUT SECTION.")
out.append("       FILE-CONTROL.")
for i in range(N_FILES):
    out.append(f"           SELECT FILE{i:03d} ASSIGN TO 'F{i:03d}'")
    out.append("               ORGANIZATION IS SEQUENTIAL.")
out.append("           SELECT REPORT-FILE ASSIGN TO 'RPTFILE'")
out.append("               ORGANIZATION IS SEQUENTIAL.")
out.append("")
out.append("       DATA DIVISION.")
out.append("       FILE SECTION.")
for i in range(N_FILES):
    out.append(f"       FD FILE{i:03d}.")
    out.append(f"       01 REC{i:03d}.")
    out.append(f"           05 F{i:03d}-KEY     PIC 9(10).")
    out.append(f"           05 F{i:03d}-AMOUNT  PIC 9(10)V99.")
    out.append(f"           05 F{i:03d}-NAME    PIC X(30).")
    out.append(f"           05 F{i:03d}-STATUS  PIC X(2).")
out.append("       FD REPORT-FILE.")
out.append("       01 RPT-RECORD.")
out.append("           05 RPT-TOTAL   PIC 9(12)V99.")
out.append("")
out.append("       WORKING-STORAGE SECTION.")
out.append("       01 WS-COUNTERS.")
out.append("           05 WS-TOTAL    PIC 9(12)V99 VALUE 0.")
out.append("           05 WS-COUNT    PIC 9(9) VALUE 0.")
out.append("")
out.append("       PROCEDURE DIVISION.")
out.append("       MAIN-PROCESS.")
# PERFORM de cada parrafo (encadena el flujo)
for i in range(N_PARAS):
    out.append(f"           PERFORM STEP-{i:05d}.")
out.append("           STOP RUN.")
out.append("")
# Definir cada parrafo. Alternamos filtros / aritmetica para variar tipos de nodo.
for i in range(N_PARAS):
    out.append(f"       STEP-{i:05d}.")
    if i % 3 == 0:
        out.append(f"           IF F{(i % N_FILES):03d}-AMOUNT > {100 + i % 900}")
        out.append(f"               ADD F{(i % N_FILES):03d}-AMOUNT TO WS-TOTAL")
        out.append("           END-IF.")
    elif i % 3 == 1:
        out.append(f"           COMPUTE WS-TOTAL = WS-TOTAL + F{(i % N_FILES):03d}-AMOUNT * 2.")
    else:
        out.append(f"           ADD F{(i % N_FILES):03d}-AMOUNT TO WS-TOTAL.")

path = "bnx_library/COBOL_Samples/mega_stress_50k.cbl"
with open(path, "w") as f:
    f.write("\n".join(out) + "\n")
print(f"generado {path}: {len(out)} lineas")
