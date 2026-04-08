import { useState } from 'react'

const DAMA_DATA = [
  {
    rubro: 'Gobernanza',
    icon: '🏛️',
    color: '#6366f1',
    onPremise: 'Centralizada, rígida. Comités formales, procesos manuales de aprobación.',
    cloud: 'Federada, más ágil. Data Mesh, ownership distribuido, políticas como código.',
    aws: 'Lake Formation, IAM policies, Glue Catalog tags',
    bnx: 'GovernancePage con políticas editables, export JSON/TXT',
  },
  {
    rubro: 'Arquitectura',
    icon: '🏗️',
    color: '#22c55e',
    onPremise: 'Tradicional (monolitos). Ab Initio Co>OS, ETL centralizado, batch nocturno.',
    cloud: 'Microservicios / event-driven. Glue jobs independientes, Kafka streaming, Step Functions.',
    aws: 'Glue, EMR, MSK, Step Functions, Lambda',
    bnx: 'DAG Builder + Codegen (Glue/Spark/StepFn/Terraform/Airflow)',
  },
  {
    rubro: 'Modelado (ODM)',
    icon: '📐',
    color: '#f59e0b',
    onPremise: 'Core transaccional. Modelos 3NF, schemas rígidos, cambios lentos.',
    cloud: 'ODS + APIs + Data Products. Schema-on-read, evolución de schema, Data Products.',
    aws: 'Glue Catalog, Lake Formation, Schema Registry',
    bnx: 'DML parser con schema inference, validación semántica',
  },
  {
    rubro: 'Integración',
    icon: '🔄',
    color: '#06b6d4',
    onPremise: 'ETL batch. Ab Initio graphs, COBOL batch, archivos planos, EBCDIC.',
    cloud: 'Streaming (Kafka, APIs). CDC real-time, event sourcing, micro-batch.',
    aws: 'DMS, MSK, Kinesis, AppFlow, Glue Streaming',
    bnx: 'SOURCE con S3/JDBC/Kafka, COBOL parser, PLAN/PSET parser',
  },
  {
    rubro: 'Storage',
    icon: '💾',
    color: '#a855f7',
    onPremise: 'RDBMS (Oracle, SQL Server). Storage costoso, escalamiento vertical.',
    cloud: 'S3, Lakehouse, NoSQL. Storage barato, escalamiento infinito, formatos abiertos.',
    aws: 'S3 (Parquet/Iceberg), DynamoDB, Redshift, ElastiCache',
    bnx: 'Terraform codegen con S3 buckets + encryption + lifecycle',
  },
  {
    rubro: 'Calidad',
    icon: '✅',
    color: '#22c55e',
    onPremise: 'Controles manuales. Scripts de validación, revisión humana, reportes Excel.',
    cloud: 'Automatizada / Data Observability. Checks en pipeline, alertas automáticas, SLAs.',
    aws: 'Glue Data Quality, CloudWatch, Deequ',
    bnx: 'Semantic Validator (column inference, join key validation, accuracy engine)',
  },
  {
    rubro: 'Seguridad',
    icon: '🔒',
    color: '#ef4444',
    onPremise: 'Perimetral. Firewall, VPN, acceso por red, controles de SO.',
    cloud: 'Zero Trust + IAM. Roles granulares, encryption at rest/transit, audit trail.',
    aws: 'IAM, KMS, Macie, CloudTrail, VPC endpoints',
    bnx: 'Terraform codegen con IAM roles, S3 encryption, least privilege',
  },
  {
    rubro: 'Metadatos',
    icon: '🏷️',
    color: '#ec4899',
    onPremise: 'Limitados. Documentación manual, wikis desactualizadas, tribal knowledge.',
    cloud: 'Data Catalog + Lineage. Metadata automática, lineage end-to-end, search.',
    aws: 'Glue Catalog, DataZone, Lake Formation',
    bnx: 'DML schema, XFR rules, DAG lineage, accuracy metrics',
  },
  {
    rubro: 'MDM',
    icon: '👤',
    color: '#f59e0b',
    onPremise: 'Centralizado. Master data en un solo sistema, sincronización batch.',
    cloud: 'Híbrido / distribuido. Golden records, CDC, entity resolution.',
    aws: 'Entity Resolution, DynamoDB, Neptune',
    bnx: 'DEDUP + LOOKUP nodes, join key validation',
  },
  {
    rubro: 'BI',
    icon: '📊',
    color: '#6366f1',
    onPremise: 'Data Warehouse. Reportes estáticos, cubos OLAP, ciclos largos.',
    cloud: 'Lakehouse + BI + AI. Dashboards real-time, ML integrado, self-service.',
    aws: 'Redshift, Athena, QuickSight, SageMaker',
    bnx: 'Multi-target codegen (Glue → Redshift, Athena queries)',
  },
  {
    rubro: 'Ciclo de vida',
    icon: '♻️',
    color: '#06b6d4',
    onPremise: 'Largo. Cambios toman semanas/meses, releases trimestrales.',
    cloud: 'Dinámico / automatizado. CI/CD, deploy en minutos, feature flags.',
    aws: 'CodePipeline, Step Functions, Lambda, Amplify',
    bnx: 'Lambda deploy, Amplify CI/CD, Terraform IaC',
  },
]

export default function DamaPage({ theme }) {
  const t = theme || {}
  const [expandedRow, setExpandedRow] = useState(null)

  const exportDama = () => {
    let r = 'DAMA FRAMEWORK — ON-PREMISE vs CLOUD\n'
    r += '='.repeat(60) + '\n\n'
    DAMA_DATA.forEach(d => {
      r += `${d.icon} ${d.rubro}\n`
      r += `  On-Premise: ${d.onPremise}\n`
      r += `  Cloud:      ${d.cloud}\n`
      r += `  AWS:        ${d.aws}\n`
      r += `  BNX:        ${d.bnx}\n\n`
    })
    const blob = new Blob([r], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'dama_framework.txt'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div style={{ padding: 32, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 700, color: t.text || '#e2e8f0', margin: 0 }}>
            📐 DAMA Framework — On-Premise vs Cloud
          </h2>
          <p style={{ fontSize: 14, color: t.dim || '#64748b', marginTop: 4 }}>
            Comparativa de capacidades de gestión de datos. Click en un rubro para ver detalles.
          </p>
        </div>
        <button onClick={exportDama} style={{
          padding: '10px 20px', borderRadius: 8, fontSize: 14, cursor: 'pointer',
          background: '#f59e0b20', border: '1px solid #f59e0b40', color: '#f59e0b', fontWeight: 600,
        }}>📥 Export</button>
      </div>

      {/* Table */}
      <div style={{
        borderRadius: 10, overflow: 'hidden',
        border: `1px solid ${t.border || '#334155'}`,
      }}>
        {/* Header */}
        <div style={{
          display: 'grid', gridTemplateColumns: '180px 1fr 1fr',
          background: t.card || '#1e2433', padding: '12px 16px',
          borderBottom: `2px solid ${t.border || '#334155'}`,
          fontSize: 14, fontWeight: 600, color: t.muted || '#94a3b8',
        }}>
          <span>Rubro DAMA</span>
          <span style={{ color: '#ef4444' }}>🏢 On-Premise</span>
          <span style={{ color: '#22c55e' }}>☁️ Cloud</span>
        </div>

        {/* Rows */}
        {DAMA_DATA.map((d, i) => (
          <div key={d.rubro}>
            <div
              style={{
                display: 'grid', gridTemplateColumns: '180px 1fr 1fr',
                padding: '14px 16px', cursor: 'pointer',
                background: expandedRow === i ? d.color + '08' : 'transparent',
                borderBottom: `1px solid ${t.border || '#334155'}20`,
              }}
              onClick={() => setExpandedRow(expandedRow === i ? null : i)}
            >
              <span style={{ fontSize: 14, fontWeight: 600, color: d.color, display: 'flex', alignItems: 'center', gap: 6 }}>
                {d.icon} {d.rubro}
              </span>
              <span style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.5 }}>{d.onPremise}</span>
              <span style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.5 }}>{d.cloud}</span>
            </div>

            {expandedRow === i && (
              <div style={{
                padding: '12px 16px 16px', display: 'flex', gap: 12, flexWrap: 'wrap',
                background: d.color + '05', borderBottom: `1px solid ${t.border || '#334155'}20`,
              }}>
                <div style={{
                  flex: '1 1 250px', padding: 12, borderRadius: 8,
                  background: '#ff990015', border: '1px solid #ff990030',
                }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#ff9900', marginBottom: 4 }}>☁️ Servicios AWS</div>
                  <div style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.6 }}>{d.aws}</div>
                </div>
                <div style={{
                  flex: '1 1 250px', padding: 12, borderRadius: 8,
                  background: '#6366f115', border: '1px solid #6366f130',
                }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#818cf8', marginBottom: 4 }}>🔧 BNX Convertidor</div>
                  <div style={{ fontSize: 13, color: t.muted || '#94a3b8', lineHeight: 1.6 }}>{d.bnx}</div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
