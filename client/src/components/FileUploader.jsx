import { useCallback, useState } from 'react'
import './FileUploader.css'

const ALLOWED = ['pdf', 'ppt', 'pptx']
const MAX_FILES = 5

function getExt(name) {
  return (name || '').split('.').pop().toLowerCase()
}

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

const FILE_ICONS = { pdf: '📄', ppt: '📊', pptx: '📊' }

// uploadProgress: null=空闲, 0-99=上传中, 100=服务器处理中
export default function FileUploader({ onUpload, loading, uploadProgress }) {
  const [files, setFiles] = useState([])
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState('')

  const addFiles = useCallback((incoming) => {
    setError('')
    const next = [...files]
    for (const f of incoming) {
      const ext = getExt(f.name)
      if (!ALLOWED.includes(ext)) {
        setError(`不支持 .${ext} 格式，请上传 PDF / PPT / PPTX`)
        continue
      }
      if (f.size > 50 * 1024 * 1024) {
        setError(`${f.name} 超过 50MB 限制`)
        continue
      }
      if (next.some(x => x.name === f.name && x.size === f.size)) continue
      if (next.length >= MAX_FILES) {
        setError(`最多同时上传 ${MAX_FILES} 个文件`)
        break
      }
      next.push(f)
    }
    setFiles(next)
  }, [files])

  const removeFile = (idx) => setFiles(f => f.filter((_, i) => i !== idx))

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    addFiles([...e.dataTransfer.files])
  }, [addFiles])

  const onChange = (e) => {
    addFiles([...e.target.files])
    e.target.value = ''
  }

  const handleSubmit = () => {
    if (files.length > 0) onUpload(files)
  }

  const canAdd = files.length < MAX_FILES && !loading
  // 只要 loading 就显示进度块，不依赖 uploadProgress（代理可能导致 lengthComputable=false）
  const isUploading = loading
  // 是否有真实进度百分比
  const hasPct = uploadProgress != null && uploadProgress >= 0

  return (
    <div className="uploader-wrap">
      {/* Drop zone */}
      {canAdd && (
        <div
          className={`drop-zone ${dragging ? 'dragging' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => document.getElementById('file-input').click()}
        >
          <input
            id="file-input"
            type="file"
            accept=".pdf,.ppt,.pptx"
            multiple
            style={{ display: 'none' }}
            onChange={onChange}
          />
          <div className="drop-icon">📂</div>
          <p className="drop-text">
            点击选择文件，或拖拽到此处
          </p>
          <p className="drop-hint">
            支持 PDF / PPT / PPTX · 单文件最大 50MB
            {files.length > 0 && ` · 还可添加 ${MAX_FILES - files.length} 个`}
          </p>
        </div>
      )}

      {/* File list */}
      {files.length > 0 && (
        <div className="file-list">
          {files.map((f, i) => (
            <div key={i} className={`file-item ${isUploading ? 'uploading' : ''}`}>
              <span className="file-icon">{FILE_ICONS[getExt(f.name)] || '📄'}</span>
              <div className="file-info">
                <span className="file-name">{f.name}</span>
                <span className="file-size">{formatSize(f.size)}</span>
              </div>
              {!loading && (
                <button className="file-remove" onClick={() => removeFile(i)} title="移除">✕</button>
              )}
            </div>
          ))}
        </div>
      )}

      {error && <p className="uploader-error">{error}</p>}

      {/* 上传进度区域 */}
      {isUploading && (
        <div className="upload-progress-block">
          {uploadProgress === 100 ? (
            <>
              <div className="progress-header">
                <span className="progress-label progress-label-done">✅ 上传完成，等待服务器响应...</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill progress-fill-pulse" style={{ width: '100%' }} />
              </div>
              <p className="progress-hint">即将进入评估页...</p>
            </>
          ) : hasPct ? (
            <>
              <div className="progress-header">
                <span className="progress-label">📤 正在上传文件...</span>
                <span className="progress-pct">{uploadProgress}%</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
              </div>
              <p className="progress-hint">请勿关闭页面</p>
            </>
          ) : (
            // 无法计算进度（如代理剥掉了 Content-Length）→ 不确定动画
            <>
              <div className="progress-header">
                <span className="progress-label">📤 正在上传文件，请稍候...</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill progress-fill-pulse" style={{ width: '70%' }} />
              </div>
              <p className="progress-hint">请勿关闭页面</p>
            </>
          )}
        </div>
      )}

      {/* Submit button — 上传中隐藏 */}
      {files.length > 0 && !isUploading && (
        <button
          className="btn btn-primary upload-submit-btn"
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading
            ? '⏳ 准备中...'
            : `🚀 开始评估${files.length > 1 ? `（${files.length} 份材料合并）` : ''}`}
        </button>
      )}
    </div>
  )
}
