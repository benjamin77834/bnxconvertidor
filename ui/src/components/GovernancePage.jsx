import { useState } from 'react'

const POLICIES = [
  {
    domain: 'Clasificación de Datos',
    icon: '🏷️',
    color: '#6366f1',
    policies: [
      { id: 'CL01', name: 'Datos Públicos', desc: 'Información disponible al público general', level: 'low', examples: 'Tasas publicadas, sucursales, productos' },
      { id: 'CL02', name: 'Datos Internos', desc: 'Uso interno del banco, no sensible', level: 'medium', examples: 'Reportes operativos, métricas de negocio' },
      { id: 'CL03', name: 'Datos Confidenciales', desc: 'Información restringida por regulación', level: 'high', examples: 'Saldos, movimientos, scores de riesgo' },
      { id: 'CL04', name: 'Datos Secretos (PII)', desc: 'Información personal identificable', level: 'critical', examples: 'CURP, RFC, número de cuenta, biométricos' },
    ]
  },
  {
    domain: 'Calidad de Datos',
    icon: '✅',
    color: '#22c55e',
    policies: [
      { id: 'QA01', name: 'Completitud', desc: 'Campos obligatorios no pueden ser NULL', level: 'high', rule: 'NOT NULL check en campos PK y críticos' },
      { id: 'QA02', name: 'Unicidad', desc: 'No duplicados en campos clave', level: 'high', rule: 'DEDUP por PK antes de carga' },
      { id: 'QA03', name: 'Formato', desc: 'Validación de formatos estándar', level: 'medium', rule: 'Regex para CLABE (18 dígitos), RFC, CURP' },
      { id: 'QA04', name: 'Rango', desc: 'Valores dentro de rangos válidos', level: 'medium', rule: 'amount > 0, rate BETWEEN 0 AND 100' },
      { id: 'QA05', name: 'Consistencia', desc: 'Datos coherentes entre fuentes', level: 'high', rule: 'Cross-validation entre Core y CRM' },
      { id: 'QA06', name: 'Frescura', desc: 'Datos actualizados dentro del SLA', level: 'medium', rule: 'Max latency: batch 24h, CDC 1h, stream 5min' },
    ]
  },
  {
    domain: 'Seguridad y Acceso',
    icon: '🔒',
    color: '#ef4444',
    policies: [
      { id: 'SE01', name: 'Encriptación en Reposo', desc: 'Todos los datos en S3 encriptados', level: 'critical', aws: 'S3 SSE-KMS, RDS encryption' },
      { id: 'SE02', name: 'Encriptación en Tránsito', desc: 'TLS 1.2+ para toda comunicación', level: 'critical', aws: 'ALB/API Gateway TLS, VPC endpoints' },
      { id: 'SE03', name: 'Control de Acceso (RBAC)', desc: 'Acceso basado en roles y least privilege', level: 'critical', aws: 'IAM roles, Lake Formation permissions' },
      { id: 'SE04', name: 'Enmascaramiento PII', desc: 'Datos PII enmascarados en ambientes no-prod', level: 'high', aws: 'Glue DataBrew, Macie detection' },
      { id: 'SE05', name: 'Auditoría de Acceso', desc: 'Log de todo acceso a datos sensibles', level: 'critical', aws: 'CloudTrail, S3 access logs, Athena audit' },
      { id: 'SE06', name: 'Retención y Borrado', desc: 'Políticas de retención por tipo de dato', level: 'high', aws: 'S3 Lifecycle, Glacier archive' },
    ]
  },
  {
    domain: 'Regulatorio (CNBV / Banxico)',
    icon: '⚖️',
    color: '#f59e0b',
    policies: [
      { id: 'RG01', name: 'Reporte R04', desc: 'Catálogo mínimo de clientes', level: 'critical', freq: 'Mensual', entity: 'CNBV' },
      { id: 'RG02', name: 'Reporte R08', desc: 'Operaciones relevantes (>$50K USD)', level: 'critical', freq: 'Mensual', entity: 'CNBV/UIF' },
      { id: 'RG03', name: 'Reporte R28', desc: 'Créditos y cartera vencida', level: 'critical', freq: 'Mensual', entity: 'CNBV' },
      { id: 'RG04', name: 'EACP', desc: 'Estados financieros consolidados', level: 'critical', freq: 'Trimestral', entity: 'CNBV' },
      { id: 'RG05', name: 'PLD/FT', desc: 'Prevención de lavado de dinero', level: 'critical', freq: 'Continuo', entity: 'UIF' },
      { id: 'RG06', name: 'SPEI Reportes', desc: 'Conciliación de transferencias', level: 'high', freq: 'Diario', entity: 'Banxico' },
      { id: 'RG07', name: 'Protección de Datos (LFPDPPP)', desc: 'Ley de protección de datos personales', level: 'critical', freq: 'Continuo', entity: 'INAI' },
    ]
  },
  {
    domain: 'Linaje y Metadata',
    icon: '🧬',
    color: '#a855f7',
    policies: [
      { id: 'LN01', name: 'Linaje End-to-End', desc: 'Trazabilidad desde fuente hasta reporte', level: 'high', tool: 'BNX Lineage + Glue Catalog' },
      { id: 'LN02', name: 'Diccionario de Datos', desc: 'Definición de cada campo y tabla', level: 'medium', tool: 'Glue Catalog + DataHub' },
      { id: 'LN03', name: 'Data Owners', desc: 'Cada dataset tiene un dueño asignado', level: 'high', tool: 'Tag en Glue Catalog' },
      { id: 'LN04', name: 'Impact Analysis', desc: 'Análisis de impacto antes de cambios', level: 'medium', tool: 'BNX Validator + DAG analysis' },
      { id: 'LN05', name: 'Versionamiento', desc: 'Control de versiones de schemas y pipelines', level: 'medium', tool: 'Git + BNX .mp/.xfr versioning' },
    ]
  },
  {
    domain: 'SLAs y Operación',
    icon: '⏱️',
    color: '#06b6d4',
    policies: [
      { id: 'SL01', name: 'Batch SLA', desc: 'Procesos batch completados antes de 6am', level: 'high', target: '< 4 horas', monitor: 'CloudWatch + SNS' },
      { id: 'SL02', name: 'CDC Latency', desc: 'Cambios reflejados en < 1 hora', level: 'medium', target: '< 60 min', monitor: 'DMS metrics' },
      { id: 'SL03', name: 'Stream Latency', desc: 'Eventos procesados en < 5 minutos', level: 'high', target: '< 5 min', monitor: 'MSK consumer lag' },
      { id: 'SL04', name: 'Disponibilidad', desc: 'Data Lake disponible 99.9%', level: 'critical', target: '99.9%', monitor: 'S3 + Glue health checks' },
      { id: 'SL05', name: 'Recovery (RPO/RTO)', desc: 'Recuperación ante desastres', level: 'critical', target: 'RPO 1h, RTO 4h', monitor: 'S3 cross-region replication' },
    ]
  },
]

const LEVEL_COLOR = {
  low: '#22c55e', medium: '#f59e0b', high: '#ef4444', critical: '#dc2626',
}
const LEVEL_LABEL = {
  low: 'Bajo', medium: 'Medio', high: 'Alto', critical: 'Crítico',
}

export default function GovernancePage({ theme }) {
  const t = theme || {}
  const [expanded, setExpanded] = useState(POLICIES.map(() => true))
  const [editPolicy, setEditPolicy] = useState(null)
  const [customPolicies, setCustomPolicies] = useState(() => {
    try { return JSON.parse(localStorage.getItem('bnx_governance_custom') || '{}') } catch { return {} }
  })

  const toggle = (i) => setExpanded(e => e.map((v, j) => j === i ? !v : v))

  const saveCustom = (id, notes) => {
    const updated = { ...customPolicies, [id]: notes }
    setCustomPolicies(updated)
    localStorage.setItem('bnx_governance_custom', JSON.stringify(updated))
    setEditPolicy(null)
  }

  const exportGovernance = () => {
    const data = {
      policies: POLICIES,
      customNotes: customPolicies,
      exportedAt: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'governance_policies.json'; a.click()
    URL.revokeObjectURL(url)
  }

  const card = {
    background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, overflow: 'hidden',
  }

  const totalPolicies = POLICIES.reduce((s, d) => s + d.policies.length, 0)
  const criticalCount = POLICIES.reduce((s, d) => s + d.policies.filter(p => p.level === 'critical').length, 0)

  return (
    <div style={{ padding: 32, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: t.text || '#e2e8f0', margin: 0 }}>
            🏛️ Gobierno de Datos — Políticas
          </h2>
          <p style={{ fontSize: 14, color: t.dim || '#64748b', marginTop: 4 }}>
            Marco de gobierno para plataforma de datos bancaria
          </p>
        </div>
        <button onClick={exportGovernance} style={{
          padding: '8px 16px', borderRadius: 8, fontSize: 13, cursor: 'pointer',
          background: '#f59e0b20', border: '1px solid #f59e0b40', color: '#f59e0b',
        }}>📥 Export Policies</button>
      </div>

      {/* Summary */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {[
          { label: 'Dominios', value: POLICIES.length, color: '#6366f1' },
          { label: 'Políticas', value: totalPolicies, color: '#22c55e' },
          { label: 'Críticas', value: criticalCount, color: '#ef4444' },
          { label: 'Con notas', value: Object.keys(customPolicies).length, color: '#f59e0b' },
        ].map(s => (
          <div key={s.label} style={{ ...card, padding: 16, flex: '1 1 120px', textAlign: 'center' }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 13, color: t.muted || '#94a3b8' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Policy domains */}
      {POLICIES.map((domain, di) => (
        <div key={domain.domain} style={card}>
          <div
            onClick={() => toggle(di)}
            style={{
              padding: '14px 20px', cursor: 'pointer',
              background: domain.color + '10', borderBottom: expanded[di] ? `1px solid ${t.border || '#334155'}` : 'none',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}
          >
            <span style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0' }}>
              {domain.icon} {domain.domain}
            </span>
            <span style={{ fontSize: 12, color: t.dim || '#64748b' }}>
              {domain.policies.length} políticas {expanded[di] ? '▼' : '▶'}
            </span>
          </div>
          {expanded[di] && (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {domain.policies.map(p => (
                <div key={p.id} style={{
                  padding: '12px 20px', borderBottom: `1px solid ${t.border || '#334155'}20`,
                  display: 'flex', gap: 12, alignItems: 'flex-start',
                }}>
                  <span style={{
                    padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 600,
                    background: LEVEL_COLOR[p.level] + '20', color: LEVEL_COLOR[p.level],
                    border: `1px solid ${LEVEL_COLOR[p.level]}40`, whiteSpace: 'nowrap', marginTop: 2,
                  }}>{LEVEL_LABEL[p.level]}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <span style={{ fontSize: 11, color: domain.color, fontWeight: 600 }}>{p.id}</span>
                      <span style={{ fontSize: 14, color: t.text || '#e2e8f0', fontWeight: 500 }}>{p.name}</span>
                    </div>
                    <div style={{ fontSize: 12, color: t.muted || '#94a3b8', marginTop: 2 }}>{p.desc}</div>
                    {(p.examples || p.rule || p.aws || p.freq || p.target) && (
                      <div style={{ fontSize: 11, color: t.dim || '#64748b', marginTop: 4 }}>
                        {p.examples && <span>📌 {p.examples}</span>}
                        {p.rule && <span>📏 {p.rule}</span>}
                        {p.aws && <span>☁️ {p.aws}</span>}
                        {p.freq && <span>📅 {p.freq} — {p.entity}</span>}
                        {p.target && <span>🎯 {p.target} — {p.monitor}</span>}
                      </div>
                    )}
                    {customPolicies[p.id] && (
                      <div style={{
                        fontSize: 11, color: '#f59e0b', marginTop: 4,
                        padding: '4px 8px', background: '#f59e0b10', borderRadius: 4,
                      }}>📝 {customPolicies[p.id]}</div>
                    )}
                  </div>
                  <button onClick={() => setEditPolicy(editPolicy === p.id ? null : p.id)} style={{
                    padding: '3px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                    background: 'transparent', border: `1px solid ${t.border || '#334155'}`,
                    color: t.muted || '#94a3b8',
                  }}>{editPolicy === p.id ? '✕' : '✏️'}</button>
                  {editPolicy === p.id && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 200 }}>
                      <textarea
                        defaultValue={customPolicies[p.id] || ''}
                        placeholder="Agregar notas..."
                        rows={2}
                        style={{
                          padding: '6px 8px', borderRadius: 6, fontSize: 11,
                          background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
                          color: t.text || '#e2e8f0', outline: 'none', resize: 'vertical',
                        }}
                        ref={el => { if (el) el._save = () => saveCustom(p.id, el.value) }}
                      />
                      <button onClick={(e) => {
                        const textarea = e.target.previousSibling
                        saveCustom(p.id, textarea.value)
                      }} style={{
                        padding: '3px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                        background: '#22c55e20', border: '1px solid #22c55e40', color: '#22c55e',
                      }}>💾 Save Note</button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
