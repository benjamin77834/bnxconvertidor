import { useState } from 'react'

const CAPABILITIES = [
  {
    area: 'Conversión Automática',
    icon: '🔄',
    color: '#1a73e8',
    what: 'Convierte pipelines de datos legacy (Ab Initio, COBOL) a código cloud (AWS Glue, PySpark) automáticamente.',
    value: 'Reduce el tiempo de migración de meses a días. Un pipeline de 80 nodos se convierte en minutos.',
    how: 'El usuario sube archivos .mp (grafo), .xfr (reglas), .dml (schema) y el sistema genera código ejecutable.',
  },
  {
    area: 'Multi-Output',
    icon: '📦',
    color: '#22c55e',
    what: 'De un solo grafo genera 5 artefactos: código Spark/Glue, orquestación (Step Functions + Airflow), e infraestructura (Terraform).',
    value: 'Elimina el trabajo manual de crear scripts, workflows e infraestructura por separado.',
    how: 'Un click genera todo lo necesario para deploy en AWS: código, orquestación e IaC.',
  },
  {
    area: 'Validación Inteligente',
    icon: '✅',
    color: '#f59e0b',
    what: 'Detecta errores en el pipeline antes de ejecutar: join keys inválidas, columnas faltantes, nodos huérfanos.',
    value: 'Evita fallos en producción. Cada error detectado en compilación ahorra horas de debugging en runtime.',
    how: 'El validador semántico propaga columnas por el DAG y verifica compatibilidad en cada nodo.',
  },
  {
    area: 'COBOL / Mainframe',
    icon: '🏦',
    color: '#a855f7',
    what: 'Parsea código COBOL legacy incluyendo EBCDIC y COMP-3 (packed decimal) y lo convierte a Spark.',
    value: 'Desbloquea la migración de mainframe sin reescribir manualmente miles de programas COBOL.',
    how: 'El parser lee FILE SECTION, PROCEDURE DIVISION, detecta encoding y genera grafos automáticamente.',
  },
  {
    area: 'Ab Initio Migration',
    icon: '📐',
    color: '#ef4444',
    what: 'Lee archivos nativos de Ab Initio: PLAN (orquestación), PSET (parámetros), XFR (transformaciones), DML (schema).',
    value: 'Migración directa de Ab Initio a AWS sin intermediarios. Compatible con LeapLogic pero open source.',
    how: 'Los 3 archivos se combinan: PLAN define estructura, PSET inyecta paths/conexiones, XFR define lógica.',
  },
  {
    area: 'Designer Visual',
    icon: '🎨',
    color: '#ec4899',
    what: 'Editor drag & drop para diseñar pipelines visualmente, similar al GDE de Ab Initio pero en web.',
    value: 'Permite a equipos no-técnicos diseñar pipelines y a técnicos editarlos rápidamente.',
    how: 'Agrega nodos, conecta edges, edita reglas por nodo, compila y descarga código — todo en el browser.',
  },
  {
    area: 'Gobierno de Datos',
    icon: '🏛️',
    color: '#06b6d4',
    what: 'Framework DAMA completo con 14 rubros, 55+ políticas, niveles de madurez y mapeo a servicios AWS.',
    value: 'Cumplimiento regulatorio (CNBV, Banxico, LFPDPPP) integrado en la herramienta de migración.',
    how: 'Políticas editables, exportables, con clasificación de datos y correspondencia On-Premise ↔ Cloud.',
  },
  {
    area: 'Serverless & Low Cost',
    icon: '☁️',
    color: '#ff9900',
    what: 'Desplegado en AWS Lambda + Amplify. Sin servidores, sin mantenimiento, auto-escalable.',
    value: 'Costo operativo de $5-20 USD/mes vs $500K+/año de licencia Ab Initio.',
    how: 'Frontend estático en Amplify, API en Lambda con Function URL, datos en S3.',
  },
]

const NUMBERS = [
  { value: '5', label: 'Outputs por grafo', desc: 'Glue, PySpark, Step Functions, Terraform, Airflow' },
  { value: '7', label: 'Tipos de nodo', desc: 'SOURCE, TRANSFORM, JOIN, DEDUP, NORMALIZE, LOOKUP, SINK' },
  { value: '3', label: 'Fuentes legacy', desc: 'Ab Initio (PLAN/PSET/XFR), COBOL (EBCDIC), Grafos (.mp)' },
  { value: '14', label: 'Rubros DAMA', desc: 'Gobierno, Arquitectura, Calidad, Seguridad, MDM, BI...' },
  { value: '100%', label: 'Accuracy', desc: 'Validación semántica antes de generar código' },
  { value: '$5', label: 'USD/mes', desc: 'Costo operativo en AWS (Lambda + S3)' },
]

export default function ExecutivePage({ theme }) {
  const t = theme || {}
  const [expanded, setExpanded] = useState(null)

  const exportPDF = () => {
    let r = 'BNX CONVERTIDOR — EXECUTIVE SUMMARY\n'
    r += '='.repeat(50) + '\n\n'
    r += 'PLATAFORMA PARA CONVERTIR O REFACTORIZAR GRAFOS LEGACY A CLOUD\n\n'
    CAPABILITIES.forEach(c => {
      r += `${c.icon} ${c.area}\n`
      r += `  Qué: ${c.what}\n`
      r += `  Valor: ${c.value}\n`
      r += `  Cómo: ${c.how}\n\n`
    })
    r += 'NÚMEROS CLAVE\n'
    NUMBERS.forEach(n => { r += `  ${n.value} — ${n.label}: ${n.desc}\n` })
    const blob = new Blob([r], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'bnx_executive_summary.txt'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div style={{ padding: 40, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 32 }}>

      {/* Hero */}
      <div style={{ textAlign: 'center', padding: '20px 0' }}>
        <div style={{ fontSize: 32, fontWeight: 700, color: t.text || '#e2e8f0' }}>
          🚀 BNX Convertidor
        </div>
        <div style={{ fontSize: 18, color: t.muted || '#94a3b8', marginTop: 8 }}>
          Plataforma para convertir o refactorizar grafos Legacy a Cloud
        </div>
        <div style={{ fontSize: 14, color: t.dim || '#64748b', marginTop: 8, maxWidth: 600, margin: '8px auto 0' }}>
          Convierte automáticamente pipelines de Ab Initio y COBOL a AWS Glue/PySpark,
          con validación semántica, gobierno de datos y deploy serverless.
        </div>
        <button onClick={exportPDF} style={{
          marginTop: 16, padding: '10px 24px', borderRadius: 8, fontSize: 14, cursor: 'pointer',
          background: (t.accent || '#1a73e8') + '20', border: `1px solid ${t.accent || '#1a73e8'}40`,
          color: t.accent || '#1a73e8', fontWeight: 600,
        }}>📥 Download Executive Summary</button>
      </div>

      {/* What is a data pipeline - simple diagram */}
      <div style={{
        borderRadius: 10, padding: 24,
        background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
      }}>
        <h3 style={{ fontSize: 18, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 8 }}>
          ¿Qué es un pipeline de datos?
        </h3>
        <p style={{ fontSize: 14, color: t.dim || '#64748b', marginBottom: 16 }}>
          Un banco procesa millones de transacciones diarias. Los datos viajan desde los sistemas origen
          hasta los reportes y aplicaciones que usan los ejecutivos, reguladores y clientes.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0, flexWrap: 'wrap', padding: '10px 0' }}>
          {[
            { icon: '🏦', label: 'Sistemas\nOrigen', desc: 'Core Banking\nTarjetas\nCOBOL/Mainframe', color: '#22c55e', phase: 'FASE 1' },
            { icon: '→', label: '', color: '#475569' },
            { icon: '🔄', label: 'ETL\n(Transformación)', desc: 'Limpiar\nValidar\nCombinar', color: '#22c55e', phase: 'FASE 1' },
            { icon: '→', label: '', color: '#475569' },
            { icon: '💾', label: 'Data Lake\n(Almacén)', desc: 'S3\nParquet\nOrganizado', color: '#a855f7', phase: 'FASE 2' },
            { icon: '→', label: '', color: '#475569' },
            { icon: '📊', label: 'Consumo\n(Reportes)', desc: 'Dashboards\nRegulatorio\nAPIs', color: '#ef4444', phase: 'FASE 3' },
          ].map((step, i) => (
            step.icon === '→' ? (
              <div key={i} style={{ fontSize: 24, color: t.dim || '#475569', padding: '0 8px' }}>→</div>
            ) : (
              <div key={i} style={{
                textAlign: 'center', padding: '12px 16px', borderRadius: 10,
                background: step.color + '12', border: `2px solid ${step.color}40`,
                minWidth: 120, position: 'relative',
              }}>
                <div style={{
                  position: 'absolute', top: -10, left: '50%', transform: 'translateX(-50%)',
                  padding: '1px 8px', borderRadius: 4, fontSize: 9, fontWeight: 700,
                  background: step.color, color: '#fff', whiteSpace: 'nowrap',
                }}>{step.phase}</div>
                <div style={{ fontSize: 28, marginTop: 4 }}>{step.icon}</div>
                <div style={{ fontSize: 13, fontWeight: 600, color: t.text || '#e2e8f0', whiteSpace: 'pre-line', marginTop: 4 }}>{step.label}</div>
                <div style={{ fontSize: 11, color: t.dim || '#64748b', whiteSpace: 'pre-line', marginTop: 4 }}>{step.desc}</div>
              </div>
            )
          ))}
        </div>

        <div style={{
          marginTop: 16, padding: 14, borderRadius: 8,
          background: (t.accent || '#1a73e8') + '10', border: `1px solid ${t.accent || '#1a73e8'}30`,
        }}>
          <div style={{ fontSize: 14, color: t.text || '#e2e8f0', lineHeight: 1.7 }}>
            <span style={{ fontWeight: 600, color: t.accent || '#1a73e8' }}>El problema:</span> Muchos bancos tienen estos pipelines en tecnología legacy
            (Ab Initio, COBOL) que corre en servidores propios costosos y difíciles de mantener.
          </div>
          <div style={{ fontSize: 14, color: t.text || '#e2e8f0', lineHeight: 1.7, marginTop: 8 }}>
            <span style={{ fontWeight: 600, color: '#22c55e' }}>La solución:</span> BNX Convertidor toma esos pipelines legacy y los convierte
            automáticamente a código cloud (AWS), reduciendo costos, tiempo y riesgo.
          </div>
        </div>

        <div style={{
          marginTop: 12, display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap',
        }}>
          {[
            { from: 'Ab Initio (legacy)', to: 'AWS Glue (cloud)', color: '#f59e0b' },
            { from: 'COBOL/Mainframe', to: 'PySpark', color: '#a855f7' },
            { from: 'Servidores propios', to: 'Serverless ($5/mes)', color: '#22c55e' },
          ].map((t2, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 8, padding: '8px 14px',
              borderRadius: 8, background: t2.color + '10', border: `1px solid ${t2.color}30`,
              fontSize: 13,
            }}>
              <span style={{ color: '#ef4444', textDecoration: 'line-through' }}>{t2.from}</span>
              <span style={{ color: t.dim || '#64748b' }}>→</span>
              <span style={{ color: '#22c55e', fontWeight: 600 }}>{t2.to}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Numbers */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
        {NUMBERS.map(n => (
          <div key={n.label} style={{
            flex: '1 1 140px', maxWidth: 180, padding: 16, borderRadius: 10, textAlign: 'center',
            background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
          }}>
            <div style={{ fontSize: 32, fontWeight: 700, color: t.accent || '#1a73e8' }}>{n.value}</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: t.text || '#e2e8f0', marginTop: 4 }}>{n.label}</div>
            <div style={{ fontSize: 11, color: t.dim || '#64748b', marginTop: 2 }}>{n.desc}</div>
          </div>
        ))}
      </div>

      {/* Capabilities */}
      <div>
        <h3 style={{ fontSize: 20, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 16, textAlign: 'center' }}>
          Capacidades
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {CAPABILITIES.map((c, i) => (
            <div key={c.area} style={{
              borderRadius: 10, overflow: 'hidden',
              background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
            }}>
              <div
                onClick={() => setExpanded(expanded === i ? null : i)}
                style={{
                  padding: '16px 20px', cursor: 'pointer',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{
                    width: 40, height: 40, borderRadius: 10,
                    background: c.color + '20', border: `1px solid ${c.color}40`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20,
                  }}>{c.icon}</span>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0' }}>{c.area}</div>
                    <div style={{ fontSize: 13, color: t.muted || '#94a3b8', marginTop: 2 }}>{c.what}</div>
                  </div>
                </div>
                <span style={{ fontSize: 14, color: t.dim || '#64748b' }}>{expanded === i ? '▼' : '▶'}</span>
              </div>

              {expanded === i && (
                <div style={{
                  padding: '0 20px 16px', display: 'flex', gap: 12, flexWrap: 'wrap',
                }}>
                  <div style={{
                    flex: '1 1 250px', padding: 14, borderRadius: 8,
                    background: '#22c55e10', border: '1px solid #22c55e30',
                  }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#22c55e', marginBottom: 4 }}>💰 Valor de Negocio</div>
                    <div style={{ fontSize: 14, color: t.muted || '#94a3b8', lineHeight: 1.6 }}>{c.value}</div>
                  </div>
                  <div style={{
                    flex: '1 1 250px', padding: 14, borderRadius: 8,
                    background: (t.accent || '#1a73e8') + '10', border: `1px solid ${t.accent || '#1a73e8'}30`,
                  }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: t.accent || '#1a73e8', marginBottom: 4 }}>⚙️ Cómo Funciona</div>
                    <div style={{ fontSize: 14, color: t.muted || '#94a3b8', lineHeight: 1.6 }}>{c.how}</div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Comparison */}
      <div style={{
        borderRadius: 10, padding: 24,
        background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
      }}>
        <h3 style={{ fontSize: 18, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 16 }}>
          ¿Por qué BNX vs alternativas?
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr 1fr', gap: 2, fontSize: 13 }}>
          {[
            ['', 'Manual', 'Ab Initio Cloud', 'SaaS Migration Tools', 'BNX'],
            ['Tiempo 40K jobs', '~45 meses', '~15 meses', '~10 meses', '~5 meses'],
            ['Equipo', '10 devs', '8 devs certificados', '5 devs + vendor', '3 devs'],
            ['Costo licencia', '$0', '$500K-2M/año', '$100-300/job', '$0 (open source)'],
            ['Costo operativo', '$200-500/mes', '$50K+/mes (EKS)', 'SaaS fee mensual', '$5-20/mes'],
            ['Multi-output', 'No', 'No', 'Parcial (1-2)', '5 formatos'],
            ['Validación', 'Manual', 'Parcial', 'Básica', 'Semántica completa'],
            ['Gobierno datos', 'Externo', 'No', 'No', 'Integrado (DAMA)'],
            ['COBOL support', 'Manual', 'No', 'Parcial', 'Automático (EBCDIC)'],
            ['Designer visual', 'No', 'No', 'No', 'Drag & drop web'],
            ['Multi-cloud', 'N/A', 'No', 'Sí', 'AWS (extensible)'],
            ['Vendor lock-in', 'No', 'Total', 'Alto', 'Bajo (open source)'],
          ].map((row, ri) => (
            row.map((cell, ci) => (
              <div key={`${ri}-${ci}`} style={{
                padding: '8px 12px',
                background: ri === 0 ? (t.bg || '#0f1117') : 'transparent',
                fontWeight: ri === 0 || ci === 0 ? 600 : 400,
                color: ri === 0 ? (t.muted || '#94a3b8')
                     : ci === 4 ? '#22c55e'
                     : ci === 3 ? '#f59e0b'
                     : ci === 0 ? (t.text || '#e2e8f0')
                     : (t.muted || '#94a3b8'),
                borderBottom: `1px solid ${t.border || '#334155'}20`,
              }}>{cell}</div>
            ))
          ))}
        </div>
      </div>
    </div>
  )
}
