import { useState, useEffect } from 'react'
import { COMPILE_URL } from '../config'

// Panel SEPARADO para traer datos reales de Cloudera (Hive/Impala) o Teradata
// para pruebas PUNTUALES. Los datos llegan YA ENMASCARADOS por la libreria de PII
// (el backend enmascara ANTES de responder; el dato real nunca sale del server).
// Via onImport(dataset) devuelve un dataset de ENTRADA a Data Sintetica, con el
// mismo formato que los sinteticos, para usarlo en la prueba.
const FETCH_URL = COMPILE_URL.replace(/\/compile$/, '/datasource/fetch')

// Pistas por fuente (puerto tipico y jar del driver JDBC esperado en el server).
const PORT_HINT = {
  teradata: '1025', hive: '10000', impala: '21050',
  mariadb: '3306', mysql: '3306', postgres: '5432',
}
// Drivers INCLUIDOS en el proyecto (carpeta drivers/, licencia libre). Al elegir
// la fuente se autollena esta ruta. Teradata e Impala son propietarios (no se
// pueden incluir por licencia): quedan vacios para que el usuario ponga el .jar.
const DRIVER_BUNDLED = {
  hive: 'drivers/hive-jdbc-standalone.jar',
  mariadb: 'drivers/mariadb-java-client.jar',
  mysql: 'drivers/mysql-connector-j.jar',
  postgres: 'drivers/postgresql.jar',
}
// Pista (placeholder) para los que NO vienen incluidos.
const DRIVER_HINT = {
  teradata: 'descárgalo de Teradata (licencia): /ruta/terajdbc4.jar',
  impala: 'descárgalo de Cloudera (licencia): /ruta/ImpalaJDBC.jar',
  hive: 'drivers/hive-jdbc-standalone.jar',
  mariadb: 'drivers/mariadb-java-client.jar',
  mysql: 'drivers/mysql-connector-j.jar',
  postgres: 'drivers/postgresql.jar',
}

export default function DataSourcePanel({ theme, onImport }) {
  const t = theme || {}
  // Abierto por defecto para que el boton "Traer datos" se vea de inmediato.
  // Se PERSISTE en localStorage para que no "parpadee" (abra/cierre) al
  // re-renderizar la pagina o cambiar de pestana.
  const [open, _setOpen] = useState(() => {
    try { return localStorage.getItem('bnx_datasource_open') !== '0' } catch { return true }
  })
  const setOpen = (v) => {
    const nv = typeof v === 'function' ? v(open) : v
    _setOpen(nv)
    try { localStorage.setItem('bnx_datasource_open', nv ? '1' : '0') } catch { /* ignore */ }
  }
  const [sourceType, setSourceType] = useState('teradata')
  const [host, setHost] = useState('')
  const [port, setPort] = useState('')
  const [database, setDatabase] = useState('')
  const [url, setUrl] = useState('')
  const [user, setUser] = useState('')
  const [password, setPassword] = useState('')
  const [table, setTable] = useState('')
  const [query, setQuery] = useState('')
  const [limit, setLimit] = useState(50)
  const [driverJar, setDriverJar] = useState('')
  const [targetNode, setTargetNode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [preview, setPreview] = useState(null) // {columns, rows} enmascarado

  // --- Conexiones guardadas (SIN password, por seguridad) ---
  // Se guardan en localStorage por tipo de fuente. Hasta MAX_SAVED por tipo.
  // El password NUNCA se persiste: se pide al conectar.
  const MAX_SAVED = 3
  const LS_CONN = 'bnx_saved_connections'
  const [savedConns, setSavedConns] = useState(() => {
    try { return JSON.parse(localStorage.getItem(LS_CONN) || '{}') } catch { return {} }
  })
  const persistConns = (next) => {
    setSavedConns(next)
    try { localStorage.setItem(LS_CONN, JSON.stringify(next)) } catch { /* ignore */ }
  }
  // Guarda la conexion actual bajo un nombre (sin password). Reemplaza si el
  // nombre ya existe; respeta el tope de MAX_SAVED por tipo.
  const saveConnection = () => {
    const name = (window.prompt('Nombre para esta conexión (ej. "Prod Teradata"):') || '').trim()
    if (!name) return
    const entry = {
      name, sourceType, host, port, database,
      url: url.trim(), user, table, driverJar,
    }
    const list = (savedConns[sourceType] || []).filter(c => c.name !== name)
    list.unshift(entry)
    if (list.length > MAX_SAVED) {
      setError(`Máximo ${MAX_SAVED} conexiones guardadas por fuente. Borra una para añadir otra.`)
      list.length = MAX_SAVED
    }
    persistConns({ ...savedConns, [sourceType]: list })
  }
  // Carga una conexion guardada en el formulario (el password queda vacio).
  const loadConnection = (c) => {
    setSourceType(c.sourceType || sourceType)
    setHost(c.host || ''); setPort(c.port || ''); setDatabase(c.database || '')
    setUrl(c.url || ''); setUser(c.user || ''); setTable(c.table || '')
    setDriverJar(c.driverJar || ''); setPassword('')
    setError('')
  }
  const deleteConnection = (st, name) => {
    const list = (savedConns[st] || []).filter(c => c.name !== name)
    persistConns({ ...savedConns, [st]: list })
  }
  const currentSaved = savedConns[sourceType] || []

  // Al montar: si la fuente por defecto trae driver incluido y el campo esta
  // vacio, lo autollena (p.ej. si el usuario cambia el default a mariadb).
  useEffect(() => {
    if (!driverJar && DRIVER_BUNDLED[sourceType]) setDriverJar(DRIVER_BUNDLED[sourceType])
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const field = {
    padding: '7px 9px', borderRadius: 6, fontSize: 12, width: '100%',
    background: t.codeBg || '#081220', color: t.text || '#e2e8f0',
    border: `1px solid ${t.border || '#334155'}`, outline: 'none', boxSizing: 'border-box',
  }
  const lbl = { fontSize: 11, color: t.dim || '#64748b', display: 'block', marginBottom: 3 }

  const fetchData = async () => {
    setLoading(true); setError(''); setPreview(null)
    try {
      const conn = { user, password }
      if (url.trim()) conn.url = url.trim()
      else { conn.host = host; conn.port = port; conn.database = database }
      const res = await fetch(FETCH_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_type: sourceType, conn,
          table: table.trim() || undefined, query: query.trim() || undefined,
          limit: Number(limit) || 50, driver_jar: driverJar.trim() || undefined,
        }),
      })
      const data = await res.json()
      if (!data.ok) { setError(data.error || 'No se pudo traer la data.'); return }
      setPreview(data)   // ya viene enmascarado
    } catch (e) {
      setError('Error: ' + e.message)
    } finally { setLoading(false) }
  }

  // Nombre base del dataset (nodo/tabla) normalizado.
  const datasetName = () =>
    (targetNode.trim() || table.trim() || 'external_source').replace(/[^A-Za-z0-9_]/g, '_')

  // Serializa el preview enmascarado a CSV.
  const toCSV = () => {
    const headers = (preview.columns || []).map(c => c.name)
    return [headers.join(',')].concat(
      (preview.rows || []).map(r => headers.map(h => {
        const v = r[h] == null ? '' : String(r[h])
        return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v
      }).join(','))
    ).join('\n') + '\n'
  }

  // Descarga DIRECTA del dataset enmascarado (CSV o JSON), independiente de si
  // hay grafo o codigo en el Compiler. El panel es autonomo: conectar -> traer
  // -> descargar.
  const downloadMasked = (fmt) => {
    if (!preview || !preview.rows?.length) return
    const name = datasetName()
    let content, mime, ext
    if (fmt === 'json') {
      content = JSON.stringify(preview.rows, null, 2)
      mime = 'application/json'; ext = 'json'
    } else {
      content = toCSV(); mime = 'text/csv'; ext = 'csv'
    }
    const blob = new Blob([content], { type: mime })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `${name}_enmascarado.${ext}`; a.click()
    URL.revokeObjectURL(url)
  }

  // Convierte el preview enmascarado en un dataset de entrada y lo devuelve
  // (opcional: solo util cuando hay un grafo/codigo donde usarlo en la prueba).
  const importToTest = () => {
    if (!preview || !preview.rows?.length) return
    const content = toCSV()
    const node = datasetName()
    const columns = (preview.columns || []).map(c => ({ name: c.name, type: 'string', pii: c.pii || null }))
    onImport && onImport({
      node, node_type: 'SOURCE', io: 'input', format: 'csv',
      content, rows: preview.rows, columns, external: true, masked: true,
    })
  }

  return (
    <div style={{
      background: '#0ea5e912', borderRadius: 10, padding: 0, overflow: 'hidden',
      border: '1px solid #0ea5e955',
    }}>
      <button onClick={() => setOpen(v => !v)}
        style={{ width: '100%', textAlign: 'left', padding: '14px 16px', cursor: 'pointer',
          background: '#0ea5e925', border: 'none', color: '#38bdf8',
          fontSize: 15, fontWeight: 800, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>🛢️ Traer datos remotos de Cloudera / Teradata (enmascarados por PII)</span>
        <span style={{ fontSize: 12, color: '#38bdf8', background: '#0ea5e930', padding: '3px 10px', borderRadius: 6 }}>
          {open ? '▲ ocultar conexión' : '▼ abrir conexión'}
        </span>
      </button>

      {open && (
        <div style={{ padding: '0 14px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ fontSize: 11, color: t.dim, lineHeight: 1.5 }}>
            Los datos llegan <b>enmascarados</b> (tarjetas, nombres, emails, etc. redactados por la
            librería de PII); el dato real nunca sale del server. Para pruebas puntuales (LIMIT).
            Los drivers de <b>Hive, MariaDB, MySQL y PostgreSQL ya vienen incluidos</b> (se autollenan al
            elegir la fuente). <b>Teradata e Impala</b> son propietarios: descarga su .jar y pon la ruta.
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
            <div><label style={lbl}>Fuente</label>
              <select value={sourceType} onChange={e => {
                const st = e.target.value
                setSourceType(st)
                // Autollenar el driver incluido para esa fuente. Teradata/Impala
                // no vienen incluidos (licencia): se limpia para que lo ponga el usuario.
                setDriverJar(DRIVER_BUNDLED[st] || '')
                if (PORT_HINT[st]) setPort(PORT_HINT[st])
              }} style={field}>
                <option value="teradata">Teradata</option>
                <option value="hive">Cloudera · Hive</option>
                <option value="impala">Cloudera · Impala</option>
                <option value="mariadb">MariaDB</option>
                <option value="mysql">MySQL</option>
                <option value="postgres">PostgreSQL</option>
                <option value="jdbc">JDBC genérico</option>
              </select>
            </div>
            <div><label style={lbl}>Host</label><input style={field} value={host} onChange={e => setHost(e.target.value)} placeholder="host.banco.com" /></div>
            <div><label style={lbl}>Puerto</label><input style={field} value={port} onChange={e => setPort(e.target.value)} placeholder={PORT_HINT[sourceType] || '1025 / 10000 / 21050'} /></div>
          </div>

          {/* Conexiones guardadas para esta fuente (max 3, sin password) */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
            <span style={{ fontSize: 11, color: t.dim }}>Conexiones guardadas ({currentSaved.length}/{MAX_SAVED}):</span>
            {currentSaved.length === 0 && (
              <span style={{ fontSize: 11, color: t.dim, fontStyle: 'italic' }}>ninguna</span>
            )}
            {currentSaved.map(c => (
              <span key={c.name} style={{
                display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11,
                background: '#0ea5e918', border: '1px solid #0ea5e955', borderRadius: 999,
                padding: '3px 4px 3px 10px', color: '#38bdf8',
              }}>
                <button onClick={() => loadConnection(c)} title="Cargar esta conexión"
                  style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', fontSize: 11, fontWeight: 700, padding: 0 }}>
                  {c.name}
                </button>
                <button onClick={() => deleteConnection(c.sourceType, c.name)} title="Borrar"
                  style={{ background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', fontSize: 12, padding: '0 2px' }}>✕</button>
              </span>
            ))}
            <button onClick={saveConnection}
              disabled={currentSaved.length >= MAX_SAVED}
              title={currentSaved.length >= MAX_SAVED ? `Máximo ${MAX_SAVED} por fuente` : 'Guardar la conexión actual (sin password)'}
              style={{
                fontSize: 11, fontWeight: 700, borderRadius: 999, padding: '4px 10px',
                cursor: currentSaved.length >= MAX_SAVED ? 'not-allowed' : 'pointer',
                background: currentSaved.length >= MAX_SAVED ? 'transparent' : '#22c55e20',
                border: `1px solid ${currentSaved.length >= MAX_SAVED ? (t.border || '#334155') : '#22c55e55'}`,
                color: currentSaved.length >= MAX_SAVED ? t.dim : '#22c55e',
              }}>💾 Guardar conexión</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <div><label style={lbl}>Base de datos</label><input style={field} value={database} onChange={e => setDatabase(e.target.value)} placeholder="esquema / database" /></div>
            <div><label style={lbl}>URL JDBC (opcional, sobreescribe host/db)</label><input style={field} value={url} onChange={e => setUrl(e.target.value)} placeholder="jdbc:teradata://host/DATABASE=db" /></div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <div><label style={lbl}>Usuario</label><input style={field} value={user} onChange={e => setUser(e.target.value)} /></div>
            <div><label style={lbl}>Password (no se guarda ni se muestra)</label><input style={field} type="password" value={password} onChange={e => setPassword(e.target.value)} /></div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 8 }}>
            <div><label style={lbl}>Tabla</label><input style={field} value={table} onChange={e => setTable(e.target.value)} placeholder="esquema.clientes" /></div>
            <div><label style={lbl}>Límite de filas</label><input style={field} type="number" value={limit} onChange={e => setLimit(e.target.value)} /></div>
          </div>
          <div><label style={lbl}>o Query SQL (opcional)</label>
            <input style={field} value={query} onChange={e => setQuery(e.target.value)} placeholder="SELECT ... FROM ... WHERE ..." /></div>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 8 }}>
            <div><label style={lbl}>Ruta del driver JDBC (.jar en el server)</label><input style={field} value={driverJar} onChange={e => setDriverJar(e.target.value)} placeholder={DRIVER_HINT[sourceType] || '/opt/drivers/driver.jar'} /></div>
            <div><label style={lbl}>Nombre del nodo/fuente</label><input style={field} value={targetNode} onChange={e => setTargetNode(e.target.value)} placeholder="external_source" /></div>
          </div>

          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button onClick={fetchData} disabled={loading}
              style={{ padding: '8px 14px', borderRadius: 8, fontSize: 13, fontWeight: 700,
                cursor: loading ? 'wait' : 'pointer', background: '#0ea5e9', color: '#fff', border: 'none' }}>
              {loading ? '⏳ Conectando...' : '🔌 Traer datos (enmascarados)'}
            </button>
            {preview && preview.rows?.length > 0 && (
              <>
                <button onClick={() => downloadMasked('csv')}
                  style={{ padding: '8px 14px', borderRadius: 8, fontSize: 13, fontWeight: 700,
                    cursor: 'pointer', background: '#22c55e', color: '#000', border: 'none' }}>
                  📥 Descargar CSV ({preview.rows.length})
                </button>
                <button onClick={() => downloadMasked('json')}
                  style={{ padding: '8px 14px', borderRadius: 8, fontSize: 13, fontWeight: 700,
                    cursor: 'pointer', background: 'transparent', color: '#22c55e', border: '1px solid #22c55e55' }}>
                  📥 JSON
                </button>
                {onImport && (
                  <button onClick={importToTest}
                    style={{ padding: '8px 14px', borderRadius: 8, fontSize: 13, fontWeight: 700,
                      cursor: 'pointer', background: 'transparent', color: '#38bdf8', border: '1px solid #38bdf855' }}>
                    ✓ Usar en la prueba
                  </button>
                )}
              </>
            )}
          </div>

          {error && <div style={{ fontSize: 12, color: '#f87171' }}>⚠️ {error}</div>}

          {preview && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span style={{ fontSize: 11, color: '#22c55e' }}>
                ✅ {preview.n} fila(s) enmascaradas · columnas PII marcadas: {(preview.columns || []).filter(c => c.pii).map(c => c.name).join(', ') || 'ninguna'}
              </span>
              <div style={{ maxHeight: 180, overflow: 'auto', border: '1px solid #33415530', borderRadius: 6 }}>
                <table style={{ borderCollapse: 'collapse', fontSize: 11, width: '100%' }}>
                  <thead>
                    <tr>{(preview.columns || []).map(c => (
                      <th key={c.name} style={{ padding: '4px 8px', textAlign: 'left', position: 'sticky', top: 0,
                        background: t.codeBg || '#081220', color: c.pii ? '#fb923c' : (t.muted || '#94a3b8'),
                        borderBottom: '1px solid #33415530' }}>{c.name}{c.pii ? ' 🔒' : ''}</th>
                    ))}</tr>
                  </thead>
                  <tbody>
                    {(preview.rows || []).slice(0, 20).map((r, i) => (
                      <tr key={i}>{(preview.columns || []).map(c => (
                        <td key={c.name} style={{ padding: '3px 8px', color: t.muted || '#94a3b8',
                          borderBottom: '1px solid #33415520', whiteSpace: 'nowrap' }}>{String(r[c.name] ?? '')}</td>
                      ))}</tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
