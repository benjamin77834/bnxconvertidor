import { useMemo, useEffect, useState, useCallback } from 'react'
import ReactFlow, {
  Background, Controls, MiniMap,
  MarkerType, useNodesState, useEdgesState
} from 'reactflow'
import 'reactflow/dist/style.css'

// ── Banking Operating Model ─────────────────────────────────
const LAYERS = [
  {
    name: 'Fuentes (Mainframe / Core)',
    color: '#22c55e',
    y: 0,
    nodes: [
      { id: 'CORE_BANKING', label: 'Core Banking\n(AS/400)', desc: 'Cuentas, saldos, movimientos' },
      { id: 'CARD_SYSTEM', label: 'Card System\n(COBOL)', desc: 'Tarjetas, autorizaciones' },
      { id: 'LOAN_SYSTEM', label: 'Loan System\n(DB2)', desc: 'Créditos, amortizaciones' },
      { id: 'PAYMENT_HUB', label: 'Payment Hub\n(SWIFT/SPEI)', desc: 'Transferencias, pagos' },
      { id: 'CRM', label: 'CRM\n(Salesforce)', desc: 'Clientes, segmentos' },
      { id: 'FRAUD_ENGINE', label: 'Fraud Engine\n(Real-time)', desc: 'Alertas, scores' },
      { id: 'KAFKA_EVENTS', label: 'Kafka\n(Eventos)', desc: 'Clicks, logins, txns' },
    ]
  },
  {
    name: 'Ingestion Layer',
    color: '#06b6d4',
    y: 140,
    nodes: [
      { id: 'INGEST_BATCH', label: 'Batch Ingestion\n(Ab Initio → Spark)', desc: 'COBOL/EBCDIC → Parquet' },
      { id: 'INGEST_CDC', label: 'CDC Ingestion\n(Debezium)', desc: 'Change Data Capture' },
      { id: 'INGEST_STREAM', label: 'Stream Ingestion\n(Kafka Connect)', desc: 'Real-time events' },
    ]
  },
  {
    name: 'Raw Zone (Data Lake)',
    color: '#6366f1',
    y: 280,
    nodes: [
      { id: 'RAW_ACCOUNTS', label: 'Raw Accounts', desc: 'S3: raw/accounts/' },
      { id: 'RAW_CARDS', label: 'Raw Cards', desc: 'S3: raw/cards/' },
      { id: 'RAW_LOANS', label: 'Raw Loans', desc: 'S3: raw/loans/' },
      { id: 'RAW_PAYMENTS', label: 'Raw Payments', desc: 'S3: raw/payments/' },
      { id: 'RAW_CUSTOMERS', label: 'Raw Customers', desc: 'S3: raw/customers/' },
      { id: 'RAW_FRAUD', label: 'Raw Fraud', desc: 'S3: raw/fraud/' },
      { id: 'RAW_EVENTS', label: 'Raw Events', desc: 'S3: raw/events/' },
    ]
  },
  {
    name: 'Curated Zone (BNX Transforms)',
    color: '#f59e0b',
    y: 420,
    nodes: [
      { id: 'CLEAN_DEDUP', label: 'Clean + Dedup', desc: 'BNX: TRANSFORM + DEDUP' },
      { id: 'NORMALIZE', label: 'Normalize', desc: 'BNX: NORMALIZE (EBCDIC→UTF8)' },
      { id: 'ENRICH_JOIN', label: 'Enrich + Join', desc: 'BNX: JOIN + LOOKUP' },
      { id: 'AGGREGATE', label: 'Aggregate', desc: 'BNX: GROUP BY + Rollup' },
      { id: 'VALIDATE', label: 'Validate', desc: 'BNX: Semantic Validator' },
    ]
  },
  {
    name: 'Business Zone (Modelos)',
    color: '#a855f7',
    y: 560,
    nodes: [
      { id: 'DIM_CUSTOMER', label: 'Dim Customer\n360°', desc: 'Perfil completo del cliente' },
      { id: 'DIM_PRODUCT', label: 'Dim Product', desc: 'Catálogo de productos' },
      { id: 'FACT_TX', label: 'Fact Transactions', desc: 'Movimientos normalizados' },
      { id: 'FACT_BALANCE', label: 'Fact Balances', desc: 'Saldos diarios' },
      { id: 'MODEL_RISK', label: 'Risk Model', desc: 'Score de riesgo crediticio' },
      { id: 'MODEL_AML', label: 'AML Model', desc: 'Anti Money Laundering' },
    ]
  },
  {
    name: 'Consumo (Reportes / APIs)',
    color: '#ef4444',
    y: 700,
    nodes: [
      { id: 'RPT_REGULATORY', label: 'Regulatory\nReports', desc: 'CNBV, Banxico, CONDUSEF' },
      { id: 'RPT_RISK', label: 'Risk\nDashboard', desc: 'Tableau / QuickSight' },
      { id: 'RPT_FINANCE', label: 'Finance\nReports', desc: 'P&L, Balance Sheet' },
      { id: 'API_MOBILE', label: 'Mobile\nAPI', desc: 'App bancaria' },
      { id: 'API_OPENBANKING', label: 'Open\nBanking', desc: 'APIs PSD2/SPEI' },
      { id: 'KAFKA_OUT', label: 'Kafka\nOutput', desc: 'Eventos procesados' },
    ]
  },
]

const EDGES_DEF = [
  // Sources → Ingestion
  ['CORE_BANKING', 'INGEST_BATCH'], ['CARD_SYSTEM', 'INGEST_BATCH'], ['LOAN_SYSTEM', 'INGEST_BATCH'],
  ['PAYMENT_HUB', 'INGEST_CDC'], ['CRM', 'INGEST_CDC'],
  ['FRAUD_ENGINE', 'INGEST_STREAM'], ['KAFKA_EVENTS', 'INGEST_STREAM'],
  // Ingestion → Raw
  ['INGEST_BATCH', 'RAW_ACCOUNTS'], ['INGEST_BATCH', 'RAW_CARDS'], ['INGEST_BATCH', 'RAW_LOANS'],
  ['INGEST_CDC', 'RAW_PAYMENTS'], ['INGEST_CDC', 'RAW_CUSTOMERS'],
  ['INGEST_STREAM', 'RAW_FRAUD'], ['INGEST_STREAM', 'RAW_EVENTS'],
  // Raw → Curated
  ['RAW_ACCOUNTS', 'CLEAN_DEDUP'], ['RAW_CARDS', 'CLEAN_DEDUP'], ['RAW_LOANS', 'CLEAN_DEDUP'],
  ['RAW_PAYMENTS', 'NORMALIZE'], ['RAW_CUSTOMERS', 'NORMALIZE'],
  ['CLEAN_DEDUP', 'ENRICH_JOIN'], ['NORMALIZE', 'ENRICH_JOIN'],
  ['RAW_FRAUD', 'ENRICH_JOIN'], ['RAW_EVENTS', 'ENRICH_JOIN'],
  ['ENRICH_JOIN', 'AGGREGATE'], ['ENRICH_JOIN', 'VALIDATE'],
  // Curated → Business
  ['AGGREGATE', 'DIM_CUSTOMER'], ['AGGREGATE', 'DIM_PRODUCT'],
  ['VALIDATE', 'FACT_TX'], ['VALIDATE', 'FACT_BALANCE'],
  ['ENRICH_JOIN', 'MODEL_RISK'], ['ENRICH_JOIN', 'MODEL_AML'],
  // Business → Consumo
  ['FACT_TX', 'RPT_REGULATORY'], ['FACT_BALANCE', 'RPT_FINANCE'],
  ['MODEL_RISK', 'RPT_RISK'], ['MODEL_AML', 'RPT_REGULATORY'],
  ['DIM_CUSTOMER', 'API_MOBILE'], ['DIM_CUSTOMER', 'API_OPENBANKING'],
  ['FACT_TX', 'KAFKA_OUT'], ['MODEL_AML', 'KAFKA_OUT'],
]

function buildModel(theme) {
  const t = theme || {}
  const nodes = []
  const edges = []

  LAYERS.forEach(layer => {
    const count = layer.nodes.length
    const totalWidth = count * 160
    const startX = (900 - totalWidth) / 2

    layer.nodes.forEach((n, i) => {
      nodes.push({
        id: n.id,
        position: { x: startX + i * 160, y: layer.y },
        data: { label: n.label, desc: n.desc, layer: layer.name },
        style: {
          background: layer.color + '18',
          border: `2px solid ${layer.color}`,
          borderRadius: 8,
          color: t.text || '#e2e8f0',
          fontSize: 11,
          padding: '8px 10px',
          minWidth: 130,
          textAlign: 'center',
          whiteSpace: 'pre-line',
        }
      })
    })
  })

  EDGES_DEF.forEach(([src, tgt], i) => {
    edges.push({
      id: `e${i}`,
      source: src,
      target: tgt,
      markerEnd: { type: MarkerType.ArrowClosed, color: '#47556980' },
      style: { stroke: '#47556980', strokeWidth: 1.2 },
    })
  })

  return { nodes, edges }
}

export default function BankingModelPage({ theme }) {
  const t = theme || {}
  const { nodes: initNodes, edges: initEdges } = useMemo(() => buildModel(t), [t])
  const [nodes, setNodes, onNodesChange] = useNodesState(initNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initEdges)
  const [editNode, setEditNode] = useState(null)

  useEffect(() => { setNodes(initNodes) }, [initNodes, setNodes])
  useEffect(() => { setEdges(initEdges) }, [initEdges, setEdges])

  const updateNode = useCallback((id, label, desc) => {
    setNodes(nds => nds.map(n =>
      n.id === id ? { ...n, data: { ...n.data, label, desc } } : n
    ))
    setEditNode(null)
  }, [setNodes])

  const onNodeClick = useCallback((_, node) => {
    setEditNode(node)
  }, [])

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      {/* Title overlay */}
      <div style={{
        position: 'absolute', top: 16, left: 16, zIndex: 10,
        background: t.sidebar || '#161b27', padding: '12px 20px',
        borderRadius: 10, border: `1px solid ${t.border || '#334155'}`,
        boxShadow: '0 4px 20px rgba(0,0,0,.3)',
      }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: t.text || '#e2e8f0' }}>
          🏦 Modelo Operativo Bancario — Data & Analytics
        </div>
        <div style={{ fontSize: 12, color: t.dim || '#64748b', marginTop: 4 }}>
          Click en un nodo para editar nombre y descripción
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
          {LAYERS.map(l => (
            <span key={l.name} style={{
              fontSize: 10, padding: '2px 8px', borderRadius: 4,
              background: l.color + '20', color: l.color, border: `1px solid ${l.color}40`,
            }}>{l.name}</span>
          ))}
        </div>
      </div>

      {/* Node editor */}
      {editNode && (() => {
        const layer = LAYERS.find(l => l.nodes.some(x => x.id === editNode.id))
        const color = layer?.color || '#64748b'
        let editLabel = editNode.data.label
        let editDesc = editNode.data.desc
        return (
          <div style={{
            position: 'absolute', top: 16, right: 16, zIndex: 10, width: 280,
            background: t.sidebar || '#161b27', borderRadius: 10,
            border: `1px solid ${t.border || '#334155'}`,
            boxShadow: '0 8px 32px rgba(0,0,0,.4)', overflow: 'hidden',
          }}>
            <div style={{
              padding: '10px 14px', background: color + '20',
              borderBottom: `1px solid ${t.border || '#334155'}`,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: t.text || '#e2e8f0' }}>
                ✏️ Edit Node
              </span>
              <button onClick={() => setEditNode(null)} style={{
                background: 'none', border: 'none', color: t.muted, fontSize: 16, cursor: 'pointer',
              }}>✕</button>
            </div>
            <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <label style={{ fontSize: 11, color: t.dim || '#64748b' }}>Layer</label>
                <span style={{
                  padding: '3px 8px', borderRadius: 4, fontSize: 11,
                  background: color + '20', color, border: `1px solid ${color}40`, alignSelf: 'flex-start',
                }}>{layer?.name}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <label style={{ fontSize: 11, color: t.dim || '#64748b' }}>Name</label>
                <textarea defaultValue={editLabel}
                  onChange={e => { editLabel = e.target.value }}
                  rows={2}
                  style={{
                    padding: '6px 10px', borderRadius: 6, fontSize: 13,
                    background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
                    color: t.text || '#e2e8f0', outline: 'none', resize: 'vertical',
                    fontFamily: 'inherit',
                  }}
                />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <label style={{ fontSize: 11, color: t.dim || '#64748b' }}>Description</label>
                <textarea defaultValue={editDesc}
                  onChange={e => { editDesc = e.target.value }}
                  rows={2}
                  style={{
                    padding: '6px 10px', borderRadius: 6, fontSize: 12,
                    background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
                    color: t.muted || '#94a3b8', outline: 'none', resize: 'vertical',
                    fontFamily: 'inherit',
                  }}
                />
              </div>
              <button onClick={() => updateNode(editNode.id, editLabel, editDesc)} style={{
                padding: '8px 16px', borderRadius: 6, cursor: 'pointer',
                background: color, color: '#fff', border: 'none', fontSize: 13, fontWeight: 600,
              }}>💾 Save</button>
            </div>
          </div>
        )
      })()}

      <ReactFlow
        nodes={nodes} edges={edges}
        onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={() => setEditNode(null)}
        fitView minZoom={0.3}
      >
        <Background color={t.flowBg || '#1e2433'} gap={20} />
        <Controls />
        <MiniMap
          nodeColor={n => {
            const layer = LAYERS.find(l => l.nodes.some(x => x.id === n.id))
            return layer?.color || '#64748b'
          }}
          style={{ background: t.card || '#1e2433' }}
        />
      </ReactFlow>
    </div>
  )
}
