import { useState, useRef, useEffect } from 'react'
import { COMPILE_URL } from '../config'

const PIPELINE_STEPS = [
  { id: 'load', label: '1. Cargar Codigo', icon: '📄' },
  { id: 'upload_s3', label: '2. Upload a S3', icon: '📤' },
  { id: 'create_job', label: '3. Crear/Actualizar Job', icon: '⚙️' },
  { id: 'run_job', label: '4. Ejecutar Job', icon: '🚀' },
  { id: 'wait', label: '5. Esperar resultado', icon: '⏳' },
  { id: 'validate', label: '6. Resultado', icon: '✅' },
]

export default function PipelinePage({ theme, compiledCode, compiledTarget }) {
  const t = theme || {}
  const fileRef = useRef(null)
  const [code, setCode] = useState('')
  const [codeSource, setCodeSource] = useState('')
  const [codeTarget, setCodeTarget] = useState('spark')
  const [stepStatus, setStepStatus] = useState({})
  const [logs, setLogs] = useState([])
  const [showCode, setShowCode] = useState(false)
  const [running, setRunning] = useState(false)
  const [polling, setPolling] = useState(false)
  const [runId, setRunId] = useState('')
  const [jobName, setJobName] = useState('bnx-e2e-pipeline-ui')
  const pollingRef = useRef(null)

  // Config
  const [bucket, setBucket] = useState('bnx-e2e-test')
  const [region, setRegion] = useState('us-east-1')
  const [role, setRole] = useState('arn:aws:iam::034711235858:role/lambdarol')

  // Si viene codigo del Compiler, precargarlo
  useEffect(() => {
    if (compiledCode && !code) {
      setCode(compiledCode)
      setCodeSource(`Compiler (target=${compiledTarget || 'glue'})`)
      setCodeTarget(compiledTarget || 'glue')
    }
  }, [compiledCode, compiledTarget])

  // Cleanup polling on unmount
  useEffect(() => {
    return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
  }, [])

  const card = {
    background: t.card || '#1e2433', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 20,
  }

  const addLog = (msg) => setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`])
  const setStep = (id, status, detail) => setStepStatus(prev => ({ ...prev, [id]: { status, detail } }))

  // --- OPCION 1: Ejecutar directo en AWS desde UI ---
  const executeInAWS = async () => {
    if (!code.trim()) return
    setRunning(true)
    setStepStatus({})
    setLogs([])
    setRunId('')

    setStep('load', 'done', codeSource || 'Manual')
    addLog(`Codigo listo: ${code.split('\n').length} lineas (${codeTarget})`)

    addLog('Enviando a AWS via Lambda /pipeline...')
    setStep('upload_s3', 'running')
    setStep('create_job', 'running')
    setStep('run_job', 'running')

    try {
      const form = new FormData()
      form.append('code', code)
      form.append('target', codeTarget)
      form.append('bucket', bucket)
      form.append('region', region)
      form.append('job_name', jobName)
      form.append('role', role)
      form.append('action', 'run')

      const res = await fetch(COMPILE_URL.replace('/compile', '/pipeline'), { method: 'POST', body: form })
      const data = await res.json()

      // Procesar pasos
      for (const step of (data.steps || [])) {
        setStep(step.step, step.status, step.detail || '')
        addLog(`${step.step}: ${step.status} — ${step.detail || ''}`)
      }

      if (data.status === 'started' && data.run_id) {
        setRunId(data.run_id)
        setJobName(data.job_name || jobName)
        addLog(`Job iniciado! RunId: ${data.run_id}`)
        setStep('wait', 'running', 'Polling status...')
        startPolling(data.job_name || jobName, data.run_id)
      } else if (data.status === 'failed') {
        addLog('Pipeline FALLO en la preparacion')
        setStep('validate', 'error', 'Fallo antes de ejecutar')
        setRunning(false)
      }
    } catch (e) {
      addLog(`ERROR de red: ${e.message}`)
      setStep('upload_s3', 'error', e.message)
      setRunning(false)
    }
  }

  // Polling para verificar status del job
  const startPolling = (jn, rid) => {
    setPolling(true)
    let attempts = 0
    pollingRef.current = setInterval(async () => {
      attempts++
      try {
        const form = new FormData()
        form.append('job_name', jn)
        form.append('run_id', rid)
        form.append('region', region)

        const res = await fetch(COMPILE_URL.replace('/compile', '/pipeline/status'), { method: 'POST', body: form })
        const data = await res.json()

        addLog(`[${attempts}] Status: ${data.status}${data.duration ? ` (${data.duration}s)` : ''}`)

        if (data.status === 'SUCCEEDED') {
          setStep('wait', 'done', `${data.duration}s`)
          setStep('validate', 'done', 'Job completado exitosamente!')
          addLog(`JOB EXITOSO en ${data.duration}s`)
          clearInterval(pollingRef.current)
          setPolling(false)
          setRunning(false)
        } else if (data.status === 'FAILED' || data.status === 'STOPPED') {
          setStep('wait', 'error', data.error || data.status)
          setStep('validate', 'error', data.error || 'Job fallo')
          addLog(`JOB FALLO: ${data.error || data.status}`)
          clearInterval(pollingRef.current)
          setPolling(false)
          setRunning(false)
        } else if (attempts > 40) {
          addLog('TIMEOUT: 10 min sin completar, deteniendo polling')
          clearInterval(pollingRef.current)
          setPolling(false)
          setRunning(false)
        }
      } catch (e) {
        addLog(`Error polling: ${e.message}`)
      }
    }, 15000) // cada 15 segundos
  }

  // --- OPCION 2: Generar script para ejecutar manual ---
  const generateScript = () => {
    const scriptPath = `scripts/${codeTarget}_job.py`
    return `#!/bin/bash
# BNX Pipeline E2E — Generado desde UI
# Target: ${codeTarget} | Fuente: ${codeSource}
# Fecha: ${new Date().toISOString()}

BUCKET="${bucket}"
REGION="${region}"
ROLE="${role}"
JOB_NAME="${jobName}"

echo "BNX Pipeline E2E (${codeTarget})"
echo "========================="

# Step 1: Upload test data
echo "[1/6] Uploading test data..."
cat << 'EOF' | aws s3 cp - s3://$BUCKET/raw/orders/data.csv
id,nombre,monto
1,juan perez,150.50
2,maria gomez,300.5
3,carlos lopez,75.25
4,ana martinez,200.0
5,luis rodriguez,120.25
6,juan perez,50.0
7,maria gomez,100.0
EOF

# Step 2: Upload script
echo "[2/6] Uploading script..."
aws s3 cp ./generated_${codeTarget}_job.py s3://$BUCKET/${scriptPath}

# Step 3: Create/update Glue job
echo "[3/6] Creating Glue job..."
aws glue create-job --name $JOB_NAME \\
  --role $ROLE \\
  --command '{"Name":"glueetl","ScriptLocation":"s3://'$BUCKET'/${scriptPath}","PythonVersion":"3"}' \\
  --default-arguments '{"--job-language":"python","--TempDir":"s3://'$BUCKET'/temp/"}' \\
  --glue-version "4.0" --number-of-workers 2 --worker-type "G.1X" \\
  --region $REGION 2>/dev/null || \\
aws glue update-job --job-name $JOB_NAME \\
  --job-update '{"Role":"'$ROLE'","Command":{"Name":"glueetl","ScriptLocation":"s3://'$BUCKET'/${scriptPath}","PythonVersion":"3"},"DefaultArguments":{"--job-language":"python","--TempDir":"s3://'$BUCKET'/temp/"},"GlueVersion":"4.0","NumberOfWorkers":2,"WorkerType":"G.1X"}' \\
  --region $REGION

# Step 4: Run job
echo "[4/6] Running job..."
RUN_ID=$(aws glue start-job-run --job-name $JOB_NAME --region $REGION --query 'JobRunId' --output text)
echo "  Run ID: $RUN_ID"

# Step 5: Wait
echo "[5/6] Waiting..."
while true; do
  STATUS=$(aws glue get-job-run --job-name $JOB_NAME --run-id $RUN_ID --region $REGION --query 'JobRun.JobRunState' --output text)
  echo "  Status: $STATUS"
  if [ "$STATUS" = "SUCCEEDED" ]; then echo "[ok] Success!"; break; fi
  if [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "STOPPED" ]; then
    echo "[!!] FAILED"; aws glue get-job-run --job-name $JOB_NAME --run-id $RUN_ID --region $REGION --query 'JobRun.ErrorMessage' --output text; exit 1
  fi
  sleep 15
done

# Step 6: Check output
echo "[6/6] Output:"
aws s3 ls s3://$BUCKET/output/ --recursive
echo "DONE"
`
  }

  // Helpers
  const loadFromCompiler = () => {
    if (compiledCode) {
      setCode(compiledCode)
      setCodeSource(`Compiler (${compiledTarget})`)
      setCodeTarget(compiledTarget || 'glue')
      setStep('load', 'done', `${compiledCode.split('\n').length} lineas`)
      addLog(`Codigo cargado del Compiler: ${compiledCode.split('\n').length} lineas (${compiledTarget})`)
    } else {
      addLog('No hay codigo compilado — ve a Compiler primero')
      setStep('load', 'error', 'Sin codigo')
    }
  }

  const loadFromFile = (file) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target.result
      setCode(content)
      setCodeSource(`Archivo: ${file.name}`)
      setCodeTarget(content.includes('GlueContext') ? 'glue' : 'spark')
      setStep('load', 'done', `${file.name} (${content.split('\n').length} lineas)`)
      addLog(`Archivo cargado: ${file.name}`)
    }
    reader.readAsText(file)
  }

  const download = (content, filename) => {
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
  }

  const stepColor = (s) => {
    if (!s) return t.dim || '#64748b'
    if (s.status === 'done') return '#22c55e'
    if (s.status === 'running') return '#f59e0b'
    if (s.status === 'error') return '#ef4444'
    if (s.status === 'info') return '#6366f1'
    return t.dim || '#64748b'
  }

  const stepIcon = (s) => {
    if (!s) return '[ ]'
    if (s.status === 'done') return '[ok]'
    if (s.status === 'running') return '[>>]'
    if (s.status === 'error') return '[!!]'
    if (s.status === 'info') return '[i]'
    return '[ ]'
  }

  return (
    <div style={{ padding: 32, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: t.text || '#e2e8f0', margin: 0 }}>
          Pipeline E2E — Ejecutar en AWS
        </h2>
        <p style={{ fontSize: 14, color: t.dim || '#64748b', marginTop: 4 }}>
          Ejecuta codigo generado (o subido) directamente en AWS Glue desde esta interfaz
        </p>
      </div>

      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        {/* Left: Code + Actions */}
        <div style={{ flex: '1 1 450px', display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Load code */}
          <div style={card}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 12 }}>
              Codigo a ejecutar
            </h3>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
              <button onClick={loadFromCompiler} style={{
                padding: '8px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 12,
                background: compiledCode ? '#22c55e15' : '#ef444410',
                border: `1px solid ${compiledCode ? '#22c55e40' : '#ef444430'}`,
                color: compiledCode ? '#22c55e' : '#ef4444', fontWeight: 600,
              }}>
                {compiledCode ? `📋 Del Compiler (${compiledTarget}, ${compiledCode.split('\n').length}L)` : '⚠️ Sin codigo compilado'}
              </button>
              <button onClick={() => fileRef.current.click()} style={{
                padding: '8px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 12,
                background: t.card || '#1e2433', border: `1px dashed ${t.border || '#334155'}`,
                color: t.muted || '#94a3b8',
              }}>📂 Subir .py</button>
              <input ref={fileRef} type="file" accept=".py" hidden
                onChange={(e) => { if (e.target.files[0]) loadFromFile(e.target.files[0]); e.target.value = '' }}
              />
            </div>

            {codeSource && (
              <div style={{
                padding: '6px 10px', borderRadius: 6, marginBottom: 10,
                background: '#22c55e10', border: '1px solid #22c55e30',
                fontSize: 12, color: '#22c55e', display: 'flex', alignItems: 'center', gap: 8,
              }}>
                <span style={{ fontWeight: 700 }}>[ok]</span>
                <span>{codeSource}</span>
                <span style={{ color: t.dim || '#64748b' }}>({code.split('\n').length}L)</span>
              </div>
            )}

            <textarea
              value={code}
              onChange={e => { setCode(e.target.value); if (!codeSource) setCodeSource('') }}
              placeholder="Pega codigo PySpark/Glue aqui, o usa los botones de arriba..."
              style={{
                width: '100%', minHeight: showCode ? 200 : 60, padding: 10, borderRadius: 8,
                background: t.codeBg || '#081220',
                border: `1px solid ${codeTarget === 'spark' ? '#22c55e40' : '#6366f140'}`,
                color: codeTarget === 'spark' ? '#22c55e' : '#6366f1',
                fontSize: 11, fontFamily: 'monospace', lineHeight: 1.5,
                resize: 'vertical', outline: 'none',
                display: showCode || !code ? 'block' : 'none',
              }}
            />
            {code && !showCode && (
              <button onClick={() => setShowCode(true)} style={{
                fontSize: 11, color: t.dim || '#64748b', background: 'none', border: 'none',
                cursor: 'pointer', textDecoration: 'underline',
              }}>Mostrar codigo ({code.split('\n').length} lineas)</button>
            )}
            {showCode && code && (
              <button onClick={() => setShowCode(false)} style={{
                fontSize: 11, color: t.dim || '#64748b', background: 'none', border: 'none',
                cursor: 'pointer', textDecoration: 'underline', marginTop: 4,
              }}>Ocultar</button>
            )}
          </div>

          {/* Config */}
          <div style={card}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 10 }}>
              Config AWS
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { label: 'Bucket', val: bucket, set: setBucket },
                { label: 'Region', val: region, set: setRegion },
                { label: 'Job Name', val: jobName, set: setJobName },
                { label: 'Role ARN', val: role, set: setRole },
              ].map(f => (
                <div key={f.label}>
                  <div style={{ fontSize: 10, color: t.dim || '#64748b', marginBottom: 3 }}>{f.label}</div>
                  <input value={f.val} onChange={e => f.set(e.target.value)} style={{
                    width: '100%', padding: '5px 8px', borderRadius: 6, fontSize: 11,
                    background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
                    color: t.text || '#e2e8f0', fontFamily: 'monospace', outline: 'none',
                  }} />
                </div>
              ))}
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {/* EJECUTAR EN AWS */}
            <button
              onClick={executeInAWS}
              disabled={!code.trim() || running}
              style={{
                flex: 1, padding: '14px 20px', borderRadius: 8,
                cursor: (!code.trim() || running) ? 'not-allowed' : 'pointer',
                background: running ? '#f59e0b' : '#22c55e',
                color: '#000', border: 'none', fontSize: 14, fontWeight: 700,
                minWidth: 200,
              }}
            >
              {running ? (polling ? '⏳ Esperando resultado...' : '⏳ Enviando...') : '🚀 Ejecutar en AWS'}
            </button>

            {/* GENERAR SCRIPT */}
            <button
              onClick={() => {
                if (!code.trim()) return
                download(generateScript(), `run_pipeline_${codeTarget}.sh`)
                download(code, `generated_${codeTarget}_job.py`)
                addLog('Script + codigo descargados')
              }}
              disabled={!code.trim()}
              style={{
                padding: '14px 20px', borderRadius: 8,
                cursor: !code.trim() ? 'not-allowed' : 'pointer',
                background: '#6366f115', border: '1px solid #6366f130',
                color: code.trim() ? '#6366f1' : '#64748b', fontSize: 13, fontWeight: 600,
              }}
            >
              📦 Descargar Script .sh
            </button>
          </div>
        </div>

        {/* Right: Status + Logs */}
        <div style={{ flex: '1 1 320px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Pipeline Steps */}
          <div style={card}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 12 }}>
              Estado del Pipeline
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {PIPELINE_STEPS.map(step => {
                const s = stepStatus[step.id]
                return (
                  <div key={step.id} style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '8px 12px', borderRadius: 6,
                    background: s ? stepColor(s) + '10' : 'transparent',
                    border: `1px solid ${s ? stepColor(s) + '30' : (t.border || '#334155')}`,
                  }}>
                    <span style={{
                      fontFamily: 'monospace', fontWeight: 700, fontSize: 11,
                      color: stepColor(s), minWidth: 32,
                    }}>{stepIcon(s)}</span>
                    <span style={{ fontSize: 14 }}>{step.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 12, fontWeight: 500, color: t.text || '#e2e8f0' }}>{step.label}</div>
                      {s?.detail && <div style={{ fontSize: 10, color: stepColor(s) }}>{s.detail}</div>}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Logs */}
          {logs.length > 0 && (
            <div style={card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', margin: 0 }}>Logs</h3>
                <button onClick={() => setLogs([])} style={{
                  padding: '2px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                  background: 'transparent', border: `1px solid ${t.border || '#334155'}`,
                  color: t.dim || '#64748b',
                }}>Limpiar</button>
              </div>
              <div style={{
                maxHeight: 250, overflowY: 'auto', padding: 10, borderRadius: 6,
                background: t.codeBg || '#081220', fontFamily: 'monospace', fontSize: 11, lineHeight: 1.8,
              }}>
                {logs.map((log, i) => (
                  <div key={i} style={{
                    color: log.includes('ERROR') || log.includes('FALLO') ? '#ef4444'
                         : log.includes('EXITOSO') || log.includes('[ok]') || log.includes('Success') ? '#22c55e'
                         : log.includes('Status:') ? '#f59e0b'
                         : (t.muted || '#94a3b8'),
                  }}>{log}</div>
                ))}
              </div>
            </div>
          )}

          {/* Instructions */}
          <div style={{ ...card, borderLeft: '3px solid #22c55e' }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: '#22c55e', marginBottom: 8 }}>Como usar</h3>
            <div style={{ fontSize: 12, color: t.dim || '#64748b', lineHeight: 1.8 }}>
              <div><strong>Opcion A</strong> — Ejecutar desde aqui:</div>
              <div style={{ paddingLeft: 12 }}>
                1. Compila un grafo en <strong>Compiler</strong><br/>
                2. Ven a <strong>Pipeline</strong> (ya tiene el codigo)<br/>
                3. Click <strong>Ejecutar en AWS</strong><br/>
                4. Espera el resultado (polling cada 15s)
              </div>
              <div style={{ marginTop: 8 }}><strong>Opcion B</strong> — Script manual:</div>
              <div style={{ paddingLeft: 12 }}>
                1. Click <strong>Descargar Script .sh</strong><br/>
                2. Corre en tu terminal: <code>bash run_pipeline.sh</code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
