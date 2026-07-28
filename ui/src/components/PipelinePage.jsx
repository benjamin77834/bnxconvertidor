import { useState } from 'react'
import { COMPILE_URL } from '../config'

const PIPELINE_STEPS = [
  { id: 'upload', label: '1. Upload Test Data', icon: '📤', desc: 'Subir datos CSV de prueba a S3' },
  { id: 'compile_spark', label: '2. Compile (Spark)', icon: '⚡', desc: 'Compilar grafo con BNX target=spark' },
  { id: 'compile_glue', label: '3. Compile (Glue)', icon: '🔧', desc: 'Compilar grafo con BNX target=glue' },
  { id: 'run_spark', label: '4. Run Spark Job', icon: '🚀', desc: 'Ejecutar PySpark en AWS Glue' },
  { id: 'run_glue', label: '5. Run Glue Job', icon: '🚀', desc: 'Ejecutar AWS Glue job' },
  { id: 'validate', label: '6. Validate Output', icon: '✅', desc: 'Comparar output Spark vs Glue vs Expected' },
  { id: 'notify', label: '7. Notify', icon: '📧', desc: 'Notificar resultado via SNS' },
]

const DEFAULT_MP = `NODE Input_File : SOURCE
NODE Filter_by_Expression : FILTER
NODE Reformat : TRANSFORM
NODE Rollup : TRANSFORM
NODE Output_File : SINK

Input_File -> Filter_by_Expression
Filter_by_Expression -> Reformat
Reformat -> Rollup
Rollup -> Output_File`

const DEFAULT_XFR = `Input_File:
  source_type s3
  path s3://bnx-e2e-test/raw/orders
  format csv

Reformat:
  select id, nombre, monto
  transform upper(nombre)

Rollup:
  group_by nombre
  agg sum(monto) as monto

Output_File:
  sink_type s3
  path s3://bnx-e2e-test/output
  format parquet
  mode overwrite`

const DEFAULT_DATA = `id,nombre,monto
1,juan perez,150.50
2,maria gomez,300.5
3,carlos lopez,75.25
4,ana martinez,200.0
5,luis rodriguez,120.25
6,juan perez,50.0
7,maria gomez,100.0`

export default function PipelinePage({ theme }) {
  const t = theme || {}
  const [mp, setMp] = useState(DEFAULT_MP)
  const [xfr, setXfr] = useState(DEFAULT_XFR)
  const [testData, setTestData] = useState(DEFAULT_DATA)
  const [target, setTarget] = useState('both')
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState(null)
  const [stepStatus, setStepStatus] = useState({})
  const [sparkCode, setSparkCode] = useState('')
  const [glueCode, setGlueCode] = useState('')
  const [logs, setLogs] = useState([])

  const card = {
    background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 20,
  }

  const addLog = (msg) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`])
  }

  const setStep = (id, status) => {
    setStepStatus(prev => ({ ...prev, [id]: status }))
  }

  const runPipeline = async () => {
    setRunning(true)
    setResults(null)
    setStepStatus({})
    setSparkCode('')
    setGlueCode('')
    setLogs([])

    addLog('Pipeline E2E iniciado')

    // Step 1: Upload (simulado — los datos ya estan en el textarea)
    setStep('upload', 'running')
    addLog(`Test data: ${testData.split('\n').length - 1} filas`)
    await new Promise(r => setTimeout(r, 500))
    setStep('upload', 'done')
    addLog('Test data listo')

    // Step 2: Compile Spark
    if (target === 'both' || target === 'spark') {
      setStep('compile_spark', 'running')
      addLog('Compilando grafo (target=spark)...')
      try {
        const form = new FormData()
        form.append('mp', new File([mp], 'test.mp'))
        if (xfr.trim()) form.append('xfr', new File([xfr], 'test.xfr'))
        form.append('target', 'spark')
        const res = await fetch(COMPILE_URL, { method: 'POST', body: form })
        const data = await res.json()
        if (data.code) {
          setSparkCode(data.code)
          setStep('compile_spark', 'done')
          addLog(`Spark code generado (${data.code.split('\n').length} lineas, ${data.nodes?.length || 0} nodos)`)
        } else {
          setStep('compile_spark', 'error')
          addLog(`ERROR Spark: ${(data.errors || []).join(', ')}`)
        }
      } catch (e) {
        setStep('compile_spark', 'error')
        addLog(`ERROR Spark: ${e.message}`)
      }
    } else {
      setStep('compile_spark', 'skip')
    }

    // Step 3: Compile Glue
    if (target === 'both' || target === 'glue') {
      setStep('compile_glue', 'running')
      addLog('Compilando grafo (target=glue)...')
      try {
        const form = new FormData()
        form.append('mp', new File([mp], 'test.mp'))
        if (xfr.trim()) form.append('xfr', new File([xfr], 'test.xfr'))
        form.append('target', 'glue')
        const res = await fetch(COMPILE_URL, { method: 'POST', body: form })
        const data = await res.json()
        if (data.code) {
          setGlueCode(data.code)
          setStep('compile_glue', 'done')
          addLog(`Glue code generado (${data.code.split('\n').length} lineas, ${data.nodes?.length || 0} nodos)`)
        } else {
          setStep('compile_glue', 'error')
          addLog(`ERROR Glue: ${(data.errors || []).join(', ')}`)
        }
      } catch (e) {
        setStep('compile_glue', 'error')
        addLog(`ERROR Glue: ${e.message}`)
      }
    } else {
      setStep('compile_glue', 'skip')
    }

    // Steps 4-5: Run jobs (informativo — requiere AWS credentials)
    const hasCode = sparkCode || glueCode
    if (target === 'both' || target === 'spark') {
      setStep('run_spark', 'info')
      addLog('Spark job listo para ejecutar en AWS Glue (requiere aws credentials)')
    }
    if (target === 'both' || target === 'glue') {
      setStep('run_glue', 'info')
      addLog('Glue job listo para ejecutar en AWS Glue (requiere aws credentials)')
    }

    // Step 6: Validate
    setStep('validate', 'info')
    addLog('Validacion disponible despues de ejecutar los jobs en AWS')

    // Step 7: Summary
    setStep('notify', 'done')
    const sparkOk = stepStatus.compile_spark !== 'error'
    const glueOk = stepStatus.compile_glue !== 'error'
    addLog(`Pipeline completado: Compilacion ${sparkOk && glueOk ? 'EXITOSA' : 'CON ERRORES'}`)

    setResults({
      sparkCode: sparkCode || '',
      glueCode: glueCode || '',
      sparkLines: sparkCode ? sparkCode.split('\n').length : 0,
      glueLines: glueCode ? glueCode.split('\n').length : 0,
    })

    setRunning(false)
  }

  const stepColor = (status) => {
    if (status === 'done') return '#22c55e'
    if (status === 'running') return '#f59e0b'
    if (status === 'error') return '#ef4444'
    if (status === 'info') return '#6366f1'
    if (status === 'skip') return '#64748b'
    return t.dim || '#64748b'
  }

  const stepIcon = (status) => {
    if (status === 'done') return '[ok]'
    if (status === 'running') return '[>>]'
    if (status === 'error') return '[!!]'
    if (status === 'info') return '[i]'
    if (status === 'skip') return '[--]'
    return '[ ]'
  }

  const download = (content, filename) => {
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div style={{ padding: 32, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: t.text || '#e2e8f0', margin: 0 }}>
          Pipeline E2E — Pruebas de Conversion
        </h2>
        <p style={{ fontSize: 14, color: t.dim || '#64748b', marginTop: 4 }}>
          Compila un grafo con BNX, genera codigo Spark y Glue, ejecuta y valida resultados
        </p>
      </div>

      {/* Architecture Diagram */}
      <div style={{
        ...card,
        background: (t.codeBg || '#081220'),
        fontFamily: 'monospace', fontSize: 12, lineHeight: 1.8,
        color: t.muted || '#94a3b8', whiteSpace: 'pre',
      }}>
{`  ┌─────────────┐     ┌─────────────────┐     ┌─────────────┐     ┌──────────┐
  │  .mp + .xfr │────>│  BNX Compiler   │────>│  Glue Jobs  │────>│ Validate │
  │  (Landing)  │     │  (Lambda)       │     │ Spark + Glue│     │ (compare)│
  └─────────────┘     └─────────────────┘     └─────────────┘     └────┬─────┘
                         │ target=spark          │ paralelo              │
                         │ target=glue           │                ┌──────┴──────┐
                         ▼                       ▼                │ SNS Alert   │
                      Bronze (S3)         Gold (S3 output)        │ (pass/fail) │
                                                                  └─────────────┘`}
      </div>

      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        {/* Left: Input */}
        <div style={{ flex: '1 1 400px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Graph input */}
          <div style={card}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 10 }}>
              Grafo de prueba (.mp)
            </h3>
            <textarea
              value={mp}
              onChange={e => setMp(e.target.value)}
              style={{
                width: '100%', minHeight: 160, padding: 10, borderRadius: 8,
                background: t.codeBg || '#081220', border: `1px solid #22c55e40`,
                color: '#22c55e', fontSize: 12, fontFamily: 'monospace',
                resize: 'vertical', outline: 'none',
              }}
            />
          </div>

          {/* XFR input */}
          <div style={card}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 10 }}>
              Reglas (.xfr)
            </h3>
            <textarea
              value={xfr}
              onChange={e => setXfr(e.target.value)}
              style={{
                width: '100%', minHeight: 140, padding: 10, borderRadius: 8,
                background: t.codeBg || '#081220', border: `1px solid #6366f140`,
                color: '#6366f1', fontSize: 12, fontFamily: 'monospace',
                resize: 'vertical', outline: 'none',
              }}
            />
          </div>

          {/* Test data */}
          <div style={card}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 10 }}>
              Datos de prueba (CSV)
            </h3>
            <textarea
              value={testData}
              onChange={e => setTestData(e.target.value)}
              style={{
                width: '100%', minHeight: 100, padding: 10, borderRadius: 8,
                background: t.codeBg || '#081220', border: `1px solid #f59e0b40`,
                color: '#f59e0b', fontSize: 12, fontFamily: 'monospace',
                resize: 'vertical', outline: 'none',
              }}
            />
          </div>

          {/* Controls */}
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <select
              value={target}
              onChange={e => setTarget(e.target.value)}
              style={{
                padding: '10px 14px', borderRadius: 8, fontSize: 13,
                background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
                color: t.text || '#e2e8f0', cursor: 'pointer',
              }}
            >
              <option value="both">Ambos (Spark + Glue)</option>
              <option value="spark">Solo PySpark</option>
              <option value="glue">Solo AWS Glue</option>
            </select>

            <button
              onClick={runPipeline}
              disabled={running || !mp.trim()}
              style={{
                flex: 1, padding: '12px 20px', borderRadius: 8, cursor: running ? 'wait' : 'pointer',
                background: running ? '#f59e0b' : '#22c55e',
                color: '#000', border: 'none', fontSize: 14, fontWeight: 700,
              }}
            >
              {running ? '⏳ Ejecutando pipeline...' : '▶ Ejecutar Pipeline E2E'}
            </button>
          </div>
        </div>

        {/* Right: Pipeline status + results */}
        <div style={{ flex: '1 1 350px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Pipeline Steps */}
          <div style={card}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 12 }}>
              Pipeline Steps
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {PIPELINE_STEPS.map(step => {
                const status = stepStatus[step.id]
                return (
                  <div key={step.id} style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '8px 12px', borderRadius: 6,
                    background: status ? stepColor(status) + '10' : 'transparent',
                    border: `1px solid ${status ? stepColor(status) + '30' : (t.border || '#334155')}`,
                  }}>
                    <span style={{
                      fontFamily: 'monospace', fontWeight: 700, fontSize: 12,
                      color: stepColor(status), minWidth: 36,
                    }}>
                      {stepIcon(status)}
                    </span>
                    <span style={{ fontSize: 16 }}>{step.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, color: t.text || '#e2e8f0' }}>
                        {step.label}
                      </div>
                      <div style={{ fontSize: 11, color: t.dim || '#64748b' }}>
                        {step.desc}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Logs */}
          {logs.length > 0 && (
            <div style={card}>
              <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 10 }}>
                Logs
              </h3>
              <div style={{
                maxHeight: 200, overflowY: 'auto', padding: 10, borderRadius: 6,
                background: t.codeBg || '#081220', fontFamily: 'monospace', fontSize: 11,
                lineHeight: 1.8,
              }}>
                {logs.map((log, i) => (
                  <div key={i} style={{
                    color: log.includes('ERROR') ? '#ef4444'
                         : log.includes('EXITOSA') ? '#22c55e'
                         : (t.muted || '#94a3b8'),
                  }}>{log}</div>
                ))}
              </div>
            </div>
          )}

          {/* Generated code download */}
          {(sparkCode || glueCode) && (
            <div style={card}>
              <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 10 }}>
                Codigo Generado
              </h3>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {sparkCode && (
                  <button onClick={() => download(sparkCode, 'spark_job.py')} style={{
                    padding: '8px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 12,
                    background: '#22c55e15', border: '1px solid #22c55e30', color: '#22c55e',
                    fontWeight: 600,
                  }}>
                    📥 spark_job.py ({sparkCode.split('\n').length} lineas)
                  </button>
                )}
                {glueCode && (
                  <button onClick={() => download(glueCode, 'glue_job.py')} style={{
                    padding: '8px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 12,
                    background: '#6366f115', border: '1px solid #6366f130', color: '#6366f1',
                    fontWeight: 600,
                  }}>
                    📥 glue_job.py ({glueCode.split('\n').length} lineas)
                  </button>
                )}
              </div>

              {/* AWS execution command */}
              <div style={{
                marginTop: 12, padding: 10, borderRadius: 6,
                background: t.codeBg || '#081220', fontSize: 11,
                fontFamily: 'monospace', color: t.dim || '#64748b',
                lineHeight: 1.8,
              }}>
                <div style={{ color: '#f59e0b', marginBottom: 4 }}># Para ejecutar en AWS:</div>
                <div>aws s3 cp spark_job.py s3://bnx-e2e-test/scripts/spark_job.py</div>
                <div>aws s3 cp glue_job.py s3://bnx-e2e-test/scripts/glue_job.py</div>
                <div style={{ marginTop: 4 }}>aws glue start-job-run --job-name bnx-convertidor-test-spark-prod</div>
                <div>aws glue start-job-run --job-name bnx-convertidor-test-glue-prod</div>
                <div style={{ marginTop: 4, color: '#22c55e' }}># O ejecutar el pipeline completo:</div>
                <div>aws stepfunctions start-execution \</div>
                <div>  --state-machine-arn arn:aws:states:us-east-1:034711235858:stateMachine:bnx-convertidor-e2e-pipeline-prod</div>
              </div>
            </div>
          )}

          {/* Terraform info */}
          <div style={{
            ...card,
            borderLeft: `3px solid #6366f1`,
          }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: '#6366f1', marginBottom: 8 }}>
              Infraestructura (Terraform)
            </h3>
            <div style={{ fontSize: 12, color: t.dim || '#64748b', lineHeight: 1.8 }}>
              <div>El pipeline completo se despliega con:</div>
              <div style={{ fontFamily: 'monospace', marginTop: 6, color: t.muted || '#94a3b8' }}>
                cd terraform && terraform apply
              </div>
              <div style={{ marginTop: 8 }}>Recursos creados:</div>
              <div style={{ marginTop: 4 }}>
                • <span style={{ color: '#22c55e' }}>S3</span> Landing → Bronze → Gold (Medallion)
              </div>
              <div>• <span style={{ color: '#f59e0b' }}>Lambda</span> Pipeline trigger (detecta .mp nuevo)</div>
              <div>• <span style={{ color: '#6366f1' }}>Glue</span> Jobs Spark + Glue + Validate</div>
              <div>• <span style={{ color: '#a855f7' }}>Step Functions</span> Orquestacion E2E</div>
              <div>• <span style={{ color: '#ef4444' }}>CloudWatch</span> Dashboard + Alarmas</div>
              <div>• <span style={{ color: '#06b6d4' }}>SNS</span> Notificaciones email</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
