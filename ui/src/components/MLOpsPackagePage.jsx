import { useState, useEffect, useMemo } from 'react'
import { COMPILE_URL } from '../config'
import OrdenFuentesPanel from './OrdenFuentesPanel'

// Seccion "Framework MLOps v2": genera un PAQUETE NUEVO y mejorado del framework
// (sin tocar el del banco) y lo empaqueta en un ZIP con entorno virtual (run.sh
// crea el venv + instala + prueba), ejemplos y pruebas reales.
const API_BASE = COMPILE_URL.replace(/\/compile$/, '')
const MANIFEST_URL = `${API_BASE}/mlops/package/manifest`
const BUILD_URL = `${API_BASE}/mlops/package/build`
const VENDOR_STATUS_URL = `${API_BASE}/vendor/status`
const VENDOR_PREPARE_URL = `${API_BASE}/vendor/prepare`
const VENDOR_LOG_URL = `${API_BASE}/vendor/prepare/log`
const DOWNLOAD_URL = (bank, extra) => `${API_BASE}/mlops/package/download?bank=${bank ? 1 : 0}&extra=${extra ? 1 : 0}`

export default function MLOpsPackagePage({ theme, onEmulate }) {
  const t = theme || {}
  const [manifest, setManifest] = useState(null)
  const [bankLibs, setBankLibs] = useState(true)
  const [extraSteps, setExtraSteps] = useState(false)
  const [monitoring, setMonitoring] = useState(false)
  const [separateMon, setSeparateMon] = useState(false)
  const [fullEnv, setFullEnv] = useState(false)
  // Version EXACTA de Python del servidor Linux (una wheel por libreria = lo mas ligero).
  const [pyTarget, setPyTarget] = useState('py3.8')  // py3.8 (banco) | py3.12
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
  const [verifying, setVerifying] = useState(false)
  const [verifyLog, setVerifyLog] = useState('')
  const [verifyResult, setVerifyResult] = useState(null)  // {ok_env, checks, steps}
  const [runPytest, setRunPytest] = useState(false)
  const [verifySerie, setVerifySerie] = useState('py3.8')  // target Linux a emular
  // Firma / despliegue del paquete.
  const [signing, setSigning] = useState(false)
  const [signResult, setSignResult] = useState(null)  // {manifest, verify, public_key_pem, private_key_pem}

  useEffect(() => {
    fetch(MANIFEST_URL)
      .then(r => r.json())
      .then(d => setManifest(d))
      .catch(() => setManifest(null))
      .finally(() => setLoading(false))
  }, [])

  // Cache de vendor (.venv/bnx_vendor_cache): estado por version y progreso de "Bajar/generar".
  const [vendorStatus, setVendorStatus] = useState(null)
  const [vendorJob, setVendorJob] = useState(null)   // {running, returncode, log}
  const [vendorErr, setVendorErr] = useState('')
  const loadVendorStatus = () =>
    fetch(VENDOR_STATUS_URL).then(r => r.json()).then(d => { if (d.ok) setVendorStatus(d) }).catch(() => {})
  useEffect(() => { loadVendorStatus() }, [])
  useEffect(() => {
    if (!vendorJob?.running) return undefined
    const id = setInterval(() => {
      fetch(VENDOR_LOG_URL).then(r => r.json()).then(d => {
        if (!d.ok) return
        setVendorJob(d.job)
        if (!d.job.running) loadVendorStatus()
      }).catch(() => {})
    }, 2000)
    return () => clearInterval(id)
  }, [vendorJob?.running])
  const startVendorPrepare = async (ver) => {
    setVendorErr('')
    try {
      const res = await fetch(VENDOR_PREPARE_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ versions: [ver] }),
      })
      const d = await res.json()
      if (!d.ok && res.status !== 409) { setVendorErr(d.error || 'No se pudo iniciar'); return }
      setVendorJob({ ...(d.job || {}), running: true, log: '' })
    } catch (e) { setVendorErr(String(e)) }
  }
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

  // ¿Este archivo es un JOB (va al REGISTRY) o un MÓDULO DE APOYO (bank_src/, copia exacta)?
  // Lo que el usuario marcó se recuerda (localStorage) para que no tenga que volver a
  // editar el router en cada paquete. Por defecto: job si usa pandas o define run().
  const [jobSel, setJobSel] = useState(() => {
    try { return JSON.parse(localStorage.getItem('bnx_mlops_registry') || '{}') } catch { return {} }
  })
  // Modulos que OTRO archivo subido importa como 'paquete.modulo' (toolbox.kernel,
  // utils.emails_full, ...): son de apoyo aunque usen pandas (read.py, data_pull.py).
  const importadosComoModulo = useMemo(() => {
    const s = new Set()
    const re = /^\s*(?:from\s+([A-Za-z_]\w*)\.([A-Za-z_]\w*)[\w.]*\s+import\b|import\s+([A-Za-z_]\w*)\.([A-Za-z_]\w*))/gm
    ;[...files, ...(pasted.trim() ? [{ code: pasted }] : [])].forEach(f => {
      for (const m of (f.code || '').matchAll(re)) s.add((m[2] || m[4]).toLowerCase())
    })
    return s
  }, [files, pasted])
  const esJob = (f) => {
    if (f.name in jobSel) return !!jobSel[f.name]
    const stem = f.name.replace(/\.(py|txt)$/i, '').toLowerCase()
    if (importadosComoModulo.has(stem)) return false
    const c = f.code || ''
    return /^\s*(import\s+pandas\b|from\s+pandas[\w.]*\s+import)/m.test(c) || /^def\s+run\s*\(/m.test(c)
  }
  const marcarJob = (name, v) => setJobSel(prev => {
    const n = { ...prev, [name]: v }
    try { localStorage.setItem('bnx_mlops_registry', JSON.stringify(n)) } catch { /* sin storage */ }
    return n
  })

  const buildMine = async () => {
    const sources = sourcesToSend()
    if (!sources.length) { setBuildError('Pega código o sube al menos un archivo .py.'); return }
    // Solo se manda 'registry' si hay algún módulo de apoyo (si no, todos son jobs: como antes).
    const jobs = sources.filter(s => esJob(s)).map(s => s.name)
    const registry = jobs.length === sources.length ? null : jobs
    setBuilding(true); setBuildError(''); setBuildResult(null); setSignResult(null)
    try {
      const res = await fetch(BUILD_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sources, include_bank_libs: bankLibs, optimize: true, extra_steps: extraSteps,
          include_monitoring: monitoring, separate_monitoring: monitoring && separateMon,
          full_env: fullEnv, py_target: pyTarget, registry,
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

  const signPackage = async () => {
    if (!buildResult?.edit_token) return
    setSigning(true); setEditMsg(''); setSignResult(null)
    try {
      const res = await fetch(`${API_BASE}/mlops/package/sign`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: buildResult.edit_token }),
      })
      const data = await res.json()
      if (!res.ok || data.error) { setEditMsg('⚠️ ' + (data.error || 'no se pudo firmar')); return }
      setSignResult(data)
      // Reflejar que ahora el paquete trae deploy/ (reload de archivos editables).
      loadEditFiles(buildResult.edit_token)
    } catch (e) { setEditMsg('⚠️ ' + e.message) }
    finally { setSigning(false) }
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
      if (!res.ok || data.error) { setEditMsg('⚠️ ' + (data.error || 'no se pudo rehacer')); return null }
      setBuildResult(r => ({ ...r, size: data.size, download_url: data.download_url, filename: data.filename,
                             offline_faltan: data.offline_faltan, vendor_mb: data.vendor_mb }))
      setEditMsg('✅ Paquete rehecho con tus ediciones — listo para descargar.')
      return data
    } catch (e) { setEditMsg('⚠️ ' + e.message); return null }
    finally { setRebuilding(false) }
  }

  // Rehacer el ZIP (con orden.json y ediciones) y DESCARGARLO en un paso.
  const rebuildYDescargar = async () => {
    const data = await rebuild()
    if (!data?.download_url) return false
    const a = document.createElement('a')
    a.href = `${API_BASE}${data.download_url}`
    a.download = data.filename || 'framework_mlops_v2.zip'
    document.body.appendChild(a); a.click(); a.remove()
    return true
  }

  // Monta el paquete en un venv real y lo PRUEBA (check_env.py + pytest opcional),
  // mostrando la salida estilo terminal. Responde la pregunta "¿faltan librerias?".
  const verify = async () => {
    if (!buildResult?.edit_token) return
    setVerifying(true); setVerifyResult(null)
    setVerifyLog(runPytest
      ? 'Montando venv local y corriendo pruebas… (fiel solo si este host es el destino)'
      : `Verificando contra el servidor LINUX del banco (${verifySerie})… resolviendo dependencias con pip, sin instalar.`)
    try {
      const res = await fetch(`${API_BASE}/mlops/package/verify`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: buildResult.edit_token, run_pytest: runPytest,
                               emulate_linux: !runPytest, serie: verifySerie }),
      })
      const data = await res.json()
      if (!res.ok || data.error) {
        setVerifyLog('⚠️ ' + (data.error || 'no se pudo verificar'))
        return
      }
      setVerifyLog(data.log || '(sin salida)')
      setVerifyResult({ ok_env: data.ok_env, checks: data.checks, steps: data.steps })
    } catch (e) { setVerifyLog('⚠️ ' + e.message) }
    finally { setVerifying(false) }
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
          (como Data Sintética): <code>setup.sh</code> crea el venv e instala todo; <code>run.sh</code> solo corre el modelo.
        </p>
      </div>

      {/* Instrucciones de ejecución (cómo correr el paquete descargado) */}
      <RunInstructions theme={t} />

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
                      <label title="Marcado = job (entra al REGISTRY del router). Desmarcado = módulo de apoyo (utils, settings, toolbox…): se copia EXACTO a bank_src/ sin convertir. Se recuerda para la próxima vez."
                        style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4, color: esJob(f) ? '#22c55e' : (t.muted || '#94a3b8'), whiteSpace: 'nowrap', cursor: 'pointer' }}>
                        <input type="checkbox" checked={esJob(f)} onChange={e => marcarJob(f.name, e.target.checked)} />
                        {esJob(f) ? 'job' : 'apoyo'}
                      </label>
                      <span style={{ color: t.dim || '#64748b' }}>{(f.code.length / 1024).toFixed(1)} KB</span>
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
            <span>Incluir <b>ambiente completo</b> (también PySpark offline en <code>vendor/</code>). Sin marcar = <b>ligero</b>: todas las librerías offline menos PySpark</span>
          </label>
          {(
            <div style={{ marginLeft: 24, display: 'flex', flexDirection: 'column', gap: 6 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: t.text || '#e2e8f0' }}>
                Versión de Python del destino:
                <select value={pyTarget} onChange={e => setPyTarget(e.target.value)}
                  style={{
                    padding: '5px 8px', borderRadius: 6, fontSize: 12,
                    background: t.codeBg || '#081220', color: t.text || '#e2e8f0',
                    border: `1px solid ${t.border || '#334155'}`, outline: 'none', cursor: 'pointer',
                  }}>
                  <option value="py3.8">Linux · Python 3.8 (servidor del banco){fullEnv ? ' — ~340 MB (con PySpark 3.5)' : ' — ~35 MB'}</option>
                  <option value="py3.12">Linux · Python 3.12{fullEnv ? ' — ~450 MB (con PySpark 4.0)' : ' — ~36 MB'}</option>
                </select>
              </label>
              <div style={{ fontSize: 11, color: t.muted || '#94a3b8' }}>
                {fullEnv
                  ? 'Completo: TODO offline, incluido PySpark. Elige la versión de los nodos del banco para bajar el tamaño.'
                  : 'Ligero: TODAS las librerías offline (pandas, numpy, pytest, cytoolz, las del banco…) MENOS PySpark: en el servidor se usa el Spark del cluster (BNX_SPARK=cluster bash run.sh).'}
                {' '}Usa tu Python y Java del sistema; esos no se empaquetan.
              </div>
              {(() => {
                const ver = pyTarget.replace('py', '')
                const est = vendorStatus?.versiones?.[ver]
                const corriendo = vendorJob?.running
                if (!corriendo && (!est || est.ok) && !vendorJob?.log) return null
                return (
                  <div style={{ fontSize: 11.5, color: '#fcd34d', padding: 8, borderRadius: 6,
                                background: '#f59e0b15', border: '1px solid #f59e0b55' }}>
                    {est && !est.ok && (
                      <div>
                        ⚠ Falta el cache de vendor para Python {ver} ({est.falta.join(', ')}). Sin él el paquete
                        no podrá ser offline completo{fullEnv ? ' y PySpark NO se incluirá' : ''}. Se guarda en{' '}
                        <code>{vendorStatus.cache_dir}</code>.
                      </div>
                    )}
                    <button onClick={() => startVendorPrepare(ver)} disabled={corriendo}
                      style={{ marginTop: 6, padding: '6px 12px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                               cursor: corriendo ? 'wait' : 'pointer', background: t.accent || '#6366f1',
                               color: '#fff', border: 'none' }}>
                      {corriendo ? '⏳ Bajando/generando…' : `⬇ Bajar/generar cache (Python ${ver})`}
                    </button>
                    {vendorErr && <div style={{ color: '#fca5a5' }}>{vendorErr}</div>}
                    {vendorJob?.log && (
                      <pre style={{ marginTop: 6, maxHeight: 160, overflow: 'auto', fontSize: 10.5,
                                    color: t.muted || '#94a3b8', whiteSpace: 'pre-wrap' }}>{vendorJob.log}</pre>
                    )}
                    {vendorJob && !vendorJob.running && vendorJob.started && (
                      <div>{vendorJob.returncode === 0
                        ? '✅ Listo: ya puedes generar de nuevo.'
                        : 'Terminó con avisos (revisa el log). Las mex-lib del banco no se bajan de PyPI: impórtalas por ZIP o en “Librerías del banco”.'}</div>
                    )}
                  </div>
                )
              })()}
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
                      {meta?.full_env && !meta?.vendor_missing && (
                        <div style={{ fontSize: 11.5, color: '#2dd4bf', marginBottom: 2 }}>
                          📦 Ambiente completo incluido: PySpark offline en <code>vendor/</code>
                          {(meta.vendor_series || []).length ? ` (${meta.vendor_series.join(', ')})` : ''}. Monta con <code>bash setup.sh</code>.
                        </div>
                      )}
                      {Object.keys(meta?.modulos_faltantes || {}).length > 0 && (
                        <div style={{ fontSize: 11.5, color: '#fca5a5', marginBottom: 2, padding: 8, borderRadius: 6,
                                      border: '1px solid #ef444455' }}>
                          ⛔ Tu código importa módulos de paquetes del banco que <b>no vienen en el paquete</b> (ni subidos ni en el
                          caché de este servidor). Los jobs fallarán con <code>No module named …</code>. Súbelos junto con tus
                          archivos (se acomodan solos en su paquete) o cárgalos en <b>📚 Librerías del banco</b>:
                          {Object.entries(meta.modulos_faltantes).map(([p, ms]) =>
                            <div key={p}>· <code>{p}</code>: {ms.map(m => `${m}.py`).join(', ')}</div>)}
                        </div>
                      )}
                      {meta && (
                        <div style={{ fontSize: 11.5, color: t.muted || '#94a3b8', marginBottom: 2 }}>
                          📚 Librerías offline en <code>vendor/</code>: {meta.vendor_mb ?? '?'} MB
                          {meta.full_env ? ' (con PySpark)' : ' (ligero: sin PySpark, usa el Spark del cluster)'}
                        </div>
                      )}
                      {(() => {
                        const f = buildResult.offline_faltan || meta?.offline_faltan || {}
                        const filas = Object.entries(f).flatMap(([s, vs]) => Object.entries(vs).map(([v, e]) => ({ s, v, e })))
                        if (!filas.length) return null
                        return (
                          <div style={{ fontSize: 11.5, color: '#f59e0b', marginBottom: 2, padding: 8, borderRadius: 6,
                                        border: '1px solid #f59e0b55' }}>
                            ⚠ En estas versiones de Python NO se podrá instalar todo offline (faltan wheels en el cache del
                            generador); ahí setup.sh intentará bajar lo que falte por internet. Si tu servidor usa otra versión, no te afecta:
                            {filas.map(x => <div key={x.s + x.v}>· Python {x.v} ({x.s}): {String(x.e).slice(0, 120)}</div>)}
                          </div>
                        )
                      })()}
                      {meta?.full_env && meta?.vendor_missing && (
                        <div style={{
                          fontSize: 11.5, color: '#fca5a5', marginBottom: 2, padding: 8, borderRadius: 6,
                          background: '#ef444415', border: '1px solid #ef444455',
                        }}>
                          ⚠️ <b>Ambiente completo pedido, pero PySpark NO se incluyó.</b> Este servidor no tiene
                          el cache de PySpark (vendor vacío) y no pudo descargarlo (sin internet). El ZIP trae el
                          código pero <b>no el PySpark offline</b>. Solución: corre{' '}
                          <code>.venv/bin/python preparar_vendor.py --python 3.X</code> o usa el botón
                          “Bajar/generar cache” de arriba; o importa un ZIP hecho en otra máquina con{' '}
                          <code>exportar_vendor.py --python 3.X</code> (<code>preparar_vendor.py --zip &lt;zip&gt;</code>).
                          Luego vuelve a generar.
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
                      {r.ok && r.role === 'apoyo'
                        ? <span style={{ color: '#a78bfa' }}> · módulo de apoyo: copia exacta (no está en el REGISTRY){r.nota ? ` — ${r.nota}` : ''}</span>
                        : r.ok && r.verbatim
                        ? <span style={{ color: '#38bdf8' }}> · PySpark / Python sin pandas: copiado completo, sin conversión</span>
                        : r.ok
                        ? ((r.todos || []).length
                          ? <span style={{ color: '#f59e0b' }}> · {r.todos.length} línea(s) a revisar</span>
                          : <span style={{ color: '#22c55e' }}> · conversión limpia</span>)
                        : <span style={{ color: '#f87171' }}> · {r.reason}</span>}
                      {r.aviso && <div style={{ marginLeft: 16, color: '#f59e0b' }}>⚠ {r.aviso}</div>}
                      {r.job_kernel && <div style={{ marginLeft: 16, color: '#f59e0b' }}>
                        ⚠ Es un job del framework del banco (<code>def run(kernel)</code>): el paquete lo envuelve como aggregate y
                        <b> no llama a su run(kernel)</b>. Para ejecutarlo hace falta el runner con el Kernel de toolbox.</div>}
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

            {/* FIRMA Y DESPLIEGUE: gobierno del paquete PySpark */}
            <div style={{ marginTop: 14, borderTop: `1px solid ${t.border || '#334155'}`, paddingTop: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0' }}>🔐 Firma y despliegue</span>
                <button onClick={signPackage} disabled={signing}
                  title="Firma el PySpark (SHA-256 + Ed25519) y verifica si es desplegable"
                  style={{
                    padding: '7px 14px', borderRadius: 8, fontSize: 12.5, fontWeight: 700, cursor: signing ? 'wait' : 'pointer',
                    background: '#a855f722', color: '#c084fc', border: '1px solid #a855f755',
                  }}>{signing ? '⏳ Firmando…' : '🔐 Firmar y verificar despliegue'}</button>
                <span style={{ fontSize: 11.5, color: t.muted || '#94a3b8' }}>
                  Firma el código PySpark generado y comprueba integridad (hash) + autenticidad (firma).
                </span>
              </div>

              {signResult && (
                <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {/* Veredicto de despliegue */}
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
                    padding: '10px 12px', borderRadius: 8,
                    background: (signResult.verify?.deployable ? '#22c55e' : '#ef4444') + '12',
                    border: `1px solid ${(signResult.verify?.deployable ? '#22c55e' : '#ef4444')}44`,
                  }}>
                    <span style={{
                      fontSize: 13, fontWeight: 800,
                      color: signResult.verify?.deployable ? '#22c55e' : '#ef4444',
                    }}>
                      {signResult.verify?.deployable ? '✅ DESPLEGABLE' : '⛔ NO DESPLEGABLE'}
                    </span>
                    <span style={{ fontSize: 12, color: t.text || '#e2e8f0' }}>
                      Firma: <b style={{ color: signResult.verify?.signature === 'VALID' ? '#22c55e' : '#ef4444' }}>{signResult.verify?.signature}</b>
                      {'  ·  '}Hashes: <b style={{ color: signResult.verify?.hashes === 'VALID' ? '#22c55e' : '#ef4444' }}>{signResult.verify?.hashes}</b>
                      {'  ·  '}{(signResult.signed_files || []).length} archivo(s) .py firmados
                    </span>
                  </div>

                  <div style={{ fontSize: 11.5, color: t.muted || '#94a3b8' }}>
                    El manifiesto firmado y la clave pública quedan en <code>deploy/</code> del paquete (pulsa “Rehacer paquete” para incluirlos en el ZIP).
                    Algoritmos: SHA-256 (integridad) + Ed25519 (autenticidad).
                  </div>

                  {/* Clave privada: se muestra UNA vez, para guardar */}
                  {signResult.private_key_pem && (
                    <details>
                      <summary style={{ fontSize: 11.5, color: '#fbbf24', cursor: 'pointer' }}>
                        🔑 Clave privada de firma (guárdala en tu gestor de secretos — se muestra una sola vez)
                      </summary>
                      <textarea readOnly value={signResult.private_key_pem}
                        onFocus={e => e.target.select()}
                        style={{
                          width: '100%', minHeight: 110, marginTop: 6, padding: 8, borderRadius: 6, boxSizing: 'border-box',
                          background: t.codeBg || '#081220', border: '1px solid #f59e0b55',
                          color: '#fbbf24', fontFamily: 'monospace', fontSize: 10.5, outline: 'none',
                        }} />
                      <div style={{ fontSize: 10.5, color: '#f87171', marginTop: 4 }}>
                        ⚠️ No se guarda en el servidor ni en el ZIP. Si la pierdes, vuelve a firmar (genera nueva).
                      </div>
                    </details>
                  )}
                </div>
              )}
            </div>

            {/* PROBAR ENTORNO: verifica contra el servidor LINUX del banco */}
            <div style={{ marginTop: 14, borderTop: `1px solid ${t.border || '#334155'}`, paddingTop: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0' }}>🧪 Probar entorno (emula Linux del banco)</span>
                <button onClick={verify} disabled={verifying}
                  title="Verifica que TODAS las dependencias resuelvan para el servidor Linux del banco (sin depender de la plataforma del portal)"
                  style={{
                    padding: '7px 14px', borderRadius: 8, fontSize: 12.5, fontWeight: 700, cursor: verifying ? 'wait' : 'pointer',
                    background: '#22c55e22', color: '#4ade80', border: '1px solid #22c55e55',
                  }}>{verifying ? '⏳ Verificando…' : '🧪 Probar y comprobar librerías'}</button>
                <label style={{ fontSize: 11.5, color: t.muted || '#94a3b8', display: 'flex', alignItems: 'center', gap: 6 }}>
                  Target Linux:
                  <select value={verifySerie} onChange={e => setVerifySerie(e.target.value)} disabled={runPytest}
                    style={{ padding: '4px 8px', borderRadius: 6, fontSize: 11.5, background: t.codeBg || '#081220',
                             border: `1px solid ${t.border || '#334155'}`, color: t.text || '#e2e8f0' }}>
                    <option value="py3.8">Linux · Python 3.8 (cp38)</option>
                    <option value="py3.12">Linux · Python 3.12 (cp312)</option>
                  </select>
                </label>
                <label style={{ fontSize: 11.5, color: t.muted || '#94a3b8', display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={runPytest} onChange={e => setRunPytest(e.target.checked)} />
                  Montar venv local + pytest (este host)
                </label>
              </div>
              <div style={{ fontSize: 11.5, color: t.muted || '#94a3b8', marginTop: 6 }}>
                Por defecto <b>emula el servidor Linux del banco</b>: resuelve todas las dependencias (con pip,
                sin instalar) para el target elegido. Así la verificación es fiel aunque el portal corra en Mac/Windows.
                Marca "venv local + pytest" solo si este equipo es el destino.
              </div>

              {verifyResult && (
                <div style={{ marginTop: 10, display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
                  <span style={{
                    fontSize: 12.5, fontWeight: 700, padding: '4px 10px', borderRadius: 6,
                    background: verifyResult.ok_env ? '#22c55e22' : '#f8717122',
                    color: verifyResult.ok_env ? '#4ade80' : '#f87171',
                    border: `1px solid ${verifyResult.ok_env ? '#22c55e55' : '#f8717155'}`,
                  }}>
                    {verifyResult.ok_env ? '✅ Todo resuelve para el servidor Linux del banco'
                      : `⛔ Faltan ${(verifyResult.checks?.missing || []).length} librería(s) para Linux`}
                  </span>
                  {(verifyResult.checks?.missing || []).length > 0 && (
                    <span style={{ fontSize: 12, color: '#f87171' }}>
                      Faltan: {verifyResult.checks.missing.join(', ')}
                    </span>
                  )}
                </div>
              )}

              {verifyLog && (
                <pre style={{
                  marginTop: 10, padding: 12, borderRadius: 8, maxHeight: 360, overflow: 'auto',
                  background: '#0a0f1a', border: `1px solid ${t.border || '#334155'}`,
                  color: '#9ae6b4', fontFamily: 'monospace', fontSize: 11.5, lineHeight: 1.5,
                  whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                }}>{verifyLog}</pre>
              )}
            </div>

            {/* ORDEN: quien va primero entre las fuentes (orden.json del paquete) */}
            {buildResult?.edit_token && (
              <OrdenFuentesPanel token={buildResult.edit_token} theme={t} apiBase={API_BASE}
                onSaved={() => loadEditFiles(buildResult.edit_token)}
                onDescargar={rebuildYDescargar} descargando={rebuilding}
                completo={!!buildResult.report?.find(r => r._meta)?.full_env} />
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
                }}>{'cd framework_mlops_v2_pkg\nbash setup.sh   # una vez\nbash run.sh     # corre el modelo'}</pre>
                <code>setup.sh</code> crea <code>.venv</code> e instala dependencias; <code>run.sh</code> solo ejecuta <code>main.py</code>.
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

// Instrucciones de ejecución del paquete descargado (también en el README del ZIP).
function RunInstructions({ theme }) {
  const t = theme || {}
  const [open, setOpen] = useState(true)
  const card = {
    background: t.card || '#0f172a', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 16,
  }
  const pre = {
    margin: '6px 0 0', padding: 10, borderRadius: 8, overflowX: 'auto',
    background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
    color: '#22c55e', fontFamily: 'monospace', fontSize: 12, lineHeight: 1.6,
  }
  const step = { fontSize: 12.5, color: t.text || '#e2e8f0', marginTop: 10, fontWeight: 700 }
  return (
    <div style={{ ...card, borderColor: '#14b8a655' }}>
      <div onClick={() => setOpen(v => !v)}
        style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
        <span style={{ fontSize: 14, fontWeight: 800, color: '#2dd4bf' }}>▶️ Cómo correr el paquete (instrucciones)</span>
        <span style={{ marginLeft: 'auto', fontSize: 12, color: t.muted || '#94a3b8' }}>{open ? '▲' : '▼'}</span>
      </div>
      {open && (
        <div style={{ marginTop: 6 }}>
          <p style={{ margin: 0, fontSize: 12, color: t.muted || '#94a3b8' }}>
            Tras descargar y descomprimir el ZIP. <b>Requisitos</b>: Python 3.8+ y Java (JDK) para Spark
            (ninguno se empaqueta; deben estar en la máquina). Estas mismas instrucciones van en el <code>README.md</code> del paquete.
          </p>

          <div style={step}>1) Montar el entorno (una sola vez)</div>
          <pre style={pre}>{`cd framework_mlops_v2_pkg
bash setup.sh       # con vendor/: PySpark OFFLINE; sin vendor/: por internet`}</pre>

          <div style={step}>2) Correr el framework (entry point: main.py)</div>
          <pre style={pre}>{`bash run.sh                      # modo DEMO (datos sintéticos, sin configurar)
bash run.sh --config cfg.json              # todas las fuentes (cada una job independiente; PIVOTE corre 1º)
bash run.sh --config cfg.json --source X   # UNA sola fuente (job aislado p/ Airflow/cron)`}</pre>
          <p style={{ margin: '6px 0 0', fontSize: 11.5, color: t.muted || '#94a3b8' }}>
            Si definiste el <b>orden de las fuentes</b>, va en <code>orden.json</code>: cada fuente con dependencias corre
            después de ellas y se salta si alguna falla. Todas comparten la <b>SparkSession</b>. El proceso <b>pivote</b> corre primero (márcalo con
            <code>{' "pivot": true'}</code> en el <code>cfg.json</code> o nómbralo <code>pivote</code>).
          </p>

          <div style={step}>3) Settings del banco (pivot.json / datapull.json)</div>
          <pre style={pre}>{`# ver los QUERY sin ejecutar (recomendado la 1a vez)
bash run.sh --config pivot.json --env uat --cohort 202501 --dry-run
# bajar las tablas de tables_info a parquet
bash run.sh --config pivot.json --env uat --cohort 202501 --extract-only
# salida en HDFS = base_path + working_path  (en el JSON o por CLI)
#   "base_path": "/data/<usuario>/managed/hive/<usuario>_managed/"
bash run.sh --config pivot.json --env uat --cohort 202501 --base-path /data/.../managed/ --extract-only`}</pre>
          <div style={step}>4) Metastore del clúster (si sale "la base no existe")</div>
          <pre style={pre}>{`# A) Spark del clúster (recomendado)
BNX_SPARK=cluster bash run.sh --config pivot.json --env uat --cohort 202501 --extract-only
# B) PySpark del venv apuntando a la config del clúster
export SPARK_CONF_DIR=/etc/spark/conf   # carpeta con hive-site.xml`}</pre>
          <p style={{ margin: '6px 0 0', fontSize: 11.5, color: '#fbbf24' }}>
            ⚠️ Si la tabla sí se consulta en Hue/beeline pero aquí "no existe", el PySpark del venv no está
            conectado al metastore del clúster. Todo el detalle viene en <code>NOTAS_EJECUCION.md</code> dentro del ZIP.
          </p>

          <p style={{ margin: '10px 0 0', fontSize: 11.5, color: t.muted || '#94a3b8' }}>
            <code>main.py</code> orquesta el pipeline, reporta las <b>optimizaciones de Spark</b> aplicadas
            (cache / broadcast / coalesce) y marca las fuentes con un <code># TODO py2spark</code> pendiente.
            El modo demo corre sin datos reales; <code>bash run.sh</code> lo ejecuta.
          </p>
        </div>
      )}
    </div>
  )
}
