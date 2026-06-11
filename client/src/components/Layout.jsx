import { NavLink } from 'react-router-dom'
import './Layout.css'

export default function Layout({ children }) {
  return (
    <div className="layout">
      <header className="navbar">
        <div className="container navbar-inner">
          <NavLink to="/" className="brand">
            <span className="brand-icon">💰</span>
            <span className="brand-name">投资大师</span>
          </NavLink>
          <nav className="nav-links">
            <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              上传评估
            </NavLink>
            <NavLink to="/history" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              历史记录
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="main-content">
        <div className="container">
          {children}
        </div>
      </main>
    </div>
  )
}
