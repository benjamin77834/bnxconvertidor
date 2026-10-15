import { useState } from 'react'

const COMPILE_URL = (import.meta.env.VITE_API_URL || '') + '/compile'
const EMULATE_URL = COMPILE_URL.replace('/compile', '/emulate')

// Emulador CICS: ejecuta el COBOL/ALGOL convertido (Python puro) con datos
// sinteticos, tracea el flujo de parrafos y muestra un grafo explicativo.
// Permite enviar el codigo + datos a Data Sintetica (igual que Py->Spark).
export default function EmulatorPage({ theme: t, sourceToken, code, lang, onSendToDataGen }) {
  const [state, setState] = useState('idle')  // idle | running | done | error
  const [report, setReport] = useState(null)
  const [err, setErr] = useState('')

  const run = async () => {
    setState('running'); setErr(''); setReport(null)
    try {
      const base = COMPILE_URL.replace('/compile', '')
      const res = await fetch(base + '/emulate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_token: sourceToken || undefined, code: code || undefined, lang: lang || 'cobol', timeout: 90 }),
      })
      const data = await res.json()
      if (!res.ok || data.error) throw new Error(data.error || `Error ${res.status}`)
      setReport(data); setState('done')
    } catch (e) {
      setErr(e.message); setState('error')
    }
  }

  const box = { background: t.card, border: `1px solid ${t.border}`, borderRadius: 10, padding: 16 }
  const canRun = Boolean(sourceToken || code)

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 22, color: t.text }}>🔬 Emulador CICS</h2>
        <p style={{ margin: '4px 0 0', fontSize: 13, color: t.muted }}>
          Ejecuta el COBOL/ALGOL convertido (Python puro) como un monitor transaccional:
          procesa un mensaje con datos sintéticos y traza el flujo real de párrafos.
          Muestra un grafo explicativo de qué hace el código y permite llevarlo a Data Sintética.
        </p>
      </div>

      {!canRun && (
        <div style={{ ...box, color: t.muted }}>
          Primero convierte un COBOL/ALGOL a <b>Python</b> en el Compiler (modo transaccional).
          Luego vuelve aquí para emularlo.
        </div>
      )}

      {canRun && (
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <button onClick={run} disabled={state === 'running'} style={{
            padding: '10px 18px', borderRadius: 8, fontSize: 14, fontWeight: 700, border: 'none',
            cursor: state === 'running' ? 'wait' : 'pointer', background: '#6366f1', color: '#fff',
          }}>{state === 'running' ? '⏳ Emulando…' : '🔬 Emular transacción'}</button>
          {report && onSendToDataGen && (
            <button onClick={() => onSendToDataGen(code, report)} style={{
              padding: '10px 18px', borderRadius: 8, fontSize: 14, fontWeight: 700, border: 'none',
              cursor: 'pointer', background: '#22c55e', color: '#04210f',
            }}>🧪 Enviar a Data Sintética</button>
          )}
        </div>
      )}

      {state === 'error' && (
        <div style={{ ...box, borderColor: '#ef4444', color: '#ffd4d4', background: '#2a0d0d' }}>
          ✕ {err}
        </div>
      )}

      {report && (
        <>
          {/* Resumen */}
          <div style={{ ...box, display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            <Stat t={t} label="Resultado" value={report.ok ? '✓ Ejecutó' : '✕ Falló'} color={report.ok ? '#22c55e' : '#ef4444'} />
            <Stat t={t} label="Párrafos ejecutados" value={(report.paragraphs_executed || 0).toLocaleString()} />
            <Stat t={t} label="Llamadas totales" value={(report.total_calls || 0).toLocaleString()} />
            <Stat t={t} label="Lookups" value={(report.lookups || []).length} />
            {report.truncated && <Stat t={t} label="Traza" value="truncada" color="#f59e0b" />}
          </div>

          {/* Flujo ejecutado (orden) */}
          <div style={box}>
            <div style={{ fontSize: 13, fontWeight: 700, color: t.text, marginBottom: 8 }}>
              🧭 Flujo ejecutado (orden de párrafos)
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {(report.order || []).slice(0, 60).map((p, i) => (
                <span key={i} style={{
                  fontSize: 11, fontFamily: 'monospace', padding: '2px 8px', borderRadius: 6,
                  background: t.codeBg || '#0b0f14', color: '#9fe', border: `1px solid ${t.border}`,
                }}>{i + 1}. {p}{(report.counts || {})[p] > 1 ? ` ×${report.counts[p]}` : ''}</span>
              ))}
              {(report.order || []).length > 60 && (
                <span style={{ fontSize: 11, color: t.muted }}>… +{report.order.length - 60} más</span>
              )}
            </div>
          </div>

          {/* Grafo Mermaid (texto, copiable para mermaid.live) */}
          <div style={box}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: t.text }}>🗺️ Grafo del flujo (Mermaid)</span>
              <button onClick={() => { navigator.clipboard.writeText(report.mermaid || '') }} style={{
                fontSize: 11, padding: '3px 10px', borderRadius: 6, cursor: 'pointer',
                background: 'transparent', border: `1px solid ${t.border}`, color: t.muted,
              }}>📋 Copiar</button>
            </div>
            <p style={{ fontSize: 11, color: t.muted, margin: '0 0 6px' }}>
              Pega esto en <a href="https://mermaid.live" target="_blank" rel="noreferrer" style={{ color: t.accent }}>mermaid.live</a> para verlo como diagrama.
            </p>
            <pre style={{
              margin: 0, padding: 10, maxHeight: 320, overflowY: 'auto', fontSize: 11,
              background: t.codeBg || '#0b0f14', color: '#cfe', borderRadius: 6,
              border: `1px solid ${t.border}`, whiteSpace: 'pre',
            }}>{report.mermaid}</pre>
          </div>

          {/* Datos sintéticos usados */}
          {report.datasets && Object.keys(report.datasets).length > 0 && (
            <div style={box}>
              <div style={{ fontSize: 13, fontWeight: 700, color: t.text, marginBottom: 8 }}>
                📦 Datos sintéticos (lookups) usados
              </div>
              {Object.entries(report.datasets).slice(0, 6).map(([name, d]) => (
                <div key={name} style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: 12, color: t.accent, fontFamily: 'monospace' }}>{name}.csv</div>
                  <div style={{ fontSize: 11, color: t.muted, fontFamily: 'monospace' }}>
                    columnas: {(d.columns || []).join(', ')}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Respuesta de la transacción */}
          {report.resp_sample && Object.keys(report.resp_sample).length > 0 && (
            <div style={box}>
              <div style={{ fontSize: 13, fontWeight: 700, color: t.text, marginBottom: 8 }}>
                📤 Respuesta de la transacción (muestra)
              </div>
              <pre style={{
                margin: 0, padding: 10, maxHeight: 240, overflowY: 'auto', fontSize: 11,
                background: t.codeBg || '#0b0f14', color: '#9fe', borderRadius: 6, border: `1px solid ${t.border}`,
              }}>{Object.entries(report.resp_sample).slice(0, 30).map(([k, v]) => `${k} = ${v}`).join('\n')}</pre>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function Stat({ t, label, value, color }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: color || t.text }}>{value}</div>
    </div>
  )
}
