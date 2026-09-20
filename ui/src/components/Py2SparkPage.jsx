import { useState, useEffect } from 'react'
import { COMPILE_URL } from '../config'
import TerminalGuide from './TerminalGuide'

// Py -> Spark: convierte codigo Python (pandas) a PySpark 3 usando el endpoint
// /py2spark del portal (misma libreria py2spark de la CLI y la extension VS Code).
// Permite pegar o subir un .py, ver el PySpark generado con sus avisos, descargarlo
// y enviarlo a Data Redactada para generar datos sinteticos y ejecutarlo local.
export default function Py2SparkPage({ theme, onSendToDataGen }) {
  const t = theme || {}
  const [src, setSrc] = useState('')
  const [result, setResult] = useState(null)   // {ok, code, warnings, unsupported}
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [examples, setExamples] = useState([])  // [{id,title,code}]

  const PY2SPARK_URL = COMPILE_URL.replace('/compile', '/py2spark')
  const EXAMPLES_URL = COMPILE_URL.replace('/compile', '/py2spark/examples')

  // Cargar los ejemplos ML (pandas) del portal al montar la pagina.
  useEffect(() => {
    fetch(EXAMPLES_URL)
      .then(r => r.json())
      .then(d => setExamples(d.examples || []))
      .catch(() => setExamples([]))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const card = {
    background: t.card || '#0f172a', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 16,
  }
  const codeBox = {
    width: '100%', minHeight: 240, padding: 12, borderRadius: 8,
    background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
    color: t.text || '#e2e8f0', fontFamily: 'monospace', fontSize: 12.5,
    lineHeight: 1.6, resize: 'vertical', outline: 'none', whiteSpace: 'pre',
  }

  const convert = async () => {
    if (!src.trim()) return
    setLoading(true); setError(''); setResult(null)
    try {
      const res = await fetch(PY2SPARK_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: src }),
      })
      const data = await res.json()
      if (data.error) { setError(data.error); return }
      // ok:false = el codigo de entrada NO es Python valido. En ese caso el
      // backend devuelve el codigo SIN convertir, asi que no debemos tratarlo
      // como exito (ni enviarlo a Data Redactada). Mostramos el error real.
      if (data.ok === false) {
        const why = (data.unsupported && data.unsupported[0]) || 'El codigo no es Python valido.'
        setError(why + ' Revisa la sintaxis (p. ej. def __init__, indentacion, o simbolos ** de Markdown pegados).')
        return
      }
      setResult(data)
    } catch (e) {
      setError('Error de red: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  const onFile = (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    const reader = new FileReader()
    reader.onload = () => setSrc(String(reader.result || ''))
    reader.readAsText(f)
  }

  const download = () => {
    if (!result?.code) return
    const blob = new Blob([result.code], { type: 'text/x-python' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'job_pyspark.py'; a.click()
    URL.revokeObjectURL(url)
  }

  const sendToDataGen = () => {
    if (!result?.code) return
    onSendToDataGen && onSendToDataGen(result.code)
  }

  const EXAMPLE = `import pandas as pd

df = pd.read_csv("ventas.csv")
df = df[df["monto"] > 100]
df["neto"] = df["monto"] - df["impuesto"]
g = df.groupby("region").agg({"monto": "sum", "neto": "mean"})
clientes = pd.read_parquet("clientes")
j = df.merge(clientes, on="cliente_id", how="left")
j = j.sort_values("monto", ascending=False)
j.to_parquet("salida")`

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 22, color: t.text || '#e2e8f0' }}>🐍 Python → PySpark 3</h2>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: t.muted || '#94a3b8' }}>
            Convierte scripts de Python (pandas) a PySpark 3. Lo que no es traducible 1:1
            se marca con <code>#&nbsp;TODO&nbsp;py2spark</code>. Misma librería que la CLI
            (<code>py2spark convert</code>) y la extensión de VS Code.
          </p>
        </div>
        <a href={COMPILE_URL.replace('/compile', '/download/vsix')} download="py2spark.vsix"
          title="Descarga la extensión de VS Code (py2spark.vsix) para convertir Python a PySpark desde el editor"
          style={{ ...btn(t, 'accent'), textDecoration: 'none', flexShrink: 0 }}>
          🧩 Extensión VS Code (.vsix)
        </a>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Entrada */}
        <div style={card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <h3 style={{ margin: 0, fontSize: 15, color: t.text || '#e2e8f0' }}>Python de entrada</h3>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {/* Selector de ejemplos ML (pandas) servidos por el portal. */}
              <select
                defaultValue=""
                onChange={e => {
                  const ex = examples.find(x => x.id === e.target.value)
                  if (ex) { setSrc(ex.code); setResult(null); setError('') }
                  else if (e.target.value === '__basic') { setSrc(EXAMPLE); setResult(null); setError('') }
                  e.target.value = ''
                }}
                title="Cargar un ejemplo de código en el editor"
                style={{
                  padding: '6px 10px', borderRadius: 8, fontSize: 12.5,
                  background: t.codeBg || '#081220', color: t.text || '#e2e8f0',
                  border: `1px solid ${t.border || '#334155'}`, outline: 'none', cursor: 'pointer',
                }}>
                <option value="" disabled>📚 Ejemplos…</option>
                <option value="__basic">Básico (pandas ETL)</option>
                {examples.map(ex => (
                  <option key={ex.id} value={ex.id}>{ex.title}</option>
                ))}
              </select>
              <label style={{ ...btn(t, 'ghost'), display: 'inline-block' }}>
                📂 Subir .py
                <input type="file" accept=".py,text/x-python" onChange={onFile} style={{ display: 'none' }} />
              </label>
            </div>
          </div>
          <textarea
            value={src}
            onChange={e => setSrc(e.target.value)}
            placeholder="Pega tu código Python (pandas) aquí..."
            style={codeBox}
          />
          <div style={{ marginTop: 10, display: 'flex', gap: 8, alignItems: 'center' }}>
            <button onClick={convert} disabled={!src.trim() || loading} style={btn(t, 'primary', !src.trim() || loading)}>
              {loading ? 'Convirtiendo…' : '⚡ Convertir a PySpark'}
            </button>
            {src && <button onClick={() => { setSrc(''); setResult(null); setError('') }} style={btn(t, 'ghost')}>Limpiar</button>}
          </div>
        </div>

        {/* Salida */}
        <div style={card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <h3 style={{ margin: 0, fontSize: 15, color: t.text || '#e2e8f0' }}>PySpark 3 generado</h3>
            {result?.code && (
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={download} style={btn(t, 'ghost')}>📥 Descargar</button>
                <button onClick={sendToDataGen} title="Genera datos sintéticos y ejecuta este PySpark localmente"
                  style={btn(t, 'accent')}>🧪 A Data Redactada</button>
              </div>
            )}
          </div>
          {error && (
            <div style={{ padding: 10, borderRadius: 8, background: '#ef444415', border: '1px solid #ef444440', color: '#ef4444', fontSize: 13, marginBottom: 8 }}>
              {error}
            </div>
          )}
          <textarea readOnly value={result?.code || ''} placeholder="El PySpark aparecerá aquí…" style={{ ...codeBox, color: '#22c55e' }} />

          {/* Avisos y no soportados */}
          {result && (result.warnings?.length > 0 || result.unsupported?.length > 0) && (
            <div style={{ marginTop: 10, fontSize: 12.5 }}>
              {result.unsupported?.length > 0 && (
                <div style={{ marginBottom: 6 }}>
                  <strong style={{ color: '#ef4444' }}>Requiere revisión manual ({result.unsupported.length}):</strong>
                  <ul style={{ margin: '4px 0 0', paddingLeft: 18, color: t.muted || '#94a3b8' }}>
                    {result.unsupported.map((u, i) => <li key={i}>{u}</li>)}
                  </ul>
                </div>
              )}
              {result.warnings?.length > 0 && (
                <div>
                  <strong style={{ color: '#f59e0b' }}>Avisos ({result.warnings.length}):</strong>
                  <ul style={{ margin: '4px 0 0', paddingLeft: 18, color: t.muted || '#94a3b8' }}>
                    {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}
          {result && result.unsupported?.length === 0 && result.warnings?.length === 0 && (
            <div style={{ marginTop: 10, fontSize: 12.5, color: '#22c55e' }}>
              ✅ Conversión sin construcciones no soportadas.
            </div>
          )}
        </div>
      </div>

      {/* Guia de comandos de terminal para hacer lo mismo por CLI. */}
      <TerminalGuide theme={t} title="Guía de comandos (terminal) — Python → PySpark" sections={[
        {
          label: 'Instalar la CLI py2spark (una vez, en el venv del proyecto)',
          cmd: 'pip install -e .',
          note: 'Deja disponible el comando `py2spark`. Sin instalar, usa: PYTHONPATH=src python -m py2spark ...',
        },
        {
          label: 'Convertir un archivo Python (pandas) a PySpark',
          cmd: 'py2spark convert mi_script.py -o job_pyspark.py',
          note: 'Sin -o imprime a stdout. Usa - para leer de stdin: cat mi_script.py | py2spark convert',
        },
        {
          label: 'Ver el resultado en JSON (código + avisos + no soportados)',
          cmd: 'py2spark convert mi_script.py --json',
        },
        {
          label: 'Ejecutar el PySpark generado localmente',
          cmd: 'python job_pyspark.py',
          note: 'Requiere pyspark y Java instalados. Para un cluster: spark-submit job_pyspark.py',
        },
        {
          label: 'Ejecutar en un cluster / EMR / Glue local con spark-submit',
          cmd: 'spark-submit --master local[*] job_pyspark.py',
        },
        {
          label: 'Convertir vía el endpoint del portal (curl)',
          cmd: `curl -s -X POST ${(typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8081')}/py2spark \\\n  -H "Content-Type: application/json" \\\n  -d '{"code": "import pandas as pd\\ndf = pd.read_csv(\\"v.csv\\")"}'`,
        },
      ]} />
    </div>
  )
}

// Estilos de boton reutilizables.
function btn(t, kind, disabled) {
  const base = {
    padding: '7px 14px', borderRadius: 8, fontSize: 12.5, fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer', border: '1px solid transparent',
    whiteSpace: 'nowrap',
  }
  if (kind === 'primary') return { ...base, background: disabled ? (t.border || '#334155') : (t.accent || '#6366f1'), color: '#fff' }
  if (kind === 'accent') return { ...base, background: '#14b8a620', border: '1px solid #14b8a640', color: '#2dd4bf' }
  // ghost
  return { ...base, background: 'transparent', border: `1px solid ${t.border || '#334155'}`, color: t.muted || '#94a3b8' }
}
