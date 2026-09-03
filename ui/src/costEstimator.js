// Estimador de costo AWS (Glue) por grafo, segun su complejidad.
// Reutiliza el modelo de precios de MetricsPage (Glue $0.44/DPU-hora, 1 DPU = 4 vCPU/16GB).
// Clasifica el grafo en Simple/Medio/Complejo por numero de nodos, joins y edges,
// y estima DPUs, duracion y costo por corrida + costo mensual segun frecuencia.

const GLUE_DPU_HOUR = 0.44 // USD por DPU-hora (Glue 4.0, us-east-1)

// Perfiles por complejidad: DPUs asignadas y minutos estimados de corrida.
// Alineado con MetricsPage: Simple 2 DPU/3min, Medio 4 DPU/20min, Complejo 8 DPU/~2-4h.
const PROFILES = {
  Simple:   { dpu: 2, minutes: 3,  color: '#22c55e' },
  Medio:    { dpu: 4, minutes: 20, color: '#f59e0b' },
  Complejo: { dpu: 8, minutes: 120, color: '#ef4444' },
}

// Clasifica el grafo por su estructura.
// - nodes: total de nodos del DAG
// - joins: nodos JOIN/LOOKUP (los mas caros: shuffle)
// - edges: total de conexiones
export function classifyComplexity({ nodes = 0, joins = 0, edges = 0 }) {
  // Reglas simples y explicables:
  //  - Complejo: muchos nodos o varios joins (>= 100 nodos, o >= 5 joins, o >= 70 edges)
  //  - Medio:    tamano intermedio (>= 15 nodos, o >= 2 joins, o >= 20 edges)
  //  - Simple:   lo demas
  if (nodes >= 100 || joins >= 5 || edges >= 70) return 'Complejo'
  if (nodes >= 15 || joins >= 2 || edges >= 20) return 'Medio'
  return 'Simple'
}

// Devuelve el detalle de costo estimado para un grafo.
// runsPerMonth: cuantas veces se ejecuta el job al mes (default 22 = dias habiles).
export function estimateGraphCost({ nodes = 0, joins = 0, edges = 0, runsPerMonth = 22 }) {
  const level = classifyComplexity({ nodes, joins, edges })
  const p = PROFILES[level]
  const dpuHours = p.dpu * (p.minutes / 60)
  const costPerRun = GLUE_DPU_HOUR * dpuHours
  const costPerMonth = costPerRun * runsPerMonth
  return {
    level,
    color: p.color,
    dpu: p.dpu,
    minutes: p.minutes,
    dpuHours: Number(dpuHours.toFixed(3)),
    costPerRun: Number(costPerRun.toFixed(3)),
    costPerMonth: Number(costPerMonth.toFixed(2)),
    runsPerMonth,
    note: 'Estimacion Glue 4.0 ($0.44/DPU-hora, us-east-1). Aproximada: el costo real depende del volumen de datos y del tiempo real de ejecucion.',
  }
}

// Extrae metricas de complejidad del resultado del compile o del runReport.
export function metricsFromResult(result) {
  if (!result) return { nodes: 0, joins: 0, edges: 0 }
  const nodes = (result.nodes && result.nodes.length) || result.node_count || 0
  const edges = (result.edges && result.edges.length) || result.edge_count || 0
  let joins = 0
  if (Array.isArray(result.nodes)) {
    joins = result.nodes.filter(n => {
      const ty = String(n.type || n.node_type || '').toUpperCase()
      return ty === 'JOIN' || ty === 'LOOKUP'
    }).length
  }
  return { nodes, joins, edges }
}
