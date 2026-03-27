import { useMemo, useEffect, useState, useCallback } from 'react'
import ReactFlow, {
  Background, Controls, MiniMap,
  MarkerType, useNodesState, useEdgesState
} from 'reactflow'
import 'reactflow/dist/style.css'

const TYPE_COLOR = {
  SOURCE:    '#22c55e',
  TRANSFORM: '#6366f1',
  XFR:       '#6366f1',
  JOIN:      '#f59e0b',
  SINK:      '#ef4444',
}

const TYPE_ICON = {
  SOURCE: '📂', TRANSFORM: '🔄', XFR: '🔄', JOIN: '🔗', SINK: '💾',
}

function buildLayout(nodes, edges, theme) {
  const t = theme || {}
  const nodeTextColor = t.text || '#e2e8f0'

  const levelMap = {}
  const inDeg = {}
  nodes.forEach(n => { inDeg[n.id] = 0 })
  edges.forEach(e => { if (inDeg[e.to] !== undefined) inDeg[e.to]++ })

  const queue = nodes.filter(n => inDeg[n.id] === 0).map(n => n.id)
  let level = 0
  const visited = new Set()

  while (queue.length) {
    const next = []
    queue.forEach(id => {
      if (visited.has(id)) return
      visited.add(id)
      levelMap[id] = level
      edges.filter(e => e.from === id).forEach(e => {
        inDeg[e.to]--
        if (inDeg[e.to] === 0) next.push(e.to)
      })
    })
    queue.length = 0
    queue.push(...next)
    level++
  }

  const levelCount = {}
  nodes.forEach(n => {
    const l = levelMap[n.id] ?? 0
    levelCount[l] = (levelCount[l] || 0) + 1
  })
  const levelIdx = {}

  const rfNodes = nodes.map(n => {
    const l = levelMap[n.id] ?? 0
    levelIdx[l] = (levelIdx[l] || 0) + 1
    const idx = levelIdx[l]
    const total = levelCount[l]
    const color = TYPE_COLOR[n.type] || '#64748b'

    return {
      id: n.id,
      position: { x: l * 220, y: (idx - (total + 1) / 2) * 80 },
      data: { label: n.name },
      style: {
        background: color + '22',
        border: `2px solid ${color}`,
        borderRadius: n.type === 'JOIN' ? 4 : 8,
        color: nodeTextColor,
        fontSize: 15,
        padding: '10px 16px',
        minWidth: 150,
        textAlign: 'center',
        cursor: 'pointer',
      }
    }
  })

  const edgeColor = t.muted || '#475569'
  const rfEdges = edges.map((e, i) => ({
    id: `e${i}`,
    source: e.from,
    target: e.to,
    markerEnd: { type: MarkerType.ArrowClosed, color: edgeColor },
    style: { stroke: edgeColor, strokeWidth: 1.5 },
  }))

  return { rfNodes, rfEdges }
}

function NodeDetail({ node, theme, onClose }) {
  const t = theme || {}
  const color = TYPE_COLOR[node.type] || '#64748b'
  const rule = node.rule || {}

  const row = (label, value) => (
    <div style={{ display: 'flex', gap: 8, fontSize: 12 }}>
      <span style={{ color: t.dim || '#64748b', minWidth: 70 }}>{label}</span>
      <span style={{ color: t.text || '#e2e8f0', wordBreak: 'break-all' }}>{value || '—'}</span>
    </div>
  )

  return (
    <div style={{
      position: 'absolute', top: 12, right: 12, zIndex: 10,
      width: 300, background: t.sidebar || '#161b27',
      border: `1px solid ${t.border || '#334155'}`,
      borderRadius: 10, overflow: 'hidden',
      boxShadow: '0 8px 32px rgba(0,0,0,.3)',
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px', background: color + '20',
        borderBottom: `1px solid ${t.border || '#334155'}`,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 16 }}>{TYPE_ICON[node.type] || '📦'}</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: t.text || '#e2e8f0' }}>{node.name}</span>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none', border: 'none', color: t.muted || '#94a3b8',
            fontSize: 16, cursor: 'pointer', padding: '0 4px',
          }}
        >✕</button>
      </div>

      {/* Body */}
      <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {row('Type', <span style={{
          padding: '1px 8px', borderRadius: 4, fontSize: 11,
          background: color + '20', color, border: `1px solid ${color}40`,
        }}>{node.type}</span>)}

        {node.subgraph && row('Subgraph', node.subgraph)}

        {row('Depth', node.parents?.length === 0 ? '0 (root)' : `${node.parents?.length} parent(s)`)}

        {node.parents?.length > 0 && row('Parents', node.parents.join(', '))}
        {node.children?.length > 0 && row('Children', node.children.join(', '))}

        {/* XFR Rule details */}
        {rule.select && (
          <div style={{
            marginTop: 4, padding: 8, borderRadius: 6,
            background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
          }}>
            <span style={{ fontSize: 10, color: t.dim || '#64748b', textTransform: 'uppercase' }}>Rule</span>
            {rule.select && (
              <div style={{ fontSize: 11, color: t.muted || '#94a3b8', marginTop: 4 }}>
                <span style={{ color: '#818cf8' }}>SELECT</span> {rule.select}
              </div>
            )}
            {rule.where && (
              <div style={{ fontSize: 11, color: t.muted || '#94a3b8', marginTop: 2 }}>
                <span style={{ color: '#f59e0b' }}>WHERE</span> {rule.where}
              </div>
            )}
            {rule.group_by && (
              <div style={{ fontSize: 11, color: t.muted || '#94a3b8', marginTop: 2 }}>
                <span style={{ color: '#22c55e' }}>GROUP BY</span> {Array.isArray(rule.group_by) ? rule.group_by.join(', ') : rule.group_by}
              </div>
            )}
          </div>
        )}

        {(rule.join_key || rule.join_type) && (
          <div style={{
            marginTop: 4, padding: 8, borderRadius: 6,
            background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
          }}>
            <span style={{ fontSize: 10, color: t.dim || '#64748b', textTransform: 'uppercase' }}>Join Config</span>
            {rule.join_key && (
              <div style={{ fontSize: 11, color: t.muted || '#94a3b8', marginTop: 4 }}>
                <span style={{ color: '#f59e0b' }}>KEY</span> {rule.join_key}
              </div>
            )}
            {rule.join_type && (
              <div style={{ fontSize: 11, color: t.muted || '#94a3b8', marginTop: 2 }}>
                <span style={{ color: '#f59e0b' }}>TYPE</span> {rule.join_type}
              </div>
            )}
          </div>
        )}

        {/* No rule */}
        {!rule.select && !rule.join_key && !rule.group_by && (
          <span style={{ fontSize: 11, color: t.dim || '#64748b', fontStyle: 'italic' }}>
            No transformation rule defined
          </span>
        )}
      </div>
    </div>
  )
}

export default function DagViewer({ data, theme }) {
  const t = theme || {}
  const [selected, setSelected] = useState(null)

  const { rfNodes, rfEdges } = useMemo(
    () => buildLayout(data.nodes, data.edges, t),
    [data, t]
  )

  const [nodes, setNodes, onNodesChange] = useNodesState(rfNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(rfEdges)

  useEffect(() => { setNodes(rfNodes) }, [rfNodes, setNodes])
  useEffect(() => { setEdges(rfEdges) }, [rfEdges, setEdges])

  const onNodeClick = useCallback((_, node) => {
    const full = data.nodes.find(n => n.id === node.id)
    setSelected(full || null)
  }, [data])

  const onPaneClick = useCallback(() => setSelected(null), [])

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        fitView
        minZoom={0.1}
      >
        <Background color={t.flowBg || '#1e2433'} gap={20} />
        <Controls />
        <MiniMap
          nodeColor={n => {
            const orig = data.nodes.find(x => x.id === n.id)
            return TYPE_COLOR[orig?.type] || '#64748b'
          }}
          style={{ background: t.card || '#1e2433' }}
        />
      </ReactFlow>

      {selected && (
        <NodeDetail node={selected} theme={t} onClose={() => setSelected(null)} />
      )}
    </div>
  )
}
