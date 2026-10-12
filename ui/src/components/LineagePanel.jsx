import { useMemo, useState } from 'react'
import { nodeLineage, columnLineage, buildAllMetadata } from '../lib/lineage'

// Descarga un texto como archivo en el navegador.
function downloadText(filename, text, mime = 'text/plain') {
  const blob = new Blob([text], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename
  document.body.appendChild(a); a.click()
  document.body.removeChild(a); URL.revokeObjectURL(url)
}

const TYPE_COLOR = {
  SOURCE: '#22c55e', TRANSFORM: '#6366f1', ROLLUP: '#7c3aed', XFR: '#6366f1',
  JOIN: '#f59e0b', SINK: '#ef4444', DEDUP: '#06b6d4', NORMALIZE: '#a855f7',
  LOOKUP: '#ec4899', CONCATENATE: '#14b8a6', GATHER: '#8b5cf6',
  PARTITION: '#f97316', FILTER: '#eab308',
}

const KIND_LABEL = {
  origin: 'origen', select: 'select', rename: 'rename', literal: 'literal',
  derived: 'derivada', 'join-key': 'llave join', passthrough: 'pasa directo',
}
const KIND_COLOR = {
  origin: '#22c55e', select: '#818cf8', rename: '#818cf8', literal: '#a855f7',
  derived: '#f59e0b', 'join-key': '#f59e0b', passthrough: '#64748b',
}

// Chip de nodo coloreado por tipo
function NodeChip({ id, type, theme, onClick }) {
  const color = TYPE_COLOR[(type || '').toUpperCase()] || '#64748b'
  return (
    <span
      onClick={onClick}
      title={type || ''}
      style={{
        padding: '2px 8px', borderRadius: 4, fontSize: 11, whiteSpace: 'nowrap',
        background: color + '22', color, border: `1px solid ${color}55`,
        cursor: onClick ? 'pointer' : 'default',
      }}>
      {id}
    </span>
  )
}

const ARROW = (t) => (
  <span style={{ color: t.dim || '#64748b', fontSize: 12 }}>→</span>
)

// Vista: linaje de NODOS (cadena aguas arriba / aguas abajo)
function NodesTab({ data, selectedId, theme, onPickNode }) {
  const t = theme || {}
  const lin = useMemo(() => nodeLineage(data, selectedId), [data, selectedId])
  const byId = useMemo(() => {
    const m = {}; (data?.nodes || []).forEach(n => { m[n.id] = n }); return m
  }, [data])

  const chainRow = (ids) => (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
      {ids.map((id, i) => (
        <span key={id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {i > 0 && ARROW(t)}
          <NodeChip id={id} type={byId[id]?.type} theme={t} onClick={() => onPickNode?.(id)} />
        </span>
      ))}
    </div>
  )

  if (!selectedId) {
    // Resumen global source -> sink
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <p style={{ fontSize: 11, color: t.dim || '#64748b', margin: 0 }}>
          Selecciona un nodo en el grafo para ver su linaje. Resumen global:
        </p>
        {lin.chains.map((c, i) => (
          <div key={i} style={{
            padding: 10, borderRadius: 8, background: t.bg || '#0f1117',
            border: `1px solid ${t.border || '#334155'}`,
          }}>
            <div style={{ fontSize: 10, color: t.dim || '#64748b', marginBottom: 6, textTransform: 'uppercase' }}>
              Hacia {c.sink}
            </div>
            {c.upstream.length === 0
              ? <span style={{ fontSize: 11, color: t.dim }}>sin dependencias</span>
              : c.upstream.map((lvl, j) => (
                <div key={j} style={{ marginBottom: 4 }}>{chainRow(lvl.ids)}</div>
              ))}
          </div>
        ))}
      </div>
    )
  }

  const n = byId[selectedId]
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <NodeChip id={selectedId} type={n?.type} theme={t} />
        <span style={{ fontSize: 11, color: t.dim || '#64748b' }}>{n?.type}</span>
      </div>

      <div>
        <div style={{ fontSize: 10, color: t.dim || '#64748b', textTransform: 'uppercase', marginBottom: 6 }}>
          ⬆ Aguas arriba (de dónde vienen los datos)
        </div>
        {lin.upstream.length === 0
          ? <span style={{ fontSize: 11, color: t.dim }}>es un origen (SOURCE)</span>
          : lin.upstream.map((lvl, j) => <div key={j} style={{ marginBottom: 4 }}>{chainRow(lvl.ids)}</div>)}
      </div>

      <div>
        <div style={{ fontSize: 10, color: t.dim || '#64748b', textTransform: 'uppercase', marginBottom: 6 }}>
          ⬇ Aguas abajo (a dónde van los datos)
        </div>
        {lin.downstream.length === 0
          ? <span style={{ fontSize: 11, color: t.dim }}>es un destino (SINK)</span>
          : lin.downstream.map((lvl, j) => <div key={j} style={{ marginBottom: 4 }}>{chainRow(lvl.ids)}</div>)}
      </div>
    </div>
  )
}

// Vista: linaje de COLUMNAS (out.col <- source.col)
function ColumnsTab({ data, selectedId, theme, onPickNode }) {
  const t = theme || {}
  const byId = useMemo(() => {
    const m = {}; (data?.nodes || []).forEach(n => { m[n.id] = n }); return m
  }, [data])

  if (!selectedId) {
    return (
      <p style={{ fontSize: 11, color: t.dim || '#64748b' }}>
        Selecciona un nodo en el grafo para ver el linaje de sus columnas
        (qué campo de salida viene de qué campo de entrada).
      </p>
    )
  }

  const lin = columnLineage(data, selectedId)
  if (!lin.rows.length) {
    return (
      <p style={{ fontSize: 11, color: t.dim || '#64748b' }}>
        No hay información de columnas para este nodo (falta la regla XFR o el DML).
      </p>
    )
  }

  const kindBadge = (k) => (
    <span style={{
      padding: '1px 6px', borderRadius: 3, fontSize: 9, textTransform: 'uppercase',
      background: (KIND_COLOR[k] || '#64748b') + '22',
      color: KIND_COLOR[k] || '#64748b',
      border: `1px solid ${(KIND_COLOR[k] || '#64748b')}44`,
    }}>{KIND_LABEL[k] || k}</span>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <NodeChip id={selectedId} type={byId[selectedId]?.type} theme={t} />
        {lin.joinKey && (
          <span style={{ fontSize: 10, color: '#f59e0b' }}>llave join: {lin.joinKey}</span>
        )}
        <span style={{ fontSize: 10, color: t.dim || '#64748b', marginLeft: 'auto' }}>
          {lin.rows.length} columnas
        </span>
      </div>

      {/* cabecera */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr auto 1.2fr auto',
        gap: 8, fontSize: 9, color: t.dim || '#64748b', textTransform: 'uppercase',
        padding: '0 4px 4px', borderBottom: `1px solid ${t.border || '#334155'}`,
      }}>
        <span>Columna salida</span><span></span><span>Procedencia</span><span>Tipo</span>
      </div>

      {lin.rows.map((r, i) => (
        <div key={i} style={{
          display: 'grid', gridTemplateColumns: '1fr auto 1.2fr auto',
          gap: 8, alignItems: 'center', padding: '5px 4px',
          borderBottom: `1px solid ${(t.border || '#334155')}44`, fontSize: 11,
        }}>
          <span style={{ color: t.text || '#e2e8f0', fontFamily: 'monospace' }}>{r.out}</span>
          {ARROW(t)}
          <span style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {r.from.length === 0
              ? <span style={{ color: t.dim, fontStyle: 'italic' }}>
                  {r.kind === 'origin' ? '(fuente)' : '(derivada / constante)'}
                </span>
              : r.from.map((f, j) => (
                <span key={j} title={byId[f.node]?.type}
                  onClick={() => onPickNode?.(f.node)}
                  style={{ cursor: 'pointer', color: t.muted || '#94a3b8', fontFamily: 'monospace' }}>
                  <span style={{ color: TYPE_COLOR[(byId[f.node]?.type || '').toUpperCase()] || '#64748b' }}>
                    {f.node}
                  </span>.{f.col}{j < r.from.length - 1 ? ', ' : ''}
                </span>
              ))}
          </span>
          {kindBadge(r.kind)}
        </div>
      ))}
    </div>
  )
}

// Menú de exportación de metadata a formatos de catálogo.
function ExportMenu({ data, theme }) {
  const t = theme || {}
  const [open, setOpen] = useState(false)

  const slug = ((data?.graph_name || 'grafo') + '').replace(/[^\w.-]+/g, '_')

  const doExport = (fmt) => {
    setOpen(false)
    let md
    try {
      md = buildAllMetadata(data)
    } catch (e) {
      alert('No se pudo generar la metadata: ' + e.message)
      return
    }
    if (fmt === 'bnx') downloadText(`${slug}.metadata.json`, JSON.stringify(md.canonical, null, 2), 'application/json')
    else if (fmt === 'openlineage') downloadText(`${slug}.openlineage.json`, JSON.stringify(md.openlineage, null, 2), 'application/json')
    else if (fmt === 'glue') downloadText(`${slug}_glue_catalog.py`, md.glue_script, 'text/x-python')
    else if (fmt === 'databricks') downloadText(`${slug}_unity_catalog.sql`, md.databricks_ddl, 'text/x-sql')
  }

  const item = (fmt, label, sub) => (
    <button onClick={() => doExport(fmt)} style={{
      display: 'block', width: '100%', textAlign: 'left', padding: '8px 12px',
      background: 'none', border: 'none', cursor: 'pointer',
      borderBottom: `1px solid ${(t.border || '#334155')}44`,
    }}>
      <div style={{ fontSize: 12, color: t.text || '#e2e8f0', fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 10, color: t.dim || '#64748b' }}>{sub}</div>
    </button>
  )

  return (
    <div style={{ position: 'relative' }}>
      <button onClick={() => setOpen(v => !v)} title="Exportar metadata" style={{
        background: 'none', border: `1px solid ${t.border || '#334155'}`,
        color: t.muted || '#94a3b8', fontSize: 11, cursor: 'pointer',
        padding: '3px 8px', borderRadius: 4,
      }}>⬇ Exportar</button>
      {open && (
        <div style={{
          position: 'absolute', top: '110%', right: 0, zIndex: 20, width: 230,
          background: t.sidebar || '#161b27', border: `1px solid ${t.border || '#334155'}`,
          borderRadius: 8, boxShadow: '0 8px 24px rgba(0,0,0,.35)', overflow: 'hidden',
        }}>
          {item('bnx', 'Metadata BNX (JSON)', 'Modelo canónico: grafo + columnas + linaje')}
          {item('openlineage', 'OpenLineage (JSON)', 'Estándar: Marquez, DataHub, etc.')}
          {item('glue', 'AWS Glue Catalog (boto3)', 'Script Python: crea tablas + metadata')}
          {item('databricks', 'Databricks Unity Catalog', 'DDL SQL: CREATE TABLE + COMMENT')}
        </div>
      )}
    </div>
  )
}

export default function LineagePanel({ data, selectedId, theme, onPickNode, collapsed, onToggle }) {
  const t = theme || {}
  const [tab, setTab] = useState('nodes')

  if (collapsed) {
    return (
      <button onClick={onToggle} title="Mostrar linaje" style={{
        position: 'absolute', top: 8, right: 8, zIndex: 11,
        padding: '6px 10px', borderRadius: 8, cursor: 'pointer', fontSize: 12,
        background: (t.card || '#1e2433') + 'ee', color: t.text || '#e2e8f0',
        border: `1px solid ${t.border || '#334155'}`, backdropFilter: 'blur(8px)',
      }}>🧬 Linaje</button>
    )
  }

  const tabBtn = (id, label) => (
    <button onClick={() => setTab(id)} style={{
      flex: 1, padding: '7px 10px', fontSize: 12, cursor: 'pointer', fontWeight: 600,
      background: tab === id ? '#6366f120' : 'transparent',
      border: 'none', borderBottom: `2px solid ${tab === id ? '#6366f1' : 'transparent'}`,
      color: tab === id ? '#818cf8' : (t.muted || '#94a3b8'),
    }}>{label}</button>
  )

  return (
    <div style={{
      width: 360, height: '100%', display: 'flex', flexDirection: 'column',
      background: t.sidebar || '#161b27',
      borderLeft: `1px solid ${t.border || '#334155'}`,
    }}>
      <div style={{
        padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 8,
        borderBottom: `1px solid ${t.border || '#334155'}`,
      }}>
        <span style={{ fontSize: 14 }}>🧬</span>
        <span style={{ fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0' }}>Linaje</span>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
          <ExportMenu data={data} theme={t} />
          <button onClick={onToggle} title="Ocultar" style={{
            background: 'none', border: 'none',
            color: t.muted || '#94a3b8', fontSize: 15, cursor: 'pointer',
          }}>⟩</button>
        </div>
      </div>

      <div style={{ display: 'flex', borderBottom: `1px solid ${t.border || '#334155'}` }}>
        {tabBtn('nodes', 'Nodos')}
        {tabBtn('columns', 'Columnas')}
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 14 }}>
        {tab === 'nodes'
          ? <NodesTab data={data} selectedId={selectedId} theme={t} onPickNode={onPickNode} />
          : <ColumnsTab data={data} selectedId={selectedId} theme={t} onPickNode={onPickNode} />}
      </div>
    </div>
  )
}
