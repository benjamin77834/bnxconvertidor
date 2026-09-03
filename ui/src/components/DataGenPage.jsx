import { useState, useRef, useEffect } from 'react'
import { COMPILE_URL, PIPELINE_URL, PIPELINE_STATUS_URL } from '../config'
import CostEstimateCard from './CostEstimateCard'
import { metricsFromResult } from '../costEstimator'

// El endpoint /datagen vive en el mismo origen que /compile
const DATAGEN_URL = COMPILE_URL.replace(/\/compile$/, '/datagen')
const RUNTEST_URL = COMPILE_URL.replace(/\/compile$/, '/runtest')
const RUNTEST_STREAM_URL = COMPILE_URL.replace(/\/compile$/, '/runtest/stream')
const OPTIMIZE_COMPARE_URL = COMPILE_URL.replace(/\/compile$/, '/optimize/compare')
const AWSCODE_URL = COMPILE_URL.replace(/\/compile$/, '/datagen/awscode')
const DOWNLOAD_URL = COMPILE_URL.replace(/\/compile$/, '/download')

const TYPES = ['string', 'integer', 'decimal', 'date', 'datetime', 'boolean']
const PII_CATEGORIES = ['', 'name', 'email', 'phone', 'card', 'account', 'ssn', 'address', 'dob', 'id']

// Etiqueta visual para entrada/salida
const IO_META = {
  input: { label: '⬇️ Entrada', color: '#22c55e' },
  output: { label: '⬆️ Salida', color: '#f59e0b' },
}
const ioMeta = (io) => IO_META[io] || IO_META.output

export default function DataGenPage({ theme, graphMp = '', graphXfr = '', compiledCode = '', compiledTarget = '', graphName = '', graphDescription = '' }) {
  const t = theme || {}
  const [mode, setMode] = useState('graph') // 'graph' | 'manual'

  // --- Modo grafo ---
  const [mp, setMp] = useState('')
  const [xfr, setXfr] = useState('')
  const [dml, setDml] = useState('')

  const hasCompilerGraph = Boolean((graphMp || '').trim())

  // Trae el grafo actual del Compiler a los campos de esta seccion
  const useCompilerGraph = () => {
    setMp(graphMp || '')
    setXfr(graphXfr || '')
    setMode('graph')
  }

  // --- Modo manual ---
  const [columns, setColumns] = useState([
    { name: 'customer_name', type: 'string', pii: 'name' },
    { name: 'risk_score', type: 'decimal', pii: '' },
    { name: 'last_updated_date', type: 'date', pii: '' },
  ])
  const [nodeName, setNodeName] = useState('manual_dataset')

  // --- Comunes ---
  const [nRows, setNRows] = useState(10)
  const [format, setFormat] = useState('csv')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null) // {mode, schema, datasets}
  const [activeDataset, setActiveDataset] = useState(0)
  const [ioFilter, setIoFilter] = useState('all') // 'all' | 'input' | 'output'

  // --- Ejecutar prueba PySpark (consola en vivo) ---
  const [running, setRunning] = useState(false)
  const [runTimeout, setRunTimeout] = useState(300) // limite de tiempo (s), configurable
  // URL base de la EC2 interna de DataLab (subnet privada). Configurable y
  // persistida: cada quien pega la IP privada de la instancia cuando exista
  // (p.ej. http://10.0.1.23:8081). Vacio = solo esta disponible "Probar local".
  const [ec2Url, setEc2Url] = useState(() => {
    try { return localStorage.getItem('bnx_ec2_url') || '' } catch { return '' }
  })
  const [showEc2Config, setShowEc2Config] = useState(false)
  const [runResult, setRunResult] = useState(null) // {ok, summary, reads, writes}
  const [consoleLines, setConsoleLines] = useState([]) // lineas en vivo
  const [localDownloads, setLocalDownloads] = useState([]) // [{name, path}] CSV de resultado local
  const [runReport, setRunReport] = useState(null) // {totals, inputs, outputs, flow, flow_counts}

  // --- Comparar performance (original vs optimizado) ---
  const [comparing, setComparing] = useState(false)
  const [compareResult, setCompareResult] = useState(null) // {original, optimized, speedup, faster_pct, equivalent, ...}

  // --- Enviar a AWS ---
  const [awsSending, setAwsSending] = useState(false)
  const [awsLogs, setAwsLogs] = useState([])
  const [awsStatus, setAwsStatus] = useState('') // '', 'running', 'ok', 'error'
  const awsPollRef = useRef(null)
  const [awsBucket, setAwsBucket] = useState('datalake-bnx-scripts-dev')
  const [awsRegion] = useState('us-east-1')
  const [awsRole] = useState('arn:aws:iam::107094296911:role/datalake-glue-role-dev')
  const [awsJobName, setAwsJobName] = useState('datalake-bnx-datagen-spark-dev')
  const [awsDownloads, setAwsDownloads] = useState([]) // [{name, url}] presigned URLs

  const isPySpark = compiledTarget === 'spark'
  const hasCode = Boolean((compiledCode || '').trim())

  const awsLog = (m) => setAwsLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${m}`])

  useEffect(() => () => { if (awsPollRef.current) clearInterval(awsPollRef.current) }, [])

  const sendToAWS = async () => {
    setAwsSending(true)
    setAwsStatus('running')
    setAwsLogs([])
    try {
      const inputs = (result?.datasets || []).filter(d => d.io === 'input')
      const datasets = inputs.length ? inputs : (result?.datasets || [])

      // 1. Generar codigo autocontenido (datos embebidos + escrituras S3 reales)
      awsLog('Generando codigo autocontenido (datos sinteticos embebidos)...')
      const genRes = await fetch(AWSCODE_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        // Enviamos el grafo (mp/xfr) para que el servidor REGENERE el PySpark
        // fresco; asi el codigo que va a AWS nunca es una version vieja cacheada.
        body: JSON.stringify({ code: compiledCode, mp: graphMp, xfr: graphXfr, datasets, keep_writes: true, bucket: awsBucket, job_name: awsJobName }),
      })
      const genData = await genRes.json()
      if (genData.error) { awsLog('ERROR: ' + genData.error); setAwsStatus('error'); setAwsSending(false); return }
      const awsCode = genData.code
      awsLog(`Codigo listo: ${awsCode.split('\n').length} lineas`)
      if (genData.output_paths?.length) {
        awsLog(`Salida se escribira en: ${genData.output_paths.map(o => o.path).join(', ')}`)
      }
      setAwsDownloads([])

      // 2. Despachar al pipeline AWS (mismo flujo que PipelinePage)
      awsLog('Subiendo a S3 y ejecutando en AWS Glue...')
      const form = new FormData()
      form.append('code', awsCode)
      form.append('target', 'spark')
      form.append('bucket', awsBucket)
      form.append('region', awsRegion)
      form.append('job_name', awsJobName)
      form.append('role', awsRole)
      form.append('action', 'run')

      const res = await fetch(PIPELINE_URL, { method: 'POST', body: form })
      const data = await res.json()
      for (const step of (data.steps || [])) {
        awsLog(`${step.step}: ${step.status} — ${step.detail || ''}`)
      }
      if (data.status === 'started' && data.run_id) {
        awsLog(`Job iniciado! RunId: ${data.run_id}`)
        startAwsPolling(data.job_name || awsJobName, data.run_id)
      } else if (data.status === 'failed') {
        awsLog('Pipeline FALLO en la preparacion')
        setAwsStatus('error')
        setAwsSending(false)
      } else {
        awsLog('Respuesta inesperada del pipeline: ' + JSON.stringify(data).slice(0, 200))
        setAwsStatus('error')
        setAwsSending(false)
      }
    } catch (e) {
      awsLog('ERROR de red: ' + e.message)
      setAwsStatus('error')
      setAwsSending(false)
    }
  }

  const startAwsPolling = (jn, rid) => {
    let attempts = 0
    awsPollRef.current = setInterval(async () => {
      attempts++
      try {
        const form = new FormData()
        form.append('job_name', jn)
        form.append('run_id', rid)
        form.append('region', awsRegion)
        const res = await fetch(PIPELINE_STATUS_URL, { method: 'POST', body: form })
        const data = await res.json()
        awsLog(`[${attempts}] Status: ${data.status}${data.duration ? ` (${data.duration}s)` : ''}`)

        // Extraer presigned URLs de descarga de los logs del job (si el status los trae)
        const logText = [data.logs, data.output, data.stdout, data.error].filter(Boolean).join('\n')
        if (logText) {
          const found = []
          const re = /\[AWS\]\s*DOWNLOAD\|([^|]+)\|(\S+)/g
          let m
          while ((m = re.exec(logText)) !== null) found.push({ name: m[1], url: m[2] })
          if (found.length) {
            setAwsDownloads(prev => {
              const seen = new Set(prev.map(d => d.url))
              return [...prev, ...found.filter(f => !seen.has(f.url))]
            })
          }
        }

        if (data.status === 'SUCCEEDED') {
          awsLog(`JOB EXITOSO en ${data.duration}s — output en S3`)
          setAwsStatus('ok'); clearInterval(awsPollRef.current); setAwsSending(false)
        } else if (data.status === 'FAILED' || data.status === 'STOPPED') {
          awsLog(`JOB FALLO: ${data.error || data.status}`)
          setAwsStatus('error'); clearInterval(awsPollRef.current); setAwsSending(false)
        } else if (attempts > 40) {
          awsLog('TIMEOUT: 10 min sin completar')
          clearInterval(awsPollRef.current); setAwsSending(false)
        }
      } catch (e) {
        awsLog('Error polling: ' + e.message)
      }
    }, 15000)
  }

  const runTest = async (target = 'local') => {
    // target: 'local' = mismo origen (Mac de la persona / server local)
    //         'ec2'   = EC2 interna de DataLab (URL configurable en ec2Url)
    let streamUrl = RUNTEST_STREAM_URL
    if (target === 'ec2') {
      const base = (ec2Url || '').trim().replace(/\/+$/, '')
      if (!base) {
        setShowEc2Config(true)
        setRunResult({ ok: false, summary: 'Configura primero la URL de la EC2 interna (⚙️).' })
        return
      }
      streamUrl = `${base}/runtest/stream`
    }
    setRunning(true)
    setRunResult(null)
    setLocalDownloads([])
    setRunReport(null)
    setConsoleLines([{
      text: target === 'ec2'
        ? `[*] Iniciando prueba en EC2 interna (${ec2Url})...`
        : '[*] Iniciando ejecución de prueba local...',
      kind: 'info',
    }])
    try {
      const inputs = (result?.datasets || []).filter(d => d.io === 'input')
      const datasets = inputs.length ? inputs : (result?.datasets || [])
      const res = await fetch(streamUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Enviamos tambien el grafo (mp/xfr) para que el servidor REGENERE el
        // PySpark fresco y la prueba nunca use codigo viejo cacheado en el navegador.
        body: JSON.stringify({ code: compiledCode, mp: graphMp, xfr: graphXfr, datasets, timeout: runTimeout, job_name: (graphName || awsJobName) }),
      })
      if (!res.ok || !res.body) {
        let msg = `HTTP ${res.status}`
        try { const j = await res.json(); msg = j.error || msg } catch {}
        setRunResult({ ok: false, summary: msg })
        setRunning(false)
        return
      }

      // Leer el stream SSE incrementalmente
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let finished = false

      while (!finished) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() // resto incompleto
        for (const part of parts) {
          const line = part.replace(/^data:\s*/, '').trim()
          if (!line) continue
          let evt
          try { evt = JSON.parse(line) } catch { continue }
          if (evt.type === 'line') {
            setConsoleLines(prev => [...prev, { text: evt.text, kind: classifyLine(evt.text) }])
          } else if (evt.type === 'done') {
            setRunResult({ ok: evt.ok, summary: evt.summary, reads: evt.reads, writes: evt.writes })
            if (Array.isArray(evt.downloads)) setLocalDownloads(evt.downloads)
            if (evt.report) setRunReport(evt.report)
            finished = true
          }
        }
      }
    } catch (e) {
      setRunResult({ ok: false, summary: `Error de red: ${e.message}` })
      setConsoleLines(prev => [...prev, { text: `Error: ${e.message}`, kind: 'error' }])
    } finally {
      setRunning(false)
    }
  }

  // Corre el codigo ORIGINAL y el OPTIMIZADO con los mismos datos y compara
  // tiempos + equivalencia de salidas. El backend regenera fresco desde el grafo.
  const comparePerf = async () => {
    setComparing(true)
    setCompareResult(null)
    try {
      const inputs = (result?.datasets || []).filter(d => d.io === 'input')
      const datasets = inputs.length ? inputs : (result?.datasets || [])
      const res = await fetch(OPTIMIZE_COMPARE_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: compiledCode, mp: graphMp, xfr: graphXfr,
          datasets, timeout: 300, job_name: (graphName || awsJobName) }),
      })
      const data = await res.json()
      if (data.error) { setCompareResult({ error: data.error }); return }
      setCompareResult(data)
    } catch (e) {
      setCompareResult({ error: e.message })
    } finally {
      setComparing(false)
    }
  }

  // Clasifica una linea para colorearla en la consola
  const classifyLine = (text) => {
    if (/Traceback|Exception|Error|ERROR|SQLSTATE/.test(text)) return 'error'
    if (/\[>\] SOURCE|READ /.test(text)) return 'source'
    if (/\[~\] JOIN|JOIN:/.test(text)) return 'join'
    if (/\[\*\] SINK|\[>\] SINK|WRITE /.test(text)) return 'sink'
    if (/\[~\] TRANSFORM|SORT|DEDUP|FILTER/.test(text)) return 'transform'
    if (/\[ok\]|Ejecución OK/.test(text)) return 'ok'
    return 'plain'
  }

  const card = {
    background: t.card || '#1e2433',
    border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 16,
  }
  const label = { fontSize: 11, color: t.dim || '#64748b', textTransform: 'uppercase', letterSpacing: 1 }
  const inputStyle = {
    padding: '6px 10px', borderRadius: 6, fontSize: 13,
    background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
    color: t.text || '#e2e8f0', outline: 'none',
  }
  const btn = (active, color = '#6366f1') => ({
    padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 13, fontWeight: 500,
    background: active ? color + '20' : 'transparent',
    border: `1px solid ${active ? color : (t.border || '#334155')}`,
    color: active ? color : (t.muted || '#94a3b8'),
  })
  const textarea = {
    width: '100%', minHeight: 120, maxHeight: 240, padding: 10, borderRadius: 8,
    background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
    color: t.text || '#e2e8f0', fontSize: 12, fontFamily: 'monospace',
    lineHeight: 1.5, resize: 'vertical', outline: 'none',
  }

  // -------------------------------------------------------------------------
  // Modo manual: editar columnas
  // -------------------------------------------------------------------------
  const addColumn = () =>
    setColumns(c => [...c, { name: `campo_${c.length + 1}`, type: 'string', pii: '' }])
  const removeColumn = (i) =>
    setColumns(c => c.filter((_, idx) => idx !== i))
  const updateColumn = (i, key, value) =>
    setColumns(c => c.map((col, idx) => (idx === i ? { ...col, [key]: value } : col)))

  // -------------------------------------------------------------------------
  // Cargar esquema desde grafo hacia el editor manual (para "traer el grafo")
  // -------------------------------------------------------------------------
  const importSchemaToManual = (schemaColumns, node) => {
    setColumns(schemaColumns.map(c => ({
      name: c.name, type: c.type, pii: c.pii || '',
    })))
    if (node) setNodeName(node)
    setMode('manual')
  }

  // -------------------------------------------------------------------------
  // Generar
  // -------------------------------------------------------------------------
  const generate = async () => {
    setLoading(true)
    setError('')
    setResult(null)
    setActiveDataset(0)
    try {
      let payload
      if (mode === 'manual') {
        payload = {
          columns: columns.map(c => ({
            name: c.name,
            type: c.type,
            // pii === '' → dejar que el backend auto-detecte; explícito si se eligió
            pii: c.pii === '' ? null : c.pii,
          })),
          node_name: nodeName,
          n_rows: Number(nRows), format,
        }
      } else {
        if (!mp.trim()) { setError('Pega o carga un .mp primero'); setLoading(false); return }
        payload = { mp, xfr, dml, n_rows: Number(nRows), format }
      }
      const res = await fetch(DATAGEN_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (data.error) { setError(data.error); return }
      setResult(data)
    } catch (e) {
      setError(`Error de red: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const downloadDataset = (ds) => {
    const ext = ds.format === 'json' ? 'json' : 'csv'
    const mime = ds.format === 'json' ? 'application/json' : 'text/csv'
    const blob = new Blob([ds.content], { type: mime })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${ds.node || 'dataset'}_redactada.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  }

  const onFile = (setter) => (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    const reader = new FileReader()
    reader.onload = ev => setter(ev.target.result || '')
    reader.readAsText(f)
  }

  // Datasets filtrados por entrada/salida
  const allDatasets = result?.datasets || []
  const hasInput = allDatasets.some(d => d.io === 'input')
  const hasOutput = allDatasets.some(d => d.io === 'output')
  const visibleDatasets = allDatasets.filter(d =>
    ioFilter === 'all' ? true : d.io === ioFilter
  )
  const ds = visibleDatasets[activeDataset] || visibleDatasets[0]

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Header */}
      <div>
        <h2 style={{ margin: 0, fontSize: 22, color: t.text || '#e2e8f0' }}>🧪 Data Redactada</h2>
        <p style={{ margin: '4px 0 0', fontSize: 13, color: t.muted || '#94a3b8' }}>
          Genera datos sintéticos con PII enmascarada. Desde el grafo convertido o definiendo el esquema manualmente.
        </p>
      </div>

      {/* Estado del codigo del Compiler (diagnostico) */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, fontSize: 12,
        borderRadius: 8, padding: '8px 12px',
        background: hasCode ? '#22c55e10' : '#f59e0b10',
        border: `1px solid ${hasCode ? '#22c55e40' : '#f59e0b40'}`,
        color: hasCode ? '#22c55e' : '#f59e0b',
      }}>
        {hasCode
          ? `✅ Código del Compiler cargado: ${compiledCode.split('\n').length} líneas · target=${compiledTarget || '?'}`
          : '⚠️ No llegó código del Compiler. Compila un grafo (target Spark) en la pestaña Compiler y volvé aquí.'}
      </div>

      {/* Selector de modo */}
      <div style={{ display: 'flex', gap: 8 }}>
        <button style={btn(mode === 'graph')} onClick={() => setMode('graph')}>📊 Desde grafo</button>
        <button style={btn(mode === 'manual')} onClick={() => setMode('manual')}>✏️ Manual</button>
      </div>

      {/* --- MODO GRAFO --- */}
      {mode === 'graph' && (
        <div style={{ ...card, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={label}>Grafo (.mp requerido, .xfr y .dml opcionales)</span>
            {hasCompilerGraph && (
              <button onClick={useCompilerGraph} style={btn(true, '#22c55e')}>
                🔗 Usar grafo del Compiler
              </button>
            )}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            {[
              { lbl: '.mp', val: mp, set: setMp, color: '#22c55e' },
              { lbl: '.xfr', val: xfr, set: setXfr, color: '#6366f1' },
              { lbl: '.dml', val: dml, set: setDml, color: '#f59e0b' },
            ].map(f => (
              <div key={f.lbl} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 12, color: f.color, fontWeight: 600 }}>{f.lbl}</span>
                  <label style={{ ...btn(false), padding: '2px 8px', fontSize: 10 }}>
                    📁 Cargar
                    <input type="file" style={{ display: 'none' }} onChange={onFile(f.set)} />
                  </label>
                </div>
                <textarea value={f.val} onChange={e => f.set(e.target.value)}
                  placeholder={`Pega el contenido ${f.lbl}...`}
                  style={{ ...textarea, borderColor: f.color + '40' }} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* --- MODO MANUAL --- */}
      {mode === 'manual' && (
        <div style={{ ...card, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={label}>Esquema manual</span>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: 11, color: t.dim }}>Dataset:</span>
              <input value={nodeName} onChange={e => setNodeName(e.target.value)}
                style={{ ...inputStyle, width: 160, fontSize: 12 }} />
            </div>
          </div>

          {/* Tabla de columnas */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.2fr 1.2fr 40px', gap: 8, fontSize: 10, color: t.dim, textTransform: 'uppercase' }}>
              <span>Nombre</span><span>Tipo</span><span>PII (redacción)</span><span></span>
            </div>
            {columns.map((col, i) => (
              <div key={i} style={{ display: 'grid', gridTemplateColumns: '2fr 1.2fr 1.2fr 40px', gap: 8, alignItems: 'center' }}>
                <input value={col.name} onChange={e => updateColumn(i, 'name', e.target.value)}
                  style={inputStyle} placeholder="nombre_campo" />
                <select value={col.type} onChange={e => updateColumn(i, 'type', e.target.value)} style={inputStyle}>
                  {TYPES.map(ty => <option key={ty} value={ty}>{ty}</option>)}
                </select>
                <select value={col.pii} onChange={e => updateColumn(i, 'pii', e.target.value)} style={inputStyle}>
                  {PII_CATEGORIES.map(p => <option key={p} value={p}>{p === '' ? '(auto)' : p}</option>)}
                </select>
                <button onClick={() => removeColumn(i)} style={{
                  ...btn(false, '#ef4444'), padding: '4px', fontSize: 14,
                }} title="Quitar columna">✕</button>
              </div>
            ))}
          </div>
          <button onClick={addColumn} style={{ ...btn(false, '#22c55e'), alignSelf: 'flex-start' }}>
            ➕ Agregar columna
          </button>
        </div>
      )}

      {/* --- CONTROLES --- */}
      <div style={{ ...card, display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span style={label}>Filas</span>
          <input type="number" min={1} max={10000} value={nRows}
            onChange={e => setNRows(e.target.value)} style={{ ...inputStyle, width: 100 }} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span style={label}>Formato</span>
          <div style={{ display: 'flex', gap: 6 }}>
            <button style={btn(format === 'csv')} onClick={() => setFormat('csv')}>CSV</button>
            <button style={btn(format === 'json')} onClick={() => setFormat('json')}>JSON</button>
          </div>
        </div>
        <div style={{ flex: 1 }} />
        <button onClick={generate} disabled={loading} style={{
          padding: '10px 24px', borderRadius: 8, cursor: loading ? 'wait' : 'pointer',
          background: '#22c55e', color: '#000', border: 'none', fontSize: 14, fontWeight: 700,
          opacity: loading ? 0.6 : 1,
        }}>{loading ? '⏳ Generando...' : '🧪 Generar datos'}</button>
      </div>

      {/* --- ERROR --- */}
      {error && (
        <div style={{ ...card, borderColor: '#ef444440', background: '#ef444410', color: '#ef4444', fontSize: 13 }}>
          ⚠️ {error}
        </div>
      )}

      {/* --- SIN DATASETS: mensaje --- */}
      {result && result.datasets && result.datasets.length === 0 && (
        <div style={{ ...card, borderColor: '#f59e0b40', background: '#f59e0b10', color: '#f59e0b', fontSize: 13, lineHeight: 1.5 }}>
          ℹ️ {result.message || 'No se generaron datos. El grafo no expone campos. Usa el modo Manual o adjunta un .dml/.xfr.'}
          <div style={{ marginTop: 10 }}>
            <button onClick={() => setMode('manual')} style={btn(true, '#f59e0b')}>
              ✏️ Cambiar a modo Manual
            </button>
          </div>
        </div>
      )}

      {/* --- RESULTADO --- */}
      {allDatasets.length > 0 && (
        <div style={{ ...card, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            <span style={label}>
              Resultado · {result.mode === 'graph' ? `${allDatasets.length} dataset(s)` : 'manual'}
              {hasInput && hasOutput && ' · entrada + salida'}
            </span>
            {ds && (
              <button onClick={() => downloadDataset(ds)} style={btn(true, '#22c55e')}>
                📥 Descargar {ds.node} ({ds.format.toUpperCase()})
              </button>
            )}
          </div>

          {/* Filtro entrada / salida (solo si hay de ambos) */}
          {hasInput && hasOutput && (
            <div style={{ display: 'flex', gap: 6 }}>
              <button style={btn(ioFilter === 'all')} onClick={() => { setIoFilter('all'); setActiveDataset(0) }}>Todos</button>
              <button style={btn(ioFilter === 'input', '#22c55e')} onClick={() => { setIoFilter('input'); setActiveDataset(0) }}>⬇️ Entrada</button>
              <button style={btn(ioFilter === 'output', '#f59e0b')} onClick={() => { setIoFilter('output'); setActiveDataset(0) }}>⬆️ Salida</button>
            </div>
          )}

          {/* Selector de dataset (cuando hay varios) */}
          {visibleDatasets.length > 1 && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {visibleDatasets.map((d, i) => {
                const io = ioMeta(d.io)
                return (
                  <button key={i} style={btn(ds === d, io.color)} onClick={() => setActiveDataset(i)}>
                    <span style={{ fontSize: 10 }}>{io.label}</span> {d.node} ({d.columns.length})
                  </button>
                )
              })}
            </div>
          )}

          {/* Etiqueta del dataset activo (entrada/salida) */}
          {ds && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <span style={{
                padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                background: ioMeta(ds.io).color + '20', color: ioMeta(ds.io).color,
                border: `1px solid ${ioMeta(ds.io).color}40`,
              }}>{ioMeta(ds.io).label} · {ds.node}</span>
              <span style={{ fontSize: 11, color: t.dim }}>
                {ds.io === 'input'
                  ? 'Datos que alimentan el job (lo que se lee).'
                  : 'Datos que el job produce (resultado esperado).'}
              </span>
              <div style={{ flex: 1 }} />
              <button onClick={() => importSchemaToManual(ds.columns, ds.node)} style={{ ...btn(false), fontSize: 11 }}>
                ✏️ Editar este esquema manualmente
              </button>
            </div>
          )}

          {/* Vista previa de tabla */}
          {ds && (
            <div style={{ overflowX: 'auto', border: `1px solid ${t.border || '#334155'}`, borderRadius: 8 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr>
                    {ds.columns.map(c => (
                      <th key={c.name} style={{
                        padding: '8px 12px', textAlign: 'left', whiteSpace: 'nowrap',
                        background: t.sidebar || '#161b27', color: t.muted || '#94a3b8',
                        borderBottom: `1px solid ${t.border || '#334155'}`,
                      }}>
                        {c.name}
                        <span style={{ fontSize: 9, color: t.dim, marginLeft: 4 }}>{c.type}</span>
                        {c.pii && <span style={{ fontSize: 9, color: '#ef4444', marginLeft: 4 }}>🔒{c.pii}</span>}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ds.rows.slice(0, 50).map((row, ri) => (
                    <tr key={ri}>
                      {ds.columns.map(c => (
                        <td key={c.name} style={{
                          padding: '6px 12px', whiteSpace: 'nowrap',
                          color: t.text || '#e2e8f0',
                          borderBottom: `1px solid ${(t.border || '#334155')}40`,
                        }}>{String(row[c.name])}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {ds && ds.rows.length > 50 && (
            <span style={{ fontSize: 11, color: t.dim }}>
              Mostrando 50 de {ds.rows.length} filas. Descarga para ver todas.
            </span>
          )}
        </div>
      )}

      {/* --- EJECUTAR PRUEBA PYSPARK --- */}
      {result?.datasets?.length > 0 && (
        <div style={{ ...card, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <span style={label}>▶️ Ejecutar prueba (PySpark)</span>
              <span style={{ fontSize: 11, color: t.dim }}>
                Corre el código del Compiler con estos datos de entrada y comprueba si funciona.
                <b> Local</b> usa tu máquina; <b>EC2 interno</b> usa la instancia privada de DataLab.
              </span>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: t.dim }}
                title="Tiempo máximo antes de cortar el job. Súbelo para grafos grandes.">
                ⏱️ Límite
                <select
                  value={runTimeout}
                  onChange={e => setRunTimeout(Number(e.target.value))}
                  disabled={running || comparing}
                  style={{
                    padding: '6px 8px', borderRadius: 6, fontSize: 12,
                    background: t.card || '#1e2433', color: t.text || '#e2e8f0',
                    border: `1px solid ${t.border || '#334155'}`, cursor: 'pointer',
                  }}
                >
                  <option value={180}>3 min</option>
                  <option value={300}>5 min</option>
                  <option value={600}>10 min</option>
                  <option value={900}>15 min</option>
                </select>
              </label>
              <button
                onClick={() => runTest('local')}
                disabled={running || comparing || !hasCode || !isPySpark}
                title="Corre en tu propia máquina (server local)"
                style={{
                  padding: '10px 18px', borderRadius: 8,
                  cursor: (running || !hasCode || !isPySpark) ? 'not-allowed' : 'pointer',
                  background: (!hasCode || !isPySpark) ? (t.border || '#334155') : '#6366f1',
                  color: '#fff', border: 'none', fontSize: 14, fontWeight: 700,
                  opacity: running ? 0.6 : 1,
                }}
              >{running ? '⏳ Ejecutando...' : '💻 Probar local'}</button>
              <button
                onClick={() => runTest('ec2')}
                disabled={running || comparing || !hasCode || !isPySpark}
                title={ec2Url ? `Corre en la EC2 interna: ${ec2Url}` : 'Configura la URL de la EC2 interna con el engranaje'}
                style={{
                  padding: '10px 18px', borderRadius: 8,
                  cursor: (running || !hasCode || !isPySpark) ? 'not-allowed' : 'pointer',
                  background: (!hasCode || !isPySpark) ? (t.border || '#334155') : (ec2Url ? '#0ea5e9' : (t.border || '#334155')),
                  color: '#fff', border: 'none', fontSize: 14, fontWeight: 700,
                  opacity: running ? 0.6 : 1,
                }}
              >{running ? '⏳ Ejecutando...' : '☁️ Probar en EC2 (interno)'}</button>
              <button
                onClick={() => setShowEc2Config(v => !v)}
                title="Configurar URL de la EC2 interna de DataLab"
                style={{
                  padding: '10px 12px', borderRadius: 8, cursor: 'pointer',
                  background: 'transparent', color: t.dim || '#64748b',
                  border: `1px solid ${t.border || '#334155'}`, fontSize: 14,
                }}
              >⚙️</button>
              <button
                onClick={comparePerf}
                disabled={running || comparing || !hasCode || !isPySpark}
                title="Corre el original y el optimizado con estos datos y compara tiempos"
                style={{
                  padding: '10px 18px', borderRadius: 8,
                  cursor: (comparing || !hasCode || !isPySpark) ? 'not-allowed' : 'pointer',
                  background: (!hasCode || !isPySpark) ? (t.border || '#334155') : '#f59e0b',
                  color: '#fff', border: 'none', fontSize: 14, fontWeight: 700,
                  opacity: comparing ? 0.6 : 1,
                }}
              >{comparing ? '⏳ Comparando...' : '⚡ Comparar performance'}</button>
            </div>
          </div>

          {/* Config de la EC2 interna (URL privada de DataLab) */}
          {showEc2Config && (
            <div style={{
              background: t.bg || '#0f1117', borderRadius: 8, padding: 12,
              border: `1px solid ${t.border || '#334155'}`, display: 'flex',
              flexDirection: 'column', gap: 6,
            }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: t.text || '#e2e8f0' }}>
                ☁️ URL de la EC2 interna (DataLab)
              </span>
              <span style={{ fontSize: 11, color: t.dim }}>
                Instancia privada en la VPC de DataLab. Solo accesible desde la red del banco / VPN.
                Pega su IP privada con el puerto 8081, p.ej. <code>http://10.0.1.23:8081</code>. Se guarda en tu navegador.
              </span>
              <div style={{ display: 'flex', gap: 8 }}>
                <input
                  type="text"
                  value={ec2Url}
                  onChange={e => setEc2Url(e.target.value)}
                  placeholder="http://10.x.x.x:8081"
                  style={{
                    flex: 1, padding: '8px 10px', borderRadius: 6, fontSize: 13,
                    background: t.card || '#1e2433', color: t.text || '#e2e8f0',
                    border: `1px solid ${t.border || '#334155'}`,
                  }}
                />
                <button
                  onClick={() => {
                    const v = (ec2Url || '').trim()
                    try { localStorage.setItem('bnx_ec2_url', v) } catch {}
                    setEc2Url(v)
                    setShowEc2Config(false)
                  }}
                  style={{
                    padding: '8px 16px', borderRadius: 6, cursor: 'pointer',
                    background: '#0ea5e9', color: '#fff', border: 'none', fontSize: 13, fontWeight: 700,
                  }}
                >Guardar</button>
              </div>
            </div>
          )}

          {/* Resultado de la comparacion original vs optimizado */}
          {compareResult && !compareResult.error && (
            <div style={{
              background: t.bg || '#0f1117', borderRadius: 10, padding: 14,
              border: `1px solid #f59e0b40`, display: 'flex', flexDirection: 'column', gap: 12,
            }}>
              <span style={{ fontSize: 16, fontWeight: 700, color: '#f59e0b' }}>
                ⚡ Validación de optimización ({compareResult.total_changes} reglas aplicadas)
              </span>

              {/* Lo principal: equivalencia de salidas */}
              <div style={{
                padding: 12, borderRadius: 8,
                background: compareResult.equivalent ? '#22c55e15' : '#f59e0b15',
                border: `1px solid ${compareResult.equivalent ? '#22c55e' : '#f59e0b'}`,
              }}>
                <div style={{ fontSize: 18, fontWeight: 700, color: compareResult.equivalent ? '#22c55e' : '#f59e0b' }}>
                  {compareResult.equivalent
                    ? '✅ Código optimizado produce las mismas salidas que el original'
                    : '⚠️ Las salidas difieren — revisar'}
                </div>
                <div style={{ fontSize: 14, color: t.muted, marginTop: 4 }}>
                  {compareResult.equivalent
                    ? 'La optimización no cambió la lógica. Mismo número de filas en todas las tablas de salida.'
                    : 'Algo cambió entre original y optimizado (no debería pasar con reglas seguras).'}
                </div>
              </div>

              {/* Optimizaciones aplicadas (lo que mejora en AWS) */}
              <div style={{ fontSize: 15, color: t.text || '#e2e8f0', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                <span>🧠 cache: <strong style={{ color: '#f59e0b' }}>{compareResult.summary?.cache_reused || 0}</strong></span>
                <span>📡 broadcast: <strong style={{ color: '#f59e0b' }}>{compareResult.summary?.broadcast_join || 0}</strong></span>
                <span>🗜️ coalesce: <strong style={{ color: '#f59e0b' }}>{compareResult.summary?.coalesce_write || 0}</strong></span>
              </div>
              {(compareResult.changes || []).slice(0, 8).map((c, i) => (
                <div key={i} style={{ fontSize: 14, color: '#f59e0b', lineHeight: 1.5 }}>• {c.detail}</div>
              ))}

              {/* Benchmark simulando nube: 2 workers + datos amplificados */}
              <div style={{ borderTop: `1px solid ${t.border}`, paddingTop: 12, marginTop: 4 }}>
                <div style={{ fontSize: 13, color: t.muted, marginBottom: 8 }}>
                  🖥️ Benchmark simulando nube: <strong style={{ color: t.text }}>{compareResult.sim_workers ?? 2} workers</strong>
                  {typeof compareResult.sim_rows === 'number' && (
                    <> · <strong style={{ color: t.text }}>{compareResult.sim_rows.toLocaleString()} filas</strong></>
                  )}
                  {compareResult.sim_amplify > 1 && (
                    <span style={{ color: t.dim }}> (datos amplificados ×{compareResult.sim_amplify})</span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: 150, background: t.card, borderRadius: 8, padding: 12, border: `1px solid ${t.border}` }}>
                    <div style={{ fontSize: 11, color: t.dim, textTransform: 'uppercase' }}>Original</div>
                    <div style={{ fontSize: 26, fontWeight: 800, color: t.text }}>{compareResult.original?.seconds}s</div>
                    <div style={{ fontSize: 11, color: compareResult.original?.ok ? '#22c55e' : '#ef4444' }}>
                      {compareResult.original?.ok ? '✅ corrió' : '❌ falló'}
                    </div>
                  </div>
                  <div style={{ flex: 1, minWidth: 150, background: t.card, borderRadius: 8, padding: 12, border: `1px solid #f59e0b` }}>
                    <div style={{ fontSize: 11, color: t.dim, textTransform: 'uppercase' }}>Optimizado</div>
                    <div style={{ fontSize: 26, fontWeight: 800, color: '#f59e0b' }}>{compareResult.optimized?.seconds}s</div>
                    <div style={{ fontSize: 11, color: compareResult.optimized?.ok ? '#22c55e' : '#ef4444' }}>
                      {compareResult.optimized?.ok ? '✅ corrió' : '❌ falló'}
                    </div>
                  </div>
                  <div style={{ flex: 1, minWidth: 150, background: t.card, borderRadius: 8, padding: 12,
                    border: `1px solid ${(compareResult.faster_pct ?? 0) >= 0 ? '#22c55e' : '#ef4444'}` }}>
                    <div style={{ fontSize: 11, color: t.dim, textTransform: 'uppercase' }}>
                      {(compareResult.faster_pct ?? 0) >= 0 ? 'Mejora' : 'Resultado'}
                    </div>
                    <div style={{ fontSize: 26, fontWeight: 800, color: (compareResult.faster_pct ?? 0) >= 0 ? '#22c55e' : '#ef4444' }}>
                      {Math.abs(compareResult.faster_pct ?? 0)}%
                    </div>
                    <div style={{ fontSize: 11, color: t.dim }}>
                      {compareResult.speedup ? `${compareResult.speedup}× ` : ''}
                      {(compareResult.faster_pct ?? 0) >= 0 ? 'más rápido' : 'más lento'}
                    </div>
                  </div>
                </div>
              </div>
              <div style={{ fontSize: 12, color: '#94a3b8', fontStyle: 'italic' }}>
                El benchmark corre con 2 workers y datos amplificados para aproximar un entorno de nube.
                En AWS con datos reales (millones de filas) y más ejecutores, la mejora es aún mayor.
              </div>

              {(!compareResult.original?.ok || !compareResult.optimized?.ok) && (
                <div style={{ fontSize: 11, color: '#ef4444', fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap', maxHeight: 160, overflow: 'auto' }}>
                  {compareResult.original?.stderr_tail || compareResult.optimized?.stderr_tail}
                </div>
              )}
            </div>
          )}
          {compareResult?.error && (
            <div style={{ fontSize: 12, color: '#ef4444' }}>❌ {compareResult.error}</div>
          )}

          {/* Avisos de precondición */}
          {!hasCode && (
            <span style={{ fontSize: 12, color: '#f59e0b' }}>
              ⚠️ No hay código compilado. Compila un grafo en el Compiler primero.
            </span>
          )}
          {hasCode && !isPySpark && (
            <span style={{ fontSize: 12, color: '#f59e0b' }}>
              ⚠️ El target actual es "{compiledTarget}". La ejecución local solo soporta PySpark —
              cambia el target a "Spark" en el Compiler y recompila.
            </span>
          )}

          {/* Estado final */}
          {runResult && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              borderRadius: 8, padding: '10px 12px',
              background: runResult.ok ? '#22c55e10' : '#ef444410',
              border: `1px solid ${runResult.ok ? '#22c55e40' : '#ef444440'}`,
            }}>
              <span style={{ fontSize: 18 }}>{runResult.ok ? '✅' : '❌'}</span>
              <span style={{ fontSize: 14, fontWeight: 700, color: runResult.ok ? '#22c55e' : '#ef4444' }}>
                {runResult.summary}
              </span>
              <div style={{ flex: 1 }} />
              {(runResult.reads?.length > 0 || runResult.writes?.length > 0) && (
                <span style={{ fontSize: 12, color: t.muted }}>
                  {runResult.reads?.length || 0} lectura(s) · {runResult.writes?.length || 0} escritura(s)
                </span>
              )}
            </div>
          )}

          {/* Consola en vivo */}
          {(running || consoleLines.length > 0) && (
            <LiveConsole lines={consoleLines} running={running} theme={t} />
          )}

          {/* Reporte: estadisticas entrada vs salida + flujo de transformacion */}
          {runReport && (
            <div style={{
              display: 'flex', flexDirection: 'column', gap: 12,
              background: '#0a0e17', border: `1px solid ${t.border || '#334155'}`,
              borderRadius: 8, padding: 14,
            }}>
              <span style={label}>📊 Reporte del grafo</span>

              {/* Descripcion en lenguaje natural del grafo (colapsable) */}
              {(runReport.description || graphDescription) && (
                <details open style={{
                  background: '#11162080', border: `1px solid ${t.border || '#334155'}`,
                  borderRadius: 8, padding: '10px 14px',
                }}>
                  <summary style={{
                    cursor: 'pointer', fontSize: 14, fontWeight: 600,
                    color: t.accent || '#818cf8', userSelect: 'none', outline: 'none',
                  }}>📝 Descripción del grafo (clic para ocultar)</summary>
                  <div style={{
                    fontSize: 16, color: t.text || '#e2e8f0', lineHeight: 1.6, marginTop: 10,
                  }}>
                    {runReport.description || graphDescription}
                  </div>
                </details>
              )}

              {/* Costo estimado en AWS segun la complejidad del grafo */}
              {(() => {
                const flow = runReport.flow || []
                const nodes = flow.length
                const joins = flow.filter(s => ['JOIN', 'LOOKUP'].includes(String(s.type || '').toUpperCase())).length
                const edges = nodes > 0 ? nodes - 1 : 0
                return <CostEstimateCard theme={t} nodes={nodes} joins={joins} edges={edges} />
              })()}

              {/* Fidelidad de los datos */}
              {runReport.fidelity && typeof runReport.fidelity.score === 'number' && (() => {
                const sc = runReport.fidelity.score
                const col = sc >= 90 ? '#22c55e' : sc >= 70 ? '#f59e0b' : '#ef4444'
                return (
                  <div style={{
                    display: 'flex', flexDirection: 'column', gap: 8,
                    background: `${col}10`, border: `1px solid ${col}35`, borderRadius: 8, padding: 12,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
                      <span style={{ fontSize: 12, color: t.dim, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                        Fidelidad de los datos
                      </span>
                      <span style={{ fontSize: 26, fontWeight: 800, color: col }}>{sc}%</span>
                    </div>
                    {/* Barra */}
                    <div style={{ height: 8, borderRadius: 4, background: '#1e293b', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.max(0, Math.min(100, sc))}%`, height: '100%', background: col }} />
                    </div>
                    {/* Desglose de factores */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 3, marginTop: 2 }}>
                      {(runReport.fidelity.factors || []).map((f, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', gap: 8, fontSize: 11, color: t.muted }}>
                          <span>
                            {f.label} <span style={{ color: t.dim }}>(peso {Math.round((f.weight || 0) * 100)}%)</span>
                            {f.detail ? <span style={{ color: t.dim }}> — {f.detail}</span> : null}
                          </span>
                          <strong style={{ color: f.score >= 90 ? '#22c55e' : f.score >= 70 ? '#f59e0b' : '#ef4444' }}>{f.score}%</strong>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })()}

              {/* Comparacion entrada vs salida */}
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {[
                  { lbl: 'Filas entrada', val: runReport.totals?.input_rows ?? 0, col: '#38bdf8' },
                  { lbl: 'Filas salida', val: runReport.totals?.output_rows ?? 0, col: '#22c55e' },
                  {
                    lbl: 'Diferencia',
                    val: `${(runReport.totals?.delta_rows ?? 0) >= 0 ? '+' : ''}${runReport.totals?.delta_rows ?? 0}`,
                    col: (runReport.totals?.delta_rows ?? 0) === 0 ? '#94a3b8' : ((runReport.totals?.delta_rows ?? 0) > 0 ? '#22c55e' : '#f59e0b'),
                  },
                ].map((c, i) => (
                  <div key={i} style={{
                    flex: '1 1 120px', minWidth: 110, borderRadius: 8, padding: '10px 12px',
                    background: `${c.col}12`, border: `1px solid ${c.col}30`,
                  }}>
                    <div style={{ fontSize: 10, color: t.dim, textTransform: 'uppercase', letterSpacing: 0.5 }}>{c.lbl}</div>
                    <div style={{ fontSize: 22, fontWeight: 800, color: c.col }}>{c.val}</div>
                  </div>
                ))}
              </div>

              {/* Detalle por fuente / tabla */}
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                <div style={{ flex: '1 1 240px' }}>
                  <div style={{ fontSize: 11, color: t.dim, marginBottom: 4 }}>Entradas</div>
                  {(runReport.inputs || []).length === 0 && (
                    <div style={{ fontSize: 12, color: t.muted }}>(ninguna)</div>
                  )}
                  {(runReport.inputs || []).map((r, i) => (
                    <div key={i} style={{ fontSize: 12, color: t.muted, fontFamily: 'monospace' }}>
                      {r.node || r.var}: <strong style={{ color: '#38bdf8' }}>{r.rows}</strong> filas
                    </div>
                  ))}
                </div>
                <div style={{ flex: '1 1 240px' }}>
                  <div style={{ fontSize: 11, color: t.dim, marginBottom: 4 }}>Salidas (tablas)</div>
                  {(runReport.outputs || []).length === 0 && (
                    <div style={{ fontSize: 12, color: t.muted }}>(ninguna)</div>
                  )}
                  {(runReport.outputs || []).map((o, i) => (
                    <div key={i} style={{ fontSize: 12, color: t.muted, fontFamily: 'monospace' }}>
                      {o.table}: <strong style={{ color: '#22c55e' }}>{o.rows}</strong> filas
                    </div>
                  ))}
                </div>
              </div>

              {/* Flujo de transformacion */}
              {(runReport.flow || []).length > 0 && (
                <div>
                  <div style={{ fontSize: 11, color: t.dim, marginBottom: 6 }}>Flujo de transformación</div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                    {runReport.flow.map((s, i) => {
                      const colByType = {
                        SOURCE: '#38bdf8', SINK: '#22c55e', JOIN: '#a855f7',
                        TRANSFORM: '#f59e0b', FILTER: '#ef4444', DEDUP: '#ef4444',
                        LOOKUP: '#06b6d4', NORMALIZE: '#eab308',
                      }
                      const col = colByType[s.type] || '#94a3b8'
                      return (
                        <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                          <span style={{
                            padding: '4px 8px', borderRadius: 6, fontSize: 11, fontWeight: 700,
                            background: `${col}18`, border: `1px solid ${col}40`, color: col,
                            fontFamily: 'monospace',
                          }} title={s.type}>{s.name}</span>
                          {i < runReport.flow.length - 1 && (
                            <span style={{ color: t.dim, fontSize: 12 }}>→</span>
                          )}
                        </span>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Descargas del resultado de la prueba LOCAL (CSV en disco) */}
          {localDownloads.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <span style={label}>⬇️ Descargar resultado (local)</span>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {localDownloads.map((d, i) => (
                  <a key={i} href={`${DOWNLOAD_URL}?f=${encodeURIComponent(d.name)}`} download
                    style={{
                      padding: '8px 14px', borderRadius: 8, fontSize: 12, fontWeight: 700,
                      background: '#22c55e', color: '#000', textDecoration: 'none',
                      display: 'inline-flex', alignItems: 'center', gap: 6,
                    }}>⬇️ {d.name}</a>
                ))}
              </div>
              <span style={{ fontSize: 10, color: t.dim }}>
                CSV generados por la prueba local (se sobrescriben en cada corrida).
              </span>
            </div>
          )}

          {/* --- ENVIAR A AWS --- */}
          <div style={{ height: 1, background: t.border || '#334155', margin: '4px 0' }} />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <span style={label}>☁️ Enviar a AWS (Glue)</span>
              <span style={{ fontSize: 11, color: t.dim }}>
                Empaqueta el código con los datos sintéticos y lo ejecuta en AWS Glue. El resultado se escribe a S3.
              </span>
            </div>
            <button
              onClick={sendToAWS}
              disabled={awsSending || !hasCode || !isPySpark}
              style={{
                padding: '10px 20px', borderRadius: 8,
                cursor: (awsSending || !hasCode || !isPySpark) ? 'not-allowed' : 'pointer',
                background: (!hasCode || !isPySpark) ? (t.border || '#334155') : '#f59e0b',
                color: '#000', border: 'none', fontSize: 14, fontWeight: 700,
                opacity: awsSending ? 0.6 : 1,
              }}
            >{awsSending ? '☁️ Enviando/ejecutando...' : '☁️ Enviar a AWS'}</button>
          </div>

          {/* Config AWS minima (editable) */}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <span style={{ fontSize: 10, color: t.dim }}>Bucket S3</span>
              <input value={awsBucket} onChange={e => setAwsBucket(e.target.value)}
                style={{ ...inputStyle, width: 240, fontSize: 11, fontFamily: 'monospace' }} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <span style={{ fontSize: 10, color: t.dim }}>Job Name</span>
              <input value={awsJobName} onChange={e => setAwsJobName(e.target.value)}
                style={{ ...inputStyle, width: 260, fontSize: 11, fontFamily: 'monospace' }} />
            </div>
          </div>

          {/* Estado AWS */}
          {awsStatus && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8, borderRadius: 8, padding: '8px 12px',
              background: awsStatus === 'ok' ? '#22c55e10' : awsStatus === 'error' ? '#ef444410' : '#f59e0b10',
              border: `1px solid ${awsStatus === 'ok' ? '#22c55e40' : awsStatus === 'error' ? '#ef444440' : '#f59e0b40'}`,
            }}>
              <span style={{ fontSize: 16 }}>{awsStatus === 'ok' ? '✅' : awsStatus === 'error' ? '❌' : '☁️'}</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: awsStatus === 'ok' ? '#22c55e' : awsStatus === 'error' ? '#ef4444' : '#f59e0b' }}>
                {awsStatus === 'ok' ? 'Job completado en AWS' : awsStatus === 'error' ? 'Falló en AWS' : 'Ejecutando en AWS...'}
              </span>
            </div>
          )}

          {/* Descargas del output (presigned URLs de S3) */}
          {awsDownloads.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <span style={label}>⬇️ Descargar resultado (S3)</span>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {awsDownloads.map((d, i) => (
                  <a key={i} href={d.url} target="_blank" rel="noopener noreferrer" download
                    style={{
                      padding: '8px 14px', borderRadius: 8, fontSize: 12, fontWeight: 700,
                      background: '#22c55e', color: '#000', textDecoration: 'none',
                      display: 'inline-flex', alignItems: 'center', gap: 6,
                    }}>⬇️ {d.name}</a>
                ))}
              </div>
              <span style={{ fontSize: 10, color: t.dim }}>Enlaces de descarga directa desde S3 (válidos 7 días).</span>
            </div>
          )}

          {/* Logs AWS */}
          {awsLogs.length > 0 && (
            <div ref={null} style={{
              background: '#0a0e17', border: `1px solid ${t.border || '#334155'}`,
              borderRadius: 8, padding: 12, maxHeight: 260, overflow: 'auto',
              fontFamily: 'monospace', fontSize: 11, lineHeight: 1.6,
            }}>
              {awsLogs.map((l, i) => (
                <div key={i} style={{
                  color: /ERROR|FALLO/.test(l) ? '#fca5a5'
                       : /EXITOSO|SUCCEEDED/.test(l) ? '#4ade80'
                       : /Status:/.test(l) ? '#fbbf24'
                       : (t.muted || '#cbd5e1'),
                  whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                }}>{l}</div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Consola tipo terminal que auto-scrollea y colorea las lineas por tipo
function LiveConsole({ lines, running, theme }) {
  const t = theme || {}
  const ref = useRef(null)
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [lines])

  const colorFor = (kind) => ({
    error: '#fca5a5',
    source: '#4ade80',
    join: '#fbbf24',
    sink: '#f87171',
    transform: '#818cf8',
    ok: '#22c55e',
    info: '#94a3b8',
    plain: t.muted || '#cbd5e1',
  }[kind] || (t.muted || '#cbd5e1'))

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 11, color: t.dim || '#64748b', textTransform: 'uppercase', letterSpacing: 1 }}>
          🖥️ Consola en vivo
        </span>
        {running && (
          <span style={{ fontSize: 11, color: '#818cf8' }}>
            <span style={{ display: 'inline-block', animation: 'bnxblink 1s infinite' }}>●</span> ejecutando...
          </span>
        )}
        <style>{`@keyframes bnxblink { 0%,100%{opacity:1} 50%{opacity:0.2} }`}</style>
      </div>
      <div ref={ref} style={{
        background: '#0a0e17', border: `1px solid ${t.border || '#334155'}`,
        borderRadius: 8, padding: 12, maxHeight: 360, overflow: 'auto',
        fontFamily: 'monospace', fontSize: 12, lineHeight: 1.5,
      }}>
        {lines.map((l, i) => (
          <div key={i} style={{ color: colorFor(l.kind), whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
            {l.text}
          </div>
        ))}
        {lines.length === 0 && (
          <span style={{ color: t.dim || '#64748b' }}>Esperando salida...</span>
        )}
      </div>
    </div>
  )
}
