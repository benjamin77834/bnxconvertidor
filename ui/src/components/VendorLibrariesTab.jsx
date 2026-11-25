import { useRef, useState } from 'react'
import VendorDescargas from './VendorDescargas'
// Pestaña "Librerías / Vendor" del Framework MLOps v2: estado del cache por pieza y 3 formas de
// llenarlo sin línea de comandos: SUBIR los ZIP desde el navegador (streaming, por archivo),
// indicar una RUTA local del servidor (carpeta BNX_interno, 3_vendor_pyX, pieza.zip, banco.zip) o
// bajar de GitHub. Todo corre en el mismo job/log que "Bajar/generar cache".
const NOMBRE_OK = /^(SHA256SUMS|[^/\\:]+\.(zip|whl|tar\.gz|json))$/i
const nuevoLote = () => Array.from(crypto.getRandomValues(new Uint8Array(12)))
  .map(b => b.toString(16).padStart(2, '0')).join('')
const fmtMB = b => (b / 1048576).toFixed(b >= 1048576 * 10 ? 0 : 1) + ' MB'

export default function VendorLibrariesTab({ theme, apiBase, pyTarget, vendorStatus, vendorJob, setVendorJob,
  piezasSel, setPiezasSel, startVendorPrepare }) {
  const t = theme || {}
  const ver = (pyTarget || 'py3.11').replace('py', '')
  const [items, setItems] = useState([])        // [{file, name, estado, pct, error, sha}]
  const [lote, setLote] = useState(nuevoLote)
  const [err, setErr] = useState('')
  const [ruta, setRuta] = useState('')
  const [drag, setDrag] = useState(false)
  const xhrs = useRef({})
  const corriendo = !!vendorJob?.running
  const subiendo = items.some(x => x.estado === 'subiendo')
  const upd = (name, patch) => setItems(prev => prev.map(x => x.name === name ? { ...x, ...patch } : x))

  const agregar = (fileList) => {
    setErr('')
    const nuevos = []
    for (const f of Array.from(fileList || [])) {
      if (!NOMBRE_OK.test(f.name)) { setErr(`Archivo no admitido: ${f.name} (solo .zip .whl .tar.gz .json o SHA256SUMS)`); continue }
      nuevos.push({ file: f, name: f.name, estado: 'pendiente', pct: 0, error: '' })
    }
    setItems(prev => [...prev.filter(p => !nuevos.some(n => n.name === p.name)), ...nuevos])
  }
  const subirUno = (it) => new Promise(resolve => {
    const xhr = new XMLHttpRequest()
    xhrs.current[it.name] = xhr
    xhr.open('POST', `${apiBase}/vendor/upload?lote=${lote}&name=${encodeURIComponent(it.name)}`)
    xhr.setRequestHeader('Content-Type', 'application/octet-stream')
    xhr.upload.onprogress = e => { if (e.lengthComputable) upd(it.name, { pct: Math.round(e.loaded * 100 / e.total) }) }
    xhr.onload = () => {
      let d = {}
      try { d = JSON.parse(xhr.responseText || '{}') } catch { /* respuesta no JSON */ }
      if (xhr.status === 200 && d.ok) upd(it.name, { estado: 'ok', pct: 100, sha: d.sha256 })
      else upd(it.name, { estado: 'error', error: d.error || `HTTP ${xhr.status}` })
      resolve()
    }
    xhr.onerror = () => { upd(it.name, { estado: 'error', error: 'error de red: se corto la conexion con el servidor (si el servidor es otra maquina, revise que acepte importar desde clientes remotos: BNX_PERMITIR_EJECUCION_REMOTA=1)' }); resolve() }
    xhr.onabort = () => { upd(it.name, { estado: 'cancelado', error: 'cancelado' }); resolve() }
    upd(it.name, { estado: 'subiendo', pct: 0, error: '' })
    xhr.send(it.file)
  })
  const subirTodo = async (soloFallidos) => {
    // Sondeo previo: el servidor puede rechazar clientes remotos y cortar la subida grande (se vería como 'error de red').
    try {
      const r = await fetch(`${apiBase}/vendor/upload?check=1`, { method: 'POST' })
      const d = await r.json().catch(() => ({}))
      if (r.status === 403 || d.ok === false) {
        const msg = d.error || `HTTP ${r.status}`
        setErr(msg)
        setItems(prev => prev.map(p => (p.estado === 'ok' ? p : { ...p, estado: 'error', error: msg })))
        return
      }
    } catch { /* sin servidor: que lo diga la subida */ }
    for (const it of items) {
      if (it.estado === 'ok') continue
      if (soloFallidos && it.estado === 'pendiente') continue
      await subirUno(it)
    }
  }
  const cancelar = async () => {
    Object.values(xhrs.current).forEach(x => { try { x.abort() } catch { /* ya termino */ } })
    xhrs.current = {}
    try {
      await fetch(`${apiBase}/vendor/upload/cancel`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lote }) })
    } catch { /* sin servidor */ }
    setItems([]); setLote(nuevoLote())
  }
  const lanzar = async (url, body) => {
    setErr('')
    try {
      const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ version: ver, piezas: piezasSel, ...body }) })
      const d = await res.json()
      if (!d.ok) { setErr(d.error || `HTTP ${res.status}`); return false }
      setVendorJob({ ...(d.job || {}), running: true, log: '' })
      return true
    } catch (e) { setErr(String(e)); return false }
  }
  const importarSubidos = async () => {
    if (await lanzar(`${apiBase}/vendor/upload/import`, { lote })) { setItems([]); setLote(nuevoLote()) }
  }

  const pz = (vendorStatus?.piezas || []).filter(x => x.python === ver)
  const host = vendorStatus?.host?.plataforma
  const banco = vendorStatus?.banco
  const box = { padding: 12, borderRadius: 8, border: `1px solid ${t.border || '#334155'}`, background: t.codeBg || '#081220' }
  const btn = (color, extra) => ({ padding: '6px 12px', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer',
    background: color, color: '#fff', border: 'none', ...extra })
  const fila = (clave, texto, x) => (
    <label key={clave} style={{ display: 'flex', gap: 8, alignItems: 'center', cursor: 'pointer' }}>
      <input type="checkbox" checked={!!piezasSel[clave]} onChange={e => setPiezasSel({ ...piezasSel, [clave]: e.target.checked })} />
      <span style={{ minWidth: 300 }}>{texto}</span>
      <span>{x ? fmtMB(x.presente ? x.bytes : (x.bytes_descarga || 0)) : '?'}</span>
      <span style={{ color: x?.presente ? '#22c55e' : '#fca5a5' }}>{x?.presente ? `✅ (${x.layout})` : '✖ falta'}</span>
      {x?.glibc_max && <span style={{ color: t.muted || '#94a3b8' }}>glibc ≤ {x.glibc_max}</span>}
      {(x?.glibc_incompatibles || []).length > 0 &&
        <span style={{ color: '#fca5a5' }}>⚠ no instalan en RHEL 8: {x.glibc_incompatibles.join(', ')}</span>}
    </label>)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: 12.5, color: t.text || '#e2e8f0' }}>
      <VendorDescargas theme={t} apiBase={apiBase} />
      <div style={box}>
        <b>Estado del cache para Linux · Python {ver}</b>{' '}
        <span style={{ color: t.muted || '#94a3b8' }}>({vendorStatus?.cache_dir || '…'}; portal: {host || '?'}, Python {vendorStatus?.host?.python || '?'})</span>
        <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {fila('ciencia_linux', `Ciencia Linux (ciencia-linux-py${ver}.zip) · servidor RHEL 8`, pz.find(x => x.pieza === 'ciencia' && x.plataforma === 'linux'))}
          {fila('pyspark', `PySpark (pyspark-py${ver}.zip) · para "PySpark incluido"`, pz.find(x => x.pieza === 'pyspark'))}
          {host && host !== 'linux' && fila('ciencia_host', `Ciencia ${host} (opcional, solo para correr aquí)`, pz.find(x => x.pieza === 'ciencia' && x.plataforma === host))}
          {banco && (
            <div>Banco (2_banco.zip): mex-lib {banco.sdists.length}/{banco.sdists.length + banco.sdists_faltan.length},
              módulos {banco.pkgcode.length}/{banco.pkgcode.length + banco.pkgcode_faltan.length}
              {(banco.sdists_faltan.length + banco.pkgcode_faltan.length) > 0
                ? <span style={{ color: '#fca5a5' }}> · faltan: {[...banco.sdists_faltan, ...banco.pkgcode_faltan].join(', ')}</span>
                : <span style={{ color: '#22c55e' }}> ✅</span>}
            </div>)}
        </div>
        <div style={{ marginTop: 6, color: t.muted || '#94a3b8' }}>
          Mínimo para el servidor: <code>ciencia-linux-py{ver}.zip</code> + <code>pyspark-py{ver}.zip</code> + <code>2_banco.zip</code>
          {' '}(+ <code>vendor-manifest.json</code> y <code>SHA256SUMS</code> para verificar sha256).
        </div>
      </div>

      <div style={{ ...box, borderStyle: 'dashed', borderColor: drag ? '#22c55e' : (t.border || '#334155') }}
        onDragOver={e => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)}
        onDrop={e => { e.preventDefault(); setDrag(false); agregar(e.dataTransfer.files) }}>
        <b>⬆ Subir piezas desde este equipo</b> (arrastra y suelta aquí o
        <label style={{ marginLeft: 6, color: '#818cf8', cursor: 'pointer', textDecoration: 'underline' }}>
          elige archivos
          <input type="file" multiple style={{ display: 'none' }} accept=".zip,.whl,.gz,.json,*"
            onChange={e => { agregar(e.target.files); e.target.value = '' }} />
        </label>)
        <div style={{ color: t.muted || '#94a3b8', marginTop: 4 }}>
          ZIP de piezas (pyspark/ciencia), vendor-manifest.json, SHA256SUMS, banco.zip / 2_banco.zip, mex-lib*.tar.gz
          o el ZIP completo del paquete interno. Se suben por archivo (sin cargarlos en memoria) y se importan al final.
        </div>
        {items.length > 0 && (
          <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
            {items.map(it => (
              <div key={it.name} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{ minWidth: 260 }}>{it.name}</span>
                <span style={{ minWidth: 70 }}>{fmtMB(it.file.size)}</span>
                <div style={{ width: 160, height: 8, background: '#33415588', borderRadius: 4 }}>
                  <div style={{ width: `${it.pct}%`, height: 8, borderRadius: 4, background: it.estado === 'error' ? '#ef4444' : '#22c55e' }} />
                </div>
                <span style={{ color: it.estado === 'ok' ? '#22c55e' : it.estado === 'error' || it.estado === 'cancelado' ? '#fca5a5' : (t.muted || '#94a3b8') }}>
                  {it.estado === 'subiendo' ? `${it.pct}%` : it.estado}{it.error ? `: ${it.error}` : ''}
                </span>
                {(it.estado === 'error' || it.estado === 'cancelado') && !subiendo &&
                  <button onClick={() => subirUno(it)} style={btn('#64748b', { padding: '2px 8px' })}>Reintentar</button>}
              </div>))}
            <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
              <button disabled={subiendo || corriendo} onClick={() => subirTodo(false)} style={btn(t.accent || '#6366f1')}>
                {subiendo ? '⏳ Subiendo…' : '⬆ Subir'}</button>
              <button disabled={subiendo || corriendo || !items.some(x => x.estado === 'ok') || items.some(x => x.estado !== 'ok')}
                onClick={importarSubidos} style={btn('#16a34a')}>📥 Importar lo subido</button>
              <button onClick={cancelar} style={btn('transparent', { color: '#fca5a5', border: '1px solid #ef444477' })}>
                ✖ Cancelar y borrar</button>
            </div>
          </div>)}
      </div>

      <div style={box}>
        <b>📂 Importar desde una carpeta o ZIP de este equipo</b> (el portal corre aquí; solo lectura)
        <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
          <input value={ruta} onChange={e => setRuta(e.target.value)} spellCheck={false}
            placeholder="C:\Users\yo\Downloads\BNX_interno_v3   (o ...\3_vendor_py3.11, pieza.zip, 2_banco.zip)"
            style={{ flex: 1, padding: '6px 8px', borderRadius: 6, fontSize: 12, background: t.card || '#0f172a',
                     color: t.text || '#e2e8f0', border: `1px solid ${t.border || '#334155'}` }} />
          <button disabled={corriendo || !ruta.trim()} onClick={() => lanzar(`${apiBase}/vendor/import`, { path: ruta.trim() })}
            style={btn('#16a34a')}>📥 Importar piezas</button>
        </div>
        <div style={{ color: t.muted || '#94a3b8', marginTop: 4 }}>
          Acepta: carpeta de release (vendor-manifest.json + ZIPs), un ZIP de pieza, banco.zip o carpeta con mex-lib*.tar.gz,
          o la carpeta BNX_interno_v3 (usa 3_vendor_py{ver} y 2_banco.zip).
        </div>
      </div>

      <div style={box}>
        <button disabled={corriendo} onClick={() => startVendorPrepare(ver)} style={btn(t.accent || '#6366f1')}>
          {corriendo ? '⏳ Trabajando…' : `⬇ Bajar de GitHub (Python ${ver})`}</button>
        <span style={{ marginLeft: 8, color: t.muted || '#94a3b8' }}>Requiere internet (release público vendor-v3; no trae el banco).</span>
      </div>

      {err && <div style={{ color: '#fca5a5' }}>⚠ {err}</div>}
      {vendorJob?.log && (
        <pre style={{ ...box, margin: 0, maxHeight: 220, overflow: 'auto', fontSize: 10.5, whiteSpace: 'pre-wrap',
                      color: t.muted || '#94a3b8' }}>{vendorJob.log}</pre>)}
      {vendorJob && !vendorJob.running && vendorJob.started && (
        vendorJob.returncode === 0
          ? <div style={{ color: '#22c55e' }}>✅ Terminó bien (código 0).</div>
          : <div style={{ color: '#fca5a5' }}>❌ Falló (código {String(vendorJob.returncode)}): {vendorJob.motivo || 'revisa el log'}.</div>)}
    </div>
  )
}
