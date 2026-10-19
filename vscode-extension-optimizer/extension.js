// Extension VS Code: BNX PySpark Optimizer — optimiza PySpark por reglas.
//
// 100% OFFLINE: el motor de optimizacion corre DENTRO de la extension
// (optimizer.js, port de src/perf_optimizer.py). NO se conecta a ningun
// servidor ni requiere el portal BNX corriendo ni Python en la maquina.
// Aplica reglas de performance SIN IA: cache de DataFrames reusados con linaje
// costoso, broadcast en joins con lado pequeno y coalesce en escritura.

const vscode = require("vscode");
const { optimizePyspark } = require("./optimizer");

/** Optimiza localmente (sin red). Devuelve una promesa por compatibilidad. */
function optimizeLocal(code) {
  return Promise.resolve().then(() => optimizePyspark(code, true));
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
  const run = async (code, editor, range) => {
    if (!code || !code.trim()) {
      vscode.window.showErrorMessage("PySpark Optimizer: no hay codigo para optimizar.");
      return;
    }
    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "PySpark Optimizer: optimizando…" },
      async () => {
        try {
          const result = await optimizeLocal(code);
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
