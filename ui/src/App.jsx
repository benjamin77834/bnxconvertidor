import React, { useState } from 'react'
import FileUpload from './components/FileUpload'
import DagViewer from './components/DagViewer'

const s = {
  app: { display: 'flex', flexDirection: 'column', height: '100vh' },
  header: {
    padding: '16px 24px', background: '#1e2433',
    borderBottom: '1px solid #334155',
    display: 'flex', alignItems: 'center', gap: 16,
  },
  title: { fontSize: 18, fontWeight: 700, color: '#e2e8f0' },
  badge: {
    fontSize: 11, padding: '2px 8px', borderRadius: 99,
    background: '#6366f120', color: '#818cf8', border: '1px solid #6366f140'
  },
  body: { display: 'flex', flex: 1, overflow: 'hidden' },
  sidebar: {
    width: 320, padding: 20, background: '#161b27',
    borderRight: '1px solid #334155', display: 'flex',
    flexDirection: 'column', gap: 20, overflowY: 'auto',
  },
  main: { flex: 1, position: 'relative' },
  section: { display: 'flex', flexDirection: 'column', gap: 8 },
  sectionTitle: { fontSize: 12, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 1 },
  msgBox: (type) => ({
    background: type === 'error' ? '#7f1d1d30' : '#78350f30',
    border: `1px solid ${type === 'error' ? '#ef444440' : '#f59e0b40'}`,
    borderRadius: 6, padding: '8px 12px', fontSize: 12,
    color: type === 'error' ? '#fca5a5' : '#fcd34d',
    maxHeight: 200, overflowY: 'auto',
  }),
  code: {
    background: '#0f1117', border: '1px solid #334155',
    borderRadius: 6, padding: 12, fontSize: 11,
    color: '#94a3b8', maxHeight: 300, overflowY: 'auto',
    fontFamily: 'monospace', whiteSpace: 'pre',
  },
  legend: { display: 'flex', flexWrap: 'wrap', gap: 8 },
  dot: (color) => ({
    width: 10, height: 10, borderRadius: '50%',
    background: color, display: 'inline-block', marginRight: 4,
  }),
  legendItem: { fontSize: 12, color: '#94a3b8', display: 'flex', alignItems: 'center' },
  empty: {
    position: 'absolute', inset: 0, display: 'flex',
    alignItems: 'center', justifyContent: 'center',
    color: '#334155', fontSize: 14,
  }
}

const LEGEND = [
  { type: 'SOURCE',    color: '#22c55e' },
  { type: 'TRANSFORM', color: '#6366f1' },
  { type: 'JOIN',      color: '#f59e0b' },
  { type: 'SINK',      color: '#ef4444' },
]

export default function App() {
  const [files, setFiles]   = useState({ mp: null, xfr: null, dml: null })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const compile = async () => {
    setLoading(true)
    const form = new FormData()
    form.append('mp', files.mp)
    if (files.xfr) form.append('xfr', files.xfr)
    if (files.dml) form.append('dml', files.dml)

    try {
      const res = await fetch('/compile', { method: 'POST', body: form })
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setResult({ errors: [`Network error: ${e.message}`], warnings: [], nodes: [], edges: [] })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={s.app}>
      <header style={s.header}>
        <span style={s.title}>🚀 BNX Compiler</span>
        <span style={s.badge}>V54</span>
        {result && (
          <span style={s.badge}>
            {result.nodes?.length} nodes · {result.edges?.length} edges
          </span>
        )}
      </header>

      <div style={s.body}>
        <aside style={s.sidebar}>
          <FileUpload files={files} setFiles={setFiles} onCompile={compile} loading={loading} />

          {/* Legend */}
          <div style={s.section}>
            <span style={s.sectionTitle}>Legend</span>
            <div style={s.legend}>
              {LEGEND.map(l => (
                <span key={l.type} style={s.legendItem}>
                  <span style={s.dot(l.color)} />{l.type}
                </span>
              ))}
            </div>
          </div>

          {/* Subgraphs */}
          {result?.subgraphs?.length > 0 && (
            <div style={s.section}>
              <span style={s.sectionTitle}>Subgraphs ({result.subgraphs.length})</span>
              {result.subgraphs.map(sg => (
                <span key={sg} style={{ fontSize: 12, color: '#94a3b8' }}>• {sg}</span>
              ))}
            </div>
          )}

          {/* Warnings */}
          {result?.warnings?.length > 0 && (
            <div style={s.section}>
              <span style={s.sectionTitle}>Warnings</span>
              <div style={s.msgBox('warning')}>
                {result.warnings.map((w, i) => <div key={i}>{w}</div>)}
              </div>
            </div>
          )}

          {/* Errors */}
          {result?.errors?.length > 0 && (
            <div style={s.section}>
              <span style={s.sectionTitle}>Errors</span>
              <div style={s.msgBox('error')}>
                {result.errors.map((e, i) => <div key={i}>{e}</div>)}
              </div>
            </div>
          )}

          {/* Generated code */}
          {result?.code && (
            <div style={s.section}>
              <span style={s.sectionTitle}>Generated Code</span>
              <pre style={s.code}>{result.code}</pre>
            </div>
          )}
        </aside>

        <main style={s.main}>
          {result?.nodes?.length > 0
            ? <DagViewer data={result} />
            : <div style={s.empty}>Upload a .mp file and click Compile to visualize the DAG</div>
          }
        </main>
      </div>
    </div>
  )
}
