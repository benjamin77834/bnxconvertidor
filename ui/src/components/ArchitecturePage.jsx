import { useMemo, useEffect, useState } from 'react'
import ReactFlow, {
  Background, Controls, MiniMap,
  MarkerType, useNodesState, useEdgesState
} from 'reactflow'
import 'reactflow/dist/style.css'

const COMPONENTS = [
  // Input Layer
  { id: 'MP_FILE', label: '.mp File\n(Graph)', x: 0, y: 0, group: 'input', desc: 'Define nodos (SOURCE, TRANSFORM, JOIN, DEDUP, NORMALIZE, LOOKUP, SINK), edges y subgraphs del pipeline' },
  { id: 'XFR_FILE', label: '.xfr File\n(Rules)', x: 0, y: 100, group: 'input', desc: 'Reglas de transformación: SELECT, WHERE, GROUP BY, join_key, dedup_keys, explode_col, source_type, etc.' },
  { id: 'DML_FILE', label: '.dml File\n(Schema)', x: 0, y: 200, group: 'input', desc: 'Schema de datos: keys por tabla y tipos de columna (string, double, int, timestamp)' },
  { id: 'COBOL_FILE', label: '.cbl File\n(COBOL)', x: 0, y: 300, group: 'input', desc: 'Código COBOL legacy con FILE SECTION, PROCEDURE DIVISION, PIC types, COMP-3/EBCDIC' },

  // Parsers
  { id: 'MP_PARSER', label: 'MP Parser\n(mp_parser.py)', x: 220, y: 0, group: 'parser', desc: 'Parsea NODE/SUBGRAPH/edges. Soporta formatos: NODE X : TYPE, A -> B, SUBGRAPH { }' },
  { id: 'XFR_PARSER', label: 'XFR Parser\n(xfr_parser.py)', x: 220, y: 100, group: 'parser', desc: 'Parsea select/where/group_by/join_key/dedup_keys/explode_col/source_type/sink_type' },
  { id: 'DML_PARSER', label: 'DML Parser\n(dml_parser.py)', x: 220, y: 200, group: 'parser', desc: 'Parsea keys y schema YAML-like. Mapea tipos COBOL PIC a Spark types' },
  { id: 'COBOL_PARSER', label: 'COBOL Parser\n(cobol_parser.py)', x: 220, y: 300, group: 'parser', desc: 'Parsea FILE SECTION, PROCEDURE DIVISION, IF/PERFORM. Detecta EBCDIC (cp500/cp1047). Genera .mp/.xfr/.dml' },

  // Core Engine
  { id: 'DAG_BUILDER', label: 'DAG Builder\n(dag/builder.py)', x: 440, y: 50, group: 'core', desc: 'Construye el DAG con nodos y edges. Topological sort con detección de ciclos. Maneja parents/children' },
  { id: 'VALIDATOR', label: 'Semantic Validator\n(validator/semantic.py)', x: 440, y: 150, group: 'core', desc: 'Infiere columnas por nodo. Valida join keys, nodos huérfanos, DEDUP/NORMALIZE/LOOKUP. Propaga schema del DML' },
  { id: 'ACCURACY', label: 'Accuracy Engine\n(accuracy.py)', x: 440, y: 250, group: 'core', desc: 'Mide cobertura: nodes, edges, transforms, joins. Calcula overall accuracy ponderado' },

  // Code Generation
  { id: 'GLUE_CODEGEN', label: 'Glue Codegen\n(glue_codegen.py)', x: 660, y: 50, group: 'codegen', desc: 'Genera AWS Glue jobs con GlueContext. Soporta 7 tipos de nodo + S3/JDBC/Kafka sources/sinks' },
  { id: 'SPARK_CODEGEN', label: 'PySpark Codegen\n(spark_codegen.py)', x: 660, y: 150, group: 'codegen', desc: 'Genera PySpark puro con SparkSession. Misma lógica que Glue pero sin dependencias AWS' },

  // API Layer
  { id: 'FASTAPI', label: 'FastAPI Server\n(api/server.py)', x: 660, y: 280, group: 'api', desc: 'Endpoints: POST /compile (mp+xfr+dml), POST /cobol. Multipart upload, target selector' },
  { id: 'LAMBDA', label: 'AWS Lambda\n(lambda/handler.py)', x: 660, y: 370, group: 'api', desc: 'Handler serverless. Parsea multipart, rutas /compile y /cobol. Function URL con CORS' },

  // UI Layer
  { id: 'COMPILER_UI', label: '🔧 Compiler\n(App.jsx)', x: 900, y: 0, group: 'ui', desc: 'Upload .mp/.xfr/.dml, selecciona target Glue/Spark, visualiza DAG con ReactFlow, descarga código' },
  { id: 'DESIGNER_UI', label: '🎨 Designer\n(DesignerPage.jsx)', x: 900, y: 80, group: 'ui', desc: 'Editor visual drag & drop. Agrega nodos, conecta edges, edita reglas por nodo, compila y genera código' },
  { id: 'BANKING_UI', label: '🏦 Banking Model\n(BankingModelPage.jsx)', x: 900, y: 160, group: 'ui', desc: 'Modelo operativo bancario con 6 capas AWS. Editable, versionable, exportable' },
  { id: 'GOVERNANCE_UI', label: '🏛️ Governance\n(GovernancePage.jsx)', x: 900, y: 240, group: 'ui', desc: '8 dominios, 55+ políticas. Editable, notas custom, mapa de burbujas, export Report/JSON' },
  { id: 'METRICS_UI', label: '📊 Metrics\n(MetricsPage.jsx)', x: 900, y: 320, group: 'ui', desc: 'Horas-hombre, estimación 40K jobs, infraestructura, timeline, metodología de cálculo' },
  { id: 'ARCHITECTURE_UI', label: '🏗️ Architecture\n(ArchitecturePage.jsx)', x: 900, y: 400, group: 'ui', desc: 'Esta página — diagrama interactivo de la arquitectura del sistema BNX' },

  // Deploy
  { id: 'AMPLIFY', label: '☁️ AWS Amplify\n(Static Hosting)', x: 1120, y: 100, group: 'deploy', desc: 'Hosting del React build. CDN, dominio custom, auto-deploy desde Git' },
  { id: 'LAMBDA_DEPLOY', label: '⚡ Lambda URL\n(Serverless API)', x: 1120, y: 250, group: 'deploy', desc: 'Function URL pública. 256MB, Python 3.11, ~$5/mes' },
]

const EDGES_DEF = [
  // Input → Parsers
  ['MP_FILE', 'MP_PARSER'], ['XFR_FILE', 'XFR_PARSER'], ['DML_FILE', 'DML_PARSER'], ['COBOL_FILE', 'COBOL_PARSER'],
  // COBOL generates files
  ['COBOL_PARSER', 'MP_PARSER'], ['COBOL_PARSER', 'XFR_PARSER'], ['COBOL_PARSER', 'DML_PARSER'],
  // Parsers → Core
  ['MP_PARSER', 'DAG_BUILDER'], ['XFR_PARSER', 'VALIDATOR'], ['DML_PARSER', 'VALIDATOR'],
  ['DAG_BUILDER', 'VALIDATOR'], ['DAG_BUILDER', 'ACCURACY'], ['VALIDATOR', 'ACCURACY'],
  // Core → Codegen
  ['DAG_BUILDER', 'GLUE_CODEGEN'], ['DAG_BUILDER', 'SPARK_CODEGEN'],
  ['VALIDATOR', 'GLUE_CODEGEN'], ['VALIDATOR', 'SPARK_CODEGEN'],
  // Core → API
  ['GLUE_CODEGEN', 'FASTAPI'], ['SPARK_CODEGEN', 'FASTAPI'], ['ACCURACY', 'FASTAPI'],
  ['GLUE_CODEGEN', 'LAMBDA'], ['SPARK_CODEGEN', 'LAMBDA'], ['ACCURACY', 'LAMBDA'],
  // API → UI
  ['FASTAPI', 'COMPILER_UI'], ['FASTAPI', 'DESIGNER_UI'],
  ['LAMBDA', 'COMPILER_UI'], ['LAMBDA', 'DESIGNER_UI'],
  // UI → Deploy
  ['COMPILER_UI', 'AMPLIFY'], ['DESIGNER_UI', 'AMPLIFY'], ['BANKING_UI', 'AMPLIFY'],
  ['GOVERNANCE_UI', 'AMPLIFY'], ['METRICS_UI', 'AMPLIFY'], ['ARCHITECTURE_UI', 'AMPLIFY'],
  ['LAMBDA', 'LAMBDA_DEPLOY'],
]

const GROUP_COLOR = {
  input: '#22c55e', parser: '#06b6d4', core: '#6366f1',
  codegen: '#f59e0b', api: '#ec4899', ui: '#a855f7', deploy: '#ef4444',
}
const GROUP_LABEL = {
  input: 'Input Files', parser: 'Parsers', core: 'Core Engine',
  codegen: 'Code Generation', api: 'API Layer', ui: 'UI (React)', deploy: 'AWS Deploy',
}

function buildArch(theme) {
  const t = theme || {}
  const nodes = COMPONENTS.map(c => ({
    id: c.id,
    position: { x: c.x, y: c.y },
    data: { label: c.label, desc: c.desc, group: c.group },
    style: {
      background: GROUP_COLOR[c.group] + '18',
      border: `2px solid ${GROUP_COLOR[c.group]}`,
      borderRadius: 8, color: t.text || '#e2e8f0',
      fontSize: 11, padding: '8px 10px', minWidth: 140,
      textAlign: 'center', whiteSpace: 'pre-line',
    }
  }))
  const edges = EDGES_DEF.map(([s, tgt], i) => ({
    id: `e${i}`, source: s, target: tgt,
    markerEnd: { type: MarkerType.ArrowClosed, color: '#47556960' },
    style: { stroke: '#47556960', strokeWidth: 1.2 },
  }))
  return { nodes, edges }
}

export default function ArchitecturePage({ theme }) {
  const t = theme || {}
  const { nodes: init, edges: initE } = useMemo(() => buildArch(t), [t])
  const [nodes, setNodes, onNodesChange] = useNodesState(init)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initE)
  const [selected, setSelected] = useState(null)

  useEffect(() => { setNodes(init) }, [init, setNodes])
  useEffect(() => { setEdges(initE) }, [initE, setEdges])

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      {/* Title */}
      <div style={{
        position: 'absolute', top: 16, left: 16, zIndex: 10,
        background: t.sidebar || '#161b27', padding: '12px 20px',
        borderRadius: 10, border: `1px solid ${t.border || '#334155'}`,
        boxShadow: '0 4px 20px rgba(0,0,0,.3)', maxWidth: 380,
      }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: t.text || '#e2e8f0' }}>
          🏗️ Arquitectura BNX Convertidor
        </div>
        <div style={{ fontSize: 12, color: t.dim || '#64748b', marginTop: 4 }}>
          {COMPONENTS.length} componentes · Click en un nodo para ver detalles
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
          {Object.entries(GROUP_LABEL).map(([k, v]) => (
            <span key={k} style={{
              fontSize: 9, padding: '2px 6px', borderRadius: 4,
              background: GROUP_COLOR[k] + '20', color: GROUP_COLOR[k], border: `1px solid ${GROUP_COLOR[k]}40`,
            }}>{v}</span>
          ))}
        </div>
      </div>

      {/* Detail panel */}
      {selected && (
        <div style={{
          position: 'absolute', top: 16, right: 16, zIndex: 10, width: 300,
          background: t.sidebar || '#161b27', borderRadius: 10,
          border: `1px solid ${t.border || '#334155'}`,
          boxShadow: '0 8px 32px rgba(0,0,0,.4)', overflow: 'hidden',
        }}>
          <div style={{
            padding: '10px 14px', background: GROUP_COLOR[selected.data.group] + '20',
            borderBottom: `1px solid ${t.border || '#334155'}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: t.text || '#e2e8f0' }}>
              {selected.data.label.split('\n')[0]}
            </span>
            <button onClick={() => setSelected(null)} style={{
              background: 'none', border: 'none', color: t.muted, fontSize: 16, cursor: 'pointer',
            }}>✕</button>
          </div>
          <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 8 }}>
            <span style={{
              padding: '2px 8px', borderRadius: 4, fontSize: 11, alignSelf: 'flex-start',
              background: GROUP_COLOR[selected.data.group] + '20',
              color: GROUP_COLOR[selected.data.group],
              border: `1px solid ${GROUP_COLOR[selected.data.group]}40`,
            }}>{GROUP_LABEL[selected.data.group]}</span>
            <div style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.7 }}>
              {selected.data.desc}
            </div>
          </div>
        </div>
      )}

      <ReactFlow
        nodes={nodes} edges={edges}
        onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
        onNodeClick={(_, n) => setSelected(n)}
        onPaneClick={() => setSelected(null)}
        fitView minZoom={0.3}
      >
        <Background color={t.flowBg || '#1e2433'} gap={20} />
        <Controls />
        <MiniMap
          nodeColor={n => {
            const c = COMPONENTS.find(x => x.id === n.id)
            return GROUP_COLOR[c?.group] || '#64748b'
          }}
          style={{ background: t.card || '#1e2433' }}
        />
      </ReactFlow>
    </div>
  )
}
