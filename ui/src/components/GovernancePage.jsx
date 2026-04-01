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
  {
    domain: 'ML / SageMaker Governance',
    icon: '🧠',
    color: '#ec4899',
    policies: [
      { id: 'ML01', name: 'Model Registry', desc: 'Todos los modelos registrados con versión y métricas', level: 'high', aws: 'SageMaker Model Registry' },
      { id: 'ML02', name: 'Feature Store', desc: 'Features centralizados y reutilizables', level: 'high', aws: 'SageMaker Feature Store → S3/Glue Catalog' },
      { id: 'ML03', name: 'Experiment Tracking', desc: 'Registro de hiperparámetros, métricas y artefactos', level: 'medium', aws: 'SageMaker Experiments + MLflow' },
      { id: 'ML04', name: 'Model Bias & Fairness', desc: 'Detección de sesgo en datos y predicciones', level: 'critical', aws: 'SageMaker Clarify' },
      { id: 'ML05', name: 'Model Explainability', desc: 'Explicabilidad de decisiones (SHAP, LIME)', level: 'high', aws: 'SageMaker Clarify Explainability' },
      { id: 'ML06', name: 'Model Monitoring', desc: 'Detección de data drift y model decay', level: 'critical', aws: 'SageMaker Model Monitor → CloudWatch' },
      { id: 'ML07', name: 'CI/CD de Modelos', desc: 'Pipeline automatizado de entrenamiento y deploy', level: 'high', aws: 'SageMaker Pipelines + CodePipeline' },
      { id: 'ML08', name: 'Aprobación de Modelos', desc: 'Workflow de aprobación antes de producción', level: 'critical', aws: 'SageMaker Model Registry approval + SNS' },
      { id: 'ML09', name: 'Data Lineage ML', desc: 'Trazabilidad de datos usados en entrenamiento', level: 'high', aws: 'SageMaker Lineage Tracking → Glue Catalog' },
      { id: 'ML10', name: 'Acceso a Datos de Training', desc: 'Solo datos aprobados para entrenamiento', level: 'critical', aws: 'Lake Formation + IAM + VPC endpoints' },
    ]
  },
  {
    domain: 'Arquitectura AWS — Servicios',
    icon: '☁️',
    color: '#ff9900',
    policies: [
      { id: 'AW01', name: 'S3 Data Lake', desc: 'Almacenamiento central: raw/, curated/, business/', level: 'critical', aws: 'S3 + Glacier + Lifecycle policies' },
      { id: 'AW02', name: 'AWS Glue', desc: 'ETL serverless: crawlers, jobs, catalog', level: 'critical', aws: 'Glue Jobs (BNX generated) + Glue Catalog' },
      { id: 'AW03', name: 'Amazon EMR', desc: 'Procesamiento distribuido para ML y big data', level: 'high', aws: 'EMR Serverless + Spark' },
      { id: 'AW04', name: 'SageMaker', desc: 'Plataforma ML: training, inference, monitoring', level: 'high', aws: 'SageMaker Studio + Endpoints + Pipelines' },
      { id: 'AW05', name: 'Amazon Redshift', desc: 'Data Warehouse para BI y reportes pesados', level: 'high', aws: 'Redshift Serverless + Spectrum (S3 query)' },
      { id: 'AW06', name: 'Amazon Athena', desc: 'SQL ad-hoc sobre S3 sin infraestructura', level: 'medium', aws: 'Athena + Glue Catalog + S3' },
      { id: 'AW07', name: 'Amazon MSK', desc: 'Kafka managed para streaming de eventos', level: 'high', aws: 'MSK + MSK Connect + Schema Registry' },
      { id: 'AW08', name: 'AWS DMS', desc: 'Migración y CDC desde bases legacy', level: 'high', aws: 'DMS + SCT (Schema Conversion Tool)' },
      { id: 'AW09', name: 'Lake Formation', desc: 'Gobierno centralizado del Data Lake', level: 'critical', aws: 'Lake Formation permissions + Glue Catalog' },
      { id: 'AW10', name: 'CloudWatch + SNS', desc: 'Monitoreo, alertas y notificaciones', level: 'high', aws: 'CloudWatch Alarms + SNS + PagerDuty' },
      { id: 'AW11', name: 'AWS Step Functions', desc: 'Orquestación de pipelines y workflows', level: 'medium', aws: 'Step Functions + Glue Jobs + Lambda' },
      { id: 'AW12', name: 'Amazon QuickSight', desc: 'Dashboards y visualización de datos', level: 'medium', aws: 'QuickSight + Athena/Redshift datasources' },
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
    borderRadius: 10,
  }

  const totalPolicies = POLICIES.reduce((s, d) => s + d.policies.length, 0)
  const criticalCount = POLICIES.reduce((s, d) => s + d.policies.filter(p => p.level === 'critical').length, 0)

  return (
    <div style={{ padding: 40, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 28 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontSize: 26, fontWeight: 700, color: t.text || '#e2e8f0', margin: 0 }}>
            🏛️ Gobierno de Datos — Políticas
          </h2>
          <p style={{ fontSize: 16, color: t.dim || '#64748b', marginTop: 6 }}>
            Marco de gobierno para plataforma de datos bancaria. Click ✏️ para agregar notas.
          </p>
        </div>
        <button onClick={exportGovernance} style={{
          padding: '10px 20px', borderRadius: 8, fontSize: 14, cursor: 'pointer',
          background: '#f59e0b20', border: '1px solid #f59e0b40', color: '#f59e0b', fontWeight: 600,
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
          <div key={s.label} style={{ ...card, padding: 20, flex: '1 1 150px', textAlign: 'center' }}>
            <div style={{ fontSize: 36, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 15, color: t.muted || '#94a3b8', marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Policy domains */}
      {POLICIES.map((domain, di) => (
        <div key={domain.domain} style={card}>
          <div
            style={{
              padding: '16px 20px',
              background: domain.color + '10', borderBottom: `1px solid ${t.border || '#334155'}`,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}
          >
            <span style={{ fontSize: 18, fontWeight: 600, color: t.text || '#e2e8f0' }}>
              {domain.icon} {domain.domain}
            </span>
            <span style={{ fontSize: 14, color: t.dim || '#64748b' }}>
              {domain.policies.length} políticas
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {domain.policies.map(p => (
                <div key={p.id} style={{
                  padding: '16px 24px', borderBottom: `1px solid ${t.border || '#334155'}20`,
                  display: 'flex', flexDirection: 'column', gap: 8,
                }}>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{
                      padding: '3px 10px', borderRadius: 4, fontSize: 12, fontWeight: 600,
                      background: LEVEL_COLOR[p.level] + '20', color: LEVEL_COLOR[p.level],
                      border: `1px solid ${LEVEL_COLOR[p.level]}40`,
                    }}>{LEVEL_LABEL[p.level]}</span>
                    <span style={{ fontSize: 13, color: domain.color, fontWeight: 600 }}>{p.id}</span>
                    <span style={{ fontSize: 16, color: t.text || '#e2e8f0', fontWeight: 500 }}>{p.name}</span>
                    <button onClick={(e) => { e.stopPropagation(); setEditPolicy(editPolicy === p.id ? null : p.id) }} style={{
                      marginLeft: 'auto', padding: '3px 10px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
                      background: editPolicy === p.id ? '#f59e0b20' : 'transparent',
                      border: `1px solid ${t.border || '#334155'}`, color: t.muted || '#94a3b8',
                    }}>{editPolicy === p.id ? '✕ Close' : '✏️ Notes'}</button>
                  </div>

                  <div style={{ fontSize: 14, color: t.muted || '#94a3b8', lineHeight: 1.6 }}>{p.desc}</div>

                  {(p.examples || p.rule || p.aws || p.freq || p.target || p.tool) && (
                    <div style={{
                      fontSize: 13, color: t.dim || '#64748b', lineHeight: 1.8,
                      padding: '8px 12px', background: (t.bg || '#0f1117') + '80', borderRadius: 6,
                    }}>
                      {p.examples && <div>📌 <span style={{ color: t.muted || '#94a3b8' }}>{p.examples}</span></div>}
                      {p.rule && <div>📏 <span style={{ color: t.muted || '#94a3b8' }}>{p.rule}</span></div>}
                      {p.aws && <div>☁️ <span style={{ color: '#ff9900' }}>{p.aws}</span></div>}
                      {p.tool && <div>🔧 <span style={{ color: '#818cf8' }}>{p.tool}</span></div>}
                      {p.freq && <div>📅 <span style={{ color: t.muted || '#94a3b8' }}>{p.freq}</span> — <span style={{ color: '#f59e0b' }}>{p.entity}</span></div>}
                      {p.target && <div>🎯 <span style={{ color: '#22c55e' }}>{p.target}</span> — <span style={{ color: t.muted || '#94a3b8' }}>{p.monitor}</span></div>}
                    </div>
                  )}

                  {customPolicies[p.id] && (
                    <div style={{
                      fontSize: 13, color: '#f59e0b', padding: '8px 12px',
                      background: '#f59e0b10', borderRadius: 6, border: '1px solid #f59e0b20',
                    }}>📝 {customPolicies[p.id]}</div>
                  )}

                  {editPolicy === p.id && (
                    <div style={{
                      display: 'flex', flexDirection: 'column', gap: 6,
                      padding: '10px 12px', background: (t.bg || '#0f1117') + '80', borderRadius: 6,
                    }}>
                      <label style={{ fontSize: 12, color: t.dim || '#64748b' }}>Agregar notas o comentarios:</label>
                      <textarea
                        defaultValue={customPolicies[p.id] || ''}
                        placeholder="Escribe notas sobre esta política..."
                        rows={3}
                        style={{
                          padding: '8px 10px', borderRadius: 6, fontSize: 13,
                          background: t.bg || '#0f1117', border: `1px solid ${t.border || '#334155'}`,
                          color: t.text || '#e2e8f0', outline: 'none', resize: 'vertical',
                          fontFamily: 'inherit', lineHeight: 1.5,
                        }}
                        id={`note_${p.id}`}
                      />
                      <button onClick={() => {
                        const el = document.getElementById(`note_${p.id}`)
                        if (el) saveCustom(p.id, el.value)
                      }} style={{
                        padding: '6px 14px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                        background: '#22c55e20', border: '1px solid #22c55e40', color: '#22c55e',
                        alignSelf: 'flex-start',
                      }}>💾 Save Note</button>
                    </div>
                  )}
                </div>
              ))}
            </div>
        </div>
      ))}
    </div>
  )
}
