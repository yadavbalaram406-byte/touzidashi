import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api/index.js'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ScoreTable from '../components/ScoreTable.jsx'
import './Result.css'

const POLL_INTERVAL = 2500

const QUOTES = [
  { text: '做一件用户真正热爱的事，比任何营销手段都有效。', author: 'Paul Graham', title: 'Y Combinator' },
  { text: '如果你不确定自己在解决一个真实的问题，那你多半没在解决真实的问题。', author: 'Paul Graham', title: 'Y Combinator' },
  { text: '如果你创业时不觉得尴尬，那说明你出发得太晚了。', author: 'Reid Hoffman', title: 'LinkedIn / Greylock' },
  { text: '创业就是在悬崖边上跳下去，在下落过程中组装飞机。', author: 'Reid Hoffman', title: 'LinkedIn' },
  { text: '市场才是决定创业成败的最关键因素，弱小的团队在好市场里也能成功。', author: 'Marc Andreessen', title: 'a16z' },
  { text: '下一件改变世界的大事，现在看起来总像是一个玩具。', author: 'Chris Dixon', title: 'a16z' },
  { text: '竞争是失败者的把戏，真正伟大的公司都是垄断者。', author: 'Peter Thiel', title: 'Founders Fund' },
  { text: '告诉我一件大多数人不相信、但你认为千真万确的事情。', author: 'Peter Thiel', title: 'Founders Fund' },
  { text: '当别人贪婪时我们恐惧，当别人恐惧时我们贪婪。', author: 'Warren Buffett', title: 'Berkshire Hathaway' },
  { text: '我宁愿在一个很好的生意里拥有一小部分，也不愿意在一个糟糕的生意里拥有全部。', author: 'Warren Buffett', title: 'Berkshire Hathaway' },
  { text: '告诉我你的激励机制，我就能告诉你结果会是什么。', author: 'Charlie Munger', title: 'Berkshire Hathaway' },
  { text: '反转人生的最快方式，是停止做那些你明知道是错的事情。', author: 'Charlie Munger', title: 'Berkshire Hathaway' },
  { text: '作为 CEO，你最重要的任务就是让公司活到明天。', author: 'Ben Horowitz', title: 'a16z' },
  { text: '平时做困难的事，是为了困难时刻不至于束手无策。', author: 'Ben Horowitz', title: 'a16z' },
  { text: '我们投的是那些拒绝承认失败的创始人。', author: 'Michael Moritz', title: 'Sequoia Capital' },
  { text: '我们最好的投资，都是当时看起来几乎不可能成功的公司。', author: 'Michael Moritz', title: 'Sequoia Capital' },
  { text: '在所有投资要素中，市场规模是最重要的，它决定了公司的天花板。', author: 'Don Valentine', title: 'Sequoia Capital' },
  { text: '我们投资传道者，不是雇佣兵——我们想要那些真正相信自己使命的创始人。', author: 'John Doerr', title: 'KPCB' },
  { text: '单位经济模型的失败不会随着规模扩张自动修复，它只会变得更糟。', author: 'Bill Gurley', title: 'Benchmark' },
  { text: '如果你打算建立一家公司，就得下定决心，即便遭受误解也不改初衷，甚至数年如此。', author: 'Jeff Bezos', title: 'Amazon' },
  { text: '我们最大的机会来自于客户永远不会改变的需求。', author: 'Jeff Bezos', title: 'Amazon' },
  { text: '创新不是关于预算，而是关于人才、流程，以及你们愿意接受哪些想法。', author: 'Steve Jobs', title: 'Apple' },
  { text: '只有偏执狂才能生存。', author: 'Andy Grove', title: 'Intel' },
  { text: '找到你热爱的事情，在人们还不知道它有多重要的时候，花时间去精通它。', author: 'Naval Ravikant', title: 'AngelList' },
  { text: '积累财富的方式是拥有别人无法复制的东西：独特的知识、技术或网络。', author: 'Naval Ravikant', title: 'AngelList' },
  { text: '市场规模是投资人最常低估的变量，正确时机下的小产品可以变成巨大的公司。', author: 'Sam Altman', title: 'OpenAI / YC' },
  { text: '做投资，你必须思考别人没有思考的事情，而不是比别人思考得更努力。', author: 'Howard Marks', title: 'Oaktree Capital' },
  { text: '最好的创始人不是在回答问题，他们在重新定义问题本身。', author: 'Chamath Palihapitiya', title: 'Social Capital' },
  { text: '如果你有一个疯狂的想法，你应该问的不是"为什么"，而是"为什么不"。', author: 'Larry Page', title: 'Google' },
  { text: '当所有人都说太难了的时候，往往正是机会最好的时候。', author: 'Jensen Huang', title: 'NVIDIA' },
  { text: '投资人最大的错误，是把一个优秀的团队和一个优秀的市场混为一谈。', author: 'Andy Rachleff', title: 'Benchmark' },
  { text: '如果你无法定义你的客户是谁，你就还不知道自己在做什么生意。', author: 'Peter Drucker', title: '管理学之父' },
  { text: '没有什么比企业文化更重要的了，因为文化决定了每一个决定。', author: 'Marc Benioff', title: 'Salesforce' },
  { text: '投资人最核心的能力是识别十年后世界的样子，然后找到今天正在做这件事的人。', author: '沈南鹏', title: '红杉中国' },
  { text: '优秀的创始人永远在学习，他们吸收信息的速度和深度远超常人。', author: '沈南鹏', title: '红杉中国' },
  { text: '我们不买公司，我们买人——买一群相信未来可以被改变的人。', author: '张磊', title: '高瓴资本' },
  { text: '做时间的朋友，因为复利的威力需要足够长的时间才能充分展现。', author: '张磊', title: '高瓴资本' },
  { text: '中国最好的创业机会，往往藏在被现有玩家集体忽视的角落里。', author: '徐新', title: '今日资本' },
  { text: '站在风口上猪都能飞，但风口过后，飞得远的永远是老鹰。', author: '雷军', title: '小米' },
  { text: '我们从不担心竞争，我们只担心自己跑得不够快。', author: '王兴', title: '美团' },
  { text: '大部分创业失败，不是因为市场不够大，而是团队无法比对手快一步学习。', author: '黄峥', title: '拼多多' },
  { text: '延迟满足感，是优秀创始人与普通人之间最重要的区别之一。', author: '张一鸣', title: '字节跳动' },
  { text: '创业初期，方向比努力更重要；大多数人懂这个道理，只是做不到。', author: '程维', title: '滴滴' },
  { text: '一个人可以走得很快，但一群人才能走得很远。', author: '俞敏洪', title: '新东方' },
  { text: '创业最容易犯的错误不是太早烧钱，而是太早扩张。', author: 'Fred Wilson', title: 'Union Square Ventures' },
  { text: '最好的投资是那些即使投资人犯傻也能赚到钱的公司，因为趋势足够强。', author: 'Vinod Khosla', title: 'Khosla Ventures' },
  { text: '我们运营公司的方式，是假设聪明人有最好的想法，然后创造环境让他们去实现。', author: 'Eric Schmidt', title: 'Google' },
  { text: '最危险的时刻，是你以为自己已经成功的时候。', author: '任正非', title: '华为' },
  { text: '不要试图去做最聪明的人，而要试图做那个最努力解决真实问题的人。', author: 'Jensen Huang', title: 'NVIDIA' },
  { text: '伟大的公司都是从解决一个小而真实的问题开始的，然后不断扩张边界。', author: 'Paul Graham', title: 'Y Combinator' },
]

export default function Result() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [status, setStatus] = useState('pending')
  const [error, setError] = useState('')

  const loadDetail = useCallback(async () => {
    const detail = await api.getEvaluation(id)
    setData(detail)
    setStatus(detail.status)
  }, [id])

  useEffect(() => {
    let timer = null

    const poll = async () => {
      try {
        const s = await api.getStatus(id)
        setStatus(s.status)
        if (s.status === 'completed' || s.status === 'failed') {
          await loadDetail()
          return
        }
        timer = setTimeout(poll, POLL_INTERVAL)
      } catch (e) {
        setError(e.message)
      }
    }

    poll()
    return () => clearTimeout(timer)
  }, [id, loadDetail])

  if (error) {
    return (
      <div className="result-page">
        <div className="card error-message">{error}</div>
        <Link to="/" className="btn btn-ghost back-btn">← 返回上传</Link>
      </div>
    )
  }

  if (status === 'pending' || status === 'processing' || !data) {
    return (
      <div className="result-page">
        <div className="card">
          <LoadingSpinner text={status === 'pending' ? '准备评估...' : 'AI 正在深度分析中，约需 1-3 分钟...'} />
          <div className="processing-steps">
            <Step label="第一步：提取项目简介" done={data?.project_intro != null} />
            <Step label="第二步：维度打分" done={data?.scores != null} />
            <Step label="第三步：生成投资建议" done={data?.suggestions != null} />
          </div>
        </div>
        <QuoteCarousel />
      </div>
    )
  }

  if (status === 'failed') {
    return (
      <div className="result-page">
        <div className="card">
          <div className="error-message">评估失败：{data?.error_message || '未知错误'}</div>
        </div>
        <Link to="/" className="btn btn-ghost back-btn">← 返回上传</Link>
      </div>
    )
  }

  return <EvalReport data={data} />
}

function Step({ label, done }) {
  return (
    <div className={`proc-step ${done ? 'done' : ''}`}>
      <span className="step-icon">{done ? '✅' : '⏳'}</span>
      <span>{label}</span>
    </div>
  )
}

// 按中文句末标点拆成多段，每段一个 <p>，兼顾英文句号
function TextBlock({ text, className }) {
  if (!text) return null
  const lines = text.split(/(?<=[。！？!?])\s*/).filter(s => s.trim())
  return (
    <div className={className}>
      {lines.length > 1
        ? lines.map((line, i) => <p key={i}>{line}</p>)
        : <p>{text}</p>}
    </div>
  )
}

export function EvalReport({ data }) {
  const intro = data.project_intro || {}
  const suggestions = data.suggestions || {}
  const captureRef = useRef(null)
  const [sharing, setSharing] = useState(false)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [shareError, setShareError] = useState('')

  const handleShare = async () => {
    if (!captureRef.current || sharing) return
    setSharing(true)
    setShareError('')
    try {
      const { toPng } = await import('html-to-image')
      await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
      const dataUrl = await toPng(captureRef.current, {
        pixelRatio: Math.min(window.devicePixelRatio ?? 2, 3),
        backgroundColor: '#f1f5f9',
        skipFonts: true,
        cacheBust: true,
      })
      const blob = await (await fetch(dataUrl)).blob()
      const filename = `${data.project_name || '投资评估'}_投资大师.png`
      const file = new File([blob], filename, { type: 'image/png' })

      // 尝试 Web Share API（iOS Safari / Android Chrome）
      if (navigator.canShare?.({ files: [file] })) {
        try {
          await navigator.share({ files: [file] })
          return
        } catch (e) {
          if (e?.name === 'AbortError') return  // 用户主动取消
          // 用户手势超时或浏览器拒绝 → 降级
        }
      }

      const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)
      if (isMobile) {
        // 移动端降级：显示图片让用户长按保存
        setPreviewUrl(dataUrl)
      } else {
        // 桌面端：触发下载
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        setTimeout(() => URL.revokeObjectURL(url), 2000)
      }
    } catch (e) {
      if (e?.name !== 'AbortError') {
        console.error('Share error:', e)
        setShareError(`图片生成失败：${e?.message || '请重试'}`)
      }
    } finally {
      setSharing(false)
    }
  }

  return (
    <div className="result-page">

      {/* ── 截图区域 ── */}
      <div ref={captureRef} className="capture-area">
        <div className="capture-header">
          <div className="capture-brand">
            <span className="capture-brand-icon">💰</span>
            <span className="capture-brand-name">投资大师</span>
            <span className="capture-brand-tag">YC标准 · AI尽调</span>
          </div>
        </div>

        <div className="result-header">
          <div>
            <h1 className="result-title">{data.project_name}</h1>
            <p className="result-meta">
              {data.original_filename} · {data.llm_provider?.toUpperCase()} {data.llm_model}
            </p>
          </div>
        </div>

        {/* Section 1: Project Intro */}
        <div className="card result-section">
          <div className="section-title">📋 项目简介</div>
          {intro.one_liner && <p className="one-liner">"{intro.one_liner}"</p>}
          {intro.summary && <TextBlock text={intro.summary} className="summary-text" />}
          <div className="intro-grid">
            {intro.market_background && (
              <div className="intro-block">
                <div className="intro-block-title">市场背景</div>
                <TextBlock text={intro.market_background} className="intro-body" />
              </div>
            )}
            {intro.comparables?.length > 0 && (
              <div className="intro-block">
                <div className="intro-block-title">对标企业</div>
                <ul className="tag-list">
                  {intro.comparables.map((c, i) => <li key={i} className="tag">{c}</li>)}
                </ul>
              </div>
            )}
          </div>
          {intro.highlights?.length > 0 && (
            <div className="intro-block">
              <div className="intro-block-title">项目亮点</div>
              <ul className="highlights-list">
                {intro.highlights.map((h, i) => <li key={i}>✦ {h}</li>)}
              </ul>
            </div>
          )}
        </div>

        {/* Section 2: Scores */}
        <div className="card result-section">
          <div className="section-title">📊 项目打分</div>
          <ScoreTable scores={data.scores} finalScore={data.final_score} decision={data.decision} />
        </div>

        {/* Section 3: Suggestions */}
        <div className="card result-section">
          <div className="section-title">💡 评估建议</div>
          <div className="suggestions-grid">
            {suggestions.strengths?.length > 0 && (
              <SuggestionBlock title="核心优势" icon="💪" items={suggestions.strengths} color="#d1fae5" />
            )}
            {suggestions.risks?.length > 0 && (
              <SuggestionBlock title="主要风险" icon="⚠️" items={suggestions.risks} color="#fee2e2" />
            )}
            {suggestions.improvements?.length > 0 && (
              <SuggestionBlock title="改进建议" icon="🎯" items={suggestions.improvements} color="#fef3c7" />
            )}
          </div>
          {suggestions.comprehensive_review && (
            <div className="comprehensive-review">
              <div className="intro-block-title">综合评述</div>
              <TextBlock text={suggestions.comprehensive_review} className="review-body" />
            </div>
          )}
          {suggestions.next_steps?.length > 0 && (
            <div className="next-steps">
              <div className="intro-block-title">下一步行动</div>
              <ol className="steps-list">
                {suggestions.next_steps.map((s, i) => <li key={i}>{s}</li>)}
              </ol>
            </div>
          )}
        </div>

        {/* 截图水印页脚 */}
        <div className="capture-footer">
          <span className="capture-footer-logo">💰 投资大师</span>
          <span className="capture-footer-dot">·</span>
          <span>AI项目尽调 · YC标准评估框架</span>
        </div>
      </div>

      {/* ── 操作按钮（截图范围外）── */}
      <div className="result-actions">
        <button
          className={`btn btn-primary share-btn ${sharing ? 'sharing' : ''}`}
          onClick={handleShare}
          disabled={sharing}
        >
          {sharing
            ? <><span className="share-spinner" />生成图片中...</>
            : '📤 分享图片'}
        </button>
        <Link to="/" className="btn btn-ghost">+ 新建评估</Link>
        <Link to="/history" className="btn btn-ghost">历史记录</Link>
      </div>
      {shareError && <div className="share-error">{shareError}</div>}

      {/* ── 移动端图片预览（长按保存）── */}
      {previewUrl && (
        <div className="share-overlay" onClick={() => setPreviewUrl(null)}>
          <div className="share-overlay-inner" onClick={e => e.stopPropagation()}>
            <p className="share-overlay-hint">长按图片保存到相册</p>
            <img src={previewUrl} className="share-overlay-img" alt="评估结果" />
            <button className="share-overlay-close" onClick={() => setPreviewUrl(null)}>关闭</button>
          </div>
        </div>
      )}

    </div>
  )
}

function SuggestionBlock({ title, icon, items, color }) {
  return (
    <div className="suggestion-block" style={{ background: color }}>
      <div className="suggestion-title">{icon} {title}</div>
      <ul className="suggestion-list">
        {items.map((item, i) => <li key={i}>{item}</li>)}
      </ul>
    </div>
  )
}

function QuoteCarousel() {
  const [idx, setIdx] = useState(() => Math.floor(Math.random() * QUOTES.length))
  const [fade, setFade] = useState(true)

  useEffect(() => {
    const timer = setInterval(() => {
      setFade(false)
      setTimeout(() => {
        setIdx(i => (i + 1) % QUOTES.length)
        setFade(true)
      }, 380)
    }, 7000)
    return () => clearInterval(timer)
  }, [])

  const q = QUOTES[idx]
  return (
    <div className="quote-carousel">
      <div className={`quote-inner ${fade ? 'quote-in' : 'quote-out'}`}>
        <p className="quote-text">"{q.text}"</p>
        <p className="quote-attr">— {q.author}<span className="quote-title">{q.title}</span></p>
      </div>
    </div>
  )
}
