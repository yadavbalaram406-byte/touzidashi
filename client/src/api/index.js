const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `请求失败 ${res.status}`)
  }
  return res.json()
}

function uploadWithProgress(files, onProgress) {
  return new Promise((resolve, reject) => {
    const form = new FormData()
    const arr = Array.isArray(files) ? files : [files]
    arr.forEach(f => form.append('files', f))

    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${BASE}/evaluations/upload`)
    xhr.timeout = 180000 // 3 分钟超时

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        onProgress?.(Math.round((e.loaded / e.total) * 100))
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText))
        } catch {
          reject(new Error('服务器响应解析失败，请重试'))
        }
      } else {
        try {
          const err = JSON.parse(xhr.responseText)
          reject(new Error(err.detail || `上传失败（${xhr.status}），请重试`))
        } catch {
          reject(new Error(`上传失败（${xhr.status}），请检查文件格式后重试`))
        }
      }
    })

    xhr.addEventListener('error', () =>
      reject(new Error('网络连接失败，请检查网络后重试'))
    )
    xhr.addEventListener('timeout', () =>
      reject(new Error('上传超时，文件可能过大，请压缩后重试'))
    )
    xhr.addEventListener('abort', () =>
      reject(new Error('上传已取消'))
    )

    xhr.send(form)
  })
}

export const api = {
  uploadEvaluation: (files, onProgress) => uploadWithProgress(files, onProgress),

  getEvaluations: (page = 1, pageSize = 20) =>
    request(`/evaluations?page=${page}&page_size=${pageSize}`),

  getEvaluation: (id) => request(`/evaluations/${id}`),

  getStatus: (id) => request(`/evaluations/${id}/status`),

  deleteEvaluation: (id) =>
    request(`/evaluations/${id}`, { method: 'DELETE' }),

  getConfig: () => request('/config'),

  testLLM: () => request('/config/test-llm', { method: 'POST' }),
}
