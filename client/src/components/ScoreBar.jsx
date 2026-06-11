import './ScoreBar.css'

export default function ScoreBar({ score, maxScore, color = '#6366f1' }) {
  const pct = Math.min(100, (score / maxScore) * 100)
  return (
    <div className="score-bar-track">
      <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
    </div>
  )
}
