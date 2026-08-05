import { useState, useEffect, useRef } from 'react'
import { LIBRARY_URL } from '../config'

export default function GrafosPage({ theme, onLoadToCompiler }) {
  const t = theme || {}
  const [projects, setProjects] = useState([])
  const [selectedProject, setSelectedProject] = useState(null)
  const [files, setFiles] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileContent, setFileContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [showNewProject, setShowNewProject] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [showUpload, setShowUpload] = useState(false)
  const [uploadName, setUploadName] = useState('')
  const [uploadMp, setUploadMp] = useState('')
  const [uploadXfr, setUploadXfr] = useState('')
  const fileInputRef = useRef(null)

  const card = { background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`, borderRadius: 10, padding: 16 }

  useEffect(() => { fetchProjects() }, [])

  const fetchProjects = async () => {
    setLoading(true)
    try {
      const form = new FormData()
      form.append('action', 'list_projects')
      const res = await fetch(LIBRARY_URL, { method: 'POST', body: form })
      const data = await res.json()
      setProjects(data.projects || [])
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const createProject = async () => {
    if (!newProjectName.trim()) return
    const form = new FormData()
    form.append('action', 'create_project')
    form.append('project', newProjectName.trim())
    await fetch(LIBRARY_URL, { method: 'POST', body: form })
    setNewProjectName('')
    setShowNewProject(false)
    fetchProjects()
  }

  const selectProject = async (proj) => {
    setSelectedProject(proj)
    setSelectedFile(null)
    setFileContent('')
    setLoading(true)
    try {
      const form = new FormData()
      form.append('action', 'list_files')
      form.append('project', proj.name)
      const res = await fetch(LIBRARY_URL, { method: 'POST', body: form })
      const data = await res.json()
      setFiles(data.files || [])
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const selectFile = async (f) => {
    setSelectedFile(f)
    const form = new FormData()
    form.append('action', 'download')
    form.append('project', selectedProject.name)
    form.append('file', f.name)
    const res = await fetch(LIBRARY_URL, { method: 'POST', body: form })
    const data = await res.json()
    setFileContent(data.content || '')
  }

  const uploadGraph = async () => {
    if (!selectedProject || !uploadMp.trim()) return
    const form = new FormData()
    form.append('action', 'upload')
    form.append('project', selectedProject.name)
    form.append('name', uploadName.trim() || 'grafo')
    form.append('mp', uploadMp)
    if (uploadXfr.trim()) form.append('xfr', uploadXfr)
    await fetch(LIBRARY_URL, { method: 'POST', body: form })
    setUploadName(''); setUploadMp(''); setUploadXfr(''); setShowUpload(false)
    selectProject(selectedProject)
  }

  const uploadFiles = async (fileList) => {
    if (!selectedProject) return
    for (const file of fileList) {
      const content = await file.text()
      const form = new FormData()
      form.append('action', 'upload')
      form.append('project', selectedProject.name)
      form.append('name', file.name.replace(/\.(mp|xfr|dml)$/, ''))
      if (file.name.endsWith('.mp')) form.append('mp', content)
      else if (file.name.endsWith('.xfr')) form.append('xfr', content)
      await fetch(LIBRARY_URL, { method: 'POST', body: form })
    }
    selectProject(selectedProject)
  }

  const deleteFile = async (f) => {
    const form = new FormData()
    form.append('action', 'delete')
    form.append('project', selectedProject.name)
    form.append('file', f.name)
    await fetch(LIBRARY_URL, { method: 'POST', body: form })
    setSelectedFile(null); setFileContent('')
    selectProject(selectedProject)
  }

  const deleteProject = async (proj) => {
    if (!confirm(`Borrar proyecto "${proj.name}" y todos sus archivos?`)) return
    const form = new FormData()
    form.append('action', 'delete')
    form.append('project', proj.name)
    await fetch(LIBRARY_URL, { method: 'POST', body: form })
    setSelectedProject(null); setFiles([]); setSelectedFile(null)
    fetchProjects()
  }

  const downloadFile = () => {
    if (!fileContent || !selectedFile) return
    const blob = new Blob([fileContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = selectedFile.name; a.click()
    URL.revokeObjectURL(url)
  }

  const compileFile = async () => {
    if (!fileContent || !selectedFile) return
    // Si es .mp, cargar al Compiler. Si tiene .xfr companion, cargarlo tambien
    let xfrContent = ''
    const baseName = selectedFile.name.replace('.mp', '')
    const xfrFile = files.find(f => f.name === `${baseName}.xfr`)
    if (xfrFile) {
      const form = new FormData()
      form.append('action', 'download')
      form.append('project', selectedProject.name)
      form.append('file', xfrFile.name)
      const res = await fetch(LIBRARY_URL, { method: 'POST', body: form })
      const data = await res.json()
      xfrContent = data.content || ''
    }
    onLoadToCompiler && onLoadToCompiler({ mp: fileContent, xfr: xfrContent, name: baseName })
  }

  return (
    <div style={{ padding: 32, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: t.text || '#e2e8f0', margin: 0 }}>Proyectos de Grafos</h2>
        <p style={{ fontSize: 13, color: t.dim || '#64748b', marginTop: 4 }}>Almacenados en S3 — visibles desde local y Amplify</p>
      </div>

      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', flex: 1 }}>
        {/* Columna 1: Proyectos */}
        <div style={{ flex: '0 0 220px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: t.muted || '#94a3b8' }}>Proyectos</span>
            <button onClick={() => setShowNewProject(!showNewProject)} style={{
              padding: '3px 8px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
              background: '#22c55e15', border: '1px solid #22c55e30', color: '#22c55e',
            }}>+ Nuevo</button>
          </div>

          {showNewProject && (
            <div style={{ display: 'flex', gap: 4 }}>
              <input value={newProjectName} onChange={e => setNewProjectName(e.target.value)}
                placeholder="Nombre..." onKeyDown={e => e.key === 'Enter' && createProject()}
                style={{ flex: 1, padding: '5px 8px', borderRadius: 6, fontSize: 11, background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`, color: t.text || '#e2e8f0', outline: 'none' }}
              />
              <button onClick={createProject} style={{ padding: '5px 8px', borderRadius: 4, fontSize: 11, cursor: 'pointer', background: '#22c55e', color: '#000', border: 'none' }}>OK</button>
            </div>
          )}

          {loading && !selectedProject && <div style={{ fontSize: 11, color: t.dim || '#64748b' }}>Cargando...</div>}

          {projects.map(p => (
            <div key={p.name} onClick={() => selectProject(p)} style={{
              padding: '10px 12px', borderRadius: 8, cursor: 'pointer',
              background: selectedProject?.name === p.name ? '#22c55e15' : (t.card || '#1e2433'),
              border: `1px solid ${selectedProject?.name === p.name ? '#22c55e40' : (t.border || '#334155')}`,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 500, color: t.text || '#e2e8f0' }}>📁 {p.name}</div>
                <div style={{ fontSize: 10, color: t.dim || '#64748b' }}>{p.graphs} grafos</div>
              </div>
              <button onClick={(e) => { e.stopPropagation(); deleteProject(p) }} style={{
                padding: '2px 5px', borderRadius: 4, fontSize: 9, cursor: 'pointer',
                background: '#ef444410', border: '1px solid #ef444430', color: '#ef4444',
              }}>✕</button>
            </div>
          ))}
        </div>

        {/* Columna 2: Archivos del proyecto */}
        {selectedProject && (
          <div style={{ flex: '0 0 280px', display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: t.muted || '#94a3b8' }}>
                {selectedProject.name}/
              </span>
              <div style={{ display: 'flex', gap: 4 }}>
                <button onClick={() => setShowUpload(!showUpload)} style={{
                  padding: '3px 8px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
                  background: '#6366f115', border: '1px solid #6366f130', color: '#6366f1',
                }}>+ Grafo</button>
                <button onClick={() => fileInputRef.current.click()} style={{
                  padding: '3px 8px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
                  background: 'transparent', border: `1px solid ${t.border || '#334155'}`, color: t.dim || '#64748b',
                }}>📂</button>
                <input ref={fileInputRef} type="file" accept=".mp,.xfr,.dml" multiple hidden
                  onChange={e => { if (e.target.files.length) uploadFiles(Array.from(e.target.files)); e.target.value = '' }}
                />
              </div>
            </div>

            {showUpload && (
              <div style={{ ...card, padding: 12, borderLeft: '3px solid #6366f1' }}>
                <input value={uploadName} onChange={e => setUploadName(e.target.value)} placeholder="Nombre del grafo"
                  style={{ width: '100%', padding: '5px 8px', borderRadius: 6, fontSize: 11, marginBottom: 6, background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`, color: t.text || '#e2e8f0', outline: 'none' }}
                />
                <textarea value={uploadMp} onChange={e => setUploadMp(e.target.value)} placeholder=".mp content..."
                  style={{ width: '100%', minHeight: 60, padding: 6, borderRadius: 6, fontSize: 10, background: t.codeBg || '#081220', border: '1px solid #22c55e30', color: '#22c55e', fontFamily: 'monospace', resize: 'vertical', outline: 'none', marginBottom: 4 }}
                />
                <textarea value={uploadXfr} onChange={e => setUploadXfr(e.target.value)} placeholder=".xfr (opcional)"
                  style={{ width: '100%', minHeight: 30, padding: 6, borderRadius: 6, fontSize: 10, background: t.codeBg || '#081220', border: '1px solid #6366f130', color: '#6366f1', fontFamily: 'monospace', resize: 'vertical', outline: 'none', marginBottom: 6 }}
                />
                <button onClick={uploadGraph} disabled={!uploadMp.trim()} style={{
                  width: '100%', padding: 6, borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: 'pointer',
                  background: uploadMp.trim() ? '#6366f1' : '#334155', color: '#fff', border: 'none',
                }}>Subir a S3</button>
              </div>
            )}

            {loading && <div style={{ fontSize: 11, color: t.dim || '#64748b' }}>Cargando...</div>}

            {files.map(f => (
              <div key={f.name} onClick={() => selectFile(f)} style={{
                padding: '8px 10px', borderRadius: 6, cursor: 'pointer',
                background: selectedFile?.name === f.name ? '#6366f115' : (t.card || '#1e2433'),
                border: `1px solid ${selectedFile?.name === f.name ? '#6366f140' : (t.border || '#334155')}`,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <div>
                  <div style={{ fontSize: 12, color: t.text || '#e2e8f0' }}>
                    {f.name.endsWith('.mp') ? '📄' : f.name.endsWith('.xfr') ? '🔄' : '📎'} {f.name}
                  </div>
                  <div style={{ fontSize: 9, color: t.dim || '#64748b' }}>
                    {(f.size/1024).toFixed(1)}KB · {new Date(f.lastModified).toLocaleDateString()}
                  </div>
                </div>
                <button onClick={(e) => { e.stopPropagation(); deleteFile(f) }} style={{
                  padding: '2px 5px', borderRadius: 4, fontSize: 9, cursor: 'pointer',
                  background: '#ef444410', border: '1px solid #ef444430', color: '#ef4444',
                }}>✕</button>
              </div>
            ))}

            {files.length === 0 && !loading && (
              <div style={{ fontSize: 11, color: t.dim || '#64748b', textAlign: 'center', padding: 16 }}>
                Proyecto vacio. Usa "+ Grafo" o 📂 para subir archivos.
              </div>
            )}
          </div>
        )}

        {/* Columna 3: Preview del archivo */}
        {selectedFile && fileContent && (
          <div style={{ flex: 1, minWidth: 300, display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ ...card }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0' }}>{selectedFile.name}</div>
                  <div style={{ fontSize: 11, color: t.dim || '#64748b' }}>{selectedProject.name}/{selectedFile.name}</div>
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button onClick={downloadFile} style={{
                    padding: '6px 12px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                    background: 'transparent', border: `1px solid ${t.border || '#334155'}`, color: t.muted || '#94a3b8',
                  }}>📥 Descargar</button>
                  {selectedFile.name.endsWith('.mp') && (
                    <button onClick={compileFile} style={{
                      padding: '6px 12px', borderRadius: 6, fontSize: 11, cursor: 'pointer', fontWeight: 600,
                      background: '#22c55e', color: '#000', border: 'none',
                    }}>🚀 Compilar</button>
                  )}
                </div>
              </div>
              <pre style={{
                padding: 12, borderRadius: 8, fontSize: 11, maxHeight: 400, overflowY: 'auto',
                background: t.codeBg || '#081220', margin: 0, whiteSpace: 'pre-wrap',
                color: selectedFile.name.endsWith('.mp') ? '#22c55e' : selectedFile.name.endsWith('.xfr') ? '#6366f1' : (t.muted || '#94a3b8'),
                fontFamily: 'monospace', border: `1px solid ${selectedFile.name.endsWith('.mp') ? '#22c55e20' : '#6366f120'}`,
              }}>{fileContent}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
