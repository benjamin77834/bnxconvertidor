import { useState, useEffect } from 'react'
import { COMPILE_URL } from '../config'

// Emulador MLOps: corre el pipeline (pasos encadenados) con datos sintéticos en
// Spark local, paso a paso, y muestra 3 salidas: grafo del pipeline, tabla por
// paso (entra/sale) y resultado final (muestra + DQC). Equivalente al emulador
// CICS pero para el framework de feature engineering / scoring.
const API_BASE = COMPILE_URL.replace(/\/compile$/, '')
const EMULATE_URL = `${API_BASE}/mlops/emulate`

// Pipeline de ejemplo (pandas de negocio encadenado). Cada paso usa `df` y deja
// el resultado en `df_out`. El emulador los convierte/encadena con datos
// sintéticos.
const EXAMPLE_STEPS = [
  { id: 'groupby', name: 'Group By', code: 'import pandas as pd\n# agrupa por cliente y resume el monto\ndf_out = df.groupby("cliente_id").agg({"monto": "sum", "saldo": "mean"}).reset_index()\n' },
  { id: 'ratios', name: 'Ratios', code: 'import numpy as np\n# ratio con protección de /0\ndf_out = df\ndf_out["utilizacion"] = np.where(df["saldo"] > 0, df["monto"] / df["saldo"], 0.0)\n' },
  { id: 'features', name: 'Feature Engineering', code: '# flag de cliente de alto monto\ndf_out = df\ndf_out["es_alto"] = (df["monto"] > 5000).astype(int)\n' },
  { id: 'scoring', name: 'Scoring', code: '# score lineal de ejemplo (en producción: XGBoost)\ndf_out = df\ndf_out["score"] = (df["utilizacion"] * 0.7 + df["es_alto"] * 0.3).clip(0, 1)\n' },
]

let _uid = 0
const newStep = (name = '', code = '') => ({ id: `step_${++_uid}`, name, code })

export default function MLOpsEmulatorPage({ theme, initialSteps, onConsumeInitial }) {
  const t = theme || {}
  const [steps, setSteps] = useState([newStep('Mi paso', 'df_out = df\n')])
  const [nRows, setNRows] = useState(30)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  // Si llegan pasos desde el generador ("Emular estas fuentes"), cargarlos.
  useEffect(() => {
    if (initialSteps && initialSteps.length) {
      _uid = 0
      setSteps(initialSteps.map(s => ({
        id: `step_${++_uid}`, name: s.name || s.id || 'paso', code: s.code || 'df_out = df\n',
      })))
      setResult(null); setError('')
      onConsumeInitial && onConsumeInitial()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialSteps])

  const card = {
    background: t.card || '#0f172a', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 16,
  }

  const loadExample = () => {
    _uid = 0
    setSteps(EXAMPLE_STEPS.map(s => ({ ...s, id: `step_${++_uid}` })))
    setResult(null); setError('')
  }
  const addStep = () => setSteps(s => [...s, newStep(`Paso ${s.length + 1}`, 'df_out = df\n')])
  const removeStep = (id) => setSteps(s => s.filter(x => x.id !== id))
  const updateStep = (id, field, val) => setSteps(s => s.map(x => x.id === id ? { ...x, [field]: val } : x))
  const move = (id, dir) => setSteps(s => {
    const i = s.findIndex(x => x.id === id)
    const j = i + dir
    if (i < 0 || j < 0 || j >= s.length) return s
    const copy = [...s];[copy[i], copy[j]] = [copy[j], copy[i]]; return copy
  })

  const emulate = async () => {
    const payload = steps.filter(s => (s.code || '').trim())
      .map(s => ({ id: s.id, name: s.name || s.id, code: s.code }))
    if (!payload.length) { setError('Agrega al menos un paso con código.'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const res = await fetch(EMULATE_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ steps: payload, n_rows: Number(nRows) || 30 }),
      })
      const data = await res.json()
      if (!res.ok || data.error && !data.steps) { setError(data.error || `HTTP ${res.status}`); return }
      setResult(data)
    } catch (e) { setError('Error de red: ' + e.message) }
    finally { setLoading(false) }
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 16, width: '100%', boxSizing: 'border-box' }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 22, color: t.text || '#e2e8f0' }}>🔬 Emulador MLOps</h2>
        <p style={{ margin: '4px 0 0', fontSize: 13, color: t.muted || '#94a3b8', maxWidth: 900 }}>
          Corre tu pipeline (extract → groupby → features → vector → scoring) con <b>datos sintéticos</b> en
          Spark local, <b>paso a paso</b>, sin Cloudera/YARN. Ves el <b>flujo</b>, qué <b>datos entran y salen</b>
          en cada paso y el <b>resultado final</b>. Cada paso usa <code>df</code> (entrada) y deja <code>df_out</code>.
        </p>
      </div>

      {/* Controles */}
      <div style={{ ...card, display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <button onClick={loadExample} style={btn(t, 'ghost')}>📚 Cargar pipeline de ejemplo</button>
        <button onClick={addStep} style={btn(t, 'ghost')}>➕ Añadir paso</button>
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, color: t.text || '#e2e8f0' }}>
          Filas sintéticas:
          <input type="number" value={nRows} min={5} max={200} onChange={e => setNRows(e.target.value)}
            style={{ width: 70, padding: '5px 8px', borderRadius: 6, background: t.codeBg || '#081220', color: t.text, border: `1px solid ${t.border || '#334155'}` }} />
        </label>
        <button onClick={emulate} disabled={loading} style={{ ...btn(t, 'primary', loading), marginLeft: 'auto' }}>
          {loading ? '⏳ Emulando…' : '▶️ Emular pipeline'}
        </button>
      </div>
      {error && <div style={{ ...card, borderColor: '#ef4444', color: '#f87171', fontSize: 13 }}>⚠️ {error}</div>}

      {/* Editor de pasos */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {steps.map((s, i) => (
          <div key={s.id} style={{ ...card, display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 12, fontWeight: 800, color: t.dim || '#64748b' }}>{i + 1}</span>
              <input value={s.name} onChange={e => updateStep(s.id, 'name', e.target.value)}
                placeholder="Nombre del paso"
                style={{ flex: 1, padding: '6px 10px', borderRadius: 6, fontSize: 13, fontWeight: 600,
                  background: t.codeBg || '#081220', color: t.text || '#e2e8f0', border: `1px solid ${t.border || '#334155'}` }} />
              <button onClick={() => move(s.id, -1)} disabled={i === 0} style={miniBtn(t, i === 0)}>↑</button>
              <button onClick={() => move(s.id, 1)} disabled={i === steps.length - 1} style={miniBtn(t, i === steps.length - 1)}>↓</button>
              <button onClick={() => removeStep(s.id)} style={{ ...miniBtn(t), color: '#f87171' }}>✕</button>
            </div>
            <textarea value={s.code} onChange={e => updateStep(s.id, 'code', e.target.value)} spellCheck={false}
              placeholder="df_out = df  # usa df (entrada) y deja df_out (salida)"
              style={{ width: '100%', minHeight: 100, padding: 10, borderRadius: 8, boxSizing: 'border-box',
                background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
                color: t.text || '#e2e8f0', fontFamily: 'monospace', fontSize: 12, lineHeight: 1.5,
                resize: 'vertical', outline: 'none', whiteSpace: 'pre' }} />
          </div>
        ))}
      </div>

      {/* Resultado */}
      {result && (
        <div style={{
          ...card, borderColor: (result.ok ? '#22c55e' : '#f59e0b') + '66',
          display: 'flex', flexDirection: 'column', gap: 14,
        }}>
          {/* Encabezado destacado de la zona de resultados */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
            paddingBottom: 10, borderBottom: `1px solid ${t.border || '#334155'}`,
          }}>
            <span style={{ fontSize: 18 }}>{result.ok ? '✅' : '⚠️'}</span>
            <span style={{ fontSize: 16, fontWeight: 800, color: t.text || '#e2e8f0' }}>
              Resultados de la emulación
            </span>
            <span style={{
              fontSize: 11.5, fontWeight: 700, padding: '3px 10px', borderRadius: 999,
              background: (result.ok ? '#22c55e' : '#f59e0b') + '22',
              color: result.ok ? '#22c55e' : '#fbbf24',
              border: `1px solid ${(result.ok ? '#22c55e' : '#f59e0b')}55`,
            }}>
              {result.ok ? 'pipeline completo' : 'se detuvo en un error'}
            </span>
            <span style={{ marginLeft: 'auto', fontSize: 12, color: t.muted || '#94a3b8' }}>
              {(result.steps || []).filter(s => s.ok).length}/{(result.steps || []).length} pasos OK
            </span>
          </div>

          {/* Librerías del banco simuladas (stub) */}
          {(result.stubbed || []).length > 0 && (
            <div style={{
              fontSize: 11.5, color: '#fbbf24', background: '#f59e0b12',
              border: '1px solid #f59e0b33', borderRadius: 8, padding: '8px 10px',
            }}>
              🏦 Librerías internas simuladas (no están en local, se stubearon para
              poder ver el flujo): <b>{result.stubbed.join(', ')}</b>.
              <span style={{ color: t.muted || '#94a3b8' }}> Su lógica real no se ejecutó;
              en la red del banco corren de verdad.</span>
            </div>
          )}

          {/* 1) Grafo del pipeline */}
          <section>
            <SectionTitle t={t} n="1" title="Flujo del pipeline" />
            <div style={{ overflowX: 'auto', paddingBottom: 6 }}>
              <PipelineGraph steps={result.steps || []} theme={t} />
            </div>
          </section>

          {/* 2) Tabla por paso (scroll propio) */}
          <section>
            <SectionTitle t={t} n="2" title="Qué pasa en cada paso (entra → sale)" />
            <div style={{
              maxHeight: 320, overflow: 'auto',
              border: `1px solid ${t.border || '#334155'}`, borderRadius: 8,
            }}>
              <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12 }}>
                <thead><tr style={{ textAlign: 'left' }}>
                  {['Paso', 'Estado', 'Entrada', 'Salida', 'Columnas nuevas', 'Tiempo'].map(h =>
                    <th key={h} style={stickyHead(t)}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {(result.steps || []).map((s, i) => (
                    <tr key={i} style={{ borderBottom: `1px solid ${(t.border || '#334155')}44` }}>
                      <td style={cell(t)}><b>{s.name}</b></td>
                      <td style={{ ...cell(t), color: s.ok ? '#22c55e' : '#ef4444', fontWeight: 700 }}>{s.ok ? 'OK' : 'ERROR'}</td>
                      <td style={cell(t)}>{s.rows_in != null ? `${s.rows_in}f × ${s.cols_in}c` : '—'}</td>
                      <td style={cell(t)}>{s.rows_out != null ? `${s.rows_out}f × ${s.cols_out}c` : '—'}</td>
                      <td style={{ ...cell(t), color: '#38bdf8' }}>{(s.new_cols || []).join(', ') || '—'}</td>
                      <td style={cell(t)}>{s.seconds != null ? `${s.seconds}s` : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {(result.steps || []).some(s => s.error) && (
              <div style={{ marginTop: 8, fontSize: 12, color: '#f87171' }}>
                {result.steps.filter(s => s.error).map((s, i) => <div key={i}>⚠️ <b>{s.name}</b>: {s.error}</div>)}
              </div>
            )}
          </section>

          {/* 3) Resultado final + DQC (scroll propio en ambos ejes) */}
          {result.final?.columns?.length > 0 && (
            <section>
              <SectionTitle t={t} n="3"
                title={`Resultado final · ${result.final.total_rows}f × ${result.final.total_cols}c (muestra de ${result.final.rows.length})`} />
              <div style={{
                maxHeight: 360, overflow: 'auto',
                border: `1px solid ${t.border || '#334155'}`, borderRadius: 8,
              }}>
                <table style={{ borderCollapse: 'collapse', fontSize: 11.5 }}>
                  <thead><tr>
                    {result.final.columns.map((c, i) => (
                      <th key={i} style={stickyHead(t)}>
                        {c}{(result.metrics?.dqc?.[c]?.null_pct) ? (
                          <span style={{ color: '#fbbf24', fontWeight: 400 }}> · {result.metrics.dqc[c].null_pct}% nulos</span>
                        ) : null}
                      </th>
                    ))}
                  </tr></thead>
                  <tbody>
                    {result.final.rows.map((r, ri) => (
                      <tr key={ri} style={{ borderBottom: `1px solid ${(t.border || '#334155')}33` }}>
                        {r.map((v, ci) => <td key={ci} style={{ ...cell(t), whiteSpace: 'nowrap' }}>{v}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}

// Grafo del pipeline dibujado con nodos (sin dependencia de mermaid runtime).
function PipelineGraph({ steps, theme }) {
  const t = theme || {}
  const node = (label, ok, sub) => (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
      padding: '8px 12px', borderRadius: 10, minWidth: 100, textAlign: 'center',
      background: ok === false ? '#7f1d1d' : (t.codeBg || '#081220'),
      border: `1px solid ${ok === false ? '#ef4444' : (t.border || '#334155')}`,
      color: ok === false ? '#fff' : (t.text || '#e2e8f0'),
    }}>
      <span style={{ fontSize: 12, fontWeight: 700 }}>{label}</span>
      {sub && <span style={{ fontSize: 10, color: ok === false ? '#fca5a5' : (t.dim || '#64748b') }}>{sub}</span>}
    </div>
  )
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
      {node('datos\nsintéticos', true, null)}
      {steps.map((s, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ color: t.dim || '#64748b', fontSize: 18, margin: '0 2px' }}>→</span>
          {node(s.name, s.ok, s.rows_out != null ? `${s.rows_out}f × ${s.cols_out}c` : null)}
        </div>
      ))}
    </div>
  )
}

function SectionTitle({ t, n, title }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
      <span style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        width: 20, height: 20, borderRadius: '50%', fontSize: 11, fontWeight: 800,
        background: (t.accent || '#6366f1') + '22', color: t.accent || '#818cf8',
        border: `1px solid ${(t.accent || '#6366f1')}55`,
      }}>{n}</span>
      <span style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0' }}>{title}</span>
    </div>
  )
}
// Cabecera sticky para tablas con scroll (se queda fija al hacer scroll vertical).
function stickyHead(t) {
  return {
    position: 'sticky', top: 0, zIndex: 1, padding: '7px 10px', textAlign: 'left',
    fontSize: 11.5, fontWeight: 700, whiteSpace: 'nowrap',
    color: t.muted || '#94a3b8', background: t.card || '#0f172a',
    borderBottom: `2px solid ${t.border || '#334155'}`,
  }
}
function cell(t) { return { padding: '6px 10px', color: t.text || '#e2e8f0' } }
function miniBtn(t, disabled) {
  return {
    padding: '4px 8px', borderRadius: 6, fontSize: 12, cursor: disabled ? 'not-allowed' : 'pointer',
    background: 'transparent', color: t.muted || '#94a3b8', border: `1px solid ${t.border || '#334155'}`,
  }
}
function btn(t, kind, disabled) {
  const base = { padding: '8px 14px', borderRadius: 8, fontSize: 12.5, fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer', border: '1px solid transparent', whiteSpace: 'nowrap' }
  if (kind === 'primary') return { ...base, background: disabled ? (t.border || '#334155') : (t.accent || '#6366f1'), color: '#fff' }
  return { ...base, background: 'transparent', border: `1px solid ${t.border || '#334155'}`, color: t.muted || '#94a3b8' }
}
