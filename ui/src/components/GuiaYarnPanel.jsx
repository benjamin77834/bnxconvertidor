import { useState } from 'react'
// Guia "Correr en YARN (cluster)" del paquete Framework MLOps v2 (Cloudera, spark3-submit).
// Comandos verificados contra src/mlops_pkg.py (run.sh, probe_workers.py y main.py del paquete).
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

export default function GuiaYarnPanel({ t, fuente }) {
  const [open, setOpen] = useState(false)
  const src = fuente || '<fuente>'
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
          <p style={p}>Genera el paquete de nuevo desde este portal con destino Python 3.11 y descárgalo. El ZIP incluye <code>probe_workers.py</code> y un <code>run.sh</code> que envía las librerías a los executors.</p>

          <div style={h}>2. Probar qué Python ven los nodos</div>
          <p style={p}>No instala nada ni toca datos. Correr sin exportar <code>PYSPARK_PYTHON</code>.</p>
          <Cmd t={t} texto="spark3-submit --master yarn --deploy-mode client probe_workers.py" />
          <Cmd t={t} texto="spark3-submit --master yarn --deploy-mode client --conf spark.pyspark.python=/usr/bin/python3.11 probe_workers.py" />
          <p style={p}>Si el primero imprime 3.11, todo está listo. Si falla con «different version» y el segundo imprime 3.11, agrega <code>BNX_EXECUTOR_PYTHON=/usr/bin/python3.11</code> al comando del paso 3.</p>

          <div style={h}>3. Correr en modo YARN</div>
          <Cmd t={t} texto={`BNX_SPARK=cluster BNX_DEPS_HDFS=hdfs:///user/<usuario>/bnx/deps bash run.sh --settings <ruta>/bin/settings --env prod --source ${src}`} />
          <ul style={{ ...p, paddingLeft: 18 }}>
            <li>La primera corrida sube el archivo de dependencias (<code>bnxdeps_&lt;hash&gt;.tgz</code>) a HDFS; las siguientes lo reutilizan.</li>
            <li>No se instala nada en los nodos: las librerías viajan con el job.</li>
            <li>Si el Python de los workers no sirve (el probe lo detecta) y las UDF simples (<code>quita_acentos</code>, <code>rmeans</code>, <code>rt_mod</code>, <code>df_mod</code>) se pueden reemplazar, se cambian solas por expresiones nativas de Spark (<code>BNX_UDF_NATIVAS</code>, automático; <code>BNX_UDF_NATIVAS=0</code> lo apaga).</li>
          </ul>

          <div style={h}>4. Limpiar dependencias viejas en HDFS</div>
          <Cmd t={t} texto="BNX_DEPS_HDFS=hdfs:///user/<usuario>/bnx/deps bash run.sh --limpiar-deps-hdfs" />
          <p style={p}>Borra los <code>bnxdeps_*.tgz</code> que no son del entorno actual. Pide confirmación en terminal; sin terminal solo lista (<code>BNX_LIMPIAR_SI=1</code> confirma).</p>

          <div style={h}>5. Qué mandar si falla</div>
          <ul style={{ ...p, paddingLeft: 18 }}>
            <li>La salida completa del paso 2 (los dos comandos).</li>
            <li>El log completo de la corrida de <code>run.sh</code>.</li>
            <li>El <code>application_id</code> de YARN (<code>application_…</code>).</li>
          </ul>
        </div>
      )}
    </div>
  )
}
