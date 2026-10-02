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

  const run = async () => {
    setRunning(true); setError(''); setResult(null)
    try {
      const ex = examples.find(e => e.id === selected)
      const body = ex ? { yaml: ex.yaml, csv: ex.csv, train: true } : {}
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
            pipeline declarativo (YAML) → código + PMML → <b>SHA-256</b> (integridad) + <b>cifrado</b> (confidencialidad)
            + <b>firma Ed25519</b> (autenticidad) → <b>VERIFY</b> antes de desplegar. El entrenamiento no forma
            parte del framework.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, flexShrink: 0, alignItems: 'center' }}>
          {examples.length > 0 && (
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
            <h3 style={{ margin: '0 0 8px', fontSize: 14, color: t.text }}>📦 Artifact PMML</h3>
            <pre style={mono}>{result.pmml}</pre>
          </div>
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
