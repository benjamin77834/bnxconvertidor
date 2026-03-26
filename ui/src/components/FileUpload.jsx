import React, { useRef } from 'react'

const s = {
  wrap: { display: 'flex', flexDirection: 'column', gap: 8 },
  label: { fontSize: 12, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 1 },
  row: { display: 'flex', gap: 12, flexWrap: 'wrap' },
  slot: {
    display: 'flex', alignItems: 'center', gap: 8,
    background: '#1e2433', border: '1px dashed #334155',
    borderRadius: 8, padding: '8px 14px', cursor: 'pointer',
    fontSize: 13, color: '#94a3b8', transition: 'border-color .2s',
  },
  slotActive: { borderColor: '#6366f1', color: '#e2e8f0' },
  btn: {
    marginTop: 8, padding: '10px 24px', background: '#6366f1',
    color: '#fff', border: 'none', borderRadius: 8,
    fontSize: 14, fontWeight: 600, cursor: 'pointer',
  },
  btnDisabled: { background: '#334155', cursor: 'not-allowed' },
}

export default function FileUpload({ files, setFiles, onCompile, loading }) {
  const refs = { mp: useRef(), xfr: useRef(), dml: useRef() }

  const pick = (key) => (e) => {
    const f = e.target.files[0]
    if (f) setFiles(prev => ({ ...prev, [key]: f }))
  }

  const canCompile = !!files.mp && !loading

  return (
    <div style={s.wrap}>
      <span style={s.label}>Upload files</span>
      <div style={s.row}>
        {['mp', 'xfr', 'dml'].map(key => (
          <div key={key}
            style={{ ...s.slot, ...(files[key] ? s.slotActive : {}) }}
            onClick={() => refs[key].current.click()}
          >
            <span>{files[key] ? `✅ ${files[key].name}` : `📄 .${key} file`}</span>
            <input ref={refs[key]} type="file" accept={`.${key}`} hidden onChange={pick(key)} />
          </div>
        ))}
      </div>
      <button
        style={{ ...s.btn, ...(canCompile ? {} : s.btnDisabled) }}
        onClick={onCompile}
        disabled={!canCompile}
      >
        {loading ? '⏳ Compiling...' : '🚀 Compile'}
      </button>
    </div>
  )
}
