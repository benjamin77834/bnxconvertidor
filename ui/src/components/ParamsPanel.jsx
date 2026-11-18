import { useState, useEffect } from 'react'

// Tabla de parámetros del pset (del plan o de un paso) con overrides editables.
// Los overrides se guardan en la orquestación (ejecucion.params / step.params) y llegan como
// variables de entorno a los jobs y a los ${PARAM} de los pasos sql/shell.
export default function ParamsPanel({ t, btn, post, file, paso, overrides, onChange, guardarSiHaceFalta, flash }) {
  const [info, setInfo] = useState(null)
  const [nuevo, setNuevo] = useState({ k: '', v: '' })
  const [busy, setBusy] = useState(false)
  useEffect(() => {
    let vivo = true
    setInfo(null)
    post('params', { file, ...(paso ? { paso } : {}) }).then(d => { if (vivo) setInfo(d) }).catch(e => { if (vivo) setInfo({ error: e.message, params: {} }) })
    return () => { vivo = false }
  }, [file, paso])   // eslint-disable-line
  const ov = overrides || {}
  const base = info?.params || {}
  const claves = [...new Set([...Object.keys(base), ...Object.keys(ov)])]
  const cell = { ...btn(false), width: '100%', boxSizing: 'border-box', textAlign: 'left', fontFamily: 'monospace', fontSize: 11 }
  const set = (k, v) => {
    const n = { ...ov }
    if (v === '' || v === undefined) delete n[k]; else n[k] = v
    onChange(n)
  }
  const agregar = () => {
    const k = nuevo.k.trim()
    if (!/^[A-Za-z_]\w*$/.test(k)) { flash('err', 'Nombre de parámetro inválido (letras, números y _).'); return }
    onChange({ ...ov, [k]: nuevo.v })
    setNuevo({ k: '', v: '' })
  }
  const descargar = async () => {
    setBusy(true)
    try {
      await guardarSiHaceFalta()
      const d = await post('pset_exportar', { file, ...(paso ? { paso } : {}) })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(new Blob([d.texto], { type: 'text/plain' }))
      a.download = d.name; a.click(); URL.revokeObjectURL(a.href)
      flash('ok', `.pset editado guardado en ${d.file} (el original no se toca)`)
    } catch (e) { flash('err', e.message) }
    setBusy(false)
  }
  return (
    <div style={{ fontSize: 12, display: 'flex', flexDirection: 'column', gap: 4, color: t.text }}>
      <div style={{ fontWeight: 600 }}>Parámetros{info?.pset ? <> del pset <code>{info.pset}</code></> : ''}</div>
      {info?.error && <div style={{ color: '#f87171' }}>{info.error}</div>}
      {info && !info.pset && <div style={{ color: t.muted }}>
        {paso ? 'Este paso no pertenece a un pset.' : 'Este plan no tiene pset.'} Puedes definir variables igualmente.</div>}
      {info?.pset && !info.archivo && <div style={{ color: '#f59e0b' }}>
        No se encontró {info.pset} en abinitio/&lt;proyecto&gt;: se muestran solo los valores aplicados.</div>}
      {claves.length > 0 && (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead><tr style={{ textAlign: 'left', color: t.muted, fontSize: 10 }}>
            <th>Nombre</th><th>Valor del pset</th><th>Override</th><th /></tr></thead>
          <tbody>{claves.map(k => (
            <tr key={k} style={{ borderTop: `1px solid ${t.border}`, verticalAlign: 'top' }}>
              <td style={{ fontFamily: 'monospace', fontSize: 11, wordBreak: 'break-all' }}>{k}</td>
              <td style={{ color: t.muted, fontFamily: 'monospace', fontSize: 10, wordBreak: 'break-all', maxWidth: 70 }}>
                {k in base ? (base[k] === '' ? '(vacío)' : base[k]) : '—'}</td>
              <td><input aria-label={`Override de ${k}`} value={ov[k] ?? ''} placeholder={k in ov ? '' : '(sin cambio)'}
                onChange={e => set(k, e.target.value)} style={{ ...cell, borderColor: k in ov ? '#a855f7' : undefined }} /></td>
              <td>{k in ov && <button style={{ ...btn(false), padding: '0 4px' }} title="Quitar override"
                onClick={() => set(k, undefined)}>↺</button>}</td>
            </tr>))}</tbody>
        </table>)}
      <div style={{ display: 'flex', gap: 4 }}>
        <input placeholder="NOMBRE" value={nuevo.k} onChange={e => setNuevo({ ...nuevo, k: e.target.value })} style={cell} />
        <input placeholder="valor" value={nuevo.v} onChange={e => setNuevo({ ...nuevo, v: e.target.value })} style={cell} />
        <button style={btn(false)} onClick={agregar}>+</button>
      </div>
      <div style={{ fontSize: 10, color: t.muted }}>
        Los overrides ganan sobre el pset y se exportan como variables de entorno a los jobs y a <code>${'{PARAM}'}</code> de
        los pasos sql/shell. Pulsa “Guardar” para escribirlos en la orquestación.
      </div>
      {info?.pset && info.archivo && (
        <button style={btn(false)} onClick={descargar} disabled={busy}
          title="Genera output/<proyecto>/psets_editados/<pset> con el formato nativo; no toca el original">
          📥 Descargar .pset editado</button>)}
    </div>
  )
}
