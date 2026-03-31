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
  SOURCE:    [],
  TRANSFORM: ['select', 'where', 'group_by'],
  JOIN:      ['join_key', 'join_type'],
  DEDUP:     ['dedup_keys', 'order_by'],
  NORMALIZE: ['explode_col', 'split_col', 'delimiter'],
  LOOKUP:    ['lookup_key', 'lookup_select'],
  SINK:      [],
}

const FIELD_LABELS = {
  select: 'SELECT', where: 'WHERE', group_by: 'GROUP BY',
  join_key: 'Join Key', join_type: 'Join Type',
  dedup_keys: 'Dedup Keys', order_by: 'Order By',
  explode_col: 'Explode Column', split_col: 'Split Column', delimiter: 'Delimiter',
  lookup_key: 'Lookup Key', lookup_select: 'Lookup Select',
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
  const nameRef = useRef(null)

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

    return { mp, xfr }
  }, [nodes, edges])

  const handleCompile = useCallback(async () => {
    setLoading(true)
    const { mp, xfr } = exportFiles()
    const form = new FormData()
    form.append('mp', new File([mp], 'design.mp'))
    if (xfr.trim().split('\n').length > 2) {
      form.append('xfr', new File([xfr], 'design.xfr'))
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
        </div>

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

      {/* Canvas */}
      <div style={{ flex: '1 1 0', position: 'relative', overflow: 'hidden' }}>
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

        {/* Code — floating bottom */}
        {result?.code && (
          <div style={{
            position: 'absolute', bottom: 0, left: 0, right: 0,
            maxHeight: codeOpen ? '50%' : 32,
            background: t.codeBg || '#0d1017',
            borderTop: `1px solid ${t.border || '#334155'}`,
            display: 'flex', flexDirection: 'column',
            transition: 'max-height .3s ease', overflow: 'hidden',
            zIndex: 5,
          }}>
            <div style={{
              padding: '6px 16px', background: t.sidebar || '#161b27',
              borderBottom: `1px solid ${t.border || '#334155'}`,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer',
              flexShrink: 0,
            }} onClick={() => setCodeOpen(o => !o)}>
              <span style={{ fontSize: 12, color: t.muted, textTransform: 'uppercase' }}>
                {target === 'spark' ? '⚡ PySpark' : '🔧 Glue'} ({result.code.split('\n').length} lines)
              </span>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <button onClick={(e) => { e.stopPropagation(); dl(result.code, target === 'spark' ? 'pyspark_job.py' : 'glue_job.py') }}
                  style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, cursor: 'pointer', background: 'transparent', border: `1px solid ${t.border || '#334155'}`, color: t.muted || '#94a3b8' }}>
                  📥
                </button>
                <span style={{ fontSize: 11, color: t.dim }}>{codeOpen ? '▼' : '▲'}</span>
              </div>
            </div>
            {codeOpen && (
              <pre style={{
                padding: 16, fontSize: 13, color: t.muted || '#94a3b8',
                fontFamily: 'monospace', whiteSpace: 'pre', overflowY: 'auto',
                flex: 1, lineHeight: 1.6, margin: 0,
              }}>{result.code}</pre>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
