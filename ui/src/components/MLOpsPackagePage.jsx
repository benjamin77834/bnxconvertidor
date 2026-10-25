import { useState, useEffect } from 'react'
import { COMPILE_URL } from '../config'

// Seccion "Framework MLOps v2": genera un PAQUETE NUEVO y mejorado del framework
// (sin tocar el del banco) y lo empaqueta en un ZIP con entorno virtual (run.sh
// crea el venv + instala + prueba), ejemplos y pruebas reales.
const API_BASE = COMPILE_URL.replace(/\/compile$/, '')
const MANIFEST_URL = `${API_BASE}/mlops/package/manifest`
const DOWNLOAD_URL = (bank) => `${API_BASE}/mlops/package/download?bank=${bank ? 1 : 0}`

export default function MLOpsPackagePage({ theme }) {
  const t = theme || {}
  const [manifest, setManifest] = useState(null)
  const [bankLibs, setBankLibs] = useState(true)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(MANIFEST_URL)
      .then(r => r.json())
      .then(d => setManifest(d))
      .catch(() => setManifest(null))
      .finally(() => setLoading(false))
  }, [])

  const card = {
    background: t.card || '#0f172a', border: `1px solid ${t.border || '#334155'}`,
    borderRadius: 10, padding: 16,
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 16, width: '100%', boxSizing: 'border-box' }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 22, color: t.text || '#e2e8f0' }}>📦 Framework MLOps v2 (mejorado)</h2>
        <p style={{ margin: '4px 0 0', fontSize: 13, color: t.muted || '#94a3b8', maxWidth: 900 }}>
          Genera un <b>paquete nuevo</b> del framework que corrige los problemas detectados (ver el diagnóstico
          en la sección anterior), <b>sin tocar el código del banco</b>. Trae un <b>entorno virtual reproducible</b>
          (como Data Sintética): <code>run.sh</code> crea el venv, instala todo y corre las pruebas.
        </p>
      </div>

      {loading && <div style={{ ...card, fontSize: 13, color: t.muted }}>Cargando…</div>}

      {manifest && (
        <>
          {/* Mejoras: antes -> ahora */}
          <div style={{ ...card }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: t.text || '#e2e8f0', marginBottom: 10 }}>
              ✨ Qué mejora respecto al framework actual
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {(manifest.improvements || []).map((im, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12.5, flexWrap: 'wrap' }}>
                  <span style={{
                    color: '#f87171', textDecoration: 'line-through', background: '#ef444412',
                    padding: '3px 8px', borderRadius: 6, border: '1px solid #ef444430',
                  }}>{im.from}</span>
                  <span style={{ color: t.dim || '#64748b' }}>→</span>
                  <span style={{
                    color: '#22c55e', background: '#22c55e12',
                    padding: '3px 8px', borderRadius: 6, border: '1px solid #22c55e30',
                  }}>{im.to}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'start' }}>
            {/* Árbol del paquete */}
            <div style={{ ...card, minWidth: 0 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: t.text || '#e2e8f0', marginBottom: 10 }}>
                📂 Qué incluye el paquete
              </div>
              <pre style={{
                margin: 0, padding: 12, borderRadius: 8, overflowX: 'auto',
                background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
                color: '#c4b5fd', fontFamily: 'monospace', fontSize: 12, lineHeight: 1.6,
              }}>{(manifest.tree || []).join('\n')}</pre>
            </div>

            {/* Generar / descargar */}
            <div style={{ ...card, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: t.text || '#e2e8f0' }}>
                ⬇️ Generar el paquete
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12.5, color: t.text || '#e2e8f0', cursor: 'pointer' }}>
                <input type="checkbox" checked={bankLibs} onChange={e => setBankLibs(e.target.checked)} />
                Incluir marcadores de librerías internas del banco (toolbox, lib_mkop_metrics, mex-lib*) en requirements.txt
              </label>
              <p style={{ margin: 0, fontSize: 11.5, color: t.muted || '#94a3b8' }}>
                {bankLibs
                  ? 'El requirements.txt incluirá las libs del banco comentadas, listas para descomentar y apuntar a tu Artifactory interno.'
                  : 'Solo dependencias open source (PySpark, pandas, pytest). Corre en cualquier máquina sin la red del banco.'}
              </p>
              <a href={DOWNLOAD_URL(bankLibs)} download
                style={{
                  display: 'inline-block', textDecoration: 'none', textAlign: 'center',
                  padding: '12px 20px', borderRadius: 8, fontSize: 14, fontWeight: 700,
                  background: t.accent || '#6366f1', color: '#fff',
                }}>
                📦 Descargar framework_mlops_v2.zip
              </a>
              <div style={{ fontSize: 11.5, color: t.muted || '#94a3b8', lineHeight: 1.6 }}>
                Después de descargar y descomprimir:
                <pre style={{
                  margin: '6px 0 0', padding: 10, borderRadius: 6,
                  background: t.codeBg || '#081220', border: `1px solid ${t.border || '#334155'}`,
                  color: '#22c55e', fontFamily: 'monospace', fontSize: 11.5,
                }}>{'cd framework_mlops_v2_pkg\nbash run.sh'}</pre>
                Crea <code>.venv</code>, instala dependencias y corre las pruebas.
              </div>
            </div>
          </div>

          <div style={{ ...card, fontSize: 12, color: t.muted || '#94a3b8', borderColor: '#38bdf855' }}>
            <b style={{ color: '#38bdf8' }}>Nota honesta:</b> este paquete es una reimplementación limpia del
            andamiaje (clase base, validaciones, router, tests) — <b>no copia el código propietario del banco</b>.
            La lógica de negocio específica de cada fuente (buró, PnL, etc.) la portas tú sobre esta base, o la
            conviertes desde pandas en la sección "🧬 Framework MLOps". Las dependencias de Cloudera/Artifactory
            se resuelven en la red del banco vía <code>requirements.txt</code>.
          </div>
        </>
      )}
    </div>
  )
}
