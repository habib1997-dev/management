import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'

const HOME_BY_ROLE = { admin: '/students', teacher: '/', parent: '/' }

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
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
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>School System</h1>
        <p className="muted">Sign in with your account.</p>
        <label>
          Email
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
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
        <p className="hint">
          Demo admin: admin@schoolsystem.com / changeme123
        </p>
      </form>
    </div>
  )
}