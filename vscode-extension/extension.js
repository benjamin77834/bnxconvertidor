// Extension VS Code: py2spark — convierte Python (pandas) a PySpark 3.
//
// OFFLINE: ejecuta el motor py2spark con el PYTHON LOCAL del usuario (sin portal
// BNX ni red). El motor (paquete ./py2spark + run_py2spark.py) va EMPAQUETADO
// dentro del .vsix; es 100% stdlib y compatible con Python 3.8+. Requisito:
// tener Python 3 instalado (configurable con py2spark.pythonPath).

const vscode = require("vscode");
const cp = require("child_process");
const path = require("path");
const fs = require("fs");

// Carpeta de la extension (donde viven run_py2spark.py y ./py2spark).
let EXT_DIR = __dirname;

/** Lista de candidatos a intérprete Python, en orden de preferencia. */
function pythonCandidates() {
  const cfg = vscode.workspace.getConfiguration("py2spark").get("pythonPath", "").trim();
  const list = [];
  if (cfg) list.push(cfg);
  // Interprete seleccionado por la extension oficial de Python, si existe.
  try {
    const pyExt = vscode.extensions.getExtension("ms-python.python");
    const execCmd = pyExt && pyExt.exports && pyExt.exports.settings &&
      pyExt.exports.settings.getExecutionDetails &&
      pyExt.exports.settings.getExecutionDetails().execCommand;
    if (Array.isArray(execCmd) && execCmd.length) list.push(execCmd[0]);
  } catch (_e) { /* ignore */ }
  list.push("python3", "python", "py");
  return [...new Set(list)];
}

/** Ejecuta run_py2spark.py con un interprete, pasando code por stdin. */
function runWithPython(pythonBin, code) {
  return new Promise((resolve, reject) => {
    const script = path.join(EXT_DIR, "run_py2spark.py");
    const child = cp.spawn(pythonBin, [script], { cwd: EXT_DIR });
    let out = "", err = "";
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      try { child.kill(); } catch (_e) { /* ignore */ }
      reject(new Error("Timeout: la conversion tardo demasiado."));
    }, 60000);

    child.on("error", (e) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      reject(e); // ENOENT => interprete no encontrado; probamos el siguiente
    });
    child.stdout.on("data", (d) => (out += d));
    child.stderr.on("data", (d) => (err += d));
    child.on("close", (codeExit) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      try {
        resolve(JSON.parse(out));
      } catch (e) {
        reject(new Error("Respuesta no valida del motor" +
          (err ? (": " + err.slice(0, 300)) : ("; salida: " + out.slice(0, 200)))));
      }
    });
    child.stdin.on("error", () => { /* el close/error ya maneja el flujo */ });
    child.stdin.write(JSON.stringify({ code }));
    child.stdin.end();
  });
}

/** Convierte localmente probando los interpretes Python disponibles. */
async function convertLocal(code) {
  const candidates = pythonCandidates();
  let lastErr = null;
  for (const bin of candidates) {
    try {
      return await runWithPython(bin, code);
    } catch (e) {
      lastErr = e;
      // ENOENT: interprete inexistente -> probar el siguiente candidato.
      if (e && (e.code === "ENOENT" || /ENOENT/.test(e.message || ""))) continue;
      // Otro error (p.ej. del propio script) -> no tiene sentido reintentar.
      throw e;
    }
  }
  throw new Error(
    "No se encontro Python 3. Instala Python 3.8+ o define la ruta en la config " +
    "'py2spark.pythonPath'. (Interpretes probados: " + candidates.join(", ") + ")" +
    (lastErr ? " — " + lastErr.message : ""));
}

/** Muestra el resultado: abre editor nuevo o reemplaza la seleccion. */
async function showResult(editor, result, replaceRange) {
  if (!result || result.ok === false) {
    const msg = (result && result.unsupported && result.unsupported[0]) ||
      (result && result.error) || "No se pudo convertir el codigo.";
    vscode.window.showErrorMessage("py2spark: " + msg);
    return;
  }
  // Avisos y no soportados.
  const warns = (result.warnings || []).length;
  const unsup = (result.unsupported || []).length;
  if (unsup > 0) {
    vscode.window.showWarningMessage(
      `py2spark: ${unsup} construccion(es) requieren revision manual (ver # TODO py2spark).`
    );
  } else if (warns > 0) {
    vscode.window.showInformationMessage(`py2spark: convertido con ${warns} aviso(s).`);
  } else {
    vscode.window.showInformationMessage("py2spark: conversion completada.");
  }

  const cfg = vscode.workspace.getConfiguration("py2spark");
  const openNew = cfg.get("openInNewEditor", true);

  if (openNew || !replaceRange) {
    const doc = await vscode.workspace.openTextDocument({
      content: result.code,
      language: "python",
    });
    await vscode.window.showTextDocument(doc, { preview: false });
  } else {
    await editor.edit((eb) => eb.replace(replaceRange, result.code));
  }
}

function activate(context) {
  EXT_DIR = context.extensionPath || __dirname;

  const run = async (code, editor, range) => {
    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "py2spark: convirtiendo a PySpark…" },
      async () => {
        try {
          const result = await convertLocal(code);
          await showResult(editor, result, range);
        } catch (e) {
          vscode.window.showErrorMessage("py2spark: " + e.message);
        }
      }
    );
  };

  // Convertir la SELECCION (o todo el documento si no hay seleccion).
  const cmdSel = vscode.commands.registerCommand("py2spark.convertSelection", async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) { vscode.window.showErrorMessage("py2spark: abre un archivo Python primero."); return; }
    const sel = editor.selection;
    const hasSel = !sel.isEmpty;
    const range = hasSel ? sel : new vscode.Range(
      editor.document.positionAt(0),
      editor.document.positionAt(editor.document.getText().length)
    );
    const code = editor.document.getText(hasSel ? sel : undefined);
    await run(code, editor, range);
  });

  // Convertir el ARCHIVO completo (siempre en editor nuevo).
  const cmdFile = vscode.commands.registerCommand("py2spark.convertFile", async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) { vscode.window.showErrorMessage("py2spark: abre un archivo Python primero."); return; }
    const code = editor.document.getText();
    await run(code, editor, null);
  });

  context.subscriptions.push(cmdSel, cmdFile);
}

function deactivate() {}

module.exports = { activate, deactivate };
