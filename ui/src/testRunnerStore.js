// testRunnerStore.js
//
// Store SINGLETON (fuera de React) para la prueba PySpark de Data Redactada.
//
// Problema que resuelve: la ejecucion de la prueba vivia dentro del componente
// DataGenPage. App.jsx monta/desmonta las paginas por renderizado condicional,
// asi que al cambiar de pestana el componente se desmontaba y la prueba (fetch +
// lector SSE) quedaba huerfana y se perdia el avance.
//
// Con este store la prueba corre AQUI (a nivel de modulo, vive mientras la
// pestana del navegador este abierta). El componente solo se SUSCRIBE: al montar
// lee el estado actual (corriendo / terminado / consola acumulada) y se re-pinta
// via callback. Cambiar de pagina ya no corta la prueba; al volver se ve el
// estatus real.
//
// El estado tambien se persiste en localStorage para sobrevivir recargas de
// pagina (la conexion SSE si se corta con un reload completo del navegador, pero
// el ultimo estado/consola queda visible).

const LS_KEY = 'bnx_dg_runner_state'

const initialState = {
  running: false,          // hay una prueba en curso
  target: null,            // 'local' | 'ec2'
  startedAt: null,         // timestamp ms
  finishedAt: null,        // timestamp ms
  console: [],             // [{text, kind}]
  result: null,            // {ok, summary, reads, writes}
  downloads: [],           // [{name, path}]
  report: null,            // {totals, inputs, outputs, flow, ...}
  error: null,             // mensaje de error de red
}

function loadPersisted() {
  try {
    const v = localStorage.getItem(LS_KEY)
    if (!v) return { ...initialState }
    const s = JSON.parse(v)
    // Si al recargar la pagina quedo 'running' pero ya no hay conexion viva
    // (un reload completo mata el fetch), lo marcamos como interrumpido para no
    // mostrar un spinner eterno.
    if (s.running && !_liveController) {
      s.running = false
      if (!s.result) {
        s.result = { ok: false, summary: 'Prueba interrumpida por recarga de pagina.' }
      }
    }
    return { ...initialState, ...s }
  } catch {
    return { ...initialState }
  }
}

let state = null
let _liveController = null      // AbortController de la prueba viva
const listeners = new Set()

function persist() {
  try {
    // No persistimos consolas gigantes enteras (limite de localStorage): las
    // ultimas 500 lineas son suficientes para ver el estatus al volver.
    const toSave = { ...state, console: state.console.slice(-500) }
    localStorage.setItem(LS_KEY, JSON.stringify(toSave))
  } catch {}
}

function emit() {
  persist()
  for (const l of listeners) {
    try { l(state) } catch {}
  }
}

function ensureState() {
  if (state === null) state = loadPersisted()
  return state
}

export function getState() {
  return ensureState()
}

export function subscribe(listener) {
  ensureState()
  listeners.add(listener)
  // avisar el estado actual de inmediato
  try { listener(state) } catch {}
  return () => listeners.delete(listener)
}

export function clearRunnerState() {
  // Aborta una prueba viva (si la hay) y resetea el estado.
  if (_liveController) {
    try { _liveController.abort() } catch {}
    _liveController = null
  }
  state = { ...initialState }
  try { localStorage.removeItem(LS_KEY) } catch {}
  emit()
}

function classifyLine(text) {
  if (/Traceback|Exception|Error|ERROR|SQLSTATE/.test(text)) return 'error'
  if (/\[>\] SOURCE|READ /.test(text)) return 'source'
  if (/\[~\] JOIN|JOIN:/.test(text)) return 'join'
  if (/\[\*\] SINK|\[>\] SINK|WRITE /.test(text)) return 'sink'
  if (/\[~\] TRANSFORM|SORT|DEDUP|FILTER/.test(text)) return 'transform'
  if (/\[ok\]|Ejecución OK/.test(text)) return 'ok'
  return 'plain'
}

// Lanza la prueba. No se re-inicia si ya hay una corriendo.
//   streamUrl: URL del endpoint SSE (/runtest/stream)
//   payload:   cuerpo JSON { code, mp, xfr, datasets, timeout, job_name }
//   target:    'local' | 'ec2' (solo informativo para la UI)
export async function startTest({ streamUrl, payload, target = 'local', initialLine }) {
  ensureState()
  if (state.running) return  // ya hay una prueba en curso

  _liveController = new AbortController()
  state = {
    ...initialState,
    running: true,
    target,
    startedAt: Date.now(),
    console: initialLine ? [{ text: initialLine, kind: 'info' }] : [],
  }
  emit()

  try {
    const res = await fetch(streamUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: _liveController.signal,
    })
    if (!res.ok || !res.body) {
      let msg = `HTTP ${res.status}`
      try { const j = await res.json(); msg = j.error || msg } catch {}
      state = { ...state, running: false, finishedAt: Date.now(),
                result: { ok: false, summary: msg } }
      _liveController = null
      emit()
      return
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let finished = false

    while (!finished) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop()
      for (const part of parts) {
        const line = part.replace(/^data:\s*/, '').trim()
        if (!line) continue
        let evt
        try { evt = JSON.parse(line) } catch { continue }
        if (evt.type === 'line') {
          state = { ...state, console: [...state.console, { text: evt.text, kind: classifyLine(evt.text) }] }
          emit()
        } else if (evt.type === 'done') {
          state = {
            ...state,
            running: false,
            finishedAt: Date.now(),
            result: { ok: evt.ok, summary: evt.summary, reads: evt.reads, writes: evt.writes },
            downloads: Array.isArray(evt.downloads) ? evt.downloads : [],
            report: evt.report || null,
          }
          finished = true
          emit()
        }
      }
    }
    // Si el stream cerro sin un evento 'done' explicito.
    if (state.running) {
      state = { ...state, running: false, finishedAt: Date.now(),
                result: state.result || { ok: false, summary: 'La conexion se cerro sin resultado.' } }
      emit()
    }
  } catch (e) {
    if (e.name === 'AbortError') {
      // Cancelacion explicita (clear): no marcar error.
      return
    }
    state = { ...state, running: false, finishedAt: Date.now(),
              error: e.message,
              console: [...state.console, { text: `Error: ${e.message}`, kind: 'error' }],
              result: { ok: false, summary: `Error de red: ${e.message}` } }
    emit()
  } finally {
    _liveController = null
  }
}
