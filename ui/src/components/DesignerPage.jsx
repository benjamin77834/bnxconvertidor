import { useState, useCallback, useRef, useMemo } from 'react'
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

// Custom node with handles
function BnxNode({ data }) {
  const color = TYPE_COLOR[data.nodeType] || '#64748b'
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
      <Handle type="source" position={Position.Right} style={{ background: color }} />
    </div>
  )
}

const nodeTypes = { bnx: BnxNode }

function download(content, filename) {
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

export default function DesignerPage({ theme }) {
  const t = theme || {}
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [nodeCount, setNodeCount] = useState(0)
  const [selected, setSelected] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [target, setTarget] = useState('glue')
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
      id,
      type: 'bnx',
      position: { x: 100 + (nodeCount % 5) * 200, y: 80 + Math.floor(nodeCount / 5) * 120 },
      data: { label: name, nodeType: type },
    }])
    setNodeCount(c => c + 1)
    if (nameRef.current) nameRef.current.value = ''
  }, [nodeCount, setNodes])

  const deleteSelected = useCallback(() => {
    if (!selected) return
    setNodes(nds => nds.filter(n => n.id !== selected))
    setEdges(eds => eds.filter(e => e.source !== selected && e.target !== selected))
    setSelected(null)
  }, [selected, setNodes, setEdges])

  // Export to .mp format
  const exportMp = useCallback(() => {
    let mp = '# Auto-generated from BNX Designer\n\n'
    nodes.forEach(n => {
      mp += `NODE ${n.data.label} : ${n.data.nodeType}\n`
    })
    mp += '\n'
    edges.forEach(e => {
      const src = nodes.find(n => n.id === e.source)
      const tgt = nodes.find(n => n.id === e.target)
      if (src && tgt) mp += `${src.data.label} -> ${tgt.data.label}\n`
    })
    return mp
  }, [nodes, edges])

  const handleExport = useCallback(() => {
    download(exportMp(), 'design.mp')
  }, [exportMp])

  const handleCompile = useCallback(async () => {
    setLoading(true)
    const mp = exportMp()
    const blob = new Blob([mp], { type: 'text/plain' })
    const file = new File([blob], 'design.mp')
    const form = new FormData()
    form.append('mp', file)
    form.append('target', target)
    try {
      const res = await fetch(COMPILE_URL, { method: 'POST', body: form })
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setResult({ errors: [`Error: ${e.message}`] })
    } finally { setLoading(false) }
  }, [exportMp, target])

  const btn = (label, onClick, color = t.muted) => (
    <button onClick={onClick} style={{
      padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 12,
      background: 'transparent', border: `1px solid ${color}40`, color,
    }}>{label}</button>
  )

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* Toolbar */}
      <div style={{
        width: 280, padding: 16, background: t.sidebar || '#161b27',
        borderRight: `1px solid ${t.border || '#334155'}`,
        display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto',
      }}>
        <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1 }}>
          Add Node
        </span>
        <input ref={nameRef} placeholder="Node name..."
          style={{
            padding: '8px 12px', borderRadius: 6, fontSize: 13,
            background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
            color: t.text || '#e2e8f0', outline: 'none',
          }}
          onKeyDown={e => { if (e.key === 'Enter') addNode('TRANSFORM') }}
        />
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {Object.keys(TYPE_COLOR).map(type => (
            <button key={type} onClick={() => addNode(type)} style={{
              padding: '5px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 11,
              background: TYPE_COLOR[type] + '20', border: `1px solid ${TYPE_COLOR[type]}40`,
              color: TYPE_COLOR[type], fontWeight: 600,
            }}>
              {TYPE_ICON[type]} {type}
            </button>
          ))}
        </div>

        <span style={{ fontSize: 14, color: t.muted, textTransform: 'uppercase', letterSpacing: 1, marginTop: 8 }}>
          Actions
        </span>
        {btn('🗑️ Delete Selected', deleteSelected, '#ef4444')}

        <div style={{ display: 'flex', gap: 6 }}>
          {['glue', 'spark'].map(tgt => (
            <button key={tgt} onClick={() => setTarget(tgt)} style={{
              flex: 1, padding: '6px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 12,
              background: target === tgt ? (t.accent || '#6366f1') + '20' : 'transparent',
              border: `1px solid ${target === tgt ? (t.accent || '#6366f1') : (t.border || '#334155')}`,
              color: target === tgt ? (t.accent || '#6366f1') : (t.muted || '#94a3b8'),
              fontWeight: target === tgt ? 600 : 400,
            }}>
              {tgt === 'glue' ? '🔧 Glue' : '⚡ Spark'}
            </button>
          ))}
        </div>

        <button onClick={handleCompile} disabled={nodes.length === 0 || loading} style={{
          padding: '10px 20px', borderRadius: 8, cursor: nodes.length > 0 ? 'pointer' : 'not-allowed',
          background: nodes.length > 0 ? (t.accent || '#6366f1') : (t.border || '#334155'),
          color: '#fff', border: 'none', fontSize: 14, fontWeight: 600,
        }}>
          {loading ? '⏳ Compiling...' : '🚀 Compile Graph'}
        </button>

        {btn('📥 Export .mp', handleExport, '#22c55e')}

        {/* Stats */}
        <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>
          {nodes.length} nodes · {edges.length} edges
        </div>

        {/* Errors/Warnings */}
        {result?.errors?.length > 0 && (
          <div style={{
            padding: 8, borderRadius: 6, fontSize: 12,
            background: '#7f1d1d30', border: '1px solid #ef444440', color: '#fca5a5',
          }}>
            {result.errors.map((e, i) => <div key={i}>{e}</div>)}
          </div>
        )}
        {result?.warnings?.length > 0 && (
          <div style={{
            padding: 8, borderRadius: 6, fontSize: 12,
            background: '#78350f30', border: '1px solid #f59e0b40', color: '#fcd34d',
          }}>
            {result.warnings.map((w, i) => <div key={i}>{w}</div>)}
          </div>
        )}

        {/* Accuracy */}
        {result?.accuracy && (
          <div style={{
            padding: 8, borderRadius: 6, fontSize: 12,
            background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
          }}>
            <span style={{
              fontSize: 20, fontWeight: 700,
              color: result.accuracy.overall_accuracy >= 90 ? '#22c55e' : '#f59e0b',
            }}>{result.accuracy.overall_accuracy}%</span>
            <span style={{ fontSize: 11, color: t.dim || '#64748b', marginLeft: 6 }}>accuracy</span>
          </div>
        )}
      </div>

      {/* Canvas + Code */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, n) => setSelected(n.id)}
            onPaneClick={() => setSelected(null)}
            nodeTypes={nodeTypes}
            fitView
            minZoom={0.2}
          >
            <Background color={t.flowBg || '#1e2433'} gap={20} />
            <Controls />
            <MiniMap
              nodeColor={() => '#6366f1'}
              style={{ background: t.card || '#1e2433' }}
            />
          </ReactFlow>
        </div>

        {/* Generated code */}
        {result?.code && (
          <div style={{
            height: '35vh', borderTop: `1px solid ${t.border || '#334155'}`,
            background: t.codeBg || '#0d1017', display: 'flex', flexDirection: 'column',
          }}>
            <div style={{
              padding: '8px 16px', background: t.sidebar || '#161b27',
              borderBottom: `1px solid ${t.border || '#334155'}`,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span style={{ fontSize: 12, color: t.muted, textTransform: 'uppercase' }}>
                Generated {target === 'spark' ? 'PySpark' : 'Glue'} Code ({result.code.split('\n').length} lines)
              </span>
              <button onClick={() => download(result.code, target === 'spark' ? 'pyspark_job.py' : 'glue_job.py')}
                style={{
                  padding: '3px 10px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
                  background: 'transparent', border: `1px solid ${t.border || '#334155'}`,
                  color: t.muted || '#94a3b8',
                }}>📥 Download</button>
            </div>
            <pre style={{
              padding: 16, fontSize: 13, color: t.muted || '#94a3b8',
              fontFamily: 'monospace', whiteSpace: 'pre', overflowY: 'auto',
              flex: 1, lineHeight: 1.6, margin: 0,
            }}>{result.code}</pre>
          </div>
        )}
      </div>
    </div>
  )
}
