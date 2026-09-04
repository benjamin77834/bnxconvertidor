import { useState } from 'react'

const ROADMAP_DATA = {
  mes1: {
    title: 'Mes 1 - Estabilizacion + Code Quality',
    color: '#6366f1',
    weeks: [
      {
        label: 'Semana 1-2: Parser GDE Nativo',
        tasks: [
          { task: 'Completar parser formato serializado Ab Initio (.mp nativo GDE)', status: 'done' },
          { task: 'Resolver mapeo de edges (ports -> flows -> vertices)', status: 'done' },
          { task: 'Validar con 3+ grafos reales del banco (barrido 36 grafos, 35/36 ok)', status: 'done' },
          { task: 'Generar job.py con edges correctos y DAG completo', status: 'done' },
          { task: 'Documentar limitaciones del parser (bajo-mediano ok, >100 nodos pendiente)', status: 'in-progress' },
        ],
      },
      {
        label: 'Semana 2-3: SonarQube Compliance',
        tasks: [
          { task: 'Configurar SonarQube scanner en el proyecto', status: 'pending' },
          { task: 'Crear sonar-project.properties', status: 'pending' },
          { task: 'Resolver issues Critical/Blocker', status: 'pending' },
          { task: 'Eliminar code smells (duplicacion, complejidad)', status: 'pending' },
          { task: 'Cobertura de tests minima 60%', status: 'pending' },
          { task: 'Quality gates: 0 bugs, 0 vulnerabilities', status: 'pending' },
        ],
      },
      {
        label: 'Semana 3-4: Testing Formal',
        tasks: [
          { task: 'Unit tests para cada parser (mp, xfr, dml, pset, plan, cobol)', status: 'pending' },
          { task: 'Unit tests para cada codegen (glue, spark, flink, airflow)', status: 'pending' },
          { task: 'Integration tests: .mp real -> job.py -> ejecucion + equivalencia de datos vs referencia', status: 'done' },
          { task: 'Test con grafos del banco (barrido 36 grafos, 35/36 ok)', status: 'done' },
          { task: 'Documentar casos de prueba en formato banco', status: 'pending' },
          { task: 'Configurar pytest + coverage report (formalizar el barrido)', status: 'in-progress' },
        ],
      },
    ],
  },
  mes2: {
    title: 'Mes 2 - Seguridad + SDLC Bancario',
    color: '#f59e0b',
    weeks: [
      {
        label: 'Semana 5-6: Seguridad (SAST/DAST)',
        tasks: [
          { task: 'SAST scan (Checkmarx/Fortify/SonarQube Security)', status: 'pending' },
          { task: 'Remediar vulnerabilidades encontradas', status: 'pending' },
          { task: 'Validar no secrets hardcodeados', status: 'done' },
          { task: 'Input validation en todos los parsers', status: 'pending' },
          { task: 'Dependency check (pip audit) - sin CVEs', status: 'pending' },
          { task: 'Documentar threat model basico', status: 'pending' },
        ],
      },
      {
        label: 'Semana 6-7: Documentacion SDLC',
        tasks: [
          { task: 'Documento de Arquitectura (SAD) - formato banco', status: 'pending' },
          { task: 'Diagrama de componentes', status: 'done' },
          { task: 'Diagrama de flujo de datos (DFD)', status: 'pending' },
          { task: 'Runbook operativo', status: 'pending' },
          { task: 'Documento de Rollback', status: 'pending' },
          { task: 'Matriz de riesgos', status: 'pending' },
        ],
      },
      {
        label: 'Semana 7-8: CI/CD Pipeline Bancario',
        tasks: [
          { task: 'Pipeline en herramienta del banco (Jenkins/GitLab CI)', status: 'pending' },
          { task: 'Stages: lint -> test -> sonar -> security -> build -> deploy', status: 'pending' },
          { task: 'Artefacto versionado (tag + changelog)', status: 'pending' },
          { task: 'Deploy a DEV automatico, QA con aprobacion', status: 'pending' },
          { task: 'Branch protection (no push directo a main)', status: 'pending' },
        ],
      },
    ],
  },
  mes3: {
    title: 'Mes 3 - QA + CAB + Produccion',
    color: '#22c55e',
    weeks: [
      {
        label: 'Semana 9-10: QA Formal',
        tasks: [
          { task: 'Pruebas en ambiente QA del banco', status: 'pending' },
          { task: 'Pruebas de regresion con grafos reales', status: 'pending' },
          { task: 'Pruebas de performance (40K jobs)', status: 'pending' },
          { task: 'Pruebas de stress (archivos .mp >10K lineas)', status: 'pending' },
          { task: 'UAT con equipo de datos', status: 'pending' },
          { task: 'Sign-off de QA', status: 'pending' },
        ],
      },
      {
        label: 'Semana 10-11: CAB (Change Advisory Board)',
        tasks: [
          { task: 'RFC (Request for Change) documentado', status: 'pending' },
          { task: 'Impacto analisis + Plan de implementacion', status: 'pending' },
          { task: 'Plan de rollback', status: 'pending' },
          { task: 'Ventana de cambio aprobada', status: 'pending' },
          { task: 'Comunicacion a stakeholders', status: 'pending' },
        ],
      },
      {
        label: 'Semana 11-12: Deploy Produccion',
        tasks: [
          { task: 'Deploy a PROD (Lambda + Amplify)', status: 'pending' },
          { task: 'Smoke tests post-deploy', status: 'pending' },
          { task: 'Monitoreo CloudWatch + Alertas SNS', status: 'pending' },
          { task: 'Handover a equipo de operaciones', status: 'pending' },
          { task: 'Documentacion soporte L1/L2/L3', status: 'pending' },
          { task: 'Retrospectiva y plan de mejora continua', status: 'pending' },
        ],
      },
    ],
  },
}

const RISKS = [
  { risk: 'Parser GDE no cubre todos los formatos', mitigation: 'Validar con multiples .mp reales, iterar', level: 'high' },
  { risk: 'SonarQube quality gate muy estricto', mitigation: 'Negociar excepciones documentadas', level: 'medium' },
  { risk: 'Tiempos de aprobacion CAB largos', mitigation: 'Iniciar RFC en semana 8, no esperar', level: 'medium' },
  { risk: 'Grafos muy complejos (>100 nodos)', mitigation: 'Tests de stress, optimizar parser', level: 'low' },
  { risk: 'Dependencia de acceso al servidor', mitigation: 'Mantener package.sh actualizado', level: 'low' },
  { risk: 'Equipo no familiarizado con Spark', mitigation: 'Sesion de capacitacion en UAT', level: 'medium' },
]

const CURRENT_EFFORTS = [
  { task: 'Parser GDE nativo (formato serializado)', status: 'done', impact: 'Ya parsea .mp reales del banco' },
  { task: 'Data Redactada (datos sinteticos + PII masking)', status: 'done', impact: 'Probar sin datos reales del banco' },
  { task: 'Ejecutor de prueba PySpark local', status: 'done', impact: 'Valida el codigo ejecutandolo, no solo leyendolo' },
  { task: 'Correccion masiva del generador (barrido 36 grafos)', status: 'done', impact: '35/36 grafos ejecutan y producen salidas' },
  { task: 'Optimizador de performance (reglas, sin IA)', status: 'done', impact: 'cache/broadcast/coalesce + benchmark' },
  { task: 'Fix Windows: encoding utf-8 (UnicodeDecodeError 0x97 en Compiler/Data Redactada)', status: 'done', impact: 'Funciona igual en Windows que en Mac/Linux' },
  { task: 'Prueba mas rapida (local[*], shuffle=8) + timeout configurable', status: 'done', impact: 'Menos timeouts en grafos grandes' },
  { task: 'Despliegue EC2 (Spark local) + CloudFront HTTPS', status: 'done', impact: 'Prueba PySpark en la nube igual que en local' },
  { task: 'Boton EC2 interno (DataLab) + runbook, y Probar local', status: 'done', impact: 'Preparado para la cuenta correcta; pendiente permisos DataLab' },
  { task: 'Correctitud del generador (fecha :, let/lookup, Create_Data) + accuracy honesto', status: 'done', impact: 'S655690 de 69% a 98.6%; el score ya no subvalora el DML embebido' },
  { task: 'Validacion de equivalencia de datos (generado vs referencia)', status: 'done', impact: 'Prueba correctitud semantica: esquema+conteo+contenido, no solo que compile' },
  { task: 'Package 7z para transferencia', status: 'done', impact: 'Mover codigo a servidor seguro' },
]

// Estatus de conversion por complejidad de grafo. Honesto: bajo/medio validado,
// alto pendiente (los 3 grafos mas grandes estan en bnx_library/ERROR/).
const COMPLEXITY_STATUS = [
  {
    level: 'Baja',
    range: 'hasta ~15 componentes / ~10 flujos',
    detail: 'Read/Reformat/Filter/Join/Rollup/Write estandar. Convierte y ejecuta de punta a punta. Correctitud verificable con /validate (equivalencia de datos vs referencia).',
    status: 'done', pct: '100%', color: '#22c55e',
  },
  {
    level: 'Media',
    range: '~15 a ~50 componentes / hasta ~46 flujos',
    detail: 'Lookups, dedup, multi-join, XFR/DML moderado. Cubierto por el barrido (35/36), accuracy 96-100%. Correctitud validable por equivalencia de datos (esquema+conteo+contenido). Degradaciones puntuales: lookup a NULL cuando la tabla no esta conectada, TODO en DML con loops.',
    status: 'done', pct: '~95%', color: '#22c55e',
  },
  {
    level: 'Alta',
    range: '100+ componentes / 70+ flujos, DML con loops-vectores',
    detail: 'NO validado. Falta: Concatenate/Gather/Partition reales (hoy passthrough), DML con loops/vectores (hoy TODO/UDF manual), join keys en grafos densos. Los 3 grafos mas grandes estan apartados en bnx_library/ERROR/.',
    status: 'pending', pct: 'pendiente', color: '#ef4444',
  },
]

// Resumen honesto de lo que FALTA. Agrupado por area, con prioridad, para que
// quede claro que sigue pendiente sin tener que expandir todo el timeline.
const PENDIENTES = [
  {
    area: 'Conversion (grafos altos)',
    priority: 'alta',
    items: [
      'Concatenate/Gather/Partition reales (hoy caen a passthrough)',
      'DML con loops/vectores (hoy TODO/UDF manual)',
      'Resolucion robusta de join keys en grafos densos',
      'Resolver lookup como join real cuando la tabla esta conectada',
      'Validar los 3 grafos mas grandes (apartados en bnx_library/ERROR/)',
    ],
  },
  {
    area: 'Testing / correctitud',
    priority: 'alta',
    items: [
      'Formalizar el barrido de 36 grafos como suite pytest (cobertura >=60%)',
      'Unit tests por parser (mp, xfr, dml, pset, plan, cobol) y por codegen',
      'Exportar salidas reales de Ab Initio como golden data (validar contra produccion, no solo referencia sintetica)',
    ],
  },
  {
    area: 'Seguridad (SAST/DAST)',
    priority: 'media',
    items: [
      'SAST scan (Checkmarx/Fortify/SonarQube Security) + remediacion',
      'Input validation en todos los parsers',
      'Dependency check (pip audit) sin CVEs',
      'Threat model basico documentado',
    ],
  },
  {
    area: 'Code quality (SonarQube)',
    priority: 'media',
    items: [
      'Configurar scanner + sonar-project.properties',
      'Quality gate: 0 Critical, 0 Blocker, 0 vulnerabilities',
      'Reducir code smells (duplicacion, complejidad)',
    ],
  },
  {
    area: 'SDLC bancario / documentacion',
    priority: 'media',
    items: [
      'SAD (arquitectura) + DFD (flujo de datos) formato banco',
      'Runbook operativo + plan de rollback + matriz de riesgos',
      'Pipeline CI/CD del banco (lint -> test -> sonar -> security -> build -> deploy)',
    ],
  },
  {
    area: 'QA + CAB + Produccion',
    priority: 'baja',
    items: [
      'QA formal + pruebas de regresion/performance/stress + UAT + sign-off',
      'RFC + CAB (Change Advisory Board) + ventana de cambio',
      'Deploy PROD + smoke tests + monitoreo CloudWatch/SNS + handover L1/L2/L3',
    ],
  },
  {
    area: 'Infraestructura',
    priority: 'baja',
    items: [
      'EC2 en DataLab (cuenta correcta): pendiente IAM role + accesos del equipo DataLab',
    ],
  },
]

// Construye un documento HTML COMPLETO (texto real, no screenshot) con todo el
// plan de 3 meses: lo hecho y lo que falta. Se abre en una ventana e imprime a
// PDF. No depende del estado colapsado de la UI ni de librerias externas.
function buildPlanHTML() {
  const esc = (s) => String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const mark = (st) => st === 'done' ? '[x]' : st === 'in-progress' ? '[~]' : '[ ]'
  const now = new Date().toLocaleString()

  let h = ''
  h += `<h1>BNX Convertidor — Plan de Trabajo 3 Meses</h1>`
  h += `<p class="sub">SDLC Bancario + SonarQube + Produccion · Generado: ${esc(now)}</p>`

  // Estatus por complejidad
  h += `<h2>Estatus del convertidor por complejidad de grafo</h2>`
  h += `<table><thead><tr><th>Complejidad</th><th>Rango</th><th>%</th><th>Detalle</th></tr></thead><tbody>`
  for (const c of COMPLEXITY_STATUS) {
    h += `<tr><td><b>${esc(c.level)}</b></td><td>${esc(c.range)}</td><td>${esc(c.pct)}</td><td>${esc(c.detail)}</td></tr>`
  }
  h += `</tbody></table>`

  // Esfuerzos actuales (lo hecho)
  h += `<h2>Esfuerzos actuales (hecho / en curso)</h2><ul class="tasks">`
  for (const e of CURRENT_EFFORTS) {
    h += `<li><span class="m">${mark(e.status)}</span> ${esc(e.task)} <span class="imp">— ${esc(e.impact)}</span></li>`
  }
  h += `</ul>`

  // Plan mes a mes (todo, sin colapsar) — lo hecho y lo que falta
  for (const [, mes] of Object.entries(ROADMAP_DATA)) {
    h += `<h2>${esc(mes.title)}</h2>`
    for (const wk of mes.weeks) {
      const done = wk.tasks.filter(x => x.status === 'done').length
      h += `<h3>${esc(wk.label)} <span class="pct">(${done}/${wk.tasks.length})</span></h3><ul class="tasks">`
      for (const task of wk.tasks) {
        const cls = task.status === 'done' ? 'done' : task.status === 'in-progress' ? 'prog' : 'pend'
        h += `<li class="${cls}"><span class="m">${mark(task.status)}</span> ${esc(task.task)}</li>`
      }
      h += `</ul>`
    }
  }

  // Resumen de faltantes
  h += `<h2>Resumen de faltantes</h2>`
  for (const p of PENDIENTES) {
    h += `<h3>${esc(p.area)} <span class="prio ${esc(p.priority)}">${esc(p.priority).toUpperCase()}</span></h3><ul class="tasks">`
    for (const it of p.items) h += `<li class="pend"><span class="m">[ ]</span> ${esc(it)}</li>`
    h += `</ul>`
  }

  // Riesgos
  h += `<h2>Riesgos</h2><table><thead><tr><th>Nivel</th><th>Riesgo</th><th>Mitigacion</th></tr></thead><tbody>`
  for (const r of RISKS) {
    h += `<tr><td>${esc(r.level).toUpperCase()}</td><td>${esc(r.risk)}</td><td>${esc(r.mitigation)}</td></tr>`
  }
  h += `</tbody></table>`

  const styles = `
    * { box-sizing: border-box; }
    body { font-family: -apple-system, Segoe UI, Arial, sans-serif; color: #111; margin: 24px; font-size: 12px; line-height: 1.5; }
    h1 { font-size: 20px; margin: 0 0 2px; }
    h2 { font-size: 15px; margin: 20px 0 8px; border-bottom: 2px solid #333; padding-bottom: 3px; break-after: avoid; }
    h3 { font-size: 13px; margin: 12px 0 4px; color: #222; break-after: avoid; }
    .sub { color: #666; margin: 0 0 8px; font-size: 11px; }
    .pct { color: #666; font-weight: normal; font-size: 11px; }
    table { width: 100%; border-collapse: collapse; margin: 6px 0; }
    th, td { border: 1px solid #bbb; padding: 5px 7px; text-align: left; vertical-align: top; font-size: 11px; }
    th { background: #eee; }
    ul.tasks { list-style: none; padding-left: 4px; margin: 4px 0; }
    ul.tasks li { margin: 2px 0; page-break-inside: avoid; }
    .m { font-family: monospace; font-weight: bold; }
    li.done .m { color: #15803d; }
    li.prog .m { color: #b45309; }
    li.pend .m { color: #b91c1c; }
    li.done { color: #15803d; }
    .imp { color: #666; }
    .prio { font-size: 10px; padding: 1px 6px; border-radius: 3px; border: 1px solid; }
    .prio.alta { color: #b91c1c; border-color: #b91c1c; }
    .prio.media { color: #b45309; border-color: #b45309; }
    .prio.baja { color: #15803d; border-color: #15803d; }
    @page { margin: 14mm; }
  `
  return `<!doctype html><html><head><meta charset="utf-8"><title>BNX — Plan 3 Meses</title><style>${styles}</style></head><body>${h}</body></html>`
}

function exportPlanPDF() {
  const html = buildPlanHTML()
  const w = window.open('', '_blank')
  if (!w) {
    alert('El navegador bloqueo la ventana. Permite pop-ups para exportar el PDF.')
    return
  }
  w.document.open()
  w.document.write(html)
  w.document.close()
  // Esperar a que renderice antes de lanzar el dialogo de impresion.
  w.onload = () => { w.focus(); w.print() }
  // Fallback por si onload no dispara (documento ya cargado).
  setTimeout(() => { try { w.focus(); w.print() } catch (e) {} }, 400)
}

export default function RoadmapPage({ theme }) {
  const t = theme || {}
  const [expandedMes, setExpandedMes] = useState('mes1')

  const card = {
    background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 20,
  }

  const statusIcon = (s) => s === 'done' ? '[ok]' : s === 'in-progress' ? '[>>]' : '[ ]'
  const statusColor = (s) => s === 'done' ? '#22c55e' : s === 'in-progress' ? '#f59e0b' : t.dim || '#64748b'

  return (
    <div style={{ padding: 32, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: t.text || '#e2e8f0', margin: 0 }}>
            Roadmap - Plan de Trabajo 3 Meses
          </h2>
          <p style={{ fontSize: 14, color: t.dim || '#64748b', marginTop: 4 }}>
            SDLC Bancario + SonarQube + Produccion
          </p>
        </div>
        <button onClick={exportPlanPDF} className="no-print" style={{
          padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13, whiteSpace: 'nowrap',
          background: (t.accent || '#6366f1') + '20', border: `1px solid ${t.accent || '#6366f1'}40`,
          color: t.accent || '#6366f1', fontWeight: 600,
        }}>📄 Exportar PDF</button>
      </div>

      {/* Estatus del convertidor por complejidad */}
      <div style={card}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 4 }}>
          Estatus del convertidor por complejidad de grafo
        </h3>
        <p style={{ fontSize: 12, color: t.dim || '#64748b', marginBottom: 14 }}>
          Validado ejecutando el PySpark con datos redactados (barrido de 36 grafos: 35/36 ok).
        </p>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {COMPLEXITY_STATUS.map((c, i) => (
            <div key={i} style={{
              flex: '1 1 240px', minWidth: 240,
              background: t.bg || '#0f1117', borderRadius: 10, padding: 14,
              border: `1px solid ${c.color}55`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: 16, fontWeight: 700, color: c.color }}>{c.level}</span>
                <span style={{
                  fontSize: 12, fontWeight: 700, color: c.color,
                  background: `${c.color}22`, borderRadius: 6, padding: '2px 8px',
                }}>{c.pct}</span>
              </div>
              <div style={{ fontSize: 11, color: t.muted || '#94a3b8', fontStyle: 'italic', marginBottom: 6 }}>
                {c.range}
              </div>
              <div style={{ fontSize: 12, color: t.text || '#e2e8f0', lineHeight: 1.5 }}>
                {c.detail}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Current Efforts */}
      <div style={card}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 12 }}>
          Esfuerzos Actuales
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {CURRENT_EFFORTS.map((e, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
              <span style={{ color: statusColor(e.status), fontWeight: 700, fontFamily: 'monospace', width: 36 }}>
                {statusIcon(e.status)}
              </span>
              <span style={{ color: t.text || '#e2e8f0', flex: 1 }}>{e.task}</span>
              <span style={{ color: t.dim || '#64748b', fontSize: 11 }}>{e.impact}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Resumen de faltantes */}
      <div style={card}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 4 }}>
          Resumen de faltantes
        </h3>
        <p style={{ fontSize: 12, color: t.dim || '#64748b', marginBottom: 14 }}>
          Lo que aun no esta hecho, agrupado por area y prioridad. Honesto: el convertidor cubre bajo/medio; falta lo de abajo para produccion bancaria.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {PENDIENTES.map((p, i) => {
            const pc = p.priority === 'alta' ? '#ef4444' : p.priority === 'media' ? '#f59e0b' : '#22c55e'
            return (
              <div key={i} style={{
                background: t.bg || '#0f1117', borderRadius: 10, padding: 14,
                border: `1px solid ${pc}44`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: t.text || '#e2e8f0' }}>{p.area}</span>
                  <span style={{
                    fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 4,
                    color: pc, background: `${pc}22`, textTransform: 'uppercase',
                  }}>{p.priority}</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, paddingLeft: 4 }}>
                  {p.items.map((it, j) => (
                    <div key={j} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 12 }}>
                      <span style={{ color: pc, fontFamily: 'monospace', fontWeight: 700 }}>[ ]</span>
                      <span style={{ color: t.muted || '#94a3b8', lineHeight: 1.5 }}>{it}</span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Timeline */}
      {Object.entries(ROADMAP_DATA).map(([mesKey, mes]) => (
        <div key={mesKey} style={{ ...card, borderLeft: `4px solid ${mes.color}` }}>
          <div
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
            onClick={() => setExpandedMes(expandedMes === mesKey ? null : mesKey)}
          >
            <h3 style={{ fontSize: 16, fontWeight: 600, color: mes.color, margin: 0 }}>
              {mes.title}
            </h3>
            <span style={{ color: t.dim || '#64748b', fontSize: 18 }}>
              {expandedMes === mesKey ? '-' : '+'}
            </span>
          </div>

          {expandedMes === mesKey && (
            <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
              {mes.weeks.map((week, wi) => {
                const done = week.tasks.filter(t => t.status === 'done').length
                const total = week.tasks.length
                const pct = Math.round((done / total) * 100)
                return (
                  <div key={wi}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 600, color: t.text || '#e2e8f0' }}>{week.label}</span>
                      <span style={{ fontSize: 12, color: mes.color, fontWeight: 600 }}>{pct}%</span>
                    </div>
                    {/* Progress bar */}
                    <div style={{ height: 4, background: (t.bg || '#0a1628'), borderRadius: 2, marginBottom: 10 }}>
                      <div style={{ height: '100%', width: `${pct}%`, background: mes.color, borderRadius: 2 }} />
                    </div>
                    {/* Tasks */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, paddingLeft: 8 }}>
                      {week.tasks.map((task, ti) => (
                        <div key={ti} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                          <span style={{ color: statusColor(task.status), fontFamily: 'monospace', fontWeight: 700 }}>
                            {statusIcon(task.status)}
                          </span>
                          <span style={{ color: task.status === 'done' ? '#22c55e' : (t.muted || '#94a3b8') }}>
                            {task.task}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      ))}

      {/* Risks */}
      <div style={card}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 12 }}>
          Riesgos
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {RISKS.map((r, i) => (
            <div key={i} style={{
              display: 'flex', gap: 12, padding: '8px 12px', borderRadius: 6,
              background: r.level === 'high' ? '#ef444410' : r.level === 'medium' ? '#f59e0b10' : '#22c55e10',
              border: `1px solid ${r.level === 'high' ? '#ef444430' : r.level === 'medium' ? '#f59e0b30' : '#22c55e30'}`,
            }}>
              <span style={{
                fontSize: 11, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
                color: r.level === 'high' ? '#ef4444' : r.level === 'medium' ? '#f59e0b' : '#22c55e',
                background: r.level === 'high' ? '#ef444420' : r.level === 'medium' ? '#f59e0b20' : '#22c55e20',
              }}>
                {r.level.toUpperCase()}
              </span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, color: t.text || '#e2e8f0', fontWeight: 500 }}>{r.risk}</div>
                <div style={{ fontSize: 11, color: t.dim || '#64748b', marginTop: 2 }}>{r.mitigation}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Success Metrics */}
      <div style={card}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 12 }}>
          Metricas de Exito
        </h3>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {[
            { label: 'SonarQube', value: '0 Critical', sub: '0 Blocker, Coverage >60%', color: '#6366f1' },
            { label: 'Parser', value: '90%+', sub: 'Grafos parseados correctamente', color: '#22c55e' },
            { label: 'Codegen', value: 'Ejecutable', sub: 'Output en Glue sin modificacion', color: '#f59e0b' },
            { label: 'Performance', value: '<30s', sub: 'Parse + gen grafo 100 nodos', color: '#06b6d4' },
            { label: 'Disponibilidad', value: '99.9%', sub: 'Lambda + Amplify PROD', color: '#22c55e' },
          ].map(m => (
            <div key={m.label} style={{
              flex: '1 1 140px', padding: 12, borderRadius: 8, textAlign: 'center',
              background: m.color + '10', border: `1px solid ${m.color}30`,
            }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: m.color }}>{m.value}</div>
              <div style={{ fontSize: 12, fontWeight: 600, color: t.text || '#e2e8f0', marginTop: 4 }}>{m.label}</div>
              <div style={{ fontSize: 11, color: t.dim || '#64748b', marginTop: 2 }}>{m.sub}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
