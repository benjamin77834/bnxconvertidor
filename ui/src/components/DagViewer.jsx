import React, { useMemo } from 'react'
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

const SUBGRAPH_BG = [
  '#1e2d3d','#1e2d2d','#2d1e2d','#2d2d1e',
  '#1e1e2d','#2d1e1e','#1e2d1e','#2d2d2d',
]

function buildLayout(nodes, edges, subgraphs) {
  // Simple left-to-right layout by topological level
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

  // Count nodes per level for vertical spacing
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
        color: '#e2e8f0',
        fontSize: 11,
        padding: '6px 10px',
        minWidth: 120,
        textAlign: 'center',
      }
    }
  })

  const rfEdges = edges.map((e, i) => ({
    id: `e${i}`,
    source: e.from,
    target: e.to,
    markerEnd: { type: MarkerType.ArrowClosed, color: '#475569' },
    style: { stroke: '#475569', strokeWidth: 1.5 },
  }))

  return { rfNodes, rfEdges }
}

export default function DagViewer({ data }) {
  const { rfNodes, rfEdges } = useMemo(
    () => buildLayout(data.nodes, data.edges, data.subgraphs),
    [data]
  )

  const [nodes, , onNodesChange] = useNodesState(rfNodes)
  const [edges, , onEdgesChange] = useEdgesState(rfEdges)

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        minZoom={0.1}
      >
        <Background color="#1e2433" gap={20} />
        <Controls />
        <MiniMap
          nodeColor={n => {
            const orig = data.nodes.find(x => x.id === n.id)
            return TYPE_COLOR[orig?.type] || '#64748b'
          }}
          style={{ background: '#1e2433' }}
        />
      </ReactFlow>
    </div>
  )
}
