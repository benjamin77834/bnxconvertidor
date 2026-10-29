import { useState, useEffect } from 'react'
import { COMPILE_URL } from '../config'

// Seccion "Framework MLOps v2": genera un PAQUETE NUEVO y mejorado del framework
// (sin tocar el del banco) y lo empaqueta en un ZIP con entorno virtual (run.sh
// crea el venv + instala + prueba), ejemplos y pruebas reales.
const API_BASE = COMPILE_URL.replace(/\/compile$/, '')
const MANIFEST_URL = `${API_BASE}/mlops/package/manifest`
const BUILD_URL = `${API_BASE}/mlops/package/build`
const DOWNLOAD_URL = (bank, extra) => `${API_BASE}/mlops/package/download?bank=${bank ? 1 : 0}&extra=${extra ? 1 : 0}`

export default function MLOpsPackagePage({ theme, onEmulate }) {
  const t = theme || {}
  const [manifest, setManifest] = useState(null)
  const [bankLibs, setBankLibs] = useState(true)
  const [extraSteps, setExtraSteps] = useState(false)
  const [monitoring, setMonitoring] = useState(false)
  const [separateMon, setSeparateMon] = useState(false)
  const [fullEnv, setFullEnv] = useState(false)
  const [pyTarget, setPyTarget] = useState('all')  // all | py38-311 | py312plus
  const [loading, setLoading] = useState(true)

  // Entrada del usuario: codigo pegado + archivos de carpeta.
  const [pasted, setPasted] = useState('')
  const [pastedName, setPastedName] = useState('mi_fuente.py')
  const [files, setFiles] = useState([])        // [{name, code}]
  const [building, setBuilding] = useState(false)
  const [buildResult, setBuildResult] = useState(null)  // {report, download_url, filename, edit_token}
  const [buildError, setBuildError] = useState('')
  // Editor del paquete generado (editar archivos y rehacer).
  const [editFiles, setEditFiles] = useState([])      // [{path, content, editable}]
  const [activePath, setActivePath] = useState('')
  const [editContent, setEditContent] = useState('')
  const [editDirty, setEditDirty] = useState(false)
  const [editMsg, setEditMsg] = useState('')
  const [rebuilding, setRebuilding] = useState(false)

  useEffect(() => {
    fetch(MANIFEST_URL)
      .then(r => r.json())
      .then(d => setManifest(d))
      .catch(() => setManifest(null))
      .finally(() => setLoading(false))
  }, [])

  // Lee los .py de una carpeta o seleccion de archivos.
  const onPickFiles = async (fileList) => {
    const arr = Array.from(fileList || []).filter(f => /\.(py|txt)$/i.test(f.name))
    const read = await Promise.all(arr.map(f => new Promise(resolve => {
      const r = new FileReader()
      r.onload = () => resolve({ name: f.webkitRelativePath || f.name, code: String(r.result || '') })
      r.onerror = () => resolve(null)
      r.readAsText(f)
    })))
    setFiles(prev => {
      const map = new Map(prev.map(x => [x.name, x]))
      for (const x of read) if (x) map.set(x.name, x)
      return Array.from(map.values())
    })
  }

  const sourcesToSend = () => {
    const out = [...files]
    if (pasted.trim()) out.unshift({ name: pastedName.trim() || 'mi_fuente.py', code: pasted })
    return out
  }

  const buildMine = async () => {
    const sources = sourcesToSend()
    if (!sources.length) { setBuildError('Pega código o sube al menos un archivo .py.'); return }
    setBuilding(true); setBuildError(''); setBuildResult(null)
    try {
      const res = await fetch(BUILD_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sources, include_bank_libs: bankLibs, optimize: true, extra_steps: extraSteps,
          include_monitoring: monitoring, separate_monitoring: monitoring && separateMon,
          full_env: fullEnv, py_target: pyTarget,
        }),
      })
      const data = await res.json()
      if (!res.ok || data.error) { setBuildError(data.error || `HTTP ${res.status}`); return }
      setBuildResult(data)
      // Cargar los archivos editables del paquete recién generado.
      if (data.edit_token) loadEditFiles(data.edit_token)
    } catch (e) { setBuildError('Error de red: ' + e.message) }
    finally { setBuilding(false) }
  }

  const loadEditFiles = async (token) => {
    try {
      const res = await fetch(`${API_BASE}/mlops/package/files?token=${encodeURIComponent(token)}`)
      const data = await res.json()
      if (!res.ok || data.error) return
      setEditFiles(data.files || [])
      // Abrir por defecto el primer archivo con "a revisar" (TODOs), o el primero.
      const withTodo = (data.files || []).find(f => f.editable && f.content.includes('# TODO py2spark'))
      const first = withTodo || (data.files || []).find(f => f.editable) || (data.files || [])[0]
      if (first) { setActivePath(first.path); setEditContent(first.content); setEditDirty(false) }
    } catch (e) { /* silencioso */ }
  }

  const openFile = (path) => {
    const f = editFiles.find(x => x.path === path)
    if (!f) return
    setActivePath(path); setEditContent(f.content); setEditDirty(false); setEditMsg('')
  }

  const saveFile = async () => {
    if (!buildResult?.edit_token || !activePath) return
    setEditMsg('Guardando…')
    try {
      const res = await fetch(`${API_BASE}/mlops/package/save`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: buildResult.edit_token, path: activePath, content: editContent }),
      })
      const data = await res.json()
      if (!res.ok || data.error) { setEditMsg('⚠️ ' + (data.error || 'no se pudo guardar')); return }
      // Reflejar el cambio en la lista local.
      setEditFiles(fs => fs.map(f => f.path === activePath ? { ...f, content: editContent } : f))
      setEditDirty(false); setEditMsg('✅ Guardado')
    } catch (e) { setEditMsg('⚠️ ' + e.message) }
  }

  const rebuild = async () => {
    if (!buildResult?.edit_token) return
    setRebuilding(true); setEditMsg('')
    try {
      const res = await fetch(`${API_BASE}/mlops/package/rebuild`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: buildResult.edit_token }),
      })
      const data = await res.json()
      if (!res.ok || data.error) { setEditMsg('⚠️ ' + (data.error || 'no se pudo rehacer')); return }
      setBuildResult(r => ({ ...r, size: data.size, download_url: data.download_url, filename: data.filename }))
      setEditMsg('✅ Paquete rehecho con tus ediciones — listo para descargar.')
    } catch (e) { setEditMsg('⚠️ ' + e.message) }
    finally { setRebuilding(false) }
  }

  const card = {
    background: t.card || '#0f172a', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 16,
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 16, width: '100%', boxSizing: 'border-box' }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 22, color: t.text || '#e2e8f0' }}>📦 Framework MLOps v2 (mejorado)</h2>
        <p style={{ margin: '4px 0 0', fontSize: 13, color: t.muted || '#94a3b8', maxWidth: 900 }}>
          Genera un <b>paquete nuevo</b> del framework que corrige los problemas detectados (ver el diagnóstico
          en la sección anterior), <b>sin tocar el código del banco</b>. Trae un <b>entorno virtual reproducible</b>
          (como Data Sintética): <code>run.sh</code> crea el venv, instala todo y corre las pruebas.
        </p>
      </div>

      {/* === SUBE TU CÓDIGO Y GENERA TU FRAMEWORK === */}
      <div style={{ ...card, borderColor: (t.accent || '#6366f1') + '66' }}>
        <div style={{ fontSize: 15, fontWeight: 800, color: t.text || '#e2e8f0' }}>
          🚀 Genera TU framework desde tu código
        </div>
        <p style={{ margin: '4px 0 10px', fontSize: 12.5, color: t.muted || '#94a3b8', maxWidth: 900 }}>
          Pega tu Python (pandas) del negocio o sube una carpeta de <code>.py</code> (una fuente por archivo).
          BNX convierte cada uno a PySpark, lo envuelve en el contrato del framework v2 (hereda de
          <code>BaseAggregate</code>), lo registra en el router y te entrega el paquete completo con venv y pruebas.
        </p>

        {/* Ejemplos cargables de un clic */}
        {(manifest?.examples || []).length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
            <span style={{ fontSize: 11.5, color: t.muted || '#94a3b8' }}>📚 Ejemplos:</span>
            {manifest.examples.map(ex => (
              <button key={ex.id} onClick={() => { setPasted(ex.code); setPastedName(ex.name) }}
                title={`Cargar ejemplo: ${ex.title}`}
                style={{
                  padding: '4px 10px', borderRadius: 999, fontSize: 11.5, cursor: 'pointer',
                  background: (t.accent || '#6366f1') + '18', color: t.accent || '#818cf8',
                  border: `1px solid ${(t.accent || '#6366f1')}44`,
                }}>{ex.title}</button>
            ))}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, alignItems: 'start' }}>
          {/* Pegar codigo */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: 0 }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: '#38bdf8' }}>📋 Pegar código</span>
              <input value={pastedName} onChange={e => setPastedName(e.target.value)}
                placeholder="nombre.py"
                style={{
                  marginLeft: 'auto', padding: '4px 8px', borderRadius: 6, fontSize: 11,
                  background: t.codeBg || '#081220', color: t.text || '#e2e8f0',
                  border: `1px solid ${t.border || '#334155'}`, outline: 'none', width: 140,
                }} />
            </div>
            <textarea value={pasted} onChange={e => setPasted(e.target.value)} spellCheck={false}
              placeholder="import pandas as pd&#10;df = pd.read_csv('bureau.csv')&#10;g = df.groupby('cliente_id').agg({'saldo':'sum'})&#10;..."
              style={{
                width: '100%', minHeight: 180, padding: 10, borderRadius: 8, boxSizing: 'border-box',
                background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
                color: t.text || '#e2e8f0', fontFamily: 'monospace', fontSize: 12, lineHeight: 1.5,
                resize: 'vertical', outline: 'none', whiteSpace: 'pre',
              }} />
          </div>

          {/* Subir carpeta / archivos */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minWidth: 0 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: '#a78bfa' }}>📁 Subir carpeta o archivos .py</span>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <label style={{ ...uploadBtn(t) }}>
                📁 Carpeta completa
                <input type="file" webkitdirectory="" directory="" multiple style={{ display: 'none' }}
                  onChange={e => onPickFiles(e.target.files)} />
              </label>
              <label style={{ ...uploadBtn(t) }}>
                📄 Archivos .py
                <input type="file" accept=".py,.txt" multiple style={{ display: 'none' }}
                  onChange={e => onPickFiles(e.target.files)} />
              </label>
              {files.length > 0 && (
                <button onClick={() => setFiles([])} style={{
                  padding: '7px 12px', borderRadius: 8, fontSize: 12, cursor: 'pointer',
                  background: 'transparent', color: t.muted || '#94a3b8', border: `1px solid ${t.border || '#334155'}`,
                }}>Quitar todos</button>
              )}
            </div>
            <div style={{
              flex: 1, minHeight: 120, maxHeight: 180, overflow: 'auto', padding: 8, borderRadius: 8,
              background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
            }}>
              {files.length === 0 ? (
                <span style={{ fontSize: 12, color: t.muted || '#94a3b8' }}>
                  Los archivos .py detectados aparecerán aquí (uno = una fuente del framework).
                </span>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  {files.map((f, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11.5 }}>
                      <span style={{ color: '#22c55e' }}>•</span>
                      <span style={{ color: t.text || '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</span>
                      <span style={{ color: t.dim || '#64748b', marginLeft: 'auto' }}>{(f.code.length / 1024).toFixed(1)} KB</span>
                      <button onClick={() => setFiles(prev => prev.filter((_, k) => k !== i))}
                        style={{ background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', fontSize: 12 }}>✕</button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Opciones de generación */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 12 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: t.text || '#e2e8f0', cursor: 'pointer' }}>
            <input type="checkbox" checked={extraSteps} onChange={e => setExtraSteps(e.target.checked)} />
            Generar también los demás pasos (feature engineering, vector assembler, scoring + pipeline)
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: t.text || '#e2e8f0', cursor: 'pointer' }}>
            <input type="checkbox" checked={monitoring} onChange={e => setMonitoring(e.target.checked)} />
            Incluir monitoreo (PSI / CSI / Data Quality)
          </label>
          {monitoring && (
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: t.muted || '#94a3b8', cursor: 'pointer', marginLeft: 24 }}>
              <input type="checkbox" checked={separateMon} onChange={e => setSeparateMon(e.target.checked)} />
              …como <b style={{ color: t.text }}>&nbsp;paquete separado</b>&nbsp; (framework_mlops_metrics, como el lib_mkop_metrics del banco)
            </label>
          )}
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: t.text || '#e2e8f0', cursor: 'pointer' }}>
            <input type="checkbox" checked={bankLibs} onChange={e => setBankLibs(e.target.checked)} />
            Incluir libs internas del banco en requirements.txt
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: t.text || '#e2e8f0', cursor: 'pointer' }}>
            <input type="checkbox" checked={fullEnv} onChange={e => setFullEnv(e.target.checked)} />
            <span>Incluir <b>ambiente completo</b> (PySpark offline en <code>vendor/</code> + <code>setup.sh</code> que monta el venv sin internet)</span>
          </label>
          {fullEnv && (
            <div style={{ marginLeft: 24, display: 'flex', flexDirection: 'column', gap: 6 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: t.text || '#e2e8f0' }}>
                Versión de Python del destino:
                <select value={pyTarget} onChange={e => setPyTarget(e.target.value)}
                  style={{
                    padding: '5px 8px', borderRadius: 6, fontSize: 12,
                    background: t.codeBg || '#081220', color: t.text || '#e2e8f0',
                    border: `1px solid ${t.border || '#334155'}`, outline: 'none', cursor: 'pointer',
                  }}>
                  <option value="all">Cualquiera (universal) — ~736 MB</option>
                  <option value="py38-311">Python 3.8–3.11 — ~306 MB</option>
                  <option value="py312plus">Python 3.12+ — ~417 MB</option>
                </select>
              </label>
              <div style={{ fontSize: 11, color: t.muted || '#94a3b8' }}>
                Elige la versión de los nodos del banco para bajar el tamaño (empaqueta UNA serie de PySpark
                en vez de dos). Usa tu Python y Java del sistema; esos no se empaquetan.
              </div>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 10, flexWrap: 'wrap' }}>
          <button onClick={buildMine} disabled={building}
            style={{
              padding: '11px 22px', borderRadius: 8, fontSize: 14, fontWeight: 700,
              cursor: building ? 'wait' : 'pointer', background: t.accent || '#6366f1', color: '#fff', border: 'none',
            }}>
            {building ? '⏳ Generando…' : '🚀 Generar mi framework'}
          </button>
          {onEmulate && (
            <button
              onClick={() => {
                const s = sourcesToSend()
                if (!s.length) { setBuildError('Pega código o sube al menos un archivo .py para emular.'); return }
                onEmulate(s.map(x => ({ id: x.name, name: x.name.replace(/\.(py|txt)$/i, ''), code: x.code })))
              }}
              title="Lleva estas fuentes al Emulador MLOps y córrelas con datos sintéticos"
              style={{
                padding: '11px 18px', borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: 'pointer',
                background: 'transparent', color: '#2dd4bf', border: '1px solid #14b8a655',
              }}>
              🔬 Emular estas fuentes
            </button>
          )}
          <span style={{ fontSize: 12, color: t.muted || '#94a3b8' }}>
            {sourcesToSend().length} fuente(s) a procesar
          </span>
          {buildError && <span style={{ fontSize: 12, color: '#f87171' }}>⚠️ {buildError}</span>}
        </div>

        {/* Resultado de la generacion */}
        {buildResult && (
          <div style={{ marginTop: 12, padding: 12, borderRadius: 8, background: '#22c55e10', border: '1px solid #22c55e40' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: '#22c55e' }}>
                ✅ Paquete generado ({buildResult.size >= 1048576
                  ? (buildResult.size / 1048576).toFixed(1) + ' MB'
                  : (buildResult.size / 1024).toFixed(1) + ' KB'})
              </span>
              <a href={`${API_BASE}${buildResult.download_url}`} download
                style={{
                  padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 700, textDecoration: 'none',
                  background: '#22c55e', color: '#000',
                }}>📦 Descargar {buildResult.filename}</a>
            </div>
            {(buildResult.report || []).length > 0 && (
              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {(() => {
                  const sourcesR = buildResult.report.filter(r => !r._meta)
                  const meta = buildResult.report.find(r => r._meta)
                  const totalTodos = sourcesR.reduce((n, r) => n + ((r.todos || []).length), 0)
                  return (
                    <>
                      <div style={{ fontSize: 11.5, color: t.muted || '#94a3b8', marginBottom: 2 }}>
                        {totalTodos > 0
                          ? `⚠️ ${totalTodos} línea(s) requieren revisión manual en total. Revisa los puntos marcados abajo (van con un "# TODO py2spark" en el archivo generado).`
                          : '✅ Todas las fuentes convirtieron sin construcciones no traducibles.'}
                      </div>
                      {meta?.full_env && (
                        <div style={{ fontSize: 11.5, color: '#2dd4bf', marginBottom: 2 }}>
                          📦 Ambiente completo incluido: PySpark offline en <code>vendor/</code>
                          {(meta.vendor_series || []).length ? ` (${meta.vendor_series.join(', ')})` : ''}. Monta con <code>bash setup.sh</code>.
                        </div>
                      )}
                    </>
                  )
                })()}
                {buildResult.report.filter(r => !r._meta).map((r, i) => (
                  <div key={i} style={{ fontSize: 11.5, color: t.text || '#e2e8f0' }}>
                    <div>
                      {r.ok ? '✅' : '⚠️'} <b>{r.source || r.name}</b>
                      <span style={{ color: t.muted || '#94a3b8' }}> ← {r.name}</span>
                      {r.file && <span style={{ color: t.dim || '#64748b' }}> · {r.file}</span>}
                      {r.ok
                        ? ((r.todos || []).length
                          ? <span style={{ color: '#f59e0b' }}> · {r.todos.length} línea(s) a revisar</span>
                          : <span style={{ color: '#22c55e' }}> · conversión limpia</span>)
                        : <span style={{ color: '#f87171' }}> · {r.reason}</span>}
                    </div>
                    {/* Detalle: lineas no traducibles de esta fuente */}
                    {(r.todos || []).length > 0 && (
                      <div style={{
                        marginTop: 4, marginLeft: 16, display: 'flex', flexDirection: 'column', gap: 4,
                        borderLeft: `2px solid #f59e0b55`, paddingLeft: 10,
                      }}>
                        {r.todos.map((td, k) => (
                          <div key={k} style={{ fontSize: 11 }}>
                            <span style={{
                              fontFamily: 'monospace', color: '#fbbf24', fontWeight: 700,
                              background: '#f59e0b18', padding: '1px 6px', borderRadius: 4,
                            }}>línea {td.line}</span>
                            <span style={{ color: t.text || '#e2e8f0' }}> {td.text.replace(/^TODO py2spark:\s*/, '')}</span>
                            {td.original && (
                              <div style={{ marginTop: 2, fontFamily: 'monospace', color: t.dim || '#64748b' }}>
                                ↳ original: <span style={{ color: '#94a3b8' }}>{td.original}</span>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* EDITOR: editar archivos generados y rehacer el paquete */}
            {editFiles.length > 0 && (
              <div style={{ marginTop: 14, borderTop: `1px solid ${t.border || '#334155'}`, paddingTop: 12 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0', marginBottom: 8 }}>
                  ✏️ Editar archivos y rehacer el paquete
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 12, alignItems: 'start' }}>
                  {/* Lista de archivos */}
                  <div style={{
                    maxHeight: 360, overflow: 'auto', borderRadius: 8,
                    background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
                  }}>
                    {editFiles.map((f, i) => {
                      const hasTodo = f.content.includes('# TODO py2spark')
                      const active = f.path === activePath
                      return (
                        <button key={i} onClick={() => openFile(f.path)} disabled={!f.editable}
                          style={{
                            display: 'block', width: '100%', textAlign: 'left', cursor: f.editable ? 'pointer' : 'default',
                            padding: '6px 10px', fontSize: 11, fontFamily: 'monospace',
                            background: active ? (t.accent || '#6366f1') + '22' : 'transparent',
                            color: f.editable ? (active ? (t.accent || '#818cf8') : (t.text || '#e2e8f0')) : (t.dim || '#64748b'),
                            border: 'none', borderBottom: `1px solid ${(t.border || '#334155')}44`,
                            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                          }}>
                          {hasTodo ? '⚠️ ' : ''}{f.path}
                        </button>
                      )
                    })}
                  </div>
                  {/* Editor del archivo activo */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 12, fontFamily: 'monospace', color: t.muted || '#94a3b8' }}>{activePath || '(elige un archivo)'}</span>
                      <button onClick={saveFile} disabled={!editDirty}
                        style={{
                          marginLeft: 'auto', padding: '6px 12px', borderRadius: 6, fontSize: 12, fontWeight: 700,
                          cursor: editDirty ? 'pointer' : 'default',
                          background: editDirty ? '#22c55e' : (t.border || '#334155'),
                          color: editDirty ? '#000' : (t.muted || '#94a3b8'), border: 'none',
                        }}>💾 Guardar archivo</button>
                      <button onClick={rebuild} disabled={rebuilding}
                        style={{
                          padding: '6px 12px', borderRadius: 6, fontSize: 12, fontWeight: 700, cursor: 'pointer',
                          background: (t.accent || '#6366f1') + '22', color: t.accent || '#818cf8',
                          border: `1px solid ${(t.accent || '#6366f1')}55`,
                        }}>{rebuilding ? '⏳ Rehaciendo…' : '🔄 Rehacer paquete'}</button>
                    </div>
                    <textarea value={editContent}
                      onChange={e => { setEditContent(e.target.value); setEditDirty(true) }}
                      spellCheck={false}
                      style={{
                        width: '100%', minHeight: 300, maxHeight: 500, padding: 10, borderRadius: 8, boxSizing: 'border-box',
                        background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
                        color: t.text || '#e2e8f0', fontFamily: 'monospace', fontSize: 12, lineHeight: 1.5,
                        resize: 'vertical', outline: 'none', whiteSpace: 'pre', overflowX: 'auto',
                      }} />
                    {editMsg && <div style={{ fontSize: 12, color: editMsg.startsWith('⚠️') ? '#f87171' : '#22c55e' }}>{editMsg}</div>}
                    <div style={{ fontSize: 11, color: t.muted || '#94a3b8' }}>
                      Edita las líneas marcadas (busca <code># TODO py2spark</code>), guarda, y pulsa “Rehacer paquete”
                      para reempaquetar el ZIP con tus cambios{buildResult.report?.find(r => r._meta)?.full_env ? ' (incluye el ambiente completo offline)' : ''}.
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {loading && <div style={{ ...card, fontSize: 13, color: t.muted }}>Cargando…</div>}

      {manifest && (
        <>
          <div style={{ fontSize: 12, fontWeight: 700, color: t.muted || '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5, marginTop: 4 }}>
            O descarga la plantilla base (framework de ejemplo)
          </div>
          {/* Mejoras: antes -> ahora */}
          <div style={{ ...card }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: t.text || '#e2e8f0', marginBottom: 10 }}>
              ✨ Qué mejora respecto al framework actual
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {(manifest.improvements || []).map((im, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12.5, flexWrap: 'wrap' }}>
                  <span style={{
                    color: '#f87171', textDecoration: 'line-through', background: '#ef444412',
                    padding: '3px 8px', borderRadius: 6, border: '1px solid #ef444430',
                  }}>{im.from}</span>
                  <span style={{ color: t.dim || '#64748b' }}>→</span>
                  <span style={{
                    color: '#22c55e', background: '#22c55e12',
                    padding: '3px 8px', borderRadius: 6, border: '1px solid #22c55e30',
                  }}>{im.to}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'start' }}>
            {/* Árbol del paquete */}
            <div style={{ ...card, minWidth: 0 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: t.text || '#e2e8f0', marginBottom: 10 }}>
                📂 Qué incluye el paquete
              </div>
              <pre style={{
                margin: 0, padding: 12, borderRadius: 8, overflowX: 'auto',
                background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
                color: '#c4b5fd', fontFamily: 'monospace', fontSize: 12, lineHeight: 1.6,
              }}>{(manifest.tree || []).join('\n')}</pre>
            </div>

            {/* Generar / descargar */}
            <div style={{ ...card, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: t.text || '#e2e8f0' }}>
                ⬇️ Generar el paquete
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12.5, color: t.text || '#e2e8f0', cursor: 'pointer' }}>
                <input type="checkbox" checked={bankLibs} onChange={e => setBankLibs(e.target.checked)} />
                Incluir marcadores de librerías internas del banco (toolbox, lib_mkop_metrics, mex-lib*) en requirements.txt
              </label>
              <p style={{ margin: 0, fontSize: 11.5, color: t.muted || '#94a3b8' }}>
                {bankLibs
                  ? 'El requirements.txt incluirá las libs del banco comentadas, listas para descomentar y apuntar a tu Artifactory interno.'
                  : 'Solo dependencias open source (PySpark, pandas, pytest). Corre en cualquier máquina sin la red del banco.'}
              </p>
              <a href={DOWNLOAD_URL(bankLibs, extraSteps)} download
                style={{
                  display: 'inline-block', textDecoration: 'none', textAlign: 'center',
                  padding: '12px 20px', borderRadius: 8, fontSize: 14, fontWeight: 700,
                  background: t.accent || '#6366f1', color: '#fff',
                }}>
                📦 Descargar framework_mlops_v2.zip
              </a>
              <div style={{ fontSize: 11.5, color: t.muted || '#94a3b8', lineHeight: 1.6 }}>
                Después de descargar y descomprimir:
                <pre style={{
                  margin: '6px 0 0', padding: 10, borderRadius: 6,
                  background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
                  color: '#22c55e', fontFamily: 'monospace', fontSize: 11.5,
                }}>{'cd framework_mlops_v2_pkg\nbash run.sh'}</pre>
                Crea <code>.venv</code>, instala dependencias y corre las pruebas.
              </div>
            </div>
          </div>

          <div style={{ ...card, fontSize: 12, color: t.muted || '#94a3b8', borderColor: '#38bdf855' }}>
            <b style={{ color: '#38bdf8' }}>Nota honesta:</b> este paquete es una reimplementación limpia del
            andamiaje (clase base, validaciones, router, tests) — <b>no copia el código propietario del banco</b>.
            La lógica de negocio específica de cada fuente (buró, PnL, etc.) la portas tú sobre esta base, o la
            conviertes desde pandas en la sección "🧬 Framework MLOps". Las dependencias de Cloudera/Artifactory
            se resuelven en la red del banco vía <code>requirements.txt</code>.
          </div>
        </>
      )}
    </div>
  )
}

function uploadBtn(t) {
  return {
    padding: '7px 12px', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer',
    background: (t.accent || '#6366f1') + '20', color: t.accent || '#818cf8',
    border: `1px solid ${(t.accent || '#6366f1')}55`, display: 'inline-block',
  }
}
