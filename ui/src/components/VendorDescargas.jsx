import { useCallback, useEffect, useRef, useState } from 'react'
// Sección "Descargas" de la pestaña Librerías / Vendor: archivos que se mandaban a mano (código del portal,
// banco.zip, ciencia/pyspark por versión, manifest, SHA256SUMS). En localhost: preparar los archivos y
// compartirlos en la red con una CLAVE (se muestra una vez). En un equipo remoto: pedir la clave y descargar.
// La clave NUNCA va en la URL: el navegador la manda en el cuerpo de un formulario POST (descarga nativa, sin
// cargar el archivo en memoria) o en el header X-BNX-Clave para consultar la lista.
const fmtMB = b => (b >= 1073741824 ? (b / 1073741824).toFixed(2) + ' GB' : (b / 1048576).toFixed(b >= 1048576 * 10 ? 0 : 1) + ' MB')
const MOTIVOS = {
  desactivado: 'El dueño de este portal aún no activó las descargas en red. Pídele que pulse «Compartir descargas en la red».',
  expirada: 'La clave expiró. Pide una nueva.',
  ip_no_permitida: 'Tu IP no está en la lista permitida.',
  demasiados_intentos: 'Demasiados intentos fallidos. Espera un minuto.',
  clave_requerida: 'Escribe la clave de descarga que te compartieron.',
  clave_incorrecta: 'Clave incorrecta.',
}

export default function VendorDescargas({ theme, apiBase }) {
  const t = theme || {}
  const base = `${apiBase}/vendor/descargas`
  const [info, setInfo] = useState(null)
  const [acceso, setAcceso] = useState(null)       // {motivo, error} cuando el servidor niega la lista
  const [clave, setClave] = useState(() => { try { return sessionStorage.getItem('bnx_clave_descarga') || '' } catch { return '' } })
  const [claveNueva, setClaveNueva] = useState('')
  const [dias, setDias] = useState(7)
  const [ips, setIps] = useState('')
  const [banco, setBanco] = useState(false)
  const [msg, setMsg] = useState('')
  const [log, setLog] = useState('')
  const [copiado, setCopiado] = useState('')
  const [bajando, setBajando] = useState(false)
  const frame = useRef(null)
  const local = !!info?.local
  const job = info?.job

  const cargar = useCallback(async (k) => {
    try {
      const r = await fetch(`${base}/estado`, { headers: k ? { 'X-BNX-Clave': k } : {} })
      const d = await r.json().catch(() => ({}))
      if (r.ok && d.ok) {
        setInfo(d); setAcceso(null)
        if (d.local && d.compartir) { setBanco(d.compartir.incluir_banco); setIps((d.compartir.ips || []).join(', ')) }
        if (!d.local) { try { sessionStorage.setItem('bnx_clave_descarga', k || '') } catch { /* sin storage */ } }
      } else { setInfo(null); setAcceso({ motivo: d.motivo || 'desactivado', error: d.error || `HTTP ${r.status}` }) }
    } catch (e) { setAcceso({ motivo: 'red', error: String(e) }) }
  }, [base])
  useEffect(() => { cargar(clave) }, [])  // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!job?.running) return undefined
    const id = setInterval(async () => {
      try { const r = await fetch(`${base}/prepare/log`); const d = await r.json(); setLog(d.job?.log || '') } catch { /* sin servidor */ }
      cargar(clave)
    }, 2000)
    return () => clearInterval(id)
  }, [job?.running, base, clave, cargar])

  const post = async (sub, body) => {
    setMsg('')
    try {
      const r = await fetch(`${base}/${sub}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) })
      const d = await r.json().catch(() => ({}))
      if (!r.ok || !d.ok) { setMsg(d.error || `HTTP ${r.status}`); return null }
      return d
    } catch (e) { setMsg(String(e)); return null }
  }
  const compartir = async () => {
    const d = await post('compartir', { dias: Number(dias) || 7, ips, incluir_banco: banco })
    if (d) { setClaveNueva(d.clave); cargar('') }
  }
  const revocar = async () => { if (await post('revocar')) { setClaveNueva(''); cargar('') } }
  const guardarConfig = async () => { if (await post('config', { ips, incluir_banco: banco, dias: Number(dias) || undefined })) { setMsg('Guardado.'); cargar('') } }
  const preparar = async (forzar) => {
    const d = await post('prepare', { forzar })
    if (d) { setLog(''); cargar('') }
  }
  const copiar = async (txt, que) => {
    try { await navigator.clipboard.writeText(txt) } catch {
      const ta = document.createElement('textarea'); ta.value = txt; document.body.appendChild(ta); ta.select()
      try { document.execCommand('copy') } catch { /* sin portapapeles */ }
      document.body.removeChild(ta)
    }
    setCopiado(que); setTimeout(() => setCopiado(''), 2000)
  }
  const bajar = (nombre) => { const f = document.getElementById(`dl-${nombre}`); if (f) f.submit() }
  const bajarSet = async () => {
    const lista = (info?.archivos || []).filter(a => a.set_linux_311 && (a.tipo !== 'banco' || info.banco_habilitado))
    setBajando(true)
    for (const a of lista) { bajar(a.nombre); await new Promise(res => setTimeout(res, 1500)) }
    setBajando(false)
    setMsg('Si el navegador pregunta «¿permitir descargas múltiples?», acepta.')
  }

  const box = { padding: 12, borderRadius: 8, border: `1px solid ${t.border || '#334155'}`, background: t.codeBg || '#081220' }
  const btn = (color, extra) => ({ padding: '6px 12px', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer',
    background: color, color: '#fff', border: 'none', ...extra })
  const input = { padding: '6px 8px', borderRadius: 6, fontSize: 12, background: t.card || '#0f172a', color: t.text || '#e2e8f0',
    border: `1px solid ${t.border || '#334155'}` }
  const muted = { color: t.muted || '#94a3b8' }
  const comp = info?.compartir
  const archivos = info?.archivos || []
  const hayBanco = archivos.some(a => a.interno)

  return (
    <section style={{ ...box, display: 'flex', flexDirection: 'column', gap: 10 }} aria-labelledby="vd-titulo">
      <h3 id="vd-titulo" style={{ margin: 0, fontSize: 14 }}>⬇ Descargas (archivos para el servidor Linux)</h3>
      <iframe ref={frame} name="bnx_descarga_frame" title="descarga" style={{ display: 'none' }} />
      <div style={muted}>
        Pasos: baja estos archivos, súbelos en la pestaña <b>Librerías / Vendor</b> de tu portal (sección «Subir piezas»)
        o usa <code>preparar_vendor.py --desde-dir</code>, y genera el paquete.
      </div>

      {acceso && (
        <form onSubmit={e => { e.preventDefault(); cargar(clave) }} style={{ display: 'flex', flexDirection: 'column', gap: 6, maxWidth: 520 }}>
          <div role="alert" style={{ color: '#fca5a5' }}>{MOTIVOS[acceso.motivo] || acceso.error}</div>
          <label htmlFor="vd-clave">Clave de descarga</label>
          <div style={{ display: 'flex', gap: 6 }}>
            <input id="vd-clave" type="password" autoComplete="off" value={clave} onChange={e => setClave(e.target.value)}
              style={{ ...input, flex: 1 }} aria-describedby="vd-clave-ayuda" />
            <button type="submit" style={btn(t.accent || '#6366f1')}>Entrar</button>
          </div>
          <div id="vd-clave-ayuda" style={muted}>La clave te la da quien administra este portal (se comparte por un canal interno; no va en la URL).</div>
        </form>)}

      {local && comp && (
        <div style={{ ...box, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <b>Compartir en la red interna</b>
          <div style={muted}>Por defecto solo este equipo (localhost) puede descargar. Los colegas abren este portal por su IP y puerto
            y escriben la clave. Estado: {comp.activo
              ? <b style={{ color: '#22c55e' }}>compartiendo, expira en {Math.max(1, Math.round(comp.expira_en_s / 3600))} h</b>
              : <b>{comp.expirada ? 'clave expirada' : 'no compartido'}</b>}</div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}>
            <div><label htmlFor="vd-dias" style={{ display: 'block' }}>Vigencia (días)</label>
              <input id="vd-dias" type="number" min="1" max="365" value={dias} onChange={e => setDias(e.target.value)} style={{ ...input, width: 80 }} /></div>
            <div style={{ flex: 1, minWidth: 240 }}><label htmlFor="vd-ips" style={{ display: 'block' }}>IPs o subredes permitidas (opcional, CIDR)</label>
              <input id="vd-ips" value={ips} onChange={e => setIps(e.target.value)} placeholder="10.20.0.0/16, 192.168.1.15"
                style={{ ...input, width: '100%', boxSizing: 'border-box' }} /></div>
          </div>
          <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input type="checkbox" checked={banco} onChange={e => setBanco(e.target.checked)} />
            Incluir librerías del banco en las descargas (banco.zip)
          </label>
          {banco && <div role="note" style={{ color: '#fbbf24' }}>⚠ Interno: no reenviar fuera del banco. Quien tenga la clave podrá bajar las mex-lib.</div>}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <button onClick={compartir} style={btn('#16a34a')}>🔑 {comp.activo ? 'Generar clave nueva' : 'Compartir descargas en la red'}</button>
            {comp.activo && <button onClick={guardarConfig} style={btn('#64748b')}>Guardar cambios</button>}
            {comp.activo && <button onClick={revocar} style={btn('transparent', { color: '#fca5a5', border: '1px solid #ef444477' })}>Revocar</button>}
          </div>
          {claveNueva && (
            <div role="status" style={{ ...box, borderColor: '#22c55e' }}>
              Clave (se muestra una sola vez; compártela por un canal interno):{' '}
              <code style={{ fontSize: 14, userSelect: 'all' }}>{claveNueva}</code>{' '}
              <button onClick={() => copiar(claveNueva, 'clave')} style={btn('#64748b', { padding: '2px 8px' })}>{copiado === 'clave' ? '✓ Copiada' : 'Copiar'}</button>
            </div>)}
        </div>)}

      {info && (
        <>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            {local && <button onClick={() => preparar(false)} disabled={!!job?.running} style={btn(t.accent || '#6366f1')}>
              {job?.running ? '⏳ Preparando…' : 'Preparar / actualizar archivos de descarga'}</button>}
            <button onClick={bajarSet} disabled={bajando || !archivos.some(a => a.set_linux_311)} style={btn('#0ea5e9')}>
              {bajando ? '⏳ Bajando…' : 'Descargar todo para Linux · Python 3.11 (RHEL 8)'}</button>
            <span style={muted} aria-live="polite">
              {info.generado ? `Generado ${info.generado} (commit ${info.commit || '-'})` : 'Aún no hay archivos preparados.'}
              {local && info.desactualizado && info.generado ? ' · desactualizado: pulsa «Preparar»' : ''}
            </span>
          </div>
          {archivos.length === 0 ? <div style={muted}>{local ? 'Pulsa «Preparar / actualizar archivos de descarga».' : 'El dueño del portal aún no preparó los archivos.'}</div> : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12 }}>
                <caption style={{ textAlign: 'left', ...muted }}>Archivos disponibles</caption>
                <thead><tr>{['Archivo', 'Para qué sirve', 'Python', 'Tamaño', 'sha256', ''].map(h => (
                  <th key={h || 'acc'} scope="col" style={{ textAlign: 'left', padding: '4px 8px', borderBottom: `1px solid ${t.border || '#334155'}` }}>{h || 'Acción'}</th>))}</tr></thead>
                <tbody>
                  {archivos.map(a => (
                    <tr key={a.nombre}>
                      <td style={{ padding: '4px 8px' }}><code>{a.nombre}</code>{a.interno && <div style={{ color: '#fbbf24' }}>Interno: no reenviar fuera del banco</div>}</td>
                      <td style={{ padding: '4px 8px', ...muted }}>{a.para}</td>
                      <td style={{ padding: '4px 8px' }}>{a.python || '—'}</td>
                      <td style={{ padding: '4px 8px', whiteSpace: 'nowrap' }}>{fmtMB(a.bytes)}</td>
                      <td style={{ padding: '4px 8px', whiteSpace: 'nowrap' }}><code>{a.sha256.slice(0, 10)}…</code>{' '}
                        <button onClick={() => copiar(a.sha256, a.nombre)} aria-label={`Copiar sha256 de ${a.nombre}`}
                          style={btn('#64748b', { padding: '1px 6px', fontSize: 11 })}>{copiado === a.nombre ? '✓' : 'Copiar'}</button></td>
                      <td style={{ padding: '4px 8px' }}>
                        <form id={`dl-${a.nombre}`} method="post" action={`${base}/get/${encodeURIComponent(a.nombre)}`} target="bnx_descarga_frame">
                          {!local && <input type="hidden" name="clave" value={clave} />}
                          <button type="submit" aria-label={`Descargar ${a.nombre}`} style={btn('#16a34a', { padding: '3px 10px' })}>Descargar</button>
                        </form></td>
                    </tr>))}
                </tbody>
              </table>
            </div>)}
          {local && !hayBanco && archivos.length > 0 && <div style={muted}>banco.zip no se generó: no hay librerías del banco en el cache.</div>}
          {log && <pre style={{ ...box, margin: 0, maxHeight: 160, overflow: 'auto', fontSize: 10.5, whiteSpace: 'pre-wrap', ...muted }}>{log}</pre>}
          {job && job.started && !job.running && (job.returncode === 0
            ? null : <div role="alert" style={{ color: '#fca5a5' }}>❌ La preparación falló: {job.motivo || 'revisa el log'}</div>)}
        </>)}
      {msg && <div role="status" style={{ color: '#fbbf24' }}>{msg}</div>}
    </section>
  )
}
