import { useState, useRef } from 'react'
import { COMPILE_URL } from '../config'

// Panel reutilizable de ANALISIS DE CALIDAD (estilo Sonar) con doble pantalla:
// izquierda editor editable (lineas marcadas en naranja), derecha
// recomendaciones/errores clicables que saltan a la linea. Solo recomendaciones,
// no cambia el codigo salvo que el usuario lo edite.
//
// Props:
//   theme      -> tema
//   code       -> codigo inicial a analizar (del Compiler, py2spark, etc.)
//   onApply(c) -> opcional; si se pasa, muestra "Aplicar al código" con el editado
const ANALYZE_URL = COMPILE_URL.replace(/\/compile$/, '/analyze')
const SV = { critical: '#ef4444', major: '#f97316', minor: '#f59e0b', info: '#64748b' }

export default function CodeQualityPanel({ theme, code = '', onApply }) {
  const t = theme || {}
  const [open, setOpen] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [edited, setEdited] = useState('')
  const [dirty, setDirty] = useState(false)
  const taRef = useRef(null)

  const effective = dirty ? edited : (code || '')

  const analyze = async () => {
    if (!(effective || '').trim()) { alert('No hay código para analizar.'); return }
    setAnalyzing(true)
    try {
      const res = await fetch(ANALYZE_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: effective }),
      })
      const data = await res.json()
      if (data.error) { alert('No se pudo analizar: ' + data.error); return }
      setAnalysis(data); setOpen(true)
    } catch (e) {
      alert('No se pudo analizar: ' + e.message)
    } finally { setAnalyzing(false) }
  }

  const jumpToLine = (lineNo) => {
    const ta = taRef.current
    if (!ta) return
    const arr = (ta.value || '').split('\n')
    let pos = 0
    for (let i = 0; i < Math.min(lineNo - 1, arr.length); i++) pos += arr[i].length + 1
    const end = pos + (arr[lineNo - 1] ? arr[lineNo - 1].length : 0)
    ta.focus()
    try { ta.setSelectionRange(pos, end) } catch { /* ignore */ }
    const lineH = ta.scrollHeight / Math.max(arr.length, 1)
    ta.scrollTop = Math.max(0, (lineNo - 3) * lineH)
  }

  const byLine = {}
  if (analysis) for (const f of (analysis.findings || [])) {
    (byLine[f.line] = byLine[f.line] || []).push(f)
  }
  const s = analysis?.summary || {}
  const lines = (effective || '').split('\n')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
        <button onClick={analyze} disabled={analyzing || !(code || '').trim()}
          title="Analiza la calidad (estilo Sonar) y permite editar; marca en naranja las recomendaciones. NO cambia nada salvo que edites."
          style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12, fontWeight: 700,
            cursor: (analyzing || !(code || '').trim()) ? 'not-allowed' : 'pointer',
            background: !(code || '').trim() ? (t.border || '#334155') : '#f97316', color: '#fff', border: 'none' }}>
          {analyzing ? '⏳ Analizando...' : '🟠 Analizar / Editar calidad'}
        </button>
        {open && (
          <span style={{ fontSize: 11, color: t.dim }}>
            {s.total || 0} hallazgo(s): {s.critical || 0} críticos, {s.major || 0} mayores, {s.minor || 0} menores, {s.info || 0} info
          </span>
        )}
      </div>

      {open && analysis && (
        <div style={{ background: '#f9731610', borderRadius: 8, padding: 12,
          border: '1px solid #f9731640', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6 }}>
            <button onClick={analyze} disabled={analyzing}
              style={{ padding: '4px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                background: '#f9731620', border: '1px solid #f97316', color: '#fb923c', fontWeight: 600 }}>
              {analyzing ? '⏳...' : '🔄 Re-analizar'}
            </button>
            {onApply && dirty && (
              <button onClick={() => onApply(edited)}
                title="Reemplaza el código mostrado por el editado"
                style={{ padding: '4px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                  background: '#22c55e20', border: '1px solid #22c55e', color: '#22c55e', fontWeight: 600 }}>
                ✓ Aplicar al código
              </button>
            )}
            <button onClick={() => setOpen(false)}
              style={{ padding: '4px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                background: 'transparent', border: `1px solid ${t.border || '#334155'}`, color: t.dim }}>
              ✕ cerrar
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {/* IZQUIERDA: editor con resaltado naranja */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span style={{ fontSize: 11, color: t.dim }}>Código {dirty ? '(editado)' : ''} — edita y pulsa 🔄 Re-analizar</span>
              <div style={{ position: 'relative', border: '1px solid #f9731640', borderRadius: 6, overflow: 'hidden' }}>
                <div aria-hidden style={{ position: 'absolute', inset: 0, margin: 0, padding: '10px 10px 10px 44px',
                  fontFamily: 'monospace', fontSize: 11.5, lineHeight: '1.5', whiteSpace: 'pre',
                  pointerEvents: 'none', overflow: 'hidden', color: 'transparent' }}>
                  {lines.map((ln, idx) => (
                    <div key={idx} style={{ background: byLine[idx + 1] ? '#f9731630' : 'transparent' }}>{ln || ' '}</div>
                  ))}
                </div>
                <textarea ref={taRef} value={effective}
                  onChange={e => { setEdited(e.target.value); setDirty(true) }}
                  spellCheck={false}
                  style={{ position: 'relative', width: '100%', minHeight: 320, resize: 'vertical',
                    padding: '10px 10px 10px 44px', margin: 0, border: 'none', outline: 'none',
                    background: 'transparent', color: t.text || '#e2e8f0',
                    fontFamily: 'monospace', fontSize: 11.5, lineHeight: '1.5', whiteSpace: 'pre' }} />
              </div>
            </div>

            {/* DERECHA: recomendaciones clicables */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span style={{ fontSize: 11, color: t.dim }}>Recomendaciones / errores (clic salta a la línea)</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 320, overflow: 'auto',
                border: '1px solid #33415530', borderRadius: 6, padding: 8, background: t.codeBg || '#081220' }}>
                {(analysis.findings || []).length === 0
                  ? <div style={{ fontSize: 12, color: '#22c55e' }}>✅ Sin recomendaciones: el código se ve limpio.</div>
                  : analysis.findings.map((f, i) => (
                    <div key={i} onClick={() => jumpToLine(f.line)} title="Ir a esta línea"
                      style={{ fontSize: 11.5, color: t.text || '#e2e8f0', lineHeight: 1.45, cursor: 'pointer',
                        borderLeft: `3px solid ${SV[f.severity] || '#f59e0b'}`, paddingLeft: 8, borderRadius: 3 }}
                      onMouseEnter={e => { e.currentTarget.style.background = '#f9731615' }}
                      onMouseLeave={e => { e.currentTarget.style.background = 'transparent' }}>
                      <div>
                        <span style={{ color: SV[f.severity] || '#f59e0b', fontWeight: 700 }}>↪ L{f.line}</span>{' '}
                        <span style={{ color: t.dim, fontSize: 10 }}>[{f.category}/{f.severity}]</span>
                      </div>
                      <div style={{ color: t.muted || '#94a3b8' }}>{f.message}</div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
