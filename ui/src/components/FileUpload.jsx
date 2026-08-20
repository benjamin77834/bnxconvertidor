import { useRef } from 'react'

export default function FileUpload({ files, setFiles, onCompile, loading, theme }) {
  const addRef = useRef()
  const t = theme || {}

  const slot = {
    display: 'flex', alignItems: 'center', gap: 8, flex: 1,
    background: t.card || '#1e2433', border: `1px dashed ${t.border || '#334155'}`,
    borderRadius: 8, padding: '8px 14px', cursor: 'pointer',
    fontSize: 13, color: t.muted || '#94a3b8', transition: 'border-color .2s',
  }
  const slotActive = { borderColor: t.accent || '#6366f1', color: t.text || '#e2e8f0' }
  const slotSelected = { borderColor: '#22c55e', background: '#22c55e10' }

  const handleAdd = (e) => {
    Array.from(e.target.files).forEach(f => {
      const ext = f.name.split('.').pop().toLowerCase()
      const mappedExt = ext === 'plan' ? 'mp' : ext  // .plan files treated as .mp
      if (['mp', 'xfr', 'dml', 'pset'].includes(mappedExt)) {
        setFiles(prev => {
          const list = prev[mappedExt] || []
          if (list.some(x => x.name === f.name)) return prev
          const updated = { ...prev, [mappedExt]: [...list, f] }
          if (!prev[`selected_${mappedExt}`]) updated[`selected_${mappedExt}`] = f.name
          return updated
        })
      }
    })
    e.target.value = ''
  }

  const remove = (ext, name) => {
    setFiles(prev => {
      const list = (prev[ext] || []).filter(f => f.name !== name)
      const updated = { ...prev, [ext]: list }
      if (prev[`selected_${ext}`] === name)
        updated[`selected_${ext}`] = list.length > 0 ? list[0].name : null
      return updated
    })
  }

  const select = (ext, name) => setFiles(prev => ({ ...prev, [`selected_${ext}`]: name }))

  const getSelected = (ext) => {
    const list = files[ext] || []
    return list.find(f => f.name === files[`selected_${ext}`]) || null
  }

  const canCompile = getSelected('mp') && !loading

  const fileInfo = {
    mp:  { label: 'Graph', desc: 'Nodos, edges y subgraphs del pipeline', required: true },
    xfr: { label: 'Transform Rules', desc: 'SELECT, WHERE, GROUP BY, JOIN keys (sube múltiples .xfr)', required: false },
    dml: { label: 'Schema', desc: 'Tipos de datos y keys por tabla', required: false },
    pset: { label: 'Parameters', desc: 'Variables del grafo (.pset): rutas, fechas, nombres', required: false },
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 14, color: t.muted || '#94a3b8', textTransform: 'uppercase', letterSpacing: 1 }}>
          Project Files
        </span>
        <button
          style={{
            padding: '4px 10px', background: t.border || '#334155', color: t.muted || '#94a3b8',
            border: 'none', borderRadius: 6, fontSize: 13, cursor: 'pointer',
          }}
          onClick={() => addRef.current.click()}
        >+ Add files</button>
        <input ref={addRef} type="file" multiple accept=".mp,.xfr,.dml,.plan,.pset" hidden onChange={handleAdd} />
      </div>

      {['mp', 'xfr', 'dml', 'pset'].map(ext => {
        const list = files[ext] || []
        const selected = files[`selected_${ext}`]
        const info = fileInfo[ext]
        return (
          <div key={ext} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div>
              <span style={{ fontSize: 13, color: t.text || '#e2e8f0', fontWeight: 600 }}>
                .{ext} — {info.label} {ext === 'xfr' && list.length > 1 && <span style={{ color: '#22c55e', fontSize: 11 }}>({list.length} archivos)</span>}
              </span>
              <span style={{ fontSize: 12, color: info.required ? '#f59e0b' : (t.dim || '#64748b'), marginLeft: 6 }}>
                {info.required ? '(required)' : '(optional)'}
              </span>
              <div style={{ fontSize: 12, color: t.dim || '#64748b', marginTop: 2 }}>
                {info.desc}
              </div>
            </div>
            {list.length === 0 ? (
              <span style={{ fontSize: 11, color: t.dim || '#475569', fontStyle: 'italic' }}>
                No .{ext} files added
              </span>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {list.map(f => (
                  <div key={f.name} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <div style={{
                      ...slot, ...slotActive,
                      ...(ext === 'xfr' ? slotSelected : (selected === f.name ? slotSelected : {})),
                      padding: '6px 10px', fontSize: 12,
                    }}>
                      {ext === 'xfr' || selected === f.name ? '✅' : '📄'} {f.name}
                    </div>
                    {ext !== 'xfr' && selected !== f.name && (
                      <button
                        style={{
                          padding: '4px 8px', background: 'transparent', color: '#22c55e',
                          border: '1px solid #22c55e40', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                        }}
                        onClick={() => select(ext, f.name)}
                      >use</button>
                    )}
                    <button
                      style={{
                        padding: '4px 8px', background: 'transparent', color: '#ef4444',
                        border: '1px solid #ef444440', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                      }}
                      onClick={() => remove(ext, f.name)}
                    >✕</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}

      <button
        style={{
          marginTop: 4, padding: '10px 24px',
          background: canCompile ? (t.accent || '#6366f1') : (t.border || '#334155'),
          color: '#fff', border: 'none', borderRadius: 8,
          fontSize: 14, fontWeight: 600, cursor: canCompile ? 'pointer' : 'not-allowed',
        }}
        onClick={() => {
          console.log('Compiling with xfr files:', (files.xfr || []).map(f => f.name))
          onCompile({
            mp: getSelected('mp'), xfr: files.xfr || [], dml: getSelected('dml'), pset: getSelected('pset'), allXfr: true,
          })
        }}
        disabled={!canCompile}
      >
        {loading ? '⏳ Compiling...' : `🚀 Compile${(files.xfr || []).length > 1 ? ` (${(files.xfr || []).length} xfr)` : ''}`}
      </button>
    </div>
  )
}
