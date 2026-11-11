import { useState, useEffect, useCallback, useMemo } from 'react'
import ReactFlow, {
  Background, Controls, MarkerType, Handle, Position,
  useNodesState, useEdgesState,
} from 'reactflow'
import 'reactflow/dist/style.css'

// Orden de las fuentes del Framework MLOps v2 (orden.json del paquete).
// Misma semantica que main.py (_orden_dependencias):
//  - sin depends_on: la fuente va despues de los pivotes (implicito, solo ORDENA)
//  - con depends_on: corre despues de esas y se SALTA si alguna fallo
//  - depends_on: [] = independiente (no espera al pivote)

const esPivoteNombre = (s) => {
  const n = String(s).trim().toLowerCase().replace(/-/g, '_')
  return n === 'pivote' || n === 'pivot' || n.endsWith('_pivote') || n.endsWith('_pivot')
}

// deps efectivas de cada fuente (explicitas o implicitas al pivote)
function efectivas(fuentes, conf) {
  const piv = fuentes.filter(s => conf[s]?.pivot || esPivoteNombre(s))
  const out = {}
  fuentes.forEach(s => {
    if (Array.isArray(conf[s]?.depends_on)) out[s] = { deps: conf[s].depends_on, explicita: true }
    else if (piv.includes(s)) out[s] = { deps: [], explicita: false }
    else out[s] = { deps: piv, explicita: false }
  })
  return { piv, out }
}

// Orden de ejecucion identico a main.py (Kahn estable: pivotes primero, luego orden original)
function ordenEjecucion(fuentes, conf) {
  const { piv, out } = efectivas(fuentes, conf)
  const idx = Object.fromEntries(fuentes.map((s, i) => [s, i]))
  const pend = Object.fromEntries(fuentes.map(s => [s, new Set(out[s].deps).size]))
  const hijos = Object.fromEntries(fuentes.map(s => [s, []]))
  fuentes.forEach(s => new Set(out[s].deps).forEach(d => hijos[d]?.push(s)))
  const clave = (s) => [piv.includes(s) ? 0 : 1, idx[s]]
  const cmp = (a, b) => { const x = clave(a), y = clave(b); return x[0] - y[0] || x[1] - y[1] }
  let listas = fuentes.filter(s => pend[s] === 0).sort(cmp)
  const res = []
  while (listas.length) {
    const s = listas.shift(); res.push(s)
    hijos[s].forEach(h => { pend[h] -= 1; if (pend[h] === 0) listas.push(h) })
    listas.sort(cmp)
  }
  return res.length === fuentes.length ? res : null   // null = ciclo
}

function creaCiclo(conf, fuentes, hacia, desde) {
  // anadir "hacia depende de desde": hay ciclo si desde ya depende (explicito) de hacia
  const { out } = efectivas(fuentes, conf)
  const seen = new Set(); const pila = [desde]
  while (pila.length) {
    const c = pila.pop()
    if (c === hacia) return true
    if (seen.has(c)) continue
    seen.add(c)
    ;(out[c]?.deps || []).forEach(d => pila.push(d))
  }
  return false
}

function FuenteNode({ data }) {
  const t = data.theme
  return (
    <div style={{
      width: 170, padding: '8px 10px', borderRadius: 8, fontSize: 12,
      background: t.card || '#1e2433', color: t.text || '#e2e8f0',
      border: `2px solid ${data.selected ? '#38bdf8' : data.pivote ? '#f59e0b' : (t.border || '#334155')}`,
    }}>
      <Handle type="target" position={Position.Left} />
      <div style={{ fontWeight: 700 }}>{data.pivote ? '⭐ ' : ''}{data.name}</div>
      <div style={{ fontSize: 10, color: t.muted || '#94a3b8' }}>
        #{data.pos} · {data.explicita ? `depende de ${data.deps.length}` : data.pivote ? 'pivote' : 'orden por defecto'}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}
const nodeTypes = { fuente: FuenteNode }

export default function OrdenFuentesPanel({ token, theme, apiBase, onSaved }) {
  const t = theme || {}
  const [fuentes, setFuentes] = useState([])
  const [conf, setConf] = useState({})
  const [dirty, setDirty] = useState(false)
  const [sel, setSel] = useState(null)
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  const btn = (primary) => ({
    padding: '5px 10px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
    background: primary ? (t.accent || '#1a73e8') : 'transparent',
    color: primary ? '#fff' : (t.text || '#e2e8f0'),
    border: `1px solid ${primary ? (t.accent || '#1a73e8') : (t.border || '#334155')}`,
  })

  const call = async (body) => {
    const r = await fetch(`${apiBase}/mlops/package/orden`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, ...body }),
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`)
    return d
  }

  const cargar = useCallback(async () => {
    if (!token) return
    try {
      const d = await call({ action: 'get' })
      setFuentes(d.fuentes || []); setConf(d.orden || {}); setDirty(false); setSel(null)
    } catch (e) { setMsg('⚠ ' + e.message) }
  }, [token])  // eslint-disable-line
  useEffect(() => { cargar() }, [cargar])

  const orden = useMemo(() => ordenEjecucion(fuentes, conf), [fuentes, conf])
  const { piv, out } = useMemo(() => efectivas(fuentes, conf), [fuentes, conf])

  // Layout por niveles (camino mas largo) + aristas explicitas (solidas) e implicitas (punteadas)
  useEffect(() => {
    const memo = {}
    const lvl = (s, seen = new Set()) => {
      if (memo[s] !== undefined) return memo[s]
      if (seen.has(s)) return 0
      seen.add(s)
      const ds = out[s]?.deps || []
      memo[s] = ds.length ? 1 + Math.max(...ds.map(d => lvl(d, seen))) : 0
      return memo[s]
    }
    const cols = {}
    fuentes.forEach(s => { (cols[lvl(s)] ||= []).push(s) })
    const pos = {}
    Object.entries(cols).forEach(([c, ids]) => ids.forEach((id, i) => { pos[id] = { x: Number(c) * 230, y: i * 80 } }))
    setNodes(fuentes.map(s => ({
      id: s, type: 'fuente', position: pos[s],
      data: { name: s, theme: t, pivote: piv.includes(s), explicita: out[s]?.explicita,
              deps: out[s]?.deps || [], selected: s === sel, pos: orden ? orden.indexOf(s) + 1 : '?' },
    })))
    setEdges(fuentes.flatMap(s => (out[s]?.deps || []).map(d => ({
      id: `${d}->${s}`, source: d, target: s,
      deletable: !!out[s]?.explicita,
      markerEnd: { type: MarkerType.ArrowClosed },
      style: out[s]?.explicita ? { stroke: t.text || '#e2e8f0' } : { stroke: '#f59e0b', strokeDasharray: '4 3' },
    }))))
  }, [fuentes, conf, sel, orden, t])  // eslint-disable-line

  const mutar = (fn) => { setConf(prev => { const n = JSON.parse(JSON.stringify(prev)); fn(n); return n }); setDirty(true) }

  const onConnect = useCallback((c) => {
    if (!c.source || !c.target || c.source === c.target) return
    if (creaCiclo(conf, fuentes, c.target, c.source)) { setMsg('⚠ Esa dependencia crearía un ciclo.'); return }
    mutar(n => {
      const x = (n[c.target] ||= {})
      // Al pasar a explicito se conservan los pivotes de los que ya dependia implicitamente
      if (!Array.isArray(x.depends_on)) x.depends_on = [...(out[c.target]?.deps || [])]
      if (!x.depends_on.includes(c.source)) x.depends_on.push(c.source)
    })
  }, [conf, fuentes, out])  // eslint-disable-line

  const onEdgesDelete = useCallback((del) => {
    mutar(n => del.forEach(e => {
      const x = n[e.target]
      if (x && Array.isArray(x.depends_on)) x.depends_on = x.depends_on.filter(d => d !== e.source)
    }))
  }, [])  // eslint-disable-line

  const guardar = async () => {
    if (!orden) { setMsg('⚠ Hay un ciclo: no se puede guardar.'); return }
    setBusy(true)
    try {
      const d = await call({ action: 'save', sources: conf })
      setConf(d.orden || {}); setDirty(false)
      setMsg(d.tiene_orden ? '✅ Guardado en orden.json. Pulsa “Rehacer paquete” para incluirlo en el ZIP.'
                           : '✅ Sin reglas: se usa el orden de siempre (orden.json eliminado). Rehaz el paquete.')
      onSaved && onSaved()
    } catch (e) { setMsg('⚠ No se guardó: ' + e.message) }
    setBusy(false)
  }

  if (!token || !fuentes.length) return null
  const c = sel ? (conf[sel] || {}) : null
  const efSel = sel ? out[sel] : null

  return (
    <div style={{ marginTop: 14, borderTop: `1px solid ${t.border || '#334155'}`, paddingTop: 12 }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0', marginBottom: 4 }}>
        🧭 Orden de las fuentes (quién va primero)
      </div>
      <div style={{ fontSize: 11.5, color: t.muted || '#94a3b8', marginBottom: 8 }}>
        Arrastra del punto derecho de una fuente al izquierdo de otra: la segunda corre después y se salta si la primera falla.
        Punteado naranja = orden por defecto (después del pivote, sin saltarse). Selecciona una flecha sólida y pulsa Supr para quitarla.
      </div>
      <div style={{ display: 'flex', gap: 12 }}>
        <div style={{ flex: 1, height: 300, border: `1px solid ${t.border || '#334155'}`, borderRadius: 8 }}>
          <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes}
            onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
            onConnect={onConnect} onEdgesDelete={onEdgesDelete}
            onNodeClick={(_, n) => setSel(n.id)} onPaneClick={() => setSel(null)}
            deleteKeyCode={['Delete', 'Backspace']} fitView minZoom={0.3}>
            <Background /><Controls />
          </ReactFlow>
        </div>
        <div style={{ width: 240, fontSize: 12, color: t.text || '#e2e8f0', display: 'flex', flexDirection: 'column', gap: 6 }}>
          {!sel && <div style={{ color: t.muted || '#94a3b8' }}>Selecciona una fuente para marcarla como pivote o ajustar de quién depende.</div>}
          {sel && (<>
            <div style={{ fontWeight: 700 }}>{sel}</div>
            <label><input type="checkbox" checked={!!c.pivot || esPivoteNombre(sel)} disabled={esPivoteNombre(sel)}
              onChange={e => mutar(n => { (n[sel] ||= {}).pivot = e.target.checked; if (!e.target.checked) delete n[sel].pivot })} />
              {' '}Pivote (corre primero){esPivoteNombre(sel) ? ' — por nombre' : ''}</label>
            <div style={{ fontWeight: 600 }}>
              {efSel.explicita ? 'Depende de (se salta si fallan):' : 'Orden por defecto: después de'}
            </div>
            {efSel.deps.length === 0 && <div style={{ color: t.muted || '#94a3b8' }}>(nada: puede correr primero)</div>}
            {efSel.deps.map(d => (
              <div key={d} style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>{d}</span>
                {efSel.explicita && <button style={{ ...btn(false), padding: '0 6px' }}
                  onClick={() => mutar(n => { n[sel].depends_on = n[sel].depends_on.filter(x => x !== d) })}>✕</button>}
              </div>))}
            {!piv.includes(sel) && !(Array.isArray(c.depends_on) && c.depends_on.length === 0) &&
              <button style={btn(false)} onClick={() => mutar(n => { (n[sel] ||= {}).depends_on = [] })}>
                Independiente (no espera al pivote)</button>}
            {Array.isArray(c.depends_on) &&
              <button style={btn(false)} onClick={() => mutar(n => { delete n[sel].depends_on; if (!Object.keys(n[sel]).length) delete n[sel] })}>
                Volver al orden por defecto</button>}
          </>)}
        </div>
      </div>
      <div style={{ marginTop: 8, fontSize: 12, color: orden ? (t.text || '#e2e8f0') : '#f87171' }}>
        <b>Orden de ejecución:</b> {orden ? orden.join(' → ') : 'hay un ciclo de dependencias'}
      </div>
      <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <button style={btn(true)} onClick={guardar} disabled={!dirty || busy || !orden}>💾 Guardar orden{dirty ? ' *' : ''}</button>
        <button style={btn(false)} onClick={cargar} disabled={busy}>↺ Descartar</button>
        <button style={btn(false)} onClick={() => { setConf({}); setDirty(true) }} disabled={busy}>Orden de siempre</button>
        {msg && <span style={{ fontSize: 12, color: msg.startsWith('✅') ? '#22c55e' : '#f87171' }}>{msg}</span>}
      </div>
    </div>
  )
}
