import { useState, useCallback, useRef } from 'react'
import ReactFlow, {
  Background, Controls, MiniMap,
  MarkerType, addEdge, useNodesState, useEdgesState,
  Handle, Position
} from 'reactflow'
import 'reactflow/dist/style.css'
import { COMPILE_URL } from '../config'

const TYPE_COLOR = {
  SOURCE: '#22c55e', TRANSFORM: '#6366f1', JOIN: '#f59e0b',
  DEDUP: '#06b6d4', NORMALIZE: '#a855f7', LOOKUP: '#ec4899', SINK: '#ef4444',
}
const TYPE_ICON = {
  SOURCE: '📂', TRANSFORM: '🔄', JOIN: '🔗',
  DEDUP: '🧹', NORMALIZE: '📐', LOOKUP: '🔍', SINK: '💾',
}

// Fields shown per node type in the editor
const TYPE_FIELDS = {
  SOURCE:    ['source_type', 'path', 'format', 'topic', 'table', 'connection'],
  TRANSFORM: ['select', 'where', 'group_by'],
  JOIN:      ['join_key', 'join_type'],
  DEDUP:     ['dedup_keys', 'order_by'],
  NORMALIZE: ['explode_col', 'split_col', 'delimiter'],
  LOOKUP:    ['lookup_key', 'lookup_select'],
  SINK:      ['sink_type', 'path', 'format', 'topic', 'table', 'connection', 'mode'],
}

const FIELD_LABELS = {
  select: 'SELECT', where: 'WHERE', group_by: 'GROUP BY',
  join_key: 'Join Key', join_type: 'Join Type',
  dedup_keys: 'Dedup Keys', order_by: 'Order By',
  explode_col: 'Explode Column', split_col: 'Split Column', delimiter: 'Delimiter',
  lookup_key: 'Lookup Key', lookup_select: 'Lookup Select',
  source_type: 'Source Type (s3/jdbc/kafka)', path: 'Path / URI',
  format: 'Format (parquet/csv/json/avro)', topic: 'Kafka Topic',
  table: 'Table Name', connection: 'Connection String',
  sink_type: 'Sink Type (s3/jdbc/kafka)', mode: 'Write Mode (overwrite/append)',
}

function BnxNode({ data }) {
  const color = TYPE_COLOR[data.nodeType] || '#64748b'
  const hasRule = data.rule && Object.values(data.rule).some(v => v)
  return (
    <div style={{
      background: color + '20', border: `2px solid ${color}`,
      borderRadius: 8, padding: '8px 14px', minWidth: 140, textAlign: 'center',
      fontSize: 13, color: '#e2e8f0',
    }}>
      <Handle type="target" position={Position.Left} style={{ background: color }} />
      <div style={{ fontSize: 10, color, fontWeight: 600, marginBottom: 2 }}>
        {TYPE_ICON[data.nodeType]} {data.nodeType}
      </div>
      <div style={{ fontWeight: 600 }}>{data.label}</div>
      {hasRule && <div style={{ fontSize: 9, color: '#22c55e', marginTop: 2 }}>✓ configured</div>}
      <Handle type="source" position={Position.Right} style={{ background: color }} />
    </div>
  )
}

const nodeTypes = { bnx: BnxNode }

function dl(content, filename) {
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

// ── Node Editor Panel ───────────────────────────────────────
function NodeEditor({ node, theme, onUpdate, onClose }) {
  const t = theme || {}
  const data = node.data
  const color = TYPE_COLOR[data.nodeType] || '#64748b'
  const fields = TYPE_FIELDS[data.nodeType] || []
  const [rule, setRule] = useState(data.rule || {})
  const [name, setName] = useState(data.label)

  const save = () => {
    onUpdate(node.id, { ...data, label: name, rule })
    onClose()
  }

  const input = (key) => (
    <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <label style={{ fontSize: 11, color: t.dim || '#64748b' }}>{FIELD_LABELS[key]}</label>
      <input
        value={rule[key] || ''}
        onChange={e => setRule(r => ({ ...r, [key]: e.target.value }))}
        placeholder={key === 'join_type' ? 'inner / left / right' : `Enter ${key}...`}
        style={{
          padding: '6px 10px', borderRadius: 6, fontSize: 12,
          background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
          color: t.text || '#e2e8f0', outline: 'none',
        }}
      />
    </div>
  )

  return (
    <div style={{
      position: 'absolute', top: 10, right: 10, zIndex: 10, width: 280,
      background: t.sidebar || '#161b27', border: `1px solid ${t.border || '#334155'}`,
      borderRadius: 10, boxShadow: '0 8px 32px rgba(0,0,0,.4)', overflow: 'hidden',
    }}>
      <div style={{
        padding: '10px 14px', background: color + '20',
        borderBottom: `1px solid ${t.border || '#334155'}`,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: t.text || '#e2e8f0' }}>
          {TYPE_ICON[data.nodeType]} Edit Node
        </span>
        <button onClick={onClose} style={{
          background: 'none', border: 'none', color: t.muted, fontSize: 16, cursor: 'pointer',
        }}>✕</button>
      </div>
      <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <label style={{ fontSize: 11, color: t.dim || '#64748b' }}>Name</label>
          <input value={name} onChange={e => setName(e.target.value)}
            style={{
              padding: '6px 10px', borderRadius: 6, fontSize: 13, fontWeight: 600,
              background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
              color: t.text || '#e2e8f0', outline: 'none',
            }}
          />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <label style={{ fontSize: 11, color: t.dim || '#64748b' }}>Type</label>
          <span style={{
            padding: '4px 10px', borderRadius: 4, fontSize: 12, fontWeight: 600,
            background: color + '20', color, border: `1px solid ${color}40`, alignSelf: 'flex-start',
          }}>{data.nodeType}</span>
        </div>
        {fields.length > 0 && (
          <>
            <div style={{ height: 1, background: t.border || '#334155', margin: '4px 0' }} />
            <span style={{ fontSize: 11, color: t.dim || '#64748b', textTransform: 'uppercase' }}>
              Rules
            </span>
            {fields.map(f => input(f))}
          </>
        )}
        <button onClick={save} style={{
          marginTop: 4, padding: '8px 16px', borderRadius: 6, cursor: 'pointer',
          background: color, color: '#fff', border: 'none', fontSize: 13, fontWeight: 600,
        }}>💾 Save</button>
      </div>
    </div>
  )
}

// ── Main Designer ───────────────────────────────────────────
export default function DesignerPage({ theme }) {
  const t = theme || {}
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [nodeCount, setNodeCount] = useState(0)
  const [editNode, setEditNode] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [target, setTarget] = useState('glue')
  const [codeOpen, setCodeOpen] = useState(false)
  const [showCodeModal, setShowCodeModal] = useState(false)
  const [designs, setDesigns] = useState(() => {
    try { return JSON.parse(localStorage.getItem('bnx_designs') || '[]') } catch { return [] }
  })
  const [showDesigns, setShowDesigns] = useState(false)
  const [designName, setDesignName] = useState('')
  const nameRef = useRef(null)
  const loadRef = useRef(null)

  const saveDesign = useCallback(() => {
    const name = designName.trim() || `Design ${designs.length + 1}`
    const snapshot = {
      name,
      date: new Date().toISOString(),
      nodes: nodes.map(n => ({ id: n.id, type: n.type, position: n.position, data: n.data })),
      edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target })),
      nodeCount,
    }
    const updated = [snapshot, ...designs].slice(0, 20)
    setDesigns(updated)
    localStorage.setItem('bnx_designs', JSON.stringify(updated))
    setDesignName('')
  }, [nodes, edges, nodeCount, designs, designName])

  const loadDesign = useCallback((d) => {
    setNodes(d.nodes.map(n => ({
      ...n,
      style: undefined, // let BnxNode handle style
    })))
    setEdges(d.edges.map(e => ({
      ...e,
      markerEnd: { type: MarkerType.ArrowClosed, color: '#475569' },
      style: { stroke: '#475569', strokeWidth: 2 },
    })))
    setNodeCount(d.nodeCount || d.nodes.length)
    setShowDesigns(false)
    setEditNode(null)
    setResult(null)
  }, [setNodes, setEdges])

  const deleteDesign = useCallback((idx) => {
    const updated = designs.filter((_, i) => i !== idx)
    setDesigns(updated)
    localStorage.setItem('bnx_designs', JSON.stringify(updated))
  }, [designs])

  const importDesign = useCallback((e) => {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      try {
        const d = JSON.parse(ev.target.result)
        if (d.nodes && d.edges) loadDesign(d)
      } catch { alert('Invalid design file') }
    }
    reader.readAsText(file)
    e.target.value = ''
  }, [loadDesign])

  const exportDesign = useCallback(() => {
    const data = {
      name: designName.trim() || 'BNX Design',
      date: new Date().toISOString(),
      nodes: nodes.map(n => ({ id: n.id, type: n.type, position: n.position, data: n.data })),
      edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target })),
      nodeCount,
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'design.json'; a.click()
    URL.revokeObjectURL(url)
  }, [nodes, edges, nodeCount, designName])

  const onConnect = useCallback((params) => {
    setEdges(eds => addEdge({
      ...params,
      markerEnd: { type: MarkerType.ArrowClosed, color: '#475569' },
      style: { stroke: '#475569', strokeWidth: 2 },
    }, eds))
  }, [setEdges])

  const addNode = useCallback((type) => {
    const id = `node_${nodeCount}`
    const name = nameRef.current?.value?.trim() || `${type}_${nodeCount}`
    setNodes(nds => [...nds, {
      id, type: 'bnx',
      position: { x: 100 + (nodeCount % 5) * 200, y: 80 + Math.floor(nodeCount / 5) * 120 },
      data: { label: name, nodeType: type, rule: {} },
    }])
    setNodeCount(c => c + 1)
    if (nameRef.current) nameRef.current.value = ''
  }, [nodeCount, setNodes])

  const updateNodeData = useCallback((id, newData) => {
    setNodes(nds => nds.map(n => n.id === id ? { ...n, data: newData } : n))
  }, [setNodes])

  const deleteSelected = useCallback(() => {
    if (!editNode) return
    setNodes(nds => nds.filter(n => n.id !== editNode.id))
    setEdges(eds => eds.filter(e => e.source !== editNode.id && e.target !== editNode.id))
    setEditNode(null)
  }, [editNode, setNodes, setEdges])

  // Export .mp + .xfr
  const exportFiles = useCallback(() => {
    let mp = '# Auto-generated from BNX Designer\n\n'
    let xfr = '# Auto-generated from BNX Designer\n\n'

    nodes.forEach(n => {
      mp += `NODE ${n.data.label} : ${n.data.nodeType}\n`
    })
    mp += '\n'
    edges.forEach(e => {
      const src = nodes.find(n => n.id === e.source)
      const tgt = nodes.find(n => n.id === e.target)
      if (src && tgt) mp += `${src.data.label} -> ${tgt.data.label}\n`
    })

    nodes.forEach(n => {
      const r = n.data.rule || {}
      const hasRule = Object.values(r).some(v => v)
      if (!hasRule) return
      xfr += `${n.data.label}:\n`
      if (r.select) xfr += `  select ${r.select}\n`
      if (r.where) xfr += `  where ${r.where}\n`
      if (r.group_by) xfr += `  group_by ${r.group_by}\n`
      if (r.join_key) xfr += `  join_key ${r.join_key}\n`
      if (r.join_type) xfr += `  join_type ${r.join_type}\n`
      if (r.dedup_keys) xfr += `  dedup_keys ${r.dedup_keys}\n`
      if (r.order_by) xfr += `  order_by ${r.order_by}\n`
      if (r.explode_col) xfr += `  explode_col ${r.explode_col}\n`
      if (r.split_col) xfr += `  split_col ${r.split_col}\n`
      if (r.delimiter) xfr += `  delimiter ${r.delimiter}\n`
      if (r.lookup_key) xfr += `  lookup_key ${r.lookup_key}\n`
      if (r.lookup_select) xfr += `  lookup_select ${r.lookup_select}\n`
      xfr += '\n'
    })

    // Generate DML from SOURCE nodes
    let dml = 'keys:\n'
    const sources = nodes.filter(n => n.data.nodeType === 'SOURCE')
    sources.forEach(n => {
      const r = n.data.rule || {}
      const select = r.select || ''
      const cols = select ? select.split(',').map(c => c.trim()).filter(c => c) : []
      if (cols.length > 0) {
        dml += `  ${n.data.label}: ${cols[0]}\n`
      }
    })
    dml += '\nschema:\n'
    sources.forEach(n => {
      const r = n.data.rule || {}
      const select = r.select || ''
      const cols = select ? select.split(',').map(c => c.trim()).filter(c => c) : []
      if (cols.length > 0) {
        dml += `  ${n.data.label}:\n`
        cols.forEach(c => { dml += `    ${c}: string\n` })
        dml += '\n'
      }
    })

    return { mp, xfr, dml }
  }, [nodes, edges])

  const handleCompile = useCallback(async () => {
    setLoading(true)
    const { mp, xfr, dml } = exportFiles()
    const form = new FormData()
    form.append('mp', new File([mp], 'design.mp'))
    if (xfr.trim().split('\n').length > 2) {
      form.append('xfr', new File([xfr], 'design.xfr'))
    }
    if (dml.trim().split('\n').length > 3) {
      form.append('dml', new File([dml], 'design.dml'))
    }
    form.append('target', target)
    try {
      const res = await fetch(COMPILE_URL, { method: 'POST', body: form })
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setResult({ errors: [`Error: ${e.message}`] })
    } finally { setLoading(false) }
  }, [exportFiles, target])

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* Toolbar */}
      <div style={{
        width: 180, minWidth: 180, padding: 10, background: t.sidebar || '#161b27',
        borderRight: `1px solid ${t.border || '#334155'}`,
        display: 'flex', flexDirection: 'column', gap: 10, overflowY: 'auto', flexShrink: 0,
      }}>
        <span style={{ fontSize: 13, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>Add Node</span>
        <input ref={nameRef} placeholder="Node name..."
          style={{
            padding: '7px 10px', borderRadius: 6, fontSize: 12,
            background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
            color: t.text || '#e2e8f0', outline: 'none',
          }}
          onKeyDown={e => { if (e.key === 'Enter') addNode('TRANSFORM') }}
        />
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {Object.keys(TYPE_COLOR).map(type => (
            <button key={type} onClick={() => addNode(type)} style={{
              padding: '4px 8px', borderRadius: 5, cursor: 'pointer', fontSize: 10,
              background: TYPE_COLOR[type] + '20', border: `1px solid ${TYPE_COLOR[type]}40`,
              color: TYPE_COLOR[type], fontWeight: 600,
            }}>{TYPE_ICON[type]} {type}</button>
          ))}
        </div>

        <div style={{ height: 1, background: t.border || '#334155' }} />

        <div style={{ display: 'flex', gap: 4 }}>
          {['glue', 'spark'].map(tgt => (
            <button key={tgt} onClick={() => setTarget(tgt)} style={{
              flex: 1, padding: '5px 8px', borderRadius: 6, cursor: 'pointer', fontSize: 11,
              background: target === tgt ? (t.accent || '#6366f1') + '20' : 'transparent',
              border: `1px solid ${target === tgt ? (t.accent || '#6366f1') : (t.border || '#334155')}`,
              color: target === tgt ? (t.accent || '#6366f1') : (t.muted || '#94a3b8'),
              fontWeight: target === tgt ? 600 : 400,
            }}>{tgt === 'glue' ? '🔧 Glue' : '⚡ Spark'}</button>
          ))}
        </div>

        <button onClick={handleCompile} disabled={nodes.length === 0 || loading} style={{
          padding: '8px 16px', borderRadius: 8, cursor: nodes.length > 0 ? 'pointer' : 'not-allowed',
          background: nodes.length > 0 ? (t.accent || '#6366f1') : (t.border || '#334155'),
          color: '#fff', border: 'none', fontSize: 13, fontWeight: 600,
        }}>{loading ? '⏳...' : '🚀 Compile'}</button>

        <div style={{ display: 'flex', gap: 4 }}>
          <button onClick={() => { const f = exportFiles(); dl(f.mp, 'design.mp') }} style={{
            flex: 1, padding: '5px 8px', borderRadius: 6, cursor: 'pointer', fontSize: 11,
            background: 'transparent', border: `1px solid #22c55e40`, color: '#22c55e',
          }}>📥 .mp</button>
          <button onClick={() => { const f = exportFiles(); dl(f.xfr, 'design.xfr') }} style={{
            flex: 1, padding: '5px 8px', borderRadius: 6, cursor: 'pointer', fontSize: 11,
            background: 'transparent', border: `1px solid #6366f140`, color: '#6366f1',
          }}>📥 .xfr</button>
          <button onClick={() => { const f = exportFiles(); dl(f.dml, 'design.dml') }} style={{
            flex: 1, padding: '5px 8px', borderRadius: 6, cursor: 'pointer', fontSize: 11,
            background: 'transparent', border: `1px solid #f59e0b40`, color: '#f59e0b',
          }}>📥 .dml</button>
        </div>

        <div style={{ height: 1, background: t.border || '#334155' }} />

        {/* Save/Load designs */}
        <span style={{ fontSize: 11, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>Designs</span>
        <div style={{ display: 'flex', gap: 4 }}>
          <input value={designName} onChange={e => setDesignName(e.target.value)}
            placeholder="Name..."
            style={{
              flex: 1, padding: '4px 8px', borderRadius: 6, fontSize: 11,
              background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
              color: t.text || '#e2e8f0', outline: 'none',
            }}
            onKeyDown={e => { if (e.key === 'Enter') saveDesign() }}
          />
          <button onClick={saveDesign} style={{
            padding: '4px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: '#22c55e20', border: '1px solid #22c55e40', color: '#22c55e',
          }}>💾</button>
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          <button onClick={() => setShowDesigns(v => !v)} style={{
            flex: 1, padding: '4px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: '#6366f120', border: '1px solid #6366f140', color: '#818cf8',
          }}>📋 Load ({designs.length})</button>
          <button onClick={exportDesign} style={{
            flex: 1, padding: '4px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: '#f59e0b20', border: '1px solid #f59e0b40', color: '#f59e0b',
          }}>📥 JSON</button>
          <button onClick={() => loadRef.current?.click()} style={{
            padding: '4px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: '#06b6d420', border: '1px solid #06b6d440', color: '#06b6d4',
          }}>📂</button>
          <input ref={loadRef} type="file" accept=".json" hidden onChange={importDesign} />
        </div>

        {showDesigns && designs.length > 0 && (
          <div style={{
            maxHeight: 150, overflowY: 'auto', borderRadius: 6,
            border: `1px solid ${t.border || '#334155'}`,
          }}>
            {designs.map((d, i) => (
              <div key={i} style={{
                padding: '5px 8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                borderBottom: `1px solid ${t.border || '#334155'}20`, fontSize: 10,
              }}>
                <div>
                  <div style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>{d.name}</div>
                  <div style={{ color: t.dim || '#64748b', fontSize: 9 }}>{d.nodes.length}n · {d.edges.length}e</div>
                </div>
                <div style={{ display: 'flex', gap: 3 }}>
                  <button onClick={() => loadDesign(d)} style={{
                    padding: '2px 5px', borderRadius: 3, fontSize: 9, cursor: 'pointer',
                    background: '#22c55e20', border: '1px solid #22c55e40', color: '#22c55e',
                  }}>Load</button>
                  <button onClick={() => deleteDesign(i)} style={{
                    padding: '2px 5px', borderRadius: 3, fontSize: 9, cursor: 'pointer',
                    background: '#ef444420', border: '1px solid #ef444440', color: '#ef4444',
                  }}>✕</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {editNode && (
          <button onClick={deleteSelected} style={{
            padding: '5px 12px', borderRadius: 6, cursor: 'pointer', fontSize: 11,
            background: 'transparent', border: '1px solid #ef444440', color: '#ef4444',
          }}>🗑️ Delete "{editNode.data.label}"</button>
        )}

        <div style={{ fontSize: 11, color: t.dim || '#64748b' }}>
          {nodes.length} nodes · {edges.length} edges
        </div>

        {result?.errors?.length > 0 && (
          <div style={{ padding: 6, borderRadius: 6, fontSize: 11, background: '#7f1d1d30', border: '1px solid #ef444440', color: '#fca5a5' }}>
            {result.errors.map((e, i) => <div key={i}>{e}</div>)}
          </div>
        )}
        {result?.warnings?.length > 0 && (
          <div style={{ padding: 6, borderRadius: 6, fontSize: 11, background: '#78350f30', border: '1px solid #f59e0b40', color: '#fcd34d' }}>
            {result.warnings.map((w, i) => <div key={i}>{w}</div>)}
          </div>
        )}
        {result?.accuracy && (
          <div style={{ padding: 6, borderRadius: 6, fontSize: 11, background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}` }}>
            <span style={{ fontSize: 18, fontWeight: 700, color: result.accuracy.overall_accuracy >= 90 ? '#22c55e' : '#f59e0b' }}>
              {result.accuracy.overall_accuracy}%
            </span>
            <span style={{ fontSize: 10, color: t.dim || '#64748b', marginLeft: 4 }}>accuracy</span>
          </div>
        )}
      </div>

      {/* Canvas + Code — scrollable */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {/* Graph canvas — fixed height */}
        <div style={{ height: '100vh', width: 'calc(100vw - 180px)', position: 'relative' }}>
          <ReactFlow
            nodes={nodes} edges={edges}
            onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, n) => setEditNode(n)}
            onPaneClick={() => setEditNode(null)}
            nodeTypes={nodeTypes} fitView minZoom={0.2}
          >
            <Background color={t.flowBg || '#1e2433'} gap={20} />
            <Controls />
            <MiniMap nodeColor={() => '#6366f1'} style={{ background: t.card || '#1e2433' }} />
          </ReactFlow>

          {/* Node editor — floating top-right */}
          {editNode && (
            <NodeEditor
              node={editNode}
              theme={t}
              onUpdate={updateNodeData}
              onClose={() => setEditNode(null)}
            />
          )}
        </div>

        {/* Floating code button */}
        {result?.code && !showCodeModal && (
          <button onClick={() => setShowCodeModal(true)} style={{
            position: 'absolute', bottom: 16, right: 16, zIndex: 100,
            padding: '10px 18px', borderRadius: 10, cursor: 'pointer',
            background: t.accent || '#6366f1', color: '#fff', border: 'none',
            fontSize: 14, fontWeight: 600, boxShadow: '0 4px 20px rgba(0,0,0,.4)',
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            📄 View Code ({result.code.split('\n').length} lines)
          </button>
        )}

        {/* Code modal */}
        {showCodeModal && result?.code && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 200,
            background: 'rgba(0,0,0,.6)', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
          }} onClick={() => setShowCodeModal(false)}>
            <div style={{
              width: '80%', maxWidth: 800, maxHeight: '80vh',
              background: t.sidebar || '#161b27', borderRadius: 12,
              border: `1px solid ${t.border || '#334155'}`,
              boxShadow: '0 16px 48px rgba(0,0,0,.5)',
              display: 'flex', flexDirection: 'column', overflow: 'hidden',
            }} onClick={e => e.stopPropagation()}>
              <div style={{
                padding: '12px 20px', background: t.card || '#1e2433',
                borderBottom: `1px solid ${t.border || '#334155'}`,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <span style={{ fontSize: 14, fontWeight: 600, color: t.text || '#e2e8f0' }}>
                  {target === 'spark' ? '⚡ PySpark' : '🔧 Glue'} — {result.code.split('\n').length} lines
                </span>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button onClick={() => dl(result.code, target === 'spark' ? 'pyspark_job.py' : 'glue_job.py')}
                    style={{
                      padding: '4px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                      background: 'transparent', border: `1px solid #22c55e40`, color: '#22c55e',
                    }}>📥 Download</button>
                  <button onClick={() => setShowCodeModal(false)} style={{
                    background: 'none', border: 'none', color: t.muted, fontSize: 18, cursor: 'pointer',
                  }}>✕</button>
                </div>
              </div>
              <pre style={{
                padding: 20, fontSize: 13, color: t.muted || '#94a3b8',
                fontFamily: 'monospace', whiteSpace: 'pre', overflowY: 'auto',
                flex: 1, lineHeight: 1.7, margin: 0,
                background: t.codeBg || '#0d1017',
              }}>{result.code}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
