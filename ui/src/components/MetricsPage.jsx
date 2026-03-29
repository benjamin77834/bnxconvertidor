import { useMemo } from 'react'

// ── Data ────────────────────────────────────────────────────
const EFFORT_DATA = [
  { phase: 'Parser MP/XFR/DML', traditional: 40, bnx: 3, unit: 'hrs' },
  { phase: 'DAG Builder + Topo Sort', traditional: 24, bnx: 2, unit: 'hrs' },
  { phase: 'Semantic Validator', traditional: 32, bnx: 2, unit: 'hrs' },
  { phase: 'Glue Codegen', traditional: 40, bnx: 3, unit: 'hrs' },
  { phase: 'PySpark Codegen', traditional: 32, bnx: 1, unit: 'hrs' },
  { phase: 'COBOL Parser', traditional: 60, bnx: 2, unit: 'hrs' },
  { phase: 'DEDUP/NORMALIZE/LOOKUP', traditional: 24, bnx: 1, unit: 'hrs' },
  { phase: 'Accuracy Engine', traditional: 16, bnx: 1, unit: 'hrs' },
  { phase: 'React UI + DAG Viewer', traditional: 48, bnx: 3, unit: 'hrs' },
  { phase: 'API (FastAPI + Lambda)', traditional: 24, bnx: 2, unit: 'hrs' },
  { phase: 'Tests + Cleanup', traditional: 16, bnx: 1, unit: 'hrs' },
  { phase: 'Deploy (Amplify + Lambda)', traditional: 8, bnx: 1, unit: 'hrs' },
]

const INFRA_DATA = [
  {
    env: 'Sandbox (Local)',
    items: ['Python 3.11', 'Node.js 18+', 'pip install fastapi uvicorn', 'npm install (React)', 'Graphviz (opcional)'],
    cost: '$0',
    time: '15 min',
  },
  {
    env: 'On-Premise',
    items: ['Servidor Linux (4 CPU, 8GB RAM)', 'Python 3.11 + pip', 'Node.js 18 + nginx reverse proxy', 'Spark cluster (standalone o YARN)', 'Firewall rules + SSL cert'],
    cost: '$200-500/mes (hardware)',
    time: '2-4 días',
  },
  {
    env: 'Cloud (AWS Serverless)',
    items: ['Lambda (256MB, Python 3.11)', 'Amplify Hosting (React static)', 'API Gateway / Function URL', 'S3 para datos de entrada/salida', 'CloudWatch para logs'],
    cost: '$5-20/mes (bajo uso)',
    time: '1-2 horas',
  },
]

// ── Bar Chart Component ─────────────────────────────────────
function BarChart({ data, theme }) {
  const t = theme || {}
  const maxVal = Math.max(...data.map(d => d.traditional))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {data.map(d => {
        const pctTraditional = (d.traditional / maxVal) * 100
        const pctBnx = (d.bnx / maxVal) * 100
        const savings = Math.round((1 - d.bnx / d.traditional) * 100)
        return (
          <div key={d.phase} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 13, color: t.text || '#e2e8f0', fontWeight: 500 }}>{d.phase}</span>
              <span style={{
                fontSize: 11, padding: '1px 6px', borderRadius: 4,
                background: '#22c55e20', color: '#22c55e', fontWeight: 600,
              }}>-{savings}%</span>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: 11, color: t.dim || '#64748b', width: 90 }}>Tradicional</span>
              <div style={{ flex: 1, height: 14, background: t.bg || '#0f1117', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ width: `${pctTraditional}%`, height: '100%', background: '#ef4444', borderRadius: 4 }} />
              </div>
              <span style={{ fontSize: 12, color: t.muted || '#94a3b8', width: 40, textAlign: 'right' }}>{d.traditional}h</span>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: 11, color: t.dim || '#64748b', width: 90 }}>BNX</span>
              <div style={{ flex: 1, height: 14, background: t.bg || '#0f1117', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ width: `${pctBnx}%`, height: '100%', background: '#22c55e', borderRadius: 4 }} />
              </div>
              <span style={{ fontSize: 12, color: t.muted || '#94a3b8', width: 40, textAlign: 'right' }}>{d.bnx}h</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── Main Component ──────────────────────────────────────────
export default function MetricsPage({ theme }) {
  const t = theme || {}

  const totals = useMemo(() => {
    const traditional = EFFORT_DATA.reduce((s, d) => s + d.traditional, 0)
    const bnx = EFFORT_DATA.reduce((s, d) => s + d.bnx, 0)
    return { traditional, bnx, savings: Math.round((1 - bnx / traditional) * 100) }
  }, [])

  const card = {
    background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 20,
  }

  return (
    <div style={{
      padding: 32, overflowY: 'auto', height: '100%',
      display: 'flex', flexDirection: 'column', gap: 28,
    }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: t.text || '#e2e8f0', margin: 0 }}>
          📊 BNX Project Metrics
        </h2>
        <p style={{ fontSize: 14, color: t.dim || '#64748b', marginTop: 4 }}>
          Comparativa de esfuerzo, infraestructura y costos
        </p>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {[
          { label: 'Tradicional', value: `${totals.traditional}h`, sub: `~${Math.round(totals.traditional / 8)} días`, color: '#ef4444' },
          { label: 'BNX Convertidor', value: `${totals.bnx}h`, sub: `~${Math.round(totals.bnx / 8)} días`, color: '#22c55e' },
          { label: 'Ahorro', value: `${totals.savings}%`, sub: `${totals.traditional - totals.bnx}h ahorradas`, color: '#6366f1' },
          { label: 'Velocidad', value: `${Math.round(totals.traditional / totals.bnx)}x`, sub: 'más rápido', color: '#f59e0b' },
        ].map(c => (
          <div key={c.label} style={{ ...card, flex: '1 1 140px', textAlign: 'center', minWidth: 140 }}>
            <div style={{ fontSize: 32, fontWeight: 700, color: c.color }}>{c.value}</div>
            <div style={{ fontSize: 14, color: t.text || '#e2e8f0', fontWeight: 600, marginTop: 4 }}>{c.label}</div>
            <div style={{ fontSize: 12, color: t.dim || '#64748b', marginTop: 2 }}>{c.sub}</div>
          </div>
        ))}
      </div>

      {/* Effort chart */}
      <div style={card}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 16 }}>
          ⏱️ Horas-Hombre por Fase
        </h3>
        <BarChart data={EFFORT_DATA} theme={t} />
      </div>

      {/* Infrastructure table */}
      <div style={card}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 16 }}>
          🏗️ Infraestructura por Ambiente
        </h3>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          {INFRA_DATA.map(env => (
            <div key={env.env} style={{
              flex: '1 1 250px', padding: 16, borderRadius: 8,
              background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
            }}>
              <div style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 8 }}>
                {env.env === 'Sandbox (Local)' ? '🖥️' : env.env === 'On-Premise' ? '🏢' : '☁️'} {env.env}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12 }}>
                {env.items.map((item, i) => (
                  <span key={i} style={{ fontSize: 12, color: t.muted || '#94a3b8' }}>• {item}</span>
                ))}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: `1px solid ${t.border || '#334155'}`, paddingTop: 8 }}>
                <div>
                  <div style={{ fontSize: 11, color: t.dim || '#64748b' }}>Costo</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#22c55e' }}>{env.cost}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 11, color: t.dim || '#64748b' }}>Setup</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#f59e0b' }}>{env.time}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Timeline */}
      <div style={card}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 16 }}>
          🗓️ Timeline de Implementación
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {[
            { week: 'Sesión 1', task: 'Parser MP + DAG Builder + Codegen Glue', status: '✅', color: '#22c55e' },
            { week: 'Sesión 2', task: 'XFR Parser + Validador Semántico + Accuracy', status: '✅', color: '#22c55e' },
            { week: 'Sesión 3', task: 'DEDUP + NORMALIZE + LOOKUP + Monster Graphs', status: '✅', color: '#22c55e' },
            { week: 'Sesión 4', task: 'React UI + DAG Viewer + Tema día/noche', status: '✅', color: '#22c55e' },
            { week: 'Sesión 5', task: 'COBOL Parser + PySpark Codegen + Deploy Lambda/Amplify', status: '✅', color: '#22c55e' },
            { week: 'Próximo', task: 'Parallel processing + KAFKA sources + Multi-target', status: '🔜', color: '#f59e0b' },
          ].map((s, i) => (
            <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start', paddingBottom: 16 }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 24 }}>
                <div style={{
                  width: 12, height: 12, borderRadius: '50%', background: s.color,
                  border: `2px solid ${s.color}40`,
                }} />
                {i < 5 && <div style={{ width: 2, height: 24, background: t.border || '#334155' }} />}
              </div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: t.text || '#e2e8f0' }}>
                  {s.status} {s.week}
                </div>
                <div style={{ fontSize: 12, color: t.dim || '#64748b', marginTop: 2 }}>{s.task}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
