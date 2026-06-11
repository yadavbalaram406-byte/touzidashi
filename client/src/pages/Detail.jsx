import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/index.js'
import { EvalReport } from './Result.jsx'

export default function Detail() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getEvaluation(id).then(setData).catch(e => setError(e.message))
  }, [id])

  if (error) return (
    <div className="result-page">
      <div className="card error-message">{error}</div>
    </div>
  )

  if (!data) return (
    <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
      加载中...
    </div>
  )

  return <EvalReport data={data} />
}
