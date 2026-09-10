import { useCallback, useEffect, useState } from 'react'
import { Pencil } from 'lucide-react'
import { api } from '../api.js'
import Avatar from '../components/Avatar.jsx'

const EMPTY_FORM = { name: '', email: '', subjects_taught: '', password: '', status: true }

export default function Teachers() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState(EMPTY_FORM)
  const [busy, setBusy] = useState(false)
  const [editing, setEditing] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api('/api/v1/teachers')
      setRows(data.data || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  function resetForm() {
    setForm(EMPTY_FORM)
    setEditing(null)
  }

  async function create(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = { ...form }
      if (!body.subjects_taught) delete body.subjects_taught
      if (!body.password) delete body.password
      delete body.status
      const res = await api('/api/v1/teachers', { method: 'POST', body })
      setNotice(`Added teacher ${res.teacher.name}`)
      resetForm()
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function startEdit(t) {
    setError('')
    setForm({
      name: t.name,
      email: t.email,
      subjects_taught: t.subjects_taught || '',
      password: '',
      status: t.status,
    })
    setEditing(t)
  }

  async function saveEdit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = {
        name: form.name,
        email: form.email,
        status: form.status,
      }
      body.subjects_taught = form.subjects_taught || null
      if (form.password) body.password = form.password
      await api(`/api/v1/teachers/${editing.teacher_id}`, { method: 'PUT', body })
      setNotice('Teacher updated')
      resetForm()
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h1>Teachers</h1>
      {notice && <div className="alert alert-ok">{notice}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <form className="form-panel" onSubmit={editing ? saveEdit : create}>
        <h2>{editing ? 'Edit teacher' : 'Add a teacher'}</h2>
        <div className="grid2">
          <label>
            Full name
            <input value={form.name} onChange={(e) => set('name', e.target.value)} required />
          </label>
          <label>
            Email
            <input type="email" value={form.email} onChange={(e) => set('email', e.target.value)} required />
          </label>
          <label>
            Subjects taught
            <input
              value={form.subjects_taught}
              onChange={(e) => set('subjects_taught', e.target.value)}
              placeholder="e.g. Math, Physics"
            />
          </label>
          {editing ? (
            <label className="check">
              <input
                type="checkbox"
                checked={form.status}
                onChange={(e) => set('status', e.target.checked)}
              />
              Account active (un-tick to deactivate)
            </label>
          ) : (
            <label>
              Password (optional — lets them log in)
              <input
                type="password"
                value={form.password}
                onChange={(e) => set('password', e.target.value)}
                placeholder="At least 8 characters"
                minLength={form.password ? 8 : undefined}
              />
            </label>
          )}
          {editing && (
            <label>
              New password (optional — leave blank to keep current)
              <input
                type="password"
                value={form.password}
                onChange={(e) => set('password', e.target.value)}
                placeholder="At least 8 characters"
                minLength={form.password ? 8 : undefined}
              />
            </label>
          )}
        </div>
        <div className="row">
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? 'Saving…' : editing ? 'Save changes' : 'Add teacher'}
          </button>
          {editing && (
            <button className="btn" type="button" onClick={resetForm}>
              Cancel edit
            </button>
          )}
        </div>
      </form>

      <div className="card">
        {loading ? (
          <p className="muted">Loading…</p>
        ) : rows.length === 0 ? (
          <p className="muted">No teachers found.</p>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Subjects</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>
            <tbody>
              {rows.map((t) => (
                <tr key={t.teacher_id}>
                  <td>
                    <div className="name-cell">
                      <Avatar name={t.name} />
                      {t.name}
                    </div>
                  </td>
                  <td>{t.email}</td>
                  <td>{t.subjects_taught || '—'}</td>
                  <td>{t.status ? <span className="pill pill-ok">Active</span> : <span className="pill pill-off">Inactive</span>}</td>
                  <td>
                    <button className="btn btn-ghost" onClick={() => startEdit(t)}>
                      <Pencil size={13} />
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
      </div>
    </div>
  )
}