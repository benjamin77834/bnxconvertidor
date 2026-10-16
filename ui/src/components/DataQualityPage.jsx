import { useState, useEffect, useCallback } from 'react'
import { COMPILE_URL } from '../config'

// Base del API local (quita el sufijo /compile para armar /quality/*).
const API_BASE = COMPILE_URL.replace(/\/compile$/, '')
const COMPARE_URL = `${API_BASE}/quality/compare`
const LIST_URL = `${API_BASE}/quality/list`
const GET_URL = `${API_BASE}/quality/get`
const DOWNLOAD_URL = (id, fmt) => `${API_BASE}/quality/download?id=${encodeURIComponent(id)}&fmt=${fmt}`

const GRADE_COLOR = { A: '#16a34a', B: '#65a30d', C: '#d97706', D: '#dc2626' }

function GradeBadge({ letter }) {
  const c = GRADE_COLOR[letter] || '#64748b'
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      minWidth: 40, height: 40, padding: '0 10px', borderRadius: 10, fontWeight: 800,
      fontSize: 22, background: c + '22', color: c, border: `2px solid ${c}`,
    }}>{letter || '?'}</span>
  )
}

// Lee un File como texto (lo mandamos como content; para CSV es lo natural).
function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(r.result)
    r.onerror = () => reject(r.error)
    r.readAsText(file)
  })
}
// Lee un File como base64 (para parquet u otros binarios).
function readFileAsB64(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => {
      const s = String(r.result)
      resolve(s.slice(s.indexOf(',') + 1))
    }
    r.onerror = () => reject(r.error)
    r.readAsDataURL(file)
  })
}

function DropFile({ label, file, onPick, theme }) {
  const t = theme || {}
  return (
    <label style={{
      flex: 1, minWidth: 220, cursor: 'pointer',
      border: `1px dashed ${t.border || '#334155'}`, borderRadius: 10, padding: 14,
      background: t.codeBg || '#081220', display: 'flex', flexDirection: 'column', gap: 6,
    }}>
      <span style={{ fontSize: 12, fontWeight: 700, color: t.text || '#e2e8f0' }}>{label}</span>
      <span style={{ fontSize: 12, color: file ? '#22c55e' : (t.muted || '#94a3b8') }}>
        {file ? `✓ ${file.name} (${(file.size / 1024).toFixed(1)} KB)` : 'Clic para elegir CSV / Parquet'}
      </span>
      <input type="file" accept=".csv,.tsv,.txt,.parquet" style={{ display: 'none' }}
        onChange={e => onPick(e.target.files?.[0] || null)} />
    </label>
  )
}

export default function DataQualityPage({ theme }) {
  const t = theme || {}
  const [name, setName] = useState('')
  const [keyCol, setKeyCol] = useState('')
  const [tol, setTol] = useState(5)
  const [fileA, setFileA] = useState(null)
  const [fileB, setFileB] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [report, setReport] = useState(null)
  const [history, setHistory] = useState([])

  const loadHistory = useCallback(async () => {
    try {
      const res = await fetch(LIST_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
      })
      const data = await res.json()
      setHistory(data.reports || [])
    } catch (e) { /* silencioso: el historial es best-effort */ }
  }, [])

  useEffect(() => { loadHistory() }, [loadHistory])

  const buildSide = async (file) => {
    const isBin = /\.parquet$/i.test(file.name)
    if (isBin) return { filename: file.name, content_b64: await readFileAsB64(file) }
    return { filename: file.name, content: await readFileAsText(file) }
  }

  const compare = async () => {
    if (!fileA || !fileB) { setError('Sube los dos datasets: A (Ab Initio) y B (convertidor).'); return }
    setLoading(true); setError(''); setReport(null)
    try {
      const body = {
        name: name.trim() || 'comparacion',
        key: keyCol.trim() || undefined,
        tol_pct: Number(tol) || 5,
        a: await buildSide(fileA),
        b: await buildSide(fileB),
      }
      const res = await fetch(COMPARE_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if (!res.ok || data.error) { setError(data.error || `HTTP ${res.status}`); return }
      setReport(data)
      loadHistory()
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const reopen = async (id) => {
    setLoading(true); setError('')
    try {
      const res = await fetch(GET_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id }),
      })
      const data = await res.json()
      if (!res.ok || data.error) { setError(data.error || `HTTP ${res.status}`); return }
      setReport(data)
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const card = {
    background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 16,
  }
  const v = report?.verdict || {}
  const cols = report?.columns || []
  const kc = report?.key_compare

  const dlBtn = (id, fmt, label, color) => (
    <a href={DOWNLOAD_URL(id, fmt)} target="_blank" rel="noreferrer"
      style={{
        padding: '6px 12px', borderRadius: 8, fontSize: 12, fontWeight: 700,
        textDecoration: 'none', background: color + '22', color, border: `1px solid ${color}55`,
      }}>{label}</a>
  )

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 22, color: t.text || '#e2e8f0' }}>⚖️ Comparador de calidad de datos</h2>
        <p style={{ margin: '4px 0 0', fontSize: 13, color: t.muted || '#94a3b8' }}>
          Compara la salida <b>A (baseline Ab Initio)</b> contra la salida <b>B (convertidor)</b>: media,
          varianza, percentiles y % de nulos por columna, con veredicto A–D. Guarda el reporte en el storage
          y permite reimprimirlo y bajarlo en HTML / CSV / JSON.
        </p>
      </div>

      {/* Entrada */}
      <div style={{ ...card, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <DropFile label="📄 Dataset A — Ab Initio (baseline)" file={fileA} onPick={setFileA} theme={t} />
          <DropFile label="📄 Dataset B — Convertidor" file={fileB} onPick={setFileB} theme={t} />
        </div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 180 }}>
            <label style={{ fontSize: 11, color: t.muted || '#94a3b8' }}>Nombre del reporte</label>
            <input value={name} onChange={e => setName(e.target.value)}
              placeholder="p.ej. settlement_oct"
              style={inputStyle(t)} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 140 }}>
            <label style={{ fontSize: 11, color: t.muted || '#94a3b8' }}>Columna llave (opcional)</label>
            <input value={keyCol} onChange={e => setKeyCol(e.target.value)}
              placeholder="p.ej. id" style={inputStyle(t)} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, width: 120 }}>
            <label style={{ fontSize: 11, color: t.muted || '#94a3b8' }}>Tolerancia %</label>
            <input type="number" value={tol} min={0} step={0.5}
              onChange={e => setTol(e.target.value)} style={inputStyle(t)} />
          </div>
          <button onClick={compare} disabled={loading}
            style={{
              padding: '10px 20px', borderRadius: 8, fontSize: 13, fontWeight: 700,
              cursor: loading ? 'wait' : 'pointer', background: '#6366f1', color: '#fff', border: 'none',
            }}>{loading ? '⏳ Comparando...' : '⚖️ Comparar'}</button>
        </div>
        {error && <div style={{ fontSize: 12, color: '#f87171' }}>⚠️ {error}</div>}
      </div>

      {/* Resultado */}
      {report && (
        <>
          <div style={{ ...card, display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
            <GradeBadge letter={v.grade} />
            <div style={{ display: 'flex', gap: 22, flexWrap: 'wrap' }}>
              <Kpi t={t} label="Calidad" value={`${v.quality_pct ?? 0}%`} />
              <Kpi t={t} label="Columnas OK" value={`${v.columns_ok ?? 0}/${v.columns_total ?? 0}`} />
              <Kpi t={t} label="Con drift" value={v.columns_drift ?? 0}
                color={v.columns_drift ? '#f97316' : undefined} />
              <Kpi t={t} label="Filas A / B" value={`${v.rows_a ?? 0} / ${v.rows_b ?? 0}`} />
            </div>
            {report.id && (
              <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
                {dlBtn(report.id, 'html', '⬇️ HTML', '#6366f1')}
                {dlBtn(report.id, 'csv', '⬇️ CSV', '#16a34a')}
                {dlBtn(report.id, 'json', '⬇️ JSON', '#64748b')}
              </div>
            )}
          </div>

          {(v.only_in_a?.length > 0 || v.only_in_b?.length > 0) && (
            <div style={{ ...card, borderColor: '#dc2626', fontSize: 12, color: '#f87171' }}>
              {v.only_in_a?.length > 0 && <div>Columnas solo en A: {v.only_in_a.join(', ')}</div>}
              {v.only_in_b?.length > 0 && <div>Columnas solo en B: {v.only_in_b.join(', ')}</div>}
            </div>
          )}

          {/* Tabla por columna */}
          <div style={{ ...card, overflowX: 'auto' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0', marginBottom: 8 }}>
              Comparación por columna
            </div>
            <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12 }}>
              <thead>
                <tr style={{ color: t.muted || '#94a3b8', textAlign: 'left' }}>
                  {['Columna', 'Estado', 'media A', 'media B', 'Δ media', 'stdev A', 'stdev B', 'p50 A', 'p50 B', 'nulos A%', 'nulos B%']
                    .map(h => <th key={h} style={{ padding: '6px 8px', borderBottom: `1px solid ${t.border || '#334155'}` }}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {cols.map((e, i) => {
                  const a = e.A || {}, b = e.B || {}, d = e.diff || {}
                  const ok = e.status === 'ok'
                  const sc = ok ? '#22c55e' : '#ef4444'
                  return (
                    <tr key={i} style={{ borderBottom: `1px solid ${(t.border || '#334155')}44` }}>
                      <td style={cellStyle(t)}><b>{e.column}</b> {!e.numeric && <span style={{ color: t.dim || '#64748b' }}>(cat)</span>}</td>
                      <td style={{ ...cellStyle(t), color: sc, fontWeight: 700 }}>{ok ? 'OK' : 'DRIFT'}</td>
                      <td style={cellStyle(t)}>{fmt(a.mean)}</td>
                      <td style={cellStyle(t)}>{fmt(b.mean)}</td>
                      <td style={{ ...cellStyle(t), color: (d.mean_pct ?? 0) > tol ? '#f97316' : (t.text || '#e2e8f0') }}>
                        {d.mean_pct != null ? `${d.mean_pct}%` : '—'}
                      </td>
                      <td style={cellStyle(t)}>{fmt(a.stdev)}</td>
                      <td style={cellStyle(t)}>{fmt(b.stdev)}</td>
                      <td style={cellStyle(t)}>{fmt(a.p50)}</td>
                      <td style={cellStyle(t)}>{fmt(b.p50)}</td>
                      <td style={cellStyle(t)}>{a.null_pct != null ? `${a.null_pct}%` : '—'}</td>
                      <td style={cellStyle(t)}>{b.null_pct != null ? `${b.null_pct}%` : '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Apareo por llave */}
          {kc && (
            <div style={{ ...card, overflowX: 'auto' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0', marginBottom: 6 }}>
                Apareo por llave: <code>{kc.key}</code>
              </div>
              <div style={{ fontSize: 12, color: t.muted || '#94a3b8', marginBottom: 8 }}>
                Filas apareadas: <b style={{ color: t.text || '#e2e8f0' }}>{kc.matched_rows}</b> (A={kc.rows_a}, B={kc.rows_b})
              </div>
              <table style={{ borderCollapse: 'collapse', width: '100%', maxWidth: 420, fontSize: 12 }}>
                <thead><tr style={{ color: t.muted || '#94a3b8', textAlign: 'left' }}>
                  <th style={{ padding: '6px 8px' }}>Columna</th><th style={{ padding: '6px 8px' }}>% celdas idénticas</th>
                </tr></thead>
                <tbody>
                  {(kc.columns || []).map((c, i) => (
                    <tr key={i} style={{ borderBottom: `1px solid ${(t.border || '#334155')}44` }}>
                      <td style={cellStyle(t)}>{c.column}</td>
                      <td style={{ ...cellStyle(t), color: (c.match_pct ?? 0) >= 95 ? '#22c55e' : '#f97316', fontWeight: 700 }}>
                        {c.match_pct != null ? `${c.match_pct}%` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* Historial */}
      <div style={{ ...card }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0' }}>
            📜 Historial de reportes ({history.length})
          </span>
          <button onClick={loadHistory} style={{
            padding: '4px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: 'transparent', color: t.muted || '#94a3b8', border: `1px solid ${t.border || '#334155'}`,
          }}>↻ Refrescar</button>
        </div>
        {history.length === 0 && (
          <span style={{ fontSize: 12, color: t.muted || '#94a3b8' }}>Aún no hay reportes guardados.</span>
        )}
        {history.length > 0 && (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12 }}>
              <thead>
                <tr style={{ color: t.muted || '#94a3b8', textAlign: 'left' }}>
                  {['', 'Nombre', 'Fecha', 'Calidad', 'Columnas', 'A → B', 'Acciones'].map((h, i) =>
                    <th key={i} style={{ padding: '6px 8px', borderBottom: `1px solid ${t.border || '#334155'}` }}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.id} style={{ borderBottom: `1px solid ${(t.border || '#334155')}44` }}>
                    <td style={cellStyle(t)}><GradeBadgeSmall letter={h.grade} /></td>
                    <td style={cellStyle(t)}><b>{h.name || h.id}</b></td>
                    <td style={{ ...cellStyle(t), color: t.dim || '#64748b' }}>{(h.generated_at || '').replace('T', ' ')}</td>
                    <td style={cellStyle(t)}>{h.quality_pct ?? '—'}%</td>
                    <td style={cellStyle(t)}>{h.columns_total ?? '—'}{h.columns_drift ? ` (${h.columns_drift} drift)` : ''}</td>
                    <td style={{ ...cellStyle(t), color: t.dim || '#64748b' }}>{h.source_a} → {h.source_b}</td>
                    <td style={cellStyle(t)}>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        <button onClick={() => reopen(h.id)} style={{
                          padding: '4px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                          background: '#6366f122', color: '#818cf8', border: '1px solid #6366f155',
                        }}>👁 Abrir</button>
                        {dlBtn(h.id, 'html', 'HTML', '#6366f1')}
                        {dlBtn(h.id, 'csv', 'CSV', '#16a34a')}
                        {dlBtn(h.id, 'json', 'JSON', '#64748b')}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function GradeBadgeSmall({ letter }) {
  const c = GRADE_COLOR[letter] || '#64748b'
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      width: 24, height: 24, borderRadius: '50%', fontWeight: 800, fontSize: 12,
      background: c + '22', color: c, border: `1.5px solid ${c}`,
    }}>{letter || '?'}</span>
  )
}

function Kpi({ t, label, value, color }) {
  return (
    <span style={{ display: 'inline-flex', flexDirection: 'column', gap: 2 }}>
      <span style={{ fontSize: 11, color: t.muted || '#94a3b8' }}>{label}</span>
      <b style={{ fontSize: 20, color: color || (t.text || '#e2e8f0') }}>{value}</b>
    </span>
  )
}

function fmt(x) {
  if (x == null || x === '') return '—'
  if (typeof x === 'number') return Number.isInteger(x) ? x : x.toFixed(2)
  return String(x)
}

function inputStyle(t) {
  return {
    padding: '8px 10px', borderRadius: 8, fontSize: 13,
    background: (t.codeBg || '#081220'), border: `1px solid ${t.border || '#334155'}`,
    color: t.text || '#e2e8f0', outline: 'none',
  }
}
function cellStyle(t) {
  return { padding: '6px 8px', color: t.text || '#e2e8f0', whiteSpace: 'nowrap' }
}
