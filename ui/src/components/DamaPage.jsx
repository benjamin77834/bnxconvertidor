import { useState } from 'react'

const DAMA_DATA = [
  {
    rubro: 'Gobernanza de Datos',
    icon: '🏛️',
    color: '#6366f1',
    onPremise: 'Centralizada, rígida. Comités formales, procesos manuales de aprobación. Políticas en documentos Word/PDF.',
    cloud: 'Federada, más ágil. Data Mesh, ownership distribuido, políticas como código. Self-service con guardrails.',
    aws: 'Lake Formation (permisos centralizados), Glue Catalog (tags de clasificación), IAM policies, AWS Config rules',
    bnx: 'GovernancePage con 8 dominios, 55+ políticas editables, notas custom, export JSON/TXT, mapa de burbujas',
    maturity: ['Nivel 1: Sin gobierno formal', 'Nivel 2: Políticas documentadas', 'Nivel 3: Políticas automatizadas', 'Nivel 4: Gobierno federado', 'Nivel 5: Data Mesh completo'],
  },
  {
    rubro: 'Arquitectura de Datos',
    icon: '🏗️',
    color: '#22c55e',
    onPremise: 'Monolítica. Ab Initio Co>OS, ETL centralizado, batch nocturno. Un solo punto de fallo.',
    cloud: 'Microservicios / event-driven. Glue jobs independientes, Kafka streaming, Step Functions. Escalamiento horizontal.',
    aws: 'Glue (ETL), EMR (Spark), MSK (Kafka), Step Functions (orquestación), Lambda (serverless), EKS (containers)',
    bnx: 'DAG Builder + 5 codegens: Glue, PySpark, Step Functions, Terraform, Airflow. Subgraphs para modularidad.',
    maturity: ['Nivel 1: Monolito batch', 'Nivel 2: ETL modular', 'Nivel 3: Lakehouse', 'Nivel 4: Event-driven', 'Nivel 5: Data Mesh + streaming'],
  },
  {
    rubro: 'Modelado de Datos (ODM)',
    icon: '📐',
    color: '#f59e0b',
    onPremise: 'Core transaccional 3NF. Schemas rígidos, cambios requieren DBA. Modelos ER en Erwin.',
    cloud: 'ODS + APIs + Data Products. Schema-on-read, evolución de schema, Data Products con contratos.',
    aws: 'Glue Catalog (schema registry), Lake Formation (data products), Schema Registry (Kafka)',
    bnx: 'DML parser con schema inference, propagación de columnas por DAG, validación semántica automática',
    maturity: ['Nivel 1: Sin modelo formal', 'Nivel 2: ER documentado', 'Nivel 3: Dimensional (star schema)', 'Nivel 4: Data Vault', 'Nivel 5: Data Products'],
  },
  {
    rubro: 'Integración de Datos',
    icon: '🔄',
    color: '#06b6d4',
    onPremise: 'ETL batch. Ab Initio graphs, COBOL batch, archivos planos EBCDIC. Ventanas de proceso nocturnas.',
    cloud: 'Streaming + micro-batch. CDC real-time, event sourcing, APIs REST/GraphQL. Procesamiento continuo.',
    aws: 'DMS (CDC), MSK (Kafka), Kinesis (streaming), AppFlow (SaaS), Glue Streaming, EventBridge',
    bnx: 'SOURCE con S3/JDBC/Kafka, COBOL parser (EBCDIC/COMP-3), PLAN/PSET parser, multi-source pipelines',
    maturity: ['Nivel 1: Archivos planos manuales', 'Nivel 2: ETL batch automatizado', 'Nivel 3: CDC + micro-batch', 'Nivel 4: Streaming real-time', 'Nivel 5: Event mesh'],
  },
  {
    rubro: 'Almacenamiento (Storage)',
    icon: '💾',
    color: '#a855f7',
    onPremise: 'RDBMS (Oracle, SQL Server, DB2). Storage costoso, escalamiento vertical, licencias caras.',
    cloud: 'S3 Lakehouse + NoSQL. Storage $0.023/GB, escalamiento infinito, formatos abiertos (Parquet, Iceberg).',
    aws: 'S3 (data lake), Redshift (DW), DynamoDB (NoSQL), ElastiCache (cache), Glacier (archive)',
    bnx: 'Terraform codegen: S3 buckets con encryption KMS, lifecycle policies, particionamiento por fecha/región',
    maturity: ['Nivel 1: Solo RDBMS', 'Nivel 2: DW separado', 'Nivel 3: Data Lake (S3)', 'Nivel 4: Lakehouse (Iceberg)', 'Nivel 5: Multi-engine (lake + DW + NoSQL)'],
  },
  {
    rubro: 'Calidad de Datos',
    icon: '✅',
    color: '#22c55e',
    onPremise: 'Controles manuales. Scripts de validación ad-hoc, revisión humana, reportes Excel de excepciones.',
    cloud: 'Automatizada / Data Observability. Checks en pipeline, alertas automáticas, SLAs medibles, anomaly detection.',
    aws: 'Glue Data Quality, CloudWatch (alertas), Deequ (validación), SNS (notificaciones)',
    bnx: 'Semantic Validator: column inference, join key validation, accuracy engine (30% nodes + 20% edges + 30% transforms + 20% joins)',
    maturity: ['Nivel 1: Sin controles', 'Nivel 2: Validación manual', 'Nivel 3: Checks automatizados', 'Nivel 4: Data Observability', 'Nivel 5: Self-healing pipelines'],
  },
  {
    rubro: 'Seguridad de Datos',
    icon: '🔒',
    color: '#ef4444',
    onPremise: 'Perimetral. Firewall, VPN, acceso por red, controles de SO. PII en texto plano.',
    cloud: 'Zero Trust + IAM. Roles granulares, encryption at rest/transit, audit trail, PII masking automático.',
    aws: 'IAM (roles), KMS (encryption), Macie (PII detection), CloudTrail (audit), VPC endpoints, Lake Formation',
    bnx: 'Terraform codegen: IAM roles least privilege, S3 SSE-KMS, Glue job encryption. Governance policies de seguridad.',
    maturity: ['Nivel 1: Sin encryption', 'Nivel 2: Encryption at rest', 'Nivel 3: RBAC + audit', 'Nivel 4: Zero Trust', 'Nivel 5: Data Privacy automation'],
  },
  {
    rubro: 'Metadatos y Catálogo',
    icon: '🏷️',
    color: '#ec4899',
    onPremise: 'Limitados. Documentación manual en wikis, tribal knowledge, sin lineage automático.',
    cloud: 'Data Catalog + Lineage. Metadata automática, lineage end-to-end, search, impact analysis.',
    aws: 'Glue Catalog (schema), DataZone (data products), Lake Formation (permissions), CloudTrail (access lineage)',
    bnx: 'DML schema registry, XFR rules como metadata, DAG lineage visual, accuracy metrics por nodo',
    maturity: ['Nivel 1: Sin catálogo', 'Nivel 2: Wiki/docs manuales', 'Nivel 3: Catálogo automatizado', 'Nivel 4: Lineage end-to-end', 'Nivel 5: Active metadata'],
  },
  {
    rubro: 'Master Data (MDM)',
    icon: '👤',
    color: '#f59e0b',
    onPremise: 'Centralizado. Master data en un solo sistema, sincronización batch, golden record manual.',
    cloud: 'Híbrido / distribuido. Entity resolution automática, CDC para sincronización, golden records dinámicos.',
    aws: 'Entity Resolution, DynamoDB (master store), Neptune (graph), DMS (sync)',
    bnx: 'DEDUP nodes (Window + row_number), LOOKUP nodes (broadcast join), join key validation',
    maturity: ['Nivel 1: Sin MDM', 'Nivel 2: MDM centralizado', 'Nivel 3: MDM con CDC', 'Nivel 4: Entity resolution', 'Nivel 5: Knowledge graph'],
  },
  {
    rubro: 'BI y Analytics',
    icon: '📊',
    color: '#6366f1',
    onPremise: 'Data Warehouse. Reportes estáticos, cubos OLAP, ciclos largos de desarrollo.',
    cloud: 'Lakehouse + BI + AI. Dashboards real-time, ML integrado, self-service analytics, NLP queries.',
    aws: 'Redshift (DW), Athena (ad-hoc SQL), QuickSight (dashboards), SageMaker (ML), Bedrock (GenAI)',
    bnx: 'Multi-target codegen: Glue → Redshift, Athena queries sobre S3. Métricas de accuracy y cobertura.',
    maturity: ['Nivel 1: Reportes manuales', 'Nivel 2: BI estático', 'Nivel 3: Self-service BI', 'Nivel 4: ML integrado', 'Nivel 5: AI-driven insights'],
  },
  {
    rubro: 'Ciclo de Vida',
    icon: '♻️',
    color: '#06b6d4',
    onPremise: 'Largo. Cambios toman semanas/meses, releases trimestrales, testing manual extensivo.',
    cloud: 'Dinámico / automatizado. CI/CD, deploy en minutos, feature flags, rollback automático.',
    aws: 'CodePipeline, CodeBuild, Step Functions, Lambda, Amplify (CI/CD), CloudFormation/Terraform',
    bnx: 'Lambda deploy automático, Amplify CI/CD desde Git, Terraform IaC, versionamiento de designs',
    maturity: ['Nivel 1: Deploy manual', 'Nivel 2: Scripts de deploy', 'Nivel 3: CI/CD básico', 'Nivel 4: GitOps + IaC', 'Nivel 5: Continuous deployment'],
  },
  {
    rubro: 'Operaciones de Datos (DataOps)',
    icon: '⚙️',
    color: '#22c55e',
    onPremise: 'Reactivo. Monitoreo manual, alertas por email, troubleshooting con logs de texto.',
    cloud: 'Proactivo / predictivo. Observability, auto-scaling, self-healing, runbooks automatizados.',
    aws: 'CloudWatch (metrics/logs), X-Ray (tracing), SNS (alerts), Auto Scaling, Systems Manager',
    bnx: 'Accuracy engine como health check, validation antes de deploy, error detection en compilación',
    maturity: ['Nivel 1: Sin monitoreo', 'Nivel 2: Alertas básicas', 'Nivel 3: Observability', 'Nivel 4: Auto-remediation', 'Nivel 5: AIOps'],
  },
  {
    rubro: 'Privacidad y Compliance',
    icon: '⚖️',
    color: '#ef4444',
    onPremise: 'Manual. Cumplimiento por auditoría, controles periódicos, documentación estática.',
    cloud: 'Automatizado. Privacy by design, consent management, data retention automática, DSAR automation.',
    aws: 'Macie (PII), Config (compliance rules), Audit Manager, Lake Formation (row/column security)',
    bnx: 'Governance policies: LFPDPPP, CNBV R04/R08/R28, PLD/FT. Clasificación de datos (PII/Confidencial).',
    maturity: ['Nivel 1: Sin compliance', 'Nivel 2: Auditoría manual', 'Nivel 3: Controles automatizados', 'Nivel 4: Privacy by design', 'Nivel 5: Compliance continuo'],
  },
  {
    rubro: 'Data Literacy',
    icon: '📚',
    color: '#a855f7',
    onPremise: 'Limitada. Solo IT entiende los datos, business depende de reportes predefinidos.',
    cloud: 'Democratizada. Self-service, data catalogs accesibles, training programs, data champions.',
    aws: 'QuickSight (self-service BI), DataZone (data marketplace), SageMaker Canvas (no-code ML)',
    bnx: 'Designer visual (drag & drop), leyendas explicativas, Architecture page con glossario técnico',
    maturity: ['Nivel 1: Solo IT', 'Nivel 2: Reportes para business', 'Nivel 3: Self-service básico', 'Nivel 4: Data champions', 'Nivel 5: Data-driven culture'],
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
                {d.maturity && (
                  <div style={{
                    flex: '1 1 100%', padding: 12, borderRadius: 8,
                    background: (t.bg || '#0f1117') + '80', border: `1px solid ${t.border || '#334155'}30`,
                  }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: t.muted || '#94a3b8', marginBottom: 8 }}>📈 Niveles de Madurez</div>
                    <div style={{ display: 'flex', gap: 4 }}>
                      {d.maturity.map((level, li) => (
                        <div key={li} style={{
                          flex: 1, padding: '6px 8px', borderRadius: 6, fontSize: 11,
                          background: li <= 2 ? '#ef444415' : li <= 3 ? '#f59e0b15' : '#22c55e15',
                          border: `1px solid ${li <= 2 ? '#ef444430' : li <= 3 ? '#f59e0b30' : '#22c55e30'}`,
                          color: li <= 2 ? '#ef4444' : li <= 3 ? '#f59e0b' : '#22c55e',
                          textAlign: 'center', lineHeight: 1.4,
                        }}>{level}</div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
