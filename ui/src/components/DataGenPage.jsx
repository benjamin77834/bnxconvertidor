import { useState, useRef, useEffect } from 'react'
import { COMPILE_URL } from '../config'

// El endpoint /datagen vive en el mismo origen que /compile
const DATAGEN_URL = COMPILE_URL.replace(/\/compile$/, '/datagen')
const RUNTEST_URL = COMPILE_URL.replace(/\/compile$/, '/runtest')
const RUNTEST_STREAM_URL = COMPILE_URL.replace(/\/compile$/, '/runtest/stream')

const TYPES = ['string', 'integer', 'decimal', 'date', 'datetime', 'boolean']
const PII_CATEGORIES = ['', 'name', 'email', 'phone', 'card', 'account', 'ssn', 'address', 'dob', 'id']

// Etiqueta visual para entrada/salida
const IO_META = {
  input: { label: '⬇️ Entrada', color: '#22c55e' },
  output: { label: '⬆️ Salida', color: '#f59e0b' },
}
const ioMeta = (io) => IO_META[io] || IO_META.output

export default function DataGenPage({ theme, graphMp = '', graphXfr = '', compiledCode = '', compiledTarget = '' }) {
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
  const [runResult, setRunResult] = useState(null) // {ok, summary, reads, writes}
  const [consoleLines, setConsoleLines] = useState([]) // lineas en vivo

  const isPySpark = compiledTarget === 'spark'
  const hasCode = Boolean((compiledCode || '').trim())

  const runTest = async () => {
    setRunning(true)
    setRunResult(null)
    setConsoleLines([{ text: '[*] Iniciando ejecución de prueba...', kind: 'info' }])
    try {
      const inputs = (result?.datasets || []).filter(d => d.io === 'input')
      const datasets = inputs.length ? inputs : (result?.datasets || [])
      const res = await fetch(RUNTEST_STREAM_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: compiledCode, datasets, timeout: 180 }),
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
              <span style={label}>▶️ Ejecutar prueba local (PySpark)</span>
              <span style={{ fontSize: 11, color: t.dim }}>
                Corre el código del Compiler con estos datos de entrada y comprueba si funciona.
              </span>
            </div>
            <button
              onClick={runTest}
              disabled={running || !hasCode || !isPySpark}
              style={{
                padding: '10px 20px', borderRadius: 8,
                cursor: (running || !hasCode || !isPySpark) ? 'not-allowed' : 'pointer',
                background: (!hasCode || !isPySpark) ? (t.border || '#334155') : '#6366f1',
                color: '#fff', border: 'none', fontSize: 14, fontWeight: 700,
                opacity: running ? 0.6 : 1,
              }}
            >{running ? '⏳ Ejecutando...' : '▶️ Ejecutar prueba'}</button>
          </div>

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
