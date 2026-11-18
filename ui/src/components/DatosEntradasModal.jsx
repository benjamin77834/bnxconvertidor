import { useState, useEffect, useCallback } from 'react'
import { ORQUESTADOR_URL } from '../config'

const ESTADO = {
  falta: { label: 'falta', color: '#ef4444' },
  sintetico: { label: 'sintético', color: '#f59e0b' },
  propio: { label: 'propio', color: '#22c55e' },
  existente: { label: 'existente', color: '#38bdf8' },
}
const ACCEPT = '.csv,.tsv,.txt,.dat,.json,.jsonl,.ndjson,.parquet,.xlsx'

// Datos de entrada EXTERNOS del plan: ver lo que espera cada job y dar datos sintéticos o PROPIOS
// (archivo subido, ruta local o CSV pegado) que se convierten a parquet en <base>/raw/<nombre>.
export default function DatosEntradasModal({ t, btn, post, file, base, onClose, onCambio, abrirVisor }) {
  const [info, setInfo] = useState(null)       // {base_path, entradas, max_mb}
  const [err, setErr] = useState('')
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)
  const [filas, setFilas] = useState(20)
  const [seed, setSeed] = useState(42)
  const [abierta, setAbierta] = useState(null)   // ruta de la entrada con el panel "Usar mis datos"
  const [modo, setModo] = useState('subir')
  const [ruta, setRuta] = useState('')
  const [texto, setTexto] = useState('')
  const [archivo, setArchivo] = useState(null)
  const [fuente, setFuente] = useState(null)
  const [an, setAn] = useState(null)             // análisis de la fuente
  const [mapeo, setMapeo] = useState({})
  const [cabecera, setCabecera] = useState('auto')
  const [aceptar, setAceptar] = useState(false)
  const input = { ...btn(false), textAlign: 'left', boxSizing: 'border-box' }

  const cargar = useCallback(async () => {
    try {
      const d = await post('datos_estado', { file, ...(base ? { base_path: base } : {}) })
      setInfo(d); setErr('')
    } catch (e) { setErr(e.message) }
  }, [file, base])   // eslint-disable-line
  useEffect(() => { cargar() }, [cargar])
  useEffect(() => {
    const k = (e) => { if (e.key === 'Escape' && !busy) onClose() }
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  }, [busy, onClose])

  const reset = () => { setAn(null); setFuente(null); setMapeo({}); setCabecera('auto'); setAceptar(false); setArchivo(null); setTexto(''); setRuta('') }
  const abrir = (e) => { setAbierta(abierta === e.ruta ? null : e.ruta); reset(); setMsg('') }
  const cab = (c = cabecera) => (c === 'auto' ? {} : { cabecera: c === 'si' })
  const mapeoLimpio = (m) => Object.fromEntries(Object.entries(m).filter(([, v]) => v))

  const sintetico = async (e) => {
    if (e.estado === 'propio' && !window.confirm(`“${e.nombre}” son datos PROPIOS. ¿Reemplazarlos por datos sintéticos?`)) return
    if (e.estado === 'sintetico' && !window.confirm('Ya hay datos sintéticos. ¿Regenerarlos?')) return
    setBusy(true); setMsg('')
    try {
      const d = await post('datos', { file, base_path: info.base_path, filas, seed, solo_rutas: [e.ruta],
        sobrescribir: e.estado !== 'falta', sobrescribir_propios: e.estado === 'propio' })
      const r = d.reporte.find(x => x.ruta === e.ruta)
      setMsg(r ? `${e.nombre}: ${r.estado}${r.filas ? ` · ${r.filas} filas` : ''}${r.motivo ? ` · ${r.motivo}` : ''}` : 'sin cambios')
      await cargar(); onCambio && onCambio()
    } catch (x) { setErr(x.message) }
    setBusy(false)
  }
  const todosLosQueFaltan = async () => {
    const faltan = info.entradas.filter(e => e.estado === 'falta').map(e => e.ruta)
    if (!faltan.length) { setMsg('No falta ninguna entrada.'); return }
    setBusy(true); setMsg('')
    try {
      const d = await post('datos', { file, base_path: info.base_path, filas, seed, solo_rutas: faltan })
      setMsg(`${d.reporte.filter(r => r.estado === 'generado').length} dataset(s) sintético(s) generado(s).`)
      await cargar(); onCambio && onCambio()
    } catch (x) { setErr(x.message) }
    setBusy(false)
  }

  const cuerpoFuente = (f, c) => ({ file, base_path: info.base_path, ruta: abierta, fuente: f, ...cab(c), mapeo: mapeoLimpio(mapeo) })
  const iniciarMapeo = (a) => {
    const m = {}
    a.columnas.forEach(c => {
      const dst = a.validacion.mapeo[c.nombre] || a.validacion.sugerencias[c.nombre]
      if (dst && dst !== c.nombre) m[c.nombre] = dst
    })
    setMapeo(m)
  }
  const analizar = async () => {
    setBusy(true); setErr(''); setMsg('')
    try {
      let f = fuente
      if (modo === 'subir') {
        if (!archivo) throw new Error('Elige un archivo.')
        const q = new URLSearchParams({ file, base_path: info.base_path, ruta: abierta, name: archivo.name })
        let r
        try {
          r = await fetch(`${ORQUESTADOR_URL}/datos_subir?${q}`, { method: 'POST', body: archivo })
        } catch { throw new Error('El servidor no respondió durante la subida') }
        const d = await r.json().catch(() => ({}))
        if (!r.ok) throw new Error(d.error || `HTTP ${r.status}`)
        f = { tipo: 'staging', token: d.token }
        setFuente(f); setAn(d); iniciarMapeo(d)
      } else {
        f = modo === 'ruta' ? { tipo: 'ruta', ruta: ruta.trim() } : { tipo: 'texto', texto }
        const d = await post('datos_analizar', { ...cuerpoFuente(f), mapeo: {} })
        setFuente(f); setAn(d); iniciarMapeo(d)
      }
    } catch (x) { setErr(x.message); setAn(null) }
    setBusy(false)
  }
  const reanalizar = async (m, c) => {
    if (!fuente) return
    try {
      const d = await post('datos_analizar', { ...cuerpoFuente(fuente, c), mapeo: mapeoLimpio(m) })
      setAn(d)
    } catch (x) { setErr(x.message) }
  }
  const importar = async (sobrescribir = false) => {
    setBusy(true); setErr(''); setMsg('')
    try {
      const d = await post('datos_importar', { ...cuerpoFuente(fuente), aceptar_avisos: aceptar, sobrescribir })
      setMsg(`✔ ${d.ruta}: ${d.filas} filas importadas (parquet, motor ${d.motor}). Marcado como propio.`)
      setAbierta(null); reset(); await cargar(); onCambio && onCambio()
    } catch (x) {
      if (x.data?.codigo === 'existe' && window.confirm(`${x.message}\n\n¿Sobrescribir?`)) { setBusy(false); return importar(true) }
      setErr(x.message)
    }
    setBusy(false)
  }

  const falt = an?.validacion?.faltantes || []
  const esperadasNombres = (an?.esperadas || []).map(c => c.name)
  return (
    <div role="dialog" aria-modal="true" aria-labelledby="datos-t"
      style={{ position: 'fixed', inset: 0, background: '#000a', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 60 }}>
      <div style={{ width: 'min(1000px, 96vw)', maxHeight: '92vh', overflow: 'auto', background: t.bg || '#0a1628', color: t.text,
        border: `1px solid ${t.border}`, borderRadius: 10, padding: 14, display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <h3 id="datos-t" style={{ margin: 0, fontSize: 15 }}>🧪 Datos de entrada del plan</h3>
          <button style={{ ...btn(false), marginLeft: 'auto' }} onClick={onClose} disabled={busy}>✕ Cerrar</button>
        </div>
        {info && <div style={{ color: t.muted }}>Base path: <code>{info.base_path}</code> · los jobs leen <code>{'<base>/raw/<nombre>'}</code>.
          Solo se listan las entradas externas (los intermedios los produce el propio plan).</div>}
        {err && <div style={{ color: '#f87171' }}>✖ {err}</div>}
        {msg && <div style={{ color: '#22c55e' }}>{msg}</div>}
        {info && info.entradas.length === 0 && <div style={{ color: t.muted }}>Este plan no tiene entradas externas con job convertido.</div>}
        {info && info.entradas.length > 0 && (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <label>Filas <input type="number" min={1} max={10000} value={filas} style={{ ...input, width: 80 }}
              onChange={e => setFilas(Math.max(1, Math.min(10000, Number(e.target.value) || 20)))} /></label>
            <label>Seed <input type="number" value={seed} style={{ ...input, width: 80 }}
              onChange={e => setSeed(Number(e.target.value) || 0)} /></label>
            <button style={btn(true)} disabled={busy} onClick={todosLosQueFaltan}>🧪 Generar sintético para los que faltan</button>
          </div>)}
        {info?.entradas.map(e => (
          <div key={e.ruta} style={{ border: `1px solid ${t.border}`, borderRadius: 8, padding: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <code style={{ fontWeight: 700 }}>{e.ruta}</code>
              <span style={{ color: ESTADO[e.estado].color, fontWeight: 700 }}>● {ESTADO[e.estado].label}</span>
              <span style={{ color: t.muted }}>paso {e.paso}</span>
              <span style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                <button style={btn(false)} disabled={busy} onClick={() => sintetico(e)}>
                  {e.estado === 'falta' ? 'Generar sintético' : 'Regenerar sintético'}</button>
                <button style={btn(abierta === e.ruta)} disabled={busy} onClick={() => abrir(e)}>📂 Usar mis datos</button>
                {e.estado !== 'falta' && <button style={btn(false)} onClick={() => abrirVisor('raw', e.nombre, info.base_path)}>🔍 Ver</button>}
              </span>
            </div>
            <div style={{ color: t.muted, wordBreak: 'break-word' }}>
              Columnas esperadas{e.nota ? ` (${e.nota})` : ''}: {e.columnas.map(c => `${c.name}:${c.type}`).join(', ')}
            </div>
            {e.detalle?.fuente && <div style={{ color: t.muted }}>
              Origen: {e.detalle.origen}{e.detalle.fuente ? ` · ${e.detalle.fuente}` : ''}{e.detalle.filas != null ? ` · ${e.detalle.filas} filas` : ''}</div>}
            {abierta === e.ruta && (
              <div style={{ borderTop: `1px solid ${t.border}`, paddingTop: 6, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ display: 'flex', gap: 6 }}>
                  {[['subir', '⬆ Subir archivo'], ['ruta', '📁 Ruta local'], ['texto', '📋 Pegar CSV']].map(([k, l]) => (
                    <button key={k} style={btn(modo === k)} onClick={() => { setModo(k); setAn(null); setFuente(null) }}>{l}</button>))}
                </div>
                {modo === 'subir' && <div>
                  <input type="file" accept={ACCEPT} onChange={ev => { setArchivo(ev.target.files[0] || null); setAn(null); setFuente(null) }} />
                  <div style={{ color: t.muted }}>CSV/TSV (separador y encoding utf-8/latin-1 detectados), JSON/JSONL, Parquet o xlsx
                    (xlsx requiere openpyxl en el servidor). Máx. {info.max_mb} MB. Solo desde esta máquina.</div>
                </div>}
                {modo === 'ruta' && <input value={ruta} onChange={ev => { setRuta(ev.target.value); setAn(null); setFuente(null) }}
                  placeholder="/ruta/archivo.csv o carpeta con parquet" style={{ ...input, width: '100%' }} />}
                {modo === 'texto' && <textarea value={texto} rows={5} onChange={ev => { setTexto(ev.target.value); setAn(null); setFuente(null) }}
                  placeholder={'id,nombre,edad\n1,Ana,30'} style={{ ...input, width: '100%', fontFamily: 'monospace', resize: 'vertical' }} />}
                <div><button style={btn(true)} disabled={busy || (modo === 'subir' ? !archivo : modo === 'ruta' ? !ruta.trim() : !texto.trim())}
                  onClick={analizar}>{busy ? 'Procesando…' : 'Analizar y validar'}</button></div>
                {an && an.nombre === e.nombre && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div>{an.formato.toUpperCase()} · {an.total_filas ?? '?'} filas
                      {an.delimitador ? ` · separador ${JSON.stringify(an.delimitador)}` : ''}{an.codificacion ? ` · ${an.codificacion}` : ''}
                      {an.formato === 'csv' && <label style={{ marginLeft: 8 }}>Cabecera{' '}
                        <select value={cabecera} onChange={ev => { setCabecera(ev.target.value); reanalizar(mapeo, ev.target.value) }} style={input}>
                          <option value="auto">auto{an.cabecera != null ? ` (${an.cabecera ? 'sí' : 'no'})` : ''}</option>
                          <option value="si">sí</option><option value="no">no</option></select></label>}
                    </div>
                    {an.avisos_lectura.map((x, i) => <div key={i} style={{ color: '#f59e0b' }}>⚠ {x}</div>)}
                    <table style={{ borderCollapse: 'collapse', fontSize: 11 }}>
                      <thead><tr style={{ textAlign: 'left', color: t.muted }}>
                        <th>Columna del archivo</th><th>Tipo</th><th>Se usará como</th></tr></thead>
                      <tbody>{an.columnas.map(c => (
                        <tr key={c.nombre} style={{ borderTop: `1px solid ${t.border}` }}>
                          <td><code>{c.nombre}</code></td><td>{c.tipo}</td>
                          <td><select aria-label={`Mapeo de ${c.nombre}`} value={mapeo[c.nombre] || (an.validacion.mapeo[c.nombre] || '')} style={input}
                            onChange={ev => { const m = { ...mapeo }; if (ev.target.value) m[c.nombre] = ev.target.value; else delete m[c.nombre]; setMapeo(m); reanalizar(m) }}>
                            <option value="">(no usar / sobrante)</option>
                            {esperadasNombres.map(n => <option key={n} value={n}>{n}</option>)}</select></td>
                        </tr>))}</tbody>
                    </table>
                    {falt.length > 0
                      ? <div style={{ color: '#f87171' }}>✖ Faltan columnas que el job lee: <b>{falt.join(', ')}</b>. Mapéalas arriba o sigue con el aviso.</div>
                      : <div style={{ color: '#22c55e' }}>✔ Todas las columnas esperadas están presentes.</div>}
                    {an.validacion.sobrantes.length > 0 && <div style={{ color: t.muted }}>
                      Sobrantes (se conservan en el parquet): {an.validacion.sobrantes.join(', ')}</div>}
                    {an.validacion.avisos.map((x, i) => <div key={i} style={{ color: '#f59e0b' }}>⚠ {x}</div>)}
                    <div style={{ overflowX: 'auto', maxHeight: 160, border: `1px solid ${t.border}` }}>
                      <table style={{ borderCollapse: 'collapse', fontSize: 11 }}>
                        <thead><tr>{an.columnas.map(c => <th key={c.nombre} style={{ textAlign: 'left', padding: '1px 6px' }}>{c.nombre}</th>)}</tr></thead>
                        <tbody>{an.vista.map((r, i) => (
                          <tr key={i}>{r.map((v, j) => <td key={j} style={{ padding: '1px 6px', whiteSpace: 'nowrap' }}>{v === null ? '∅' : String(v)}</td>)}</tr>))}</tbody>
                      </table>
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      {falt.length > 0 && <label><input type="checkbox" checked={aceptar} onChange={ev => setAceptar(ev.target.checked)} /> seguir aunque falten columnas</label>}
                      <button style={btn(true)} disabled={busy || (falt.length > 0 && !aceptar)} onClick={() => importar(false)}>
                        ✔ Importar como parquet en raw/{e.nombre}</button>
                      {e.estado === 'propio' && <span style={{ color: '#f59e0b' }}>reemplazará tus datos propios (pedirá confirmación)</span>}
                    </div>
                  </div>)}
              </div>)}
          </div>))}
      </div>
    </div>
  )
}
