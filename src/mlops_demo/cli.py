# -*- coding: utf-8 -*-
"""Shim de los CLI del cluster (hdfs, hadoop fs, beeline, impala-shell...) para el DEMO.
Se emulan localmente sobre demo_out/; el resto de comandos externos se simulan (rc 0, sin salida)."""
import io
import os
import shlex
import shutil
import subprocess
import sys
import time

from . import rutas
from .estado import E, log

HDFS = ("hdfs", "hadoop")
OTROS = ("beeline", "impala-shell", "hive", "kinit", "klist", "kdestroy", "sqoop", "distcp", "yarn",
         "mapred", "oozie", "hbase", "spark-sql")
_OPERADORES = ("|", "&&", "||", ";", ">", ">>", "2>&1", "<")
_HELPER = ("import sys;sys.stdout.buffer.write(bytes.fromhex(sys.argv[1]));sys.stdout.flush();"
           "sys.stderr.buffer.write(bytes.fromhex(sys.argv[2]));sys.stderr.flush();sys.exit(int(sys.argv[3]))")


def _prog(argv):
    p = os.path.basename(argv[0]).lower() if argv else ""
    for ext in (".cmd", ".exe", ".sh", ".bat"):
        if p.endswith(ext):
            p = p[:-len(ext)]
    return p


def _r(p):
    """Ruta de HDFS -> local (todo lo absoluto o con esquema es del cluster)."""
    if p.startswith("/") or rutas._esquema(p):
        return rutas.ruta_demo(p)
    return p


def _hdfs_ls(args):
    rec = any(a in ("-R",) for a in args)
    paths = [a for a in args if not a.startswith("-")]
    out, err, rc = [], [], 0
    for orig in paths:
        loc = _r(orig)
        if not os.path.exists(loc):
            err.append("ls: `%s': No such file or directory" % orig)
            rc = 1
            continue
        items = []
        if os.path.isdir(loc):
            if rec:
                for r, ds, fs in os.walk(loc):
                    for n in sorted(ds + fs):
                        items.append(os.path.join(r, n))
            else:
                items = [os.path.join(loc, n) for n in sorted(os.listdir(loc))]
            out.append("Found %d items" % len(items))
        else:
            items = [loc]
        for it in items:
            if it == loc:
                nombre = orig
            else:
                nombre = orig.rstrip("/") + "/" + os.path.relpath(it, loc).replace(os.sep, "/")
            st = os.stat(it)
            d = os.path.isdir(it)
            out.append("%s   %s mlops hdfs %10d %s %s" % (
                "drwxr-xr-x" if d else "-rw-r--r--", "-" if d else "3", 0 if d else st.st_size,
                time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)), nombre))
    return "\n".join(out) + ("\n" if out else ""), "\n".join(err) + ("\n" if err else ""), rc


def _hdfs(args):
    """args = lo que sigue a 'hdfs dfs' / 'hadoop fs'. Devuelve (stdout, stderr, rc) o None si no se sabe."""
    if not args:
        return None
    sub = args[0].lstrip("-").lower()
    rest = args[1:]
    flags = [a for a in rest if a.startswith("-") and len(a) > 1]
    pos = [a for a in rest if not (a.startswith("-") and len(a) > 1)]
    if sub == "ls":
        return _hdfs_ls(rest)
    if sub == "test":
        if not pos:
            return "", "test: missing path\n", 1
        loc = _r(pos[-1])
        modo = flags[0] if flags else "-e"
        ok = os.path.isdir(loc) if modo == "-d" else (os.path.isfile(loc) if modo == "-f" else
             (os.path.exists(loc) and os.path.getsize(loc) == 0 if modo == "-z" else os.path.exists(loc)))
        return "", "", 0 if ok else 1
    if sub == "mkdir":
        for p in pos:
            os.makedirs(_r(p), exist_ok=True)
        return "", "", 0
    if sub in ("rm", "rmr", "rmdir"):
        rc, err = 0, ""
        for p in pos:
            loc = _r(p)
            if os.path.isdir(loc):
                shutil.rmtree(loc, ignore_errors=True)
            elif os.path.exists(loc):
                os.remove(loc)
            elif "-f" not in flags:
                err += "rm: `%s': No such file or directory\n" % p
                rc = 1
        return "", err, rc
    if sub in ("put", "copyfromlocal", "movefromlocal"):
        if len(pos) < 2:
            return "", "put: missing operand\n", 1
        dst = _r(pos[-1])
        for s in pos[:-1]:
            if os.path.isdir(dst) or len(pos) > 2:
                os.makedirs(dst, exist_ok=True)
                d2 = os.path.join(dst, os.path.basename(s.rstrip("/\\")))
            else:
                os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
                d2 = dst
            if os.path.exists(d2):
                if "-f" not in flags:
                    return "", "put: `%s': File exists\n" % pos[-1], 1
                shutil.rmtree(d2) if os.path.isdir(d2) else os.remove(d2)
            (shutil.copytree if os.path.isdir(s) else shutil.copy2)(s, d2)
        return "", "", 0
    if sub in ("get", "copytolocal", "movetolocal"):
        if len(pos) < 2:
            return "", "get: missing operand\n", 1
        src, dst = _r(pos[0]), pos[1]
        if not os.path.exists(src):
            return "", "get: `%s': No such file or directory\n" % pos[0], 1
        if os.path.isdir(src):
            if not os.path.exists(dst):
                shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return "", "", 0
    if sub in ("cat", "text", "tail"):
        out = []
        for p in pos:
            loc = _r(p)
            fs = [loc] if os.path.isfile(loc) else sorted(
                os.path.join(r, f) for r, _d, ff in os.walk(loc) for f in ff) if os.path.isdir(loc) else []
            if not fs:
                return "", "cat: `%s': No such file or directory\n" % p, 1
            for f in fs:
                with open(f, "r", encoding="utf-8", errors="replace") as fh:
                    out.append(fh.read())
        return "".join(out), "", 0
    if sub == "du":
        out = []
        for p in pos:
            loc = _r(p)
            tot = sum(os.path.getsize(os.path.join(r, f)) for r, _d, ff in os.walk(loc) for f in ff) \
                if os.path.isdir(loc) else (os.path.getsize(loc) if os.path.exists(loc) else 0)
            out.append("%d  %d  %s" % (tot, tot * 3, p))
        return "\n".join(out) + "\n", "", 0
    if sub in ("mv", "cp"):
        if len(pos) < 2:
            return "", "%s: missing operand\n" % sub, 1
        s, d = _r(pos[0]), _r(pos[1])
        if not os.path.exists(s):
            return "", "%s: `%s': No such file or directory\n" % (sub, pos[0]), 1
        os.makedirs(os.path.dirname(d) or ".", exist_ok=True)
        if sub == "mv":
            shutil.move(s, d)
        else:
            (shutil.copytree if os.path.isdir(s) else shutil.copy2)(s, d)
        return "", "", 0
    if sub == "touchz":
        for p in pos:
            loc = _r(p)
            os.makedirs(os.path.dirname(loc) or ".", exist_ok=True)
            open(loc, "a").close()
        return "", "", 0
    if sub == "count":
        out = []
        for p in pos:
            loc = _r(p)
            nd = sum(len(ds) for _r2, ds, _f in os.walk(loc)) + 1 if os.path.isdir(loc) else 0
            nf = sum(len(ff) for _r2, _d, ff in os.walk(loc)) if os.path.isdir(loc) else 1
            tot = sum(os.path.getsize(os.path.join(r, f)) for r, _d, ff in os.walk(loc) for f in ff) \
                if os.path.isdir(loc) else 0
            out.append("%12d %12d %18d %s" % (nd, nf, tot, p))
        return "\n".join(out) + "\n", "", 0
    if sub in ("chmod", "chown", "chgrp", "setrep", "expunge", "setfacl"):
        return "", "", 0
    return None


def _simulado(argv, texto):
    cmd = " ".join(argv)
    if E["estricto"]:
        raise RuntimeError("[demo] comando externo no soportado en modo estricto (BNX_DEMO_ESTRICTO=1): %s" % cmd)
    log("comando externo simulado: %s" % cmd[:140])
    E["comandos"].append({"job": E["job"], "cmd": cmd[:200], "tipo": "externo"})
    return "", "", 0


def interceptar(args, shell=False):
    """(stdout, stderr, rc) si es un CLI del cluster; None si debe correr normal."""
    if isinstance(args, (list, tuple)):
        argv = [str(x) for x in args]
    elif isinstance(args, str):
        try:
            argv = shlex.split(args, posix=(os.name != "nt"))
        except ValueError:
            argv = args.split()
    else:
        return None
    if not argv:
        return None
    prog = _prog(argv)
    if prog not in HDFS and prog not in OTROS:
        return None
    if any(a in _OPERADORES for a in argv):
        return _simulado(argv, args)
    if prog in HDFS:
        sub = argv[1].lower() if len(argv) > 1 else ""
        if sub in ("dfs", "fs"):
            r = _hdfs(argv[2:])
            if r is not None:
                E["comandos"].append({"job": E["job"], "cmd": " ".join(argv)[:200], "tipo": "hdfs"})
                return r
        elif prog == "hadoop" and sub == "version":
            return "Hadoop 3.x (demo)\n", "", 0
    return _simulado(argv, args)


class _Popen(subprocess.Popen):
    def __init__(self, args, *a, **k):
        res = interceptar(args, k.get("shell"))
        if res is not None:
            out, err, rc = res
            args = [sys.executable, "-c", _HELPER, out.encode("utf-8", "replace").hex(),
                    err.encode("utf-8", "replace").hex(), str(rc)]
            k = dict(k)
            k.pop("shell", None)
            k.pop("executable", None)
            k.pop("preexec_fn", None)
        super(_Popen, self).__init__(args, *a, **k)


def _system(cmd):
    res = interceptar(cmd, True)
    if res is None:
        return E["orig"]["system"](cmd)
    out, err, rc = res
    sys.stdout.write(out)
    sys.stderr.write(err)
    sys.stdout.flush()
    return rc << 8 if os.name != "nt" else rc


class _Pipe(io.StringIO):
    rc = 0

    def close(self):
        super(_Pipe, self).close()
        return None if not self.rc else self.rc << 8


def _popen(cmd, mode="r", buffering=-1):
    res = interceptar(cmd, True)
    if res is None:
        return E["orig"]["popen"](cmd, mode, buffering)
    p = _Pipe(res[0] + res[1])
    p.rc = res[2]
    return p


def aplicar():
    O = E["orig"]
    O["Popen"], O["system"], O["popen"] = subprocess.Popen, os.system, os.popen
    subprocess.Popen = _Popen
    os.system = _system
    os.popen = _popen


def quitar():
    O = E["orig"]
    if "Popen" in O:
        subprocess.Popen, os.system, os.popen = O["Popen"], O["system"], O["popen"]
