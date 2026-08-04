import { useState, useEffect, useRef } from 'react'
import { COMPILE_URL } from '../config'

const LIB_URL = COMPILE_URL.replace('/compile', '/library')

export default function GrafosPage({ theme, onLoadToCompiler }) {
  const t = theme || {}
  const [graphs, setGraphs] = useState([])
  const [loading, setLoading] = useState(false)
  const [showSave, setShowSave] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [saveMp, setSaveMp] = useState('')
  const [saveXfr, setSaveXfr] = useState('')
  const [filter, setFilter] = useState('')
  const [selected, setSelected] = useState(null)
  const importRef = useRef(null)
  const uploadRef = useRef(null)

  useEffect(() => { fetchGraphs() }, [])

  const fetchGraphs = async () => {
    setLoading(true)
    try {
      const form = new FormData()
      form.append('action', 'list')
      const res = await fetch(LIB_URL, { method: 'POST', body: form })
      const data = await res.json()
      setGraphs(data.graphs || [])
    } catch (e) { console.error('Library error:', e) }
    finally { setLoading(false) }
  }

  const saveGraph = async () => {
    if (!saveName.trim() || !saveMp.trim()) return
    const form = new FormData()
    form.append('action', 'save')
    form.append('name', saveName.trim())
    form.append('mp', saveMp)
    if (saveXfr.trim()) form.append('xfr', saveXfr)
    const res = await fetch(LIB_URL, { method: 'POST', body: form })
    const data = await res.json()
    if (data.saved) {
      setGraphs(prev => [data.saved, ...prev])
      setSaveName(''); setSaveMp(''); setSaveXfr(''); setShowSave(false)
    }
  }

  const deleteGraph = async (id) => {
    const form = new FormData()
    form.append('action', 'delete')
    form.append('id', id)
    await fetch(LIB_URL, { method: 'POST', body: form })
    setGraphs(prev => prev.filter(g => g.id !== id))
    if (selected?.id === id) setSelected(null)
  }

  const uploadFiles = async (fileList) => {
    for (const file of fileList) {
      const reader = new FileReader()
      reader.onload = async (e) => {
        const content = e.target.result
        const name = file.name.replace(/\.(mp|xfr|dml)$/, '')
        const form = new FormData()
        form.append('action', 'save')
        form.append('name', name)
        form.append('mp', content)
        await fetch(LIB_URL, { method: 'POST', body: form })
        fetchGraphs()
      }
      reader.readAsText(file)
    }
  }

  const exportGraph = (g) => {
    const blob = new Blob([g.mp], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `${g.name.replace(/\s/g, '_')}.mp`; a.click()
    URL.revokeObjectURL(url)
    if (g.xfr) {
      setTimeout(() => {
        const b = new Blob([g.xfr], { type: 'text/plain' })
        const u = URL.createObjectURL(b)
        const a2 = document.createElement('a')
        a2.href = u; a2.download = `${g.name.replace(/\s/g, '_')}.xfr`; a2.click()
        URL.revokeObjectURL(u)
      }, 200)
    }
  }

  const exportAll = () => {
    const blob = new Blob([JSON.stringify(graphs, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'bnx_graph_library.json'; a.click()
    URL.revokeObjectURL(url)
  }

  const importLib = async (file) => {
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const imported = JSON.parse(e.target.result)
        if (Array.isArray(imported)) {
          for (const g of imported) {
            const form = new FormData()
            form.append('action', 'save')
            form.append('name', g.name || 'imported')
            form.append('mp', g.mp || '')
            if (g.xfr) form.append('xfr', g.xfr)
            await fetch(LIB_URL, { method: 'POST', body: form })
          }
          fetchGraphs()
        }
      } catch {}
    }
    reader.readAsText(file)
  }

  const filtered = filter
    ? graphs.filter(g => g.name.toLowerCase().includes(filter.toLowerCase()))
    : graphs

  const card = { background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`, borderRadius: 10, padding: 20 }

  return (
    <div style={{ padding: 32, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: t.text || '#e2e8f0', margin: 0 }}>
            Biblioteca de Grafos
          </h2>
          <p style={{ fontSize: 14, color: t.dim || '#64748b', marginTop: 4 }}>
            {graphs.length} grafos guardados — visibles desde local y Amplify
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => setShowSave(!showSave)} style={{
            padding: '10px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
            background: '#22c55e15', border: '1px solid #22c55e40', color: '#22c55e', fontWeight: 600,
          }}>+ Nuevo grafo</button>
          <button onClick={() => uploadRef.current.click()} style={{
            padding: '10px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
            background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`, color: t.muted || '#94a3b8',
          }}>📂 Subir archivos</button>
          <input ref={uploadRef} type="file" accept=".mp,.xfr,.dml" multiple hidden
            onChange={(e) => { if (e.target.files.length) uploadFiles(Array.from(e.target.files)); e.target.value = '' }}
          />
          <button onClick={exportAll} disabled={!graphs.length} style={{
            padding: '10px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
            background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`, color: t.muted || '#94a3b8',
          }}>📥 Export todo</button>
          <button onClick={() => importRef.current.click()} style={{
            padding: '10px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
            background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`, color: t.muted || '#94a3b8',
          }}>📤 Import JSON</button>
          <input ref={importRef} type="file" accept=".json" hidden
            onChange={(e) => { if (e.target.files[0]) importLib(e.target.files[0]); e.target.value = '' }}
          />
          <button onClick={fetchGraphs} style={{
            padding: '10px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
            background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`, color: t.muted || '#94a3b8',
          }}>{loading ? '...' : '↻ Refresh'}</button>
        </div>
      </div>

      {/* Save form */}
      {showSave && (
        <div style={{ ...card, borderLeft: '3px solid #22c55e' }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: '#22c55e', margin: '0 0 12px' }}>Guardar nuevo grafo</h3>
          <input value={saveName} onChange={e => setSaveName(e.target.value)} placeholder="Nombre del grafo..."
            style={{ width: '100%', padding: '8px 12px', borderRadius: 8, fontSize: 13, marginBottom: 10, background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`, color: t.text || '#e2e8f0', outline: 'none' }}
          />
          <div style={{ display: 'flex', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: '#22c55e', marginBottom: 4 }}>.mp (requerido)</div>
              <textarea value={saveMp} onChange={e => setSaveMp(e.target.value)} placeholder="NODE Read : SOURCE&#10;NODE Transform : TRANSFORM&#10;..."
                style={{ width: '100%', minHeight: 150, padding: 10, borderRadius: 8, fontSize: 12, background: t.codeBg || '#081220', border: '1px solid #22c55e30', color: '#22c55e', fontFamily: 'monospace', resize: 'vertical', outline: 'none' }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: '#6366f1', marginBottom: 4 }}>.xfr (opcional)</div>
              <textarea value={saveXfr} onChange={e => setSaveXfr(e.target.value)} placeholder="Read:&#10;  source_type s3&#10;  path s3://..."
                style={{ width: '100%', minHeight: 150, padding: 10, borderRadius: 8, fontSize: 12, background: t.codeBg || '#081220', border: '1px solid #6366f130', color: '#6366f1', fontFamily: 'monospace', resize: 'vertical', outline: 'none' }}
              />
            </div>
          </div>
          <button onClick={saveGraph} disabled={!saveName.trim() || !saveMp.trim()} style={{
            marginTop: 12, padding: '10px 20px', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer',
            background: saveName.trim() && saveMp.trim() ? '#22c55e' : '#334155',
            color: saveName.trim() && saveMp.trim() ? '#000' : '#64748b', border: 'none',
          }}>Guardar</button>
        </div>
      )}

      {/* Search */}
      {graphs.length > 0 && (
        <input value={filter} onChange={e => setFilter(e.target.value)} placeholder="Buscar grafos por nombre..."
          style={{ padding: '10px 14px', borderRadius: 8, fontSize: 13, background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`, color: t.text || '#e2e8f0', outline: 'none', width: 300 }}
        />
      )}

      {/* Grid */}
      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        {/* List */}
        <div style={{ flex: '1 1 400px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          {loading && <div style={{ color: t.dim || '#64748b', fontSize: 13 }}>Cargando...</div>}
          {!loading && filtered.length === 0 && (
            <div style={{ ...card, textAlign: 'center', color: t.dim || '#64748b', fontSize: 13 }}>
              Sin grafos. Usa "+ Nuevo grafo" o "Subir archivos" para empezar.
            </div>
          )}
          {filtered.map(g => (
            <div key={g.id} onClick={() => setSelected(g)} style={{
              ...card, padding: 14, cursor: 'pointer',
              borderLeft: `3px solid ${selected?.id === g.id ? '#22c55e' : 'transparent'}`,
              background: selected?.id === g.id ? (t.accent || '#1a73e8') + '10' : (t.card || '#1e2433'),
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: t.text || '#e2e8f0' }}>{g.name}</div>
                  <div style={{ fontSize: 11, color: t.dim || '#64748b', marginTop: 2 }}>
                    {g.nodes || '?'} nodos · {g.savedAt ? new Date(g.savedAt).toLocaleDateString() : ''}
                    {g.xfr ? ' · +xfr' : ''}
                    {g.source === 'file' ? ' · 📄 archivo' : ' · ☁️ S3'}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 4 }}>
                  <button onClick={(e) => { e.stopPropagation(); onLoadToCompiler && onLoadToCompiler(g) }} style={{
                    padding: '5px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                    background: '#22c55e15', border: '1px solid #22c55e30', color: '#22c55e', fontWeight: 600,
                  }}>Compilar</button>
                  <button onClick={(e) => { e.stopPropagation(); exportGraph(g) }} style={{
                    padding: '5px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                    background: 'transparent', border: `1px solid ${t.border || '#334155'}`, color: t.dim || '#64748b',
                  }}>↓</button>
                  <button onClick={(e) => { e.stopPropagation(); deleteGraph(g.id) }} style={{
                    padding: '5px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                    background: '#ef444410', border: '1px solid #ef444430', color: '#ef4444',
                  }}>✕</button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Preview */}
        {selected && (
          <div style={{ flex: '1 1 350px', display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={card}>
              <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', margin: '0 0 8px' }}>{selected.name}</h3>
              <div style={{ fontSize: 11, color: t.dim || '#64748b', marginBottom: 10 }}>
                {selected.nodes} nodos · ID: {selected.id}
              </div>
              <div style={{ fontSize: 11, color: '#22c55e', marginBottom: 4 }}>.mp</div>
              <pre style={{
                padding: 10, borderRadius: 6, fontSize: 11, maxHeight: 250, overflowY: 'auto',
                background: t.codeBg || '#081220', color: '#22c55e', fontFamily: 'monospace',
                border: '1px solid #22c55e20', margin: 0, whiteSpace: 'pre-wrap',
              }}>{selected.mp}</pre>
              {selected.xfr && (
                <>
                  <div style={{ fontSize: 11, color: '#6366f1', marginBottom: 4, marginTop: 10 }}>.xfr</div>
                  <pre style={{
                    padding: 10, borderRadius: 6, fontSize: 11, maxHeight: 150, overflowY: 'auto',
                    background: t.codeBg || '#081220', color: '#6366f1', fontFamily: 'monospace',
                    border: '1px solid #6366f120', margin: 0, whiteSpace: 'pre-wrap',
                  }}>{selected.xfr}</pre>
                </>
              )}
              <button onClick={() => onLoadToCompiler && onLoadToCompiler(selected)} style={{
                marginTop: 12, width: '100%', padding: '10px', borderRadius: 8, fontSize: 13, fontWeight: 600,
                cursor: 'pointer', background: '#22c55e', color: '#000', border: 'none',
              }}>🚀 Compilar este grafo</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
