import { useState } from 'react'
import { estimateGraphCost } from '../costEstimator'

// Tarjeta reutilizable: costo estimado en AWS (Glue) segun la complejidad del grafo.
// Se usa en Compiler y en Data Redactada cuando se prueba un grafo.
// Props: theme, nodes, joins, edges.
export default function CostEstimateCard({ theme, nodes = 0, joins = 0, edges = 0 }) {
  const t = theme || {}
  const [runs, setRuns] = useState(22)
  if (!nodes && !edges) return null

  const est = estimateGraphCost({ nodes, joins, edges, runsPerMonth: runs })
  const fmt = (n) => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

  return (
    <details style={{
      background: '#0a0e17', border: `1px solid ${est.color}55`,
      borderRadius: 8, padding: '10px 14px',
    }}>
      <summary style={{
        cursor: 'pointer', fontSize: 14, fontWeight: 700, color: est.color,
        userSelect: 'none', outline: 'none',
      }}>
        💰 Costo estimado en AWS · complejidad {est.level}
      </summary>

      <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {/* Metricas de complejidad */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {[
            { lbl: 'Nodos', val: nodes, col: '#38bdf8' },
            { lbl: 'Joins/Lookups', val: joins, col: '#a855f7' },
            { lbl: 'Conexiones', val: edges, col: '#94a3b8' },
            { lbl: 'DPUs', val: est.dpu, col: est.color },
            { lbl: 'Min/corrida', val: est.minutes, col: est.color },
          ].map((c, i) => (
            <div key={i} style={{
              flex: '1 1 90px', minWidth: 90, textAlign: 'center',
              background: '#11162080', borderRadius: 6, padding: '8px 6px',
            }}>
              <div style={{ fontSize: 18, fontWeight: 700, color: c.col }}>{c.val}</div>
              <div style={{ fontSize: 10, color: t.dim || '#64748b' }}>{c.lbl}</div>
            </div>
          ))}
        </div>

        {/* Costo por corrida y mensual */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <div style={{
            flex: '1 1 160px', background: '#11162080', borderRadius: 8,
            padding: 12, border: `1px solid ${est.color}40`,
          }}>
            <div style={{ fontSize: 11, color: t.dim || '#64748b' }}>Costo por ejecución</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: est.color }}>${fmt(est.costPerRun)}</div>
            <div style={{ fontSize: 10, color: t.muted || '#94a3b8' }}>{est.dpuHours} DPU-hora</div>
          </div>
          <div style={{
            flex: '1 1 160px', background: '#11162080', borderRadius: 8,
            padding: 12, border: `1px solid ${est.color}40`,
          }}>
            <div style={{ fontSize: 11, color: t.dim || '#64748b' }}>Costo mensual estimado</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: est.color }}>${fmt(est.costPerMonth)}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
              <span style={{ fontSize: 10, color: t.muted || '#94a3b8' }}>corridas/mes</span>
              <input
                type="number" min={1} max={1000} value={runs}
                onChange={e => setRuns(Math.max(1, Math.min(1000, Number(e.target.value) || 1)))}
                style={{
                  width: 60, padding: '2px 6px', borderRadius: 4, fontSize: 12,
                  background: t.card || '#1e2433', color: t.text || '#e2e8f0',
                  border: `1px solid ${t.border || '#334155'}`,
                }}
              />
            </div>
          </div>
        </div>

        <div style={{ fontSize: 10, color: t.dim || '#64748b', lineHeight: 1.5 }}>
          {est.note}
        </div>
      </div>
    </details>
  )
}
