import { useState, useEffect } from 'react'
import { COMPILE_URL } from '../config'

// Pagina "Librerias del banco": gestiona el cache de librerias internas del
// banco (mex-lib*, toolbox/utils/bnmxverse, deps pinneadas como pandas 1.3.1)
// que se empaquetan OFFLINE en los paquetes del Framework MLOps v2.
// Funciona similar a Grafos: lista lo que hay, importa desde una ruta del disco,
// elimina y verifica que una mex-lib importe limpio.
const API_BASE = COMPILE_URL.replace(/\/compile$/, '')
const BANKLIBS_URL = `${API_BASE}/banklibs`

const fmtSize = (n) => {
  if (n == null) return ''
  if (n < 1024) return n + ' B'
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB'
  return (n / 1024 / 1024).toFixed(1) + ' MB'
}

const STATUS_STYLE = {
  verificada: { bg: '#22c55e22', fg: '#4ade80', br: '#22c55e55', icon: '✅' },
  incompleta: { bg: '#f8717122', fg: '#f87171', br: '#f8717155', icon: '⛔' },
  desconocida: { bg: '#f59e0b22', fg: '#fbbf24', br: '#f59e0b55', icon: '❔' },
  incluida: { bg: '#6366f122', fg: '#a5b4fc', br: '#6366f155', icon: '📦' },
}

export default function BankLibsPage({ theme }) {
  const t = theme || {}
  const [inv, setInv] = useState({ wheels: [], pkgcode: [] })
  const [loading, setLoading] = useState(true)
  const [importPath, setImportPath] = useState('')
  const [importing, setImporting] = useState(false)
  const [msg, setMsg] = useState('')
  const [verifyName, setVerifyName] = useState('')
  const [verifyLog, setVerifyLog] = useState('')
  const [verifyOk, setVerifyOk] = useState(null)
  const [vendorStatus, setVendorStatus] = useState(null)   // {py38-311:{...}, py312plus:{...}}
  const [exporting, setExporting] = useState(false)
  const [exportSerie, setExportSerie] = useState('py38-311')
  const [exportMsg, setExportMsg] = useState('')

  const card = { background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`, borderRadius: 10, padding: 16 }

  useEffect(() => { refresh() }, [])

  const post = async (payload) => {
    const res = await fetch(BANKLIBS_URL, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    return res.json()
  }

  const refresh = async () => {
    setLoading(true)
    try {
      const data = await post({ action: 'list' })
      if (data.wheels || data.pkgcode) setInv({ wheels: data.wheels || [], pkgcode: data.pkgcode || [] })
      const vs = await post({ action: 'vendor_status' })
      if (vs.series) setVendorStatus(vs.series)
    } catch (e) { setMsg('⚠️ ' + e.message) }
    finally { setLoading(false) }
  }

  const exportVendor = async () => {
    setExporting(true); setExportMsg('Empaquetando el vendor (PySpark + librerías)… puede tardar, son cientos de MB.')
    try {
      const data = await post({ action: 'export_vendor', serie: exportSerie })
      if (!data.ok || data.error) { setExportMsg('⚠️ ' + (data.error || 'no se pudo exportar')); return }
      setExportMsg(`✅ Listo: ${data.filename} (${(data.size / 1024 / 1024).toFixed(0)} MB). Descargando…`)
      // Disparar la descarga nativa del navegador (streaming desde disco).
      const a = document.createElement('a')
      a.href = `${API_BASE}${data.download_url}`
      a.download = data.filename
      document.body.appendChild(a); a.click(); a.remove()
    } catch (e) { setExportMsg('⚠️ ' + e.message) }
    finally { setExporting(false) }
  }

  const doImport = async () => {
    if (!importPath.trim()) return
    setImporting(true); setMsg('')
    try {
      const data = await post({ action: 'import_path', path: importPath.trim() })
      if (data.error) { setMsg('⚠️ ' + data.error); return }
      if (data.wheels || data.pkgcode) setInv({ wheels: data.wheels || [], pkgcode: data.pkgcode || [] })
      const nc = (data.copiados || []).length
      setMsg(nc > 0 ? `✅ Importado: ${nc} archivo(s) nuevo(s)/actualizado(s).` : 'ℹ️ Nada nuevo (todo ya estaba igual).')
    } catch (e) { setMsg('⚠️ ' + e.message) }
    finally { setImporting(false) }
  }

  const doDelete = async (name, kind) => {
    const label = kind === 'pkgcode' ? `el módulo "${name}"` : `"${name}"`
    if (!confirm(`¿Eliminar ${label} del cache de librerías del banco?`)) return
    setMsg('')
    try {
      const data = await post({ action: 'delete', name, kind })
      if (data.wheels || data.pkgcode) setInv({ wheels: data.wheels || [], pkgcode: data.pkgcode || [] })
      setMsg(data.deleted ? `🗑️ Eliminado: ${data.deleted}` : '⚠️ No se encontró para eliminar.')
    } catch (e) { setMsg('⚠️ ' + e.message) }
  }

  const doVerify = async (name) => {
    setVerifyName(name); setVerifyOk(null)
    setVerifyLog(`Montando un venv de prueba e instalando ${name}…\n(Esto tarda; instala pandas/pyspark de prueba.)`)
    try {
      const data = await post({ action: 'verify', name })
      if (data.error) { setVerifyLog('⚠️ ' + data.error); return }
      setVerifyOk(data.ok)
      setVerifyLog(data.log || '(sin salida)')
    } catch (e) { setVerifyLog('⚠️ ' + e.message) }
  }

  const StatusBadge = ({ status, reason }) => {
    const s = STATUS_STYLE[status] || STATUS_STYLE.desconocida
    return (
      <span title={reason || ''} style={{
        fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 6,
        background: s.bg, color: s.fg, border: `1px solid ${s.br}`, whiteSpace: 'nowrap',
      }}>{s.icon} {status}</span>
    )
  }

  const mexLibs = inv.wheels.filter(w => w.kind === 'mex-lib')
  const deps = inv.wheels.filter(w => w.kind !== 'mex-lib')

  return (
    <div style={{ padding: 32, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: t.text || '#e2e8f0', margin: 0 }}>📚 Librerías del banco</h2>
        <p style={{ fontSize: 13, color: t.dim || '#64748b', marginTop: 4, maxWidth: 820 }}>
          Gestiona las librerías internas del banco que se empaquetan <b>offline</b> en los paquetes del
          Framework MLOps v2 (sin depender del Artifactory). Importa versiones nuevas desde una ruta del disco,
          elimina las viejas y verifica que una <code>mex-lib</code> importe limpio antes de confiar en ella.
        </p>
      </div>

      {/* Importar desde ruta */}
      <div style={{ ...card, borderLeft: '3px solid #22c55e' }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0', marginBottom: 8 }}>
          📥 Importar librerías desde una ruta del disco
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <input value={importPath} onChange={e => setImportPath(e.target.value)}
            placeholder="/Users/.../170589.DAA.MLOps_RPS_2026-0001-refactor_v1"
            onKeyDown={e => e.key === 'Enter' && doImport()}
            style={{
              flex: 1, minWidth: 320, padding: '8px 10px', borderRadius: 6, fontSize: 12.5,
              background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
              color: t.text || '#e2e8f0', outline: 'none', fontFamily: 'monospace',
            }} />
          <button onClick={doImport} disabled={importing || !importPath.trim()}
            style={{
              padding: '8px 16px', borderRadius: 8, fontSize: 12.5, fontWeight: 700,
              cursor: importing ? 'wait' : 'pointer', background: '#22c55e', color: '#000', border: 'none',
            }}>{importing ? '⏳ Importando…' : '📥 Importar'}</button>
          <button onClick={refresh} title="Recargar el inventario"
            style={{ padding: '8px 12px', borderRadius: 8, fontSize: 12.5, cursor: 'pointer', background: '#6366f122', color: '#a5b4fc', border: '1px solid #6366f155' }}>🔄</button>
        </div>
        <div style={{ fontSize: 11.5, color: t.dim || '#64748b', marginTop: 8 }}>
          Copia del directorio: los <code>*.tar.gz</code>/<code>*.whl</code> (solo wheels de Linux; el servidor del banco es Linux)
          y los módulos <code>toolbox</code>/<code>utils</code>/<code>bnmxverse</code> (estén en la raíz o en <code>bin/</code>).
        </div>
        {msg && <div style={{ fontSize: 12.5, marginTop: 8, color: msg.startsWith('⚠️') ? '#f87171' : (msg.startsWith('✅') || msg.startsWith('🗑️') ? '#4ade80' : '#a5b4fc') }}>{msg}</div>}
      </div>

      {/* Exportar el vendor (entorno virtual offline) para otra maquina */}
      <div style={{ ...card, borderLeft: '3px solid #a855f7' }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0', marginBottom: 6 }}>
          ⬇️ Descargar el entorno (PySpark + librerías) para un servidor sin internet
        </div>
        <div style={{ fontSize: 11.5, color: t.dim || '#64748b', marginBottom: 10 }}>
          Genera un ZIP con <b>PySpark offline</b> + las librerías del banco, para montar el entorno virtual en
          una máquina aislada. Descárgalo aquí, cópialo al servidor y corre
          <code> python importar_vendor.py bnx_vendor_&lt;serie&gt;.zip</code> (el script va incluido en el ZIP).
        </div>

        {/* Estado del cache por serie */}
        {vendorStatus && (
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
            {Object.entries(vendorStatus).map(([serie, v]) => (
              <span key={serie} style={{
                fontSize: 11.5, padding: '3px 10px', borderRadius: 6,
                background: v.has_pyspark ? '#22c55e18' : '#f59e0b18',
                color: v.has_pyspark ? '#4ade80' : '#fbbf24',
                border: `1px solid ${v.has_pyspark ? '#22c55e44' : '#f59e0b44'}`,
              }}>
                {v.has_pyspark ? '✅' : '⚠️'} {serie}: {v.has_pyspark ? `PySpark listo (${(v.bytes / 1024 / 1024).toFixed(0)} MB)` : 'sin PySpark en cache'}
              </span>
            ))}
          </div>
        )}

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <label style={{ fontSize: 12, color: t.muted || '#94a3b8' }}>Serie de Python del destino:</label>
          <select value={exportSerie} onChange={e => setExportSerie(e.target.value)}
            style={{
              padding: '7px 10px', borderRadius: 6, fontSize: 12.5,
              background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
              color: t.text || '#e2e8f0', outline: 'none',
            }}>
            <option value="py38-311">Python 3.8–3.11 (PySpark 3.5) — ~550 MB</option>
            <option value="py312plus">Python 3.12+ (PySpark 4.0) — ~670 MB</option>
            <option value="all">Ambas (todo) — ~1.1 GB</option>
          </select>
          <button onClick={exportVendor} disabled={exporting}
            style={{
              padding: '8px 16px', borderRadius: 8, fontSize: 12.5, fontWeight: 700,
              cursor: exporting ? 'wait' : 'pointer', background: '#a855f7', color: '#fff', border: 'none',
            }}>{exporting ? '⏳ Empaquetando…' : '⬇️ Descargar entorno (.zip)'}</button>
        </div>
        {exportMsg && <div style={{ fontSize: 12.5, marginTop: 8, color: exportMsg.startsWith('⚠️') ? '#f87171' : (exportMsg.startsWith('✅') ? '#4ade80' : '#c4b5fd') }}>{exportMsg}</div>}
      </div>

      {loading ? (
        <div style={{ color: t.muted || '#94a3b8', fontSize: 13 }}>Cargando inventario…</div>
      ) : (
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'flex-start' }}>
          {/* mex-lib */}
          <div style={{ flex: '1 1 420px', minWidth: 360, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0' }}>
              🧩 Paquetes del banco (mex-lib) — {mexLibs.length}
            </div>
            {mexLibs.length === 0 && <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>(ninguno)</div>}
            {mexLibs.map(w => (
              <div key={w.name} style={{ ...card, padding: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 12.5, color: t.text || '#e2e8f0', fontFamily: 'monospace' }}>{w.name}</span>
                  <StatusBadge status={w.status} reason={w.reason} />
                </div>
                {w.reason && <div style={{ fontSize: 11, color: '#f87171' }}>{w.reason}</div>}
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <span style={{ fontSize: 10.5, color: t.dim || '#64748b' }}>{fmtSize(w.size)}</span>
                  <div style={{ flex: 1 }} />
                  <button onClick={() => doVerify(w.name)}
                    style={{ padding: '4px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer', background: '#22c55e18', color: '#4ade80', border: '1px solid #22c55e44' }}>🧪 Verificar</button>
                  <button onClick={() => doDelete(w.name, 'wheel')}
                    style={{ padding: '4px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer', background: '#ef444410', color: '#f87171', border: '1px solid #ef444440' }}>✕</button>
                </div>
              </div>
            ))}

            {/* deps pinneadas */}
            <div style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0', marginTop: 10 }}>
              📌 Dependencias pinneadas — {deps.length}
            </div>
            {deps.length === 0 && <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>(ninguna)</div>}
            {deps.map(w => (
              <div key={w.name} style={{ ...card, padding: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 12, color: t.text || '#e2e8f0', fontFamily: 'monospace', wordBreak: 'break-all' }}>{w.name}</span>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span style={{ fontSize: 10.5, color: t.dim || '#64748b' }}>{fmtSize(w.size)}</span>
                  <button onClick={() => doDelete(w.name, 'wheel')}
                    style={{ padding: '4px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer', background: '#ef444410', color: '#f87171', border: '1px solid #ef444440' }}>✕</button>
                </div>
              </div>
            ))}
          </div>

          {/* pkgcode (modulos de PYTHONPATH) */}
          <div style={{ flex: '1 1 320px', minWidth: 280, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0' }}>
              🧰 Módulos de PYTHONPATH — {inv.pkgcode.length}
            </div>
            <div style={{ fontSize: 11, color: t.dim || '#64748b', marginBottom: 2 }}>
              No son paquetes pip; van en <code>./bank_pkg</code> y <code>main.py</code> los agrega al path.
            </div>
            {inv.pkgcode.length === 0 && <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>(ninguno)</div>}
            {inv.pkgcode.map(p => (
              <div key={p.module} style={{ ...card, padding: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0' }}>📦 {p.module}</span>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <span style={{ fontSize: 10.5, color: t.dim || '#64748b' }}>{p.files.length} archivos</span>
                    <button onClick={() => doDelete(p.module, 'pkgcode')}
                      style={{ padding: '3px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer', background: '#ef444410', color: '#f87171', border: '1px solid #ef444440' }}>✕</button>
                  </div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2, maxHeight: 180, overflowY: 'auto' }}>
                  {p.files.map(f => (
                    <div key={f.name} style={{ fontSize: 11, color: t.muted || '#94a3b8', fontFamily: 'monospace', display: 'flex', justifyContent: 'space-between' }}>
                      <span>{f.name}</span><span style={{ color: t.dim || '#64748b' }}>{fmtSize(f.size)}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Log de verificacion */}
      {verifyLog && (
        <div style={{ ...card }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0' }}>🧪 Verificación: {verifyName}</span>
            {verifyOk != null && (
              <span style={{
                fontSize: 12, fontWeight: 700, padding: '3px 10px', borderRadius: 6,
                background: verifyOk ? '#22c55e22' : '#f8717122', color: verifyOk ? '#4ade80' : '#f87171',
                border: `1px solid ${verifyOk ? '#22c55e55' : '#f8717155'}`,
              }}>{verifyOk ? '✅ Importa limpio' : '⛔ Falla al importar'}</span>
            )}
          </div>
          <pre style={{
            padding: 12, borderRadius: 8, maxHeight: 320, overflow: 'auto', margin: 0,
            background: '#0a0f1a', border: `1px solid ${t.border || '#334155'}`,
            color: '#9ae6b4', fontFamily: 'monospace', fontSize: 11.5, lineHeight: 1.5,
            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
          }}>{verifyLog}</pre>
        </div>
      )}
    </div>
  )
}
