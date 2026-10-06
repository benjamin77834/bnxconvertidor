import { useState } from 'react'
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
const DRIVER_HINT = {
  teradata: '/opt/drivers/terajdbc4.jar',
  hive: '/opt/drivers/HiveJDBC.jar',
  impala: '/opt/drivers/ImpalaJDBC.jar',
  mariadb: '/opt/drivers/mariadb-java-client.jar',
  mysql: '/opt/drivers/mysql-connector-j.jar',
  postgres: '/opt/drivers/postgresql.jar',
}

export default function DataSourcePanel({ theme, onImport }) {
  const t = theme || {}
  // Abierto por defecto para que el boton "Traer datos" se vea de inmediato
  // (antes estaba colapsado y el usuario no encontraba el boton).
  const [open, setOpen] = useState(true)
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

  // Convierte el preview enmascarado en un dataset de entrada y lo devuelve.
  const importToTest = () => {
    if (!preview || !preview.rows?.length) return
    const headers = (preview.columns || []).map(c => c.name)
    const rows = preview.rows
    const content = [headers.join(',')].concat(
      rows.map(r => headers.map(h => {
        const v = r[h] == null ? '' : String(r[h])
        return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v
      }).join(','))
    ).join('\n') + '\n'
    const node = (targetNode.trim() || table.trim() || 'external_source').replace(/[^A-Za-z0-9_]/g, '_')
    const columns = (preview.columns || []).map(c => ({ name: c.name, type: 'string', pii: c.pii || null }))
    onImport && onImport({
      node, node_type: 'SOURCE', io: 'input', format: 'csv',
      content, columns, rows, external: true, masked: true,
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
            Requiere el driver JDBC en el server (Teradata: terajdbc4.jar; Cloudera: Hive/Impala jar;
            MariaDB/MySQL: mariadb-java-client.jar / mysql-connector-j.jar; PostgreSQL: postgresql.jar).
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
            <div><label style={lbl}>Fuente</label>
              <select value={sourceType} onChange={e => setSourceType(e.target.value)} style={field}>
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
              <button onClick={importToTest}
                style={{ padding: '8px 14px', borderRadius: 8, fontSize: 13, fontWeight: 700,
                  cursor: 'pointer', background: '#22c55e', color: '#000', border: 'none' }}>
                ✓ Usar en la prueba ({preview.rows.length} filas)
              </button>
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
