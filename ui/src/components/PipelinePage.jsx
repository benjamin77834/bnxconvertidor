import { useState, useRef, useEffect } from 'react'
import { COMPILE_URL } from '../config'

const PIPELINE_STEPS = [
  { id: 'load', label: '1. Cargar Codigo', icon: '📄', desc: 'Leer codigo del Compiler o subir .py' },
  { id: 'upload_s3', label: '2. Upload a S3', icon: '📤', desc: 'Subir script a s3://bnx-e2e-test/scripts/' },
  { id: 'create_job', label: '3. Crear/Actualizar Job', icon: '⚙️', desc: 'Crear o actualizar el Glue job' },
  { id: 'run_job', label: '4. Ejecutar Job', icon: '🚀', desc: 'Iniciar el Glue job en AWS' },
  { id: 'wait', label: '5. Esperar resultado', icon: '⏳', desc: 'Polling hasta SUCCEEDED o FAILED' },
  { id: 'validate', label: '6. Validar output', icon: '✅', desc: 'Verificar que el output sea correcto' },
  { id: 'notify', label: '7. Notificar', icon: '📧', desc: 'Resultado final del pipeline' },
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

  // Config
  const [bucket, setBucket] = useState('bnx-e2e-test')
  const [region, setRegion] = useState('us-east-1')
  const [jobName, setJobName] = useState('bnx-e2e-testg1')
  const [role, setRole] = useState('arn:aws:iam::034711235858:role/lambdarol')

  // Si viene codigo del Compiler, precargarlo
  useEffect(() => {
    if (compiledCode && !code) {
      setCode(compiledCode)
      setCodeSource(`Compiler (target=${compiledTarget || 'glue'})`)
      setCodeTarget(compiledTarget || 'glue')
    }
  }, [compiledCode, compiledTarget])

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

  // Cargar desde Compiler
  const loadFromCompiler = () => {
    if (compiledCode) {
      setCode(compiledCode)
      setCodeSource(`Compiler (target=${compiledTarget || 'glue'})`)
      setCodeTarget(compiledTarget || 'glue')
      addLog(`Codigo cargado desde Compiler: ${compiledCode.split('\n').length} lineas (${compiledTarget})`)
      setStep('load', 'done')
    } else {
      addLog('ERROR: No hay codigo compilado. Ve a Compiler primero y compila un grafo.')
      setStep('load', 'error')
    }
  }

  // Subir archivo .py
  const loadFromFile = (file) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target.result
      setCode(content)
      setCodeSource(`Archivo: ${file.name}`)
      // Detectar target por contenido
      if (content.includes('GlueContext') || content.includes('glueContext')) {
        setCodeTarget('glue')
      } else {
        setCodeTarget('spark')
      }
      addLog(`Archivo cargado: ${file.name} (${content.split('\n').length} lineas)`)
      setStep('load', 'done')
    }
    reader.readAsText(file)
  }

  // Pegar codigo directo
  const loadFromPaste = () => {
    if (code.trim()) {
      setCodeSource('Manual (pegado)')
      if (code.includes('GlueContext')) setCodeTarget('glue')
      addLog(`Codigo manual: ${code.split('\n').length} lineas`)
      setStep('load', 'done')
    }
  }

  // Generar el shell script para ejecutar
  const generateScript = () => {
    const scriptPath = codeTarget === 'glue' ? 'scripts/glue_job.py' : 'scripts/spark_job.py'
    const finalJobName = jobName || `bnx-test-${codeTarget}`

    return `#!/bin/bash
# BNX Pipeline E2E — Generado desde la UI
# Target: ${codeTarget}
# Fuente: ${codeSource}
# Fecha: ${new Date().toISOString()}

BUCKET="${bucket}"
REGION="${region}"
ROLE="${role}"
JOB_NAME="${finalJobName}"

echo "═══════════════════════════════════════"
echo " BNX Pipeline E2E (${codeTarget})"
echo "═══════════════════════════════════════"

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
echo "[2/6] Uploading script to S3..."
aws s3 cp ./generated_${codeTarget}_job.py s3://$BUCKET/${scriptPath}

# Step 3: Create or update Glue job
echo "[3/6] Creating/updating Glue job..."
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
echo "[4/6] Running Glue job..."
RUN_ID=$(aws glue start-job-run --job-name $JOB_NAME --region $REGION --query 'JobRunId' --output text)
echo "  Run ID: $RUN_ID"

# Step 5: Wait
echo "[5/6] Waiting for job to complete..."
while true; do
  STATUS=$(aws glue get-job-run --job-name $JOB_NAME --run-id $RUN_ID --region $REGION --query 'JobRun.JobRunState' --output text)
  echo "  Status: $STATUS"
  if [ "$STATUS" = "SUCCEEDED" ]; then
    echo "[ok] Job completed successfully!"
    break
  elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "STOPPED" ]; then
    echo "[!!] Job FAILED!"
    aws glue get-job-run --job-name $JOB_NAME --run-id $RUN_ID --region $REGION --query 'JobRun.ErrorMessage' --output text
    exit 1
  fi
  sleep 15
done

# Step 6: Validate output
echo "[6/6] Checking output..."
aws s3 ls s3://$BUCKET/output/ --recursive
echo ""
echo "═══════════════════════════════════════"
echo " PIPELINE COMPLETE"
echo "═══════════════════════════════════════"
`
  }

  const download = (content, filename) => {
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
  }

  const stepColor = (status) => {
    if (status === 'done') return '#22c55e'
    if (status === 'running') return '#f59e0b'
    if (status === 'error') return '#ef4444'
    if (status === 'info') return '#6366f1'
    return t.dim || '#64748b'
  }

  const stepIcon = (status) => {
    if (status === 'done') return '[ok]'
    if (status === 'running') return '[>>]'
    if (status === 'error') return '[!!]'
    if (status === 'info') return '[i]'
    return '[ ]'
  }

  return (
    <div style={{ padding: 32, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: t.text || '#e2e8f0', margin: 0 }}>
          Pipeline E2E — Pruebas de Ejecucion
        </h2>
        <p style={{ fontSize: 14, color: t.dim || '#64748b', marginTop: 4 }}>
          Toma el codigo generado por BNX Compiler (o sube un .py) y lo ejecuta en AWS Glue para validar
        </p>
      </div>

      {/* Architecture */}
      <div style={{
        ...card, background: (t.codeBg || '#081220'),
        fontFamily: 'monospace', fontSize: 12, lineHeight: 1.8,
        color: t.muted || '#94a3b8', whiteSpace: 'pre',
      }}>
{`  ┌──────────────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ Compiler genera  │────>│ Pipeline │────>│ AWS Glue │────>│ Validate │
  │ spark/glue code  │     │ sube S3  │     │ ejecuta  │     │  output  │
  └──────────────────┘     └──────────┘     └──────────┘     └──────────┘
         o bien:
  ┌──────────────────┐
  │ Upload .py file  │─────────┘
  └──────────────────┘`}
      </div>

      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        {/* Left: Code Source */}
        <div style={{ flex: '1 1 450px', display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Step 1: Load code */}
          <div style={card}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 12 }}>
              Paso 1: Cargar codigo
            </h3>

            {/* Options */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
              <button
                onClick={loadFromCompiler}
                style={{
                  padding: '10px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                  background: compiledCode ? '#22c55e15' : '#ef444410',
                  border: `1px solid ${compiledCode ? '#22c55e40' : '#ef444430'}`,
                  color: compiledCode ? '#22c55e' : '#ef4444',
                  fontWeight: 600,
                }}
              >
                {compiledCode
                  ? `📋 Usar codigo del Compiler (${compiledTarget}, ${compiledCode.split('\n').length} lineas)`
                  : '⚠️ No hay codigo compilado'}
              </button>

              <button
                onClick={() => fileRef.current.click()}
                style={{
                  padding: '10px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                  background: t.card || '#1e2433',
                  border: `1px dashed ${t.border || '#334155'}`,
                  color: t.muted || '#94a3b8', fontWeight: 500,
                }}
              >
                📂 Subir archivo .py
              </button>
              <input ref={fileRef} type="file" accept=".py" hidden
                onChange={(e) => { if (e.target.files[0]) loadFromFile(e.target.files[0]); e.target.value = '' }}
              />

              {code.trim() && !codeSource && (
                <button
                  onClick={loadFromPaste}
                  style={{
                    padding: '10px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                    background: '#6366f115', border: '1px solid #6366f130',
                    color: '#6366f1', fontWeight: 500,
                  }}
                >
                  ✏️ Usar codigo pegado
                </button>
              )}
            </div>

            {/* Status */}
            {codeSource && (
              <div style={{
                padding: '8px 12px', borderRadius: 6, marginBottom: 12,
                background: '#22c55e10', border: '1px solid #22c55e30',
                display: 'flex', alignItems: 'center', gap: 8,
              }}>
                <span style={{ color: '#22c55e', fontWeight: 700, fontSize: 13 }}>[ok]</span>
                <span style={{ fontSize: 13, color: t.text || '#e2e8f0' }}>
                  {codeSource} — <span style={{ color: codeTarget === 'spark' ? '#22c55e' : '#6366f1' }}>{codeTarget}</span>
                </span>
                <span style={{ fontSize: 12, color: t.dim || '#64748b' }}>
                  ({code.split('\n').length} lineas)
                </span>
              </div>
            )}

            {/* Code editor/viewer */}
            <div style={{ position: 'relative' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: 12, color: t.dim || '#64748b' }}>
                  {code ? 'Codigo a ejecutar:' : 'Pega codigo aqui o usa las opciones de arriba:'}
                </span>
                {code && (
                  <button onClick={() => setShowCode(!showCode)} style={{
                    padding: '3px 8px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
                    background: 'transparent', border: `1px solid ${t.border || '#334155'}`,
                    color: t.dim || '#64748b',
                  }}>{showCode ? 'Ocultar' : 'Ver codigo'}</button>
                )}
              </div>
              {(!code || showCode) && (
                <textarea
                  value={code}
                  onChange={e => { setCode(e.target.value); setCodeSource('') }}
                  placeholder="Pega aqui el codigo PySpark o Glue generado..."
                  style={{
                    width: '100%', minHeight: code ? 200 : 80, padding: 10, borderRadius: 8,
                    background: t.codeBg || '#081220',
                    border: `1px solid ${codeTarget === 'spark' ? '#22c55e40' : '#6366f140'}`,
                    color: codeTarget === 'spark' ? '#22c55e' : '#6366f1',
                    fontSize: 12, fontFamily: 'monospace', lineHeight: 1.5,
                    resize: 'vertical', outline: 'none',
                  }}
                />
              )}
            </div>
          </div>

          {/* Config */}
          <div style={card}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 12 }}>
              Configuracion AWS
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              {[
                { label: 'S3 Bucket', value: bucket, set: setBucket },
                { label: 'Region', value: region, set: setRegion },
                { label: 'Job Name', value: jobName, set: setJobName },
                { label: 'Glue Role ARN', value: role, set: setRole },
              ].map(f => (
                <div key={f.label}>
                  <div style={{ fontSize: 11, color: t.dim || '#64748b', marginBottom: 4 }}>{f.label}</div>
                  <input
                    value={f.value}
                    onChange={e => f.set(e.target.value)}
                    style={{
                      width: '100%', padding: '6px 10px', borderRadius: 6, fontSize: 12,
                      background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
                      color: t.text || '#e2e8f0', fontFamily: 'monospace', outline: 'none',
                    }}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button
              onClick={() => {
                if (!code.trim()) return
                download(code, `generated_${codeTarget}_job.py`)
                addLog(`Descargado: generated_${codeTarget}_job.py`)
              }}
              disabled={!code.trim()}
              style={{
                padding: '12px 20px', borderRadius: 8, cursor: code.trim() ? 'pointer' : 'not-allowed',
                background: '#6366f115', border: '1px solid #6366f130',
                color: code.trim() ? '#6366f1' : '#64748b', fontSize: 13, fontWeight: 600,
              }}
            >
              📥 Descargar .py
            </button>

            <button
              onClick={() => {
                if (!code.trim()) return
                const script = generateScript()
                download(script, `run_pipeline_${codeTarget}.sh`)
                addLog(`Script descargado: run_pipeline_${codeTarget}.sh`)
                setStep('load', 'done')
                setStep('upload_s3', 'info')
                setStep('create_job', 'info')
                setStep('run_job', 'info')
                setStep('wait', 'info')
                setStep('validate', 'info')
                setStep('notify', 'info')
              }}
              disabled={!code.trim()}
              style={{
                padding: '12px 20px', borderRadius: 8, cursor: code.trim() ? 'pointer' : 'not-allowed',
                background: code.trim() ? '#22c55e' : '#334155',
                color: code.trim() ? '#000' : '#64748b',
                border: 'none', fontSize: 13, fontWeight: 700,
              }}
            >
              📦 Generar Script de Ejecucion (.sh)
            </button>

            <button
              onClick={() => {
                if (!code.trim()) return
                // Copy aws commands to clipboard
                const cmds = [
                  `# Subir script a S3`,
                  `aws s3 cp ./generated_${codeTarget}_job.py s3://${bucket}/scripts/${codeTarget}_job.py`,
                  ``,
                  `# Ejecutar Glue job`,
                  `aws glue start-job-run --job-name ${jobName} --region ${region}`,
                ].join('\n')
                navigator.clipboard.writeText(cmds)
                addLog('Comandos AWS copiados al clipboard')
              }}
              disabled={!code.trim()}
              style={{
                padding: '12px 20px', borderRadius: 8, cursor: code.trim() ? 'pointer' : 'not-allowed',
                background: '#f59e0b15', border: '1px solid #f59e0b30',
                color: code.trim() ? '#f59e0b' : '#64748b', fontSize: 13, fontWeight: 600,
              }}
            >
              📋 Copiar comandos AWS
            </button>
          </div>
        </div>

        {/* Right: Pipeline status */}
        <div style={{ flex: '1 1 320px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Pipeline Steps */}
          <div style={card}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', marginBottom: 12 }}>
              Pipeline Steps
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
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
                      fontFamily: 'monospace', fontWeight: 700, fontSize: 11,
                      color: stepColor(status), minWidth: 32,
                    }}>
                      {stepIcon(status)}
                    </span>
                    <span style={{ fontSize: 15 }}>{step.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 12, fontWeight: 500, color: t.text || '#e2e8f0' }}>
                        {step.label}
                      </div>
                      <div style={{ fontSize: 10, color: t.dim || '#64748b' }}>{step.desc}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Logs */}
          {logs.length > 0 && (
            <div style={card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <h3 style={{ fontSize: 15, fontWeight: 600, color: t.text || '#e2e8f0', margin: 0 }}>Logs</h3>
                <button onClick={() => setLogs([])} style={{
                  padding: '2px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                  background: 'transparent', border: `1px solid ${t.border || '#334155'}`,
                  color: t.dim || '#64748b',
                }}>Limpiar</button>
              </div>
              <div style={{
                maxHeight: 180, overflowY: 'auto', padding: 10, borderRadius: 6,
                background: t.codeBg || '#081220', fontFamily: 'monospace', fontSize: 11, lineHeight: 1.8,
              }}>
                {logs.map((log, i) => (
                  <div key={i} style={{
                    color: log.includes('ERROR') ? '#ef4444'
                         : log.includes('[ok]') ? '#22c55e'
                         : (t.muted || '#94a3b8'),
                  }}>{log}</div>
                ))}
              </div>
            </div>
          )}

          {/* Quick reference */}
          <div style={{ ...card, borderLeft: '3px solid #6366f1' }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: '#6366f1', marginBottom: 8 }}>
              Flujo de trabajo
            </h3>
            <div style={{ fontSize: 12, color: t.dim || '#64748b', lineHeight: 1.8 }}>
              <div><span style={{ color: '#22c55e' }}>1.</span> Ve a <strong>Compiler</strong> y compila un grafo</div>
              <div><span style={{ color: '#22c55e' }}>2.</span> Ven a <strong>Pipeline</strong> — el codigo ya esta cargado</div>
              <div><span style={{ color: '#22c55e' }}>3.</span> Click <strong>"Generar Script"</strong> para obtener el .sh</div>
              <div><span style={{ color: '#22c55e' }}>4.</span> Ejecuta el script en tu terminal con AWS CLI</div>
              <div style={{ marginTop: 8, color: t.muted || '#94a3b8' }}>
                O sube un .py cualquiera para probarlo en Glue.
              </div>
            </div>
          </div>

          {/* Terraform deploy info */}
          <div style={{ ...card, borderLeft: '3px solid #f59e0b' }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: '#f59e0b', marginBottom: 8 }}>
              Pipeline automatizado (Terraform)
            </h3>
            <div style={{ fontSize: 12, color: t.dim || '#64748b', lineHeight: 1.8 }}>
              <div>Con <code style={{ color: '#f59e0b' }}>terraform apply</code> se despliega:</div>
              <div style={{ marginTop: 4 }}>
                • Lambda trigger (detecta .mp en S3 Landing)
              </div>
              <div>• Glue jobs (Spark + Glue + Validate)</div>
              <div>• Step Functions (orquestacion completa)</div>
              <div>• EventBridge (ejecucion diaria opcional)</div>
              <div style={{ marginTop: 8, fontFamily: 'monospace', fontSize: 11, color: t.muted || '#94a3b8' }}>
                cd terraform && terraform apply
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
