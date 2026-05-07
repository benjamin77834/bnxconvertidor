import { useState, useRef, useEffect } from 'react'
import { COMPILE_URL } from '../config'

export default function OcrPage({ theme }) {
  const t = theme || {}
  const [image, setImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [extractedText, setExtractedText] = useState('')
  const [parsed, setParsed] = useState(null)
  const [generatedMp, setGeneratedMp] = useState('')
  const [loading, setLoading] = useState(false)
  const [compiledCode, setCompiledCode] = useState(null)
  const [target, setTarget] = useState('glue')
  const fileRef = useRef(null)

  // Listen for paste events (Cmd+V with image from clipboard)
  useEffect(() => {
    const handlePaste = (e) => {
      const items = e.clipboardData?.items
      if (!items) return
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.startsWith('image/')) {
          e.preventDefault()
          const file = items[i].getAsFile()
          setImage(file)
          const reader = new FileReader()
          reader.onload = (ev) => setImagePreview(ev.target.result)
          reader.readAsDataURL(file)
          break
        }
      }
    }
    document.addEventListener('paste', handlePaste)
    return () => document.removeEventListener('paste', handlePaste)
  }, [])

  const handleImageUpload = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setImage(file)
    const reader = new FileReader()
    reader.onload = (ev) => setImagePreview(ev.target.result)
    reader.readAsDataURL(file)
    e.target.value = ''
  }

  // Paste from clipboard (Cmd+V)
  const handlePaste = (e) => {
    const items = e.clipboardData?.items
    if (!items) return
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.startsWith('image/')) {
        e.preventDefault()
        const file = items[i].getAsFile()
        setImage(file)
        const reader = new FileReader()
        reader.onload = (ev) => setImagePreview(ev.target.result)
        reader.readAsDataURL(file)
        return
      }
    }
  }

  const extractFromImage = async () => {
    if (!image) return
    setLoading(true)
    const form = new FormData()
    form.append('image', image)
    try {
      const res = await fetch(COMPILE_URL.replace('/compile', '/ocr'), { method: 'POST', body: form })
      const data = await res.json()
      if (data.error) {
        setExtractedText(`Error: ${data.error}\n\nTip: ${data.tip || 'Pega el texto directamente abajo'}`)
      } else {
        setExtractedText(data.extracted_text || '')
        setParsed(data.parsed || null)
        setGeneratedMp(data.generated_mp || '')
      }
    } catch (e) {
      setExtractedText(`Error: ${e.message}`)
    } finally { setLoading(false) }
  }

  const extractFromText = async () => {
    if (!extractedText.trim()) return
    setLoading(true)
    const form = new FormData()
    form.append('text', extractedText)
    try {
      const res = await fetch(COMPILE_URL.replace('/compile', '/ocr'), { method: 'POST', body: form })
      const data = await res.json()
      setParsed(data.parsed || null)
      setGeneratedMp(data.generated_mp || '')
    } catch (e) {
      setParsed(null)
    } finally { setLoading(false) }
  }

  const compileGenerated = async () => {
    if (!generatedMp.trim()) return
    setLoading(true)
    const form = new FormData()
    form.append('mp', new File([generatedMp], 'ocr_generated.mp'))
    form.append('target', target)
    try {
      const res = await fetch(COMPILE_URL, { method: 'POST', body: form })
      const data = await res.json()
      setCompiledCode(data.code || null)
    } catch (e) {
      setCompiledCode(null)
    } finally { setLoading(false) }
  }

  const card = {
    background: t.card || '#152a52', border: `1px solid ${t.border || '#1e3a6e'}`,
    borderRadius: 10, padding: 16,
  }

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }} onPaste={handlePaste} tabIndex={0}>
      {/* Left panel — Image + Text */}
      <div style={{
        width: 420, padding: 20, background: t.sidebar || '#0f1f3d',
        borderRight: `1px solid ${t.border || '#1e3a6e'}`,
        display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto',
      }}>
        <div>
          <h3 style={{ margin: 0, fontSize: 18, color: t.text || '#e8edf5' }}>
            OCR — Extractor de Grafos
          </h3>
          <p style={{ margin: '4px 0 0', fontSize: 12, color: t.dim || '#5a7399' }}>
            Sube un screenshot de Ab Initio o pega el texto del log
          </p>
        </div>

        {/* Image upload */}
        <div style={card}>
          <div style={{ fontSize: 13, fontWeight: 600, color: t.text || '#e8edf5', marginBottom: 8 }}>
            1. Subir imagen
          </div>
          <button onClick={() => fileRef.current.click()} style={{
            width: '100%', padding: '12px 16px', borderRadius: 8, cursor: 'pointer',
            background: imagePreview ? '#22c55e15' : (t.bg || '#0a1628'),
            border: `2px dashed ${imagePreview ? '#22c55e' : (t.border || '#1e3a6e')}`,
            color: imagePreview ? '#22c55e' : (t.muted || '#8fa3c4'), fontSize: 13,
          }}>
            {imagePreview ? 'Imagen cargada - click para cambiar' : 'Click para subir o Cmd+V para pegar screenshot'}
          </button>
          <input ref={fileRef} type="file" accept="image/*" hidden onChange={handleImageUpload} />
          
          {imagePreview && (
            <img src={imagePreview} alt="Preview" style={{
              width: '100%', marginTop: 8, borderRadius: 6, border: `1px solid ${t.border || '#1e3a6e'}`,
              maxHeight: 200, objectFit: 'contain', background: '#000',
            }} />
          )}

          {imagePreview && (
            <button onClick={extractFromImage} disabled={loading} style={{
              width: '100%', marginTop: 8, padding: '8px 16px', borderRadius: 8,
              background: '#6366f1', color: '#fff', border: 'none', fontSize: 13,
              fontWeight: 600, cursor: loading ? 'wait' : 'pointer',
            }}>{loading ? 'Extrayendo...' : 'Extraer texto (OCR)'}</button>
          )}
        </div>

        {/* Text paste */}
        <div style={card}>
          <div style={{ fontSize: 13, fontWeight: 600, color: t.text || '#e8edf5', marginBottom: 8 }}>
            2. Texto extraido (o pegar directamente)
          </div>
          <textarea
            value={extractedText}
            onChange={e => setExtractedText(e.target.value)}
            placeholder="Pega aqui el texto del log de Ab Initio (XXGpvertex, XXGflow, XXGedge, etc.)"
            style={{
              width: '100%', minHeight: 150, padding: 10, borderRadius: 8,
              background: t.codeBg || '#081220', border: `1px solid ${t.border || '#1e3a6e'}`,
              color: t.text || '#e8edf5', fontSize: 11, fontFamily: 'monospace',
              lineHeight: 1.5, resize: 'vertical', outline: 'none',
            }}
          />
          <button onClick={extractFromText} disabled={!extractedText.trim() || loading} style={{
            width: '100%', marginTop: 8, padding: '8px 16px', borderRadius: 8,
            background: extractedText.trim() ? '#f59e0b' : (t.border || '#1e3a6e'),
            color: '#fff', border: 'none', fontSize: 13, fontWeight: 600,
            cursor: extractedText.trim() ? 'pointer' : 'not-allowed',
          }}>{loading ? 'Parseando...' : 'Parsear texto'}</button>
        </div>

        {/* Parsed results */}
        {parsed && (
          <div style={card}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#22c55e', marginBottom: 8 }}>
              3. Resultado del parsing
            </div>
            <div style={{ fontSize: 12, color: t.muted || '#8fa3c4', display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span>Formato: <strong style={{ color: '#6366f1' }}>{parsed.format}</strong></span>
              {parsed.graph_name && <span>Grafo: <strong style={{ color: '#f59e0b' }}>{parsed.graph_name}</strong></span>}
              <span>Nodos: <strong style={{ color: '#22c55e' }}>{parsed.nodes?.length || 0}</strong></span>
              <span>Edges: <strong style={{ color: '#22c55e' }}>{parsed.edges?.length || 0}</strong></span>
              <span>Flows: <strong>{parsed.flows?.length || 0}</strong></span>
              <span>Params: <strong>{parsed.parameters?.length || 0}</strong></span>
              <span>Lineas: <strong>{parsed.raw_lines}</strong></span>
            </div>
          </div>
        )}
      </div>

      {/* Right panel — Generated MP + Code */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Target + Compile */}
        <div style={{
          padding: '12px 20px', background: t.sidebar || '#0f1f3d',
          borderBottom: `1px solid ${t.border || '#1e3a6e'}`,
          display: 'flex', alignItems: 'center', gap: 12,
        }}>
          <span style={{ fontSize: 13, color: t.muted || '#8fa3c4' }}>Target:</span>
          {['glue', 'spark', 'flink'].map(tgt => (
            <button key={tgt} onClick={() => setTarget(tgt)} style={{
              padding: '4px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
              background: target === tgt ? (t.accent || '#1a73e8') + '20' : 'transparent',
              border: `1px solid ${target === tgt ? (t.accent || '#1a73e8') : (t.border || '#1e3a6e')}`,
              color: target === tgt ? (t.accent || '#1a73e8') : (t.muted || '#8fa3c4'),
              fontWeight: target === tgt ? 600 : 400,
            }}>{tgt === 'glue' ? 'Glue' : tgt === 'spark' ? 'Spark' : 'Flink'}</button>
          ))}
          <button onClick={compileGenerated} disabled={!generatedMp.trim() || loading} style={{
            marginLeft: 'auto', padding: '6px 16px', borderRadius: 8,
            background: generatedMp.trim() ? '#22c55e' : (t.border || '#1e3a6e'),
            color: '#fff', border: 'none', fontSize: 13, fontWeight: 600,
            cursor: generatedMp.trim() ? 'pointer' : 'not-allowed',
          }}>Compile Generated .mp</button>
        </div>

        {/* Content area */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {/* Generated MP */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: `1px solid ${t.border || '#1e3a6e'}` }}>
            <div style={{ padding: '8px 16px', background: t.card || '#152a52', borderBottom: `1px solid ${t.border || '#1e3a6e'}` }}>
              <span style={{ fontSize: 12, color: '#22c55e', fontWeight: 600 }}>GENERATED .MP</span>
            </div>
            <textarea
              value={generatedMp}
              onChange={e => setGeneratedMp(e.target.value)}
              placeholder="El .mp generado aparecera aqui..."
              style={{
                flex: 1, padding: 16, border: 'none', outline: 'none', resize: 'none',
                background: t.codeBg || '#081220', color: '#22c55e',
                fontSize: 12, fontFamily: 'monospace', lineHeight: 1.6,
              }}
            />
          </div>

          {/* Compiled code */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '8px 16px', background: t.card || '#152a52', borderBottom: `1px solid ${t.border || '#1e3a6e'}` }}>
              <span style={{ fontSize: 12, color: '#6366f1', fontWeight: 600 }}>
                COMPILED CODE ({target.toUpperCase()})
              </span>
            </div>
            <pre style={{
              flex: 1, padding: 16, margin: 0, overflow: 'auto',
              background: t.codeBg || '#081220', color: t.muted || '#8fa3c4',
              fontSize: 12, fontFamily: 'monospace', lineHeight: 1.6,
            }}>
              {compiledCode || '// Compila el .mp generado para ver el codigo aqui'}
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}
