import './ScoreTable.css'

const DECISION_CFG = {
  'Strong Yes':    { icon: '🏆', label: '绝对力推',   color: '#065f46', bg: '#d1fae5', bar: '#10b981' },
  'Cautious Yes':  { icon: '📈', label: '谨慎看好',   color: '#92400e', bg: '#fef3c7', bar: '#f59e0b' },
  'Keep in Touch': { icon: '👀', label: '保持观察',   color: '#1e40af', bg: '#dbeafe', bar: '#3b82f6' },
  'Pass':          { icon: '🛑', label: '直接否决',   color: '#991b1b', bg: '#fee2e2', bar: '#ef4444' },
}

const DIM_META = {
  team:       { icon: '👥', color: '#6366f1' },
  pain_point: { icon: '🎯', color: '#10b981' },
  traction:   { icon: '📈', color: '#f59e0b' },
  moat:       { icon: '🏰', color: '#ef4444' },
}

// 从 "🛑 Pass" 提取 "Pass"，兼容旧格式和纯标签
function extractLabel(decision) {
  if (!decision) return ''
  const stripped = decision.replace(/^\S+\s*/, '').trim()
  return stripped in DECISION_CFG ? stripped : decision.trim()
}

// 解析 "加分项：...扣分项（重灾区）：..." → [{isPlus, content}]
function parseReasoning(text) {
  if (!text) return []
  const parts = []
  const re = /(加分项[^：]*|扣分项[^：]*)：([\s\S]+?)(?=(?:加分项|扣分项)[^：]*：|$)/g
  let m
  while ((m = re.exec(text)) !== null) {
    parts.push({ isPlus: m[1].includes('加'), content: m[2].trim().replace(/。\s*$/, '') })
  }
  return parts
}

function ReasoningText({ text }) {
  const parts = parseReasoning(text)
  if (parts.length === 0) return <p className="sdim-reasoning">{text}</p>
  return (
    <div className="sdim-reasoning-wrap">
      {parts.map((p, i) => (
        <div key={i} className={`reason-part ${p.isPlus ? 'reason-plus' : 'reason-minus'}`}>
          <span className="reason-tag">{p.isPlus ? '✦ 加分' : '▲ 扣分'}</span>
          <span className="reason-text">{p.content}</span>
        </div>
      ))}
    </div>
  )
}

export default function ScoreTable({ scores, finalScore, decision }) {
  if (!scores || scores.length === 0) return null

  const label = extractLabel(decision)
  const dec = DECISION_CFG[label] ?? DECISION_CFG['Pass']

  return (
    <div className="score-table">

      {/* ── 总分英雄 ── */}
      {finalScore != null && (
        <div className="final-hero" style={{ background: dec.bg }}>
          <div className="final-num" style={{ color: dec.color }}>{finalScore}</div>
          <div className="final-right">
            <div className="final-pts" style={{ color: dec.color }}>分</div>
            <div className="final-badge" style={{ color: dec.color }}>
              {dec.icon} {label}
            </div>
            <div className="final-label-cn" style={{ color: dec.color }}>{dec.label}</div>
          </div>
          <div className="final-bar-wrap">
            <div className="final-bar-track">
              <div className="final-bar-fill"
                style={{ width: `${finalScore}%`, background: dec.bar }} />
            </div>
            <span className="final-bar-hint">满分 100 分</span>
          </div>
        </div>
      )}

      {/* ── 2×2 维度卡 ── */}
      <div className="score-dims-grid">
        {scores.map((dim) => {
          const meta = DIM_META[dim.key] || { icon: '📊', color: '#6366f1' }
          const pct = Math.min(100, (dim.score / dim.max_score) * 100)
          return (
            <div key={dim.key} className="sdim-card"
              style={{ '--dc': meta.color }}>
              <div className="sdim-header">
                <span className="sdim-icon">{meta.icon}</span>
                <span className="sdim-name">{dim.name}</span>
                <span className="sdim-score-num" style={{ color: meta.color }}>
                  {dim.score}<span className="sdim-max">/{dim.max_score}</span>
                </span>
              </div>
              <div className="sdim-bar-track">
                <div className="sdim-bar-fill"
                  style={{ width: `${pct}%`, background: meta.color }} />
              </div>
              <div className="sdim-tier-badge"
                style={{ color: meta.color, background: `${meta.color}18`, borderColor: `${meta.color}50` }}>
                {dim.tier_label}
              </div>
              <ReasoningText text={dim.reasoning} />
            </div>
          )
        })}
      </div>

    </div>
  )
}
