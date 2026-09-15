import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShieldCheck, ClipboardCheck, BookOpen, LogIn } from 'lucide-react'
import { useAuth } from '../auth.jsx'
import { getCachedBrand } from '../brand.js'

const HOME_BY_ROLE = { admin: '/students', teacher: '/', parent: '/' }

const FEATURES = [
  { icon: ShieldCheck, text: 'Secure logins for administrators, teachers, and parents' },
  { icon: ClipboardCheck, text: 'Daily attendance and grade records in a few clicks' },
  { icon: BookOpen, text: 'Portal for parents with live grades and report cards' },
]

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const brand = getCachedBrand()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const role = await login(email, password)
      navigate(HOME_BY_ROLE[role] || '/')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-showcase">
        <div className="login-showcase-inner">
          <img src={brand.logo_url} alt={brand.name} className="login-logo" />
          <h1>{brand.name}</h1>
          {brand.tagline && <p className="tagline">{brand.tagline}</p>}
          {brand.demo && <span className="badge-demo">Demo preview</span>}
        </div>

        <div className="login-features">
          {FEATURES.map((f) => {
            const Icon = f.icon
            return (
              <div key={f.text} className="login-feature">
                <span className="login-feature-icon">
                  <Icon size={17} strokeWidth={2.2} />
                </span>
                <span>{f.text}</span>
              </div>
            )
          })}
        </div>

        <div className="login-foot">Student Management System</div>
      </div>

      <div className="login-side">
        <form className="login-card" onSubmit={handleSubmit}>
          <h2>Welcome back</h2>
          <p className="login-sub">Sign in to continue to your dashboard.</p>
          <label>
            Email
            {' '}
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label>
            Password
            {' '}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          {error && <div className="alert alert-error">{error}</div>}
          <button className="btn btn-primary" type="submit" disabled={busy}>
            <LogIn size={16} />
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
          {brand.demo && (
            <p className="hint">
              Demo admin login: admin@schoolsystem.com (password chosen at seed time)
            </p>
          )}
        </form>
      </div>
    </div>
  )
}