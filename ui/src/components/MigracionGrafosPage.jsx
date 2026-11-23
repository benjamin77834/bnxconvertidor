import { useState, useEffect, useCallback, useMemo } from 'react'
import { MIGRACION_URL } from '../config'

const NIVEL_COLOR = { Simple: '#22c55e', Medio: '#f59e0b', Alto: '#ef4444' }

// Llamada JSON al backend; mismo manejo de errores que OrquestadorPage
async function call(action, body, query) {
  const post = body !== undefined
  const qs = query ? '?' + new URLSearchParams(query).toString() : ''
  let r
  try {
    r = await fetch(`${MIGRACION_URL}/${action}${qs}`, post ? {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    } : undefined)
  } catch {
    throw new Error('El servidor no respondió (¿se cayó? revisa la terminal de start_server)')
  }
  const txt = await r.text()
  let d = {}
  try { d = txt ? JSON.parse(txt) : {} } catch { d = { error: txt.slice(0, 300) } }
  if (!r.ok || d.ok === false) throw new Error(d.error || `HTTP ${r.status}`)
  return d
}

// Barra de avance de un nivel contra su meta
function Barra({ nivel, info, t }) {
  const dif = info.diferencia
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: t.text }}>
        <span>{nivel}: {info.cantidad} grafos ({info.porcentaje}%)</span>
        <span style={{ color: t.muted }}>meta {info.meta}% · diferencia {dif > 0 ? '+' : ''}{dif} pts</span>
      </div>
      <div style={{ position: 'relative', height: 12, background: t.codeBg, borderRadius: 6 }}>
        <div style={{ width: `${Math.min(100, info.porcentaje)}%`, height: '100%', background: NIVEL_COLOR[nivel], borderRadius: 6 }} />
        <div title={`meta ${info.meta}%`} style={{ position: 'absolute', left: `${info.meta}%`, top: -2, bottom: -2, width: 2, background: t.text }} />
      </div>
    </div>
  )
}

function GrafoCard({ g, meta, personas, t, estilos, onCambio, onError, onIrOrquestador }) {
  const { inp, btn } = estilos
  const [abierto, setAbierto] = useState(false)
  const [estado, setEstado] = useState(g.estado)
  const [notaEstado, setNotaEstado] = useState('')
  const [notaNueva, setNotaNueva] = useState('')
  const [rol, setRol] = useState(meta.roles[0])
  const [nombre, setNombre] = useState('')
  const [correo, setCorreo] = useState('')
  const [notaClasif, setNotaClasif] = useState('')

  useEffect(() => { setEstado(g.estado) }, [g.estado])

  const run = async (action, body) => {
    try { await call(action, { id: g.id, ...body }); onCambio() } catch (e) { onError(e.message) }
  }
  // Autocompletado: si el nombre coincide con una persona ya registrada, se completa el correo
  const alEscribirNombre = (v) => {
    setNombre(v)
    const p = personas.find(x => x.nombre.toLowerCase() === v.toLowerCase())
    if (p) setCorreo(p.correo)
  }
  const color = NIVEL_COLOR[g.nivel]

  return (
    <div style={{ background: t.card, border: `1px solid ${t.border}`, borderLeft: `4px solid ${color}`, borderRadius: 8, padding: 12, marginBottom: 10, color: t.text }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
        <strong style={{ fontSize: 14 }}>{g.archivo}</strong>
        <span style={{ fontSize: 11, color: t.muted }}>{g.tipo}</span>
        <span style={{ background: color, color: '#fff', borderRadius: 10, padding: '1px 10px', fontSize: 12 }}>{g.nivel}</span>
        {g.es_manual && <span style={{ border: `1px solid ${color}`, borderRadius: 10, padding: '0 8px', fontSize: 11 }}>manual</span>}
        {!g.presente && <span style={{ color: '#ef4444', fontSize: 11 }}>ya no está en la carpeta</span>}
        <span style={{ marginLeft: 'auto', fontSize: 12, color: t.muted }}>estado: <b style={{ color: t.text }}>{g.estado}</b></span>
        <button style={btn(false)} onClick={() => setAbierto(a => !a)}>{abierto ? '▾ Ocultar' : '▸ Detalle'}</button>
      </div>
      <div style={{ fontSize: 12, color: t.muted, marginTop: 6 }}>
        Razón: {g.razones.length ? g.razones.join(' · ') : '—'}
      </div>
      <div style={{ fontSize: 12, marginTop: 4 }}>
        <span style={{ color: t.muted }}>Fuente:</span> {g.fuente.join(', ') || '—'} &nbsp;
        <span style={{ color: t.muted }}>Destino:</span> {g.destino.join(', ') || '—'}
      </div>
      <div style={{ fontSize: 12, marginTop: 4 }}>
        <span style={{ color: t.muted }}>Participantes:</span>{' '}
        {g.participantes.length ? g.participantes.map((p, i) => (
          <span key={i} style={{ marginRight: 8 }}>{p.rol}: {p.nombre}</span>
        )) : '—'}
      </div>
      {g.conversion && (
        <div style={{ fontSize: 12, marginTop: 4 }}>
          <span style={{ color: t.muted }}>Conversión:</span> <code>{g.conversion}</code>{' '}
          {onIrOrquestador && <button style={btn(false)} onClick={onIrOrquestador}>Ir al Orquestador</button>}
        </div>
      )}

      {abierto && (
        <div style={{ marginTop: 10, borderTop: `1px solid ${t.border}`, paddingTop: 10, display: 'grid', gap: 12 }}>
          <div>
            <div style={{ fontSize: 12, color: t.muted, marginBottom: 4 }}>Clasificación (automática: {g.clasif.auto.nivel})</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              <input style={{ ...inp, width: 220 }} placeholder="Motivo del cambio (opcional)" value={notaClasif} onChange={e => setNotaClasif(e.target.value)} />
              {meta.niveles.map(n => (
                <button key={n} style={btn(g.es_manual && g.nivel === n)} onClick={() => run('clasificar', { nivel: n, nota: notaClasif })}>{n}</button>
              ))}
              {g.es_manual && <button style={btn(false)} onClick={() => run('clasificar', { nivel: null, nota: notaClasif })}>Volver a automático</button>}
            </div>
            {g.clasif.nota_manual && <div style={{ fontSize: 11, color: t.muted, marginTop: 2 }}>Nota: {g.clasif.nota_manual}</div>}
          </div>

          <div>
            <div style={{ fontSize: 12, color: t.muted, marginBottom: 4 }}>Cambiar estado</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              <select style={inp} value={estado} onChange={e => setEstado(e.target.value)}>
                {meta.estados.map(e => <option key={e} value={e}>{e}</option>)}
              </select>
              <input style={{ ...inp, width: 260 }} placeholder="Nota del cambio" value={notaEstado} onChange={e => setNotaEstado(e.target.value)} />
              <button style={btn(true)} disabled={estado === g.estado}
                onClick={async () => { await run('estado', { estado, nota: notaEstado }); setNotaEstado('') }}>Aplicar</button>
            </div>
            <div style={{ fontSize: 11, color: t.muted, marginTop: 6 }}>Historial</div>
            {g.historial.length === 0 ? <div style={{ fontSize: 12 }}>Sin cambios</div> : g.historial.map((h, i) => (
              <div key={i} style={{ fontSize: 12 }}>{h.fecha} · {h.de} → {h.a}{h.nota ? ` · ${h.nota}` : ''}</div>
            ))}
          </div>

          <div>
            <div style={{ fontSize: 12, color: t.muted, marginBottom: 4 }}>Participantes</div>
            {g.participantes.map((p, i) => (
              <div key={i} style={{ fontSize: 12, display: 'flex', gap: 8, alignItems: 'center', marginBottom: 2 }}>
                <span>{p.rol}: {p.nombre} &lt;{p.correo}&gt;</span>
                <button style={btn(false)} onClick={() => run('quitar', { persona_id: p.persona_id, rol: p.rol })}>Quitar</button>
              </div>
            ))}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 4 }}>
              <select style={inp} value={rol} onChange={e => setRol(e.target.value)}>
                {meta.roles.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
              <input style={inp} list="mig-personas" placeholder="Nombre" value={nombre} onChange={e => alEscribirNombre(e.target.value)} />
              <input style={inp} placeholder="Correo" value={correo} onChange={e => setCorreo(e.target.value)} />
              <button style={btn(true)} disabled={!nombre.trim() || !correo.trim()}
                onClick={async () => { await run('asignar', { rol, nombre, correo }); setNombre(''); setCorreo('') }}>Agregar</button>
            </div>
          </div>

          <div>
            <div style={{ fontSize: 12, color: t.muted, marginBottom: 4 }}>Notas</div>
            {g.notas.map((n, i) => <div key={i} style={{ fontSize: 12 }}>{n.fecha} · {n.texto}</div>)}
            <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
              <input style={{ ...inp, width: 320 }} placeholder="Nueva nota" value={notaNueva} onChange={e => setNotaNueva(e.target.value)} />
              <button style={btn(true)} disabled={!notaNueva.trim()}
                onClick={async () => { await run('nota', { texto: notaNueva }); setNotaNueva('') }}>Agregar nota</button>
            </div>
          </div>
          {g.psets.length > 0 && <div style={{ fontSize: 12 }}><span style={{ color: t.muted }}>Psets:</span> {g.psets.join(', ')}</div>}
        </div>
      )}
    </div>
  )
}

export default function MigracionGrafosPage({ theme: t, onIrOrquestador }) {
  const [meta, setMeta] = useState(null)
  const [lotes, setLotes] = useState([])
  const [carpeta, setCarpeta] = useState('')
  const [lote, setLote] = useState('')
  const [grafos, setGrafos] = useState([])
  const [resumen, setResumen] = useState(null)
  const [personas, setPersonas] = useState([])
  const [fNivel, setFNivel] = useState('')
  const [fEstado, setFEstado] = useState('')
  const [fPersona, setFPersona] = useState('')
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [cargando, setCargando] = useState(false)

  const inp = { background: t.codeBg, color: t.text, border: `1px solid ${t.border}`, borderRadius: 6, padding: '4px 8px', fontSize: 12 }
  const btn = (activo) => ({
    background: activo ? t.accent : t.codeBg, color: activo ? '#fff' : t.text,
    border: `1px solid ${activo ? t.accent : t.border}`, borderRadius: 6, padding: '4px 10px', fontSize: 12, cursor: 'pointer',
  })

  const refrescarLotes = useCallback(async () => {
    const d = await call('lotes')
    setMeta({ estados: d.estados, roles: d.roles, niveles: d.niveles, carpetas: d.carpetas })
    setLotes(d.lotes)
    return d
  }, [])

  const refrescarLote = useCallback(async (id) => {
    if (!id) { setGrafos([]); setResumen(null); return }
    const q = {}
    if (fNivel) q.nivel = fNivel
    if (fEstado) q.estado = fEstado
    if (fPersona) q.persona = fPersona
    const [g, r, p] = await Promise.all([
      call('grafos', undefined, { lote: id, ...q }), call('resumen', undefined, { lote: id }), call('personas'),
    ])
    setGrafos(g.grafos); setResumen(r); setPersonas(p.personas)
  }, [fNivel, fEstado, fPersona])

  const alerta = (e) => setError(e instanceof Error ? e.message : String(e))

  useEffect(() => {
    refrescarLotes().then(d => { if (d.lotes.length) setLote(d.lotes[0].id) }).catch(alerta)
  }, [refrescarLotes])

  useEffect(() => { refrescarLote(lote).catch(alerta) }, [lote, refrescarLote])

  const cargarLote = async () => {
    setError(''); setInfo(''); setCargando(true)
    try {
      const r = await call('cargar', { carpeta })
      const d = await refrescarLotes()
      setLote(r.lote.id)
      setInfo(`Lote cargado: ${r.grafos} grafos (${r.nuevos} nuevos)`)
      if (!d.lotes.length) setLote('')
    } catch (e) { alerta(e) } finally { setCargando(false) }
  }

  const recargar = () => { setError(''); refrescarLote(lote).catch(alerta) }
  const urlExport = (fmt) => `${MIGRACION_URL}/exportar?fmt=${fmt}&lote=${encodeURIComponent(lote)}`
  const personasConGrafos = useMemo(() => personas, [personas])

  if (!meta) {
    return <div style={{ padding: 20, color: t.text }}>{error || 'Cargando…'}</div>
  }
  const estilos = { inp, btn }

  return (
    <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', background: t.bg }}>
    <div style={{ padding: 20, color: t.text, maxWidth: 1200, margin: '0 auto' }}>
      <h2 style={{ margin: '0 0 12px' }}>🚚 Migración de grafos</h2>
      <datalist id="mig-personas">{personas.map(p => <option key={p.id} value={p.nombre} />)}</datalist>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center', marginBottom: 12 }}>
        <select style={inp} value={carpeta} onChange={e => setCarpeta(e.target.value)}>
          <option value="">Carpeta de grafos…</option>
          {meta.carpetas.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <button style={btn(true)} disabled={!carpeta || cargando} onClick={cargarLote}>{cargando ? 'Cargando…' : 'Cargar lote'}</button>
        <span style={{ color: t.muted, fontSize: 12 }}>Lote:</span>
        <select style={inp} value={lote} onChange={e => setLote(e.target.value)}>
          <option value="">—</option>
          {lotes.map(l => <option key={l.id} value={l.id}>{l.nombre}</option>)}
        </select>
        {lote && <>
          <a style={{ ...btn(false), textDecoration: 'none' }} href={urlExport('csv')}>Exportar CSV</a>
          <a style={{ ...btn(false), textDecoration: 'none' }} href={urlExport('xlsx')}>Exportar Excel</a>
        </>}
      </div>
      {info && <div style={{ color: '#22c55e', fontSize: 13, marginBottom: 8 }}>{info}</div>}
      {error && <div style={{ color: '#ef4444', fontSize: 13, marginBottom: 8 }}>⚠ {error}</div>}

      {resumen && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 12, marginBottom: 16 }}>
          <div style={{ background: t.card, border: `1px solid ${t.border}`, borderRadius: 8, padding: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>Complejidad vs meta ({resumen.total} grafos)</div>
            {meta.niveles.map(n => <Barra key={n} nivel={n} info={resumen.niveles[n]} t={t} />)}
          </div>
          <div style={{ background: t.card, border: `1px solid ${t.border}`, borderRadius: 8, padding: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>Estado</div>
            {meta.estados.map(e => (
              <div key={e} style={{ fontSize: 12, display: 'flex', justifyContent: 'space-between' }}>
                <span>{e}</span><span>{resumen.estados[e].cantidad} ({resumen.estados[e].porcentaje}%)</span>
              </div>
            ))}
          </div>
          <div style={{ background: t.card, border: `1px solid ${t.border}`, borderRadius: 8, padding: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>Carga por persona</div>
            {resumen.personas.length === 0 ? <div style={{ fontSize: 12, color: t.muted }}>Sin participantes asignados</div> : (
              <table style={{ fontSize: 12, width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ color: t.muted, textAlign: 'left' }}>
                  <th>Persona</th><th>Roles</th><th>Total</th><th>Abiertos</th>
                </tr></thead>
                <tbody>{resumen.personas.map(p => (
                  <tr key={p.persona_id}>
                    <td>{p.nombre}</td>
                    <td>{Object.entries(p.roles).map(([r, n]) => `${r} ${n}`).join(', ')}</td>
                    <td>{p.total}</td><td>{p.abiertos}</td>
                  </tr>
                ))}</tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {lote && (
        <>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center', marginBottom: 10 }}>
            <span style={{ color: t.muted, fontSize: 12 }}>Filtros:</span>
            <select style={inp} value={fNivel} onChange={e => setFNivel(e.target.value)}>
              <option value="">Todos los niveles</option>
              {meta.niveles.map(n => <option key={n} value={n}>{n}</option>)}
            </select>
            <select style={inp} value={fEstado} onChange={e => setFEstado(e.target.value)}>
              <option value="">Todos los estados</option>
              {meta.estados.map(e => <option key={e} value={e}>{e}</option>)}
            </select>
            <select style={inp} value={fPersona} onChange={e => setFPersona(e.target.value)}>
              <option value="">Todas las personas</option>
              {personasConGrafos.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
            </select>
            <span style={{ color: t.muted, fontSize: 12 }}>{grafos.length} grafos</span>
          </div>
          {grafos.map(g => (
            <GrafoCard key={g.id} g={g} meta={meta} personas={personas} t={t} estilos={estilos}
              onCambio={recargar} onError={setError} onIrOrquestador={onIrOrquestador} />
          ))}
        </>
      )}
    </div>
    </div>
  )
}
