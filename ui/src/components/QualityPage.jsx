import { useState } from 'react'
import { COMPILE_URL } from '../config'

const ANALYZE_URL = COMPILE_URL.replace(/\/compile$/, '/analyze')

// Colores por tipo/severidad estilo SonarQube.
const TYPE_META = {
  BUG: { label: 'Bugs', icon: '🐞', color: '#ef4444' },
  VULNERABILITY: { label: 'Vulnerabilidades', icon: '🔓', color: '#f97316' },
  SECURITY_HOTSPOT: { label: 'Security Hotspots', icon: '🔥', color: '#eab308' },
  CODE_SMELL: { label: 'Code Smells', icon: '🧹', color: '#6366f1' },
}
const SEV_COLOR = {
  BLOCKER: '#dc2626', CRITICAL: '#f97316', MAJOR: '#eab308',
  MINOR: '#38bdf8', INFO: '#94a3b8',
}
const RATING_COLOR = { A: '#22c55e', B: '#84cc16', C: '#eab308', D: '#f97316', E: '#ef4444' }

function RatingBadge({ letter, theme }) {
  const c = RATING_COLOR[letter] || '#94a3b8'
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      width: 30, height: 30, borderRadius: '50%', fontWeight: 800, fontSize: 15,
      background: c + '22', color: c, border: `2px solid ${c}`,
    }}>{letter}</span>
  )
}

export default function QualityPage({ theme, compiledCode = '' }) {
  const t = theme || {}
  const [code, setCode] = useState(compiledCode || '')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const analyze = async () => {
    if (!code.trim()) { setError('Pega código o compila un grafo primero.'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const res = await fetch(ANALYZE_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
      const data = await res.json()
      if (data.error) { setError(data.error); return }
      setResult(data)
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const card = {
    background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 16,
  }
  const sonar = result?.sonar
  const findings = result?.findings || []

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 22, color: t.text || '#e2e8f0' }}>🛡️ Calidad del código (estilo SonarQube)</h2>
        <p style={{ margin: '4px 0 0', fontSize: 13, color: t.muted || '#94a3b8' }}>
          Analiza el PySpark/Python por reglas (bugs, vulnerabilidades, hotspots, code smells) con
          Quality Gate, deuda técnica y ratings A–E. No modifica el código.
        </p>
      </div>

      {/* Entrada */}
      <div style={{ ...card, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: t.text || '#e2e8f0' }}>Código a analizar</span>
          <button onClick={analyze} disabled={loading}
            style={{
              padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 700,
              cursor: loading ? 'wait' : 'pointer',
              background: '#6366f1', color: '#fff', border: 'none',
            }}>{loading ? '⏳ Analizando...' : '🔎 Analizar'}</button>
        </div>
        <textarea value={code} onChange={e => setCode(e.target.value)}
          placeholder="Pega aquí el PySpark/Python (o compila un grafo y vuelve: llega el código del Compiler)."
          style={{
            width: '100%', minHeight: 140, maxHeight: 260, padding: 10, borderRadius: 8,
            background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
            color: t.text || '#e2e8f0', fontSize: 12, fontFamily: 'monospace',
            resize: 'vertical', outline: 'none',
          }} />
        {error && <div style={{ fontSize: 12, color: '#f87171' }}>⚠️ {error}</div>}
      </div>

      {sonar && (
        <>
          {/* Quality Gate */}
          <div style={{
            ...card, borderWidth: 2,
            borderColor: sonar.quality_gate === 'PASSED' ? '#22c55e' : '#ef4444',
            display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
          }}>
            <span style={{
              fontSize: 15, fontWeight: 800, padding: '6px 16px', borderRadius: 8,
              background: (sonar.quality_gate === 'PASSED' ? '#22c55e' : '#ef4444') + '22',
              color: sonar.quality_gate === 'PASSED' ? '#22c55e' : '#ef4444',
              border: `1px solid ${sonar.quality_gate === 'PASSED' ? '#22c55e' : '#ef4444'}`,
            }}>
              Quality Gate: {sonar.quality_gate === 'PASSED' ? '✓ PASSED' : '✗ FAILED'}
            </span>
            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', fontSize: 12 }}>
              {(sonar.quality_gate_conditions || []).map((c, i) => (
                <span key={i} style={{ color: c.passed ? '#22c55e' : '#ef4444' }}>
                  {c.passed ? '✓' : '✗'} {c.metric} {c.op} {c.threshold} (actual: {c.actual})
                </span>
              ))}
            </div>
          </div>

          {/* Tarjetas de métricas */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12 }}>
            {[
              { k: 'BUG', count: sonar.counts.bugs, rating: sonar.ratings.reliability },
              { k: 'VULNERABILITY', count: sonar.counts.vulnerabilities, rating: sonar.ratings.security },
              { k: 'SECURITY_HOTSPOT', count: sonar.counts.security_hotspots, rating: sonar.ratings.security_review },
              { k: 'CODE_SMELL', count: sonar.counts.code_smells, rating: sonar.ratings.maintainability },
            ].map(({ k, count, rating }) => {
              const m = TYPE_META[k]
              return (
                <div key={k} style={{ ...card, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 12, color: t.muted || '#94a3b8' }}>{m.icon} {m.label}</span>
                    <RatingBadge letter={rating} theme={t} />
                  </div>
                  <span style={{ fontSize: 28, fontWeight: 800, color: m.color }}>{count}</span>
                </div>
              )
            })}
          </div>

          {/* Deuda técnica */}
          <div style={{ ...card, display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 20 }}>⏱️</span>
            <span style={{ fontSize: 13, color: t.muted || '#94a3b8' }}>Deuda técnica estimada:</span>
            <span style={{ fontSize: 16, fontWeight: 800, color: t.text || '#e2e8f0' }}>{sonar.technical_debt}</span>
          </div>

          {/* Lista de issues */}
          <div style={{ ...card, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0', marginBottom: 6 }}>
              Issues ({findings.length})
            </div>
            {findings.length === 0 && (
              <span style={{ fontSize: 12, color: '#22c55e' }}>✓ Sin hallazgos — el código luce limpio.</span>
            )}
            {findings.map((f, i) => {
              const m = TYPE_META[f.type] || TYPE_META.CODE_SMELL
              const sc = SEV_COLOR[f.sonar_severity] || '#94a3b8'
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 10, padding: '8px 4px',
                  borderBottom: `1px solid ${(t.border || '#334155')}44`, fontSize: 12,
                }}>
                  <span title={m.label} style={{ fontSize: 14 }}>{m.icon}</span>
                  <span style={{
                    fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 3,
                    background: sc + '22', color: sc, border: `1px solid ${sc}55`, whiteSpace: 'nowrap',
                  }}>{f.sonar_severity}</span>
                  <span style={{ fontFamily: 'monospace', color: t.dim || '#64748b', whiteSpace: 'nowrap' }}>
                    L{f.line} · {f.rule_key}
                  </span>
                  <span style={{ color: t.text || '#e2e8f0', flex: 1 }}>{f.message}</span>
                  <span style={{ color: t.dim || '#64748b', whiteSpace: 'nowrap' }}>{f.effort_min}min</span>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
