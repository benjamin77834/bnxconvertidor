import { useState, useEffect, useRef } from 'react'
import { COMPILE_URL } from '../config'

const LIB_URL = COMPILE_URL.replace('/compile', '/library')

export default function GraphLibrary({ theme, onLoad }) {
  const t = theme || {}
  const [graphs, setGraphs] = useState([])
  const [loading, setLoading] = useState(false)
  const [showSave, setShowSave] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [saveMp, setSaveMp] = useState('')
  const [saveXfr, setSaveXfr] = useState('')
  const [filter, setFilter] = useState('')
  const importRef = useRef(null)

  // Cargar lista al montar
  useEffect(() => { fetchGraphs() }, [])

  const fetchGraphs = async () => {
    setLoading(true)
    try {
      const form = new FormData()
      form.append('action', 'list')
      const res = await fetch(LIB_URL, { method: 'POST', body: form })
      const data = await res.json()
      setGraphs(data.graphs || [])
    } catch (e) {
      console.error('Library fetch error:', e)
    } finally { setLoading(false) }
  }

  // Guardar grafo en S3
  const saveGraph = async () => {
    if (!saveName.trim() || !saveMp.trim()) return
    try {
      const form = new FormData()
      form.append('action', 'save')
      form.append('name', saveName.trim())
      form.append('mp', saveMp)
      if (saveXfr.trim()) form.append('xfr', saveXfr)
      const res = await fetch(LIB_URL, { method: 'POST', body: form })
      const data = await res.json()
      if (data.saved) {
        setGraphs(prev => [data.saved, ...prev])
        setSaveName('')
        setSaveMp('')
        setSaveXfr('')
        setShowSave(false)
      }
    } catch (e) { console.error('Save error:', e) }
  }

  // Borrar grafo de S3
  const deleteGraph = async (id) => {
    try {
      const form = new FormData()
      form.append('action', 'delete')
      form.append('id', id)
      await fetch(LIB_URL, { method: 'POST', body: form })
      setGraphs(prev => prev.filter(g => g.id !== id))
    } catch (e) { console.error('Delete error:', e) }
  }

  // Exportar biblioteca como JSON
  const exportAll = () => {
    const blob = new Blob([JSON.stringify(graphs, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'bnx_graph_library.json'; a.click()
    URL.revokeObjectURL(url)
  }

  // Importar biblioteca desde JSON (sube cada grafo a S3)
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
      } catch { /* ignore */ }
    }
    reader.readAsText(file)
  }

  // Exportar un grafo individual
  const exportGraph = (graph) => {
    const blob = new Blob([graph.mp], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `${graph.name.replace(/\s/g, '_')}.mp`; a.click()
    URL.revokeObjectURL(url)
    if (graph.xfr) {
      setTimeout(() => {
        const b = new Blob([graph.xfr], { type: 'text/plain' })
        const u = URL.createObjectURL(b)
        const a2 = document.createElement('a')
        a2.href = u; a2.download = `${graph.name.replace(/\s/g, '_')}.xfr`; a2.click()
        URL.revokeObjectURL(u)
      }, 200)
    }
  }

  const filtered = filter
    ? graphs.filter(g => g.name.toLowerCase().includes(filter.toLowerCase()))
    : graphs

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 14, color: t.muted || '#94a3b8', textTransform: 'uppercase', letterSpacing: 1 }}>
          Biblioteca ({graphs.length})
        </span>
        <div style={{ display: 'flex', gap: 4 }}>
          <button onClick={() => setShowSave(!showSave)} style={{
            padding: '4px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: showSave ? '#22c55e20' : 'transparent',
            border: `1px solid ${showSave ? '#22c55e' : (t.border || '#334155')}`,
            color: showSave ? '#22c55e' : (t.dim || '#64748b'),
          }}>+ Guardar</button>
          <button onClick={fetchGraphs} style={{
            padding: '4px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: 'transparent', border: `1px solid ${t.border || '#334155'}`,
            color: t.dim || '#64748b',
          }}>{loading ? '...' : '↻'}</button>
          <button onClick={exportAll} disabled={!graphs.length} style={{
            padding: '4px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: 'transparent', border: `1px solid ${t.border || '#334155'}`,
            color: t.dim || '#64748b',
          }}>↓</button>
          <button onClick={() => importRef.current.click()} style={{
            padding: '4px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: 'transparent', border: `1px solid ${t.border || '#334155'}`,
            color: t.dim || '#64748b',
          }}>↑</button>
          <input ref={importRef} type="file" accept=".json" hidden
            onChange={(e) => { if (e.target.files[0]) importLib(e.target.files[0]); e.target.value = '' }}
          />
        </div>
      </div>

      {/* Save form */}
      {showSave && (
        <div style={{
          background: t.card || '#1e2433', border: `1px solid #22c55e40`,
          borderRadius: 8, padding: 12, borderLeft: '3px solid #22c55e',
        }}>
          <input value={saveName} onChange={e => setSaveName(e.target.value)}
            placeholder="Nombre del grafo..."
            style={{
              width: '100%', padding: '5px 8px', borderRadius: 6, fontSize: 12, marginBottom: 6,
              background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
              color: t.text || '#e2e8f0', outline: 'none',
            }}
          />
          <textarea value={saveMp} onChange={e => setSaveMp(e.target.value)}
            placeholder="Contenido .mp..."
            style={{
              width: '100%', minHeight: 60, padding: 6, borderRadius: 6, fontSize: 11,
              background: t.codeBg || '#081220', border: `1px solid #22c55e30`,
              color: '#22c55e', fontFamily: 'monospace', resize: 'vertical', outline: 'none',
              marginBottom: 4,
            }}
          />
          <textarea value={saveXfr} onChange={e => setSaveXfr(e.target.value)}
            placeholder=".xfr (opcional)..."
            style={{
              width: '100%', minHeight: 30, padding: 6, borderRadius: 6, fontSize: 11,
              background: t.codeBg || '#081220', border: `1px solid #6366f130`,
              color: '#6366f1', fontFamily: 'monospace', resize: 'vertical', outline: 'none',
              marginBottom: 6,
            }}
          />
          <button onClick={saveGraph} disabled={!saveName.trim() || !saveMp.trim()} style={{
            width: '100%', padding: '7px', borderRadius: 6, fontSize: 12, fontWeight: 600,
            cursor: saveName.trim() && saveMp.trim() ? 'pointer' : 'not-allowed',
            background: saveName.trim() && saveMp.trim() ? '#22c55e' : (t.border || '#334155'),
            color: saveName.trim() && saveMp.trim() ? '#000' : '#64748b', border: 'none',
          }}>Guardar en S3</button>
        </div>
      )}

      {/* Search */}
      {graphs.length > 3 && (
        <input value={filter} onChange={e => setFilter(e.target.value)}
          placeholder="Buscar..."
          style={{
            width: '100%', padding: '5px 8px', borderRadius: 6, fontSize: 11,
            background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
            color: t.text || '#e2e8f0', outline: 'none',
          }}
        />
      )}

      {/* List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 220, overflowY: 'auto' }}>
        {filtered.length === 0 && !loading && (
          <div style={{ fontSize: 11, color: t.dim || '#64748b', textAlign: 'center', padding: 10 }}>
            Sin grafos. Usa "+ Guardar" para agregar.
          </div>
        )}
        {loading && <div style={{ fontSize: 11, color: t.dim || '#64748b', textAlign: 'center' }}>Cargando...</div>}
        {filtered.map(g => (
          <div key={g.id} style={{
            display: 'flex', alignItems: 'center', gap: 6, padding: '6px 8px',
            borderRadius: 6, background: t.card || '#1e2433',
            border: `1px solid ${t.border || '#334155'}`,
          }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 500, color: t.text || '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {g.name}
              </div>
              <div style={{ fontSize: 9, color: t.dim || '#64748b' }}>
                {g.nodes || '?'} nodos · {g.savedAt ? new Date(g.savedAt).toLocaleDateString() : ''}
                {g.xfr ? ' · +xfr' : ''}
              </div>
            </div>
            <button onClick={() => onLoad && onLoad(g)} title="Cargar en editor" style={{
              padding: '3px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
              background: '#22c55e15', border: '1px solid #22c55e30', color: '#22c55e',
            }}>Usar</button>
            <button onClick={() => exportGraph(g)} title="Descargar .mp" style={{
              padding: '3px 5px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
              background: 'transparent', border: `1px solid ${t.border || '#334155'}`, color: t.dim || '#64748b',
            }}>↓</button>
            <button onClick={() => deleteGraph(g.id)} title="Eliminar" style={{
              padding: '3px 5px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
              background: '#ef444410', border: '1px solid #ef444430', color: '#ef4444',
            }}>✕</button>
          </div>
        ))}
      </div>
    </div>
  )
}
