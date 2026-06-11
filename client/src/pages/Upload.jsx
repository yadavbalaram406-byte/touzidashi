import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import FileUploader from '../components/FileUploader.jsx'
import { api } from '../api/index.js'
import './Upload.css'

const DIMENSIONS = [
  {
    icon: '👥',
    name: '团队与执行力',
    max: 30,
    color: '#6366f1',
    bg: '#eef2ff',
    tiers: [
      { range: '25–30', label: '顶级配置', desc: '10年+深度认知，极客动手+极强销售，迭代速度按天计' },
      { range: '15–24', label: '标准组合', desc: '技术+商业配置完整，大厂/行业背景，1-2 月内可跑出 MVP' },
      { range: '0–14',  label: '存在硬伤', desc: '核心技术外包，或全技术无商业，或陷入半年以上憋大招' },
    ],
  },
  {
    icon: '🎯',
    name: '痛点与市场时机',
    max: 25,
    color: '#10b981',
    bg: '#ecfdf5',
    tiers: [
      { range: '20–25', label: '完美击中', desc: '"头发着火"级刚需，契合大模型突破或生态结构性真空' },
      { range: '10–19', label: '稳健生意', desc: '痛点真实但属改良型，市场有天花板，千万级现金流生意' },
      { range: '0–9',   label: '伪需求/红海', desc: '拿技术找场景自嗨，或进入被巨头免费策略锁死的市场' },
    ],
  },
  {
    icon: '📈',
    name: '商业牵引力',
    max: 25,
    color: '#f59e0b',
    bg: '#fffbeb',
    tiers: [
      { range: '20–25', label: '极强验证', desc: '未写完代码就跑通真实付费，高复购留存，转化漏斗优秀' },
      { range: '10–19', label: '初步成型', desc: '有早期内测用户，LTV/CAC 逻辑通顺，单体经济模型成立' },
      { range: '0–9',   label: '逻辑断裂', desc: '仅免费用户，商业化寄望未来流量变现，获客成本不清晰' },
    ],
  },
  {
    icon: '🏰',
    name: '护城河与壁垒',
    max: 20,
    color: '#ef4444',
    bg: '#fff1f2',
    tiers: [
      { range: '16–20', label: '极高壁垒', desc: '颠覆性专有技术，切入极难替换的企业工作流或双边网络' },
      { range: '8–15',  label: '先发优势', desc: '体验极佳但依赖开源模型，护城河靠执行力和时间窗口' },
      { range: '0–7',   label: '极易复制', desc: '纯 UI 创新或 Prompt 套壳，竞对一个周末就能克隆' },
    ],
  },
]

const DECISIONS = [
  { icon: '🏆', range: '85–100', label: 'Strong Yes',      chinese: '绝对力推', color: '#065f46', bg: '#d1fae5' },
  { icon: '📈', range: '70–84',  label: 'Cautious Yes',    chinese: '谨慎看好', color: '#92400e', bg: '#fef3c7' },
  { icon: '👀', range: '50–69',  label: 'Keep in Touch',   chinese: '保持观察', color: '#1e40af', bg: '#dbeafe' },
  { icon: '🛑', range: '<50',    label: 'Pass',            chinese: '直接否决', color: '#991b1b', bg: '#fee2e2' },
]

export default function Upload() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(null)
  const [error, setError] = useState('')
  const pendingFilesRef = useRef(null)

  const handleUpload = useCallback((files) => {
    pendingFilesRef.current = files
    setLoading(true)
    setError('')
    setUploadProgress(0)
  }, [])

  // useEffect 保证在 React 把 loading=true commit 到 DOM 后才启动 XHR
  useEffect(() => {
    if (!loading || !pendingFilesRef.current) return
    const files = pendingFilesRef.current
    pendingFilesRef.current = null

    api.uploadEvaluation(files, (pct) => {
      setUploadProgress(pct)
    }).then(result => {
      navigate(`/result/${result.id}`)
    }).catch(e => {
      setError(e.message)
      setLoading(false)
      setUploadProgress(null)
    })
  }, [loading, navigate])

  return (
    <div className="upload-page">

      {/* ── 屏一：上传区 ── */}
      <section className="upload-section">
        <div className="upload-hero">
          <span className="hero-icon">💰</span>
          <div>
            <h1 className="upload-title">投资大师</h1>
            <p className="upload-subtitle">上传项目文档，基于YC标准自动完成尽调评估</p>
          </div>
        </div>

        <div className="card upload-card">
          <FileUploader onUpload={handleUpload} loading={loading} uploadProgress={uploadProgress} />
          {error && (
            <div className="upload-error-block">
              <p className="upload-error-title">⚠️ 上传失败</p>
              <p className="upload-error-msg">{error}</p>
              <p className="upload-error-hint">请检查网络连接或文件格式，然后重新上传</p>
            </div>
          )}
        </div>

        {/* Peek strip — 展示 4 个决策结果，引导向下滚动看维度详情 */}
        <a href="#framework" className="framework-peek">
          <div className="peek-dims">
            {DECISIONS.map(d => (
              <div key={d.label} className="peek-dim"
                style={{ background: d.bg, borderColor: d.color, color: d.color }}>
                <span className="peek-dim-icon">{d.icon}</span>
                <span className="peek-dim-name">{d.range}</span>
                <span className="peek-dim-score">{d.chinese}</span>
              </div>
            ))}
          </div>
          <span className="peek-hint">查看评分维度详情 ↓</span>
        </a>
      </section>

      {/* ── 屏二：评分框架 ── */}
      <section className="framework-section" id="framework">
        <div className="framework-header">
          <div className="framework-titles">
            <h2 className="framework-title">YC 早期项目评估框架</h2>
            <p className="framework-subtitle">4 个核心维度 · 100 分制 · 源自 Y Combinator 标准</p>
          </div>
        </div>

        <div className="dimensions-grid">
          {DIMENSIONS.map((dim) => (
            <div key={dim.name} className="dim-card" style={{ '--dim-color': dim.color, '--dim-bg': dim.bg }}>
              <div className="dim-card-header">
                <span className="dim-icon">{dim.icon}</span>
                <div>
                  <div className="dim-name">{dim.name}</div>
                  <span className="dim-max-badge" style={{ background: dim.color }}>满分 {dim.max} 分</span>
                </div>
              </div>
              <div className="dim-tiers">
                {dim.tiers.map((tier, i) => (
                  <div key={i} className={`tier-row tier-${i}`}>
                    <div className="tier-head">
                      <span className="tier-range">{tier.range}</span>
                      <span className="tier-label">{tier.label}</span>
                    </div>
                    <p className="tier-desc">{tier.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

    </div>
  )
}
