import { useState, useCallback, useRef } from 'react'
import FileUpload from './components/FileUpload'
import DagViewer from './components/DagViewer'
import MetricsPage from './components/MetricsPage'
import DesignerPage from './components/DesignerPage'
import { COMPILE_URL } from './config'

// ── Themes ──────────────────────────────────────────────────
const dark = {
  bg: '#0f1117', sidebar: '#161b27', header: '#1e2433',
  card: '#1e2433', border: '#334155', text: '#e2e8f0',
  muted: '#94a3b8', dim: '#64748b', codeBg: '#0d1017',
  accent: '#6366f1', accentBg: '#6366f120', accentBorder: '#6366f140',
  flowBg: '#1e2433',
}
const light = {
  bg: '#f8fafc', sidebar: '#ffffff', header: '#ffffff',
  card: '#f1f5f9', border: '#e2e8f0', text: '#1e293b',
  muted: '#64748b', dim: '#94a3b8', codeBg: '#f8fafc',
  accent: '#6366f1', accentBg: '#6366f110', accentBorder: '#6366f130',
  flowBg: '#f1f5f9',
}

const LEGEND = [
  { type: 'SOURCE',    color: '#22c55e', desc: 'Lectura de datos desde S3, DB o archivos' },
  { type: 'TRANSFORM', color: '#6366f1', desc: 'SELECT, WHERE, GROUP BY sobre los datos' },
  { type: 'JOIN',      color: '#f59e0b', desc: 'Combina dos o más datasets por una key' },
  { type: 'DEDUP',     color: '#06b6d4', desc: 'Elimina registros duplicados por key' },
  { type: 'NORMALIZE', color: '#a855f7', desc: 'Expande un registro en múltiples filas' },
  { type: 'LOOKUP',    color: '#ec4899', desc: 'Enriquece con tabla de referencia (broadcast)' },
  { type: 'SINK',      color: '#ef4444', desc: 'Escritura final a S3, DB o archivo' },
]

// ── Helpers ─────────────────────────────────────────────────
function download(content, filename, mime = 'text/plain') {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

export default function App() {
  const [files, setFiles]       = useState({ mp: [], xfr: [], dml: [] })
  const [result, setResult]     = useState(null)
  const [loading, setLoading]   = useState(false)
  const [codeOpen, setCodeOpen] = useState(false)
  const [isDark, setIsDark]     = useState(true)
  const [target, setTarget]     = useState('glue')
  const [page, setPage]         = useState('compiler')
  const dagRef                  = useRef(null)
  const cobolRef                = useRef(null)

  const t = isDark ? dark : light

  const compile = async (selected) => {
    setLoading(true)
    const form = new FormData()
    form.append('mp', selected.mp)
    if (selected.xfr) form.append('xfr', selected.xfr)
    if (selected.dml) form.append('dml', selected.dml)
    form.append('target', target)
    try {
      const res = await fetch(COMPILE_URL, { method: 'POST', body: form })
      const data = await res.json()
      setResult(data)
      if (data.code) setCodeOpen(true)
    } catch (e) {
      setResult({ errors: [`Network error: ${e.message}`], warnings: [], nodes: [], edges: [] })
    } finally { setLoading(false) }
  }

  const downloadCode = useCallback(() => {
    if (result?.code) download(result.code, target === 'spark' ? 'pyspark_job.py' : 'glue_job.py')
  }, [result, target])

  const downloadReport = useCallback(() => {
    if (!result) return
    const counts = {}
    result.nodes.forEach(n => { counts[n.type] = (counts[n.type] || 0) + 1 })
    const acc = result.accuracy || {}

    let report = `BNX CONVERTIDOR - COMPILATION REPORT\n`
    report += `${'='.repeat(50)}\n`
    report += `Generated: ${new Date().toISOString()}\n`
    report += `Target: ${target.toUpperCase()}\n\n`

    report += `GRAPH SUMMARY\n${'-'.repeat(30)}\n`
    report += `Total Nodes: ${result.nodes.length}\n`
    report += `Total Edges: ${result.edges.length}\n`
    report += `Subgraphs: ${result.subgraphs?.length || 0}\n\n`

    report += `NODES BY TYPE\n${'-'.repeat(30)}\n`
    Object.entries(counts).forEach(([type, count]) => {
      report += `  ${type}: ${count}\n`
    })

    report += `\nACCURACY\n${'-'.repeat(30)}\n`
    report += `  Overall: ${acc.overall_accuracy || 0}%\n`
    report += `  Nodes: ${acc.resolved_nodes || 0}/${acc.total_nodes || 0} (${acc.node_accuracy || 0}%)\n`
    report += `  Edges: ${acc.resolved_edges || 0}/${acc.total_edges || 0} (${acc.edge_accuracy || 0}%)\n`
    report += `  Transforms: ${acc.resolved_transforms || 0}/${acc.total_transforms || 0} (${acc.transform_accuracy || 0}%)\n`
    report += `  Joins: ${acc.resolved_joins || 0}/${acc.total_joins || 0} (${acc.join_accuracy || 0}%)\n`

    if (result.warnings?.length) {
      report += `\nWARNINGS (${result.warnings.length})\n${'-'.repeat(30)}\n`
      result.warnings.forEach(w => { report += `  ${w}\n` })
    }
    if (result.errors?.length) {
      report += `\nERRORS (${result.errors.length})\n${'-'.repeat(30)}\n`
      result.errors.forEach(e => { report += `  ${e}\n` })
    }

    report += `\nEXECUTION ORDER\n${'-'.repeat(30)}\n`
    result.nodes.forEach((n, i) => {
      const rule = n.rule || {}
      let detail = ''
      if (rule.select && rule.select !== '*') detail += ` SELECT ${rule.select}`
      if (rule.where) detail += ` WHERE ${rule.where}`
      if (rule.group_by) detail += ` GROUP BY ${Array.isArray(rule.group_by) ? rule.group_by.join(', ') : rule.group_by}`
      if (rule.join_key) detail += ` JOIN ON ${rule.join_key} (${rule.join_type || 'inner'})`
      if (rule.dedup_keys) detail += ` DEDUP BY ${rule.dedup_keys.join(', ')}`
      if (rule.explode_col) detail += ` EXPLODE ${rule.explode_col}`
      if (rule.split_col) detail += ` SPLIT ${rule.split_col}`
      if (rule.lookup_key) detail += ` LOOKUP ON ${rule.lookup_key}`
      report += `  ${i + 1}. ${n.name} (${n.type})${n.subgraph ? ` [${n.subgraph}]` : ''}${detail}\n`
      if (n.parents?.length) report += `     ← ${n.parents.join(', ')}\n`
    })

    if (result.code) {
      report += `\n${'='.repeat(50)}\nGENERATED CODE\n${'='.repeat(50)}\n\n`
      report += result.code
    }

    if (result.generated_mp) {
      report += `\n${'='.repeat(50)}\nGENERATED .MP\n${'='.repeat(50)}\n\n`
      report += result.generated_mp
    }
    if (result.generated_xfr) {
      report += `\n${'='.repeat(50)}\nGENERATED .XFR\n${'='.repeat(50)}\n\n`
      report += result.generated_xfr
    }
    if (result.generated_dml) {
      report += `\n${'='.repeat(50)}\nGENERATED .DML\n${'='.repeat(50)}\n\n`
      report += result.generated_dml
    }

    download(report, 'bnx_report.txt')
  }, [result, target])

  const compileCobol = async (file) => {
    setLoading(true)
    const form = new FormData()
    form.append('cobol', file)
    form.append('target', target)
    try {
      const res = await fetch(COMPILE_URL.replace('/compile', '/cobol'), { method: 'POST', body: form })
      const data = await res.json()
      setResult(data)
      if (data.code) setCodeOpen(true)
    } catch (e) {
      setResult({ errors: [`Network error: ${e.message}`], warnings: [], nodes: [], edges: [] })
    } finally { setLoading(false) }
  }

  const downloadDag = useCallback(() => {
    if (!dagRef.current) return
    const svgEl = dagRef.current.querySelector('.react-flow__viewport')
    if (!svgEl) return
    // Clone the SVG and serialize
    const flowEl = dagRef.current.querySelector('svg.react-flow__edges')
      || dagRef.current.querySelector('svg')
    if (flowEl) {
      const clone = flowEl.cloneNode(true)
      const svgData = new XMLSerializer().serializeToString(clone)
      const blob = new Blob([svgData], { type: 'image/svg+xml' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = 'bnx_dag.svg'; a.click()
      URL.revokeObjectURL(url)
    }
  }, [])

  const msgBox = (type) => ({
    background: type === 'error' ? '#7f1d1d30' : '#78350f30',
    border: `1px solid ${type === 'error' ? '#ef444440' : '#f59e0b40'}`,
    borderRadius: 6, padding: '8px 12px', fontSize: 14,
    color: type === 'error' ? '#fca5a5' : '#fcd34d',
    maxHeight: 200, overflowY: 'auto',
  })

  const iconBtn = {
    padding: '8px 14px', borderRadius: 6, border: `1px solid ${t.border}`,
    background: t.card, color: t.muted, fontSize: 14, cursor: 'pointer',
    display: 'flex', alignItems: 'center', gap: 4,
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: t.bg, color: t.text }}>
      {/* Header */}
      <header style={{
        padding: '12px 24px', background: t.header, borderBottom: `1px solid ${t.border}`,
        display: 'flex', alignItems: 'center', gap: 16,
      }}>
        <span style={{ fontSize: 20, fontWeight: 700 }}>🚀 BNX Compiler</span>
        <span style={{
          fontSize: 13, padding: '3px 10px', borderRadius: 99,
          background: t.accentBg, color: t.accent, border: `1px solid ${t.accentBorder}`,
        }}>V54</span>

        {result && (
          <span style={{
            fontSize: 13, padding: '3px 10px', borderRadius: 99,
            background: t.accentBg, color: t.accent, border: `1px solid ${t.accentBorder}`,
          }}>
            {result.nodes?.length} nodes · {result.edges?.length} edges
          </span>
        )}

        {/* Page tabs */}
        <div style={{ display: 'flex', gap: 4, marginLeft: 8 }}>
          {[
            { id: 'compiler', label: '🔧 Compiler' },
            { id: 'designer', label: '🎨 Designer' },
            { id: 'metrics', label: '📊 Metrics' },
          ].map(tab => (
            <button key={tab.id}
              onClick={() => setPage(tab.id)}
              style={{
                padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
                background: page === tab.id ? t.accent + '20' : 'transparent',
                border: `1px solid ${page === tab.id ? t.accent : 'transparent'}`,
                color: page === tab.id ? t.accent : t.muted,
                fontWeight: page === tab.id ? 600 : 400,
              }}
            >{tab.label}</button>
          ))}
        </div>

        <div style={{ flex: 1 }} />

        {/* Downloads */}
        {result?.code && (
          <button style={iconBtn} onClick={downloadCode}>📥 Code</button>
        )}
        {result?.nodes?.length > 0 && (
          <button style={iconBtn} onClick={downloadDag}>🖼️ DAG</button>
        )}

        {/* Theme toggle */}
        <button
          style={{ ...iconBtn, fontSize: 16, padding: '4px 10px' }}
          onClick={() => setIsDark(d => !d)}
        >
          {isDark ? '☀️' : '🌙'}
        </button>
      </header>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {page === 'metrics' ? (
          <MetricsPage theme={t} />
        ) : page === 'designer' ? (
          <DesignerPage theme={t} />
        ) : (
        <>
        {/* Sidebar */}
        <aside style={{
          width: 360, padding: 24, background: t.sidebar, flexShrink: 0,
          borderRight: `1px solid ${t.border}`, display: 'flex',
          flexDirection: 'column', gap: 20, overflowY: 'auto',
        }}>
          <FileUpload files={files} setFiles={setFiles} onCompile={compile} loading={loading} theme={t} />

          {/* Target selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>Target</span>
            <div style={{ display: 'flex', gap: 8 }}>
              {[
                { id: 'glue', label: '🔧 Glue', desc: 'AWS Glue + GlueContext' },
                { id: 'spark', label: '⚡ PySpark', desc: 'PySpark puro + SparkSession' },
              ].map(opt => (
                <button key={opt.id}
                  onClick={() => setTarget(opt.id)}
                  style={{
                    flex: 1, padding: '8px 12px', borderRadius: 8, cursor: 'pointer',
                    background: target === opt.id ? t.accent + '20' : t.card,
                    border: `2px solid ${target === opt.id ? t.accent : t.border}`,
                    color: target === opt.id ? t.text : t.muted,
                    fontSize: 13, fontWeight: target === opt.id ? 600 : 400,
                    textAlign: 'center',
                  }}
                  title={opt.desc}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* COBOL upload */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>COBOL Migration</span>
            <span style={{ fontSize: 12, color: t.dim }}>Sube un .cbl y se convierte a grafo automáticamente</span>
            <button
              style={{
                padding: '8px 16px', borderRadius: 8, cursor: 'pointer',
                background: t.card, border: `1px dashed ${t.border}`,
                color: t.muted, fontSize: 13,
              }}
              onClick={() => cobolRef.current.click()}
            >📋 Upload .cbl file</button>
            <input ref={cobolRef} type="file" accept=".cbl,.cob,.cobol" hidden
              onChange={(e) => { if (e.target.files[0]) compileCobol(e.target.files[0]); e.target.value = '' }}
            />
          </div>

          {/* Legend */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>Legend</span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {LEGEND.map(l => (
                <div key={l.type} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                  <span style={{
                    width: 12, height: 12, borderRadius: '50%', background: l.color,
                    marginTop: 3, flexShrink: 0,
                  }} />
                  <div>
                    <span style={{ fontSize: 13, color: t.text, fontWeight: 600 }}>{l.type}</span>
                    <div style={{ fontSize: 12, color: t.dim, marginTop: 1 }}>{l.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Subgraphs */}
          {result?.subgraphs?.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>
                Subgraphs ({result.subgraphs.length})
              </span>
              {result.subgraphs.map(sg => (
                <span key={sg} style={{ fontSize: 14, color: t.muted }}>• {sg}</span>
              ))}
            </div>
          )}

          {/* Warnings */}
          {result?.warnings?.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>Warnings</span>
              <div style={msgBox('warning')}>
                {result.warnings.map((w, i) => <div key={i}>{w}</div>)}
              </div>
            </div>
          )}

          {/* Errors */}
          {result?.errors?.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>Errors</span>
              <div style={msgBox('error')}>
                {result.errors.map((e, i) => <div key={i}>{e}</div>)}
              </div>
            </div>
          )}

          {/* Accuracy */}
          {result?.accuracy && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>Accuracy</span>
              <div style={{
                background: t.card, borderRadius: 8, padding: 12,
                border: `1px solid ${t.border}`, display: 'flex', flexDirection: 'column', gap: 8,
              }}>
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    fontSize: 28, fontWeight: 700,
                    color: result.accuracy.overall_accuracy >= 90 ? '#22c55e'
                         : result.accuracy.overall_accuracy >= 70 ? '#f59e0b' : '#ef4444',
                  }}>
                    {result.accuracy.overall_accuracy}%
                  </span>
                  <span style={{ fontSize: 13, color: t.dim }}>overall</span>
                </div>
                {[
                  { label: 'Nodes', val: result.accuracy.node_accuracy, n: result.accuracy.resolved_nodes, t: result.accuracy.total_nodes },
                  { label: 'Edges', val: result.accuracy.edge_accuracy, n: result.accuracy.resolved_edges, t: result.accuracy.total_edges },
                  { label: 'Transforms', val: result.accuracy.transform_accuracy, n: result.accuracy.resolved_transforms, t: result.accuracy.total_transforms },
                  { label: 'Joins', val: result.accuracy.join_accuracy, n: result.accuracy.resolved_joins, t: result.accuracy.total_joins },
                ].map(m => (
                  <div key={m.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 13, color: t.dim, width: 80 }}>{m.label}</span>
                    <div style={{ flex: 1, height: 6, background: t.bg, borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{
                        width: `${m.val}%`, height: '100%', borderRadius: 3,
                        background: m.val >= 90 ? '#22c55e' : m.val >= 70 ? '#f59e0b' : '#ef4444',
                      }} />
                    </div>
                    <span style={{ fontSize: 13, color: t.muted, width: 50, textAlign: 'right' }}>{m.n}/{m.t}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        {/* Main */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Stats bar */}
          {result?.nodes?.length > 0 && (() => {
            const counts = {}
            result.nodes.forEach(n => { counts[n.type] = (counts[n.type] || 0) + 1 })
            const TYPE_COLOR = {
              SOURCE: '#22c55e', TRANSFORM: '#6366f1', XFR: '#6366f1',
              JOIN: '#f59e0b', DEDUP: '#06b6d4', NORMALIZE: '#a855f7',
              LOOKUP: '#ec4899', SINK: '#ef4444',
            }
            return (
              <div style={{
                display: 'flex', gap: 12, padding: '10px 20px', flexWrap: 'wrap',
                background: t.sidebar, borderBottom: `1px solid ${t.border}`,
                alignItems: 'center',
              }}>
                <span style={{
                  fontSize: 15, fontWeight: 700, color: t.text,
                  marginRight: 8,
                }}>
                  {result.nodes.length} nodes · {result.edges.length} edges
                  {result.subgraphs?.length > 0 && ` · ${result.subgraphs.length} subgraphs`}
                </span>
                <span style={{ width: 1, height: 20, background: t.border }} />
                {Object.entries(counts).map(([type, count]) => (
                  <span key={type} style={{
                    display: 'flex', alignItems: 'center', gap: 5,
                    padding: '3px 10px', borderRadius: 6,
                    background: (TYPE_COLOR[type] || '#64748b') + '15',
                    border: `1px solid ${(TYPE_COLOR[type] || '#64748b')}30`,
                    fontSize: 13, color: TYPE_COLOR[type] || '#64748b', fontWeight: 600,
                  }}>
                    <span style={{
                      width: 8, height: 8, borderRadius: '50%',
                      background: TYPE_COLOR[type] || '#64748b',
                    }} />
                    {count} {type}
                  </span>
                ))}
                <span style={{ flex: 1 }} />
                {result.code && (
                  <button onClick={downloadCode} style={{
                    padding: '4px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                    background: t.card, border: `1px solid ${t.border}`, color: t.muted,
                  }}>📥 Code</button>
                )}
                <button onClick={downloadDag} style={{
                  padding: '4px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                  background: t.card, border: `1px solid ${t.border}`, color: t.muted,
                }}>🖼️ DAG</button>
                <button onClick={downloadReport} style={{
                  padding: '4px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                  background: '#6366f115', border: `1px solid #6366f130`, color: '#818cf8',
                }}>📋 Full Report</button>
              </div>
            )
          })()}
          <div ref={dagRef} style={{ flex: 1, position: 'relative', minHeight: 0 }}>
            {result?.nodes?.length > 0
              ? <DagViewer data={result} theme={t} />
              : <div style={{
                  position: 'absolute', inset: 0, display: 'flex',
                  alignItems: 'center', justifyContent: 'center', color: t.dim, fontSize: 14,
                }}>Upload a .mp file and click Compile to visualize the DAG</div>
            }
          </div>

          {/* Code panel */}
          {result?.code && (
            <div style={{
              borderTop: `1px solid ${t.border}`, background: t.codeBg,
              display: 'flex', flexDirection: 'column', overflow: 'hidden',
              height: codeOpen ? '50vh' : 36, transition: 'height .3s ease',
            }}>
              <div
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '8px 16px', background: t.sidebar, cursor: 'pointer',
                  borderBottom: `1px solid ${t.border}`,
                }}
                onClick={() => setCodeOpen(o => !o)}
              >
                <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>
                  Generated Spark Code ({result.code.split('\n').length} lines)
                </span>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <button
                    style={{ ...iconBtn, padding: '4px 10px', fontSize: 13 }}
                    onClick={(e) => { e.stopPropagation(); downloadCode() }}
                  >📥 Download</button>
                  <button style={{
                    fontSize: 13, color: t.accent, background: 'none',
                    border: `1px solid ${t.accentBorder}`, borderRadius: 4, padding: '4px 10px', cursor: 'pointer',
                  }}>
                    {codeOpen ? '▼ Collapse' : '▲ Expand'}
                  </button>
                </div>
              </div>
              {codeOpen && (
                <pre style={{
                  padding: 16, fontSize: 14, color: t.muted,
                  fontFamily: 'monospace', whiteSpace: 'pre', overflowY: 'auto',
                  flex: 1, lineHeight: 1.6, margin: 0,
                }}>{result.code}</pre>
              )}
            </div>
          )}
        </div>
        </>
        )}
      </div>
    </div>
  )
}
