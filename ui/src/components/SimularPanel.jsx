import { useState, useEffect, useRef, useCallback } from 'react'
import ParquetVisor from './ParquetVisor'

// Simulacion de los jobs de un paquete generado, estilo terminal (solo Mac/Linux con Java; solo localhost).
// Backend: /mlops/simular/{info,iniciar,estado,cancelar,reiniciar,visor,espacio,limpiar} (src/mlops_simular.py).
// El PIVOTE corre siempre primero: 'Simular todos' = pivotes y luego el resto; un job suelto que no es
// pivote corre antes el pivote de su modelo si su salida aun no esta en demo_out de esta sesion.
const COLORES = { 30: '#6b7280', 31: '#f87171', 32: '#4ade80', 33: '#fbbf24', 34: '#60a5fa', 35: '#c084fc', 36: '#22d3ee', 37: '#e5e7eb', 90: '#9ca3af' }
const ANSI = /\x1b\[([0-9;]*)m/g

// Colores basicos ANSI; sin ANSI, por prefijo de la linea ([OK] / [ERROR] / [sim] ...).
function colorLinea(l) {
  if (/^\s*\[OK\]|\[kernel\] FIN OK/.test(l)) return '#4ade80'
  if (/^\s*\[ERROR\]|\[kernel\] FIN ERROR|Traceback|^\w*(Error|Exception)\b/.test(l)) return '#f87171'
  if (/^\[\d+\/\d+\]/.test(l)) return '#22d3ee'
  if (/^\[(sim|orden)\]/.test(l)) return '#93c5fd'
  if (/\[AVISO\]|WARN/.test(l)) return '#fbbf24'
  if (/^\$ /.test(l)) return '#a78bfa'
  return null
}
function Linea({ texto }) {
  if (!ANSI.test(texto)) {
    ANSI.lastIndex = 0
    const c = colorLinea(texto)
    return <div style={c ? { color: c } : undefined}>{texto || '\u00a0'}</div>
  }
  ANSI.lastIndex = 0
  const partes = []
  let color = null, bold = false, ult = 0, m
  while ((m = ANSI.exec(texto)) !== null) {
    if (m.index > ult) partes.push({ s: texto.slice(ult, m.index), color, bold })
    for (const cod of (m[1] || '0').split(';').map(Number)) {
      if (cod === 0) { color = null; bold = false } else if (cod === 1) bold = true
      else if (COLORES[cod]) color = COLORES[cod]
    }
    ult = m.index + m[0].length
  }
  ANSI.lastIndex = 0
  if (ult < texto.length) partes.push({ s: texto.slice(ult), color, bold })
  return <div>{partes.map((p, i) => <span key={i} style={{ color: p.color || undefined, fontWeight: p.bold ? 700 : undefined }}>{p.s}</span>)}</div>
}

const fmtBytes = (n) => (n >= 1073741824 ? `${(n / 1073741824).toFixed(1)} GB` : `${Math.max(0, Math.round((n || 0) / 1048576))} MB`)
const fmtSeg = (s) => (s >= 60 ? `${Math.floor(s / 60)} min ${Math.round(s % 60)} s` : `${(s || 0).toFixed(1)} s`)
const filasDe = (esc) => (esc || []).reduce((n, e) => n + (Number.isInteger(e.filas) ? e.filas : 0), 0)
const ETIQ = { preparando: 'preparando entorno', corriendo: 'corriendo', ok: 'terminó OK', fallo: 'falló', cancelado: 'cancelado' }
const COLOR_ESTADO = { preparando: '#fbbf24', corriendo: '#38bdf8', ok: '#4ade80', fallo: '#f87171', cancelado: '#fbbf24' }

export default function SimularPanel({ t, apiBase, token }) {
  const [info, setInfo] = useState(null)
  const [errorInfo, setErrorInfo] = useState('')
  const [run, setRun] = useState(null)        // {id, estado, duracion, resumen, pasos, ...}
  const [log, setLog] = useState('')
  const [msg, setMsg] = useState('')
  const [copiado, setCopiado] = useState(false)
  const [visor, setVisor] = useState(null)
  const [espacio, setEspacio] = useState(null)   // {total, carpetas, max}: disco que ocupan las simulaciones (venvs)
  const [settings, setSettings] = useState(() => { try { return localStorage.getItem('bnx_sim_settings') || '' } catch { return '' } })
  const offRef = useRef(0)
  const termRef = useRef(null)
  const pegado = useRef(true)               // autoscroll solo si el usuario no subio a leer
  const timer = useRef(null)
  const post = (ruta, body) => fetch(`${apiBase}/mlops/simular/${ruta}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  }).then(async r => { const d = await r.json().catch(() => ({})); if (!r.ok || d.ok === false) throw new Error(d.error || `HTTP ${r.status}`); return d })

  const cargarInfo = useCallback(async () => {
    if (!token) return
    try {
      const r = await fetch(`${apiBase}/mlops/simular/info?token=${encodeURIComponent(token)}`)
      const d = await r.json()
      if (!r.ok || d.ok === false) throw new Error(d.error || `HTTP ${r.status}`)
      setInfo(d); setErrorInfo('')
    } catch (e) { setInfo(null); setErrorInfo(e.message) }
  }, [apiBase, token])
  const cargarEspacio = useCallback(async () => {
    try {
      const r = await fetch(`${apiBase}/mlops/simular/espacio`)
      const d = await r.json()
      if (r.ok && d.ok !== false) setEspacio(d)
    } catch { /* sin espacio: el boton queda sin tamano */ }
  }, [apiBase])
  useEffect(() => { cargarInfo(); cargarEspacio() }, [cargarInfo, cargarEspacio])
  useEffect(() => () => clearInterval(timer.current), [])

  const sondear = useCallback((id) => {
    clearInterval(timer.current)
    const tick = async () => {
      try {
        const r = await fetch(`${apiBase}/mlops/simular/estado?run=${id}&offset=${offRef.current}`)
        const d = await r.json()
        if (!r.ok || d.ok === false) throw new Error(d.error || `HTTP ${r.status}`)
        offRef.current = d.offset
        if (d.log) setLog(l => l + d.log)
        setRun(d)
        if (d.terminado) { clearInterval(timer.current); cargarInfo(); cargarEspacio() }
      } catch (e) { clearInterval(timer.current); setMsg('No se pudo leer el estado: ' + e.message) }
    }
    timer.current = setInterval(tick, 700)
    tick()
  }, [apiBase, cargarInfo])

  const activo = run && !run.terminado
  const simular = async (job) => {
    setMsg(''); setLog(''); offRef.current = 0; pegado.current = true
    try {
      const d = await post('iniciar', { token, job: job || 'todos', settings: settings.trim() || undefined })
      try { localStorage.setItem('bnx_sim_settings', settings.trim()) } catch { /* sin storage */ }
      setRun({ id: d.run, estado: 'preparando', duracion: 0, resumen: [], pasos: [], plan: [] })
      sondear(d.run)
      setTimeout(() => termRef.current && termRef.current.focus(), 0)
    } catch (e) { setMsg(e.message) }
  }
  const cancelar = async () => {
    try { await post('cancelar', { run: run.id }) } catch (e) { setMsg(e.message) }
  }
  const reiniciar = async () => {
    try { await post('reiniciar', { token }); setMsg('demo_out reiniciado: la próxima simulación empieza limpia.'); cargarInfo() }
    catch (e) { setMsg(e.message) }
  }
  const limpiarSims = async () => {
    const n = (espacio?.carpetas || []).filter(c => !c.activo).length
    if (!window.confirm(`Se borran ${n} simulación(es) guardada(s) (${fmtBytes(espacio?.total)}); la que está corriendo no se toca. El entorno se vuelve a montar en la próxima simulación. ¿Continuar?`)) return
    try {
      const d = await post('limpiar', { conservar: 0 })
      setMsg(`Simulaciones limpiadas: ${d.borradas.length} carpeta(s), ${fmtBytes(d.liberado)} liberados.`)
      cargarEspacio(); cargarInfo()
    } catch (e) { setMsg(e.message) }
  }
  const copiar = async () => {
    try { await navigator.clipboard.writeText(log) } catch {
      const ta = document.createElement('textarea'); ta.value = log; document.body.appendChild(ta); ta.select()
      try { document.execCommand('copy') } catch { /* sin portapapeles */ }
      ta.remove()
    }
    setCopiado(true); setTimeout(() => setCopiado(false), 1800)
  }
  // autoscroll del terminal mientras el usuario no haya subido a leer
  useEffect(() => {
    const el = termRef.current
    if (el && pegado.current) el.scrollTop = el.scrollHeight
  }, [log])
  const onScroll = (e) => {
    const el = e.currentTarget
    pegado.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40
  }
  const visorPost = (accion, body) => post('visor', { token, action: accion, ...body })

  const b = (primary, off) => ({
    padding: '6px 12px', borderRadius: 6, fontSize: 12, fontWeight: 700, cursor: off ? 'not-allowed' : 'pointer',
    opacity: off ? 0.5 : 1,
    background: primary ? '#16a34a' : 'transparent', color: primary ? '#fff' : (t.text || '#e2e8f0'),
    border: `1px solid ${primary ? '#16a34a' : (t.border || '#334155')}`,
  })
  const bloqueado = !info || !info.soportado || activo
  const lineas = log ? log.replace(/\n$/, '').split('\n') : []

  return (
    <div style={{ marginTop: 14, borderTop: `1px solid ${t.border || '#334155'}`, paddingTop: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0' }}>🖥 Simular jobs (terminal)</span>
        <button onClick={() => simular(null)} disabled={bloqueado} aria-label="Simular todos los jobs, pivotes primero"
          title="Corre todos los jobs: primero los pivote, después el resto" style={b(true, bloqueado)}>▶ Simular todos</button>
        <button onClick={reiniciar} disabled={!info || !info.soportado || activo} aria-label="Reiniciar la carpeta demo_out"
          title="Borra demo_out y el estado de la sesión: empieza limpio" style={b(false, !info || !info.soportado || activo)}>↺ Reiniciar demo_out</button>
        <button onClick={limpiarSims} disabled={!espacio || !(espacio.carpetas || []).some(c => !c.activo)} aria-label="Limpiar simulaciones guardadas"
          title={`Borra los entornos de simulación guardados (se conservan automáticamente los ${espacio?.max ?? 2} más recientes; BNX_SIMULAR_MAX). Nunca borra el que está corriendo.`}
          style={b(false, !espacio || !(espacio.carpetas || []).some(c => !c.activo))}>
          🧹 Limpiar simulaciones{espacio ? ` (${fmtBytes(espacio.total)} en ${(espacio.carpetas || []).length})` : ''}</button>
        <span style={{ fontSize: 11.5, color: t.muted || '#94a3b8' }}>
          Spark local con datos sintéticos (<code>python main.py --demo</code>). El pivote corre siempre primero.
        </span>
      </div>
      <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', fontSize: 12 }}>
        <label htmlFor="sim-settings" style={{ color: t.muted || '#94a3b8' }}>Carpeta <code>bin/settings</code> del banco (opcional, ruta local):</label>
        <input id="sim-settings" value={settings} onChange={e => setSettings(e.target.value)} disabled={activo}
          placeholder={info?.settings ? 'el paquete trae settings: se usan' : '/ruta/a/bin/settings (su config de negocio, sin conectar a Hive)'}
          style={{ flex: 1, minWidth: 260, padding: '4px 8px', borderRadius: 6, fontSize: 12, background: t.codeBg || '#081220', color: t.text || '#e2e8f0', border: `1px solid ${t.border || '#334155'}` }} />
      </div>
      {errorInfo && <div role="alert" style={{ marginTop: 8, fontSize: 12, color: '#f87171' }}>⚠ {errorInfo}</div>}
      {info && !info.soportado && (
        <div role="alert" style={{ marginTop: 8, padding: 8, borderRadius: 6, fontSize: 12, color: '#fbbf24', border: '1px solid #f59e0b55' }}>
          ⛔ {info.mensaje}
        </div>)}
      {info && info.soportado && (
        <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {(info.jobs || []).map(j => {
            const r = (run?.resumen || []).find(x => x.job === j.name)
            const hecho = (info.hechos || []).includes(j.name)
            return (
              <div key={j.name} style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 12, color: t.text || '#e2e8f0' }}>
                <button onClick={() => simular(j.name)} disabled={bloqueado} aria-label={`Simular el job ${j.name}`}
                  style={{ ...b(false, bloqueado), padding: '3px 10px' }}>▶ Simular</button>
                <code style={{ minWidth: 190 }}>{j.name}</code>
                {j.pivote && <span style={{ color: '#fbbf24', fontWeight: 700 }}>⚑ pivote</span>}
                <span style={{ color: t.dim || '#64748b' }}>{j.kind === 'kernel' ? 'job del banco' : 'aggregate'}</span>
                {r ? <span style={{ color: r.estado === 'OK' ? '#4ade80' : '#f87171' }}>[{r.estado}] {fmtSeg(r.seg)}</span>
                  : hecho ? <span style={{ color: '#4ade80' }}>[OK] en esta sesión</span> : null}
              </div>)
          })}
        </div>)}
      {info && info.soportado && info.mensaje && (
        <div style={{ marginTop: 6, fontSize: 11, color: t.dim || '#64748b' }}>
          Java: {info.mensaje} · entorno {info.entorno_listo ? 'ya montado (se reutiliza)' : 'se monta en la primera simulación (setup.sh, una sola vez)'}
        </div>)}
      {msg && <div role="alert" style={{ marginTop: 8, fontSize: 12, color: '#fbbf24' }}>⚠ {msg}</div>}

      {(run || log) && (
        <div style={{ marginTop: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 6 }}>
            <span role="status" aria-live="polite" style={{ fontSize: 12.5, fontWeight: 700, color: COLOR_ESTADO[run?.estado] || '#94a3b8' }}>
              {run ? `${ETIQ[run.estado] || run.estado} · ${fmtSeg(run.duracion)}` : ''}
              {run && run.arranque_seg > 0 ? ` (arranque del entorno ${fmtSeg(run.arranque_seg)})` : ''}
              {run && run.venv_reutilizado ? ' · entorno reutilizado' : ''}
            </span>
            {activo && <button onClick={cancelar} aria-label="Cancelar la simulación" style={b(false, false)}>■ Cancelar</button>}
            <button onClick={copiar} aria-label="Copiar el log al portapapeles" style={b(false, !log)} disabled={!log}>
              {copiado ? '✓ Copiado' : '⧉ Copiar log'}</button>
          </div>
          <div ref={termRef} role="log" aria-label="Salida de la simulación" aria-live="off" tabIndex={0} onScroll={onScroll}
            style={{
              background: '#0b0f14', color: '#d1d5db', fontFamily: 'ui-monospace, Menlo, Consolas, monospace', fontSize: 12,
              lineHeight: 1.45, padding: 10, borderRadius: 8, border: `1px solid ${t.border || '#334155'}`,
              height: 340, overflow: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            }}>
            {lineas.map((l, i) => <Linea key={i} texto={l} />)}
            {activo && <span aria-hidden="true" style={{ color: '#4ade80' }}>▌</span>}
          </div>
          {run && run.terminado && (run.resumen || []).length > 0 && (
            <div style={{ marginTop: 8, fontSize: 12, color: t.text || '#e2e8f0' }}>
              <div style={{ fontWeight: 700, marginBottom: 4 }}>
                Resumen: {(run.resumen || []).filter(r => r.estado === 'OK').length}/{run.resumen.length} OK · {fmtSeg(run.duracion)}
              </div>
              <table style={{ borderCollapse: 'collapse', fontSize: 12 }}>
                <tbody>
                  {run.resumen.map((r, i) => (
                    <tr key={i}>
                      <td style={{ padding: '2px 10px 2px 0', fontWeight: 700, color: r.estado === 'OK' ? '#4ade80' : '#f87171' }}>[{r.estado}]</td>
                      <td style={{ padding: '2px 10px 2px 0' }}><code>{r.job}</code></td>
                      <td style={{ padding: '2px 10px 2px 0' }}>{fmtSeg(r.seg)}</td>
                      <td style={{ padding: '2px 0' }}>
                        {(r.escrituras || []).length
                          ? `${filasDe(r.escrituras)} fila(s) en ${r.escrituras.length} salida(s): ` +
                            r.escrituras.map(e => `${String(e.destino).split('/').slice(-2).join('/')} (${e.filas ?? '?'})`).join(', ')
                          : (r.detalle || '—')}
                      </td>
                    </tr>))}
                </tbody>
              </table>
              <button onClick={() => setVisor({ k: Date.now() })} aria-label="Ver las salidas de demo_out en el visor de datos"
                style={{ ...b(false, false), marginTop: 6 }}>📊 Ver salidas (demo_out)</button>
            </div>)}
        </div>)}
      {visor && <ParquetVisor key={visor.k} t={t} btn={(p) => ({
        padding: '6px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
        background: p ? (t.accent || '#1a73e8') : 'transparent', color: p ? '#fff' : (t.text || '#e2e8f0'),
        border: `1px solid ${p ? (t.accent || '#1a73e8') : (t.border || '#334155')}`,
      })} post={visorPost} basePath="demo_out" inicial={{ zona: 'output' }} onClose={() => setVisor(null)} />}
    </div>
  )
}
