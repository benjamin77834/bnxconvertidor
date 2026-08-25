import { useState, useCallback, useRef, useEffect } from 'react'
import FileUpload from './components/FileUpload'
import DagViewer from './components/DagViewer'
import MetricsPage from './components/MetricsPage'
import DesignerPage from './components/DesignerPage'
import OcrPage from './components/OcrPage'
import BankingModelPage from './components/BankingModelPage'
import GovernancePage from './components/GovernancePage'
import ArchitecturePage from './components/ArchitecturePage'
import ExecutivePage from './components/ExecutivePage'
import RoadmapPage from './components/RoadmapPage'
import HistoryPage from './components/HistoryPage'
import PipelinePage from './components/PipelinePage'
import GraphLibrary from './components/GraphLibrary'
import GrafosPage from './components/GrafosPage'
import DataGenPage from './components/DataGenPage'
import { COMPILE_URL } from './config'

// ── Themes ──────────────────────────────────────────────────
const dark = {
  bg: '#0a1628', sidebar: '#0f1f3d', header: '#122448',
  card: '#152a52', border: '#1e3a6e', text: '#e8edf5',
  muted: '#8fa3c4', dim: '#5a7399', codeBg: '#081220',
  accent: '#1a73e8', accentBg: '#1a73e820', accentBorder: '#1a73e840',
  flowBg: '#0f1f3d',
}
const light = {
  bg: '#f5f0e8', sidebar: '#fdf6e3', header: '#2E7D32',
  card: '#ffffff', border: '#4CAF50', text: '#1a1a1a',
  muted: '#2d4a2e', dim: '#5a7a5c', codeBg: '#f9f9f5',
  accent: '#1B5E20', accentBg: '#1B5E2018', accentBorder: '#1B5E2030',
  flowBg: '#f5f0e8', headerText: '#ffffff',
}

const LEGEND = [
  { type: 'SOURCE',      color: '#22c55e', desc: 'Lectura de datos desde S3, DB o archivos (Scan)' },
  { type: 'TRANSFORM',   color: '#6366f1', desc: 'SELECT, WHERE, GROUP BY (Reformat/Rollup)' },
  { type: 'ROLLUP',      color: '#7c3aed', desc: 'Agrupación y agregaciones (SUM, COUNT, AVG, MAX)' },
  { type: 'JOIN',        color: '#f59e0b', desc: 'Combina dos o más datasets por una key' },
  { type: 'DEDUP',       color: '#06b6d4', desc: 'Elimina registros duplicados por key (Dedup Sort)' },
  { type: 'NORMALIZE',   color: '#a855f7', desc: 'Expande un registro en múltiples filas' },
  { type: 'LOOKUP',      color: '#ec4899', desc: 'Enriquece con tabla de referencia (broadcast)' },
  { type: 'CONCATENATE', color: '#14b8a6', desc: 'Une datasets sin key (unionByName)' },
  { type: 'GATHER',      color: '#8b5cf6', desc: 'Merge múltiples streams en uno' },
  { type: 'PARTITION',   color: '#f97316', desc: 'Reparticiona por key a N particiones' },
  { type: 'FILTER',      color: '#eab308', desc: 'Filtra con puerto de rechazo (2 salidas)' },
  { type: 'SINK',        color: '#ef4444', desc: 'Escritura final a S3, DB o Kafka' },
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
  // result persiste en localStorage para que el codigo compilado sobreviva a
  // recargas de pagina (asi Data Redactada / Pipeline no pierden el codigo).
  const [result, _setResult]    = useState(() => {
    try {
      const saved = localStorage.getItem('bnx_last_result')
      return saved ? JSON.parse(saved) : null
    } catch { return null }
  })
  const setResult = (val) => {
    _setResult(val)
    try {
      if (val && val.code) localStorage.setItem('bnx_last_result', JSON.stringify(val))
      else if (!val) localStorage.removeItem('bnx_last_result')
    } catch { /* localStorage lleno o no disponible: ignorar */ }
  }
  const [loading, setLoading]   = useState(false)
  const [codeOpen, setCodeOpen] = useState(false)
  const [isDark, setIsDark]     = useState(true)
  const [target, _setTarget]    = useState(() => {
    try { return localStorage.getItem('bnx_last_target') || 'glue' } catch { return 'glue' }
  })
  const setTarget = (val) => {
    _setTarget(val)
    try { localStorage.setItem('bnx_last_target', val) } catch { /* ignore */ }
  }
  const [page, setPage]         = useState('compiler')
  const [expandedPanel, setExpandedPanel] = useState(null)  // 'code' | 'dag' | 'editor-mp' | 'editor-xfr' | 'editor-pset' | null

  // Cerrar fullscreen con Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') setExpandedPanel(null)
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])
  const dagRef                  = useRef(null)
  const cobolRef                = useRef(null)
  const planRef                 = useRef(null)
  const psetRef                 = useRef(null)
  const [psetFile, setPsetFile] = useState(null)
  const [planXfrFile, setPlanXfrFile] = useState(null)
  const planXfrRef              = useRef(null)
  const [mpFiles, setMpFiles]   = useState([])
  const mpFilesRef              = useRef(null)
  const mpFilesData             = useRef([])  // Persist mp files across re-renders
  const refactorRef             = useRef(null)
  const [refactorResult, setRefactorResult] = useState(null)
  const [showEditor, setShowEditor] = useState(false)
  const [editorTab, setEditorTab] = useState('mp')
  // Los editores persisten en localStorage para que Data Redactada tenga el
  // grafo (.mp/.xfr) aun despues de recargar la pagina.
  const _lsGet = (k) => { try { return localStorage.getItem(k) || '' } catch { return '' } }
  const _lsSet = (k, v) => { try { if (v) localStorage.setItem(k, v); else localStorage.removeItem(k) } catch { /* ignore */ } }
  const [editorMp, _setEditorMp] = useState(() => _lsGet('bnx_editor_mp'))
  const [editorXfr, _setEditorXfr] = useState(() => _lsGet('bnx_editor_xfr'))
  const [editorPset, _setEditorPset] = useState(() => _lsGet('bnx_editor_pset'))
  const setEditorMp = (v) => { _setEditorMp(v); _lsSet('bnx_editor_mp', v) }
  const setEditorXfr = (v) => { _setEditorXfr(v); _lsSet('bnx_editor_xfr', v) }
  const setEditorPset = (v) => { _setEditorPset(v); _lsSet('bnx_editor_pset', v) }

  const t = isDark ? dark : light

  // Debug: track mpFiles state changes
  console.log('RENDER - target:', target, 'mpFiles:', mpFiles.length, mpFiles.map(f => f.name))

  const [compileTime, setCompileTime] = useState(null)

  const compile = async (selected) => {
    setLoading(true)
    const startTime = Date.now()
    const form = new FormData()
    form.append('mp', selected.mp)
    // Guardar el contenido del .mp en el editor para que Data Redactada lo tenga
    // (aunque se haya compilado subiendo archivos, no pegando en el editor).
    try {
      if (selected.mp && typeof selected.mp.text === 'function') {
        selected.mp.text().then(txt => setEditorMp(txt)).catch(() => {})
      }
    } catch { /* ignore */ }
    // Handle multiple .xfr files — concatenate them into one
    if (selected.allXfr && Array.isArray(selected.xfr) && selected.xfr.length > 0) {
      // Read all xfr files and concatenate
      const xfrContents = []
      for (const f of selected.xfr) {
        const text = await f.text()
        xfrContents.push(`# === ${f.name} ===\n${text}`)
      }
      const combined = xfrContents.join('\n\n')
      form.append('xfr', new File([combined], 'combined.xfr'))
      setEditorXfr(combined)
    } else if (selected.xfr && !Array.isArray(selected.xfr)) {
      form.append('xfr', selected.xfr)
      try {
        if (typeof selected.xfr.text === 'function') {
          selected.xfr.text().then(txt => setEditorXfr(txt)).catch(() => {})
        }
      } catch { /* ignore */ }
    }
    if (selected.dml) form.append('dml', selected.dml)
    if (selected.pset) form.append('pset', selected.pset)
    form.append('target', target)
    try {
      const res = await fetch(COMPILE_URL, { method: 'POST', body: form })
      const data = await res.json()
      setCompileTime(Date.now() - startTime)
      setResult(data)
      if (data.code) setCodeOpen(true)
    } catch (e) {
      setCompileTime(Date.now() - startTime)
      setResult({ errors: [`Network error: ${e.message}`], warnings: [], nodes: [], edges: [] })
    } finally { setLoading(false) }
  }

  const downloadCode = useCallback(() => {
    if (result?.code) download(result.code, target === 'spark' ? 'pyspark_job.py' : target === 'flink' ? 'flink_job.py' : 'glue_job.py')
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

  const refactorCode = async (file) => {
    setLoading(true)
    const form = new FormData()
    form.append('code', file)
    form.append('source_version', 'all')
    try {
      const res = await fetch(COMPILE_URL.replace('/compile', '/refactor'), { method: 'POST', body: form })
      const data = await res.json()
      setRefactorResult(data)
      if (data.code) {
        setResult({ nodes: [], edges: [], code: data.code, errors: [], warnings: [],
          refactor: true, changes: data.changes, total_changes: data.total_changes,
          original_lines: data.original_lines, refactored_lines: data.refactored_lines })
        setCodeOpen(true)
      }
    } catch (e) {
      setRefactorResult({ error: e.message })
    } finally { setLoading(false) }
  }

  const compilePlan = async (planFile, psetFile) => {
    setLoading(true)
    const startTime = Date.now()
    const form = new FormData()
    form.append('plan', planFile)
    if (psetFile) form.append('pset', psetFile)
    if (planXfrFile) form.append('xfr', planXfrFile)
    console.log('MP FILES COUNT:', mpFilesData.current.length, mpFilesData.current.map(f => f.name))
    mpFilesData.current.forEach((f, i) => form.append(`mp_file_${i}`, f))
    form.append('target', target)
    try {
      const res = await fetch(COMPILE_URL.replace('/compile', '/plan'), { method: 'POST', body: form })
      const data = await res.json()
      setCompileTime(Date.now() - startTime)
      setResult(data)
      if (data.code) setCodeOpen(true)
    } catch (e) {
      setCompileTime(Date.now() - startTime)
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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: t.bg, color: t.text, transition: 'background .4s ease, color .4s ease' }}>
      <style>{`@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>

      {/* Fullscreen Overlay */}
      {expandedPanel && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 9999,
          background: t.bg, display: 'flex', flexDirection: 'column',
        }}>
          {/* Fullscreen header */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '10px 20px', background: t.header, borderBottom: `1px solid ${t.border}`,
          }}>
            <span style={{ fontSize: 16, fontWeight: 700, color: t.headerText || t.text }}>
              {expandedPanel === 'code' && `📄 Generated ${target === 'flink' ? 'Flink' : target === 'spark' ? 'Spark' : 'Glue'} Code`}
              {expandedPanel === 'dag' && '🔀 DAG Graph'}
              {expandedPanel === 'editor-mp' && '📄 Editor .mp'}
              {expandedPanel === 'editor-xfr' && '🔄 Editor .xfr'}
              {expandedPanel === 'editor-pset' && '⚙️ Editor .pset'}
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              {expandedPanel === 'code' && result?.code && (
                <button onClick={downloadCode} style={{
                  padding: '6px 14px', borderRadius: 6, fontSize: 13, cursor: 'pointer',
                  background: '#22c55e20', border: '1px solid #22c55e', color: '#22c55e', fontWeight: 600,
                }}>📥 Download</button>
              )}
              <button onClick={() => setExpandedPanel(null)} style={{
                padding: '6px 14px', borderRadius: 6, fontSize: 13, cursor: 'pointer',
                background: '#ef444420', border: '1px solid #ef4444', color: '#ef4444', fontWeight: 600,
              }}>✕ Cerrar</button>
            </div>
          </div>
          {/* Fullscreen content */}
          <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {expandedPanel === 'code' && result?.code && (
              <pre style={{
                flex: 1, padding: 20, fontSize: 14, color: t.muted,
                fontFamily: 'monospace', whiteSpace: 'pre', overflowY: 'auto',
                lineHeight: 1.6, margin: 0, background: t.codeBg,
              }}>{result.code}</pre>
            )}
            {expandedPanel === 'dag' && result?.nodes?.length > 0 && (
              <div style={{ flex: 1, width: '100%', height: '100%' }}>
                <DagViewer data={result} theme={t} />
              </div>
            )}
            {expandedPanel === 'editor-mp' && (
              <textarea
                value={editorMp}
                onChange={e => setEditorMp(e.target.value)}
                placeholder="Pega tu contenido .mp aquí..."
                style={{
                  flex: 1, padding: 20, margin: 0, border: 'none', outline: 'none', resize: 'none',
                  background: t.codeBg || '#081220', color: '#22c55e',
                  fontSize: 14, fontFamily: 'monospace', lineHeight: 1.6,
                }}
              />
            )}
            {expandedPanel === 'editor-xfr' && (
              <textarea
                value={editorXfr}
                onChange={e => setEditorXfr(e.target.value)}
                placeholder="Pega tu contenido .xfr aquí..."
                style={{
                  flex: 1, padding: 20, margin: 0, border: 'none', outline: 'none', resize: 'none',
                  background: t.codeBg || '#081220', color: '#6366f1',
                  fontSize: 14, fontFamily: 'monospace', lineHeight: 1.6,
                }}
              />
            )}
            {expandedPanel === 'editor-pset' && (
              <textarea
                value={editorPset}
                onChange={e => setEditorPset(e.target.value)}
                placeholder="Pega tu contenido .pset aquí..."
                style={{
                  flex: 1, padding: 20, margin: 0, border: 'none', outline: 'none', resize: 'none',
                  background: t.codeBg || '#081220', color: '#f59e0b',
                  fontSize: 14, fontFamily: 'monospace', lineHeight: 1.6,
                }}
              />
            )}
          </div>
        </div>
      )}

      {/* Header */}
      <header style={{
        padding: '12px 24px', background: t.header, borderBottom: `1px solid ${t.border}`,
        display: 'flex', alignItems: 'center', gap: 16,
      }}>
        <span style={{ fontSize: 20, fontWeight: 700, color: t.headerText || t.text }}>🚀 BNX Compiler</span>
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
            { id: 'executive', label: '🎯 Executive' },
            { id: 'compiler', label: '🔧 Compiler' },
            { id: 'designer', label: '🎨 Designer' },
            { id: 'ocr', label: '📷 OCR' },
            { id: 'banking', label: '🏦 Banking' },
            { id: 'architecture', label: '🏗️ Architecture' },
            { id: 'metrics', label: '📊 Metrics' },
            { id: 'roadmap', label: '🗺️ Roadmap' },
            { id: 'pipeline', label: '🧪 Pipeline' },
            { id: 'grafos', label: '📁 Grafos' },
            { id: 'datagen', label: '🧪 Data Redactada' },
            { id: 'history', label: '📜 History' },
          ].map(tab => (
            <button key={tab.id}
              onClick={() => setPage(tab.id)}
              style={{
                padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
                background: page === tab.id ? t.accent + '20' : 'transparent',
                border: `1px solid ${page === tab.id ? t.accent : 'transparent'}`,
                color: page === tab.id ? (t.headerText || t.accent) : (t.headerText || t.muted),
                fontWeight: page === tab.id ? 600 : 400,
              }}
            >{tab.label}</button>
          ))}
        </div>

        <div style={{ flex: 1 }} />

        {/* Downloads */}
        {result?.code && (
          <button style={{
            ...iconBtn,
            background: '#22c55e20',
            border: '1px solid #22c55e',
            color: '#22c55e',
            fontWeight: 700,
            animation: result.code.length > 5000 ? 'blink 1.5s ease-in-out infinite' : 'none',
          }} onClick={downloadCode}>📥 Code</button>
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
        {page === 'executive' ? (
          <ExecutivePage theme={t} />
        ) : page === 'metrics' ? (
          <MetricsPage theme={t} />
        ) : page === 'roadmap' ? (
          <RoadmapPage theme={t} />
        ) : page === 'history' ? (
          <HistoryPage theme={t} />
        ) : page === 'pipeline' ? (
          <PipelinePage theme={t} compiledCode={result?.code || ''} compiledTarget={target} extractorCode={result?.extractor_code || ''} hasDbSources={result?.has_db_sources || false} />
        ) : page === 'grafos' ? (
          <GrafosPage theme={t} onLoadToCompiler={(g) => {
            setEditorMp(g.mp || '')
            setEditorXfr(g.xfr || '')
            if (g.pset) setEditorPset(g.pset)
            setShowEditor(true)
            setEditorTab(g.xfr ? 'xfr' : 'mp')
            setPage('compiler')
            // Auto-compile after loading from Grafos
            setTimeout(() => {
              const compileBtn = document.querySelector('[data-compile-btn]')
              if (compileBtn) compileBtn.click()
            }, 500)
          }} />
        ) : page === 'datagen' ? (
          <DataGenPage theme={t} graphMp={editorMp} graphXfr={editorXfr}
            compiledCode={result?.code || ''} compiledTarget={target}
            graphName={result?.graph_name || ''} graphDescription={result?.description || ''} />
        ) : page === 'designer' ? (
          <DesignerPage theme={t} />
        ) : page === 'ocr' ? (
          <OcrPage theme={t} />
        ) : page === 'banking' ? (
          <BankingModelPage theme={t} />
        ) : page === 'architecture' ? (
          <ArchitecturePage theme={t} />
        ) : (
        <>
        {/* Sidebar */}
        <aside style={{
          width: 360, padding: 24, background: t.sidebar, flexShrink: 0,
          borderRight: `1px solid ${t.border}`, display: 'flex',
          flexDirection: 'column', gap: 20, overflowY: 'auto',
        }}>
          <FileUpload files={files} setFiles={setFiles} onCompile={compile} loading={loading} theme={t} />

          {/* Biblioteca de Grafos (S3) */}
          <GraphLibrary theme={t} onLoad={(g) => {
            setEditorMp(g.mp || '')
            setEditorXfr(g.xfr || '')
            setShowEditor(true)
            setEditorTab('mp')
          }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>✏️ Editor</span>
              <button onClick={() => setShowEditor(e => !e)} style={{
                padding: '2px 8px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
                background: showEditor ? t.accent + '20' : 'transparent',
                border: `1px solid ${showEditor ? t.accent : t.border}`,
                color: showEditor ? t.accent : t.dim,
              }}>{showEditor ? 'Cerrar' : 'Abrir'}</button>
            </div>
            {showEditor && (
              <>
                <span style={{ fontSize: 11, color: t.dim }}>Pega o escribe .mp, .xfr, .pset directamente</span>
                {/* Tab selector */}
                <div style={{ display: 'flex', gap: 4 }}>
                  {[
                    { id: 'mp', label: '📄 .mp', color: '#22c55e' },
                    { id: 'xfr', label: '🔄 .xfr', color: '#6366f1' },
                    { id: 'pset', label: '⚙️ .pset', color: '#f59e0b' },
                  ].map(tab => (
                    <button key={tab.id} onClick={() => setEditorTab(tab.id)} style={{
                      flex: 1, padding: '4px 8px', borderRadius: 6, cursor: 'pointer', fontSize: 11,
                      background: editorTab === tab.id ? tab.color + '20' : 'transparent',
                      border: `1px solid ${editorTab === tab.id ? tab.color : t.border}`,
                      color: editorTab === tab.id ? tab.color : t.dim, fontWeight: editorTab === tab.id ? 600 : 400,
                    }}>{tab.label}</button>
                  ))}
                </div>
                {/* Editor area */}
                {editorTab === 'mp' && (
                  <>
                  <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                    <button onClick={() => setExpandedPanel('editor-mp')} style={{
                      padding: '2px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                      background: 'transparent', border: `1px solid #22c55e40`, color: '#22c55e',
                    }}>🔲 Expandir</button>
                    <button onClick={() => { navigator.clipboard.writeText(editorMp) }} style={{
                      padding: '2px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                      background: 'transparent', border: `1px solid #22c55e40`, color: '#22c55e',
                    }}>📋 Copiar</button>
                    <button onClick={() => { const ta = document.getElementById('editor-mp'); if(ta){ ta.select(); ta.focus() } }} style={{
                      padding: '2px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                      background: 'transparent', border: `1px solid #22c55e40`, color: '#22c55e',
                    }}>✅ Seleccionar</button>
                  </div>
                  <textarea
                    id="editor-mp"
                    value={editorMp}
                    onChange={e => setEditorMp(e.target.value)}
                    placeholder={`NODE ReadCSV : SOURCE\nNODE Transform : TRANSFORM\nNODE WriteOut : SINK\n\nReadCSV -> Transform\nTransform -> WriteOut\n\n# También soporta formato nativo Ab Initio:\n# {timestamp|XXGpvertex|id|...|name|...}`}
                    style={{
                      width: '100%', minHeight: 140, maxHeight: 300, padding: 10, borderRadius: 8,
                      background: t.codeBg || '#081220', border: `1px solid #22c55e40`,
                      color: '#22c55e', fontSize: 12, fontFamily: 'monospace', lineHeight: 1.5,
                      resize: 'vertical', outline: 'none',
                    }}
                  />
                  </>
                )}
                {editorTab === 'xfr' && (
                  <>
                    {editorXfr && editorXfr.includes('# ===') && (
                      <div style={{ fontSize: 11, color: '#6366f1', marginBottom: 4, padding: '4px 8px', borderRadius: 4, background: '#6366f110', border: '1px solid #6366f130' }}>
                        📎 {(editorXfr.match(/# ===/g) || []).length} archivo(s) .xfr concatenados
                      </div>
                    )}
                    <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                      <button onClick={() => setExpandedPanel('editor-xfr')} style={{
                        padding: '2px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                        background: 'transparent', border: `1px solid #6366f140`, color: '#6366f1',
                      }}>🔲 Expandir</button>
                      <button onClick={() => { navigator.clipboard.writeText(editorXfr) }} style={{
                        padding: '2px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                        background: 'transparent', border: `1px solid #6366f140`, color: '#6366f1',
                      }}>📋 Copiar</button>
                      <button onClick={() => { const ta = document.getElementById('editor-xfr'); if(ta){ ta.select(); ta.focus() } }} style={{
                        padding: '2px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                        background: 'transparent', border: `1px solid #6366f140`, color: '#6366f1',
                      }}>✅ Seleccionar</button>
                    </div>
                    <textarea
                      id="editor-xfr"
                      value={editorXfr}
                      onChange={e => setEditorXfr(e.target.value)}
                      placeholder={`ReadCSV:\n  source_type s3\n  path s3://bucket/data\n  format csv\n\nTransform:\n  select id, name, amount\n  where amount > 0\n\nWriteOut:\n  sink_type s3\n  path s3://output\n  format parquet`}
                      style={{
                        width: '100%', minHeight: 140, maxHeight: 300, padding: 10, borderRadius: 8,
                        background: t.codeBg || '#081220', border: `1px solid #6366f140`,
                        color: '#6366f1', fontSize: 12, fontFamily: 'monospace', lineHeight: 1.5,
                        resize: 'vertical', outline: 'none',
                      }}
                    />
                  </>
                )}
                {editorTab === 'pset' && (
                  <>
                  <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                    <button onClick={() => setExpandedPanel('editor-pset')} style={{
                      padding: '2px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                      background: 'transparent', border: `1px solid #f59e0b40`, color: '#f59e0b',
                    }}>🔲 Expandir</button>
                    <button onClick={() => { navigator.clipboard.writeText(editorPset) }} style={{
                      padding: '2px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                      background: 'transparent', border: `1px solid #f59e0b40`, color: '#f59e0b',
                    }}>📋 Copiar</button>
                    <button onClick={() => { const ta = document.getElementById('editor-pset'); if(ta){ ta.select(); ta.focus() } }} style={{
                      padding: '2px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                      background: 'transparent', border: `1px solid #f59e0b40`, color: '#f59e0b',
                    }}>✅ Seleccionar</button>
                  </div>
                  <textarea
                    id="editor-pset"
                    value={editorPset}
                    onChange={e => setEditorPset(e.target.value)}
                    placeholder={`# Formato simple:\nS3_INPUT = s3://datalake/raw\nS3_OUTPUT = s3://datalake/curated\n\n# O formato nativo Ab Initio:\n# !prototype|P|||path\n# KEY||||VALUE`}
                    style={{
                      width: '100%', minHeight: 140, maxHeight: 300, padding: 10, borderRadius: 8,
                      background: t.codeBg || '#081220', border: `1px solid #f59e0b40`,
                      color: '#f59e0b', fontSize: 12, fontFamily: 'monospace', lineHeight: 1.5,
                      resize: 'vertical', outline: 'none',
                    }}
                  />
                  </>
                )}
                {/* Status indicators */}
                <div style={{ display: 'flex', gap: 8, fontSize: 10, color: t.dim }}>
                  {editorMp.trim() && <span style={{ color: '#22c55e' }}>✅ MP ({editorMp.split('\n').length} líneas)</span>}
                  {editorXfr.trim() && <span style={{ color: '#6366f1' }}>✅ XFR</span>}
                  {editorPset.trim() && <span style={{ color: '#f59e0b' }}>✅ PSET</span>}
                  {!editorMp.trim() && <span style={{ color: '#ef4444' }}>⚠️ MP requerido</span>}
                </div>
                <button
                  onClick={() => {
                    if (!editorMp.trim()) return
                    setLoading(true)
                    const startTime = Date.now()
                    const form = new FormData()
                    form.append('mp', new File([editorMp], 'editor.mp'))
                    if (editorXfr.trim()) form.append('xfr', new File([editorXfr], 'editor.xfr'))
                    form.append('target', target)
                    fetch(COMPILE_URL, { method: 'POST', body: form })
                      .then(res => res.json())
                      .then(data => { setCompileTime(Date.now() - startTime); setResult(data); if (data.code) setCodeOpen(true) })
                      .catch(e => { setCompileTime(Date.now() - startTime); setResult({ errors: [`Error: ${e.message}`], warnings: [], nodes: [], edges: [] }) })
                      .finally(() => setLoading(false))
                  }}
                  disabled={!editorMp.trim() || loading}
                  data-compile-btn="true"
                  style={{
                    padding: '8px 16px', borderRadius: 8, cursor: editorMp.trim() ? 'pointer' : 'not-allowed',
                    background: editorMp.trim() ? t.accent : t.border,
                    color: '#fff', border: 'none', fontSize: 13, fontWeight: 600,
                  }}
                >{loading ? '⏳...' : '🚀 Compile Editor'}</button>
              </>
            )}
          </div>

          {/* Target selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>Target</span>
            <div style={{ display: 'flex', gap: 8 }}>
              {[
                { id: 'glue', label: '🔧 Glue', desc: 'AWS Glue + GlueContext' },
                { id: 'spark', label: '⚡ PySpark', desc: 'PySpark puro + SparkSession' },
                { id: 'flink', label: '🌊 Flink', desc: 'PyFlink + Table API / Flink SQL' },
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

          {/* Refactor Legacy Code */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>Refactorización</span>
            <span style={{ fontSize: 12, color: t.dim }}>Sube código Spark 2 / Python 2 / Glue 2 y se refactoriza automáticamente</span>
            <button
              style={{
                padding: '8px 16px', borderRadius: 8, cursor: 'pointer',
                background: t.card, border: `1px dashed ${t.border}`,
                color: t.muted, fontSize: 13,
              }}
              onClick={() => refactorRef.current.click()}
            >🔄 Upload .py file</button>
            <input ref={refactorRef} type="file" hidden
              onChange={(e) => { if (e.target.files[0]) refactorCode(e.target.files[0]); e.target.value = '' }}
            />
            {refactorResult && !refactorResult.error && (
              <div style={{
                background: t.card, borderRadius: 8, padding: 10,
                border: `1px solid ${t.border}`, display: 'flex', flexDirection: 'column', gap: 6,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#22c55e' }}>
                    ✅ {refactorResult.total_changes} cambios aplicados
                  </span>
                  <button onClick={() => {
                    if (refactorResult.code) download(refactorResult.code, 'refactored.py')
                  }} style={{
                    padding: '3px 8px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
                    background: '#22c55e20', border: '1px solid #22c55e40', color: '#22c55e',
                  }}>📥 Download</button>
                </div>
                <div style={{ fontSize: 11, color: t.dim }}>
                  {refactorResult.original_lines} → {refactorResult.refactored_lines} líneas
                </div>
                {refactorResult.changes?.map((c, i) => (
                  <div key={i} style={{ fontSize: 11, color: c.action.includes('WARNING') ? '#f59e0b' : '#22c55e' }}>
                    {c.action} {c.name} ({c.count}x)
                  </div>
                ))}
              </div>
            )}
            {refactorResult?.error && (
              <div style={{ fontSize: 11, color: '#ef4444', padding: 6 }}>❌ {refactorResult.error}</div>
            )}
          </div>

          {/* Ab Initio PLAN/PSET upload */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>Ab Initio PLAN</span>
            <span style={{ fontSize: 12, color: t.dim }}>Sube en orden: 1° PSET, 2° XFR, 3° MP files (opcional), 4° PLAN (compila al subir PLAN)</span>
            {psetFile && (
              <span style={{ fontSize: 11, color: '#22c55e' }}>✅ 1. PSET: {psetFile.name}</span>
            )}
            {planXfrFile && (
              <span style={{ fontSize: 11, color: '#6366f1' }}>✅ 2. XFR: {planXfrFile.name}</span>
            )}
            <div style={{ display: 'flex', gap: 6 }}>
              <button style={{
                flex: 1, padding: '8px 12px', borderRadius: 8, cursor: 'pointer',
                background: psetFile ? '#22c55e15' : t.card,
                border: `1px dashed ${psetFile ? '#22c55e' : t.border}`,
                color: psetFile ? '#22c55e' : t.muted, fontSize: 12,
              }} onClick={() => psetRef.current.click()}>1° ⚙️ .pset</button>
              <button style={{
                flex: 1, padding: '8px 12px', borderRadius: 8, cursor: 'pointer',
                background: planXfrFile ? '#6366f115' : t.card,
                border: `1px dashed ${planXfrFile ? '#6366f1' : t.border}`,
                color: planXfrFile ? '#6366f1' : t.muted, fontSize: 12,
              }} onClick={() => planXfrRef.current.click()}>2° 🔄 .xfr</button>
              <button style={{
                flex: 1, padding: '8px 12px', borderRadius: 8, cursor: 'pointer',
                background: mpFilesData.current.length > 0 ? '#f59e0b15' : t.card,
                border: `1px dashed ${mpFilesData.current.length > 0 ? '#f59e0b' : t.border}`,
                color: mpFilesData.current.length > 0 ? '#f59e0b' : t.muted, fontSize: 12,
              }} onClick={() => { console.log('MP BUTTON CLICKED'); mpFilesRef.current.click() }}>3° 📦 .mp ({mpFilesData.current.length})</button>
              <button style={{
                flex: 1, padding: '8px 12px', borderRadius: 8, cursor: 'pointer',
                background: t.card, border: `1px dashed ${t.accent || '#6366f1'}`,
                color: t.accent || '#6366f1', fontSize: 12, fontWeight: 600,
              }} onClick={() => planRef.current.click()}>4° 📄 .plan</button>
            </div>
            {(mpFiles.length > 0 || mpFilesData.current.length > 0) && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <span style={{ fontSize: 11, color: '#f59e0b' }}>📦 {mpFilesData.current.length} MP file{mpFilesData.current.length > 1 ? 's' : ''}:</span>
                {mpFilesData.current.map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11 }}>
                    <span style={{ color: t.muted, flex: 1 }}>{f.name}</span>
                    <button onClick={() => { mpFilesData.current = mpFilesData.current.filter((_, j) => j !== i); setMpFiles([...mpFilesData.current]) }} style={{
                      background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: 11, padding: '0 4px',
                    }}>❌</button>
                  </div>
                ))}
              </div>
            )}
            <div style={{
              fontSize: 11, color: t.dim, lineHeight: 1.5, padding: '6px 8px',
              background: t.bg, borderRadius: 6, border: `1px solid ${t.border}`,
            }}>
              📄 <span style={{ color: t.muted }}>PLAN</span> = orquestación (qué grafos y en qué orden)<br/>
              ⚙️ <span style={{ color: t.muted }}>PSET</span> = parámetros (paths S3, Kafka, DB)<br/>
              🔄 <span style={{ color: t.muted }}>XFR</span> = lógica de negocio (select, where, joins)<br/>
              📦 <span style={{ color: t.muted }}>MP</span> = grafos externos (Grafo de Grafos)<br/>
              <span style={{ color: '#22c55e' }}>PLAN + MP files = Mega-DAG unificado</span>
            </div>
            <input ref={planRef} type="file" hidden
              onChange={(e) => { if (e.target.files[0]) compilePlan(e.target.files[0], psetFile); e.target.value = '' }}
            />
            <input ref={psetRef} type="file" hidden
              onChange={(e) => { if (e.target.files[0]) { setPsetFile(e.target.files[0]) }; e.target.value = '' }}
            />
            <input ref={planXfrRef} type="file" accept=".xfr" hidden
              onChange={(e) => { if (e.target.files[0]) { setPlanXfrFile(e.target.files[0]) }; e.target.value = '' }}
            />
            <input ref={mpFilesRef} type="file" multiple hidden
              onChange={(e) => {
                if (e.target.files.length) {
                  const newFiles = Array.from(e.target.files)
                  mpFilesData.current = [...mpFilesData.current, ...newFiles]
                  setMpFiles([...mpFilesData.current])
                  console.log('MP FILES STORED:', mpFilesData.current.length, mpFilesData.current.map(f => f.name))
                }
                e.target.value = ''
              }}
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

              {/* Accuracy explanation */}
              <div style={{
                marginTop: 4, padding: 10, borderRadius: 6,
                background: t.bg, border: `1px solid ${t.border}`,
                fontSize: 12, color: t.dim, lineHeight: 1.6,
              }}>
                <div style={{ fontWeight: 600, color: t.muted, marginBottom: 4 }}>¿Cómo se calcula?</div>
                <div>Mide qué tan completa es la traducción del grafo al código:</div>
                <div style={{ marginTop: 4 }}>
                  <div>• <span style={{ color: '#22c55e' }}>Nodes</span> — nodos con padre válido o SOURCE</div>
                  <div>• <span style={{ color: '#22c55e' }}>Edges</span> — conexiones donde ambos nodos existen</div>
                  <div>• <span style={{ color: '#6366f1' }}>Transforms</span> — nodos con regla XFR (select/where/group_by)</div>
                  <div>• <span style={{ color: '#f59e0b' }}>Joins</span> — nodos JOIN con join_key configurada</div>
                </div>
                <div style={{ marginTop: 6, fontFamily: 'monospace', fontSize: 11, color: t.muted }}>
                  Overall = Nodes×30% + Edges×20% + Transforms×30% + Joins×20%
                </div>
                <div style={{ marginTop: 4 }}>
                  <span style={{ color: '#22c55e' }}>90%+</span> producción ·{' '}
                  <span style={{ color: '#f59e0b' }}>70-89%</span> ajustes ·{' '}
                  <span style={{ color: '#ef4444' }}>&lt;70%</span> faltan reglas
                </div>
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
              <>
              <div style={{
                display: 'flex', gap: 12, padding: '10px 20px', flexWrap: 'wrap',
                background: t.sidebar, borderBottom: `1px solid ${t.border}`,
                alignItems: 'center',
              }}>
                <span style={{
                  fontSize: 15, fontWeight: 700, color: t.text,
                  marginRight: 8,
                }}>
                  {result.graph_name && <span style={{ color: t.accent || '#6366f1' }}>{result.graph_name} — </span>}
                  {result.nodes.length} nodes · {result.edges.length} edges
                  {result.subgraphs?.length > 0 && ` · ${result.subgraphs.length} subgraphs`}
                </span>
                <span style={{ width: 1, height: 20, background: t.border }} />
                {compileTime && (
                  <span style={{
                    fontSize: 13, color: '#22c55e', fontWeight: 600,
                    padding: '3px 10px', borderRadius: 6,
                    background: '#22c55e15', border: '1px solid #22c55e30',
                  }}>⚡ {compileTime}ms</span>
                )}
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
                {result.stepfunctions && (
                  <button onClick={() => download(result.stepfunctions, 'step_functions.json')} style={{
                    padding: '4px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                    background: t.card, border: `1px solid ${t.border}`, color: t.muted,
                  }}>⚡ StepFn</button>
                )}
                {result.terraform && (
                  <button onClick={() => download(result.terraform, 'main.tf')} style={{
                    padding: '4px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                    background: t.card, border: `1px solid ${t.border}`, color: t.muted,
                  }}>🏗️ Terraform</button>
                )}
                {result.airflow && (
                  <button onClick={() => download(result.airflow, 'airflow_dag.py')} style={{
                    padding: '4px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                    background: t.card, border: `1px solid ${t.border}`, color: t.muted,
                  }}>🌀 Airflow</button>
                )}
              </div>
              {/* Descripcion en lenguaje natural del grafo */}
              {result.description && (
                <div style={{
                  padding: '8px 20px', background: t.sidebar,
                  borderBottom: `1px solid ${t.border}`,
                  fontSize: 13, color: t.muted, lineHeight: 1.5,
                }}>
                  <span style={{ color: t.accent || '#818cf8', fontWeight: 600 }}>📝 Descripción: </span>
                  {result.description}
                </div>
              )}
              </>
            )
          })()}
          <div ref={dagRef} style={{ flex: 1, position: 'relative', minHeight: 0 }}>
            {result?.nodes?.length > 0 && (
              <button onClick={() => setExpandedPanel('dag')} style={{
                position: 'absolute', top: 10, right: 10, zIndex: 10,
                padding: '6px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                background: t.card, border: `1px solid ${t.border}`, color: t.muted,
                display: 'flex', alignItems: 'center', gap: 4,
              }}>🔲 Fullscreen</button>
            )}
            {result?.nodes?.length > 0
              ? <DagViewer data={result} theme={t} onEditNode={(nodeId, newRule) => {
                  // Update the node rule in result and recompile
                  const updatedNodes = result.nodes.map(n =>
                    n.id === nodeId ? { ...n, rule: { ...n.rule, ...newRule } } : n
                  )
                  const updatedResult = { ...result, nodes: updatedNodes }
                  setResult(updatedResult)

                  // Build XFR from updated rules and recompile
                  let xfr = ''
                  updatedNodes.forEach(n => {
                    const r = n.rule || {}
                    const hasRule = Object.values(r).some(v => v)
                    if (!hasRule) return
                    xfr += `${n.name}:\n`
                    Object.entries(r).forEach(([k, v]) => { if (v) xfr += `  ${k} ${v}\n` })
                    xfr += '\n'
                  })

                  // Build MP from nodes/edges
                  let mp = ''
                  updatedNodes.forEach(n => { mp += `NODE ${n.name} : ${n.type}\n` })
                  mp += '\n'
                  result.edges.forEach(e => { mp += `${e.from} -> ${e.to}\n` })

                  const form = new FormData()
                  form.append('mp', new File([mp], 'edited.mp'))
                  if (xfr.trim()) form.append('xfr', new File([xfr], 'edited.xfr'))
                  form.append('target', target)

                  setLoading(true)
                  const startTime = Date.now()
                  fetch(COMPILE_URL, { method: 'POST', body: form })
                    .then(res => res.json())
                    .then(data => { setCompileTime(Date.now() - startTime); setResult(data) })
                    .finally(() => setLoading(false))
                }} />
              : <div style={{
                  position: 'absolute', inset: 0, display: 'flex',
                  alignItems: 'center', justifyContent: 'center', color: t.dim, fontSize: 14,
                }}>Upload a .mp file and click Compile to visualize the DAG</div>
            }
          </div>

          {/* DB Sources Alert — Two Programs */}
          {result?.has_db_sources && (
            <div style={{
              borderTop: `1px solid #f59e0b40`, background: '#f59e0b08',
              padding: '12px 20px', display: 'flex', alignItems: 'center', gap: 16,
            }}>
              <span style={{ fontSize: 24 }}>🗄️</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#f59e0b' }}>
                  Se detectaron {result.db_sources_count} fuente(s) de base de datos — Se generan 2 programas
                </div>
                <div style={{ fontSize: 11, color: t.dim, marginTop: 2 }}>
                  Programa 1: Extractor (DB → S3) | Programa 2: Transformer (S3 → S3)
                </div>
              </div>
              <button onClick={() => {
                const blob = new Blob([result.extractor_code], { type: 'text/plain' })
                const url = URL.createObjectURL(blob); const a = document.createElement('a')
                a.href = url; a.download = 'bnx_extractor_job.py'; a.click(); URL.revokeObjectURL(url)
              }} style={{
                padding: '8px 16px', borderRadius: 6, cursor: 'pointer',
                background: '#f59e0b', color: '#000', border: 'none', fontSize: 12, fontWeight: 700,
              }}>📥 Extractor</button>
              <button onClick={() => {
                const code = result.code || '# No transform code generated'
                const blob = new Blob([code], { type: 'text/plain' })
                const url = URL.createObjectURL(blob); const a = document.createElement('a')
                a.href = url; a.download = `bnx_${target}_transform_job.py`; a.click(); URL.revokeObjectURL(url)
              }} style={{
                padding: '8px 16px', borderRadius: 6, cursor: 'pointer',
                background: '#22c55e', color: '#000', border: 'none', fontSize: 12, fontWeight: 700,
              }}>📥 Transformer</button>
            </div>
          )}

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
                  {result.refactor
                    ? `🔄 Refactored Code (${result.refactored_lines} lines — ${result.total_changes} changes)`
                    : `Generated ${target === 'flink' ? 'Flink' : target === 'spark' ? 'Spark' : 'Glue'} Code (${result.code.split('\n').length} lines)`
                  }
                </span>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <button
                    style={{ ...iconBtn, padding: '4px 10px', fontSize: 13 }}
                    onClick={(e) => { e.stopPropagation(); setExpandedPanel('code') }}
                  >🔲 Fullscreen</button>
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
                result.code && result.code.length > 5000 ? (
                  <div style={{ padding: 20, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, flex: 1, justifyContent: 'center' }}>
                    <style>{`@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>
                    <span style={{ fontSize: 48 }}>⚠️</span>
                    <span style={{ fontSize: 16, color: t.text, fontWeight: 700, textAlign: 'center' }}>
                      CÓDIGO MUY GRANDE — DESCARGA REQUERIDA
                    </span>
                    <span style={{ fontSize: 13, color: t.muted, textAlign: 'center' }}>
                      {result.code.split('\n').length} líneas · {(result.code.length / 1024).toFixed(1)} KB — El código no se puede mostrar en pantalla
                    </span>
                    <button onClick={() => {
                      const blob = new Blob([result.code], { type: 'text/plain' })
                      const url = URL.createObjectURL(blob)
                      const a = document.createElement('a')
                      a.href = url; a.download = `bnx_${target}_job.py`; a.click()
                      URL.revokeObjectURL(url)
                    }} style={{
                      padding: '14px 32px', borderRadius: 8, cursor: 'pointer',
                      background: '#22c55e', color: '#000', border: 'none',
                      fontSize: 16, fontWeight: 700,
                      animation: 'blink 1.5s ease-in-out infinite',
                      boxShadow: '0 0 20px rgba(34,197,94,0.4)',
                    }}>📥 DESCARGAR CÓDIGO AQUÍ</button>
                    <pre style={{
                      padding: 12, fontSize: 11, color: t.dim,
                      fontFamily: 'monospace', whiteSpace: 'pre', overflowY: 'auto',
                      maxHeight: 120, width: '100%', margin: 0,
                      background: t.bg || '#0f1117', borderRadius: 6,
                      border: `1px solid ${t.border}`,
                    }}>{result.code.slice(0, 600)}...{'\n\n'}# ... ({result.code.split('\n').length - 15} líneas más)</pre>
                  </div>
                ) : (
                  <pre style={{
                    padding: 16, fontSize: 14, color: t.muted,
                    fontFamily: 'monospace', whiteSpace: 'pre', overflowY: 'auto',
                    flex: 1, lineHeight: 1.6, margin: 0,
                  }}>{result.code}</pre>
                )
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
