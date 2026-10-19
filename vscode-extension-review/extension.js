// Extension VS Code: BNX Code Review (estilo Sonar).
//
// Llama al endpoint /analyze del portal BNX (mismo motor que la GUI de Data
// Sintetica) y pinta los hallazgos como DIAGNOSTICOS nativos del editor
// (subrayado + panel Problems). Reglas: palabras reservadas / shadowing de
// built-ins, performance (.collect/.toPandas/.count), seguridad (secretos
// hardcodeados), smells (except desnudo, print, lineas largas, etc.).
// No requiere Python local. La URL del portal es configurable (bnxReview.serverUrl).

const vscode = require("vscode");
const http = require("http");
const https = require("https");
const { URL } = require("url");

/** POST JSON al endpoint /analyze y devuelve el objeto de respuesta. */
function analyzeViaServer(serverUrl, code) {
  return new Promise((resolve, reject) => {
    let base;
    try {
      base = new URL(serverUrl.replace(/\/+$/, "") + "/analyze");
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
        "Revisa que el portal BNX este corriendo y la config bnxReview.serverUrl."))
    );
    req.on("timeout", () => { req.destroy(); reject(new Error("Timeout al contactar el servidor.")); });
    req.write(payload);
    req.end();
  });
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

async function analyzeDocument(doc, collection, serverUrl, silent) {
  if (!doc || doc.languageId !== "python") {
    if (!silent) vscode.window.showErrorMessage("BNX Review: abre un archivo Python/PySpark primero.");
    return;
  }
  const code = doc.getText();
  if (!code.trim()) { collection.set(doc.uri, []); return; }
  try {
    const result = await analyzeViaServer(serverUrl, code);
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

  const serverUrl = () =>
    vscode.workspace.getConfiguration("bnxReview").get("serverUrl", "http://127.0.0.1:8081");
  const analyzeOnSave = () =>
    vscode.workspace.getConfiguration("bnxReview").get("analyzeOnSave", true);

  // Comando: analizar el archivo activo (muestra resumen).
  const cmdAnalyze = vscode.commands.registerCommand("bnxReview.analyzeFile", async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) { vscode.window.showErrorMessage("BNX Review: abre un archivo Python primero."); return; }
    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "BNX Review: analizando…" },
      async () => { await analyzeDocument(editor.document, collection, serverUrl(), false); }
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
      analyzeDocument(doc, collection, serverUrl(), true);
    }
  });

  // Limpiar diagnosticos al cerrar el documento.
  const onClose = vscode.workspace.onDidCloseTextDocument((doc) => collection.delete(doc.uri));

  context.subscriptions.push(cmdAnalyze, cmdClear, onSave, onClose);
}

function deactivate() {}

module.exports = { activate, deactivate };
