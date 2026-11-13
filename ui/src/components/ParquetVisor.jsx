import { useState, useEffect, useRef, useCallback } from 'react'

const PAGINA = 100
const ZONAS = [{ id: 'output', label: 'output' }, { id: 'raw', label: 'raw' }]

const fmtBytes = (n) => (n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(1)} KB` : `${(n / 1048576).toFixed(1)} MB`)

const csvCelda = (v) => {
  if (v === null || v === undefined) return ''
  const s = typeof v === 'object' ? JSON.stringify(v) : String(v)
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

// Visor de datasets parquet/csv de <base>/raw y <base>/output (solo lectura).
// `post` es el helper del orquestador; `inicial` = {zona, nombre} para abrir un dataset directo.
export default function ParquetVisor({ t, btn, post, basePath, inicial, onClose }) {
  const [zona, setZona] = useState(inicial?.zona || 'output')
  const [lista, setLista] = useState(null)       // datasets del base_path
  const [sel, setSel] = useState(inicial?.nombre || null)
  const [datos, setDatos] = useState(null)       // respuesta de leer_parquet
  const [offset, setOffset] = useState(0)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')
  const dlg = useRef(null)
  const previo = useRef(typeof document !== 'undefined' ? document.activeElement : null)
  const reqId = useRef(0)
  const cerrarRef = useRef(onClose)
  cerrarRef.current = onClose

  const cargarLista = useCallback(async () => {
    try {
      const d = await post('datasets', { base_path: basePath })
      setLista(d.datasets || [])
      setError('')
    } catch (e) { setLista([]); setError(e.message) }
  }, [post, basePath])

  const cargarPagina = useCallback(async (z, nombre, off) => {
    if (!nombre) { setDatos(null); return }
    const id = ++reqId.current
    setCargando(true)
    try {
      const d = await post('leer_parquet', { base_path: basePath, zona: z, nombre, limite: PAGINA, offset: off })
      if (id !== reqId.current) return
      setDatos(d); setError('')
    } catch (e) {
      if (id !== reqId.current) return
      setDatos(null); setError(e.message)
    }
    if (id === reqId.current) setCargando(false)
  }, [post, basePath])

  useEffect(() => { cargarLista() }, [cargarLista])
  useEffect(() => { cargarPagina(zona, sel, offset) }, [zona, sel, offset, cargarPagina])

  // foco en el modal, Esc cierra, Tab queda dentro y el foco vuelve al boton que lo abrio
  useEffect(() => {
    dlg.current?.focus()
    const ant = previo.current
    const k = (e) => {
      if (e.key === 'Escape') { e.stopPropagation(); cerrarRef.current(); return }
      if (e.key !== 'Tab' || !dlg.current) return
      const f = dlg.current.querySelectorAll('button:not([disabled]), select, [tabindex="0"]')
      if (!f.length) return
      const a = f[0], z = f[f.length - 1]
      if (e.shiftKey && (document.activeElement === a || document.activeElement === dlg.current)) { e.preventDefault(); z.focus() }
      else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus() }
    }
    window.addEventListener('keydown', k)
    return () => { window.removeEventListener('keydown', k); ant?.focus?.() }
  }, [])

  const elegir = (z, nombre) => { setZona(z); setSel(nombre); setOffset(0) }
  const refrescar = () => { cargarLista(); cargarPagina(zona, sel, offset) }

  const descargarCsv = () => {
    if (!datos) return
    const lineas = [datos.columnas.map(c => csvCelda(c.nombre)).join(',')]
    datos.filas.forEach(f => lineas.push(f.map(csvCelda).join(',')))
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob(['\uFEFF' + lineas.join('\r\n')], { type: 'text/csv;charset=utf-8' }))
    a.download = `${(sel || 'datos').replace(/[^\w.-]+/g, '_')}_${offset + 1}-${offset + datos.filas.length}.csv`
    a.click(); URL.revokeObjectURL(a.href)
  }

  const delaZona = (lista || []).filter(d => d.zona === zona)
  const total = datos?.total_filas
  const hasta = datos ? offset + datos.filas.length : 0
  const haySig = datos && (total == null ? datos.filas.length === PAGINA : hasta < total)
  const muted = t.muted || '#94a3b8'
  const sm = { ...btn(false), padding: '2px 8px', fontSize: 11 }

  return (
    <div style={{ position: 'fixed', inset: 0, background: '#000a', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 60 }}
      onMouseDown={(e) => { if (e.target === e.currentTarget) cerrarRef.current() }}>
      <div ref={dlg} role="dialog" aria-modal="true" aria-labelledby="pq-titulo" tabIndex={-1}
        style={{ width: 'min(1200px, 96vw)', height: 'min(760px, 92vh)', display: 'flex', flexDirection: 'column', gap: 8, padding: 12,
          borderRadius: 10, outline: 'none', background: t.bg || '#0a1628', color: t.text || '#e2e8f0',
          border: `1px solid ${t.border || '#334155'}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <h3 id="pq-titulo" style={{ margin: 0, fontSize: 15 }}>🔍 Ver datos</h3>
          <code style={{ fontSize: 11, color: muted, wordBreak: 'break-all' }}>{basePath}</code>
          <span style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
            <button style={sm} onClick={refrescar} aria-label="Refrescar la lista y los datos">↻ Refrescar</button>
            <button style={sm} onClick={onClose} aria-label="Cerrar el visor de datos">✕ Cerrar</button>
          </span>
        </div>

        <div style={{ display: 'flex', flex: 1, gap: 10, minHeight: 0 }}>
          <div style={{ width: 250, display: 'flex', flexDirection: 'column', gap: 6, minHeight: 0 }}>
            <div role="group" aria-label="Zona" style={{ display: 'flex', gap: 4 }}>
              {ZONAS.map(z => (
                <button key={z.id} style={{ ...sm, flex: 1, ...(zona === z.id ? { background: t.accent || '#1a73e8', color: '#fff' } : {}) }}
                  aria-pressed={zona === z.id} onClick={() => { setZona(z.id); setSel(null); setDatos(null); setOffset(0) }}>
                  {z.label}{lista ? ` (${lista.filter(d => d.zona === z.id).length})` : ''}</button>))}
            </div>
            <ul aria-label={`Datasets de ${zona}`} style={{ listStyle: 'none', margin: 0, padding: 0, overflowY: 'auto', flex: 1,
              border: `1px solid ${t.border || '#334155'}`, borderRadius: 6 }}>
              {lista === null && <li style={{ padding: 8, fontSize: 12, color: muted }}>Cargando…</li>}
              {lista && delaZona.length === 0 && <li style={{ padding: 8, fontSize: 12, color: muted }}>
                No hay datasets en {zona}/.</li>}
              {delaZona.map(d => (
                <li key={d.nombre}>
                  <button onClick={() => elegir(zona, d.nombre)} aria-current={sel === d.nombre ? 'true' : undefined}
                    style={{ display: 'block', width: '100%', textAlign: 'left', padding: '6px 8px', cursor: 'pointer', fontSize: 12,
                      background: sel === d.nombre ? (t.accent || '#1a73e8') + '33' : 'transparent', color: 'inherit',
                      border: 'none', borderBottom: `1px solid ${t.border || '#334155'}` }}>
                    <div style={{ wordBreak: 'break-all', fontWeight: 600 }}>{d.nombre}</div>
                    <div style={{ fontSize: 10, color: muted }}>
                      {d.formato} · {d.archivos} archivo{d.archivos === 1 ? '' : 's'} · {fmtBytes(d.bytes)}
                      {d.modificado ? ` · ${d.modificado.replace('T', ' ')}` : ''}</div>
                  </button>
                </li>))}
            </ul>
          </div>

          <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
            {error && <div role="alert" style={{ color: '#f87171', fontSize: 12 }}>✖ {error}</div>}
            {!sel && !error && <div style={{ color: muted, fontSize: 12 }}>Elige un dataset de la lista.</div>}
            {sel && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', fontSize: 12 }}>
                <strong style={{ wordBreak: 'break-all' }}>{zona}/{sel}</strong>
                {datos && <span style={{ color: muted }}>
                  {datos.filas.length ? `Filas ${offset + 1}–${hasta}` : 'Sin filas'}
                  {total != null ? ` de ${total.toLocaleString()}` : ' (total desconocido)'} · {datos.columnas.length} columnas
                  · {datos.archivos} archivo{datos.archivos === 1 ? '' : 's'} · motor <b>{datos.motor}</b></span>}
                {cargando && <span role="status" style={{ color: muted }}>⏳ leyendo…</span>}
                <span style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                  <button style={sm} disabled={offset === 0 || cargando} aria-label="Página anterior"
                    onClick={() => setOffset(Math.max(0, offset - PAGINA))}>◀ Anterior</button>
                  <button style={sm} disabled={!haySig || cargando} aria-label="Página siguiente"
                    onClick={() => setOffset(offset + PAGINA)}>Siguiente ▶</button>
                  <button style={sm} disabled={!datos || !datos.filas.length} onClick={descargarCsv}
                    aria-label="Descargar como CSV las filas visibles">📥 CSV (visibles)</button>
                </span>
              </div>)}
            {datos && (
              <div style={{ flex: 1, overflow: 'auto', border: `1px solid ${t.border || '#334155'}`, borderRadius: 6 }}>
                <table style={{ borderCollapse: 'collapse', fontSize: 12, minWidth: '100%' }}>
                  <caption style={{ position: 'absolute', left: -9999 }}>Filas de {zona}/{sel}</caption>
                  <thead>
                    <tr>
                      <th scope="col" style={{ position: 'sticky', top: 0, background: t.card || '#1e2433', padding: '4px 8px', textAlign: 'right', color: muted }}>#</th>
                      {datos.columnas.map(c => (
                        <th key={c.nombre} scope="col" title={`${c.nombre} (${c.tipo})`}
                          style={{ position: 'sticky', top: 0, background: t.card || '#1e2433', padding: '4px 8px', textAlign: 'left',
                            whiteSpace: 'nowrap', borderLeft: `1px solid ${t.border || '#334155'}` }}>
                          {c.nombre}<div style={{ fontSize: 10, fontWeight: 400, color: muted }}>{c.tipo}</div>
                        </th>))}
                    </tr>
                  </thead>
                  <tbody>
                    {datos.filas.map((f, i) => (
                      <tr key={offset + i} style={{ borderTop: `1px solid ${t.border || '#334155'}` }}>
                        <th scope="row" style={{ padding: '3px 8px', textAlign: 'right', color: muted, fontWeight: 400 }}>{offset + i + 1}</th>
                        {f.map((v, j) => {
                          const txt = v === null || v === undefined ? null : (typeof v === 'object' ? JSON.stringify(v) : String(v))
                          return (
                            <td key={j} title={txt ?? 'null'}
                              style={{ padding: '3px 8px', maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                                borderLeft: `1px solid ${t.border || '#334155'}`,
                                ...(txt === null ? { color: '#64748b', fontStyle: 'italic' } : {}),
                                ...(typeof v === 'number' ? { textAlign: 'right' } : {}) }}>
                              {txt === null ? 'null' : txt}</td>)
                        })}
                      </tr>))}
                  </tbody>
                </table>
              </div>)}
          </div>
        </div>
      </div>
    </div>
  )
}
