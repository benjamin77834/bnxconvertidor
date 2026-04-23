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
  { phase: 'Designer Visual (Ab Initio style)', traditional: 60, bnx: 3, unit: 'hrs' },
  { phase: 'Source/Sink Connectors (S3/JDBC/Kafka)', traditional: 32, bnx: 2, unit: 'hrs' },
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
    abinitio:    { simple: 4, medium: 12, complex: 30 },
    saas:        { simple: 2, medium: 6, complex: 15 },
    bnx:         { simple: 0.5, medium: 1.5, complex: 4 },
  }

  const tradTotal = simple * HOURS.traditional.simple + medium * HOURS.traditional.medium + complex * HOURS.traditional.complex
  const abTotal = simple * HOURS.abinitio.simple + medium * HOURS.abinitio.medium + complex * HOURS.abinitio.complex
  const saasTotal = simple * HOURS.saas.simple + medium * HOURS.saas.medium + complex * HOURS.saas.complex
  const bnxTotal = simple * HOURS.bnx.simple + medium * HOURS.bnx.medium + complex * HOURS.bnx.complex

  const RATE = 30 // USD/hr
  const tradCost = tradTotal * RATE
  const abCost = abTotal * RATE
  const saasCost = saasTotal * RATE
  const bnxCost = bnxTotal * RATE

  // Team size: 8h/day, 22 days/month
  const tradMonths = Math.round(tradTotal / (10 * 8 * 22)) // 10 devs
  const abMonths = Math.round(abTotal / (8 * 8 * 22))      // 8 devs Ab Initio
  const saasMonths = Math.round(saasTotal / (5 * 8 * 22))  // 5 devs + vendor
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
            label: 'Tradicional (Manual)', color: '#ef4444',
            items: [
              { k: 'Horas totales', v: `${fmt(tradTotal)}h` },
              { k: 'Equipo', v: '10 devs senior' },
              { k: 'Duración', v: `~${tradMonths} meses` },
              { k: 'Costo ($30/h)', v: `$${fmt(tradCost)} USD` },
            ]
          },
          {
            label: 'Ab Initio Cloud', color: '#f59e0b',
            items: [
              { k: 'Horas totales', v: `${fmt(abTotal)}h` },
              { k: 'Equipo', v: '8 devs Ab Initio' },
              { k: 'Duración', v: `~${abMonths} meses` },
              { k: 'Costo ($30/h)', v: `$${fmt(abCost)} USD` },
            ]
          },
          {
            label: 'SaaS Migration Tools', color: '#a855f7',
            items: [
              { k: 'Horas totales', v: `${fmt(saasTotal)}h` },
              { k: 'Equipo', v: '5 devs + vendor' },
              { k: 'Duración', v: `~${saasMonths} meses` },
              { k: 'Costo ($30/h)', v: `$${fmt(saasCost)} USD` },
              { k: '+ Licencia SaaS', v: 'Variable ($100-300/job)' },
            ]
          },
          {
            label: 'BNX Convertidor', color: '#22c55e',
            items: [
              { k: 'Horas totales', v: `${fmt(bnxTotal)}h` },
              { k: 'Equipo', v: '3 devs' },
              { k: 'Duración', v: `~${bnxMonths} meses` },
              { k: 'Costo ($30/h)', v: `$${fmt(bnxCost)} USD` },
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
          <span style={{ fontSize: 12, color: t.dim || '#64748b', width: 90 }}>Ab Initio Cloud</span>
          <div style={{ flex: 1, height: 20, background: t.bg || '#0f1117', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{ width: `${(abTotal / barMax) * 100}%`, height: '100%', background: '#f59e0b', borderRadius: 4 }} />
          </div>
          <span style={{ fontSize: 12, color: t.muted || '#94a3b8', width: 80, textAlign: 'right' }}>{fmt(abTotal)}h</span>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 12, color: t.dim || '#64748b', width: 90 }}>SaaS Tools</span>
          <div style={{ flex: 1, height: 20, background: t.bg || '#0f1117', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{ width: `${(saasTotal / barMax) * 100}%`, height: '100%', background: '#a855f7', borderRadius: 4 }} />
          </div>
          <span style={{ fontSize: 12, color: t.muted || '#94a3b8', width: 80, textAlign: 'right' }}>{fmt(saasTotal)}h</span>
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
          <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>USD ahorrados vs Tradicional</div>
        </div>
        <div>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#f59e0b' }}>${fmt(abCost - bnxCost)}</div>
          <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>vs Ab Initio Cloud</div>
        </div>
        <div>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#a855f7' }}>${fmt(saasCost - bnxCost)}</div>
          <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>vs SaaS Tools</div>
        </div>
        <div>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#6366f1' }}>{Math.round(tradTotal / bnxTotal)}x</div>
          <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>más rápido vs Tradicional</div>
        </div>
      </div>

      {/* Detailed explanation */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 4 }}>
        <div style={{ padding: 14, borderRadius: 8, background: (t.bg || '#0f1117') + '80', border: `1px solid ${t.border || '#334155'}30` }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#f59e0b', marginBottom: 8 }}>
            🟡 ¿Por qué 8 desarrolladores con Ab Initio Cloud?
          </div>
          <div style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.8 }}>
            <div>Migrar Ab Initio de on-premise a cloud (re-platforming) mantiene la tecnología pero requiere adaptación. Con 8 desarrolladores certificados Ab Initio:</div>
            <div style={{ marginTop: 6 }}>
              <div>• <span style={{ color: t.text || '#e2e8f0' }}>Capacidad mensual</span>: 8 devs × 8h × 22 días = <span style={{ color: '#f59e0b', fontWeight: 600 }}>1,408 horas/mes</span></div>
              <div>• <span style={{ color: t.text || '#e2e8f0' }}>Total horas</span>: {fmt(abTotal)}h</div>
              <div>• <span style={{ color: t.text || '#e2e8f0' }}>Duración</span>: {fmt(abTotal)}h ÷ 1,408 h/mes = <span style={{ color: '#f59e0b', fontWeight: 600 }}>~{abMonths} meses</span></div>
            </div>
            <div style={{ marginTop: 6 }}>El proceso de migración Ab Initio Cloud incluye:</div>
            <div style={{ paddingLeft: 12 }}>
              <div>1. <span style={{ color: t.text || '#e2e8f0' }}>Re-configurar el Co&gt;Operating System</span> para Kubernetes (EKS)</div>
              <div>2. <span style={{ color: t.text || '#e2e8f0' }}>Adaptar paths de archivos</span> de filesystem local a S3</div>
              <div>3. <span style={{ color: t.text || '#e2e8f0' }}>Ajustar layouts de paralelismo</span> para pods de Kubernetes</div>
              <div>4. <span style={{ color: t.text || '#e2e8f0' }}>Migrar conexiones de DB</span> de on-premise a RDS/Redshift</div>
              <div>5. <span style={{ color: t.text || '#e2e8f0' }}>Containerizar Ab Initio</span> — empaquetar el runtime en Docker images para EKS</div>
              <div>6. <span style={{ color: t.text || '#e2e8f0' }}>Re-testing completo</span> de cada grafo en el nuevo ambiente</div>
            </div>
            <div style={{ marginTop: 6 }}>Horas por job (Ab Initio Cloud):</div>
            <div style={{ paddingLeft: 12 }}>
              <div>• Simple: <span style={{ color: '#f59e0b', fontWeight: 600 }}>4h</span> — cambio de paths, ajuste de layout, test básico</div>
              <div>• Medium: <span style={{ color: '#f59e0b', fontWeight: 600 }}>12h</span> — adaptar conexiones DB, ajustar joins, re-test con datos</div>
              <div>• Complex: <span style={{ color: '#f59e0b', fontWeight: 600 }}>30h</span> — re-configurar subgraphs, paralelismo, COBOL copybooks, test extensivo</div>
            </div>
            <div style={{ marginTop: 6, fontStyle: 'italic', color: t.dim || '#64748b' }}>
              Nota: Ab Initio Cloud requiere licencias ($$$) + desarrolladores certificados Ab Initio (escasos y caros).
              El costo de licencia no está incluido en el cálculo de horas-hombre.
            </div>
          </div>
        </div>

        <div style={{ padding: 14, borderRadius: 8, background: (t.bg || '#0f1117') + '80', border: `1px solid ${t.border || '#334155'}30` }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#ef4444', marginBottom: 8 }}>
            🔴 ¿Por qué 10 desarrolladores en Tradicional?
          </div>
          <div style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.8 }}>
            <div>Un proyecto de migración de 40,000 jobs Ab Initio es un programa multi-año. Con 10 desarrolladores senior trabajando 8h/día, 22 días/mes:</div>
            <div style={{ marginTop: 6 }}>
              <div>• <span style={{ color: t.text || '#e2e8f0' }}>Capacidad mensual</span>: 10 devs × 8h × 22 días = <span style={{ color: '#ef4444', fontWeight: 600 }}>1,760 horas/mes</span></div>
              <div>• <span style={{ color: t.text || '#e2e8f0' }}>Total horas</span>: {fmt(tradTotal)}h</div>
              <div>• <span style={{ color: t.text || '#e2e8f0' }}>Duración</span>: {fmt(tradTotal)}h ÷ 1,760 h/mes = <span style={{ color: '#ef4444', fontWeight: 600 }}>~{tradMonths} meses</span></div>
            </div>
            <div style={{ marginTop: 6 }}>Cada desarrollador necesita:</div>
            <div style={{ paddingLeft: 12 }}>
              <div>1. Analizar el grafo Ab Initio original (entender la lógica)</div>
              <div>2. Mapear campos y transformaciones manualmente</div>
              <div>3. Escribir el código PySpark/Glue equivalente</div>
              <div>4. Probar con datos de prueba y comparar resultados</div>
              <div>5. Documentar y hacer code review</div>
            </div>
            <div style={{ marginTop: 6, fontStyle: 'italic', color: t.dim || '#64748b' }}>
              Con menos de 10 devs el proyecto tomaría más de 4 años, lo cual no es viable para la mayoría de bancos.
            </div>
          </div>
        </div>

        <div style={{ padding: 14, borderRadius: 8, background: (t.bg || '#0f1117') + '80', border: `1px solid ${t.border || '#334155'}30` }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#22c55e', marginBottom: 8 }}>
            🟢 ¿Por qué solo 3 desarrolladores con BNX?
          </div>
          <div style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.8 }}>
            <div>BNX Convertidor automatiza los pasos 2 y 3 del proceso tradicional. Con 3 desarrolladores:</div>
            <div style={{ marginTop: 6 }}>
              <div>• <span style={{ color: t.text || '#e2e8f0' }}>Capacidad mensual</span>: 3 devs × 8h × 22 días = <span style={{ color: '#22c55e', fontWeight: 600 }}>528 horas/mes</span></div>
              <div>• <span style={{ color: t.text || '#e2e8f0' }}>Total horas</span>: {fmt(bnxTotal)}h</div>
              <div>• <span style={{ color: t.text || '#e2e8f0' }}>Duración</span>: {fmt(bnxTotal)}h ÷ 528 h/mes = <span style={{ color: '#22c55e', fontWeight: 600 }}>~{bnxMonths} meses</span></div>
            </div>
            <div style={{ marginTop: 6 }}>El flujo con BNX es:</div>
            <div style={{ paddingLeft: 12 }}>
              <div>1. Cargar el grafo Ab Initio (.mp) en el convertidor</div>
              <div>2. <span style={{ color: '#22c55e' }}>BNX genera automáticamente</span> el código PySpark/Glue</div>
              <div>3. El desarrollador revisa, ajusta join keys y reglas específicas</div>
              <div>4. El validador semántico detecta errores antes de ejecutar</div>
              <div>5. Deploy directo a AWS</div>
            </div>
            <div style={{ marginTop: 6, fontStyle: 'italic', color: t.dim || '#64748b' }}>
              Los 3 devs se enfocan en validación y ajustes, no en escribir código desde cero.
            </div>
          </div>
        </div>

        <div style={{ padding: 14, borderRadius: 8, background: (t.bg || '#0f1117') + '80', border: `1px solid ${t.border || '#334155'}30` }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#f59e0b', marginBottom: 8 }}>
            🟡 Fórmula del Cálculo
          </div>
          <div style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.8 }}>
            <div style={{ fontFamily: 'monospace', padding: 10, background: (t.bg || '#0f1117'), borderRadius: 6, marginBottom: 8 }}>
              <div style={{ color: t.text || '#e2e8f0' }}>Total Horas = (Jobs Simple × Hrs/Job) + (Jobs Medium × Hrs/Job) + (Jobs Complex × Hrs/Job)</div>
              <div style={{ marginTop: 4 }}>
                <span style={{ color: '#ef4444' }}>Tradicional</span> = ({fmt(simple)} × 8h) + ({fmt(medium)} × 24h) + ({fmt(complex)} × 60h) = <span style={{ color: '#ef4444', fontWeight: 600 }}>{fmt(tradTotal)}h</span>
              </div>
              <div>
                <span style={{ color: '#f59e0b' }}>Ab Initio Cloud</span> = ({fmt(simple)} × 4h) + ({fmt(medium)} × 12h) + ({fmt(complex)} × 30h) = <span style={{ color: '#f59e0b', fontWeight: 600 }}>{fmt(abTotal)}h</span>
              </div>
              <div>
                <span style={{ color: '#22c55e' }}>BNX</span> = ({fmt(simple)} × 0.5h) + ({fmt(medium)} × 1.5h) + ({fmt(complex)} × 4h) = <span style={{ color: '#22c55e', fontWeight: 600 }}>{fmt(bnxTotal)}h</span>
              </div>
              <div style={{ marginTop: 4 }}>
                <span style={{ color: '#6366f1' }}>Costo</span> = Total Horas × $30 USD/h (tarifa dev senior LATAM)
              </div>
              <div>
                <span style={{ color: '#6366f1' }}>Duración</span> = Total Horas ÷ (Equipo × 8h × 22 días/mes)
              </div>
            </div>
            <div>
              <span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Distribución de complejidad</span>: basada en perfil típico de migración Ab Initio bancaria.
              40% de los jobs son simples (Input→Reformat→Output), 40% son medium (Joins+Rollups), 20% son complex (Multi-stage+COBOL+Subgraphs).
            </div>
            <div style={{ marginTop: 6 }}>
              <span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Horas por job</span>: estimadas con base en la complejidad del grafo.
              Un job simple tiene 3-5 nodos, un medium tiene 10-20 nodos con joins, un complex tiene 30+ nodos con subgraphs y lógica COBOL.
            </div>
          </div>
        </div>
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

      {/* Comparativa LeapLogic vs Ab Initio vs BNX */}
      <div style={card}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 4 }}>
          🔬 Comparativa de Tecnología: LeapLogic vs Ab Initio Cloud vs BNX Convertidor
        </h3>
        <p style={{ fontSize: 13, color: t.dim || '#64748b', marginBottom: 20 }}>
          Entradas, salidas, tecnología y diferenciadores de cada plataforma de migración
        </p>

        {/* Speed & Impact Chart */}
        {(() => {
          const metrics = [
            { label: 'Velocidad\nmigración', leap: 65, abi: 40, bnx: 95 },
            { label: 'Costo\n(inverso)', leap: 30, abi: 25, bnx: 98 },
            { label: 'Targets\ncloud', leap: 80, abi: 50, bnx: 90 },
            { label: 'Open\nSource', leap: 0, abi: 0, bnx: 100 },
            { label: 'Soporte\nCOBOL', leap: 85, abi: 70, bnx: 80 },
            { label: 'Multi-\ntarget', leap: 75, abi: 30, bnx: 95 },
            { label: 'Planes\ncíclicos', leap: 60, abi: 100, bnx: 85 },
            { label: 'Grafo\nde Grafos', leap: 70, abi: 100, bnx: 90 },
          ]
          const barH = 22
          const gap = 10
          const labelW = 70
          const chartW = 420
          const colors = { leap: '#06b6d4', abi: '#f59e0b', bnx: '#22c55e' }

          return (
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 12 }}>
                📊 Índice de Capacidades (0–100)
              </div>
              <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
                {[['LeapLogic', colors.leap], ['Ab Initio Cloud', colors.abi], ['BNX Convertidor', colors.bnx]].map(([name, color]) => (
                  <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{ width: 12, height: 12, borderRadius: 2, background: color }} />
                    <span style={{ fontSize: 12, color: t.muted || '#94a3b8' }}>{name}</span>
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: gap }}>
                {metrics.map((m, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: labelW, fontSize: 11, color: t.dim || '#64748b', textAlign: 'right', whiteSpace: 'pre-line', lineHeight: 1.3 }}>{m.label}</div>
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 3 }}>
                      {[['leap', m.leap], ['abi', m.abi], ['bnx', m.bnx]].map(([key, val]) => (
                        <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div style={{ flex: 1, height: barH, background: (t.bg || '#0f1117') + '80', borderRadius: 4, overflow: 'hidden', position: 'relative' }}>
                            <div style={{
                              width: `${val}%`, height: '100%', borderRadius: 4,
                              background: colors[key] + (key === 'bnx' ? 'cc' : '80'),
                              transition: 'width 0.6s ease',
                              display: 'flex', alignItems: 'center', paddingLeft: 8,
                            }}>
                              {val > 15 && <span style={{ fontSize: 10, color: '#fff', fontWeight: 600 }}>{val}</span>}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 12, fontSize: 11, color: t.dim || '#64748b', fontStyle: 'italic' }}>
                * Índice estimado basado en capacidades documentadas públicamente. Costo (inverso) = 100 - costo relativo normalizado.
              </div>
            </div>
          )
        })()}

        {/* Cost comparison highlight */}
        <div style={{
          display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap',
          padding: 16, borderRadius: 10, background: '#f59e0b08', border: `1px solid #f59e0b20`,
        }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: t.text || '#e2e8f0', width: '100%', marginBottom: 4 }}>
            💰 Costo Anual: Licencia + Infraestructura
          </div>
          {[
            { label: 'LeapLogic', license: '$50K-$200K', infra: '$2K-$10K/mes', total: '$74K-$320K/año', color: '#06b6d4', icon: '🔵' },
            { label: 'Ab Initio Cloud', license: 'Licencia existente', infra: '$2K-$10K/mes', total: '$24K-$120K/año', color: '#f59e0b', icon: '🟡' },
            { label: 'BNX Convertidor', license: '$0 (open source)', infra: '$5-$20/mes', total: '$60-$240/año', color: '#22c55e', icon: '🟢' },
          ].map(c => (
            <div key={c.label} style={{
              flex: '1 1 180px', padding: '12px 14px', borderRadius: 8,
              background: c.color + '10', border: `2px solid ${c.color}30`,
            }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: c.color }}>{c.icon} {c.label}</div>
              <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 11, color: t.dim || '#64748b' }}>Licencia</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: t.text || '#e2e8f0' }}>{c.license}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 11, color: t.dim || '#64748b' }}>Infra</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: t.text || '#e2e8f0' }}>{c.infra}</span>
                </div>
                <div style={{ borderTop: `1px solid ${c.color}30`, paddingTop: 4, marginTop: 4, display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: c.color }}>Total/año</span>
                  <span style={{ fontSize: 14, fontWeight: 700, color: c.color }}>{c.total}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Technology comparison table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, minWidth: 700 }}>
            <thead>
              <tr style={{ background: (t.bg || '#0f1117') + '80' }}>
                <th style={{ padding: '10px 14px', textAlign: 'left', color: t.dim || '#64748b', borderBottom: `2px solid ${t.border || '#334155'}`, width: '18%' }}>Criterio</th>
                <th style={{ padding: '10px 14px', textAlign: 'center', color: '#06b6d4', borderBottom: `2px solid #06b6d440`, width: '27%' }}>
                  🔵 LeapLogic (Impetus)
                </th>
                <th style={{ padding: '10px 14px', textAlign: 'center', color: '#f59e0b', borderBottom: `2px solid #f59e0b40`, width: '27%' }}>
                  🟡 Ab Initio Cloud (EKS)
                </th>
                <th style={{ padding: '10px 14px', textAlign: 'center', color: '#22c55e', borderBottom: `2px solid #22c55e40`, width: '28%' }}>
                  🟢 BNX Convertidor
                </th>
              </tr>
            </thead>
            <tbody>
              {[
                {
                  criteria: '🏗️ Tecnología base',
                  leap: 'Plataforma SaaS propietaria. Motor de análisis estático de código Ab Initio. Reglas de transformación predefinidas.',
                  abinitio: 'Ab Initio GDE + Co>Operating System migrado a Kubernetes (EKS). Misma plataforma, diferente infraestructura.',
                  bnx: 'Python 3.11 open source. Parsers propios (.mp/.xfr/.dml). DAG Builder + Semantic Validator + Codegen multi-target.',
                  leapColor: '#06b6d4', abiColor: '#f59e0b', bnxColor: '#22c55e',
                },
                {
                  criteria: '📥 Entradas',
                  leap: '• Grafos Ab Initio (.mp, .xfr, .dml)\n• COBOL (.cbl)\n• Hive/Teradata SQL\n• Informatica mappings\n• DataStage jobs',
                  abinitio: '• Grafos Ab Initio nativos (.mp, .xfr, .dml, .pset)\n• PLAN files\n• Parámetros PSET\n• Sandbox Ab Initio existente',
                  bnx: '• Grafos Ab Initio (.mp, .xfr, .dml)\n• COBOL (.cbl) con EBCDIC/COMP-3\n• PLAN + PSET (Grafo de Grafos)\n• Código Spark 2/Python 2 (refactorización)\n• Diseño visual (drag & drop)',
                  leapColor: '#06b6d4', abiColor: '#f59e0b', bnxColor: '#22c55e',
                },
                {
                  criteria: '📤 Salidas',
                  leap: '• PySpark (Databricks/EMR)\n• Hive SQL\n• Teradata SQL\n• Reporte de migración\n• Documentación automática',
                  abinitio: '• Grafos Ab Initio ejecutándose en EKS\n• Misma lógica, diferente infraestructura\n• Sin cambio de código',
                  bnx: '• AWS Glue (PySpark + GlueContext)\n• PySpark puro (SparkSession)\n• Apache Flink (PyFlink + Flink SQL)\n• Step Functions (JSON)\n• Terraform (.tf)\n• Airflow (Python DAG)\n• Código refactorizado Spark 3/Python 3',
                  leapColor: '#06b6d4', abiColor: '#f59e0b', bnxColor: '#22c55e',
                },
                {
                  criteria: '🎯 Targets cloud',
                  leap: 'Databricks, AWS EMR, Azure HDInsight, Google Dataproc',
                  abinitio: 'AWS EKS, Azure AKS, GCP GKE (Kubernetes)',
                  bnx: 'AWS Glue, AWS Lambda, Apache Flink, cualquier cluster Spark',
                  leapColor: '#06b6d4', abiColor: '#f59e0b', bnxColor: '#22c55e',
                },
                {
                  criteria: '🔄 Tipos de nodo soportados',
                  leap: 'Reformat, Rollup, Join, Dedup, Normalize, Lookup, Concatenate, Gather, Partition, Filter, Read, Write + 50+ componentes Ab Initio',
                  abinitio: 'Todos los componentes Ab Initio nativos (100% compatibilidad)',
                  bnx: 'SOURCE, TRANSFORM, JOIN, DEDUP, NORMALIZE, LOOKUP, CONCATENATE, GATHER, PARTITION, FILTER, SINK (11 tipos)',
                  leapColor: '#06b6d4', abiColor: '#f59e0b', bnxColor: '#22c55e',
                },
                {
                  criteria: '🔗 Conectores',
                  leap: 'S3, HDFS, JDBC (Oracle/MySQL/PG), Kafka, Hive, Teradata, Snowflake',
                  abinitio: 'Todos los conectores Ab Initio nativos: MFS, Oracle, DB2, Teradata, SAP, mainframe',
                  bnx: 'S3/filesystem (CSV/Parquet/JSON/Avro), Apache Kafka, JDBC (MySQL/PG/Oracle)',
                  leapColor: '#06b6d4', abiColor: '#f59e0b', bnxColor: '#22c55e',
                },
                {
                  criteria: '🔄 Planes cíclicos',
                  leap: 'Soportado via Databricks workflows con retry logic',
                  abinitio: 'Nativo — SCHEDULE: CYCLIC, MAX_ITERATIONS, CONVERGENCE en PLAN/PSET',
                  bnx: 'Soportado — SCHEDULE: CYCLIC, MAX_ITERATIONS, CONVERGENCE en PLAN/PSET. Genera iteration loop con checkpoint/staging.',
                  leapColor: '#06b6d4', abiColor: '#f59e0b', bnxColor: '#22c55e',
                },
                {
                  criteria: '🏗️ Grafo de Grafos',
                  leap: 'Soportado — migra PLANs con múltiples grafos como workflows',
                  abinitio: 'Nativo — PLAN orquesta múltiples grafos con DEPENDS',
                  bnx: 'Soportado — PLAN + múltiples .mp → Mega-DAG unificado con cross-graph edges y namespacing',
                  leapColor: '#06b6d4', abiColor: '#f59e0b', bnxColor: '#22c55e',
                },
                {
                  criteria: '💰 Modelo de costo',
                  leap: 'Licencia SaaS: $50K-$200K+ USD/año según volumen de jobs',
                  abinitio: 'Licencia Ab Initio existente + costo EKS (~$2K-$10K/mes según cluster)',
                  bnx: 'Open source. Solo costo de infraestructura AWS: ~$5-20/mes (Lambda + Amplify)',
                  leapColor: '#06b6d4', abiColor: '#f59e0b', bnxColor: '#22c55e',
                  highlight: true,
                },
                {
                  criteria: '⚡ Velocidad de migración',
                  leap: '~2-4h por job complejo. Requiere revisión manual del output.',
                  abinitio: 'Lift & shift — sin reescritura. Días/semanas para configurar EKS.',
                  bnx: '0.5-4h por job según complejidad. Compilación automática en segundos.',
                  leapColor: '#06b6d4', abiColor: '#f59e0b', bnxColor: '#22c55e',
                },
                {
                  criteria: '🎨 UI / Experiencia',
                  leap: 'UI web propietaria. Visualización de grafos. Reportes de migración.',
                  abinitio: 'GDE (Graphical Development Environment) — IDE propietario de Ab Initio',
                  bnx: 'React UI con DAG viewer interactivo, Designer drag & drop, modo batch CLI, Architecture + Glosario',
                  leapColor: '#06b6d4', abiColor: '#f59e0b', bnxColor: '#22c55e',
                },
                {
                  criteria: '🔓 Open Source',
                  leap: '❌ Propietario (Impetus Technologies)',
                  abinitio: '❌ Propietario (Ab Initio Software)',
                  bnx: '✅ Código abierto. Python + React. Extensible.',
                  leapColor: '#06b6d4', abiColor: '#f59e0b', bnxColor: '#22c55e',
                },
              ].map((row, i) => (
                <tr key={i} style={{
                  borderBottom: `1px solid ${t.border || '#334155'}20`, verticalAlign: 'top',
                  background: row.highlight ? '#f59e0b10' : 'transparent',
                }}>
                  <td style={{ padding: '10px 14px', color: t.text || '#e2e8f0', fontWeight: 600, fontSize: 12 }}>{row.criteria}</td>
                  <td style={{ padding: '10px 14px', color: row.highlight ? '#ef4444' : (t.muted || '#94a3b8'), fontSize: 12, lineHeight: 1.6, whiteSpace: 'pre-line', background: row.highlight ? '#ef444415' : '#06b6d408', fontWeight: row.highlight ? 600 : 400 }}>{row.leap}</td>
                  <td style={{ padding: '10px 14px', color: row.highlight ? '#f59e0b' : (t.muted || '#94a3b8'), fontSize: 12, lineHeight: 1.6, whiteSpace: 'pre-line', background: row.highlight ? '#f59e0b15' : '#f59e0b08', fontWeight: row.highlight ? 600 : 400 }}>{row.abinitio}</td>
                  <td style={{ padding: '10px 14px', color: row.highlight ? '#22c55e' : (t.muted || '#94a3b8'), fontSize: 12, lineHeight: 1.6, whiteSpace: 'pre-line', background: row.highlight ? '#22c55e15' : '#22c55e08', fontWeight: row.highlight ? 600 : 400 }}>{row.bnx}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Summary badges */}
        <div style={{ display: 'flex', gap: 12, marginTop: 20, flexWrap: 'wrap' }}>
          {[
            { label: 'LeapLogic', tag: 'SaaS propietario', sub: 'Mejor para migración masiva multi-plataforma', color: '#06b6d4' },
            { label: 'Ab Initio Cloud', tag: 'Lift & shift a EKS', sub: 'Mejor para preservar lógica Ab Initio sin reescribir', color: '#f59e0b' },
            { label: 'BNX Convertidor', tag: 'Open source + multi-target', sub: 'Mejor para AWS Glue/Flink con control total del código', color: '#22c55e' },
          ].map(b => (
            <div key={b.label} style={{
              flex: '1 1 200px', padding: '12px 16px', borderRadius: 8,
              background: b.color + '10', border: `1px solid ${b.color}30`,
            }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: b.color }}>{b.label}</div>
              <div style={{ fontSize: 12, color: t.text || '#e2e8f0', fontWeight: 600, marginTop: 4 }}>{b.tag}</div>
              <div style={{ fontSize: 11, color: t.dim || '#64748b', marginTop: 4 }}>{b.sub}</div>
            </div>
          ))}
        </div>
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
            { week: 'Sesión 6', task: 'Designer Visual (drag & drop) + Editor de nodos + Code modal', status: '✅', color: '#22c55e' },
            { week: 'Sesión 7', task: 'Connectors S3/JDBC/Kafka en SOURCE y SINK', status: '✅', color: '#22c55e' },
            { week: 'Próximo', task: 'Parallel processing + Multi-target + Schema inference avanzado', status: '🔜', color: '#f59e0b' },
          ].map((s, i) => (
            <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start', paddingBottom: 16 }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 24 }}>
                <div style={{
                  width: 12, height: 12, borderRadius: '50%', background: s.color,
                  border: `2px solid ${s.color}40`,
                }} />
                {i < 7 && <div style={{ width: 2, height: 24, background: t.border || '#334155' }} />}
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
              { k: 'Costo ($30/h)', v: '$13,680 USD' },
            ], color: '#ef4444' },
            { label: 'Con BNX Convertidor', items: [
              { k: 'Personas', v: '1 dev' },
              { k: 'Horas totales', v: '27h' },
              { k: 'Días laborales', v: '~3 días' },
              { k: 'Semanas', v: '<1 semana' },
              { k: 'Costo ($30/h)', v: '$810 USD' },
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
              <div style={{ fontSize: 28, fontWeight: 700, color: '#22c55e' }}>$12,870</div>
              <div style={{ fontSize: 12, color: t.dim || '#64748b' }}>USD ahorrados</div>
            </div>
            <div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#f59e0b' }}>429h</div>
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          <div style={{ padding: 16, borderRadius: 8, background: (t.bg || '#0f1117') + '80', border: `1px solid ${t.border || '#334155'}30` }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: '#ef4444', marginBottom: 8 }}>
              🔴 ¿Cómo se calcularon las Horas Tradicionales?
            </div>
            <div style={{ fontSize: 14, color: t.muted || '#94a3b8', lineHeight: 1.8 }}>
              Las horas tradicionales representan el esfuerzo estimado para un equipo de 2-3 desarrolladores senior
              construyendo cada componente desde cero, sin herramientas de automatización. Se calcularon así:
            </div>
            <div style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.8, marginTop: 8 }}>
              <div>1. <span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Análisis y diseño</span> — ~20% del tiempo. Definir la arquitectura, formatos de archivo, tipos de nodo, estructura del DAG.</div>
              <div>2. <span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Implementación</span> — ~50% del tiempo. Escribir el código, parsers, codegen, validador, UI.</div>
              <div>3. <span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Testing y debugging</span> — ~20% del tiempo. Tests unitarios, integración, corrección de bugs.</div>
              <div>4. <span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Deploy y documentación</span> — ~10% del tiempo. Configurar AWS, CI/CD, documentar.</div>
            </div>
            <div style={{ fontSize: 13, color: t.dim || '#64748b', marginTop: 10, fontStyle: 'italic' }}>
              Referencia: proyectos similares de migración Ab Initio → Spark en la industria financiera reportan
              300-500 horas-hombre para un MVP funcional (fuente: estimaciones de consultoras Big 4 y vendors de migración).
            </div>
          </div>

          <div style={{ padding: 16, borderRadius: 8, background: (t.bg || '#0f1117') + '80', border: `1px solid ${t.border || '#334155'}30` }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: '#22c55e', marginBottom: 8 }}>
              🟢 ¿Cómo se calcularon las Horas BNX Convertidor?
            </div>
            <div style={{ fontSize: 14, color: t.muted || '#94a3b8', lineHeight: 1.8 }}>
              Las horas BNX son el tiempo real medido en cada sesión de desarrollo. El proceso fue:
            </div>
            <div style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.8, marginTop: 8 }}>
              <div>1. <span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Diseño iterativo en tiempo real</span> — no hubo fase de diseño separada. Se diseñó e implementó simultáneamente con el convertidor.</div>
              <div>2. <span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Generación de código acelerada</span> — el convertidor BNX automatiza la traducción de grafos a código Spark.</div>
              <div>3. <span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Validación inmediata</span> — cada cambio se probó al instante con grafos de prueba (small, advanced, monster).</div>
              <div>4. <span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Deploy en la misma sesión</span> — Lambda y Amplify se configuraron como parte del flujo.</div>
            </div>
            <div style={{ fontSize: 13, color: t.dim || '#64748b', marginTop: 10, fontStyle: 'italic' }}>
              Cada sesión duró entre 2-4 horas. El total de 27h representa ~7 sesiones de trabajo.
            </div>
          </div>

          <div style={{ padding: 16, borderRadius: 8, background: (t.bg || '#0f1117') + '80', border: `1px solid ${t.border || '#334155'}30` }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: '#6366f1', marginBottom: 8 }}>
              🔵 ¿Cómo se calcula el Ahorro?
            </div>
            <div style={{ fontSize: 14, color: t.muted || '#94a3b8', lineHeight: 1.8 }}>
              <div><span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Ahorro en horas</span> = Horas Tradicionales - Horas BNX</div>
              <div><span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Ahorro %</span> = (1 - Horas BNX / Horas Tradicionales) × 100</div>
              <div><span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Velocidad</span> = Horas Tradicionales / Horas BNX</div>
              <div><span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Costo</span> = Horas × $30 USD/h (tarifa promedio dev senior LATAM)</div>
            </div>
          </div>

          <div style={{ padding: 16, borderRadius: 8, background: (t.bg || '#0f1117') + '80', border: `1px solid ${t.border || '#334155'}30` }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: '#f59e0b', marginBottom: 8 }}>
              🟡 ¿Cómo se calcula la Migración Masiva (40K jobs)?
            </div>
            <div style={{ fontSize: 14, color: t.muted || '#94a3b8', lineHeight: 1.8 }}>
              <div><span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Distribución</span>: 40% simple, 40% medium, 20% complex — basado en perfil típico de migración Ab Initio bancaria.</div>
              <div style={{ marginTop: 6 }}><span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Horas por job (Tradicional)</span>:</div>
              <div style={{ paddingLeft: 16 }}>• Simple (Input→Reformat→Output): <span style={{ color: '#ef4444' }}>8h</span> — análisis del grafo, mapeo de campos, codificación manual, testing</div>
              <div style={{ paddingLeft: 16 }}>• Medium (Joins+Rollups+Lookups): <span style={{ color: '#ef4444' }}>24h</span> — múltiples fuentes, lógica de negocio, validación cruzada</div>
              <div style={{ paddingLeft: 16 }}>• Complex (Multi-stage+COBOL+Subgraphs): <span style={{ color: '#ef4444' }}>60h</span> — COBOL parsing, EBCDIC, subgrafos anidados, testing extensivo</div>
              <div style={{ marginTop: 6 }}><span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Horas por job (BNX)</span>:</div>
              <div style={{ paddingLeft: 16 }}>• Simple: <span style={{ color: '#22c55e' }}>0.5h</span> — compilación automática, revisión rápida del output</div>
              <div style={{ paddingLeft: 16 }}>• Medium: <span style={{ color: '#22c55e' }}>1.5h</span> — compilación + ajustes manuales de join keys y reglas</div>
              <div style={{ paddingLeft: 16 }}>• Complex: <span style={{ color: '#22c55e' }}>4h</span> — COBOL parsing automático + validación semántica + ajustes</div>
              <div style={{ marginTop: 6 }}><span style={{ color: t.text || '#e2e8f0', fontWeight: 500 }}>Fórmula</span>: Total = (Simple × hrs) + (Medium × hrs) + (Complex × hrs)</div>
            </div>
          </div>

          <div>
            <div style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 8 }}>
              📋 Desglose por Fase
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: `2px solid ${t.border || '#334155'}` }}>
                  <th style={{ textAlign: 'left', padding: '8px 10px', color: t.dim || '#64748b' }}>Fase</th>
                  <th style={{ textAlign: 'center', padding: '8px 10px', color: '#ef4444' }}>Tradicional</th>
                  <th style={{ textAlign: 'center', padding: '8px 10px', color: '#22c55e' }}>BNX</th>
                  <th style={{ textAlign: 'left', padding: '8px 10px', color: t.dim || '#64748b' }}>Qué incluye</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { phase: 'Parser MP/XFR/DML', t: '40h', b: '3h', why: '3 parsers con regex, manejo de errores, edge cases, tests unitarios por parser' },
                  { phase: 'DAG Builder', t: '24h', b: '2h', why: 'Topological sort (Kahn\'s algorithm), detección de ciclos, manejo de subgraphs, parents/children' },
                  { phase: 'Validador Semántico', t: '32h', b: '2h', why: 'Inferencia de columnas nodo por nodo, propagación a través del DAG, validación de join keys vs columnas disponibles' },
                  { phase: 'Glue Codegen', t: '40h', b: '3h', why: 'Generación de código PySpark válido para 7 tipos de nodo (SOURCE, TRANSFORM, JOIN, DEDUP, NORMALIZE, LOOKUP, SINK) + S3/JDBC/Kafka' },
                  { phase: 'PySpark Codegen', t: '32h', b: '1h', why: 'Variante sin GlueContext, usa SparkSession. Misma lógica, diferente boilerplate' },
                  { phase: 'COBOL Parser', t: '60h', b: '2h', why: 'Parsing de FILE SECTION (FD + 05 levels), PROCEDURE DIVISION (PERFORM/IF/COMPUTE), PIC types, COMP-3, detección EBCDIC' },
                  { phase: 'DEDUP/NORM/LOOKUP', t: '24h', b: '1h', why: 'Window functions para DEDUP, explode/split para NORMALIZE, broadcast join para LOOKUP' },
                  { phase: 'Accuracy Engine', t: '16h', b: '1h', why: 'Métricas ponderadas: 30% nodos, 20% edges, 30% transforms, 20% joins. Detección de issues por nodo' },
                  { phase: 'React UI + DAG Viewer', t: '48h', b: '3h', why: 'ReactFlow para grafos interactivos, tema día/noche, panel de detalle por nodo, file upload múltiple' },
                  { phase: 'Designer Visual', t: '60h', b: '3h', why: 'Editor drag & drop, custom nodes con handles, edición de reglas por nodo, compilación en vivo, code modal' },
                  { phase: 'Connectors S3/JDBC/Kafka', t: '32h', b: '2h', why: 'source_type/sink_type en XFR, codegen condicional para readStream (Kafka), jdbc options, parquet/csv/json' },
                  { phase: 'API + Lambda', t: '24h', b: '2h', why: 'FastAPI con multipart upload, Lambda handler con cgi parsing, CORS, Function URL, /compile y /cobol endpoints' },
                  { phase: 'Tests + Cleanup', t: '16h', b: '1h', why: '13 tests (parser, builder, validator), eliminación de 20+ archivos legacy duplicados' },
                  { phase: 'Deploy', t: '8h', b: '1h', why: 'Amplify hosting (amplify.yml), Lambda zip deploy, Function URL config, CORS headers, env variables' },
                ].map((r, i) => (
                  <tr key={i} style={{ borderBottom: `1px solid ${t.border || '#334155'}20` }}>
                    <td style={{ padding: '8px 10px', color: t.text || '#e2e8f0', fontWeight: 500 }}>{r.phase}</td>
                    <td style={{ padding: '8px 10px', color: '#ef4444', textAlign: 'center', fontWeight: 600 }}>{r.t}</td>
                    <td style={{ padding: '8px 10px', color: '#22c55e', textAlign: 'center', fontWeight: 600 }}>{r.b}</td>
                    <td style={{ padding: '8px 10px', color: t.dim || '#64748b', fontSize: 12 }}>{r.why}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ padding: 16, borderRadius: 8, background: (t.bg || '#0f1117') + '80', border: `1px solid ${t.border || '#334155'}30` }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 8 }}>
              💰 Costos de Infraestructura
            </div>
            <div style={{ fontSize: 14, color: t.muted || '#94a3b8', lineHeight: 1.8 }}>
              <div><span style={{ fontWeight: 600, color: '#22c55e' }}>Sandbox ($0/mes)</span> — Python 3.11 + Node.js 18 instalados localmente. Sin costo. Para desarrollo y pruebas.</div>
              <div style={{ marginTop: 6 }}><span style={{ fontWeight: 600, color: '#f59e0b' }}>On-Premise ($200-500/mes)</span> — Servidor Linux (4 CPU, 8GB RAM). Spark standalone o YARN. Incluye: hardware, electricidad, mantenimiento, SSL, firewall. Para equipos que no pueden usar cloud.</div>
              <div style={{ marginTop: 6 }}><span style={{ fontWeight: 600, color: '#6366f1' }}>Cloud AWS ($5-20/mes)</span> — Desglose:</div>
              <div style={{ paddingLeft: 16, fontSize: 13 }}>
                <div>• Lambda: ~$0.20 por 1M invocaciones + $0.0000166/GB-segundo</div>
                <div>• Amplify Hosting: gratis hasta 5GB/mes de transferencia</div>
                <div>• S3: $0.023/GB almacenamiento + $0.0004/1K requests</div>
                <div>• CloudWatch Logs: $0.50/GB ingestado</div>
                <div>• Total estimado para uso bajo-medio: $5-20/mes</div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
