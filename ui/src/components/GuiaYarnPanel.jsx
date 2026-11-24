import { useState } from 'react'
// Guia "Correr en YARN (cluster)" del paquete Framework MLOps v2 (Cloudera, spark3-submit).
// Comandos verificados contra src/mlops_pkg.py (run.sh, probe_workers.py y main.py del paquete).
// --source = NOMBRE DEL JOB del banco (rps_datapull...), nunca un archivo (main.py).
// Sin datos del banco: solo placeholders entre < >.

function Cmd({ t, texto }) {
  const [ok, setOk] = useState(false)
  const copiar = () => {
    navigator.clipboard.writeText(texto).then(() => { setOk(true); setTimeout(() => setOk(false), 1500) }).catch(() => {})
  }
  return (
    <div style={{ position: 'relative', margin: '6px 0' }}>
      <pre style={{
        margin: 0, padding: '10px 70px 10px 12px', borderRadius: 6, fontSize: 12, overflowX: 'auto',
        background: '#0b1220', color: '#e2e8f0', border: `1px solid ${t.border || '#334155'}`, whiteSpace: 'pre-wrap', wordBreak: 'break-all',
      }}>{texto}</pre>
      <button onClick={copiar} style={{
        position: 'absolute', top: 6, right: 6, padding: '3px 8px', fontSize: 11, borderRadius: 5, cursor: 'pointer',
        background: 'transparent', color: t.muted || '#94a3b8', border: `1px solid ${t.border || '#334155'}`,
      }}>{ok ? '✓ Copiado' : '📋 Copiar'}</button>
    </div>
  )
}

export default function GuiaYarnPanel({ t, fuentes }) {
  const [open, setOpen] = useState(false)
  const lista = (fuentes || []).filter(n => n && n !== 'main')
  const src = lista[0] || '<job_del_banco>'
  const h = { fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0', marginTop: 12 }
  const p = { fontSize: 12.5, color: t.muted || '#94a3b8', margin: '4px 0', lineHeight: 1.5 }
  return (
    <div style={{ marginTop: 14, borderTop: `1px solid ${t.border || '#334155'}`, paddingTop: 12 }}>
      <button onClick={() => setOpen(o => !o)} style={{
        background: 'none', border: 'none', padding: 0, cursor: 'pointer', fontSize: 13, fontWeight: 700, color: t.text || '#e2e8f0',
      }}>{open ? '▾' : '▸'} 🚀 Correr en YARN (clúster)</button>
      {open && (
        <div style={{ marginTop: 6 }}>
          <p style={p}>Guía para el servidor del banco (RHEL 8, Python 3.11, Cloudera con <code>spark3-submit</code>). Los comandos se ejecutan en el edge node, dentro de la carpeta del paquete.</p>

          <div style={h}>1. Regenerar el paquete (Python 3.11)</div>
          <p style={p}>Genera el paquete de nuevo desde este portal con destino Python 3.11 y descárgalo. El ZIP incluye <code>probe_workers.py</code> y un <code>run.sh</code> que usa el Python de los nodos si ya tiene numpy/pandas (si no, envía las librerías del venv).</p>

          <div style={h}>2. Probar qué Python ven los nodos</div>
          <p style={p}>No instala nada ni toca datos. Correr sin exportar <code>PYSPARK_PYTHON</code>.</p>
          <Cmd t={t} texto="spark3-submit --master yarn --deploy-mode client probe_workers.py" />
          <p style={p}>Al final imprime la línea exacta <code>BNX_EXECUTOR_PYTHON=&lt;ruta&gt;</code> si los nodos ya tienen Python 3.11 con <code>numpy=True</code> y <code>pandas=True</code>. Cópiala tal cual al paso 3. Si los nodos no tienen numpy/pandas, no pongas esa variable: <code>run.sh</code> envía las librerías.</p>
          <p style={p}>Si falla con «different version», prueba con otro Python 3.11 de los nodos:</p>
          <Cmd t={t} texto="spark3-submit --master yarn --deploy-mode client --conf spark.pyspark.python=<ruta_python3.11_de_los_nodos> probe_workers.py" />

          <div style={h}>3. Correr un job del banco en YARN</div>
          <p style={p}><code>--source</code> es el <b>nombre del job</b> del banco, no un archivo ni <code>main</code>. Con <code>--settings</code> y <code>--env</code> corre el job real (sin <code>--source</code> corren todos, el pivote primero).{lista.length > 0 ? ' Jobs de este paquete: ' : ' Los nombres válidos los lista el error si te equivocas.'}{lista.length > 0 && lista.map((n, i) => <span key={n}>{i > 0 ? ', ' : ''}<code>{n}</code></span>)}</p>
          <Cmd t={t} texto={`BNX_EXECUTOR_PYTHON=<ruta_python_de_los_nodos> BNX_SPARK=cluster bash run.sh --settings <ruta>/bin/settings --env prod --source ${src}`} />
          <ul style={{ ...p, paddingLeft: 18 }}>
            <li><code>BNX_EXECUTOR_PYTHON</code> es la línea que imprimió el paso 2. Con ella <code>run.sh</code> usa ese Python en los executors y no envía el venv. Sin ella, <code>run.sh</code> hace el mismo probe y, si los nodos tienen numpy/pandas, también lo usa solo.</li>
            <li>Si los nodos no tienen numpy/pandas: quita esa variable y agrega <code>BNX_DEPS_HDFS=hdfs:///user/&lt;usuario&gt;/bnx/deps</code>. La primera corrida sube las librerías (<code>bnxdeps_&lt;hash&gt;.tgz</code>) a HDFS y las siguientes las reutilizan. No se instala nada en los nodos.</li>
            <li>Si el Python de los workers no sirve y las UDF simples (<code>quita_acentos</code>, <code>rmeans</code>, <code>rt_mod</code>, <code>df_mod</code>) se pueden reemplazar, se cambian solas por expresiones nativas de Spark (<code>BNX_UDF_NATIVAS</code>, automático; <code>BNX_UDF_NATIVAS=0</code> lo apaga).</li>
            <li><code>BNX_DEPS_ENVIAR=1</code> fuerza enviar el venv aunque los nodos ya tengan numpy/pandas.</li>
          </ul>

          <div style={h}>4. Rutas de salida y temporales en HDFS</div>
          <p style={p}>Un job del banco escribe donde dicen sus settings (<code>general_root</code> de <code>jobs.json</code>): esa ruta HDFS debe ser tuya. Para bajar tablas con un <code>--config</code> usa <code>--base-path &lt;ruta HDFS&gt;</code> (o <code>BNX_BASE_PATH</code>). Si ves «SIN PERMISO de escritura», cambia a una ruta donde puedas escribir. Los temporales del modo DEMO (sin <code>--source</code> de un job) usan tu HOME en HDFS (<code>/user/&lt;usuario&gt;/.bnx_tmp</code>), nunca la carpeta del paquete; se cambian con:</p>
          <Cmd t={t} texto="BNX_HDFS_TMP=/user/<usuario>/bnx_tmp BNX_SPARK=cluster bash run.sh" />

          <div style={h}>5. Limpiar dependencias viejas en HDFS</div>
          <Cmd t={t} texto="BNX_DEPS_HDFS=hdfs:///user/<usuario>/bnx/deps bash run.sh --limpiar-deps-hdfs" />
          <p style={p}>Borra los <code>bnxdeps_*.tgz</code> que no son del entorno actual. Pide confirmación en terminal; sin terminal solo lista (<code>BNX_LIMPIAR_SI=1</code> confirma).</p>

          <div style={h}>6. Qué mandar si falla</div>
          <ul style={{ ...p, paddingLeft: 18 }}>
            <li>La salida completa del paso 2.</li>
            <li>El log completo de la corrida de <code>run.sh</code>.</li>
            <li>El <code>application_id</code> de YARN (<code>application_…</code>).</li>
          </ul>
        </div>
      )}
    </div>
  )
}
