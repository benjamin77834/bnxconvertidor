import { useMemo, useEffect, useState, useCallback } from 'react'
import ReactFlow, {
  Background, Controls, MiniMap,
  MarkerType, addEdge, useNodesState, useEdgesState
} from 'reactflow'
import 'reactflow/dist/style.css'
import GovernancePage from './GovernancePage'
import DamaPage from './DamaPage'

// ── Banking Operating Model ─────────────────────────────────
const LAYERS = [
  {
    name: 'Fuentes (Mainframe / Core)',
    color: '#22c55e',
    y: 0,
    nodes: [
      { id: 'CORE_BANKING', label: 'Core Banking\n(AS/400)', desc: 'Cuentas, saldos, movimientos' },
      { id: 'CARD_SYSTEM', label: 'Card System\n(COBOL/VSAM)', desc: 'Tarjetas, autorizaciones, límites' },
      { id: 'LOAN_SYSTEM', label: 'Loan System\n(DB2)', desc: 'Créditos, amortizaciones, garantías' },
      { id: 'PAYMENT_HUB', label: 'Payment Hub\n(SWIFT/SPEI)', desc: 'Transferencias, pagos interbancarios' },
      { id: 'CRM', label: 'CRM\n(Salesforce)', desc: 'Clientes, segmentos, campañas' },
      { id: 'FRAUD_ENGINE', label: 'Fraud Engine\n(Real-time)', desc: 'Alertas, scores, reglas' },
      { id: 'KAFKA_EVENTS', label: 'Kafka\n(Eventos)', desc: 'Clicks, logins, sesiones' },
      { id: 'TREASURY', label: 'Treasury\n(Murex)', desc: 'FX, derivados, posiciones' },
      { id: 'COMPLIANCE', label: 'Compliance\n(Actimize)', desc: 'KYC, PEP, sanciones' },
    ]
  },
  {
    name: 'AWS: Ingestion Layer',
    color: '#06b6d4',
    y: 150,
    nodes: [
      { id: 'DMS', label: '🔄 AWS DMS\n(Migration)', desc: 'DB2/Oracle → S3 full + CDC' },
      { id: 'TRANSFER', label: '📦 AWS Transfer\n(SFTP)', desc: 'Archivos EBCDIC/flat del mainframe' },
      { id: 'MSK', label: '📡 Amazon MSK\n(Kafka)', desc: 'Streaming de eventos real-time' },
      { id: 'KINESIS', label: '⚡ Kinesis\n(Firehose)', desc: 'Ingesta de clicks y logs' },
      { id: 'APPFLOW', label: '🔗 AppFlow\n(SaaS)', desc: 'Salesforce, SAP connectors' },
    ]
  },
  {
    name: 'AWS: Raw Zone (S3 Data Lake)',
    color: '#6366f1',
    y: 300,
    nodes: [
      { id: 'RAW_ACCOUNTS', label: '📂 Raw Accounts\n(S3/Parquet)', desc: 's3://datalake/raw/accounts/' },
      { id: 'RAW_CARDS', label: '📂 Raw Cards\n(S3/Parquet)', desc: 's3://datalake/raw/cards/' },
      { id: 'RAW_LOANS', label: '📂 Raw Loans\n(S3/Parquet)', desc: 's3://datalake/raw/loans/' },
      { id: 'RAW_PAYMENTS', label: '📂 Raw Payments\n(S3/Parquet)', desc: 's3://datalake/raw/payments/' },
      { id: 'RAW_CUSTOMERS', label: '📂 Raw Customers\n(S3/Parquet)', desc: 's3://datalake/raw/customers/' },
      { id: 'RAW_FRAUD', label: '📂 Raw Fraud\n(S3/JSON)', desc: 's3://datalake/raw/fraud/' },
      { id: 'RAW_EVENTS', label: '📂 Raw Events\n(S3/JSON)', desc: 's3://datalake/raw/events/' },
      { id: 'RAW_TREASURY', label: '📂 Raw Treasury\n(S3/CSV)', desc: 's3://datalake/raw/treasury/' },
      { id: 'RAW_COMPLIANCE', label: '📂 Raw Compliance\n(S3/Parquet)', desc: 's3://datalake/raw/compliance/' },
    ]
  },
  {
    name: 'AWS: Processing (Glue / EMR / BNX)',
    color: '#f59e0b',
    y: 450,
    nodes: [
      { id: 'GLUE_CLEAN', label: '🔧 Glue Job\nClean + Dedup', desc: 'BNX: TRANSFORM + DEDUP' },
      { id: 'GLUE_NORMALIZE', label: '🔧 Glue Job\nNormalize', desc: 'BNX: NORMALIZE (EBCDIC→UTF8)' },
      { id: 'GLUE_ENRICH', label: '🔧 Glue Job\nEnrich + Join', desc: 'BNX: JOIN + LOOKUP' },
      { id: 'GLUE_AGGREGATE', label: '🔧 Glue Job\nAggregate', desc: 'BNX: GROUP BY + Rollup' },
      { id: 'GLUE_VALIDATE', label: '🔧 Glue Job\nValidate', desc: 'BNX: Semantic Validator' },
      { id: 'EMR_ML', label: '🧠 EMR\nML Models', desc: 'Risk scoring, churn prediction' },
      { id: 'GLUE_CATALOG', label: '📋 Glue Catalog\n(Metadata)', desc: 'Schema registry, partitions' },
    ]
  },
  {
    name: 'AWS: Curated Zone (S3 + Glue Catalog)',
    color: '#a855f7',
    y: 600,
    nodes: [
      { id: 'DIM_CUSTOMER', label: '👤 Dim Customer\n360°', desc: 'Perfil completo del cliente' },
      { id: 'DIM_PRODUCT', label: '📦 Dim Product', desc: 'Catálogo de productos bancarios' },
      { id: 'DIM_BRANCH', label: '🏢 Dim Branch', desc: 'Sucursales y regiones' },
      { id: 'FACT_TX', label: '💳 Fact Transactions', desc: 'Movimientos normalizados' },
      { id: 'FACT_BALANCE', label: '💰 Fact Balances', desc: 'Saldos diarios por cuenta' },
      { id: 'FACT_PAYMENTS', label: '🔄 Fact Payments', desc: 'Pagos y transferencias' },
      { id: 'MODEL_RISK', label: '⚠️ Risk Model', desc: 'Score crediticio + PD/LGD' },
      { id: 'MODEL_AML', label: '🔍 AML Model', desc: 'Anti Money Laundering alerts' },
      { id: 'MODEL_CHURN', label: '📉 Churn Model', desc: 'Predicción de abandono' },
    ]
  },
  {
    name: 'AWS: Consumo (Athena / Redshift / APIs)',
    color: '#ef4444',
    y: 750,
    nodes: [
      { id: 'ATHENA', label: '🔎 Athena\n(Ad-hoc SQL)', desc: 'Consultas sobre S3' },
      { id: 'REDSHIFT', label: '🏗️ Redshift\n(Data Warehouse)', desc: 'Reportes pesados, BI' },
      { id: 'QUICKSIGHT', label: '📊 QuickSight\n(Dashboards)', desc: 'Risk, Finance, Ops dashboards' },
      { id: 'RPT_REGULATORY', label: '📋 Regulatory\n(CNBV/Banxico)', desc: 'R04, R08, R28, EACP' },
      { id: 'RPT_FINANCE', label: '💼 Finance\n(P&L/Balance)', desc: 'Estados financieros' },
      { id: 'API_GATEWAY', label: '🌐 API Gateway\n(REST)', desc: 'APIs para mobile y web' },
      { id: 'API_OPENBANKING', label: '🏦 Open Banking\n(PSD2/SPEI)', desc: 'APIs regulatorias' },
      { id: 'SNS_ALERTS', label: '🔔 SNS\n(Alertas)', desc: 'Notificaciones de fraude' },
      { id: 'KAFKA_OUT', label: '📡 MSK Output\n(Eventos)', desc: 'Eventos procesados downstream' },
    ]
  },
]

const EDGES_DEF = [
  // Sources → Ingestion
  ['CORE_BANKING', 'DMS'], ['CARD_SYSTEM', 'TRANSFER'], ['LOAN_SYSTEM', 'DMS'],
  ['PAYMENT_HUB', 'DMS'], ['CRM', 'APPFLOW'],
  ['FRAUD_ENGINE', 'MSK'], ['KAFKA_EVENTS', 'KINESIS'],
  ['TREASURY', 'TRANSFER'], ['COMPLIANCE', 'APPFLOW'],
  // Ingestion → Raw
  ['DMS', 'RAW_ACCOUNTS'], ['DMS', 'RAW_LOANS'], ['DMS', 'RAW_PAYMENTS'],
  ['TRANSFER', 'RAW_CARDS'], ['TRANSFER', 'RAW_TREASURY'],
  ['MSK', 'RAW_FRAUD'], ['KINESIS', 'RAW_EVENTS'],
  ['APPFLOW', 'RAW_CUSTOMERS'], ['APPFLOW', 'RAW_COMPLIANCE'],
  // Raw → Processing
  ['RAW_ACCOUNTS', 'GLUE_CLEAN'], ['RAW_CARDS', 'GLUE_CLEAN'], ['RAW_LOANS', 'GLUE_CLEAN'],
  ['RAW_PAYMENTS', 'GLUE_NORMALIZE'], ['RAW_CUSTOMERS', 'GLUE_NORMALIZE'],
  ['RAW_TREASURY', 'GLUE_NORMALIZE'],
  ['GLUE_CLEAN', 'GLUE_ENRICH'], ['GLUE_NORMALIZE', 'GLUE_ENRICH'],
  ['RAW_FRAUD', 'GLUE_ENRICH'], ['RAW_EVENTS', 'GLUE_ENRICH'],
  ['RAW_COMPLIANCE', 'GLUE_ENRICH'],
  ['GLUE_ENRICH', 'GLUE_AGGREGATE'], ['GLUE_ENRICH', 'GLUE_VALIDATE'],
  ['GLUE_CLEAN', 'GLUE_CATALOG'], ['GLUE_NORMALIZE', 'GLUE_CATALOG'],
  ['GLUE_ENRICH', 'EMR_ML'],
  // Processing → Curated
  ['GLUE_AGGREGATE', 'DIM_CUSTOMER'], ['GLUE_AGGREGATE', 'DIM_PRODUCT'], ['GLUE_AGGREGATE', 'DIM_BRANCH'],
  ['GLUE_VALIDATE', 'FACT_TX'], ['GLUE_VALIDATE', 'FACT_BALANCE'], ['GLUE_VALIDATE', 'FACT_PAYMENTS'],
  ['EMR_ML', 'MODEL_RISK'], ['EMR_ML', 'MODEL_AML'], ['EMR_ML', 'MODEL_CHURN'],
  // Curated → Consumo
  ['FACT_TX', 'ATHENA'], ['FACT_BALANCE', 'ATHENA'], ['DIM_CUSTOMER', 'ATHENA'],
  ['FACT_TX', 'REDSHIFT'], ['FACT_BALANCE', 'REDSHIFT'], ['FACT_PAYMENTS', 'REDSHIFT'],
  ['REDSHIFT', 'QUICKSIGHT'], ['ATHENA', 'QUICKSIGHT'],
  ['FACT_TX', 'RPT_REGULATORY'], ['MODEL_AML', 'RPT_REGULATORY'],
  ['FACT_BALANCE', 'RPT_FINANCE'], ['DIM_BRANCH', 'RPT_FINANCE'],
  ['DIM_CUSTOMER', 'API_GATEWAY'], ['MODEL_CHURN', 'API_GATEWAY'],
  ['DIM_CUSTOMER', 'API_OPENBANKING'], ['FACT_PAYMENTS', 'API_OPENBANKING'],
  ['MODEL_AML', 'SNS_ALERTS'], ['MODEL_RISK', 'SNS_ALERTS'],
  ['FACT_TX', 'KAFKA_OUT'], ['MODEL_AML', 'KAFKA_OUT'],
]

function buildModel(theme) {
  const t = theme || {}
  const nodes = []
  const edges = []

  LAYERS.forEach(layer => {
    const count = layer.nodes.length
    const totalWidth = count * 150
    const startX = (1400 - totalWidth) / 2

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
  const [versions, setVersions] = useState(() => {
    try { return JSON.parse(localStorage.getItem('bnx_banking_versions') || '[]') } catch { return [] }
  })
  const [versionName, setVersionName] = useState('')
  const [showVersions, setShowVersions] = useState(false)
  const [subTab, setSubTab] = useState('model')
  const [addNodeLayer, setAddNodeLayer] = useState(null)
  const [newNodeName, setNewNodeName] = useState('')
  const [nodeCounter, setNodeCounter] = useState(100)

  useEffect(() => { setNodes(initNodes) }, [initNodes, setNodes])
  useEffect(() => { setEdges(initEdges) }, [initEdges, setEdges])

  const updateNode = useCallback((id, label, desc) => {
    setNodes(nds => nds.map(n =>
      n.id === id ? { ...n, data: { ...n.data, label, desc } } : n
    ))
    setEditNode(null)
  }, [setNodes])

  const deleteNode = useCallback((id) => {
    setNodes(nds => nds.filter(n => n.id !== id))
    setEdges(eds => eds.filter(e => e.source !== id && e.target !== id))
    setEditNode(null)
  }, [setNodes, setEdges])

  const addNewNode = useCallback((layerIdx) => {
    const layer = LAYERS[layerIdx]
    if (!layer || !newNodeName.trim()) return
    const id = `CUSTOM_${nodeCounter}`
    const existingInLayer = nodes.filter(n => {
      const nl = LAYERS.find(l => l.nodes.some(x => x.id === n.id))
      return nl?.name === layer.name
    })
    setNodes(nds => [...nds, {
      id,
      position: { x: 100 + existingInLayer.length * 150, y: layer.y },
      data: { label: newNodeName.trim(), desc: 'Custom node', layer: layer.name },
      style: {
        background: layer.color + '18', border: `2px solid ${layer.color}`,
        borderRadius: 8, color: t.text || '#e2e8f0', fontSize: 11,
        padding: '8px 10px', minWidth: 130, textAlign: 'center', whiteSpace: 'pre-line',
      }
    }])
    setNodeCounter(c => c + 1)
    setNewNodeName('')
    setAddNodeLayer(null)
  }, [newNodeName, nodeCounter, nodes, t, setNodes])

  const onConnect = useCallback((params) => {
    setEdges(eds => addEdge({
      ...params,
      markerEnd: { type: MarkerType.ArrowClosed, color: '#47556980' },
      style: { stroke: '#47556980', strokeWidth: 1.2 },
    }, eds))
  }, [setEdges])

  const clearModel = useCallback(() => {
    if (window.confirm('¿Limpiar todo el modelo? Se perderán los cambios no guardados.')) {
      setNodes([])
      setEdges([])
      setEditNode(null)
    }
  }, [setNodes, setEdges])

  const resetModel = useCallback(() => {
    const { nodes: fresh, edges: freshEdges } = buildModel(t)
    setNodes(fresh)
    setEdges(freshEdges)
    setEditNode(null)
  }, [t, setNodes, setEdges])

  const onNodeClick = useCallback((_, node) => {
    setEditNode(node)
  }, [])

  const saveVersion = useCallback(() => {
    const name = versionName.trim() || `v${versions.length + 1} — ${new Date().toLocaleString()}`
    const snapshot = {
      name,
      date: new Date().toISOString(),
      nodes: nodes.map(n => ({ id: n.id, position: n.position, data: n.data })),
    }
    const updated = [snapshot, ...versions].slice(0, 20) // max 20 versions
    setVersions(updated)
    localStorage.setItem('bnx_banking_versions', JSON.stringify(updated))
    setVersionName('')
  }, [nodes, versions, versionName])

  const loadVersion = useCallback((v) => {
    setNodes(nds => nds.map(n => {
      const saved = v.nodes.find(s => s.id === n.id)
      if (saved) return { ...n, position: saved.position, data: { ...n.data, ...saved.data } }
      return n
    }))
    setShowVersions(false)
  }, [setNodes])

  const deleteVersion = useCallback((idx) => {
    const updated = versions.filter((_, i) => i !== idx)
    setVersions(updated)
    localStorage.setItem('bnx_banking_versions', JSON.stringify(updated))
  }, [versions])

  const exportModel = useCallback(() => {
    const data = {
      nodes: nodes.map(n => ({ id: n.id, position: n.position, data: n.data })),
      edges: edges.map(e => ({ source: e.source, target: e.target })),
      exportedAt: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'banking_model.json'; a.click()
    URL.revokeObjectURL(url)
  }, [nodes, edges])

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Sub-tabs */}
      <div style={{
        display: 'flex', gap: 0, background: t.sidebar || '#161b27',
        borderBottom: `1px solid ${t.border || '#334155'}`, flexShrink: 0,
      }}>
        {[
          { id: 'model', label: '🏦 Modelo Operativo' },
          { id: 'dama', label: '📐 DAMA Framework' },
          { id: 'governance', label: '🏛️ Gobierno de Datos' },
        ].map(tab => (
          <button key={tab.id} onClick={() => setSubTab(tab.id)} style={{
            padding: '10px 20px', cursor: 'pointer', fontSize: 14,
            background: subTab === tab.id ? (t.accent || '#6366f1') + '15' : 'transparent',
            borderBottom: subTab === tab.id ? `2px solid ${t.accent || '#6366f1'}` : '2px solid transparent',
            color: subTab === tab.id ? (t.accent || '#6366f1') : (t.muted || '#94a3b8'),
            fontWeight: subTab === tab.id ? 600 : 400,
            border: 'none', borderBottomWidth: 2, borderBottomStyle: 'solid',
            borderBottomColor: subTab === tab.id ? (t.accent || '#6366f1') : 'transparent',
          }}>{tab.label}</button>
        ))}
      </div>

      {subTab === 'governance' ? (
        <GovernancePage theme={t} />
      ) : subTab === 'dama' ? (
        <DamaPage theme={t} />
      ) : (
      <div style={{ flex: 1, position: 'relative' }}>
      {/* Title + Actions overlay */}
      <div style={{
        position: 'absolute', top: 16, left: 16, zIndex: 10,
        background: t.sidebar || '#161b27', padding: '12px 20px',
        borderRadius: 10, border: `1px solid ${t.border || '#334155'}`,
        boxShadow: '0 4px 20px rgba(0,0,0,.3)', maxWidth: 360,
      }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: t.text || '#e2e8f0' }}>
          🏦 Modelo Operativo Bancario — Data & Analytics
        </div>
        <div style={{ fontSize: 12, color: t.dim || '#64748b', marginTop: 4 }}>
          Click en un nodo para editar. Guarda versiones de tus cambios.
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
          {LAYERS.map(l => (
            <span key={l.name} style={{
              fontSize: 9, padding: '2px 6px', borderRadius: 4,
              background: l.color + '20', color: l.color, border: `1px solid ${l.color}40`,
            }}>{l.name}</span>
          ))}
        </div>

        {/* Save */}
        <div style={{ display: 'flex', gap: 6, marginTop: 12 }}>
          <input value={versionName} onChange={e => setVersionName(e.target.value)}
            placeholder="Nombre versión..."
            style={{
              flex: 1, padding: '5px 8px', borderRadius: 6, fontSize: 11,
              background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
              color: t.text || '#e2e8f0', outline: 'none',
            }}
            onKeyDown={e => { if (e.key === 'Enter') saveVersion() }}
          />
          <button onClick={saveVersion} style={{
            padding: '5px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: '#22c55e20', border: '1px solid #22c55e40', color: '#22c55e',
          }}>💾 Save</button>
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
          <button onClick={() => setShowVersions(v => !v)} style={{
            flex: 1, padding: '5px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: '#6366f120', border: '1px solid #6366f140', color: '#818cf8',
          }}>📋 Versions ({versions.length})</button>
          <button onClick={exportModel} style={{
            flex: 1, padding: '5px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: '#f59e0b20', border: '1px solid #f59e0b40', color: '#f59e0b',
          }}>📥 Export</button>
        </div>

        {/* Model management */}
        <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
          <button onClick={resetModel} style={{
            flex: 1, padding: '5px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: '#06b6d420', border: '1px solid #06b6d440', color: '#06b6d4',
          }}>🔄 Reset</button>
          <button onClick={clearModel} style={{
            flex: 1, padding: '5px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
            background: '#ef444420', border: '1px solid #ef444440', color: '#ef4444',
          }}>🗑️ Clear</button>
        </div>

        {/* Add node to layer */}
        <div style={{ marginTop: 4 }}>
          <div style={{ fontSize: 11, color: t.dim || '#64748b', marginBottom: 4 }}>Agregar nodo a capa:</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {LAYERS.map((l, i) => (
              <button key={l.name} onClick={() => setAddNodeLayer(addNodeLayer === i ? null : i)} style={{
                padding: '2px 6px', borderRadius: 4, fontSize: 9, cursor: 'pointer',
                background: addNodeLayer === i ? l.color + '30' : l.color + '10',
                border: `1px solid ${l.color}40`, color: l.color,
              }}>{l.icon}</button>
            ))}
          </div>
          {addNodeLayer !== null && (
            <div style={{ display: 'flex', gap: 4, marginTop: 6 }}>
              <input value={newNodeName} onChange={e => setNewNodeName(e.target.value)}
                placeholder={`Nodo en ${LAYERS[addNodeLayer]?.name}...`}
                style={{
                  flex: 1, padding: '4px 8px', borderRadius: 6, fontSize: 11,
                  background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
                  color: t.text || '#e2e8f0', outline: 'none',
                }}
                onKeyDown={e => { if (e.key === 'Enter') addNewNode(addNodeLayer) }}
              />
              <button onClick={() => addNewNode(addNodeLayer)} style={{
                padding: '4px 8px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                background: '#22c55e20', border: '1px solid #22c55e40', color: '#22c55e',
              }}>+</button>
            </div>
          )}
        </div>

        <div style={{ fontSize: 11, color: t.dim || '#64748b', marginTop: 4 }}>
          {nodes.length} nodos · {edges.length} conexiones · Arrastra entre nodos para conectar
        </div>

        {/* Versions list */}
        {showVersions && versions.length > 0 && (
          <div style={{
            marginTop: 8, maxHeight: 200, overflowY: 'auto',
            borderRadius: 6, border: `1px solid ${t.border || '#334155'}`,
          }}>
            {versions.map((v, i) => (
              <div key={i} style={{
                padding: '6px 10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                borderBottom: `1px solid ${t.border || '#334155'}20`,
                fontSize: 11,
              }}>
                <div>
                  <div style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>{v.name}</div>
                  <div style={{ color: t.dim || '#64748b', fontSize: 10 }}>
                    {new Date(v.date).toLocaleString()} · {v.nodes.length} nodes
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 4 }}>
                  <button onClick={() => loadVersion(v)} style={{
                    padding: '2px 6px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                    background: '#22c55e20', border: '1px solid #22c55e40', color: '#22c55e',
                  }}>Load</button>
                  <button onClick={() => {
                    const data = { ...v, exportedAt: new Date().toISOString() }
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url; a.download = `${v.name.replace(/\s/g, '_')}.json`; a.click()
                    URL.revokeObjectURL(url)
                  }} style={{
                    padding: '2px 6px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                    background: '#f59e0b20', border: '1px solid #f59e0b40', color: '#f59e0b',
                  }}>📥</button>
                  <button onClick={() => deleteVersion(i)} style={{
                    padding: '2px 6px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                    background: '#ef444420', border: '1px solid #ef444440', color: '#ef4444',
                  }}>✕</button>
                </div>
              </div>
            ))}
          </div>
        )}
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
              <button onClick={() => deleteNode(editNode.id)} style={{
                padding: '8px 16px', borderRadius: 6, cursor: 'pointer',
                background: '#ef444420', color: '#ef4444', border: '1px solid #ef444440', fontSize: 13,
              }}>🗑️ Delete Node</button>
            </div>
          </div>
        )
      })()}

      <ReactFlow
        nodes={nodes} edges={edges}
        onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
        onConnect={onConnect}
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
    )}
    </div>
  )
}
