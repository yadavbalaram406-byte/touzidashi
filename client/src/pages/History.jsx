import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/index.js'
import './History.css'

function statusBadge(status) {
  const map = {
    completed: 'badge-success',
    processing: 'badge-info',
    pending: 'badge-gray',
    failed: 'badge-danger',
  }
  const labels = {
    completed: '已完成',
    processing: '评估中',
    pending: '排队中',
    failed: '失败',
  }
  return <span className={`badge ${map[status] || 'badge-gray'}`}>{labels[status] || status}</span>
}

export default function History() {
  const [data, setData] = useState(null)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async (p) => {
    setLoading(true)
    try {
      const res = await api.getEvaluations(p, 12)
      setData(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(page) }, [page])

  const handleDelete = async (id, e) => {
    e.preventDefault()
    e.stopPropagation()
    if (!confirm('确定删除这条评估记录？')) return
    await api.deleteEvaluation(id)
    load(page)
  }

  if (loading && !data) return <div className="history-page"><div className="card" style={{textAlign:'center',padding:'48px'}}>加载中...</div></div>

  if (error) return <div className="history-page"><div className="error-message">{error}</div></div>

  const items = data?.items || []

  return (
    <div className="history-page">
      <div className="history-header">
        <h2 className="page-title">历史记录</h2>
        <Link to="/" className="btn btn-primary">+ 新建评估</Link>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">
          <div className="icon">📂</div>
          <p>还没有评估记录</p>
          <Link to="/" className="btn btn-primary">上传第一个项目</Link>
        </div>
      ) : (
        <>
          <div className="history-grid">
            {items.map((item) => (
              <Link
                key={item.id}
                to={item.status === 'completed' ? `/detail/${item.id}` : `/result/${item.id}`}
                className="history-card"
              >
                <div className="hcard-top">
                  <span className="hcard-type">.{item.file_type.toUpperCase()}</span>
                  {statusBadge(item.status)}
                </div>
                <div className="hcard-name">{item.project_name}</div>
                <div className="hcard-file">{item.original_filename}</div>
                {item.final_score != null && (
                  <div className="hcard-score">
                    <span className="hcard-score-num">{item.final_score}</span>
                    <span className="hcard-score-label">/100 · {item.decision}</span>
                  </div>
                )}
                <div className="hcard-footer">
                  <span className="hcard-date">{new Date(item.created_at).toLocaleString('zh-CN')}</span>
                  <button className="btn btn-danger hcard-del" onClick={(e) => handleDelete(item.id, e)}>删除</button>
                </div>
              </Link>
            ))}
          </div>

          {data.total_pages > 1 && (
            <div className="pagination">
              <button className="btn btn-ghost" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>上一页</button>
              <span className="page-info">{page} / {data.total_pages}</span>
              <button className="btn btn-ghost" disabled={page >= data.total_pages} onClick={() => setPage(p => p + 1)}>下一页</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
