import { useState, useEffect } from 'react'
import { COMPILE_URL } from '../config'

// Framework de Modelos (operacionalizacion): toma un modelo entregado por negocio
// y produce un paquete estandarizado y verificable — pipeline declarativo ->
// codigo + PMML -> SHA-256 + cifrado Fernet + firma Ed25519 -> VERIFY (deployable).
// Llama al endpoint /model/run del portal. El entrenamiento NO es parte del
// framework: el modelo demo solo simula el artefacto entregado por negocio.
const MODEL_RUN_URL = COMPILE_URL.replace('/compile', '/model/run')
const MODEL_EXAMPLES_URL = COMPILE_URL.replace('/compile', '/model/examples')

export default function ModelFrameworkPage({ theme }) {
  const t = theme || {}
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [examples, setExamples] = useState([])
  const [selected, setSelected] = useState('')
  const [mode, setMode] = useState('example')   // 'example' | 'upload'
  const [upYaml, setUpYaml] = useState('')       // contenido del .yml subido
  const [upCsv, setUpCsv] = useState('')         // contenido del .csv subido
  const [upYamlName, setUpYamlName] = useState('')
  const [upCsvName, setUpCsvName] = useState('')
  const [showHelp, setShowHelp] = useState(false)   // panel "¿Qué hace esto?"

  // Cargar los ejemplos disponibles (config YAML + dataset) al montar.
  useEffect(() => {
    fetch(MODEL_EXAMPLES_URL)
      .then(r => r.json())
      .then(d => {
        const list = d.examples || []
        setExamples(list)
        if (list.length) setSelected(list[0].id)
      })
      .catch(() => {})
  }, [])

  const readFile = (file, setContent, setName) => {
    const reader = new FileReader()
    reader.onload = () => { setContent(reader.result || ''); setName(file.name) }
    reader.readAsText(file)
  }

  const run = async () => {
    setRunning(true); setError(''); setResult(null)
    try {
      let body
      if (mode === 'upload') {
        if (!upYaml.trim()) { setError('Sube un archivo de configuración .yml.'); return }
        if (!upCsv.trim()) { setError('Sube un dataset .csv.'); return }
        body = { yaml: upYaml, csv: upCsv, train: true }
      } else {
        const ex = examples.find(e => e.id === selected)
        body = ex ? { yaml: ex.yaml, csv: ex.csv, train: true } : {}
      }
      const res = await fetch(MODEL_RUN_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if (data.error) { setError(data.error); return }
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally { setRunning(false) }
  }

  const card = {
    background: t.card || '#1e2433', borderRadius: 10, padding: 16,
    border: `1px solid ${t.border || '#334155'}`,
  }
  const mono = {
    fontFamily: 'monospace', fontSize: 11, whiteSpace: 'pre-wrap',
    background: t.codeBg || '#081220', borderRadius: 6, padding: 10,
    color: t.muted || '#94a3b8', maxHeight: 260, overflow: 'auto',
    border: '1px solid #33415530', margin: 0,
  }
  const sec = result?.manifest?.security || {}

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 22, color: t.text || '#e2e8f0' }}>🔐 Modelos (Operacionalización)</h2>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: t.muted || '#94a3b8', maxWidth: 720, lineHeight: 1.5 }}>
            Toma un modelo entregado por negocio y produce un paquete estandarizado y verificable:
            pipeline declarativo (YAML) → código + <b>PMML y job PySpark</b> → <b>SHA-256</b> (integridad)
            + <b>cifrado</b> (confidencialidad) + <b>firma Ed25519</b> (autenticidad) → <b>VERIFY</b> antes de
            desplegar. El entrenamiento no forma parte del framework.
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flexShrink: 0, alignItems: 'flex-end' }}>
          {/* Toggle: ejemplo vs subir archivos */}
          <div style={{ display: 'flex', gap: 4 }}>
            {['example', 'upload'].map(m => (
              <button key={m} onClick={() => setMode(m)}
                style={{
                  padding: '5px 10px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                  background: mode === m ? '#8b5cf620' : 'transparent',
                  border: `1px solid ${mode === m ? '#8b5cf6' : (t.border || '#334155')}`,
                  color: mode === m ? '#a78bfa' : (t.muted || '#94a3b8'), fontWeight: mode === m ? 600 : 400,
                }}>{m === 'example' ? '📚 Ejemplo' : '📤 Subir archivos'}</button>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {mode === 'example' && examples.length > 0 && (
              <select value={selected} onChange={e => setSelected(e.target.value)}
                title="Ejemplo de modelo a operacionalizar"
                style={{
                  padding: '9px 10px', borderRadius: 8, fontSize: 13,
                  background: t.card || '#1e2433', color: t.text || '#e2e8f0',
                  border: `1px solid ${t.border || '#334155'}`,
                }}>
                {examples.map(ex => (
                  <option key={ex.id} value={ex.id}>{ex.name} ({ex.features.length} features)</option>
                ))}
              </select>
            )}
            {mode === 'upload' && (
              <div style={{ display: 'flex', gap: 6 }}>
                <label style={{ padding: '8px 10px', borderRadius: 8, fontSize: 12, cursor: 'pointer',
                  background: 'transparent', border: `1px solid ${upYaml ? '#22c55e60' : (t.border || '#334155')}`,
                  color: upYaml ? '#22c55e' : (t.muted || '#94a3b8') }}>
                  {upYamlName ? `📄 ${upYamlName}` : '📄 config .yml'}
                  <input type="file" accept=".yml,.yaml" hidden
                    onChange={e => { if (e.target.files[0]) readFile(e.target.files[0], setUpYaml, setUpYamlName); e.target.value = '' }} />
                </label>
                <label style={{ padding: '8px 10px', borderRadius: 8, fontSize: 12, cursor: 'pointer',
                  background: 'transparent', border: `1px solid ${upCsv ? '#22c55e60' : (t.border || '#334155')}`,
                  color: upCsv ? '#22c55e' : (t.muted || '#94a3b8') }}>
                  {upCsvName ? `🗃️ ${upCsvName}` : '🗃️ dataset .csv'}
                  <input type="file" accept=".csv" hidden
                    onChange={e => { if (e.target.files[0]) readFile(e.target.files[0], setUpCsv, setUpCsvName); e.target.value = '' }} />
                </label>
              </div>
            )}
            <button onClick={run} disabled={running}
              style={{
                padding: '10px 18px', borderRadius: 8,
                cursor: running ? 'not-allowed' : 'pointer', fontSize: 14, fontWeight: 700,
                background: running ? (t.border || '#334155') : '#8b5cf6', color: '#fff', border: 'none',
              }}>
              {running ? '⏳ Ejecutando pipeline…' : '▶️ Ejecutar framework'}
            </button>
          </div>
        </div>
      </div>

      {/* Documentacion colapsable: "¿Que hace esto?" (visible pero discreta) */}
      <div style={{ ...card, marginBottom: 16, padding: 0, overflow: 'hidden' }}>
        <button onClick={() => setShowHelp(v => !v)}
          style={{
            width: '100%', textAlign: 'left', padding: '12px 16px', cursor: 'pointer',
            background: 'transparent', border: 'none', color: t.text || '#e2e8f0',
            fontSize: 14, fontWeight: 600, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
          <span>❓ ¿Qué hace esta sección? (documentación)</span>
          <span style={{ color: t.dim }}>{showHelp ? '▲ ocultar' : '▼ mostrar'}</span>
        </button>
        {showHelp && (
          <div style={{ padding: '0 16px 16px', fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.65 }}>
            <p style={{ marginTop: 0 }}>
              <b style={{ color: t.text }}>En una frase:</b> es un sello de calidad y seguridad automatizado para
              modelos. Entra un modelo entrenado (entregado por negocio) y sale un paquete estandarizado,
              cifrado, firmado y verificable, con auditoría completa — y si algo se altera, se rechaza solo.
            </p>

            <p style={{ color: t.text, fontWeight: 600, marginBottom: 4 }}>El problema que resuelve</p>
            <p style={{ marginTop: 0 }}>
              Entre “tengo un modelo que funciona” y “está en producción de forma segura y auditable” hay muchos
              pasos de control que normalmente se hacen a mano. Esta sección los automatiza y estandariza.
            </p>

            <p style={{ color: t.text, fontWeight: 600, marginBottom: 4 }}>Qué hace, paso a paso</p>
            <ol style={{ margin: '0 0 8px', paddingLeft: 20 }}>
              <li><b>Lee una configuración (YAML)</b> que describe el modelo, sus variables y qué pasos ejecutar.</li>
              <li><b>Ejecuta un pipeline</b> de 6 etapas: data_validation → preparation → feature_engineering → score → evaluation → package.</li>
              <li><b>Genera los entregables</b>: código de scoring, artefacto <b>PMML</b> (JPMML/JVM) y un <b>job PySpark</b> (scoring a escala en Spark).</li>
              <li><b>Aplica 3 controles de seguridad</b> (abajo).</li>
              <li><b>Verifica antes de desplegar</b>: si firma y hashes cuadran → <code>deployable: True</code>.</li>
              <li><b>Deja rastro</b>: audit log (quién, qué etapa, cuándo, resultado) y correos de control.</li>
            </ol>

            <p style={{ color: t.text, fontWeight: 600, marginBottom: 4 }}>Los 3 controles de seguridad</p>
            <ul style={{ margin: '0 0 8px', paddingLeft: 20 }}>
              <li><b>SHA-256 (integridad)</b>: huella de cada archivo; si cambia un carácter, cambia la huella.</li>
              <li><b>Cifrado Fernet (confidencialidad)</b>: cifra el código generado para que no se lea sin la llave.</li>
              <li><b>Firma Ed25519 (autenticidad)</b>: firma el manifiesto; garantiza que lo emitió quien dice y nadie lo alteró.</li>
            </ul>

            <p style={{ color: t.text, fontWeight: 600, marginBottom: 4 }}>La demo que verás al ejecutar</p>
            <p style={{ marginTop: 0 }}>
              El sistema verifica el paquete (deployable=True), luego <b>altera a propósito</b> el código
              (simula manipulación) → la verificación lo <b>rechaza por “Hash mismatch”</b> → lo <b>restaura</b> →
              vuelve a deployable=True. Demuestra que ningún archivo modificado llega a producción sin detectarse.
            </p>

            <p style={{ marginBottom: 0, fontSize: 12, color: t.dim, fontStyle: 'italic' }}>
              Nota: es un MVP demo. El modelo se entrena con XGBoost solo para simular el que entregaría negocio
              (el entrenamiento no es parte del framework). La firma y verificación sí son criptografía real
              (Ed25519 / Fernet / SHA-256). Hay “switch points” marcados para reemplazar el código demo por las
              librerías corporativas reales.
            </p>
          </div>
        )}
      </div>

      {error && (
        <div style={{ ...card, borderColor: '#ef444460', marginBottom: 16 }}>
          <span style={{ color: '#f87171', fontSize: 13 }}>⚠️ {error}</span>
        </div>
      )}

      {result && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {/* Estado del deployment */}
          <div style={{ ...card, gridColumn: '1 / -1',
            borderColor: result.deployable ? '#22c55e60' : '#ef444460',
            background: (result.deployable ? '#22c55e' : '#ef4444') + '12' }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: result.deployable ? '#22c55e' : '#ef4444' }}>
              {result.deployable ? '✅ deployable = True' : '❌ deployable = False'}
            </div>
            <div style={{ fontSize: 12, color: t.muted, marginTop: 4 }}>
              firma: <b>{result.verify?.signature}</b> · hashes: <b>{result.verify?.hashes}</b> ·
              execution_id: <code>{result.execution_id?.slice(0, 8)}</code>
            </div>
          </div>

          {/* Pipeline */}
          <div style={card}>
            <h3 style={{ margin: '0 0 8px', fontSize: 14, color: t.text }}>🧩 Pipeline ejecutado</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {(result.pipeline || []).map((s, i) => (
                <span key={i} style={{ fontSize: 12, padding: '3px 8px', borderRadius: 6,
                  background: '#8b5cf620', border: '1px solid #8b5cf640', color: '#a78bfa' }}>{i + 1}. {s}</span>
              ))}
            </div>
            <div style={{ fontSize: 11, color: t.dim, marginTop: 10 }}>
              métricas score: filas {result.metrics?.rows}, media {result.metrics?.mean?.toFixed?.(4)}
            </div>
          </div>

          {/* Seguridad */}
          <div style={card}>
            <h3 style={{ margin: '0 0 8px', fontSize: 14, color: t.text }}>🔐 Seguridad del manifest</h3>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: t.muted, lineHeight: 1.7 }}>
              <li><b>Integridad</b>: SHA-256 de {Object.keys(result.manifest?.artifacts || {}).length} artifacts</li>
              <li><b>Confidencialidad</b>: cifrado {sec.encryption?.algorithm || '—'} del código generado</li>
              <li><b>Autenticidad</b>: firma {sec.signature?.algorithm || '—'} del manifest canónico</li>
            </ul>
          </div>

          {/* Demo de integridad */}
          <div style={{ ...card, gridColumn: '1 / -1' }}>
            <h3 style={{ margin: '0 0 8px', fontSize: 14, color: t.text }}>🛡️ Control de integridad (demo altero → rechazo → restauro)</h3>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', fontSize: 12 }}>
              <span style={{ color: '#f87171' }}>
                Tras alterar el código: deployable = <b>{String(result.integrity_demo?.tampered?.deployable)}</b>
                {result.integrity_demo?.tampered?.error ? ` (${result.integrity_demo.tampered.error})` : ''}
              </span>
              <span style={{ color: '#22c55e' }}>
                Tras restaurar: deployable = <b>{String(result.integrity_demo?.restored?.deployable)}</b>
              </span>
            </div>
          </div>

          {/* Manifest */}
          <div style={card}>
            <h3 style={{ margin: '0 0 8px', fontSize: 14, color: t.text }}>📄 Execution Manifest</h3>
            <pre style={mono}>{JSON.stringify(result.manifest, null, 2)}</pre>
          </div>

          {/* Audit log */}
          <div style={card}>
            <h3 style={{ margin: '0 0 8px', fontSize: 14, color: t.text }}>📜 Audit log ({result.audit?.length || 0} eventos)</h3>
            <pre style={mono}>{(result.audit || []).map(e =>
              `[${e.status}] ${e.component}${e.duration_ms != null ? ' · ' + e.duration_ms + 'ms' : ''}`
            ).join('\n')}</pre>
          </div>

          {/* Codigo generado */}
          <div style={card}>
            <h3 style={{ margin: '0 0 8px', fontSize: 14, color: t.text }}>⚙️ Código generado</h3>
            <pre style={mono}>{result.generated_code}</pre>
          </div>

          {/* PMML */}
          <div style={card}>
            <h3 style={{ margin: '0 0 8px', fontSize: 14, color: t.text }}>📦 Artifact PMML (scoring JPMML/JVM)</h3>
            <pre style={mono}>{result.pmml}</pre>
          </div>

          {/* Job PySpark de scoring */}
          {result.generated_pyspark && (
            <div style={{ ...card, gridColumn: '1 / -1' }}>
              <h3 style={{ margin: '0 0 8px', fontSize: 14, color: t.text }}>
                🐍 Job PySpark de scoring (equivalente al PMML, escala en Spark)
              </h3>
              <pre style={{ ...mono, maxHeight: 340 }}>{result.generated_pyspark}</pre>
            </div>
          )}
        </div>
      )}

      {!result && !error && (
        <div style={{ ...card, textAlign: 'center', color: t.dim, fontSize: 13 }}>
          Pulsa <b>Ejecutar framework</b> para correr el pipeline de operacionalización de ejemplo
          (modelo de riesgo crediticio XGBoost) y ver el manifest firmado, el audit log y la verificación.
        </div>
      )}
    </div>
  )
}
