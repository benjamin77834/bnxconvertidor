import { useState } from 'react'

// Guia de comandos de terminal (copiables). Se usa en Py->Spark y Data Redactada
// para mostrar como hacer lo mismo desde la linea de comandos.
//
// Props:
//   theme    tema de la app
//   title    titulo del panel (opcional)
//   sections [{ label, cmd, note? }]  bloques de comando

export default function TerminalGuide({ theme, title = 'Guía de comandos (terminal)', sections = [] }) {
  const t = theme || {}
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(-1)

  const copy = (text, i) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(i)
      setTimeout(() => setCopied(-1), 1200)
    }).catch(() => {})
  }

  return (
    <div style={{
      marginTop: 12, border: `1px solid ${t.border || '#334155'}`, borderRadius: 10,
      background: t.card || '#0f172a', overflow: 'hidden',
    }}>
      <button onClick={() => setOpen(o => !o)} style={{
        width: '100%', textAlign: 'left', padding: '10px 14px', cursor: 'pointer',
        background: 'transparent', border: 'none', color: t.text || '#e2e8f0',
        fontSize: 14, fontWeight: 600, display: 'flex', justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <span>💻 {title}</span>
        <span style={{ color: t.dim || '#64748b', fontSize: 12 }}>{open ? '▲ ocultar' : '▼ mostrar'}</span>
      </button>

      {open && (
        <div style={{ padding: '4px 14px 14px' }}>
          {sections.map((s, i) => (
            <div key={i} style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 12.5, color: t.muted || '#94a3b8', marginBottom: 4 }}>
                {s.label}
              </div>
              <div style={{ position: 'relative' }}>
                <pre style={{
                  margin: 0, padding: '10px 40px 10px 12px', borderRadius: 8,
                  background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
                  color: '#22c55e', fontFamily: 'monospace', fontSize: 12.5,
                  whiteSpace: 'pre-wrap', wordBreak: 'break-word', lineHeight: 1.5,
                }}>{s.cmd}</pre>
                <button onClick={() => copy(s.cmd, i)}
                  title="Copiar comando"
                  style={{
                    position: 'absolute', top: 6, right: 6, padding: '3px 8px',
                    borderRadius: 6, fontSize: 11, cursor: 'pointer',
                    background: copied === i ? '#22c55e' : (t.border || '#334155') + '80',
                    color: copied === i ? '#04240f' : (t.muted || '#94a3b8'),
                    border: 'none', fontWeight: 600,
                  }}>{copied === i ? '✓ copiado' : 'copiar'}</button>
              </div>
              {s.note && (
                <div style={{ fontSize: 11.5, color: t.dim || '#64748b', marginTop: 3 }}>
                  {s.note}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
