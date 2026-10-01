// Extension VS Code: BNX PySpark Optimizer — optimiza PySpark por reglas.
//
// Llama al endpoint /optimize del portal BNX (mismo motor que la CLI y la GUI),
// que aplica reglas de performance SIN IA: cache de DataFrames reusados con
// linaje costoso, broadcast en joins con lado pequeno y coalesce en escritura.
// No requiere Python en la maquina del usuario. La URL del portal es
// configurable (psparkOptimizer.serverUrl).

const vscode = require("vscode");
const http = require("http");
const https = require("https");
const { URL } = require("url");

/** POST JSON al endpoint /optimize y devuelve el objeto de respuesta. */
function optimizeViaServer(serverUrl, code) {
  return new Promise((resolve, reject) => {
    let base;
    try {
      base = new URL(serverUrl.replace(/\/+$/, "") + "/optimize");
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
            resolve(JSON.parse(body));
          } catch (e) {
            reject(new Error("Respuesta no valida del servidor: " + body.slice(0, 200)));
          }
        });
      }
    );
    req.on("error", (e) =>
      reject(new Error("No se pudo conectar a " + base.href + " (" + e.message + "). " +
        "Revisa que el portal BNX este corriendo y la config psparkOptimizer.serverUrl."))
    );
    req.on("timeout", () => { req.destroy(); reject(new Error("Timeout al contactar el servidor.")); });
    req.write(payload);
    req.end();
  });
}

/** Resumen legible de los cambios aplicados. */
function summarize(result) {
  const s = result.summary || {};
  const parts = [];
  if (s.cache_reused) parts.push(`${s.cache_reused} cache`);
  if (s.broadcast_join) parts.push(`${s.broadcast_join} broadcast`);
  if (s.coalesce_write) parts.push(`${s.coalesce_write} coalesce`);
  const n = result.total_changes || 0;
  if (n === 0) return "sin cambios (el codigo ya esta optimizado)";
  return `${n} optimizacion(es)` + (parts.length ? `: ${parts.join(", ")}` : "");
}

/** Muestra el resultado: abre editor nuevo o reemplaza la seleccion. */
async function showResult(editor, result, replaceRange) {
  if (!result || result.ok === false || result.error) {
    vscode.window.showErrorMessage("PySpark Optimizer: " + (result && result.error || "no se pudo optimizar."));
    return;
  }
  const msg = summarize(result);
  if ((result.total_changes || 0) === 0) {
    vscode.window.showInformationMessage("PySpark Optimizer: " + msg);
  } else {
    vscode.window.showInformationMessage("PySpark Optimizer: " + msg + ".");
  }

  const cfg = vscode.workspace.getConfiguration("psparkOptimizer");
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
    vscode.workspace.getConfiguration("psparkOptimizer").get("serverUrl", "http://localhost:8081");

  const run = async (code, editor, range) => {
    if (!code || !code.trim()) {
      vscode.window.showErrorMessage("PySpark Optimizer: no hay codigo para optimizar.");
      return;
    }
    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "PySpark Optimizer: optimizando…" },
      async () => {
        try {
          const result = await optimizeViaServer(serverUrl(), code);
          await showResult(editor, result, range);
        } catch (e) {
          vscode.window.showErrorMessage("PySpark Optimizer: " + e.message);
        }
      }
    );
  };

  // Optimizar la SELECCION (o todo el documento si no hay seleccion).
  const cmdSel = vscode.commands.registerCommand("psparkOptimizer.optimizeSelection", async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) { vscode.window.showErrorMessage("PySpark Optimizer: abre un archivo PySpark primero."); return; }
    const sel = editor.selection;
    const hasSel = !sel.isEmpty;
    const range = hasSel ? sel : new vscode.Range(
      editor.document.positionAt(0),
      editor.document.positionAt(editor.document.getText().length)
    );
    const code = editor.document.getText(hasSel ? sel : undefined);
    await run(code, editor, range);
  });

  // Optimizar el ARCHIVO completo (siempre en editor nuevo).
  const cmdFile = vscode.commands.registerCommand("psparkOptimizer.optimizeFile", async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) { vscode.window.showErrorMessage("PySpark Optimizer: abre un archivo PySpark primero."); return; }
    const code = editor.document.getText();
    await run(code, editor, null);
  });

  context.subscriptions.push(cmdSel, cmdFile);
}

function deactivate() {}

module.exports = { activate, deactivate };
