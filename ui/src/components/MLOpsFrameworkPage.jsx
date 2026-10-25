import { useState, useEffect, useRef } from 'react'
import { COMPILE_URL } from '../config'

// Seccion "Framework MLOps": explica el pipeline de feature engineering para
// scoring crediticio PASO A PASO, con ejemplos pandas de negocio (convertibles a
// Spark con el convertidor BNX) y la referencia del framework real en PySpark.
// Integra con /py2spark (convertir), /optimize (mejorar) y Data Sintetica.
const API_BASE = COMPILE_URL.replace(/\/compile$/, '')
const FRAMEWORK_URL = `${API_BASE}/mlops/framework`
const PY2SPARK_URL = `${API_BASE}/py2spark`
const OPTIMIZE_URL = `${API_BASE}/optimize`

export default function MLOpsFrameworkPage({ theme, onSendToDataGen }) {
  const t = theme || {}
  const [steps, setSteps] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [loadingSteps, setLoadingSteps] = useState(true)
  const stepRefs = useRef({})

  useEffect(() => {
    fetch(FRAMEWORK_URL)
      .then(r => r.json())
      .then(d => {
        const s = d.steps || []
        setSteps(s)
        if (s.length) setActiveId(s[0].id)
      })
      .catch(() => setSteps([]))
      .finally(() => setLoadingSteps(false))
  }, [])

  const scrollToStep = (id) => {
    setActiveId(id)
    const el = stepRefs.current[id]
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const card = {
    background: t.card || '#0f172a', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 16,
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 16, width: '100%', boxSizing: 'border-box' }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 22, color: t.text || '#e2e8f0' }}>🧬 Framework MLOps</h2>
        <p style={{ margin: '4px 0 0', fontSize: 13, color: t.muted || '#94a3b8', maxWidth: 900 }}>
          Pipeline de feature engineering para <b>scoring crediticio</b>, paso a paso. El negocio escribe
          Python (pandas); aquí lo <b>conviertes a PySpark</b> con el convertidor BNX, lo <b>optimizas</b> y lo
          llevas a <b>Data Sintética</b> para probarlo. Cada paso incluye el ejemplo de negocio y cómo se ve
          en el framework real (producción).
        </p>
      </div>

      {/* Diagrama del pipeline (nodos clicables) */}
      <div style={{ ...card }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: t.muted || '#94a3b8', marginBottom: 10, textTransform: 'uppercase', letterSpacing: 0.5 }}>
          Flujo del pipeline
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
          {steps.map((s, i) => (
            <div key={s.id} style={{ display: 'flex', alignItems: 'center' }}>
              <button onClick={() => scrollToStep(s.id)}
                style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
                  padding: '8px 10px', borderRadius: 10, cursor: 'pointer', minWidth: 92,
                  background: activeId === s.id ? (t.accent || '#6366f1') + '22' : (t.codeBg || '#081220'),
                  border: `1px solid ${activeId === s.id ? (t.accent || '#6366f1') : (t.border || '#334155')}`,
                  color: activeId === s.id ? (t.accent || '#818cf8') : (t.text || '#e2e8f0'),
                }}>
                <span style={{ fontSize: 20, lineHeight: 1 }}>{s.emoji}</span>
                <span style={{ fontSize: 10.5, fontWeight: 700, textAlign: 'center', lineHeight: 1.2 }}>
                  {s.title.replace(/^\d+\.\s*/, '')}
                </span>
              </button>
              {i < steps.length - 1 && (
                <span style={{ color: t.dim || '#64748b', fontSize: 18, margin: '0 2px' }}>→</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {loadingSteps && (
        <div style={{ ...card, fontSize: 13, color: t.muted || '#94a3b8' }}>Cargando pasos del framework…</div>
      )}

      {/* Tarjetas por paso */}
      {steps.map(s => (
        <div key={s.id} ref={el => { stepRefs.current[s.id] = el }}>
          <StepCard step={s} theme={t} onSendToDataGen={onSendToDataGen} />
        </div>
      ))}

      {/* Area libre: pega otro codigo y convierte/mejora */}
      <FreeForm theme={t} onSendToDataGen={onSendToDataGen} />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Tarjeta de un paso: resumen + pandas (editable) + referencia + acciones.
// ---------------------------------------------------------------------------
function StepCard({ step, theme, onSendToDataGen }) {
  const t = theme || {}
  const [code, setCode] = useState(step.pandas || '')
  const [showRef, setShowRef] = useState(false)
  const conv = useConvert(code)

  const card = {
    background: t.card || '#0f172a', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 16,
  }
  return (
    <div style={{ ...card, display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div>
        <h3 style={{ margin: 0, fontSize: 17, color: t.text || '#e2e8f0' }}>{step.emoji} {step.title}</h3>
        <p style={{ margin: '4px 0 0', fontSize: 12.5, color: t.muted || '#94a3b8' }}>{step.summary}</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        {/* Pandas de negocio (editable) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: 0 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#38bdf8' }}>🐍 Python de negocio (pandas) — editable</div>
          <textarea value={code} onChange={e => setCode(e.target.value)} spellCheck={false}
            style={codeBox(t, 200)} />
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button onClick={conv.convert} disabled={conv.loading} style={btn(t, 'primary', conv.loading)}>
              {conv.loading ? '…' : '⚡ Convertir a Spark'}
            </button>
            {conv.result?.code && (
              <>
                <button onClick={conv.optimize} disabled={conv.optimizing} style={btn(t, 'secondary', conv.optimizing)}>
                  {conv.optimizing ? '…' : '✨ Optimizar'}
                </button>
                <button onClick={() => onSendToDataGen && onSendToDataGen(conv.result.code, code)}
                  style={btn(t, 'accent')}>🧪 Data Sintética</button>
              </>
            )}
            <button onClick={() => setShowRef(v => !v)} style={btn(t, 'ghost')}>
              {showRef ? 'Ocultar' : 'Ver'} framework real
            </button>
          </div>
        </div>

        {/* Salida PySpark */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: 0 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#22c55e' }}>⚡ PySpark generado</div>
          {conv.error && (
            <div style={{ padding: 8, borderRadius: 6, background: '#ef444415', border: '1px solid #ef444440', color: '#f87171', fontSize: 12 }}>
              {conv.error}
            </div>
          )}
          <textarea readOnly value={conv.result?.code || ''} spellCheck={false}
            placeholder="Convierte el pandas para ver aquí el PySpark…"
            style={{ ...codeBox(t, 200), color: '#22c55e' }} />
          {conv.optimizeSummary && (
            <div style={{ fontSize: 11.5, color: '#fbbf24' }}>✨ {conv.optimizeSummary}</div>
          )}
          {conv.result && (conv.result.unsupported?.length > 0 || conv.result.warnings?.length > 0) && (
            <div style={{ fontSize: 11.5, color: t.muted || '#94a3b8' }}>
              {conv.result.unsupported?.length > 0 && <div style={{ color: '#f87171' }}>Revisión manual: {conv.result.unsupported.length}</div>}
              {conv.result.warnings?.length > 0 && <div style={{ color: '#f59e0b' }}>Avisos: {conv.result.warnings.length}</div>}
            </div>
          )}
        </div>
      </div>

      {/* Referencia del framework real */}
      {showRef && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#a78bfa' }}>🏭 Así se ve en el framework real (PySpark, producción)</div>
          <pre style={{ ...codeBox(t, 'auto'), margin: 0, color: '#c4b5fd', maxHeight: 260, overflow: 'auto' }}>{step.framework_ref}</pre>
        </div>
      )}

      {/* Datos de muestra */}
      {step.sample_csv && (
        <details>
          <summary style={{ fontSize: 11.5, color: t.muted || '#94a3b8', cursor: 'pointer' }}>
            📄 Datos de muestra para este paso (CSV)
          </summary>
          <pre style={{ ...codeBox(t, 'auto'), margin: '6px 0 0', color: t.text || '#e2e8f0', maxHeight: 180, overflow: 'auto' }}>{step.sample_csv}</pre>
        </details>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Area libre: pega cualquier Python y convierte/optimiza.
// ---------------------------------------------------------------------------
function FreeForm({ theme, onSendToDataGen }) {
  const t = theme || {}
  const [code, setCode] = useState('')
  const conv = useConvert(code)
  const card = {
    background: t.card || '#0f172a', border: `2px dashed ${t.border || '#334155'}`,
    borderRadius: 10, padding: 16,
  }
  return (
    <div style={{ ...card, display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div>
        <h3 style={{ margin: 0, fontSize: 16, color: t.text || '#e2e8f0' }}>✍️ Tu propio código</h3>
        <p style={{ margin: '4px 0 0', fontSize: 12.5, color: t.muted || '#94a3b8' }}>
          Pega cualquier Python (pandas) del framework o de tus modelos y conviértelo/optimízalo a PySpark aquí mismo.
        </p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: 0 }}>
          <textarea value={code} onChange={e => setCode(e.target.value)} spellCheck={false}
            placeholder="import pandas as pd&#10;df = pd.read_csv('datos.csv')&#10;..."
            style={codeBox(t, 220)} />
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button onClick={conv.convert} disabled={conv.loading || !code.trim()} style={btn(t, 'primary', conv.loading || !code.trim())}>
              {conv.loading ? '…' : '⚡ Convertir a Spark'}
            </button>
            {conv.result?.code && (
              <>
                <button onClick={conv.optimize} disabled={conv.optimizing} style={btn(t, 'secondary', conv.optimizing)}>
                  {conv.optimizing ? '…' : '✨ Optimizar'}
                </button>
                <button onClick={() => onSendToDataGen && onSendToDataGen(conv.result.code, code)}
                  style={btn(t, 'accent')}>🧪 Data Sintética</button>
              </>
            )}
            {code && <button onClick={() => setCode('')} style={btn(t, 'ghost')}>Limpiar</button>}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: 0 }}>
          {conv.error && (
            <div style={{ padding: 8, borderRadius: 6, background: '#ef444415', border: '1px solid #ef444440', color: '#f87171', fontSize: 12 }}>
              {conv.error}
            </div>
          )}
          <textarea readOnly value={conv.result?.code || ''} spellCheck={false}
            placeholder="El PySpark aparecerá aquí…"
            style={{ ...codeBox(t, 220), color: '#22c55e' }} />
          {conv.optimizeSummary && <div style={{ fontSize: 11.5, color: '#fbbf24' }}>✨ {conv.optimizeSummary}</div>}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Hook: convertir pandas->PySpark (/py2spark) y optimizar (/optimize).
// ---------------------------------------------------------------------------
function useConvert(code) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [optimizing, setOptimizing] = useState(false)
  const [optimizeSummary, setOptimizeSummary] = useState('')
  const [error, setError] = useState('')

  const convert = async () => {
    if (!code.trim()) return
    setLoading(true); setError(''); setResult(null); setOptimizeSummary('')
    try {
      const res = await fetch(PY2SPARK_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
      const data = await res.json()
      if (data.error) { setError(data.error); return }
      if (data.ok === false) {
        setError((data.unsupported && data.unsupported[0]) || 'El código no es Python válido.')
        return
      }
      setResult(data)
    } catch (e) { setError('Error de red: ' + e.message) }
    finally { setLoading(false) }
  }

  const optimize = async () => {
    if (!result?.code) return
    setOptimizing(true); setOptimizeSummary('')
    try {
      const res = await fetch(OPTIMIZE_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: result.code }),
      })
      const data = await res.json()
      if (data.error) { setError(data.error); return }
      setResult(r => ({ ...r, code: data.code }))
      const s = data.summary || {}
      const parts = []
      if (s.cache_reused) parts.push(`${s.cache_reused} cache`)
      if (s.broadcast_join) parts.push(`${s.broadcast_join} broadcast`)
      if (s.coalesce_write) parts.push(`${s.coalesce_write} coalesce`)
      if (s.dead_code_removed) parts.push(`${s.dead_code_removed} limpieza`)
      setOptimizeSummary(data.total_changes
        ? `${data.total_changes} optimización(es)` + (parts.length ? `: ${parts.join(', ')}` : '')
        : 'sin cambios (ya estaba optimizado)')
    } catch (e) { setError('Error al optimizar: ' + e.message) }
    finally { setOptimizing(false) }
  }

  return { result, loading, optimizing, optimizeSummary, error, convert, optimize }
}

// ---------------------------------------------------------------------------
function codeBox(t, minHeight) {
  return {
    width: '100%', minHeight: minHeight === 'auto' ? undefined : minHeight,
    padding: 10, borderRadius: 8, boxSizing: 'border-box',
    background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
    color: t.text || '#e2e8f0', fontFamily: 'monospace', fontSize: 12,
    lineHeight: 1.5, resize: 'vertical', outline: 'none', whiteSpace: 'pre',
    overflowX: 'auto',
  }
}

function btn(t, kind, disabled) {
  const base = {
    padding: '7px 14px', borderRadius: 8, fontSize: 12.5, fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer', border: '1px solid transparent',
    whiteSpace: 'nowrap',
  }
  if (kind === 'primary') return { ...base, background: disabled ? (t.border || '#334155') : (t.accent || '#6366f1'), color: '#fff' }
  if (kind === 'accent') return { ...base, background: '#14b8a620', border: '1px solid #14b8a640', color: '#2dd4bf' }
  if (kind === 'secondary') return { ...base, background: '#f59e0b20', border: '1px solid #f59e0b40', color: '#fbbf24' }
  return { ...base, background: 'transparent', border: `1px solid ${t.border || '#334155'}`, color: t.muted || '#94a3b8' }
}
