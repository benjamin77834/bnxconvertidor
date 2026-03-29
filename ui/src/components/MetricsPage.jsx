import { useMemo, useState } from 'react'

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

// ── Migration Estimator ─────────────────────────────────────
function MigrationEstimator({ theme }) {
  const t = theme || {}
  const [jobCount, setJobCount] = useState(40000)

  // Assumptions per job (averages based on Ab Initio complexity profiles)
  // Simple: 40%, Medium: 40%, Complex: 20%
  const simple = Math.round(jobCount * 0.4)
  const medium = Math.round(jobCount * 0.4)
  const complex = jobCount - simple - medium

  // Hours per job by method
  const HOURS = {
    traditional: { simple: 8, medium: 24, complex: 60 },
    bnx:         { simple: 0.5, medium: 1.5, complex: 4 },
  }

  const tradTotal = simple * HOURS.traditional.simple + medium * HOURS.traditional.medium + complex * HOURS.traditional.complex
  const bnxTotal = simple * HOURS.bnx.simple + medium * HOURS.bnx.medium + complex * HOURS.bnx.complex

  const RATE = 80 // USD/hr
  const tradCost = tradTotal * RATE
  const bnxCost = bnxTotal * RATE

  // Team size: 8h/day, 22 days/month
  const tradMonths = Math.round(tradTotal / (10 * 8 * 22)) // 10 devs
  const bnxMonths = Math.round(bnxTotal / (3 * 8 * 22))    // 3 devs

  const fmt = (n) => n.toLocaleString('en-US')

  const barMax = tradTotal

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Slider */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <span style={{ fontSize: 13, color: t.dim || '#64748b', whiteSpace: 'nowrap' }}>Jobs Ab Initio:</span>
        <input type="range" min={1000} max={100000} step={1000} value={jobCount}
          onChange={e => setJobCount(Number(e.target.value))}
          style={{ flex: 1, accentColor: '#6366f1' }}
        />
        <span style={{
          fontSize: 18, fontWeight: 700, color: '#6366f1', minWidth: 80, textAlign: 'right',
        }}>{fmt(jobCount)}</span>
      </div>

      {/* Distribution */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {[
          { label: 'Simple (40%)', count: simple, color: '#22c55e', desc: 'Input → Reformat → Output' },
          { label: 'Medium (40%)', count: medium, color: '#f59e0b', desc: 'Joins + Rollups + Lookups' },
          { label: 'Complex (20%)', count: complex, color: '#ef4444', desc: 'Multi-stage + COBOL + Subgraphs' },
        ].map(p => (
          <div key={p.label} style={{
            flex: '1 1 150px', padding: 12, borderRadius: 8,
            background: p.color + '10', border: `1px solid ${p.color}30`,
          }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: p.color }}>{fmt(p.count)}</div>
            <div style={{ fontSize: 13, color: t.text || '#e2e8f0', fontWeight: 600 }}>{p.label}</div>
            <div style={{ fontSize: 11, color: t.dim || '#64748b', marginTop: 2 }}>{p.desc}</div>
          </div>
        ))}
      </div>

      {/* Comparison */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {[
          {
            label: 'Tradicional', color: '#ef4444',
            items: [
              { k: 'Horas totales', v: `${fmt(tradTotal)}h` },
              { k: 'Equipo', v: '10 devs senior' },
              { k: 'Duración', v: `~${tradMonths} meses` },
              { k: 'Costo ($80/h)', v: `$${fmt(tradCost)} USD` },
            ]
          },
          {
            label: 'BNX Convertidor', color: '#22c55e',
            items: [
              { k: 'Horas totales', v: `${fmt(bnxTotal)}h` },
              { k: 'Equipo', v: '3 devs' },
              { k: 'Duración', v: `~${bnxMonths} meses` },
              { k: 'Costo ($80/h)', v: `$${fmt(bnxCost)} USD` },
            ]
          },
        ].map(col => (
          <div key={col.label} style={{
            flex: '1 1 250px', padding: 16, borderRadius: 8,
            background: t.bg || '#0f1117', border: `1px solid ${col.color}30`,
          }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: col.color, marginBottom: 10 }}>{col.label}</div>
            {col.items.map(item => (
              <div key={item.k} style={{
                display: 'flex', justifyContent: 'space-between', padding: '5px 0',
                borderBottom: `1px solid ${t.border || '#334155'}20`,
              }}>
                <span style={{ fontSize: 13, color: t.dim || '#64748b' }}>{item.k}</span>
                <span style={{ fontSize: 13, color: t.text || '#e2e8f0', fontWeight: 600 }}>{item.v}</span>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Visual bar */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 12, color: t.dim || '#64748b', width: 90 }}>Tradicional</span>
          <div style={{ flex: 1, height: 20, background: t.bg || '#0f1117', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{ width: '100%', height: '100%', background: '#ef4444', borderRadius: 4 }} />
          </div>
          <span style={{ fontSize: 12, color: t.muted || '#94a3b8', width: 80, textAlign: 'right' }}>{fmt(tradTotal)}h</span>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 12, color: t.dim || '#64748b', width: 90 }}>BNX</span>
          <div style={{ flex: 1, height: 20, background: t.bg || '#0f1117', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{ width: `${(bnxTotal / barMax) * 100}%`, height: '100%', background: '#22c55e', borderRadius: 4 }} />
          </div>
          <span style={{ fontSize: 12, color: t.muted || '#94a3b8', width: 80, textAlign: 'right' }}>{fmt(bnxTotal)}h</span>
        </div>
      </div>

      {/* Savings */}
      <div style={{
        padding: 16, borderRadius: 8, background: '#6366f110', border: '1px solid #6366f130',
        display: 'flex', gap: 24, flexWrap: 'wrap',
      }}>
        <div>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#22c55e' }}>${fmt(tradCost - bnxCost)}</div>
          <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>USD ahorrados</div>
        </div>
        <div>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#f59e0b' }}>{fmt(tradTotal - bnxTotal)}h</div>
          <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>horas ahorradas</div>
        </div>
        <div>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#6366f1' }}>{Math.round(tradTotal / bnxTotal)}x</div>
          <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>más rápido</div>
        </div>
        <div>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#ec4899' }}>{tradMonths - bnxMonths} meses</div>
          <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>de calendario ahorrados</div>
        </div>
      </div>

      {/* Assumptions */}
      <div style={{ fontSize: 11, color: t.dim || '#64748b', lineHeight: 1.6 }}>
        Supuestos: distribución 40% simple / 40% medium / 20% complex basada en perfil típico de migración Ab Initio bancaria.
        Horas tradicionales: simple 8h, medium 24h, complex 60h por job (incluye análisis, desarrollo, testing, deploy).
        Horas BNX: simple 0.5h, medium 1.5h, complex 4h por job (compilación automática + validación + ajustes manuales).
        Tarifa: $80 USD/h (dev senior LATAM). Equipo tradicional: 10 devs. Equipo BNX: 3 devs.
      </div>
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

      {/* Estimación migración masiva */}
      <div style={card}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 16 }}>
          🏭 Estimación de Migración Masiva Ab Initio → Spark
        </h3>
        <MigrationEstimator theme={t} />
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

      {/* Metodología */}
      <div style={card}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 16 }}>
          🧮 ¿Cuánto hubiera costado construir BNX Convertidor?
        </h3>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 20 }}>
          {[
            { label: 'Equipo Tradicional', items: [
              { k: 'Personas', v: '2 devs senior' },
              { k: 'Horas totales', v: '364h' },
              { k: 'Días laborales', v: '~45 días' },
              { k: 'Semanas', v: '~9 semanas' },
              { k: 'Costo ($80/h)', v: '$29,120 USD' },
            ], color: '#ef4444' },
            { label: 'Con BNX Convertidor', items: [
              { k: 'Personas', v: '1 dev' },
              { k: 'Horas totales', v: '22h' },
              { k: 'Días laborales', v: '~3 días' },
              { k: 'Semanas', v: '<1 semana' },
              { k: 'Costo ($80/h)', v: '$1,760 USD' },
            ], color: '#22c55e' },
          ].map(col => (
            <div key={col.label} style={{
              flex: '1 1 250px', padding: 16, borderRadius: 8,
              background: t.bg || '#0f1117', border: `1px solid ${col.color}30`,
            }}>
              <div style={{ fontSize: 15, fontWeight: 600, color: col.color, marginBottom: 12 }}>
                {col.label}
              </div>
              {col.items.map(item => (
                <div key={item.k} style={{
                  display: 'flex', justifyContent: 'space-between', padding: '4px 0',
                  borderBottom: `1px solid ${t.border || '#334155'}20`,
                }}>
                  <span style={{ fontSize: 13, color: t.dim || '#64748b' }}>{item.k}</span>
                  <span style={{ fontSize: 13, color: t.text || '#e2e8f0', fontWeight: 600 }}>{item.v}</span>
                </div>
              ))}
            </div>
          ))}
        </div>

        <div style={{
          padding: 16, borderRadius: 8, background: '#6366f110',
          border: `1px solid #6366f130`, marginBottom: 20,
        }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#818cf8', marginBottom: 8 }}>
            💰 Ahorro Total
          </div>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#22c55e' }}>$27,360</div>
              <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>USD ahorrados</div>
            </div>
            <div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#f59e0b' }}>342h</div>
              <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>horas ahorradas</div>
            </div>
            <div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#6366f1' }}>8 semanas</div>
              <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>de calendario ahorradas</div>
            </div>
          </div>
        </div>
      </div>

      {/* Metodología detallada */}
      <div style={card}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 16 }}>
          📝 Metodología de Cálculo
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 6 }}>
              Horas Tradicionales
            </div>
            <div style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.7 }}>
              Estimadas con base en benchmarks de la industria para un equipo de 2-3 desarrolladores senior
              construyendo un compilador de grafos desde cero. Incluye: diseño, implementación, testing,
              debugging, documentación y deploy. Referencia: proyectos similares de migración Ab Initio → Spark
              reportan 300-500 horas-hombre para un MVP funcional.
            </div>
          </div>

          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 6 }}>
              Horas BNX Convertidor
            </div>
            <div style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.7 }}>
              Medidas directamente del tiempo real invertido en cada sesión de desarrollo.
              Cada fase se completó en una sola sesión de trabajo con asistencia de IA generativa.
              El tiempo incluye: diseño iterativo, implementación, corrección de errores en tiempo real,
              validación y deploy.
            </div>
          </div>

          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 6 }}>
              Desglose por Fase
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${t.border || '#334155'}` }}>
                  <th style={{ textAlign: 'left', padding: '6px 8px', color: t.dim || '#64748b' }}>Fase</th>
                  <th style={{ textAlign: 'left', padding: '6px 8px', color: t.dim || '#64748b' }}>Tradicional</th>
                  <th style={{ textAlign: 'left', padding: '6px 8px', color: t.dim || '#64748b' }}>BNX</th>
                  <th style={{ textAlign: 'left', padding: '6px 8px', color: t.dim || '#64748b' }}>Justificación</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { phase: 'Parser MP/XFR/DML', t: '40h', b: '3h', why: '3 parsers con regex, manejo de errores, tests unitarios' },
                  { phase: 'DAG Builder', t: '24h', b: '2h', why: 'Topo sort, detección de ciclos, manejo de subgraphs' },
                  { phase: 'Validador Semántico', t: '32h', b: '2h', why: 'Inferencia de columnas, propagación por DAG, detección de join keys' },
                  { phase: 'Glue Codegen', t: '40h', b: '3h', why: 'Generación de código Spark válido para 7 tipos de nodo' },
                  { phase: 'PySpark Codegen', t: '32h', b: '1h', why: 'Variante del Glue codegen con SparkSession' },
                  { phase: 'COBOL Parser', t: '60h', b: '2h', why: 'Parsing de FILE SECTION, PROCEDURE DIVISION, PIC types' },
                  { phase: 'DEDUP/NORM/LOOKUP', t: '24h', b: '1h', why: '3 nuevos tipos de nodo con Window, explode, broadcast' },
                  { phase: 'Accuracy Engine', t: '16h', b: '1h', why: 'Métricas de cobertura por nodo, edge, transform, join' },
                  { phase: 'React UI', t: '48h', b: '3h', why: 'DAG viewer interactivo, tema dual, panel de detalle, file upload' },
                  { phase: 'API + Lambda', t: '24h', b: '2h', why: 'FastAPI + Lambda handler con multipart parsing' },
                  { phase: 'Tests + Cleanup', t: '16h', b: '1h', why: '13 tests, eliminación de 20+ archivos legacy' },
                  { phase: 'Deploy', t: '8h', b: '1h', why: 'Amplify + Lambda Function URL + CORS' },
                ].map((r, i) => (
                  <tr key={i} style={{ borderBottom: `1px solid ${t.border || '#334155'}20` }}>
                    <td style={{ padding: '6px 8px', color: t.text || '#e2e8f0' }}>{r.phase}</td>
                    <td style={{ padding: '6px 8px', color: '#ef4444' }}>{r.t}</td>
                    <td style={{ padding: '6px 8px', color: '#22c55e' }}>{r.b}</td>
                    <td style={{ padding: '6px 8px', color: t.dim || '#64748b' }}>{r.why}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 6 }}>
              Costos de Infraestructura
            </div>
            <div style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.7 }}>
              <span style={{ fontWeight: 600 }}>Sandbox:</span> $0 — solo requiere Python y Node.js instalados localmente.
              <br />
              <span style={{ fontWeight: 600 }}>On-Premise:</span> $200-500/mes — basado en costo de servidor dedicado
              (4 CPU, 8GB RAM) con Spark standalone. Incluye mantenimiento y SSL.
              <br />
              <span style={{ fontWeight: 600 }}>Cloud (AWS):</span> $5-20/mes — Lambda cobra por invocación (~$0.20 por 1M requests),
              Amplify Hosting es gratuito en tier free (5GB/mes). S3 para datos es ~$0.023/GB.
              Estimado para uso bajo-medio de un equipo de desarrollo.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
