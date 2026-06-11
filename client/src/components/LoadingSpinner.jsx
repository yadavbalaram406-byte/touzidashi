import './LoadingSpinner.css'

export default function LoadingSpinner({ text = '评估中，请稍候...' }) {
  return (
    <div className="spinner-wrap">
      <div className="spinner" />
      <p className="spinner-text">{text}</p>
    </div>
  )
}
