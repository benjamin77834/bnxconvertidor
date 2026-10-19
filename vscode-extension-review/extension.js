// Extension VS Code: BNX Code Review (estilo Sonar).
//
// 100% OFFLINE: el motor de analisis corre DENTRO de la extension (reviewer.js,
// port de src/code_review.py). NO se conecta a ningun servidor ni requiere el
// portal BNX ni Python. Pinta los hallazgos como DIAGNOSTICOS nativos del editor
// (subrayado + panel Problems). Reglas: shadowing de built-ins, performance
// (.collect/.toPandas/.count), seguridad (secretos hardcodeados), smells
// (except desnudo, except:pass, == None, print, funciones largas, lineas largas).

const vscode = require("vscode");
const { reviewCode } = require("./reviewer");

/** Analiza localmente (sin red). Devuelve una promesa por compatibilidad. */
function analyzeLocal(code) {
  return Promise.resolve().then(() => reviewCode(code));
}

/** Mapea la severidad BNX a la severidad de diagnostico de VS Code. */
function toSeverity(sev) {
  switch (sev) {
    case "critical": return vscode.DiagnosticSeverity.Error;
    case "major": return vscode.DiagnosticSeverity.Warning;
    // minor e info -> Information (visible). Evitamos 'Hint' porque VS Code lo
    // dibuja casi invisible (3 puntitos) y a veces lo oculta del panel Problems,
    // asi el usuario no "veia" los hallazgos aunque la notificacion los contaba.
    case "minor": return vscode.DiagnosticSeverity.Warning;
    default: return vscode.DiagnosticSeverity.Information;
  }
}

/** Construye los diagnosticos del documento a partir de los hallazgos. */
function buildDiagnostics(doc, findings) {
  const diags = [];
  for (const f of findings || []) {
    const lineNo = Math.max(0, (f.line || 1) - 1);
    const line = lineNo < doc.lineCount ? doc.lineAt(lineNo) : null;
    const range = line
      ? new vscode.Range(lineNo, line.firstNonWhitespaceCharacterIndex, lineNo, line.text.length)
      : new vscode.Range(lineNo, 0, lineNo, 0);
    // Mensaje estilo SonarLint: "[TYPE] mensaje". type/rule_key vienen del
    // modelo Sonar del backend (BUG/CODE_SMELL/VULNERABILITY/SECURITY_HOTSPOT).
    const typeTag = f.type ? `[${f.type}] ` : "";
    const d = new vscode.Diagnostic(range, typeTag + (f.message || f.rule), toSeverity(f.severity));
    d.source = "BNX Review (Sonar)";
    // d.code con la clave de regla tipo Sonar (python:Sxxxx) para que se vea en
    // el panel Problems, como SonarLint.
    d.code = f.rule_key || f.rule;
    diags.push(d);
  }
  return diags;
}

async function analyzeDocument(doc, collection, silent) {
  if (!doc || doc.languageId !== "python") {
    if (!silent) vscode.window.showErrorMessage("BNX Review: abre un archivo Python/PySpark primero.");
    return;
  }
  const code = doc.getText();
  if (!code.trim()) { collection.set(doc.uri, []); return; }
  try {
    const result = await analyzeLocal(code);
    if (result.error) {
      if (!silent) vscode.window.showErrorMessage("BNX Review: " + result.error);
      return;
    }
    const findings = result.findings || [];
    collection.set(doc.uri, buildDiagnostics(doc, findings));
    if (!silent) {
      const s = result.summary || {};
      if (findings.length === 0) {
        vscode.window.showInformationMessage("BNX Review: sin hallazgos — el codigo luce limpio.");
      } else {
        const msg = `${s.total || findings.length} hallazgo(s): ${s.critical || 0} críticos, ${s.major || 0} mayores, ${s.minor || 0} menores, ${s.info || 0} info.`;
        // Abrir el panel Problems para que el usuario VEA los hallazgos (no solo
        // la notificacion). Ofrecemos un boton por si prefiere abrirlo a mano.
        try { await vscode.commands.executeCommand("workbench.actions.view.problems"); } catch (_e) { /* ignore */ }
        const pick = await vscode.window.showInformationMessage(
          "BNX Review: " + msg + " Revisa el panel Problems (Cmd/Ctrl+Shift+M).",
          "Ver Problems");
        if (pick === "Ver Problems") {
          try { await vscode.commands.executeCommand("workbench.actions.view.problems"); } catch (_e) { /* ignore */ }
        }
      }
    }
  } catch (e) {
    if (!silent) vscode.window.showErrorMessage("BNX Review: " + e.message);
  }
}

function activate(context) {
  const collection = vscode.languages.createDiagnosticCollection("bnxReview");
  context.subscriptions.push(collection);

  const analyzeOnSave = () =>
    vscode.workspace.getConfiguration("bnxReview").get("analyzeOnSave", true);

  // Comando: analizar el archivo activo (muestra resumen).
  const cmdAnalyze = vscode.commands.registerCommand("bnxReview.analyzeFile", async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) { vscode.window.showErrorMessage("BNX Review: abre un archivo Python primero."); return; }
    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "BNX Review: analizando…" },
      async () => { await analyzeDocument(editor.document, collection, false); }
    );
  });

  // Comando: limpiar diagnosticos del archivo activo.
  const cmdClear = vscode.commands.registerCommand("bnxReview.clear", () => {
    const editor = vscode.window.activeTextEditor;
    if (editor) collection.delete(editor.document.uri);
  });

  // Analisis automatico al guardar (silencioso).
  const onSave = vscode.workspace.onDidSaveTextDocument((doc) => {
    if (analyzeOnSave() && doc.languageId === "python") {
      analyzeDocument(doc, collection, true);
    }
  });

  // Limpiar diagnosticos al cerrar el documento.
  const onClose = vscode.workspace.onDidCloseTextDocument((doc) => collection.delete(doc.uri));

  context.subscriptions.push(cmdAnalyze, cmdClear, onSave, onClose);
}

function deactivate() {}

module.exports = { activate, deactivate };
