import { useState, useEffect, useRef, useCallback } from 'react'
import ParquetVisor from './ParquetVisor'

// Simulacion de los jobs de un paquete generado, estilo terminal (solo Mac/Linux con Java; solo localhost).
// Backend: /mlops/simular/{info,iniciar,estado,cancelar,reiniciar,visor,espacio,limpiar,linux,preparar} (src/mlops_simular.py).
// 'Dónde simular': este equipo (venv del host) o Linux RHEL 8 x86_64 (contenedor de Podman, como el servidor del banco).
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

// Monitoreo de recursos EN VIVO: CPU % (100% = un núcleo) y memoria del runner y sus hijos (JVM de Spark), con marcas por job.
// Datos: muestras que escribe bnx_demo/monitor.py (cada ~1 s) y el backend entrega de forma incremental (moff).
function MonitorRecursos({ t, muestras, eventos, nucleos, ncpu }) {
  const W = 640, H = 130, PADL = 34, PADB = 16
  if (!muestras.length) return null
  const t0 = muestras[0].t - (muestras[0].dt || 1)
  const t1 = muestras[muestras.length - 1].t
  const span = Math.max(5, t1 - t0)
  const maxCpu = Math.max(100 * (nucleos || 1), ...muestras.map(m => m.cpu))
  const maxMem = Math.max(256, ...muestras.map(m => m.rss))
  const x = (tt) => PADL + ((tt - t0) / span) * (W - PADL - 4)
  const yc = (v) => 4 + (1 - v / maxCpu) * (H - PADB - 8)
  const ym = (v) => 4 + (1 - v / maxMem) * (H - PADB - 8)
  const linea = (f, g) => muestras.map(m => `${x(m.t).toFixed(1)},${g(m[f]).toFixed(1)}`).join(' ')
  const u = muestras[muestras.length - 1]
  const pico = Math.max(...muestras.map(m => m.cpu)), picoMem = Math.max(...muestras.map(m => m.rss))
  const alt = `CPU actual ${u.cpu.toFixed(0)}% (${(u.cpu / 100).toFixed(1)} de ${nucleos || '?'} núcleos asignados), pico ${pico.toFixed(0)}%; memoria actual ${u.rss.toFixed(0)} MB, pico ${picoMem.toFixed(0)} MB`
  const marcas = eventos.filter(e => e.ev === 'inicio' || e.ev === 'fin')
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 12, marginBottom: 2 }} role="status" aria-live="off">
        <span style={{ color: '#f97316', fontWeight: 700 }}>CPU {u.cpu.toFixed(0)}% · {(u.cpu / 100).toFixed(1)} de {nucleos || '?'} núcleos{ncpu ? ` (máquina: ${ncpu})` : ''}</span>
        <span style={{ color: '#38bdf8', fontWeight: 700 }}>Memoria {u.rss.toFixed(0)} MB</span>
        {u.cpu_sis != null && <span style={{ color: t.dim || '#94a3b8' }}>sistema: CPU {u.cpu_sis.toFixed(0)}%{u.mem_tot ? ` · RAM ${u.mem_sis.toFixed(0)}/${u.mem_tot.toFixed(0)} MB` : ''}</span>}
        {u.act != null && <span style={{ color: t.dim || '#94a3b8' }}>tareas Spark activas: {u.act}</span>}
        {u.job && <span style={{ color: '#93c5fd' }}>job: {u.job}</span>}
      </div>
      <svg role="img" aria-label={alt} viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', maxWidth: 760, background: '#0b0f14', borderRadius: 8, border: `1px solid ${t.border || '#334155'}` }}>
        <title>{alt}</title>
        <line x1={PADL} y1={yc(100 * (nucleos || 1))} x2={W - 4} y2={yc(100 * (nucleos || 1))} stroke="#7c2d12" strokeDasharray="4 3" />
        <text x={2} y={yc(100 * (nucleos || 1)) + 3} fontSize="9" fill="#fb923c">{100 * (nucleos || 1)}%</text>
        <text x={2} y={H - PADB - 2} fontSize="9" fill="#94a3b8">0</text>
        {marcas.map((e, i) => (e.t >= t0 ? <g key={i}>
          <line x1={x(e.t)} y1={2} x2={x(e.t)} y2={H - PADB} stroke={e.ev === 'inicio' ? '#4ade80' : '#a78bfa'} strokeDasharray="2 3" opacity="0.7" />
          {e.ev === 'inicio' && <text x={x(e.t) + 2} y={10} fontSize="8" fill="#86efac">{String(e.job).slice(0, 14)}</text>}
        </g> : null))}
        <polyline fill="none" stroke="#38bdf8" strokeWidth="1.3" opacity="0.8" points={linea('rss', ym)} />
        <polyline fill="none" stroke="#f97316" strokeWidth="1.6" points={linea('cpu', yc)} />
        <text x={W - 4} y={H - 3} fontSize="9" fill="#94a3b8" textAnchor="end">{span.toFixed(0)} s · naranja: CPU % · azul: memoria (máx {maxMem.toFixed(0)} MB)</text>
      </svg>
    </div>)
}
const filaRec = (r) => r && r.cpu_prom !== undefined
// Tarjetas de "qué falta" (bank_compat): una ROJA por cada componente de una librería del banco que falta o falla
// (con dónde cargarlo y los pasos), y una ÁMBAR con los parches BNX aplicados (no validados contra la salida original).
function TarjetasFaltantes({ t, items }) {
  const lista = Array.isArray(items) ? items : []
  const faltas = lista.filter(f => f.tipo !== 'parcheado')
  const parches = lista.filter(f => f.tipo === 'parcheado')
  if (!lista.length) return null
  const copiar = (txt) => { try { navigator.clipboard.writeText(txt) } catch { /* sin portapapeles */ } }
  return (
    <div role="region" aria-label="Componentes de librerías del banco que faltan o fueron parchados" style={{ display: 'grid', gap: 8, marginBottom: 8 }}>
      {faltas.map((f, i) => (
        <div key={`f${i}`} role="alert" style={{ border: '2px solid #ef4444', background: '#450a0a', borderRadius: 8, padding: '8px 12px' }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <strong style={{ color: '#fecaca', fontSize: 13 }}>⛔ FALTA {f.componente}</strong>
            <span style={{ color: '#fca5a5', fontSize: 12 }}>job <code>{f.job}</code> · librería <code>{f.libreria} {f.version || ''}</code></span>
            <button onClick={() => copiar(f.texto)} aria-label={`Copiar el mensaje de ${f.componente}`}
              style={{ marginLeft: 'auto', fontSize: 11, padding: '2px 8px', borderRadius: 6, border: '1px solid #ef4444', background: 'transparent', color: '#fecaca', cursor: 'pointer' }}>⧉ Copiar</button>
          </div>
          <pre style={{ margin: '6px 0 0', whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 12, color: '#fee2e2', fontFamily: 'ui-monospace, Menlo, Consolas, monospace' }}>{f.texto}</pre>
        </div>))}
      {parches.length > 0 && (
        <details style={{ border: '2px solid #f59e0b', background: '#451a03', borderRadius: 8, padding: '8px 12px' }}>
          <summary style={{ cursor: 'pointer', color: '#fde68a', fontWeight: 700, fontSize: 13 }}>
            ⚠ {parches.length} parche(s) BNX aplicados sobre librerías del banco (NO validado contra la salida original)</summary>
          <ul style={{ margin: '6px 0 0', paddingLeft: 18, fontSize: 12, color: '#fef3c7' }}>
            {parches.map((f, i) => <li key={i}><code>{f.job}</code>: {f.texto}{f.por_que ? ` — ${f.por_que}` : ''}</li>)}
          </ul>
          <div style={{ fontSize: 11.5, color: '#fcd34d', marginTop: 4 }}>Pide al equipo dueño las librerías completas y cárgalas en Framework MLOps v2 → Librerías / Vendor → Banco.</div>
        </details>)}
    </div>)
}
export default function SimularPanel({ t, apiBase, token }) {
  const [info, setInfo] = useState(null)
  const [errorInfo, setErrorInfo] = useState('')
  const [run, setRun] = useState(null)        // {id, estado, duracion, resumen, pasos, ...}
  const [log, setLog] = useState('')
  const [msg, setMsg] = useState('')
  const [copiado, setCopiado] = useState(false)
  const [visor, setVisor] = useState(null)
  const [espacio, setEspacio] = useState(null)   // {total, carpetas, max}: disco que ocupan las simulaciones (venvs)
  const [settings, setSettings] = useState('')
  const [donde, setDonde] = useState(() => { try { return localStorage.getItem('bnx_sim_donde') === 'linux' ? 'linux' : 'mac' } catch { return 'mac' } })
  const [linux, setLinux] = useState(null)      // {podman, maquina_existe, habilitado, razon, gb, preparacion}
  const [prep, setPrep] = useState({ estado: 'idle', log: '' })   // preparación de Linux (en segundo plano)
  const [env, setEnv] = useState('')           // '' = automático (el ambiente con todas las claves)
  const [envsExt, setEnvsExt] = useState(null)   // análisis de la carpeta bin/settings elegida a mano
  const prepOff = useRef(0)
  const prepTimer = useRef(null)
  const offRef = useRef(0)
  const monOff = useRef(0)
  const [mon, setMon] = useState({ muestras: [], eventos: [] })   // monitoreo de recursos en vivo
  const termRef = useRef(null)
  const pegado = useRef(true)               // autoscroll solo si el usuario no subio a leer
  const timer = useRef(null)
  const post = (ruta, body) => fetch(`${apiBase}/mlops/simular/${ruta}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  }).then(async r => { const d = await r.json().catch(() => ({})); if (!r.ok || d.ok === false) throw new Error(d.error || `HTTP ${r.status}`); return d })

  const cargarInfo = useCallback(async () => {
    if (!token) return
    try {
      const r = await fetch(`${apiBase}/mlops/simular/info?token=${encodeURIComponent(token)}&donde=${donde}`)
      const d = await r.json()
      if (!r.ok || d.ok === false) throw new Error(d.error || `HTTP ${r.status}`)
      setInfo(d); setErrorInfo('')
      if (d.linux) setLinux(d.linux)
      // carpeta bin/settings: la recordada para ESTE proyecto o, si no hay, la que trae el paquete (autodetectada)
      let guardada = ''
      try { guardada = localStorage.getItem(`bnx_sim_settings:${d.proyecto || ''}`) || '' } catch { /* sin storage */ }
      setSettings(prev => prev || guardada || d.settings_detectado || '')
    } catch (e) { setInfo(null); setErrorInfo(e.message) }
  }, [apiBase, token, donde])
  const cargarEspacio = useCallback(async () => {
    try {
      const r = await fetch(`${apiBase}/mlops/simular/espacio`)
      const d = await r.json()
      if (r.ok && d.ok !== false) setEspacio(d)
    } catch { /* sin espacio: el boton queda sin tamano */ }
  }, [apiBase])
  useEffect(() => { cargarInfo(); cargarEspacio() }, [cargarInfo, cargarEspacio])
  useEffect(() => () => { clearInterval(timer.current); clearInterval(prepTimer.current) }, [])
  useEffect(() => { try { localStorage.setItem('bnx_sim_donde', donde) } catch { /* sin storage */ } }, [donde])
  const linuxOk = !!(linux && linux.habilitado)
  const sondearPrep = useCallback(() => {
    clearInterval(prepTimer.current)
    const tick = async () => {
      try {
        const r = await fetch(`${apiBase}/mlops/simular/linux?offset=${prepOff.current}`)
        const d = await r.json()
        if (!r.ok || d.ok === false) throw new Error(d.error || `HTTP ${r.status}`)
        setLinux(d)
        const p = d.prep || {}
        prepOff.current = p.offset ?? prepOff.current
        setPrep(x => ({ estado: p.estado || d.preparacion?.estado || 'idle', log: x.log + (p.log || ''), duracion: p.duracion }))
        if (p.terminado) { clearInterval(prepTimer.current); cargarInfo() }
      } catch (e) { clearInterval(prepTimer.current); setMsg('No se pudo leer la preparación de Linux: ' + e.message) }
    }
    prepTimer.current = setInterval(tick, 1500)
    tick()
  }, [apiBase, cargarInfo])
  const prepararLinux = async () => {
    setMsg(''); prepOff.current = 0; setPrep({ estado: 'corriendo', log: '' })
    try { await post('preparar', {}); sondearPrep() } catch (e) { setMsg(e.message); setPrep({ estado: 'idle', log: '' }) }
  }
  useEffect(() => { if (linux && linux.preparacion && linux.preparacion.estado === 'corriendo' && !prepTimer.current) sondearPrep() }, [linux, sondearPrep])

  const sondear = useCallback((id) => {
    clearInterval(timer.current)
    const tick = async () => {
      try {
        const r = await fetch(`${apiBase}/mlops/simular/estado?run=${id}&offset=${offRef.current}&moff=${monOff.current}`)
        const d = await r.json()
        if (!r.ok || d.ok === false) throw new Error(d.error || `HTTP ${r.status}`)
        offRef.current = d.offset
        if (d.monitor) {
          monOff.current = d.monitor_offset
          if (d.monitor.length) setMon(m => ({
            muestras: [...m.muestras, ...d.monitor.filter(x => x.cpu !== undefined)].slice(-1800),
            eventos: [...m.eventos, ...d.monitor.filter(x => x.ev)].slice(-400) }))
        }
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
    setMsg(''); setLog(''); offRef.current = 0; monOff.current = 0; setMon({ muestras: [], eventos: [] }); pegado.current = true
    try {
      const d = await post('iniciar', { token, job: job || 'todos', donde, settings: settings.trim() || undefined, env: env || undefined })
      try { localStorage.setItem(`bnx_sim_settings:${info?.proyecto || ''}`, settings.trim()) } catch { /* sin storage */ }
      setRun({ id: d.run, estado: 'preparando', duracion: 0, resumen: [], pasos: [], plan: [] })
      sondear(d.run)
      setTimeout(() => termRef.current && termRef.current.focus(), 0)
    } catch (e) { setMsg(e.message) }
  }
  const cancelar = async () => {
    try { await post('cancelar', { run: run.id }) } catch (e) { setMsg(e.message) }
  }
  const reiniciar = async () => {
    try { await post('reiniciar', { token, donde }); setMsg('demo_out reiniciado: la próxima simulación empieza limpia.'); cargarInfo() }
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
  const analizarEnvs = async (ruta) => {
    setEnvsExt(null)
    if (!ruta.trim()) return
    try {
      const r = await fetch(`${apiBase}/mlops/simular/envs?path=${encodeURIComponent(ruta.trim())}`)
      const d = await r.json()
      if (!r.ok || d.ok === false) throw new Error(d.error || `HTTP ${r.status}`)
      setEnvsExt(d); setMsg('')
    } catch (e) { setMsg(e.message) }
  }
  const envsInfo = envsExt || info?.envs || null
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
  const visorPost = (accion, body) => post('visor', { token, donde: run?.donde || donde, action: accion, ...body })

  const b = (primary, off) => ({
    padding: '6px 12px', borderRadius: 6, fontSize: 12, fontWeight: 700, cursor: off ? 'not-allowed' : 'pointer',
    opacity: off ? 0.5 : 1,
    background: primary ? '#16a34a' : 'transparent', color: primary ? '#fff' : (t.text || '#e2e8f0'),
    border: `1px solid ${primary ? '#16a34a' : (t.border || '#334155')}`,
  })
  const bloqueado = !info || (donde === 'mac' && !info.soportado) || (donde === 'linux' && !linuxOk) || activo
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
          {donde === 'linux'
            ? <>Dentro del contenedor: <code>bash setup.sh</code> (sin red), <code>python check_env.py</code> y <code>bash run.sh --demo</code>. No hay YARN/Hive/Teradata. El pivote corre primero.</>
            : <>Spark local con datos sintéticos (<code>python main.py --demo</code>). El pivote corre siempre primero.</>}
        </span>
      </div>
      <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', fontSize: 12 }}>
        <label htmlFor="sim-settings" style={{ color: t.muted || '#94a3b8' }}>Carpeta <code>bin/settings</code> del banco (opcional, ruta local):</label>
        <input id="sim-settings" value={settings} onChange={e => setSettings(e.target.value)} onBlur={e => analizarEnvs(e.target.value)} disabled={activo}
          placeholder={info?.settings ? 'el paquete trae settings: se usan' : '/ruta/a/bin/settings (solo lectura; sin ella el demo infiere settings mínimos)'}
          style={{ flex: 1, minWidth: 260, padding: '4px 8px', borderRadius: 6, fontSize: 12, background: t.codeBg || '#081220', color: t.text || '#e2e8f0', border: `1px solid ${t.border || '#334155'}` }} />
      </div>
      <div style={{ marginTop: 8, display: 'flex', gap: 14, alignItems: 'center', flexWrap: 'wrap', fontSize: 12 }}>
        <span style={{ color: t.muted || '#94a3b8', fontWeight: 700 }}>Dónde simular:</span>
        <label style={{ display: 'flex', gap: 5, alignItems: 'center', color: t.text || '#e2e8f0', cursor: activo ? 'not-allowed' : 'pointer' }}>
          <input type="radio" name="sim-donde" checked={donde === 'mac'} disabled={activo} onChange={() => { setDonde('mac'); setLog(''); setRun(null) }} />
          Este equipo (macOS)
        </label>
        <label title={linuxOk ? 'Contenedor RHEL 8 x86_64 (Podman): glibc 2.28, Python 3.11, Java 17; setup.sh sin red' : (linux?.razon || 'Linux no disponible')}
          style={{ display: 'flex', gap: 5, alignItems: 'center', color: linuxOk ? (t.text || '#e2e8f0') : '#64748b', cursor: (activo || !linuxOk) ? 'not-allowed' : 'pointer' }}>
          <input type="radio" name="sim-donde" checked={donde === 'linux'} disabled={activo || !linuxOk} onChange={() => { setDonde('linux'); setLog(''); setRun(null) }} />
          Linux RHEL 8 x86_64 (contenedor)
        </label>
        {linux && !linuxOk && linux.podman && prep.estado !== 'corriendo' && (
          <button onClick={prepararLinux} aria-label="Preparar Linux (una vez)" style={b(true, false)}
            title="Crea la máquina de Podman (4 CPU, 6 GB RAM, 30 GB de disco) y las imágenes RHEL 8; descarga ~1.5 GB">
            Preparar Linux (una vez, ~{linux.gb || 8} GB)</button>)}
        {linux && !linux.podman && <span style={{ color: '#fbbf24' }}>⛔ {linux.razon}</span>}
        {linux && linux.podman && !linuxOk && prep.estado !== 'corriendo' && <span style={{ color: t.dim || '#64748b' }}>{linux.razon}</span>}
        {linuxOk && linux.razon && <span style={{ color: t.dim || '#64748b' }}>{linux.razon}</span>}
      </div>
      {(prep.estado !== 'idle' || prep.log) && (
        <div style={{ marginTop: 6 }}>
          <div role="status" aria-live="polite" style={{ fontSize: 12, fontWeight: 700, color: prep.estado === 'ok' ? '#4ade80' : prep.estado === 'fallo' ? '#f87171' : '#fbbf24' }}>
            Preparación de Linux: {prep.estado === 'corriendo' ? `en curso${prep.duracion ? ` (${fmtSeg(prep.duracion)})` : ''}` : prep.estado === 'ok' ? 'lista' : prep.estado === 'fallo' ? 'falló' : prep.estado}
          </div>
          <pre aria-label="Log de la preparación de Linux" style={{ margin: '4px 0 0', maxHeight: 160, overflow: 'auto', background: '#0b0f14', color: '#d1d5db',
            fontSize: 11, padding: 8, borderRadius: 6, border: `1px solid ${t.border || '#334155'}`, whiteSpace: 'pre-wrap' }}>{prep.log.slice(-6000)}</pre>
        </div>)}
      {envsInfo && envsInfo.envs && envsInfo.envs.length > 0 && (
        <div style={{ marginTop: 6, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', fontSize: 12 }}>
          <label htmlFor="sim-env" style={{ color: t.muted || '#94a3b8' }}>Ambiente de los settings:</label>
          <select id="sim-env" value={env} onChange={e => setEnv(e.target.value)} disabled={activo}
            style={{ padding: '3px 6px', borderRadius: 6, fontSize: 12, background: t.codeBg || '#081220', color: t.text || '#e2e8f0', border: `1px solid ${t.border || '#334155'}` }}>
            <option value="">automático{envsInfo.recomendado ? ` (${envsInfo.recomendado})` : ''}</option>
            {envsInfo.envs.map(e => <option key={e} value={e}>{e}{envsInfo.n && envsInfo.n[e] ? ` — le faltan ${envsInfo.n[e]} clave(s)` : ''}</option>)}
          </select>
          {envsInfo.motivo && <span style={{ color: t.dim || '#64748b' }}>{envsInfo.motivo}</span>}
          {env && envsInfo.n && envsInfo.n[env] > 0 && (
            <span style={{ color: '#fbbf24' }}>⚠ {env} no trae {envsInfo.n[env]} clave(s) que otro ambiente sí (p. ej. {(envsInfo.faltan[env] || [])[0]}); los settings del banco no se modifican.</span>)}
        </div>)}
      {errorInfo && <div role="alert" style={{ marginTop: 8, fontSize: 12, color: '#f87171' }}>⚠ {errorInfo}</div>}
      {info && donde === 'mac' && !info.soportado && (
        <div role="alert" style={{ marginTop: 8, padding: 8, borderRadius: 6, fontSize: 12, color: '#fbbf24', border: '1px solid #f59e0b55' }}>
          ⛔ {info.mensaje}
        </div>)}
      {info && (donde === 'linux' || info.soportado) && (
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
      {info && (donde === 'linux' || (info.soportado && info.mensaje)) && (
        <div style={{ marginTop: 6, fontSize: 11, color: t.dim || '#64748b' }}>
          {donde === 'linux' ? 'Linux (Podman)' : `Java: ${info.mensaje}`} · entorno {info.entorno_listo ? 'ya montado (se reutiliza)' : 'se monta en la primera simulación (setup.sh, una sola vez)'}
          {info.settings_detectado ? ' · el paquete trae bin/settings (se usa por defecto)' : ' · sin bin/settings en el paquete: el demo infiere settings mínimos del código'}
        </div>)}
      {msg && <div role="alert" style={{ marginTop: 8, fontSize: 12, color: '#fbbf24' }}>⚠ {msg}</div>}

      {(run || log) && (
        <div style={{ marginTop: 10 }}>
          {run && run.encabezado && (
            <div style={{ marginBottom: 4, fontSize: 12, fontWeight: 700, color: '#93c5fd' }}>{run.encabezado}</div>)}
          {run && (run.demo_conf || run.env) && (
            <div style={{ marginBottom: 4, fontSize: 12, color: '#93c5fd' }}>{run.demo_conf}{run.env ? ` | ambiente ${run.env}` : ''}</div>)}
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
          {run && <TarjetasFaltantes t={t} items={run.faltantes} />}
          <div ref={termRef} role="log" aria-label="Salida de la simulación" aria-live="off" tabIndex={0} onScroll={onScroll}
            style={{
              background: '#0b0f14', color: '#d1d5db', fontFamily: 'ui-monospace, Menlo, Consolas, monospace', fontSize: 12,
              lineHeight: 1.45, padding: 10, borderRadius: 8, border: `1px solid ${t.border || '#334155'}`,
              height: 340, overflow: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            }}>
            {lineas.map((l, i) => <Linea key={i} texto={l} />)}
            {activo && <span aria-hidden="true" style={{ color: '#4ade80' }}>▌</span>}
          </div>
          <MonitorRecursos t={t} muestras={mon.muestras} eventos={mon.eventos}
            nucleos={mon.muestras.length ? mon.muestras[mon.muestras.length - 1].n : 1}
            ncpu={mon.muestras.length ? mon.muestras[mon.muestras.length - 1].ncpu : null} />
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
                      <td style={{ padding: '2px 10px 2px 0', color: t.dim || '#94a3b8' }}
                        title="CPU promedio / pico (100% = un núcleo) · núcleos promedio · memoria pico · tareas Spark · eficiencia = CPU / (tiempo × núcleos asignados)">
                        {filaRec(r.recursos) ? `CPU ${r.recursos.cpu_prom.toFixed(0)}% (pico ${r.recursos.cpu_pico.toFixed(0)}%) · ${r.recursos.nuc_prom.toFixed(2)} núc. · ${r.recursos.mem_pico.toFixed(0)} MB · ${r.recursos.tareas ?? '—'} tareas · efic. ${r.recursos.eficiencia.toFixed(2)}` : ''}
                      </td>
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
