import { useState } from 'react'
import { COMPILE_URL } from '../config'

// El endpoint /datagen vive en el mismo origen que /compile
const DATAGEN_URL = COMPILE_URL.replace(/\/compile$/, '/datagen')

const TYPES = ['string', 'integer', 'decimal', 'date', 'datetime', 'boolean']
const PII_CATEGORIES = ['', 'name', 'email', 'phone', 'card', 'account', 'ssn', 'address', 'dob', 'id']

export default function DataGenPage({ theme }) {
  const t = theme || {}
  const [mode, setMode] = useState('graph') // 'graph' | 'manual'

  // --- Modo grafo ---
  const [mp, setMp] = useState('')
  const [xfr, setXfr] = useState('')
  const [dml, setDml] = useState('')

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

  const ds = result?.datasets?.[activeDataset]

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
          <span style={label}>Grafo (.mp requerido, .xfr y .dml opcionales)</span>
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

      {/* --- RESULTADO --- */}
      {result?.datasets?.length > 0 && (
        <div style={{ ...card, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            <span style={label}>
              Resultado · {result.mode === 'graph' ? `${result.datasets.length} nodo(s)` : 'manual'}
            </span>
            {ds && (
              <button onClick={() => downloadDataset(ds)} style={btn(true, '#22c55e')}>
                📥 Descargar {ds.node} ({ds.format.toUpperCase()})
              </button>
            )}
          </div>

          {/* Selector de dataset (cuando hay varios nodos) */}
          {result.datasets.length > 1 && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {result.datasets.map((d, i) => (
                <button key={i} style={btn(activeDataset === i)} onClick={() => setActiveDataset(i)}>
                  {d.node} ({d.columns.length})
                </button>
              ))}
            </div>
          )}

          {/* Botón para traer este esquema al editor manual */}
          {ds && (
            <button onClick={() => importSchemaToManual(ds.columns, ds.node)} style={{ ...btn(false), alignSelf: 'flex-start', fontSize: 11 }}>
              ✏️ Editar este esquema manualmente
            </button>
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
    </div>
  )
}
