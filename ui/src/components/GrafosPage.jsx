import { useState, useEffect, useRef } from 'react'
import { LIBRARY_URL } from '../config'

export default function GrafosPage({ theme, onLoadToCompiler }) {
  const t = theme || {}
  const [projects, setProjects] = useState([])
  const [selectedProject, setSelectedProject] = useState(null)
  const [files, setFiles] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileContent, setFileContent] = useState('')
  const [selected, setSelected] = useState(new Set()) // multi-select
  const [loading, setLoading] = useState(false)
  const [showNewProject, setShowNewProject] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [showUpload, setShowUpload] = useState(false)
  const [uploadName, setUploadName] = useState('')
  const [uploadMp, setUploadMp] = useState('')
  const [uploadXfr, setUploadXfr] = useState('')
  const [compiling, setCompiling] = useState(false)
  const fileInputRef = useRef(null)

  const card = { background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`, borderRadius: 10, padding: 16 }

  useEffect(() => { fetchProjects() }, [])

  const fetchProjects = async () => {
    setLoading(true)
    try {
      const form = new FormData(); form.append('action', 'list_projects')
      const res = await fetch(LIBRARY_URL, { method: 'POST', body: form })
      const data = await res.json()
      setProjects(data.projects || [])
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const createProject = async () => {
    if (!newProjectName.trim()) return
    const form = new FormData(); form.append('action', 'create_project'); form.append('project', newProjectName.trim())
    await fetch(LIBRARY_URL, { method: 'POST', body: form })
    setNewProjectName(''); setShowNewProject(false); fetchProjects()
  }

  const selectProject = async (proj) => {
    setSelectedProject(proj); setSelectedFile(null); setFileContent(''); setSelected(new Set())
    setLoading(true)
    try {
      const form = new FormData(); form.append('action', 'list_files'); form.append('project', proj.name)
      const res = await fetch(LIBRARY_URL, { method: 'POST', body: form })
      const data = await res.json()
      setFiles(data.files || [])
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const selectFile = async (f) => {
    setSelectedFile(f)
    const form = new FormData(); form.append('action', 'download'); form.append('project', selectedProject.name); form.append('file', f.name)
    const res = await fetch(LIBRARY_URL, { method: 'POST', body: form })
    const data = await res.json()
    setFileContent(data.content || '')
  }

  const toggleSelect = (fname) => {
    const next = new Set(selected)
    if (next.has(fname)) next.delete(fname); else next.add(fname)
    setSelected(next)
  }

  const selectAll = () => {
    if (selected.size === files.length) setSelected(new Set())
    else setSelected(new Set(files.map(f => f.name)))
  }

  // Compilar seleccion — descarga archivos seleccionados y envia al Compiler
  const compileSelection = async () => {
    if (!selectedProject || selected.size === 0) return
    setCompiling(true)
    const downloaded = {}
    for (const fname of selected) {
      const form = new FormData(); form.append('action', 'download'); form.append('project', selectedProject.name); form.append('file', fname)
      const res = await fetch(LIBRARY_URL, { method: 'POST', body: form })
      const data = await res.json()
      if (data.content) downloaded[fname] = data.content
    }

    // Clasificar archivos
    const mpFiles = Object.entries(downloaded).filter(([k]) => k.endsWith('.mp'))
    const xfrFiles = Object.entries(downloaded).filter(([k]) => k.endsWith('.xfr'))
    const psetFiles = Object.entries(downloaded).filter(([k]) => k.endsWith('.pset'))
    const planFiles = Object.entries(downloaded).filter(([k]) => k.endsWith('.plan'))

    // Enviar al Compiler
    if (onLoadToCompiler) {
      // Concatenate all .xfr files into one (each with a header comment)
      const combinedXfr = xfrFiles.map(([name, content]) => 
        `# === ${name} ===\n${content}`
      ).join('\n\n')
      
      onLoadToCompiler({
        mp: mpFiles.length ? mpFiles[0][1] : '',
        xfr: combinedXfr,
        pset: psetFiles.length ? psetFiles[0][1] : '',
        plan: planFiles.length ? planFiles[0][1] : '',
        mpFiles: mpFiles.map(([name, content]) => ({ name, content })),
        xfrFiles: xfrFiles.map(([name, content]) => ({ name, content })),
        name: selectedProject.name,
      })
    }
    setCompiling(false)
  }

  const uploadGraph = async () => {
    if (!selectedProject || !uploadMp.trim()) return
    const form = new FormData(); form.append('action', 'upload'); form.append('project', selectedProject.name)
    form.append('name', uploadName.trim() || 'grafo'); form.append('mp', uploadMp)
    if (uploadXfr.trim()) form.append('xfr', uploadXfr)
    await fetch(LIBRARY_URL, { method: 'POST', body: form })
    setUploadName(''); setUploadMp(''); setUploadXfr(''); setShowUpload(false)
    selectProject(selectedProject)
  }

  const uploadFiles = async (fileList) => {
    if (!selectedProject) return
    for (const file of fileList) {
      const content = await file.text()
      const form = new FormData(); form.append('action', 'upload'); form.append('project', selectedProject.name)
      form.append('name', file.name.replace(/\.(mp|xfr|dml|pset|plan)$/, ''))
      if (file.name.endsWith('.mp')) form.append('mp', content)
      else if (file.name.endsWith('.xfr')) form.append('xfr', content)
      else { form.append('mp', content) } // generic
      await fetch(LIBRARY_URL, { method: 'POST', body: form })
    }
    selectProject(selectedProject)
  }

  const deleteFile = async (f) => {
    const form = new FormData(); form.append('action', 'delete'); form.append('project', selectedProject.name); form.append('file', f.name)
    await fetch(LIBRARY_URL, { method: 'POST', body: form })
    setSelectedFile(null); setFileContent('')
    selectProject(selectedProject)
  }

  const deleteProject = async (proj) => {
    if (!confirm(`Borrar proyecto "${proj.name}" y todos sus archivos?`)) return
    const form = new FormData(); form.append('action', 'delete'); form.append('project', proj.name)
    await fetch(LIBRARY_URL, { method: 'POST', body: form })
    setSelectedProject(null); setFiles([]); setSelectedFile(null); fetchProjects()
  }

  const downloadFile = (f) => {
    if (!selectedProject) return
    const form = new FormData(); form.append('action', 'download'); form.append('project', selectedProject.name); form.append('file', f?.name || selectedFile?.name)
    fetch(LIBRARY_URL, { method: 'POST', body: form })
      .then(res => res.json())
      .then(data => {
        if (data.content) {
          const blob = new Blob([data.content], { type: 'text/plain' })
          const url = URL.createObjectURL(blob); const a = document.createElement('a')
          a.href = url; a.download = f?.name || selectedFile?.name; a.click(); URL.revokeObjectURL(url)
        }
      })
  }

  const downloadSelected = async () => {
    if (!selectedProject || selected.size === 0) return
    for (const fname of selected) {
      const form = new FormData(); form.append('action', 'download'); form.append('project', selectedProject.name); form.append('file', fname)
      const res = await fetch(LIBRARY_URL, { method: 'POST', body: form })
      const data = await res.json()
      if (data.content) {
        const blob = new Blob([data.content], { type: 'text/plain' })
        const url = URL.createObjectURL(blob); const a = document.createElement('a')
        a.href = url; a.download = fname; a.click(); URL.revokeObjectURL(url)
      }
    }
  }

  const fileIcon = (name) => {
    if (name.endsWith('.mp')) return '📄'
    if (name.endsWith('.xfr')) return '🔄'
    if (name.endsWith('.pset')) return '⚙️'
    if (name.endsWith('.plan')) return '📋'
    if (name.endsWith('.dml')) return '🗂️'
    return '📎'
  }

  return (
    <div style={{ padding: 32, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: t.text || '#e2e8f0', margin: 0 }}>Proyectos de Grafos</h2>
        <p style={{ fontSize: 13, color: t.dim || '#64748b', marginTop: 4 }}>Selecciona archivos (.mp, .xfr, .pset, .plan) y compila desde aqui</p>
      </div>

      <div style={{ display: 'flex', gap: 20, flex: 1, minHeight: 0 }}>
        {/* Col 1: Proyectos */}
        <div style={{ flex: '0 0 200px', display: 'flex', flexDirection: 'column', gap: 8, overflowY: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: t.muted || '#94a3b8' }}>Proyectos</span>
            <button onClick={() => setShowNewProject(!showNewProject)} style={{ padding: '3px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer', background: '#22c55e15', border: '1px solid #22c55e30', color: '#22c55e' }}>+</button>
          </div>
          {showNewProject && (
            <div style={{ display: 'flex', gap: 4 }}>
              <input value={newProjectName} onChange={e => setNewProjectName(e.target.value)} placeholder="Nombre..." onKeyDown={e => e.key === 'Enter' && createProject()}
                style={{ flex: 1, padding: '4px 6px', borderRadius: 4, fontSize: 11, background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`, color: t.text || '#e2e8f0', outline: 'none' }} />
              <button onClick={createProject} style={{ padding: '4px 6px', borderRadius: 4, fontSize: 10, cursor: 'pointer', background: '#22c55e', color: '#000', border: 'none' }}>OK</button>
            </div>
          )}
          {projects.map(p => (
            <div key={p.name} onClick={() => selectProject(p)} style={{
              padding: '8px 10px', borderRadius: 6, cursor: 'pointer',
              background: selectedProject?.name === p.name ? '#22c55e15' : (t.card || '#1e2433'),
              border: `1px solid ${selectedProject?.name === p.name ? '#22c55e40' : (t.border || '#334155')}`,
            }}>
              <div style={{ fontSize: 12, fontWeight: 500, color: t.text || '#e2e8f0' }}>📁 {p.name}</div>
              <div style={{ fontSize: 10, color: t.dim || '#64748b' }}>{p.graphs} grafos</div>
            </div>
          ))}
        </div>

        {/* Col 2: Archivos */}
        {selectedProject && (
          <div style={{ flex: '0 0 300px', display: 'flex', flexDirection: 'column', gap: 8, overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 4 }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: t.muted || '#94a3b8' }}>{selectedProject.name}/</span>
              <div style={{ display: 'flex', gap: 4 }}>
                <button onClick={selectAll} style={{ padding: '3px 6px', borderRadius: 4, fontSize: 10, cursor: 'pointer', background: 'transparent', border: `1px solid ${t.border || '#334155'}`, color: t.dim || '#64748b' }}>
                  {selected.size === files.length ? '☐ Ninguno' : '☑ Todos'}
                </button>
                <button onClick={() => setShowUpload(!showUpload)} style={{ padding: '3px 6px', borderRadius: 4, fontSize: 10, cursor: 'pointer', background: '#6366f115', border: '1px solid #6366f130', color: '#6366f1' }}>+ Grafo</button>
                <button onClick={() => fileInputRef.current.click()} style={{ padding: '3px 6px', borderRadius: 4, fontSize: 10, cursor: 'pointer', background: 'transparent', border: `1px solid ${t.border || '#334155'}`, color: t.dim || '#64748b' }}>📂</button>
                <input ref={fileInputRef} type="file" accept=".mp,.xfr,.dml,.pset,.plan" multiple hidden onChange={e => { if (e.target.files.length) uploadFiles(Array.from(e.target.files)); e.target.value = '' }} />
              </div>
            </div>

            {/* Compilar/Descargar seleccion */}
            {selected.size > 0 && (
              <div style={{ display: 'flex', gap: 4 }}>
                <button onClick={compileSelection} disabled={compiling} style={{
                  padding: '8px 12px', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  background: '#22c55e', color: '#000', border: 'none', flex: 1,
                }}>
                  {compiling ? '⏳...' : `🚀 Compilar ${selected.size}`}
                </button>
                <button onClick={downloadSelected} style={{
                  padding: '8px 12px', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  background: '#6366f120', color: '#6366f1', border: '1px solid #6366f140',
                }}>
                  📥 Bajar
                </button>
              </div>
            )}

            {showUpload && (
              <div style={{ ...card, padding: 10, borderLeft: '3px solid #6366f1' }}>
                <input value={uploadName} onChange={e => setUploadName(e.target.value)} placeholder="Nombre"
                  style={{ width: '100%', padding: '4px 6px', borderRadius: 4, fontSize: 11, marginBottom: 4, background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`, color: t.text || '#e2e8f0', outline: 'none' }} />
                <textarea value={uploadMp} onChange={e => setUploadMp(e.target.value)} placeholder=".mp"
                  style={{ width: '100%', minHeight: 50, padding: 4, borderRadius: 4, fontSize: 10, background: t.codeBg || '#081220', border: '1px solid #22c55e30', color: '#22c55e', fontFamily: 'monospace', resize: 'vertical', outline: 'none', marginBottom: 4 }} />
                <textarea value={uploadXfr} onChange={e => setUploadXfr(e.target.value)} placeholder=".xfr (opcional)"
                  style={{ width: '100%', minHeight: 30, padding: 4, borderRadius: 4, fontSize: 10, background: t.codeBg || '#081220', border: '1px solid #6366f130', color: '#6366f1', fontFamily: 'monospace', resize: 'vertical', outline: 'none', marginBottom: 4 }} />
                <button onClick={uploadGraph} disabled={!uploadMp.trim()} style={{ width: '100%', padding: 5, borderRadius: 4, fontSize: 11, cursor: 'pointer', background: '#6366f1', color: '#fff', border: 'none' }}>Subir</button>
              </div>
            )}

            {files.map(f => (
              <div key={f.name} style={{
                padding: '6px 8px', borderRadius: 6, cursor: 'pointer',
                background: selectedFile?.name === f.name ? '#6366f115' : (t.card || '#1e2433'),
                border: `1px solid ${selected.has(f.name) ? '#22c55e40' : selectedFile?.name === f.name ? '#6366f140' : (t.border || '#334155')}`,
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
                <input type="checkbox" checked={selected.has(f.name)} onChange={() => toggleSelect(f.name)}
                  style={{ cursor: 'pointer', accentColor: '#22c55e' }} />
                <div onClick={() => selectFile(f)} style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 11, color: t.text || '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {fileIcon(f.name)} {f.name}
                  </div>
                  <div style={{ fontSize: 9, color: t.dim || '#64748b' }}>
                    {(f.size / 1024).toFixed(1)}KB
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 3 }}>
                  <button onClick={(e) => { e.stopPropagation(); downloadFile(f) }} style={{ padding: '2px 4px', borderRadius: 3, fontSize: 9, cursor: 'pointer', background: '#6366f110', border: '1px solid #6366f130', color: '#6366f1' }}>📥</button>
                  <button onClick={() => deleteFile(f)} style={{ padding: '2px 4px', borderRadius: 3, fontSize: 9, cursor: 'pointer', background: '#ef444410', border: '1px solid #ef444430', color: '#ef4444' }}>✕</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Col 3: Preview */}
        {selectedFile && fileContent && (
          <div style={{ flex: 1, minWidth: 250, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ ...card }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: t.text || '#e2e8f0' }}>{selectedFile.name}</div>
                <div style={{ display: 'flex', gap: 4 }}>
                  <button onClick={() => downloadFile(selectedFile)} style={{ padding: '4px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer', background: 'transparent', border: `1px solid ${t.border || '#334155'}`, color: t.muted || '#94a3b8' }}>📥</button>
                  {selectedFile.name.endsWith('.mp') && (
                    <button onClick={() => onLoadToCompiler && onLoadToCompiler({ mp: fileContent, xfr: '', name: selectedFile.name.replace('.mp', '') })} style={{ padding: '4px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer', background: '#22c55e', color: '#000', border: 'none', fontWeight: 600 }}>🚀 Compilar</button>
                  )}
                </div>
              </div>
              <pre style={{
                padding: 10, borderRadius: 6, fontSize: 11, maxHeight: 400, overflowY: 'auto',
                background: t.codeBg || '#081220', margin: 0, whiteSpace: 'pre-wrap',
                color: selectedFile.name.endsWith('.mp') ? '#22c55e' : selectedFile.name.endsWith('.xfr') ? '#6366f1' : selectedFile.name.endsWith('.pset') ? '#f59e0b' : (t.muted || '#94a3b8'),
                fontFamily: 'monospace', border: '1px solid #33415530',
              }}>{fileContent}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
