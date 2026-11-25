import { useState, useEffect, useCallback, useRef } from 'react'
import { PRESENTACION_URL } from '../config'

// Llamada JSON al backend; mismo manejo de errores que MigracionGrafosPage
async function call(action, body) {
  let r
  try {
    r = await fetch(`${PRESENTACION_URL}/${action}`, body === undefined ? undefined : {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    })
  } catch {
    throw new Error('El servidor no respondió (¿se cayó? revisa la terminal de start_server)')
  }
  return r
}

async function json(action, body) {
  const r = await call(action, body)
  const txt = await r.text()
  let d = {}
  try { d = txt ? JSON.parse(txt) : {} } catch { d = { error: txt.slice(0, 300) } }
  if (!r.ok || d.ok === false) throw new Error(d.error || `HTTP ${r.status}`)
  return d
}

// Una lámina: las primitivas vienen del servidor (mismo dibujo que el .pptx y el .pdf)
function Lamina({ s, ancho }) {
  const alto = ancho * 540 / 960
  return (
    <svg viewBox="0 0 960 540" width={ancho} height={alto} style={{ background: '#fff', borderRadius: 6, boxShadow: '0 1px 6px rgba(0,0,0,.25)', display: 'block' }}>
      {s.prims.map((p, i) => p.k === 'rect' ? (
        <rect key={i} x={p.x} y={p.y} width={p.w} height={p.h} fill={p.fill} stroke={p.line || 'none'} strokeWidth={p.line ? 0.75 : 0} />
      ) : (
        <foreignObject key={i} x={p.x} y={p.y} width={p.w} height={p.h}>
          <div xmlns="http://www.w3.org/1999/xhtml" style={{
            fontSize: p.size, color: p.color, fontWeight: p.bold ? 700 : 400, textAlign: p.align === 'c' ? 'center' : 'left',
            fontFamily: 'Calibri, Helvetica, Arial, sans-serif', lineHeight: 1.2, overflow: 'hidden', height: '100%',
          }}>
            {p.paras.map((t, j) => <div key={j} style={{ marginBottom: p.bullets ? 6 : 0 }}>{p.bullets ? '• ' : ''}{t}</div>)}
          </div>
        </foreignObject>
      ))}
    </svg>
  )
}

const CAMPOS = [
  ['n_simple', 'Grafos Simple'], ['n_medio', 'Grafos Medio'], ['n_alto', 'Grafos Alto'], ['n_alto_plan', 'Grafos Alto con plan/pset'],
  ['horas_simple', 'Horas por grafo Simple'], ['horas_medio', 'Horas por grafo Medio'],
  ['auto_simple', '% automático Simple'], ['auto_medio', '% automático Medio'], ['auto_alto', '% automático Alto'],
  ['alto_horas', 'Horas Alto con plan/pset (2 sem = 80)'],
  ['alto_sin_plan_horas', 'Horas Alto SIN plan/pset (PENDIENTE DE CONFIRMAR)'],
  ['horas_semana', 'Horas por persona por semana'], ['equipo', 'Personas en el equipo'],
  ['manual_simple', 'Todo manual: h por grafo Simple'], ['manual_medio', 'Todo manual: h por grafo Medio'],
  ['manual_alto', 'Todo manual: h Alto'],
]

export default function PresentacionPage({ theme: t }) {
  const [tipo, setTipo] = useState('grafos')
  const [proyectos, setProyectos] = useState([])
  const [libs, setLibs] = useState(null)
  const [mlops, setMlops] = useState(null)
  const [sel, setSel] = useState([])
  const [fecha, setFecha] = useState('')
  const [params, setParams] = useState({ alto_modo: 'por_grafo' })
  const [vista, setVista] = useState(null)
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)
  const [bajando, setBajando] = useState('')
  const [actualizando, setActualizando] = useState(false)
  const seq = useRef(0)

  const inp = { background: t.codeBg, color: t.text, border: `1px solid ${t.border}`, borderRadius: 6, padding: '4px 8px', fontSize: 12 }
  const btn = (activo) => ({
    background: activo ? t.accent : t.codeBg, color: activo ? '#fff' : t.text,
    border: `1px solid ${activo ? t.accent : t.border}`, borderRadius: 6, padding: '6px 12px', fontSize: 12, cursor: 'pointer',
  })
  const alerta = (e) => setError(e instanceof Error ? e.message : String(e))

  useEffect(() => {
    json('proyectos').then((d) => {
      setProyectos(d.proyectos); setLibs(d.librerias); setFecha(d.fecha_hoy); setMlops(d.mlops)
    }).catch(alerta)
  }, [])

  const cuerpo = useCallback(() => {
    if (tipo === 'mlops') return { tipo, fecha_corte: fecha }
    const p = { alto_modo: params.alto_modo }
    CAMPOS.forEach(([k]) => { if (params[k] !== undefined && params[k] !== '') p[k] = params[k] })
    return { tipo, proyectos: sel, fecha_corte: fecha, params: p }
  }, [tipo, sel, fecha, params])

  const generar = useCallback(async () => {
    if (tipo === 'grafos' && !sel.length) { setVista(null); return }
    const n = ++seq.current
    setCargando(true); setError('')
    try {
      const d = await json('vista', cuerpo())
      if (n === seq.current) setVista(d)
    } catch (e) { if (n === seq.current) { setVista(null); alerta(e) } }
    if (n === seq.current) setCargando(false)
  }, [tipo, sel, cuerpo])

  // Recalcula al cambiar la presentación, los proyectos, la fecha o los parámetros (pausa corta al teclear)
  useEffect(() => { const h = setTimeout(generar, 350); return () => clearTimeout(h) }, [generar, mlops])

  const descargar = async (fmt) => {
    setBajando(fmt); setError('')
    try {
      const r = await call('descargar', { ...cuerpo(), fmt })
      if (!r.ok) {
        let m = `HTTP ${r.status}`
        try { m = (await r.json()).error || m } catch { /* sin cuerpo JSON */ }
        throw new Error(m)
      }
      const blob = await r.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${tipo === 'mlops' ? 'framework_mlops_v2' : 'migracion_grafos_pyspark'}_${fecha}.${fmt}`
      a.click()
      URL.revokeObjectURL(a.href)
    } catch (e) { alerta(e) }
    setBajando('')
  }

  const actualizarMlops = async () => {
    setActualizando(true); setError('')
    try {
      const d = await json('actualizar_mlops', { fuente: (mlops?.fuentes || [])[0] })
      setMlops((m) => ({ ...m, datos: d.datos }))
    } catch (e) { alerta(e) }
    setActualizando(false)
  }

  const alternar = (n) => setSel((s) => (s.includes(n) ? s.filter((x) => x !== n) : [...s, n]))
  const setP = (k, v) => setParams((p) => ({ ...p, [k]: v }))
  const faltan = libs && Object.values(libs).filter((l) => !l.ok)
  const real = vista && vista.tipo === 'grafos' && vista.datos.total.niveles
  const md = mlops && mlops.datos

  return (
    <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', background: t.bg }}>
    <div style={{ padding: 20, color: t.text, maxWidth: 1250 }}>
      <h2 style={{ margin: '0 0 4px' }}>Presentaciones ejecutivas</h2>
      <div style={{ color: t.muted, fontSize: 13, marginBottom: 12 }}>
        Dos presentaciones separadas de 2 láminas cada una. Las cifras salen de los datos reales al generar; lo que falta se muestra como «sin dato». Descarga en PowerPoint o PDF con el mismo contenido.
      </div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        <button style={btn(tipo === 'grafos')} onClick={() => { setTipo('grafos'); setVista(null) }}>Migración de grafos Ab Initio → PySpark</button>
        <button style={btn(tipo === 'mlops')} onClick={() => { setTipo('mlops'); setVista(null) }}>Framework MLOps v2</button>
      </div>
      {error && <div style={{ background: '#7f1d1d', color: '#fff', padding: '8px 12px', borderRadius: 6, marginBottom: 10, fontSize: 13 }}>{error}</div>}
      {faltan && faltan.length > 0 && (
        <div style={{ background: '#78350f', color: '#fff', padding: '8px 12px', borderRadius: 6, marginBottom: 10, fontSize: 13 }}>
          Falta instalar: {faltan.map((l) => l.instalar).join(' ; ')} (en el entorno donde corre el servidor) y reiniciar el servidor.
        </div>
      )}

      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <div style={{ width: 330, flex: '0 0 330px' }}>
          <label style={{ fontSize: 12, display: 'block', marginBottom: 14 }}>Fecha de corte{' '}
            <input type="date" style={inp} value={fecha} onChange={(e) => setFecha(e.target.value)} />
          </label>

          {tipo === 'grafos' ? (
            <>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>Proyectos (output/ y abinitio/)</div>
              <div style={{ maxHeight: 190, overflowY: 'auto', border: `1px solid ${t.border}`, borderRadius: 6, padding: 6, marginBottom: 6 }}>
                {proyectos.map((p) => (
                  <label key={p.nombre} style={{ display: 'flex', gap: 6, fontSize: 12, padding: '2px 0', cursor: 'pointer' }}>
                    <input type="checkbox" checked={sel.includes(p.nombre)} onChange={() => alternar(p.nombre)} />
                    <span>{p.nombre}</span>
                    <span style={{ color: t.muted }}>· {p.grafos_ok} convertidos{p.tiene_abinitio ? '' : ' · sin abinitio/'}</span>
                  </label>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 6, marginBottom: 14 }}>
                <button style={btn(false)} onClick={() => setSel(proyectos.map((p) => p.nombre))}>Todos</button>
                <button style={btn(false)} onClick={() => setSel([])}>Ninguno</button>
              </div>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>Estimación de esfuerzo</div>
              <div style={{ fontSize: 12, marginBottom: 8 }}>
                Las 2 semanas de Alto con plan/pset son:{' '}
                <select style={inp} value={params.alto_modo} onChange={(e) => setP('alto_modo', e.target.value)}>
                  <option value="por_grafo">por grafo</option>
                  <option value="total">total</option>
                </select>
              </div>
              {CAMPOS.map(([k, label]) => (
                <label key={k} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, marginBottom: 4, gap: 6 }}>
                  <span style={k === 'alto_sin_plan_horas' ? { color: '#e8a317', fontWeight: 600 } : undefined}>{label}</span>
                  <input type="number" min="0" step="any" style={{ ...inp, width: 80 }}
                    placeholder={vista && vista.params ? String(vista.params[k]) : ''} value={params[k] ?? ''}
                    onChange={(e) => setP(k, e.target.value)} />
                </label>
              ))}
              <div style={{ color: '#e8a317', fontSize: 11, marginTop: 4 }}>
                Pendiente de confirmar: las horas de un grafo complejo sin plan/pset no están decididas. El valor por defecto (40 h) es un supuesto; las 80 h (2 semanas) aplican solo a los muy complejos con plan/pset.
                {real && ` Hoy: ${real.Alto === 0 ? 'ningún grafo Alto' : `${vista.datos.total.alto_con_plan} Alto con plan/pset, ${vista.datos.total.alto_sin_plan} sin plan/pset, ${vista.datos.total.alto_sin_dato} sin dato`}.`}
              </div>
              <div style={{ color: t.muted, fontSize: 11, marginTop: 4 }}>
                Vacío = valor por defecto (los grafos Simple/Medio/Alto salen de lo convertido: {real ? `${real.Simple}/${real.Medio}/${real.Alto}` : '…'}). Escribe otros números para proyectar al portafolio total.
              </div>
            </>
          ) : (
            <>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>Datos del paquete</div>
              <div style={{ fontSize: 12, marginBottom: 8, color: t.muted }}>
                {md && md.hay_paquete
                  ? `Última medición: ${md.generado || 'sin fecha'} (${md.jobs} jobs).`
                  : 'sin dato: aún no se ha medido el paquete.'}
                {' '}Simulación registrada: {md && md.simulacion ? `${md.simulacion.con_salida} de ${md.simulacion.jobs} jobs (${md.simulacion.fecha})` : 'sin dato'}.
              </div>
              <button style={btn(false)} disabled={actualizando || !(mlops && mlops.fuentes.length)} onClick={actualizarMlops}>
                {actualizando ? 'Armando paquete… (puede tardar 1–2 min)' : 'Actualizar cifras del paquete'}
              </button>
              <div style={{ color: t.muted, fontSize: 11, marginTop: 6 }}>
                Arma los paquetes con y sin PySpark desde {mlops && mlops.fuentes.length ? `mlops22/${mlops.fuentes[0]}` : 'mlops22/ (no hay carpetas)'} en modo lectura, toma jobs, tamaños y estado de las librerías, y borra los ZIP temporales.
              </div>
            </>
          )}

          <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
            <button style={btn(true)} disabled={!vista || !libs?.pptx.ok || !!bajando} onClick={() => descargar('pptx')}>
              {bajando === 'pptx' ? 'Generando…' : 'Descargar PowerPoint'}
            </button>
            <button style={btn(true)} disabled={!vista || !libs?.pdf.ok || !!bajando} onClick={() => descargar('pdf')}>
              {bajando === 'pdf' ? 'Generando…' : 'Descargar PDF'}
            </button>
          </div>
        </div>

        <div style={{ flex: 1, minWidth: 560 }}>
          {tipo === 'grafos' && !sel.length && <div style={{ color: t.muted, fontSize: 13 }}>Elige al menos un proyecto para generar la presentación.</div>}
          {cargando && <div style={{ color: t.muted, fontSize: 12 }}>Calculando…</div>}
          {vista && vista.laminas.map((s) => (
            <div key={s.n} style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 12, color: t.muted, marginBottom: 4 }}>Lámina {s.n} de {vista.laminas.length}: {s.titulo}</div>
              <Lamina s={s} ancho={760} />
            </div>
          ))}
        </div>
      </div>
    </div>
    </div>
  )
}
