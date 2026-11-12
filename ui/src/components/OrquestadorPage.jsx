import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import ReactFlow, {
  Background, Controls, MiniMap, MarkerType,
  useNodesState, useEdgesState, Handle, Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { ORQUESTADOR_URL } from '../config'

// Colores por estado de la accion del paso
const STATUS_COLOR = {
  ok: '#22c55e',            // tiene .py convertido / script presente
  faltante: '#ef4444',      // referencia un archivo que no esta en la carpeta
  sin_convertir: '#f59e0b', // el grafo existe pero no se convirtio
  no_traducido: '#64748b',  // tarea de programa/script sin traduccion automatica
}

// Ubicacion de ejecucion de cada paso: color / icono / etiqueta
const UBIC = {
  local: { label: 'Local', icon: '🖥️', color: '#3b82f6' },
  remoto: { label: 'Remoto', icon: '🔌', color: '#14b8a6' },
  nube: { label: 'Nube', icon: '☁️', color: '#f97316' },
}

// Tipos de paso y campos de su formulario (kind: text|int|list|kv|json|bool|select|job)
const TIPOS_UI = {
  graph: { label: 'Grafo convertido (*_spark.py)', ubic: 'local', fields: [
    { k: 'target', label: 'Job convertido del proyecto', kind: 'job', req: true }] },
  python: { label: 'Python (.py)', ubic: 'local', fields: [
    { k: 'target', label: 'Script .py', kind: 'text', req: true, ph: 'scripts/mi_script.py' },
    { k: 'args', label: 'Argumentos (uno por línea)', kind: 'list' }] },
  shell: { label: 'Shell / .ksh / .sh', ubic: 'local', fields: [
    { k: 'comando', label: 'Comando o script', kind: 'text', req: true, ph: 'prepara_directorios.ksh arg1' }] },
  spark_submit: { label: 'spark-submit', ubic: 'local', fields: [
    { k: 'target', label: 'Job .py', kind: 'text', req: true, ph: 'output/proy/job_spark.py' },
    { k: 'master', label: 'Master', kind: 'text', ph: 'local[*] / yarn' },
    { k: 'spark_args', label: 'Args de spark-submit (uno por línea)', kind: 'list' },
    { k: 'args', label: 'Argumentos del job (uno por línea)', kind: 'list' }] },
  esperar_archivo: { label: 'Esperar archivo (sensor)', ubic: 'local', fields: [
    { k: 'ruta', label: 'Ruta local (admite *) o s3://bucket/clave', kind: 'text', req: true },
    { k: 'timeout_s', label: 'Timeout (s)', kind: 'int', ph: '300' },
    { k: 'intervalo_s', label: 'Intervalo (s)', kind: 'int', ph: '10' },
    { k: 'profile', label: 'AWS profile (si es s3://)', kind: 'text' },
    { k: 'region', label: 'AWS region (si es s3://)', kind: 'text' }] },
  ssh: { label: 'SSH (comando remoto)', ubic: 'remoto', fields: [
    { k: 'host', label: 'Host', kind: 'text', req: true, ph: 'servidor.empresa.com' },
    { k: 'usuario', label: 'Usuario', kind: 'text' },
    { k: 'puerto', label: 'Puerto', kind: 'int', ph: '22' },
    { k: 'identidad', label: 'Ruta de la clave (nunca su contenido)', kind: 'text', ph: '~/.ssh/id_ed25519' },
    { k: 'comando', label: 'Comando remoto', kind: 'text', req: true }] },
  http: { label: 'HTTP (webhook / API)', ubic: 'remoto', fields: [
    { k: 'metodo', label: 'Método', kind: 'select', opts: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'] },
    { k: 'url', label: 'URL', kind: 'text', req: true, ph: 'https://...' },
    { k: 'body', label: 'Body (JSON)', kind: 'json' },
    { k: 'headers', label: 'Headers sin secretos (clave=valor por línea)', kind: 'kv' },
    { k: 'token_env', label: 'Variable de entorno con el token (nombre)', kind: 'text', ph: 'MI_TOKEN' },
    { k: 'timeout_s', label: 'Timeout (s)', kind: 'int', ph: '30' }] },
  glue_job: { label: 'AWS Glue job', ubic: 'nube', fields: [
    { k: 'job_name', label: 'Nombre del job', kind: 'text', req: true },
    { k: 'args', label: 'Argumentos (--clave=valor por línea)', kind: 'kv' },
    { k: 'profile', label: 'AWS profile', kind: 'text' }, { k: 'region', label: 'AWS region', kind: 'text' }] },
  emr_step: { label: 'AWS EMR step (Spark)', ubic: 'nube', fields: [
    { k: 'cluster_id', label: 'Cluster ID', kind: 'text', req: true, ph: 'j-XXXXXXXX' },
    { k: 'script', label: 'Script en S3', kind: 'text', req: true, ph: 's3://bucket/job.py' },
    { k: 'args', label: 'Argumentos (uno por línea)', kind: 'list' },
    { k: 'nombre', label: 'Nombre del step', kind: 'text' },
    { k: 'action_on_failure', label: 'Si falla', kind: 'select', opts: ['CONTINUE', 'CANCEL_AND_WAIT', 'TERMINATE_CLUSTER'] },
    { k: 'profile', label: 'AWS profile', kind: 'text' }, { k: 'region', label: 'AWS region', kind: 'text' }] },
  lambda: { label: 'AWS Lambda', ubic: 'nube', fields: [
    { k: 'function_name', label: 'Función (nombre o ARN)', kind: 'text', req: true },
    { k: 'payload', label: 'Payload (JSON)', kind: 'json' },
    { k: 'profile', label: 'AWS profile', kind: 'text' }, { k: 'region', label: 'AWS region', kind: 'text' }] },
  s3_copy: { label: 'S3 copiar (aws s3 cp)', ubic: 'nube', fields: [
    { k: 'origen', label: 'Origen (local o s3://)', kind: 'text', req: true },
    { k: 'destino', label: 'Destino (local o s3://)', kind: 'text', req: true },
    { k: 'recursivo', label: 'Recursivo (carpeta)', kind: 'bool' },
    { k: 'profile', label: 'AWS profile', kind: 'text' }, { k: 'region', label: 'AWS region', kind: 'text' }] },
}

const ubicDe = (a) => {
  if (!a) return 'local'
  if (a.type === 'esperar_archivo') return String(a.ruta || '').startsWith('s3://') ? 'nube' : 'local'
  return TIPOS_UI[a.type]?.ubic || 'local'
}

// Texto corto de lo que hace un paso
const resumenAccion = (a) => {
  if (!a) return ''
  const t = a.type
  if (t === 'python' || t === 'spark_submit' || t === 'graph') return (a.target || '').split('/').pop()
  if (t === 'shell') return a.comando
  if (t === 'ssh') return `${a.usuario ? a.usuario + '@' : ''}${a.host}: ${a.comando}`
  if (t === 'http') return `${a.metodo || 'GET'} ${a.url}`
  if (t === 'esperar_archivo') return a.ruta
  if (t === 'glue_job') return a.job_name
  if (t === 'emr_step') return `${a.cluster_id} ${a.script}`
  if (t === 'lambda') return a.function_name
  if (t === 's3_copy') return `${a.origen} → ${a.destino}`
  return ''
}

const campoATexto = (f, v) => {
  if (f.kind === 'bool') return !!v
  if (v === undefined || v === null) return ''
  if (f.kind === 'list') return (v || []).join('\n')
  if (f.kind === 'kv') return Object.entries(v || {}).map(([k, x]) => `${k}=${x}`).join('\n')
  if (f.kind === 'json') return typeof v === 'string' ? v : JSON.stringify(v, null, 2)
  return String(v)
}

// Texto del formulario -> valor del campo (undefined = vacío, no se envía)
const textoACampo = (f, v) => {
  if (f.kind === 'bool') return v ? true : undefined
  const t = String(v ?? '').trim()
  if (!t) return undefined
  if (f.kind === 'int') {
    if (!/^\d+$/.test(t)) throw new Error(`${f.label}: debe ser un entero`)
    return Number(t)
  }
  if (f.kind === 'list') return String(v).split('\n').map(x => x.replace(/\r$/, '')).filter(x => x.trim() !== '')
  if (f.kind === 'kv') {
    const o = {}
    String(v).split('\n').filter(x => x.trim()).forEach(l => {
      const i = l.indexOf('=')
      if (i < 1) throw new Error(`${f.label}: use clave=valor (línea: ${l})`)
      o[l.slice(0, i).trim()] = l.slice(i + 1)
    })
    return o
  }
  if (f.kind === 'json') {
    try { return JSON.parse(t) } catch { throw new Error(`${f.label}: JSON inválido`) }
  }
  return t
}

async function post(path, body) {
  const r = await fetch(`${ORQUESTADOR_URL}/${path}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  })
  const d = await r.json().catch(() => ({}))
  if (!r.ok) throw Object.assign(new Error(d.error || `HTTP ${r.status}`), { data: d })
  return d
}

const EXT_OK = ['.pset', '.plan', '.mp', '.xfr', '.dml', '.ksh', '.dbc']
const extOf = (n) => (n.match(/\.[^.]+$/) || [''])[0].toLowerCase()

// File -> base64 (por trozos: String.fromCharCode con arrays enormes revienta la pila)
async function toB64(file) {
  const buf = new Uint8Array(await file.arrayBuffer())
  let bin = ''
  for (let i = 0; i < buf.length; i += 0x8000) {
    bin += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000))
  }
  return btoa(bin)
}

// Orden en niveles: nivel = camino mas largo desde una raiz (sin dependencias)
function layout(steps) {
  const byId = Object.fromEntries(steps.map(s => [s.id, s]))
  const memo = {}
  const lvl = (id, seen = new Set()) => {
    if (memo[id] !== undefined) return memo[id]
    if (seen.has(id)) return 0
    seen.add(id)
    const deps = (byId[id]?.depends_on || []).filter(d => byId[d])
    memo[id] = deps.length ? 1 + Math.max(...deps.map(d => lvl(d, seen))) : 0
    return memo[id]
  }
  const cols = {}
  steps.forEach(s => { (cols[lvl(s.id)] ||= []).push(s.id) })
  const pos = {}
  Object.entries(cols).forEach(([c, ids]) => ids.forEach((id, i) => {
    pos[id] = { x: Number(c) * 290, y: i * 110 }
  }))
  return pos
}

// true si anadir "step depende de dep" crearia un ciclo
function createsCycle(steps, stepId, depId) {
  if (stepId === depId) return true
  const byId = Object.fromEntries(steps.map(s => [s.id, s]))
  const seen = new Set()
  const stack = [depId]
  while (stack.length) {
    const cur = stack.pop()
    if (cur === stepId) return true
    if (seen.has(cur)) continue
    seen.add(cur)
    ;(byId[cur]?.depends_on || []).forEach(d => stack.push(d))
  }
  return false
}

function StepNode({ data }) {
  const s = data.step
  const color = STATUS_COLOR[s.action?.status] || '#64748b'
  const tgt = s.action?.target ? s.action.target.split(/[\\/]/).pop() : (s.action?.source || '')
  const nuevo = s.action?.type in TIPOS_UI && s.action.type !== 'graph'
  const u = s.action?.type === 'plan' ? null : UBIC[ubicDe(s.action)]
  return (
    <div style={{
      width: 230, padding: '8px 10px', borderRadius: 8,
      background: data.theme.card || '#1e2433', color: data.theme.text || '#e2e8f0',
      border: `2px ${s.solo_en_fallo ? 'dashed' : 'solid'} ${data.selected ? '#38bdf8' : color}`,
      boxShadow: u ? `inset 6px 0 0 ${u.color}` : undefined,
      opacity: s.enabled ? 1 : 0.45, fontSize: 12,
    }}>
      <Handle type="target" position={Position.Left} />
      {u && <div style={{ fontSize: 10, fontWeight: 700, color: u.color }}>{u.icon} {u.label}</div>}
      <div style={{ fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {s.name}
      </div>
      <div style={{ fontSize: 10, color: data.theme.muted || '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {s.action?.type === 'plan'
          ? `${s.id} · 🧩 plan · ${s.action.pasos ?? '?'} pasos${s.action.pset ? ` · pset ${s.action.pset}` : ''}`
          : nuevo ? `${s.id} · ${s.action.type}: ${resumenAccion(s.action)}`
          : `${s.id} · ${s.action?.type}${tgt ? `: ${tgt}` : ''}`}
      </div>
      <div style={{ fontSize: 10, marginTop: 2 }}>
        <span style={{ color }}>● {s.action?.status === 'sin_convertir' ? 'sin convertir' : s.action?.status}</span>
        {s.solo_en_fallo && <span style={{ color: '#fb923c' }}> · solo en fallo</span>}
        {!s.enabled && <span> · deshabilitado</span>}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}
const nodeTypes = { step: StepNode }

// true si el paso 'a' corre antes que 'b' (b depende de a, directa o transitivamente)
function runsBefore(steps, a, b) {
  const byId = Object.fromEntries(steps.map(s => [s.id, s]))
  const seen = new Set()
  const stack = [...(byId[b]?.depends_on || [])]
  while (stack.length) {
    const cur = stack.pop()
    if (cur === a) return true
    if (seen.has(cur)) continue
    seen.add(cur)
    ;(byId[cur]?.depends_on || []).forEach(d => stack.push(d))
  }
  return false
}

// Panel de configuracion de ejecucion (python / spark-submit) y enlaces de datos
function EjecucionPanel({ t, btn, ej, setEj, plan, nameOf, sugerir, addEnlace, toggleEnlace, delEnlace }) {
  const [nuevo, setNuevo] = useState({ desde: '', salida: '', hacia: '', entrada: '' })
  const [argsTxt, setArgsTxt] = useState((ej.spark_args || []).join(' '))
  useEffect(() => { setArgsTxt((ej.spark_args || []).join(' ')) }, [plan.plan])  // eslint-disable-line
  const input = { ...btn(false), width: '100%', boxSizing: 'border-box', textAlign: 'left' }
  const jobs = plan.steps.filter(s => s.action?.type === 'graph' && s.action?.target)
  const ioDe = (id, kind) => (plan.steps.find(s => s.id === id)?.action?.io?.[kind] || []).map(x => x.ruta)
  return (
    <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 6, color: t.text }}>
      <div style={{ fontWeight: 700 }}>Ejecución</div>
      <label>Modo
        <select value={ej.modo || 'python'} onChange={e => setEj('modo', e.target.value)} style={input}>
          <option value="python">python job.py</option>
          <option value="spark-submit">spark-submit</option>
        </select></label>
      {ej.modo === 'spark-submit' && <label>Args de spark-submit
        <input value={argsTxt} onChange={e => setArgsTxt(e.target.value)}
          onBlur={() => setEj('spark_args', argsTxt.trim() ? argsTxt.trim().split(/\s+/) : [])}
          placeholder="--master local[*]" style={input} /></label>}
      <label>Base path (BNX_BASE_PATH)
        <input value={ej.base_path || ''} onChange={e => setEj('base_path', e.target.value)}
          placeholder="/ruta/local o s3://bucket/prefijo" style={input} /></label>
      <div style={{ fontSize: 10, color: t.muted }}>
        Se usa en la ejecución real (terminal) y en el DAG de Airflow. Desde aquí solo hay dry-run.
      </div>

      <div style={{ fontWeight: 700, marginTop: 10 }}>Enlaces de datos</div>
      <div style={{ fontSize: 10, color: t.muted }}>
        Antes del job destino se copia la salida del origen a su entrada.
      </div>
      {(plan.enlaces || []).length === 0 && <div style={{ fontSize: 11, color: t.muted }}>(ninguno)</div>}
      {(plan.enlaces || []).map(e => (
        <div key={e.id} style={{ fontSize: 11, borderTop: `1px solid ${t.border}`, paddingTop: 4, opacity: e.habilitado === false ? 0.5 : 1 }}>
          <div><b>{e.id}</b> {nameOf(e.desde)} → {nameOf(e.hacia)} <span style={{ color: t.muted }}>({e.origen})</span></div>
          <div style={{ color: t.muted, wordBreak: 'break-all' }}>{e.salida} ⇒ {e.entrada}</div>
          <span style={{ display: 'flex', gap: 4 }}>
            <button style={{ ...btn(false), padding: '0 6px' }} onClick={() => toggleEnlace(e.id)}>
              {e.habilitado === false ? 'Habilitar' : 'Deshabilitar'}</button>
            <button style={{ ...btn(false), padding: '0 6px' }} onClick={() => delEnlace(e.id)}>✕</button>
          </span>
        </div>))}
      <button style={btn(false)} onClick={sugerir}>✨ Sugerir por nombre de dataset</button>
      {jobs.length < 2 && <div style={{ fontSize: 10, color: '#f59e0b' }}>
        Hacen falta al menos 2 pasos con job convertido para enlazar.</div>}
      {jobs.length >= 2 && (<>
        <div style={{ fontSize: 11, fontWeight: 600 }}>Nuevo enlace</div>
        <select value={nuevo.desde} onChange={e => setNuevo({ ...nuevo, desde: e.target.value, salida: '' })} style={input}>
          <option value="">Desde (job origen)…</option>
          {jobs.map(s => <option key={s.id} value={s.id}>{s.name} ({s.id})</option>)}
        </select>
        <input list="io-salidas" value={nuevo.salida} onChange={e => setNuevo({ ...nuevo, salida: e.target.value })}
          placeholder="salida, ej. output/op_x" style={input} />
        <datalist id="io-salidas">{ioDe(nuevo.desde, 'escribe').map(r => <option key={r} value={r} />)}</datalist>
        <select value={nuevo.hacia} onChange={e => setNuevo({ ...nuevo, hacia: e.target.value, entrada: '' })} style={input}>
          <option value="">Hacia (job destino)…</option>
          {jobs.filter(s => !nuevo.desde || runsBefore(plan.steps, nuevo.desde, s.id))
            .map(s => <option key={s.id} value={s.id}>{s.name} ({s.id})</option>)}
        </select>
        <input list="io-entradas" value={nuevo.entrada} onChange={e => setNuevo({ ...nuevo, entrada: e.target.value })}
          placeholder="entrada, ej. raw/input_y" style={input} />
        <datalist id="io-entradas">{ioDe(nuevo.hacia, 'lee').map(r => <option key={r} value={r} />)}</datalist>
        <button style={btn(true)} onClick={() => { addEnlace(nuevo); setNuevo({ desde: '', salida: '', hacia: '', entrada: '' }) }}>+ Añadir enlace</button>
      </>)}
    </div>
  )
}

// Guia "Cómo se usa" (pasos 1-6). Cada paso con pestaña tiene un boton para ir a ella.
const PASOS = [
  { n: 1, titulo: 'Subir los archivos', tab: 'imp', ir: 'Ir a Importar',
    texto: 'En "Importar pset / plan": escribe un nombre de proyecto y arrastra JUNTOS el .plan, sus .pset y los .mp de los grafos que el plan ejecuta (y .xfr/.dml/.ksh si los tienes). Pulsa "Subir". El plan no trae los grafos adentro, solo su ruta: si falta el .mp, ese paso saldrá en rojo.' },
  { n: 2, titulo: 'Procesar', tab: 'imp', ir: 'Ir a Importar',
    texto: 'Junto a tu proyecto pulsa "Procesar": genera el mapa de relaciones, convierte cada .mp a PySpark y crea la orquestación del plan. Al terminar te lleva a "Orquestación".' },
  { n: 3, titulo: 'Revisar el resultado', tab: 'orq', ir: 'Ir a Orquestación',
    texto: 'Cada cuadro es una tarea del plan en su orden. Borde verde = job PySpark listo, rojo = falta un archivo, gris = tarea de Ab Initio sin traducción, punteado = solo corre si algo falla. Clic en un paso con job → "Ver código PySpark". En "Mapa pset ↔ grafo" ves qué pset usa cada grafo y qué falta. Si subiste varios planes, todos aparecen en el selector; si un plan tiene sus psets, además hay una variante por pset (plan__pset) con sus parámetros aplicados.' },
  { n: 4, titulo: 'Acomodar el orden (si hace falta)', tab: 'orq', ir: 'Ir a Orquestación',
    texto: 'Arrastra del punto derecho de un paso al izquierdo de otro: el segundo corre después. Para quitar una dependencia, selecciona la flecha y pulsa Supr. En el panel derecho: deshabilitar, "solo si falla", "continuar si falla". "Invertir flechas" si el orden salió al revés. Pulsa "Guardar" (un ciclo se rechaza). Para encadenar VARIOS planes (uno después de otro): "🧩 Plan de planes", marca los planes en orden y pulsa Crear; luego se acomoda igual.' },
  { n: 5, titulo: 'Preparar la ejecución', tab: 'orq', ir: 'Ir a Orquestación',
    texto: 'Sin ningún paso seleccionado, el panel derecho muestra "Ejecución": elige python o spark-submit. Si un job usa la salida de otro, en "Enlaces de datos" pulsa "Sugerir" o créalos. "Datos sintéticos" genera entradas de prueba y deja el base_path listo. "Dry-run" muestra qué correría y en qué orden, sin ejecutar nada.' },
  { n: 6, titulo: 'Ejecutar o llevar a producción', tab: null,
    texto: 'Desde la pantalla solo hay dry-run (por seguridad). Para ejecutar de verdad, en la terminal:', cmd:
      '.venv/bin/python -m src.orquestador ejecutar output/<proyecto>/orquestacion_<plan>.json --ejecutar',
    extra: 'Para Airflow: "DAG Airflow" y descarga el .py del DAG.' },
]

// Crear un "plan de planes": elegir 2+ orquestaciones del proyecto en el orden en que corren.
function ComponerPanel({ t, btn, card, planes, actual, onCreado, onError }) {
  const [orden, setOrden] = useState(() => (actual && !/orquestacion_PLANES_/.test(actual) ? [actual] : []))
  const [nombre, setNombre] = useState('')
  const [cadena, setCadena] = useState(true)
  const [busy, setBusy] = useState(false)
  const etiqueta = (f) => f.split('/').pop().replace(/^orquestacion_/, '').replace(/\.json$/, '')
  const toggle = (f) => setOrden(o => o.includes(f) ? o.filter(x => x !== f) : [...o, f])
  const crear = async () => {
    if (orden.length < 2) { onError('Elige al menos 2 planes.'); return }
    if (!/^[A-Za-z0-9][\w.-]{0,80}$/.test(nombre.trim())) { onError('Escribe un nombre (letras, números, . _ -).'); return }
    setBusy(true)
    try {
      const r = await fetch(`${ORQUESTADOR_URL}/componer`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ planes: orden, nombre: nombre.trim(), cadena }),
      })
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.error || `HTTP ${r.status}`)
      onCreado(d.file)
    } catch (e) { onError(`No se creó: ${e.message}`) }
    setBusy(false)
  }
  return (
    <div style={{ ...card, margin: '0 12px 8px', fontSize: 12 }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>🧩 Nuevo plan de planes</div>
      <div style={{ color: t.muted, marginBottom: 6 }}>
        Marca los planes en el orden en que deben correr (el número indica el orden). Puedes usar el plan base o
        una variante por pset (<code>plan__pset</code>).
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 4, maxHeight: 160, overflowY: 'auto' }}>
        {planes.map(f => (
          <label key={f} style={{ display: 'flex', gap: 6, alignItems: 'center', cursor: 'pointer' }}>
            <input type="checkbox" checked={orden.includes(f)} onChange={() => toggle(f)} />
            <span style={{ width: 18, textAlign: 'right', color: '#38bdf8', fontWeight: 700 }}>
              {orden.includes(f) ? orden.indexOf(f) + 1 : ''}</span>
            <span style={{ wordBreak: 'break-all' }}>{etiqueta(f)}</span>
          </label>))}
        {planes.length < 2 && <div style={{ color: '#f59e0b' }}>Este proyecto tiene menos de 2 planes.</div>}
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 8, flexWrap: 'wrap' }}>
        <input value={nombre} onChange={e => setNombre(e.target.value)} placeholder="Nombre, ej. cierre_mensual"
          style={{ ...btn(false), textAlign: 'left', minWidth: 220 }} />
        <label><input type="checkbox" checked={cadena} onChange={e => setCadena(e.target.checked)} /> En cadena (cada uno espera al anterior)</label>
        <button style={btn(true)} onClick={crear} disabled={busy || orden.length < 2}>Crear</button>
      </div>
    </div>
  )
}

// Crear una orquestacion desde cero (sin .plan)
function NuevaPanel({ t, btn, card, proyectos, proyectoInicial, onCreada, onError }) {
  const [nombre, setNombre] = useState('')
  const [proyecto, setProyecto] = useState(proyectoInicial || '')
  const [busy, setBusy] = useState(false)
  const ok = /^[A-Za-z0-9][\w.-]{0,80}$/.test(nombre.trim()) && /^[A-Za-z0-9][\w.-]{0,63}$/.test(proyecto.trim())
  const crear = async () => {
    setBusy(true)
    try {
      const d = await post('nueva', { nombre: nombre.trim(), proyecto: proyecto.trim() })
      onCreada(d.file)
    } catch (e) { onError(`No se creó: ${e.message}`) }
    setBusy(false)
  }
  const inp = { ...btn(false), textAlign: 'left', minWidth: 200 }
  return (
    <div style={{ ...card, margin: '0 12px 8px', fontSize: 12 }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>✨ Nueva orquestación (desde cero)</div>
      <div style={{ color: t.muted, marginBottom: 6 }}>
        Crea una orquestación vacía en <code>output/&lt;proyecto&gt;/orquestacion_&lt;nombre&gt;.json</code>; después agrega pasos
        (grafos convertidos, scripts, SSH, HTTP, AWS...) en el panel derecho.
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <input value={nombre} onChange={e => setNombre(e.target.value)} placeholder="Nombre, ej. cierre_diario" style={inp} />
        <input list="nueva-proyectos" value={proyecto} onChange={e => setProyecto(e.target.value)}
          placeholder="Proyecto (carpeta en output/)" style={inp} />
        <datalist id="nueva-proyectos">{proyectos.map(p => <option key={p} value={p} />)}</datalist>
        <button style={btn(true)} onClick={crear} disabled={busy || !ok}>Crear</button>
      </div>
    </div>
  )
}

// Formulario para agregar/editar un paso de una orquestacion manual
function PasoForm({ t, btn, plan, inicial, proyecto, onGuardar, onCancelar, onError }) {
  const [tipo, setTipo] = useState(inicial?.action?.type || 'shell')
  const [nombre, setNombre] = useState(inicial?.name || '')
  const [vals, setVals] = useState(() => {
    const v = {}
    const def = TIPOS_UI[inicial?.action?.type]
    ;(def?.fields || []).forEach(f => { v[f.k] = campoATexto(f, inicial.action[f.k]) })
    return v
  })
  const [deps, setDeps] = useState(inicial?.depends_on || [])
  const [jobs, setJobs] = useState([])
  const def = TIPOS_UI[tipo]
  const input = { ...btn(false), width: '100%', boxSizing: 'border-box', textAlign: 'left', fontFamily: 'inherit' }
  useEffect(() => {
    if (tipo !== 'graph' || !proyecto) return
    post('jobs', { proyecto }).then(d => setJobs(d.jobs || [])).catch(() => setJobs([]))
  }, [tipo, proyecto])
  const otros = plan.steps.filter(s => s.id !== inicial?.id)
  const u = UBIC[ubicDe({ type: tipo, ruta: vals.ruta })]
  const guardar = () => {
    try {
      if (!nombre.trim()) throw new Error('Escribe un nombre para el paso.')
      const action = { type: tipo }
      def.fields.forEach(f => {
        const v = textoACampo(f, vals[f.k])
        if (v === undefined && f.req) throw new Error(`Falta: ${f.label}`)
        if (v !== undefined) action[f.k] = v
      })
      onGuardar({ name: nombre.trim(), action, depends_on: deps })
    } catch (e) { onError(e.message) }
  }
  return (
    <div style={{ fontSize: 12, display: 'flex', flexDirection: 'column', gap: 6, color: t.text }}>
      <div style={{ fontWeight: 700, fontSize: 14 }}>{inicial ? `Editar paso ${inicial.id}` : 'Agregar paso'}</div>
      <label>Tipo
        <select value={tipo} disabled={!!inicial} onChange={e => { setTipo(e.target.value); setVals({}) }} style={input}>
          {Object.entries(UBIC).map(([k, ub]) => (
            <optgroup key={k} label={`${ub.icon} ${ub.label}`}>
              {Object.entries(TIPOS_UI).filter(([, d]) => d.ubic === k)
                .map(([tk, d]) => <option key={tk} value={tk}>{d.label}</option>)}
            </optgroup>))}
        </select></label>
      <div style={{ color: u.color, fontWeight: 700 }}>{u.icon} Se ejecuta: {u.label}</div>
      <label>Nombre del paso
        <input value={nombre} onChange={e => setNombre(e.target.value)} style={input} /></label>
      {def.fields.map(f => (
        <label key={f.k}>{f.label}{f.req ? ' *' : ''}
          {f.kind === 'bool' ? (
            <input type="checkbox" checked={!!vals[f.k]} style={{ marginLeft: 6 }}
              onChange={e => setVals({ ...vals, [f.k]: e.target.checked })} />
          ) : f.kind === 'select' ? (
            <select value={vals[f.k] || f.opts[0]} onChange={e => setVals({ ...vals, [f.k]: e.target.value })} style={input}>
              {f.opts.map(o => <option key={o} value={o}>{o}</option>)}</select>
          ) : f.kind === 'job' ? (<>
            <input list="paso-jobs" value={vals[f.k] || ''} onChange={e => setVals({ ...vals, [f.k]: e.target.value })}
              placeholder={jobs.length ? 'Elige un *_spark.py' : 'output/<proyecto>/<grafo>_spark.py'} style={input} />
            <datalist id="paso-jobs">{jobs.map(j => <option key={j} value={j} />)}</datalist>
            {!jobs.length && <div style={{ fontSize: 10, color: '#f59e0b' }}>
              No hay *_spark.py en output/{proyecto || '<proyecto>'}. Procesa el .mp en "Importar" primero.</div>}
          </>) : (f.kind === 'list' || f.kind === 'kv' || f.kind === 'json') ? (
            <textarea value={vals[f.k] || ''} rows={3} onChange={e => setVals({ ...vals, [f.k]: e.target.value })}
              placeholder={f.ph} style={{ ...input, resize: 'vertical' }} />
          ) : (
            <input value={vals[f.k] ?? ''} onChange={e => setVals({ ...vals, [f.k]: e.target.value })}
              placeholder={f.ph} style={input} />)}
        </label>))}
      {tipo === 'ssh' && <div style={{ fontSize: 10, color: t.muted }}>Usa tu clave / ssh-agent (BatchMode). No se guardan contraseñas.</div>}
      {tipo === 'http' && <div style={{ fontSize: 10, color: t.muted }}>El token se lee de la variable de entorno al ejecutar; no se guarda en el JSON.</div>}
      {def.ubic === 'nube' && <div style={{ fontSize: 10, color: t.muted }}>Usa la CLI <code>aws</code> con tus credenciales; profile/region vacíos toman los de Ejecución.</div>}
      <div style={{ fontWeight: 600 }}>Corre después de:</div>
      {otros.length === 0 && <div style={{ color: t.muted }}>(no hay otros pasos)</div>}
      {otros.map(s => {
        const ciclo = inicial && createsCycle(plan.steps, inicial.id, s.id)
        return (
          <label key={s.id} style={{ opacity: ciclo ? 0.4 : 1 }}>
            <input type="checkbox" disabled={ciclo} checked={deps.includes(s.id)}
              onChange={e => setDeps(e.target.checked ? [...deps, s.id] : deps.filter(x => x !== s.id))} /> {s.name} <span style={{ color: t.muted }}>({s.id})</span>
          </label>)
      })}
      <div style={{ display: 'flex', gap: 6 }}>
        <button style={btn(true)} onClick={guardar}>{inicial ? 'Aplicar' : 'Agregar'}</button>
        <button style={btn(false)} onClick={onCancelar}>Cancelar</button>
      </div>
      <div style={{ fontSize: 10, color: t.muted }}>Aplica al diagrama; pulsa “Guardar” arriba para escribirlo al archivo.</div>
    </div>
  )
}

function GuiaUso({ t, btn, irA, cerrar }) {
  return (
    <section id="orq-ayuda" aria-label="Cómo se usa el Orquestador"
      style={{ margin: '10px 16px 0', padding: 12, borderRadius: 10, background: t.card || '#152a52',
               border: `1px solid ${t.border || '#1e3a6e'}`, color: t.text || '#e8edf5', maxHeight: '45vh', overflowY: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <h3 style={{ margin: 0, fontSize: 14 }}>❓ Cómo se usa el Orquestador</h3>
        <span style={{ fontSize: 11, color: t.muted || '#8fa3c4' }}>
          Prueba rápida: abre el proyecto <code>demo_plan_pset_mp</code> (ya procesado) y sigue desde el paso 3.
        </span>
        <button style={{ ...btn(false), marginLeft: 'auto', padding: '2px 8px' }} onClick={cerrar}
          aria-label="Cerrar la guía">✕</button>
      </div>
      <ol style={{ margin: 0, paddingLeft: 0, listStyle: 'none', display: 'grid',
                   gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 8 }}>
        {PASOS.map(p => (
          <li key={p.n} style={{ border: `1px solid ${t.border || '#1e3a6e'}`, borderRadius: 8, padding: 10, fontSize: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <span aria-hidden="true" style={{ width: 22, height: 22, borderRadius: 11, display: 'inline-flex',
                alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 12,
                background: t.accent || '#1a73e8', color: '#fff' }}>{p.n}</span>
              <strong>{p.titulo}</strong>
            </div>
            <p style={{ margin: '0 0 6px', lineHeight: 1.45, color: t.muted || '#8fa3c4' }}>{p.texto}</p>
            {p.cmd && <pre style={{ margin: '0 0 6px', padding: 6, borderRadius: 6, fontSize: 10.5, whiteSpace: 'pre-wrap',
              wordBreak: 'break-all', background: t.codeBg || '#081220' }}>{p.cmd}</pre>}
            {p.extra && <p style={{ margin: '0 0 6px', color: t.muted || '#8fa3c4' }}>{p.extra}</p>}
            {p.tab && <button style={{ ...btn(false), padding: '2px 8px', fontSize: 11 }} onClick={() => irA(p.tab)}>{p.ir} →</button>}
          </li>
        ))}
      </ol>
    </section>
  )
}

export default function OrquestadorPage({ theme }) {
  const t = theme || {}
  const [tab, setTab] = useState('orq')
  // Guia de uso: abierta la primera vez; luego se recuerda si el usuario la cerro.
  const [ayuda, setAyuda] = useState(() => {
    try { return localStorage.getItem('bnx_orq_ayuda') !== '0' } catch { return true }
  })
  const toggleAyuda = (v) => setAyuda(prev => {
    const n = typeof v === 'boolean' ? v : !prev
    try { localStorage.setItem('bnx_orq_ayuda', n ? '1' : '0') } catch { /* sin storage */ }
    return n
  })
  const [files, setFiles] = useState([])
  const [maps, setMaps] = useState([])
  const [file, setFile] = useState('')
  const [plan, setPlan] = useState(null)       // plan en edicion
  const [dirty, setDirty] = useState(false)
  const [selId, setSelId] = useState(null)
  const [msg, setMsg] = useState(null)         // {kind:'ok'|'err', text}
  const [dry, setDry] = useState(null)         // salida del dry-run
  const [busy, setBusy] = useState(false)
  const [pmap, setPmap] = useState(null)
  const [mapFile, setMapFile] = useState('')
  const [projects, setProjects] = useState([])
  const [projName, setProjName] = useState('')
  const [picked, setPicked] = useState([])      // File[] elegidos para subir
  const [upState, setUpState] = useState(null)  // {done,total,current}
  const [procLog, setProcLog] = useState(null)  // {ok, log}
  const [processing, setProcessing] = useState(false)
  const [code, setCode] = useState(null)      // {name,size,truncated,code}
  const [componiendo, setComponiendo] = useState(false)   // panel "Plan de planes"
  const [creando, setCreando] = useState(false)           // panel "Nueva orquestación"
  const [form, setForm] = useState(null)                  // formulario de paso: {id?} (manual)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  const card = { background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`, borderRadius: 10, padding: 12 }
  const btn = (primary) => ({
    padding: '6px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
    background: primary ? (t.accent || '#1a73e8') : 'transparent',
    color: primary ? '#fff' : (t.text || '#e2e8f0'),
    border: `1px solid ${primary ? (t.accent || '#1a73e8') : (t.border || '#334155')}`,
  })
  const flash = (kind, text) => { setMsg({ kind, text }); setTimeout(() => setMsg(null), 6000) }

  // ---- carga ----
  const loadList = useCallback(async () => {
    try {
      const d = await post('list')
      setFiles(d.plans || []); setMaps(d.maps || [])
      if (d.plans?.length && !file) setFile(d.plans[0])
      setProjects((await post('projects')).projects || [])
    } catch (e) { flash('err', `No se pudo listar: ${e.message}`) }
  }, [file])
  useEffect(() => { loadList() }, [])  // eslint-disable-line

  const loadPlan = useCallback(async (f) => {
    if (!f) return
    try {
      const d = await post('get', { file: f })
      setPlan(d.plan); setDirty(false); setSelId(null); setDry(null)
      if (d.plan._warning) flash('err', d.plan._warning)
    } catch (e) { flash('err', e.message) }
  }, [])
  useEffect(() => { loadPlan(file) }, [file, loadPlan])

  useEffect(() => {
    if (tab !== 'map' || !maps.length) return
    const f = maps.includes(mapFile) ? mapFile : maps[0]
    post('map', { file: f }).then(setPmap).catch(e => flash('err', e.message))
  }, [tab, maps, mapFile])

  // ---- plan -> nodos/aristas ----
  const relayout = useCallback((p) => {
    const pos = layout(p.steps)
    setNodes(p.steps.map(s => ({
      id: s.id, type: 'step', position: pos[s.id] || { x: 0, y: 0 },
      data: { step: s, theme: t, selected: false },
    })))
  }, [setNodes, t])

  useEffect(() => { if (plan) relayout(plan) }, [file, plan?.plan])  // eslint-disable-line

  // ---- encuadre automatico: mostrar SIEMPRE todos los pasos ----
  const [rf, setRf] = useState(null)         // instancia de ReactFlow (onInit)
  const lienzoRef = useRef(null)
  const verTodo = useCallback(() => {
    if (!rf) return
    // doble rAF: esperar a que React pinte los nodos y el layout cambie de tamaño
    requestAnimationFrame(() => requestAnimationFrame(() => rf.fitView({ padding: 0.15, duration: 250 })))
  }, [rf])
  // al cambiar de plan, al (re)acomodar y al abrir/cerrar paneles que cambian el alto
  useEffect(() => { verTodo() }, [verTodo, file, nodes.length, !!code, !!dry, ayuda, tab])  // eslint-disable-line
  // al cambiar el tamaño del lienzo (ventana, paneles laterales)
  useEffect(() => {
    const el = lienzoRef.current
    if (!el || typeof ResizeObserver === 'undefined') return
    let timer = null
    const ro = new ResizeObserver(() => { clearTimeout(timer); timer = setTimeout(verTodo, 120) })
    ro.observe(el)
    return () => { ro.disconnect(); clearTimeout(timer) }
  }, [verTodo, tab])

  // Mantener datos/aristas sincronizados con el plan sin mover posiciones
  useEffect(() => {
    if (!plan) return
    setNodes(prev => {
      const have = new Set(prev.map(n => n.id))
      if (plan.steps.length !== prev.length || plan.steps.some(s => !have.has(s.id))) return prev
      const byId = Object.fromEntries(plan.steps.map(s => [s.id, s]))
      return prev.map(n => ({ ...n, data: { step: byId[n.id], theme: t, selected: n.id === selId } }))
    })
    setEdges(plan.steps.flatMap(s => s.depends_on.map(d => {
      const fl = s.dep_flags?.[d]
      return {
        id: `${d}->${s.id}`, source: d, target: s.id,
        label: fl ? `flag ${fl}` : undefined,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: t.muted || '#94a3b8' },
        labelStyle: { fontSize: 10 },
      }
    })).concat((plan.enlaces || []).filter(e => e.habilitado !== false).map(e => ({
      // Enlaces de datos: punteados en violeta. No se borran con Supr (id 'enlace:')
      id: `enlace:${e.id}`, source: e.desde, target: e.hacia, deletable: false,
      label: `📦 ${e.salida.split('/').pop()}`, animated: true,
      style: { stroke: '#a855f7', strokeDasharray: '4 3' }, labelStyle: { fontSize: 10, fill: '#a855f7' },
    }))))
  }, [plan, selId, t, setNodes, setEdges])

  // Quitar una dependencia puede dejar enlaces invalidos: tambien se limpian
  const limpiarEnlaces = (p) => {
    const before = (p.enlaces || []).length
    p.enlaces = (p.enlaces || []).filter(e => runsBefore(p.steps, e.desde, e.hacia))
    if (p.enlaces.length !== before) flash('err', `${before - p.enlaces.length} enlace(s) quitados: su destino ya no corre después del origen`)
  }

  const mutate = (fn) => {
    setPlan(prev => {
      const next = JSON.parse(JSON.stringify(prev))
      fn(next)
      return next
    })
    setDirty(true)
  }

  // ---- interacciones ----
  const onConnect = useCallback((c) => {
    if (!plan || !c.source || !c.target) return
    if (plan.steps.find(s => s.id === c.target)?.depends_on.includes(c.source)) return
    if (createsCycle(plan.steps, c.target, c.source)) {
      flash('err', 'Esa dependencia crearia un ciclo: no se agrego.')
      return
    }
    mutate(p => { p.steps.find(s => s.id === c.target).depends_on.push(c.source) })
  }, [plan])  // eslint-disable-line

  const onEdgesDelete = useCallback((del) => {
    del = del.filter(e => !String(e.id).startsWith('enlace:'))  // los enlaces se quitan desde el panel
    if (!del.length) return
    mutate(p => {
      del.forEach(e => {
        const s = p.steps.find(x => x.id === e.target)
        if (s) {
          s.depends_on = s.depends_on.filter(d => d !== e.source)
          if (s.dep_flags) delete s.dep_flags[e.source]
        }
      })
      limpiarEnlaces(p)
    })
  }, [])  // eslint-disable-line

  const invertir = () => mutate(p => {
    const rev = {}
    p.steps.forEach(s => s.depends_on.forEach(d => { (rev[d] ||= []).push(s.id) }))
    p.steps.forEach(s => { s.depends_on = rev[s.id] || []; s.dep_flags = {} })
    p.direccion = p.direccion === 'inversa' ? 'prior' : 'inversa'
    limpiarEnlaces(p)  // los enlaces dependen del orden
  })

  // ---- ejecucion (spark-submit) / enlaces / airflow ----
  const ej = plan?.ejecucion || { modo: 'python', base_path: '', spark_args: [] }
  const setEj = (k, v) => mutate(p => { p.ejecucion = { ...(p.ejecucion || {}), [k]: v } })

  const sugerir = async () => {
    try {
      const d = await post('sugerir', { file, plan })
      const nuevos = d.enlaces.length - (plan.enlaces || []).length
      mutate(p => { p.enlaces = d.enlaces })
      flash('ok', nuevos > 0 ? `${nuevos} enlace(s) sugeridos (falta Guardar)` : 'No hay enlaces nuevos por nombre de dataset.')
    } catch (e) { flash('err', e.message) }
  }

  const addEnlace = (e) => {
    if (!e.desde || !e.hacia || !e.salida || !e.entrada) { flash('err', 'Completa los 4 campos del enlace.'); return }
    if (!runsBefore(plan.steps, e.desde, e.hacia)) { flash('err', 'El paso destino debe correr después del origen.'); return }
    mutate(p => {
      const n = Math.max(0, ...(p.enlaces || []).map(x => Number(String(x.id).replace(/\D/g, '')) || 0)) + 1
      p.enlaces = [...(p.enlaces || []), { id: `e${n}`, ...e, origen: 'manual', habilitado: true }]
    })
  }

  const datosSinteticos = async () => {
    const txt = window.prompt('Filas por dataset de entrada (1-10000):', '20')
    if (txt === null) return
    const filas = Math.max(1, Math.min(10000, parseInt(txt, 10) || 20))
    setBusy(true)
    try {
      if (dirty) { await post('save', { file, plan }); setDirty(false) }
      let d = await post('datos', { file, filas })
      if (d.reporte.some(r => r.estado === 'existe') &&
          window.confirm('Algunos datasets ya existen. ¿Regenerarlos (se sobrescriben)?')) {
        d = await post('datos', { file, filas, sobrescribir: true })
      }
      const icon = { generado: '✔', existe: '•', omitido: '–', error: '✖' }
      const lineas = d.reporte.map(r => `${icon[r.estado] || '?'} [${r.estado}] ${r.paso} ${r.ruta}` +
        (r.filas ? ` · ${r.filas} filas · ${r.columnas.join(', ')}` : '') + (r.motivo ? ` · ${r.motivo}` : ''))
      setDry({ ok: d.reporte.every(r => r.estado !== 'error'),
        output: `Datos sintéticos en ${d.base_path}\n(base_path del plan actualizado)\n\n` +
          (lineas.join('\n') || 'Ningún paso con job convertido: no hay entradas que generar.') })
      await loadPlan(file)
      flash('ok', `${d.reporte.filter(r => r.estado === 'generado').length} dataset(s) generados`)
    } catch (e) { flash('err', `Datos sintéticos: ${e.message}`) }
    setBusy(false)
  }

  const verAirflow = async () => {
    try {
      if (dirty) { await post('save', { file, plan }); setDirty(false) }
      const d = await post('airflow', { file })
      setCode({ name: d.name, size: d.code.length, truncated: false, code: d.code, descargable: true })
    } catch (e) { flash('err', `No se pudo generar el DAG: ${e.message}`) }
  }

  const descargarTexto = (name, text) => {
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([text], { type: 'text/x-python' }))
    a.download = name; a.click(); URL.revokeObjectURL(a.href)
  }

  const guardar = async () => {
    setBusy(true)
    try {
      await post('save', { file, plan })
      setDirty(false); flash('ok', 'Guardado.')
      if (plan.origen === 'manual') await loadPlan(file)   // el servidor normaliza las acciones
    } catch (e) { flash('err', `No se guardo: ${e.message}`) }
    setBusy(false)
  }

  const dryRun = async () => {
    setBusy(true)
    try {
      if (dirty) await post('save', { file, plan })   // el dry-run usa el archivo guardado
      setDirty(false)
      setDry(await post('run', { file }))
    } catch (e) { flash('err', e.message) }
    setBusy(false)
  }

  const descargar = () => {
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([JSON.stringify(plan, null, 2)], { type: 'application/json' }))
    a.download = file.split('/').pop(); a.click()
    URL.revokeObjectURL(a.href)
  }

  // ---- importar / procesar ----
  const pickFiles = (list) => {
    const arr = Array.from(list || [])
    const bad = arr.filter(f => !EXT_OK.includes(extOf(f.name)))
    if (bad.length) flash('err', `Ignorados (extensión no soportada): ${bad.map(f => f.name).join(', ')}`)
    setPicked(prev => {
      const names = new Set(prev.map(f => f.name))
      return [...prev, ...arr.filter(f => EXT_OK.includes(extOf(f.name)) && !names.has(f.name))]
    })
  }

  const subir = async () => {
    const name = projName.trim()
    if (!/^[A-Za-z0-9][\w.\-]{0,63}$/.test(name)) { flash('err', 'Nombre de proyecto inválido (letras, números, . _ -).'); return }
    if (!picked.length) { flash('err', 'Elige archivos primero.'); return }
    setBusy(true)
    try {
      for (let i = 0; i < picked.length; i++) {
        setUpState({ done: i, total: picked.length, current: picked[i].name })
        await post('upload', { project: name, name: picked[i].name, data: await toB64(picked[i]) })
      }
      setPicked([]); flash('ok', `${picked.length} archivo(s) subidos a "${name}".`)
      await loadList()
    } catch (e) { flash('err', `Falló la subida: ${e.message}`) }
    setUpState(null); setBusy(false)
  }

  const procesar = async (name) => {
    setProcessing(true); setProcLog(null)
    try {
      const d = await post('process', { project: name })
      setProcLog({ ok: true, log: d.log })
      const list = await post('list')
      setFiles(list.plans || []); setMaps(list.maps || [])
      setProjects((await post('projects')).projects || [])
      setMapFile(d.map)
      if (d.plans?.length) {
        setFile(d.plans[0]); setTab('orq')
        flash('ok', `Listo: ${d.plans.length} orquestación(es) generadas.`)
      } else {
        flash('ok', 'Procesado. El proyecto no tiene planes (.plan); revisa el mapa.')
        setTab('map')
      }
    } catch (e) {
      setProcLog({ ok: false, log: e.data?.log || e.message })
      flash('err', `Falló el proceso: ${e.message}`)
    }
    setProcessing(false)
  }

  const nombreOk = /^[A-Za-z0-9][\w.\-]{0,63}$/.test(projName.trim())

  const convertirAhora = async (mp) => {
    setProcessing(true)
    try {
      const d = await post('convertir', { project: proyectoDe(file), mp })
      await loadPlan(file)
      flash('ok', `Convertido: ${mp}. Orquestación actualizada (${(d.plans || []).length} archivo/s).`)
    } catch (e) { flash('err', `No se pudo convertir ${mp}: ${e.data?.error || e.message}`) }
    setProcessing(false)
  }

  const verCodigo = async (target) => {
    try { setCode(await post('code', { file: target })) }
    catch (e) { flash('err', `No se pudo leer el código: ${e.message}`) }
  }

  // ---- pasos de una orquestacion manual ----
  const proyectoDe = (f) => (plan?.proyecto || f.split(/[\\/]/).slice(-2, -1)[0] || '')
  const aplicarPaso = (datos, id) => {
    const next = JSON.parse(JSON.stringify(plan))
    let nid = id
    if (id) {
      const st = next.steps.find(x => x.id === id)
      Object.assign(st, { name: datos.name, action: datos.action, depends_on: datos.depends_on })
      st.dep_flags = Object.fromEntries(Object.entries(st.dep_flags || {}).filter(([k]) => datos.depends_on.includes(k)))
      limpiarEnlaces(next)
    } else {
      const n = Math.max(0, ...next.steps.map(x => Number(String(x.id).replace(/\D/g, '')) || 0)) + 1
      nid = `t${n}`
      next.steps.push({ id: nid, name: datos.name, action: datos.action, depends_on: datos.depends_on,
        dep_flags: {}, solo_en_fallo: false, enabled: true, continue_on_error: false })
    }
    setForm(null); setPlan(next); setDirty(true); setSelId(nid); relayout(next)
  }
  const borrarPaso = (id) => {
    if (!window.confirm('¿Borrar este paso y sus dependencias/enlaces?')) return
    const next = JSON.parse(JSON.stringify(plan))
    next.steps = next.steps.filter(x => x.id !== id)
    next.steps.forEach(x => {
      x.depends_on = x.depends_on.filter(d => d !== id)
      if (x.dep_flags) delete x.dep_flags[id]
    })
    next.enlaces = (next.enlaces || []).filter(e => e.desde !== id && e.hacia !== id)
    setPlan(next); setDirty(true); setSelId(null); setForm(null); relayout(next)
  }
  useEffect(() => { setForm(null) }, [file])

  const sel = useMemo(() => plan?.steps.find(s => s.id === selId), [plan, selId])
  const nameOf = (id) => plan?.steps.find(s => s.id === id)?.name || id

  // ---- mapa pset <-> grafo ----
  const mapRows = useMemo(() => {
    if (!pmap) return []
    return Object.values(pmap.nodes).filter(n => n.kind === 'pset' && n.present).map(n => {
      const proto = (n.prototype || '').split('/').pop().replace(/^\d+_/, '')
      const tgt = pmap.nodes[proto]
      return { pset: n.name, proto: proto || '(sin prototype)', ok: !!(tgt && tgt.present), kind: tgt?.kind, np: Object.keys(n.params || {}).length }
    })
  }, [pmap])

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: t.bg, color: t.text }}>
      <div style={{ padding: '10px 16px', display: 'flex', gap: 8, alignItems: 'center', borderBottom: `1px solid ${t.border}` }}>
        <strong style={{ fontSize: 14 }}>🧭 Orquestador</strong>
        <button style={btn(tab === 'orq')} onClick={() => setTab('orq')}>Orquestación</button>
        <button style={btn(tab === 'map')} onClick={() => setTab('map')}>Mapa pset ↔ grafo</button>
        <button style={btn(tab === 'imp')} onClick={() => setTab('imp')}>⬆ Importar pset / plan</button>
        <button style={{ ...btn(ayuda), marginLeft: 'auto' }} onClick={() => toggleAyuda()}
          aria-expanded={ayuda} aria-controls="orq-ayuda">❓ Cómo se usa</button>
        {msg && <span style={{ marginLeft: 12, fontSize: 12, color: msg.kind === 'ok' ? '#22c55e' : '#f87171' }}>{msg.text}</span>}
      </div>
      {ayuda && <GuiaUso t={t} btn={btn} irA={(x) => setTab(x)} cerrar={() => toggleAyuda(false)} />}

      {tab === 'orq' && (
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflowY: 'auto' }}>
            <div style={{ padding: 10, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
              <select value={file} onChange={e => {
                if (dirty && !window.confirm('Hay cambios sin guardar. ¿Descartarlos?')) return
                setFile(e.target.value)
              }} style={{ ...btn(false), maxWidth: 360 }}>
                {files.length === 0 && <option value="">(sin orquestaciones)</option>}
                {files.map(f => <option key={f} value={f}>{f.replace(/^output\//, '')}</option>)}
              </select>
              <button style={btn(false)} onClick={loadList}>↻ Recargar lista</button>
              <button style={btn(true)} onClick={guardar} disabled={!dirty || busy}>💾 Guardar{dirty ? ' *' : ''}</button>
              <button style={btn(false)} onClick={() => { if (plan) { relayout(plan); verTodo() } }}>⇄ Reacomodar</button>
              <button style={btn(false)} onClick={verTodo} disabled={!plan} title="Encuadrar el diagrama para ver todos los pasos">⛶ Ver todo</button>
              <button style={btn(false)} onClick={invertir} disabled={!plan}>⇅ Invertir flechas</button>
              <button style={btn(false)} onClick={() => { if (!dirty || window.confirm('¿Descartar cambios?')) loadPlan(file) }} disabled={!dirty}>↺ Descartar</button>
              <button style={btn(false)} onClick={dryRun} disabled={!plan || busy}>▶ Dry-run</button>
              <button style={btn(false)} onClick={verAirflow} disabled={!plan || busy}>🌀 DAG Airflow</button>
              <button style={btn(false)} onClick={datosSinteticos} disabled={!plan || busy}
                title="Genera parquet de entrada en <carpeta del plan>/datos_sinteticos/raw y deja el base_path apuntando ahí">🧪 Datos sintéticos</button>
              <button style={btn(false)} onClick={descargar} disabled={!plan}>📥 JSON</button>
              <button style={btn(creando)} onClick={() => setCreando(v => !v)}
                title="Crea una orquestación vacía sin .plan y arma los pasos a mano">✨ Nueva orquestación</button>
              <button style={btn(componiendo)} onClick={() => setComponiendo(v => !v)} disabled={!file}
                title="Une 2 o más planes de este proyecto en un plan de planes">🧩 Plan de planes</button>
            </div>
            {creando && (
              <NuevaPanel t={t} btn={btn} card={card}
                proyectos={[...new Set([...projects.map(p => p.name), ...files.map(f => f.split('/')[1]).filter(Boolean)])]}
                proyectoInicial={file ? proyectoDe(file) : ''}
                onCreada={async (nuevo) => {
                  setCreando(false)
                  const d = await post('list'); setFiles(d.plans || []); setMaps(d.maps || [])
                  setFile(nuevo); flash('ok', 'Orquestación creada. Agrega pasos en el panel derecho.')
                }}
                onError={(m) => flash('err', m)} />
            )}
            {componiendo && (
              <ComponerPanel t={t} btn={btn} card={card} actual={file}
                planes={files.filter(f => f.split('/').slice(0, -1).join('/') === file.split('/').slice(0, -1).join('/')
                  && !/orquestacion_PLANES_/.test(f))}
                onCreado={async (nuevo) => {
                  setComponiendo(false)
                  const d = await post('list'); setFiles(d.plans || []); setMaps(d.maps || [])
                  setFile(nuevo); flash('ok', 'Plan de planes creado.')
                }}
                onError={(m) => flash('err', m)} />
            )}
            {plan?.origen === 'manual' && (
              <div style={{ margin: '0 12px 6px', fontSize: 12, color: '#38bdf8' }}>
                ✨ <b>Orquestación manual</b> (sin .plan): agrega, edita y borra pasos en el panel derecho.
                {Object.values(UBIC).map(ub => <span key={ub.label} style={{ marginLeft: 10, color: ub.color }}>{ub.icon} {ub.label}</span>)}
              </div>
            )}
            {plan?.tipo === 'plan_de_planes' && (
              <div style={{ margin: '0 12px 6px', fontSize: 12, color: '#a78bfa' }}>
                🧩 <b>Plan de planes</b>: cada cuadro es una orquestación completa. Acomoda el orden igual que en un plan;
                “Abrir este plan” entra a cada una. El <i>base path</i> de aquí, si lo pones, se comparte con todos.
              </div>
            )}
            {plan?.pset && (
              <details style={{ margin: '0 12px 6px', fontSize: 12 }}>
                <summary style={{ cursor: 'pointer', color: '#38bdf8' }}>
                  Variante del pset <b>{plan.pset}</b> · {Object.keys(plan.ejecucion?.env || {}).length} parámetro(s) aplicados
                  {Object.keys(plan.params_pendientes || {}).length > 0 &&
                    <span style={{ color: '#f59e0b' }}> · {Object.keys(plan.params_pendientes).length} sin resolver</span>}
                </summary>
                <div style={{ color: t.muted, marginTop: 4 }}>
                  Se pasan como variables de entorno a cada job (ganan sobre el valor por defecto del grafo).
                  {Object.entries(plan.ejecucion?.env || {}).map(([k, v]) => <div key={k}><code>{k}={v}</code></div>)}
                  {Object.entries(plan.params_pendientes || {}).map(([k, v]) =>
                    <div key={k} style={{ color: '#f59e0b' }}><code>{k}</code>: {v}</div>)}
                </div>
              </details>
            )}
            <div style={{ fontSize: 11, color: t.muted, padding: '0 12px 6px' }}>
              Arrastra del punto derecho de un paso al izquierdo de otro para añadir una dependencia (el primero corre antes).
              Selecciona una flecha y pulsa Supr para quitarla. La ejecución real no está disponible desde la GUI.
            </div>
            <div ref={lienzoRef} style={{ flex: 1, minHeight: 360 }}>
              <ReactFlow
                nodes={nodes} edges={edges} nodeTypes={nodeTypes}
                onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
                onConnect={onConnect} onEdgesDelete={onEdgesDelete}
                onNodeClick={(_, n) => setSelId(n.id)} onPaneClick={() => setSelId(null)}
                onInit={setRf}
                deleteKeyCode={['Delete', 'Backspace']} fitView fitViewOptions={{ padding: 0.15 }} minZoom={0.1}
              >
                <Background /><Controls />
                {/* Minimapa con colores del tema (por defecto es blanco y tapa el diagrama en modo oscuro) */}
                <MiniMap pannable zoomable
                  style={{ background: t.card || '#152a52', border: `1px solid ${t.border || '#1e3a6e'}`, width: 160, height: 100 }}
                  maskColor={(t.bg || '#0a1628') + 'aa'}
                  nodeColor={n => (plan?.origen === 'manual' && n.data?.step
                    ? UBIC[ubicDe(n.data.step.action)].color
                    : STATUS_COLOR[n.data?.step?.action?.status] || '#64748b')}
                  nodeStrokeWidth={2} />
              </ReactFlow>
            </div>
            {code && (
              <div style={{ ...card, margin: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginBottom: 6, fontSize: 12 }}>
                  <strong>{code.name} <span style={{ color: t.muted }}>({(code.size / 1024).toFixed(0)} KB)</span></strong>
                  <span style={{ display: 'flex', gap: 6 }}>
                    <button style={btn(false)} onClick={() => navigator.clipboard?.writeText(code.code)}>Copiar</button>
                    {code.descargable && <button style={btn(false)} onClick={() => descargarTexto(code.name, code.code)}>📥 Descargar</button>}
                    <button style={btn(false)} onClick={() => setCode(null)}>✕</button>
                  </span>
                </div>
                {code.truncated && <div style={{ color: '#f59e0b', fontSize: 11, marginBottom: 4 }}>
                  Vista parcial (primeros 400 KB). El archivo completo está en la ruta indicada arriba.</div>}
                <pre style={{ margin: 0, maxHeight: 220, overflow: 'auto', fontSize: 11, background: t.codeBg || '#0b1220', padding: 8, borderRadius: 6 }}>{code.code}</pre>
              </div>
            )}
            {dry && (
              <div style={{ ...card, margin: 10, position: 'relative' }}>
                <button style={{ ...btn(false), position: 'absolute', top: 6, right: 6, padding: '0 6px' }}
                  onClick={() => setDry(null)} aria-label="Cerrar resultado">✕</button>
                <pre style={{ margin: 0, maxHeight: 160, overflow: 'auto', fontSize: 11, whiteSpace: 'pre-wrap', paddingRight: 28 }}>
                  {dry.output}{'\n'}{dry.ok ? '✔ sin problemas' : '✖ hay archivos faltantes o fallos (ver arriba)'}
                </pre>
              </div>
            )}
          </div>

          <div style={{ width: 290, borderLeft: `1px solid ${t.border}`, padding: 12, overflowY: 'auto' }}>
            {form && plan && (
              <PasoForm key={form.id || 'nuevo'} t={t} btn={btn} plan={plan}
                inicial={form.id ? plan.steps.find(x => x.id === form.id) : null}
                proyecto={proyectoDe(file)}
                onGuardar={(datos) => aplicarPaso(datos, form.id)} onCancelar={() => setForm(null)}
                onError={(m) => flash('err', m)} />)}
            {!form && !sel && <div style={{ fontSize: 12, color: t.muted }}>
              Selecciona un paso para ver y editar sus datos.
              {plan?.origen === 'manual' && <div style={{ marginTop: 8 }}>
                <button style={btn(true)} onClick={() => setForm({})}>+ Agregar paso</button></div>}
              <div style={{ marginTop: 12 }}>
                {Object.entries(STATUS_COLOR).map(([k, c]) =>
                  <div key={k} style={{ fontSize: 11 }}><span style={{ color: c }}>●</span> {k}</div>)}
                <div style={{ fontSize: 11 }}>┄ borde punteado: solo en fallo</div>
                {Object.values(UBIC).map(ub => <div key={ub.label} style={{ fontSize: 11 }}>
                  <span style={{ color: ub.color }}>▌</span> {ub.icon} {ub.label}</div>)}
              </div>
              {plan && <EjecucionPanel t={t} btn={btn} ej={ej} setEj={setEj} plan={plan}
                nameOf={nameOf} sugerir={sugerir} addEnlace={addEnlace}
                toggleEnlace={(id) => mutate(p => { const e = p.enlaces.find(x => x.id === id); e.habilitado = !e.habilitado })}
                delEnlace={(id) => mutate(p => { p.enlaces = p.enlaces.filter(x => x.id !== id) })} />}
            </div>}
            {!form && sel && (
              <div style={{ fontSize: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ fontWeight: 700, fontSize: 14 }}>{sel.name}</div>
                <div style={{ color: t.muted }}>{sel.id} · {sel.action?.type} · {sel.action?.status}
                  {sel.action?.type !== 'plan' && <span style={{ color: UBIC[ubicDe(sel.action)].color }}>
                    {' '}· {UBIC[ubicDe(sel.action)].icon} {UBIC[ubicDe(sel.action)].label}</span>}</div>
                {sel.action?.type in TIPOS_UI && sel.action.type !== 'graph' &&
                  <div style={{ wordBreak: 'break-all', color: t.muted }}>{resumenAccion(sel.action)}</div>}
                {plan?.origen === 'manual' && (
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button style={btn(false)} onClick={() => setForm({ id: sel.id })}>✏️ Editar paso</button>
                    <button style={btn(false)} onClick={() => borrarPaso(sel.id)}>🗑 Borrar</button>
                    <button style={btn(false)} onClick={() => setForm({})}>+ Paso</button>
                  </div>)}
                {sel.action?.target && <div style={{ wordBreak: 'break-all', color: t.muted }}>{sel.action.target}</div>}
                {sel.action?.type === 'graph' && sel.action?.target &&
                  <button style={btn(true)} onClick={() => verCodigo(sel.action.target)}>👁 Ver código PySpark</button>}
                {sel.action?.type === 'plan' && sel.action?.target &&
                  <button style={btn(true)} onClick={() => {
                    if (dirty && !window.confirm('Hay cambios sin guardar en este plan de planes. ¿Descartarlos?')) return
                    setFile(sel.action.target)
                  }}>📂 Abrir este plan</button>}
                {sel.action?.status === 'sin_convertir' && <>
                  <div style={{ color: '#f59e0b' }}>El grafo <b>{sel.action.source}</b> está en la carpeta pero aún no se convierte.</div>
                  <button style={btn(true)} disabled={processing || busy}
                    onClick={() => convertirAhora(sel.action.source)}>
                    {processing ? 'Convirtiendo…' : '⚙ Convertir ahora'}</button>
                </>}
                {sel.action?.status === 'faltante' && sel.action?.source && !sel.action?.target &&
                  <div style={{ color: '#f87171' }}>Falta: {sel.action.source}{sel.action.pset ? ` (grafo del pset ${sel.action.pset})` : ''}</div>}
                {sel.action?.nota && <div style={{ color: t.muted }}>{sel.action.nota}</div>}
                <label><input type="checkbox" checked={sel.enabled}
                  onChange={e => mutate(p => { p.steps.find(s => s.id === sel.id).enabled = e.target.checked })} /> Habilitado</label>
                <label><input type="checkbox" checked={!!sel.solo_en_fallo}
                  onChange={e => mutate(p => { p.steps.find(s => s.id === sel.id).solo_en_fallo = e.target.checked })} /> Solo corre si algo falla</label>
                <label><input type="checkbox" checked={!!sel.continue_on_error}
                  onChange={e => mutate(p => { p.steps.find(s => s.id === sel.id).continue_on_error = e.target.checked })} /> Continuar si falla</label>
                <div style={{ fontWeight: 600 }}>Corre después de:</div>
                {sel.depends_on.length === 0 && <div style={{ color: t.muted }}>(inicio del plan)</div>}
                {sel.depends_on.map(d => (
                  <div key={d} style={{ display: 'flex', justifyContent: 'space-between', gap: 6 }}>
                    <span>{nameOf(d)} <span style={{ color: t.muted }}>({d})</span></span>
                    <button style={{ ...btn(false), padding: '0 6px' }} title="Quitar dependencia"
                      onClick={() => mutate(p => {
                        const s = p.steps.find(x => x.id === sel.id)
                        s.depends_on = s.depends_on.filter(x => x !== d)
                        limpiarEnlaces(p)
                      })}>✕</button>
                  </div>
                ))}
                <select value="" onChange={e => {
                  const d = e.target.value
                  if (!d) return
                  if (createsCycle(plan.steps, sel.id, d)) { flash('err', 'Crearía un ciclo.'); return }
                  mutate(p => p.steps.find(s => s.id === sel.id).depends_on.push(d))
                }} style={btn(false)}>
                  <option value="">+ añadir dependencia…</option>
                  {plan.steps.filter(s => s.id !== sel.id && !sel.depends_on.includes(s.id))
                    .map(s => <option key={s.id} value={s.id}>{s.name} ({s.id})</option>)}
                </select>
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'map' && (
        <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
          {!maps.length && <div style={{ color: t.muted }}>
            No hay <code>pset_map.json</code>. Genéralo con <code>python -m src.pset_map abinitio/&lt;carpeta&gt;</code>.
          </div>}
          {maps.length > 1 && (
            <select value={maps.includes(mapFile) ? mapFile : maps[0]} onChange={e => setMapFile(e.target.value)}
              style={{ ...btn(false), marginBottom: 8 }}>
              {maps.map(m => <option key={m} value={m}>{m.replace(/^abinitio\//, '').replace(/\/pset_map\.json$/, '')}</option>)}
            </select>
          )}
          {pmap && (<>
            <div style={{ color: t.muted, fontSize: 12, marginBottom: 8 }}>
              {maps.includes(mapFile) ? mapFile : maps[0]} · {mapRows.length} psets · {pmap.missing?.length || 0} referencias faltantes
            </div>
            <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
              <thead><tr style={{ textAlign: 'left', color: t.muted }}>
                <th>Pset</th><th>Instancia</th><th>Tipo</th><th>Estado</th><th>Params</th></tr></thead>
              <tbody>{mapRows.map(r => (
                <tr key={r.pset} style={{ borderTop: `1px solid ${t.border}` }}>
                  <td>{r.pset}</td><td>{r.proto}</td><td>{r.kind || '-'}</td>
                  <td style={{ color: r.ok ? '#22c55e' : '#ef4444' }}>{r.ok ? 'presente' : 'FALTANTE'}</td>
                  <td>{r.np}</td></tr>))}</tbody>
            </table>
            <h4>Faltantes</h4>
            <div style={{ fontSize: 12, columns: 2 }}>
              {(pmap.missing || []).map(m => <div key={m}>{pmap.nodes[m]?.kind} · {m}</div>)}
            </div>
            <h4>Grafos sin pset</h4>
            <div style={{ fontSize: 12 }}>{(pmap.graphs_without_pset || []).join(', ') || 'ninguno'}</div>
          </>)}
        </div>
      )}

      {tab === 'imp' && (
        <div style={{ flex: 1, overflow: 'auto', padding: 16, display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-start' }}>
          <div style={{ ...card, flex: '1 1 380px', maxWidth: 560 }}>
            <h4 style={{ margin: '0 0 8px' }}>1. Subir archivos</h4>
            <div style={{ fontSize: 12, color: t.muted, marginBottom: 8 }}>
              Sube los <code>.pset</code>, <code>.plan</code> y <code>.mp</code> juntos (y .xfr/.dml/.ksh/.dbc si los tienes).
              Se guardan en <code>abinitio/&lt;proyecto&gt;/</code>. Un archivo con el mismo nombre se reemplaza.
            </div>
            <input list="proj-list" value={projName} onChange={e => setProjName(e.target.value)}
              placeholder="Nombre del proyecto (nuevo o existente)"
              style={{ ...btn(false), width: '100%', boxSizing: 'border-box', marginBottom: 8, textAlign: 'left' }} />
            <datalist id="proj-list">{projects.map(p => <option key={p.name} value={p.name} />)}</datalist>
            <div
              onDragOver={e => e.preventDefault()}
              onDrop={e => { e.preventDefault(); pickFiles(e.dataTransfer.files) }}
              style={{ border: `2px dashed ${t.border}`, borderRadius: 8, padding: 16, textAlign: 'center', fontSize: 12 }}>
              Arrastra archivos aquí o{' '}
              <label style={{ color: t.accent, cursor: 'pointer', textDecoration: 'underline' }}>
                elígelos
                <input type="file" multiple accept={EXT_OK.join(',')} style={{ display: 'none' }}
                  onChange={e => { pickFiles(e.target.files); e.target.value = '' }} />
              </label>
            </div>
            {picked.length > 0 && (
              <div style={{ marginTop: 8, fontSize: 12, maxHeight: 220, overflow: 'auto' }}>
                {picked.map(f => (
                  <div key={f.name} style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                    <span>{f.name} <span style={{ color: t.muted }}>({(f.size / 1024).toFixed(0)} KB)</span></span>
                    <button style={{ ...btn(false), padding: '0 6px' }}
                      onClick={() => setPicked(prev => prev.filter(x => x !== f))}>✕</button>
                  </div>))}
              </div>)}
            <div style={{ marginTop: 10, display: 'flex', gap: 8, alignItems: 'center' }}>
              <button style={{ ...btn(true), opacity: nombreOk && picked.length ? 1 : 0.5 }} onClick={subir}
                disabled={busy || !picked.length || !nombreOk}>⬆ Subir {picked.length || ''}</button>
              {picked.length > 0 && !nombreOk && <span style={{ fontSize: 12, color: '#f59e0b' }}>
                Escribe un nombre de proyecto (letras, números, . _ -)</span>}
              {upState && <span style={{ fontSize: 12, color: t.muted }}>
                {upState.done + 1}/{upState.total} · {upState.current}</span>}
            </div>
          </div>

          <div style={{ ...card, flex: '2 1 460px' }}>
            <h4 style={{ margin: '0 0 8px' }}>2. Procesar proyecto</h4>
            <div style={{ fontSize: 12, color: t.muted, marginBottom: 8 }}>
              Procesar = generar el mapa de relaciones, convertir los grafos a PySpark y crear la orquestación de cada plan.
              Puede tardar con grafos grandes.
            </div>
            {projects.length === 0 && <div style={{ fontSize: 12, color: t.muted }}>No hay proyectos todavía.</div>}
            {projects.map(p => (
              <div key={p.name} style={{ borderTop: `1px solid ${t.border}`, padding: '8px 0', fontSize: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
                  <strong>{p.name}</strong>
                  <button style={btn(true)} onClick={() => procesar(p.name)} disabled={processing || busy}>
                    {processing ? 'Procesando…' : '⚙ Procesar'}
                  </button>
                </div>
                <div style={{ color: t.muted }}>
                  {Object.entries(p.counts).map(([k, v]) => `${v} .${k}`).join(' · ') || 'sin archivos'}
                  {p.tiene_mapa ? ' · con mapa' : ''}
                  {p.orquestaciones.length ? ` · ${p.orquestaciones.length} orquestación(es)` : ''}
                </div>
                {!p.counts.plan && <div style={{ color: '#f59e0b' }}>Sin .plan: se generará el mapa y la conversión, pero no orquestación.</div>}
                {p.counts.plan && !p.counts.pset && <div style={{ color: '#f59e0b' }}>Hay planes pero no psets.</div>}
              </div>))}
            {processing && <div style={{ marginTop: 8, fontSize: 12 }}>⏳ Convirtiendo… no cierres la pestaña.</div>}
            {procLog && (
              <pre style={{ marginTop: 8, maxHeight: 260, overflow: 'auto', fontSize: 11, whiteSpace: 'pre-wrap',
                border: `1px solid ${procLog.ok ? '#22c55e' : '#ef4444'}`, borderRadius: 6, padding: 8 }}>{procLog.log}</pre>)}
          </div>
        </div>
      )}
    </div>
  )
}
