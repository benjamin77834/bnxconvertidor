#!/usr/bin/env python3
"""Convierte en lote todos los .mp de una carpeta con main.py y resume el resultado.

Uso:
    python scripts/convertir_lote.py <carpeta> [--out output/lote] [--target spark]
                                      [--timeout 900]

El pset de cada grafo lo detecta main.py por la linea !prototype. Genera un
<out>/reporte_lote.md con estado, accuracy y ultimas lineas de error por grafo.
"""
import argparse
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def convertir(mp, out_dir, target, timeout):
    base = os.path.splitext(os.path.basename(mp))[0]
    out_py = os.path.join(out_dir, base + f"_{target}.py")
    t0 = time.time()
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(ROOT, "main.py"), "--project", mp,
             "--output", out_py, "--target", target],
            cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        log, rc = (r.stdout or "") + (r.stderr or ""), r.returncode
    except subprocess.TimeoutExpired as e:
        log, rc = ((e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes)
                   else (e.stdout or "")) + f"\nTIMEOUT {timeout}s", -1
    with open(os.path.join(out_dir, base + ".log"), "w", encoding="utf-8") as f:
        f.write(log)
    m = re.search(r"Overall:\s*([\d.]+)%", log)
    n = re.search(r"Nodes:\s*(\d+)/(\d+)", log)
    pset = re.search(r"PSET detectado por !prototype: (\S+)", log)
    ok = rc == 0 and os.path.exists(out_py)
    return {"graph": os.path.basename(mp), "ok": ok, "rc": rc,
            "accuracy": m.group(1) if m else "-",
            "nodes": f"{n.group(1)}/{n.group(2)}" if n else "-",
            "pset": pset.group(1) if pset else "(ninguno)",
            "secs": round(time.time() - t0, 1),
            "err": "" if ok else " | ".join(log.strip().splitlines()[-3:])[:300]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", default=os.path.join(ROOT, "output", "lote"))
    ap.add_argument("--target", default="spark")
    ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    mps = sorted(f for f in os.listdir(a.folder) if f.lower().endswith(".mp"))
    rows = []
    for f in mps:
        print(f"[>] {f}", flush=True)
        row = convertir(os.path.join(a.folder, f), a.out, a.target, a.timeout)
        print(f"    ok={row['ok']} acc={row['accuracy']} nodes={row['nodes']} "
              f"pset={row['pset']} {row['secs']}s", flush=True)
        rows.append(row)
    lines = ["# Reporte de conversion en lote", "",
             f"Carpeta: `{os.path.abspath(a.folder)}`  Target: `{a.target}`", "",
             "| Grafo | OK | Accuracy | Nodos | Pset detectado | Seg | Error |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['graph']} | {'si' if r['ok'] else 'NO'} | {r['accuracy']} | {r['nodes']} "
                     f"| {r['pset']} | {r['secs']} | {r['err'].replace('|', '/')} |")
    lines.append(f"\nOK: {sum(r['ok'] for r in rows)}/{len(rows)}")
    with open(os.path.join(a.out, "reporte_lote.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[ok] reporte: {os.path.join(a.out, 'reporte_lote.md')}")

    # Con planes en la carpeta: generar la orquestacion editable sobre lo convertido
    if any(f.lower().endswith(".plan") for f in os.listdir(a.folder)):
        sys.path.insert(0, ROOT)
        from src import orquestador
        for p in orquestador.save_all(orquestador.build(a.folder, a.out), a.out):
            print(f"[ok] orquestacion: {p}")


if __name__ == "__main__":
    main()
