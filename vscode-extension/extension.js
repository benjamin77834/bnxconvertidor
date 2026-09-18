// Extension VS Code: py2spark — convierte Python (pandas) a PySpark 3.
//
// Llama al endpoint /py2spark del portal BNX (mismo motor que la CLI y la GUI),
// asi no requiere Python instalado en la maquina del usuario. La URL del portal
// es configurable (py2spark.serverUrl).

const vscode = require("vscode");
const http = require("http");
const https = require("https");
const { URL } = require("url");

/** POST JSON al endpoint /py2spark y devuelve el objeto de respuesta. */
function convertViaServer(serverUrl, code) {
  return new Promise((resolve, reject) => {
    let base;
    try {
      base = new URL(serverUrl.replace(/\/+$/, "") + "/py2spark");
    } catch (e) {
      return reject(new Error("URL de servidor invalida: " + serverUrl));
    }
    const payload = JSON.stringify({ code });
    const lib = base.protocol === "https:" ? https : http;
    const req = lib.request(
      base,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(payload),
        },
        timeout: 30000,
      },
      (res) => {
        let body = "";
        res.on("data", (c) => (body += c));
        res.on("end", () => {
          try {
            const data = JSON.parse(body);
            resolve(data);
          } catch (e) {
            reject(new Error("Respuesta no valida del servidor: " + body.slice(0, 200)));
          }
        });
      }
    );
    req.on("error", (e) =>
      reject(new Error("No se pudo conectar a " + base.href + " (" + e.message + "). " +
        "Revisa que el portal BNX este corriendo y la config py2spark.serverUrl."))
    );
    req.on("timeout", () => { req.destroy(); reject(new Error("Timeout al contactar el servidor.")); });
    req.write(payload);
    req.end();
  });
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
  const serverUrl = () =>
    vscode.workspace.getConfiguration("py2spark").get("serverUrl", "http://localhost:8081");

  const run = async (code, editor, range) => {
    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "py2spark: convirtiendo a PySpark…" },
      async () => {
        try {
          const result = await convertViaServer(serverUrl(), code);
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
