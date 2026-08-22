import { useState } from 'react'

const TIMELINE = [
  {
    date: '20 Mar 2026',
    title: 'Dia 1: Fundacion del proyecto',
    desc: 'Creamos el repositorio con el motor de migracion ETL v7. Parsers basicos para .mp y .xfr, generadores de codigo para Glue y Spark. Estructura modular en src/.',
    tags: ['setup', 'parsers', 'codegen'],
    color: '#6366f1',
  },
  {
    date: '23 Mar 2026',
    title: 'Dia 2: Documentacion y ramas',
    desc: 'Actualizamos README con instrucciones de uso. Creamos ramas empresav2 y empresav3 para iterar las demos.',
    tags: ['docs', 'git'],
    color: '#64748b',
  },
  {
    date: '26 Mar 2026',
    title: 'Dia 3: Gran reestructura + UI React',
    desc: 'Creamos la interfaz grafica (React + Vite + ReactFlow), el server FastAPI, limpieza masiva del codigo, DAG Builder con topological sort, validador semantico, motor de accuracy. Grafos de prueba: monster, advanced, small. Lambda handler + Amplify.',
    tags: ['ui', 'api', 'dag', 'refactor'],
    color: '#22c55e',
  },
  {
    date: '27 Mar 2026',
    title: 'Dia 4: Deploy a AWS',
    desc: 'Primer deploy a produccion: Lambda con lambda_package.zip + Lambda URL. Grafo de prueba complejo con DML. Mejoras al DagViewer y validador.',
    tags: ['deploy', 'lambda', 'aws'],
    color: '#f59e0b',
  },
  {
    date: '28 Mar 2026',
    title: 'Dia 5: Parser COBOL + Metricas',
    desc: 'Parser de COBOL: .cbl se convierte a .mp + .xfr + .dml automaticamente. Archivo COBOL bancario de ejemplo. Pagina de Metricas con estimaciones de costos.',
    tags: ['cobol', 'parser', 'metrics'],
    color: '#a855f7',
  },
  {
    date: '31 Mar 2026',
    title: 'Dia 7: Designer + Banking + Governance',
    desc: 'Editor visual drag-and-drop (Designer Page), Modelo operativo bancario (Banking), Gobierno de datos basado en DAMA (Governance). COBOL EBCDIC y tarjeta de credito.',
    tags: ['ui', 'designer', 'banking', 'governance'],
    color: '#ec4899',
  },
  {
    date: '5 Abr 2026',
    title: 'Dia 9: Pagina de Arquitectura',
    desc: 'ArchitecturePage con diagrama interactivo del sistema y glosario de componentes tecnicos.',
    tags: ['ui', 'architecture'],
    color: '#06b6d4',
  },
  {
    date: '7 Abr 2026',
    title: 'Dia 11: Parser de PLANs Ab Initio',
    desc: 'plan_parser.py para PLAN/PSET de Ab Initio. Grafo de Grafos: multiples grafos con dependencias. Ejemplos: sample_banking.plan (22 grafos) y credit_card.plan. PySpark generado desde planes.',
    tags: ['parser', 'plan', 'mega-dag'],
    color: '#22c55e',
  },
  {
    date: '9 Abr 2026',
    title: 'Dia 13: Pagina Ejecutiva',
    desc: 'ExecutivePage con resumen C-level: pipeline F1/F2/F3, comparativa de tecnologias, KPIs ejecutivos.',
    tags: ['ui', 'executive'],
    color: '#f59e0b',
  },
  {
    date: '14 Abr 2026',
    title: 'Dias 14-15: Flink + Planes Ciclicos',
    desc: 'Generador Apache Flink (PyFlink + Flink SQL). Planes ciclicos con MAX_ITERATIONS y CONVERGENCE. Glosario de 11 tipos de nodo.',
    tags: ['flink', 'codegen', 'cyclic'],
    color: '#6366f1',
  },
  {
    date: '17 Abr 2026',
    title: 'Dia 16: Motor de Refactorizacion',
    desc: 'refactor_engine.py: migra Spark 2 a 3, Python 2 a 3, Glue 2 a 4 automaticamente. Integracion con UI y API. README reescrito.',
    tags: ['refactor', 'engine'],
    color: '#ef4444',
  },
  {
    date: '22 Abr 2026',
    title: 'Dia 17: Admin Mode + Downloads',
    desc: 'Modo admin con password en Architecture (muestra codigo fuente). Endpoint de descarga ZIP (backend/frontend/all con scripts de instalacion).',
    tags: ['admin', 'downloads'],
    color: '#64748b',
  },
  {
    date: '23 Abr 2026',
    title: 'Dia 18: Formato nativo Ab Initio (GDE)',
    desc: 'Parser GDE para formato serializado real del banco (XXGpvertex/XXGedge). Grafo monster de 45 nodos nativo. Editor multi-tab con syntax highlighting. PSET nativo (KEY||||VALUE + PDL).',
    tags: ['parser', 'gde', 'native'],
    color: '#22c55e',
  },
  {
    date: '4 May 2026',
    title: 'Dia 20: Filtro de fechas',
    desc: 'Filtro scan_date (scan_year/scan_month/partition_filter). Mapeo de funciones de fecha Ab Initio a PySpark equivalentes.',
    tags: ['codegen', 'dates'],
    color: '#06b6d4',
  },
  {
    date: '5 May 2026',
    title: 'Dia 21: SonarQube + Seguridad',
    desc: 'Configuracion sonar-project.properties. requirements.txt para BlackDuck. Preparacion para compliance bancario.',
    tags: ['sonar', 'security', 'compliance'],
    color: '#f59e0b',
  },
  {
    date: '6 May 2026',
    title: 'Dia 22: CLI + Packaging',
    desc: 'bnx.sh (CLI rapido), package.sh (7z portable de 72KB), visualizador DAG en HTML, limpieza de emojis para servidores ASCII.',
    tags: ['cli', 'packaging'],
    color: '#a855f7',
  },
  {
    date: '7 May 2026',
    title: 'Dia 23: Motor OCR',
    desc: 'OCR para grafos Ab Initio: sube screenshot o pega texto, extrae nodos y conexiones, genera .mp y compila. Multi-paste con acumulacion, Cmd+V para imagenes.',
    tags: ['ocr', 'ai'],
    color: '#ec4899',
  },
  {
    date: '8 May 2026',
    title: 'Dia 24: Estimador de costos',
    desc: 'Cloud Cost Estimator (slider 1K-40K jobs). Matriz de decision ejecutiva (Ab Initio vs EKS vs LeapLogic vs BNX a 5 anos). Tema MonkeyPhone, exportar PDF.',
    tags: ['metrics', 'executive', 'costs'],
    color: '#f59e0b',
  },
  {
    date: '25 May 2026',
    title: 'Dia 26: GDE Parser mejorado + Roadmap',
    desc: 'Parser GDE con finditer (mas robusto). Limpieza ASCII. Plan de trabajo 3 meses (SDLC bancario). Pagina Roadmap en UI.',
    tags: ['parser', 'gde', 'roadmap'],
    color: '#22c55e',
  },
  {
    date: '3 Jun 2026',
    title: 'Dia 27: GDE Parser completo',
    desc: 'Parser GDE funcional al 100%: nombres, edges, transforms embebidos. serve_ui fix para transforms extraidos.',
    tags: ['parser', 'gde', 'complete'],
    color: '#22c55e',
  },
  {
    date: '24 Jun 2026',
    title: 'Dia 28: Target Python/Pandas',
    desc: 'Python/Pandas como target de generacion de codigo. Para equipos que no necesitan Spark. Fix groupby quoting.',
    tags: ['codegen', 'pandas'],
    color: '#6366f1',
  },
  {
    date: '21 Ago 2026',
    title: 'Dia 29: Fix codegen de fechas + UI grafos grandes',
    desc: 'Correccion de expresiones de cast de fecha Ab Initio (date("YYYY-MM-DD"))(string("|"))campo → to_date() en Glue y PySpark. Causa raiz: se traducia el SELECT completo antes de dividir por columnas. Fix de join_key como lista en el validador (de error bloqueante a warning). Toolbar en DagViewer para grafos grandes (ocultar Sort/Gather, busqueda, zoom).',
    tags: ['codegen', 'dates', 'ui', 'fix'],
    color: '#f59e0b',
  },
  {
    date: '21 Ago 2026',
    title: 'Dia 30: Data Redactada (datos sinteticos)',
    desc: 'Nueva herramienta: genera datos sinteticos con PII enmascarada desde el grafo o manual. Detecta PII por nombre (nombre, cuenta, tarjeta, email, ssn/rfc, etc.). Infiere esquema del grafo (dml_fields, casts, select). Separa entrada (in.) y salida (out.). Modo manual con tabla editable. Salida CSV/JSON. Conectada al grafo del Compiler.',
    tags: ['datagen', 'pii', 'ui'],
    color: '#14b8a6',
  },
  {
    date: '22 Ago 2026',
    title: 'Dia 31: Ejecutor de prueba local PySpark',
    desc: 'Corre el PySpark generado localmente con los datos sinteticos: reemplaza lecturas S3 por DataFrames en memoria, neutraliza escrituras/shell. Tolera limitaciones estructurales (nodos None, join keys ausentes, lookups sin traducir, PARAMS faltantes, tipos mezclados) pero NO oculta errores reales. Consola en vivo via Server-Sent Events con colores por tipo de nodo.',
    tags: ['datagen', 'test', 'pyspark'],
    color: '#14b8a6',
  },
  {
    date: '22 Ago 2026',
    title: 'Dia 32: Bugs de codegen detectados por la prueba',
    desc: 'La prueba local encontro y se corrigieron bugs reales del generador: string_like/instr sin traducir, if/else con parentesis anidados que se rompia (THEN )), casts con longitud numerica (string(40))campo, y string_like con 3er argumento (escape). Cada correccion mejora Glue y PySpark para todos los grafos.',
    tags: ['codegen', 'fix', 'test'],
    color: '#ef4444',
  },
  {
    date: '22 Ago 2026',
    title: 'Dia 33: Esquema real + valores de join compartidos',
    desc: 'Extraccion del record format real del .mp GDE (record string(N) campo; ... end;). Propagacion de columnas hacia los SOURCE trazando los edges: las join keys y campos de reformat aparecen en las fuentes reales. Valores de join compartidos (pool determinístico por nombre) para que los joins emparejen datos en vez de dejar columnas en NULL.',
    tags: ['datagen', 'gde', 'schema', 'join'],
    color: '#14b8a6',
  },
  {
    date: '22 Ago 2026',
    title: 'Dia 34: Enviar a AWS + ciclo en Arquitectura',
    desc: 'Boton Enviar a AWS desde Data Redactada: empaqueta el PySpark con datos sinteticos EMBEBIDOS (codigo autocontenido) y lo despacha al pipeline Glue existente con polling de estado, sin credenciales locales. Documentado el ciclo completo (grafo → datos → prueba → AWS) en la pagina de Arquitectura y en este historial.',
    tags: ['datagen', 'aws', 'pipeline', 'architecture'],
    color: '#14b8a6',
  },
]

const STATS = [
  { label: 'Dias de desarrollo', value: '34', color: '#6366f1' },
  { label: 'Commits', value: '135+', color: '#22c55e' },
  { label: 'Componentes', value: '25+', color: '#f59e0b' },
  { label: 'Parsers', value: '6', color: '#a855f7' },
  { label: 'Code Generators', value: '7', color: '#ec4899' },
  { label: 'Paginas UI', value: '9', color: '#06b6d4' },
]

const TAG_COLORS = {
  setup: '#64748b', docs: '#64748b', git: '#64748b',
  ui: '#6366f1', api: '#06b6d4', dag: '#22c55e', refactor: '#ef4444',
  deploy: '#f59e0b', lambda: '#f59e0b', aws: '#f59e0b',
  cobol: '#a855f7', parser: '#22c55e', metrics: '#f59e0b',
  designer: '#ec4899', banking: '#f59e0b', governance: '#6366f1',
  architecture: '#06b6d4', plan: '#22c55e', 'mega-dag': '#22c55e',
  executive: '#f59e0b', flink: '#6366f1', codegen: '#22c55e',
  cyclic: '#a855f7', engine: '#ef4444', admin: '#64748b',
  downloads: '#64748b', gde: '#22c55e', native: '#22c55e',
  dates: '#06b6d4', sonar: '#f59e0b', security: '#ef4444',
  compliance: '#f59e0b', cli: '#a855f7', packaging: '#a855f7',
  ocr: '#ec4899', ai: '#ec4899', costs: '#f59e0b',
  roadmap: '#22c55e', complete: '#22c55e', pandas: '#6366f1',
  datagen: '#14b8a6', pii: '#14b8a6', test: '#14b8a6', pyspark: '#6366f1',
  schema: '#14b8a6', join: '#f59e0b', pipeline: '#14b8a6', fix: '#ef4444',
}

export default function HistoryPage({ theme }) {
  const t = theme || {}
  const [filter, setFilter] = useState('')

  const filtered = filter
    ? TIMELINE.filter(item =>
        item.tags.includes(filter) ||
        item.title.toLowerCase().includes(filter) ||
        item.desc.toLowerCase().includes(filter)
      )
    : TIMELINE

  const allTags = [...new Set(TIMELINE.flatMap(item => item.tags))].sort()

  const card = {
    background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 20,
  }

  return (
    <div style={{ padding: 32, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: t.text || '#e2e8f0', margin: 0 }}>
          Historial del Proyecto
        </h2>
        <p style={{ fontSize: 14, color: t.dim || '#64748b', marginTop: 4 }}>
          Bitacora completa de desarrollo — desde el dia 1 hasta hoy
        </p>
      </div>

      {/* Stats */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {STATS.map(s => (
          <div key={s.label} style={{
            flex: '1 1 120px', padding: 14, borderRadius: 8, textAlign: 'center',
            background: s.color + '10', border: `1px solid ${s.color}30`,
          }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 11, color: t.dim || '#64748b', marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: 12, color: t.dim || '#64748b', marginRight: 8 }}>Filtrar:</span>
        <button
          onClick={() => setFilter('')}
          style={{
            padding: '3px 10px', borderRadius: 12, fontSize: 11, cursor: 'pointer',
            background: !filter ? '#6366f120' : 'transparent',
            border: `1px solid ${!filter ? '#6366f1' : (t.border || '#334155')}`,
            color: !filter ? '#6366f1' : (t.dim || '#64748b'),
          }}
        >Todos</button>
        {allTags.map(tag => (
          <button
            key={tag}
            onClick={() => setFilter(filter === tag ? '' : tag)}
            style={{
              padding: '3px 10px', borderRadius: 12, fontSize: 11, cursor: 'pointer',
              background: filter === tag ? (TAG_COLORS[tag] || '#64748b') + '20' : 'transparent',
              border: `1px solid ${filter === tag ? (TAG_COLORS[tag] || '#64748b') : (t.border || '#334155')}`,
              color: filter === tag ? (TAG_COLORS[tag] || '#64748b') : (t.dim || '#64748b'),
            }}
          >{tag}</button>
        ))}
      </div>

      {/* Timeline */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0, position: 'relative' }}>
        {/* Vertical line */}
        <div style={{
          position: 'absolute', left: 15, top: 8, bottom: 8, width: 2,
          background: t.border || '#334155',
        }} />

        {filtered.map((item, i) => (
          <div key={i} style={{ display: 'flex', gap: 16, paddingBottom: 20, position: 'relative' }}>
            {/* Dot */}
            <div style={{
              width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
              background: item.color + '20', border: `2px solid ${item.color}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 12, fontWeight: 700, color: item.color, zIndex: 1,
            }}>
              {i + 1}
            </div>

            {/* Content */}
            <div style={{
              ...card, flex: 1, padding: 14,
              borderLeft: `3px solid ${item.color}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0' }}>
                    {item.title}
                  </div>
                  <div style={{ fontSize: 12, color: item.color, marginTop: 2 }}>
                    {item.date}
                  </div>
                </div>
              </div>
              <div style={{ fontSize: 13, color: t.muted || '#94a3b8', marginTop: 8, lineHeight: 1.6 }}>
                {item.desc}
              </div>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 8 }}>
                {item.tags.map(tag => (
                  <span key={tag} style={{
                    padding: '2px 8px', borderRadius: 10, fontSize: 10, fontWeight: 600,
                    background: (TAG_COLORS[tag] || '#64748b') + '20',
                    color: TAG_COLORS[tag] || '#64748b',
                    border: `1px solid ${(TAG_COLORS[tag] || '#64748b')}30`,
                    cursor: 'pointer',
                  }} onClick={() => setFilter(tag)}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div style={card}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 12 }}>
          Estado Actual de Componentes
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8 }}>
          {[
            'Parser MP (texto)', 'Parser MP (GDE nativo)', 'Parser XFR', 'Parser DML',
            'Parser COBOL', 'Parser PLAN/PSET', 'DAG Builder + Mega-DAG', 'Validador semantico',
            'Codegen Glue', 'Codegen Spark', 'Codegen Flink', 'Codegen Step Functions',
            'Codegen Terraform', 'Codegen Airflow', 'Codegen Python/Pandas',
            'Motor de refactorizacion', 'Motor OCR', 'Motor de accuracy',
            'Data Redactada (datos sinteticos)', 'Ejecutor de prueba PySpark',
            'Consola en vivo (SSE)', 'Esquema real + join compartido', 'Enviar a AWS (pipeline)',
            'UI React (9 tabs)', 'API FastAPI + Lambda', 'CLI batch', 'Packaging portable',
          ].map(comp => (
            <div key={comp} style={{
              display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px',
              borderRadius: 6, background: '#22c55e10', border: '1px solid #22c55e30',
            }}>
              <span style={{ color: '#22c55e', fontWeight: 700, fontSize: 12 }}>[ok]</span>
              <span style={{ fontSize: 12, color: t.text || '#e2e8f0' }}>{comp}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
