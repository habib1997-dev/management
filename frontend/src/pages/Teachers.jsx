import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'

const EMPTY_FORM = { name: '', email: '', subjects_taught: '', password: '' }

export default function Teachers() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState(EMPTY_FORM)
  const [busy, setBusy] = useState(false)
  const [editing, setEditing] = useState(null)
  const [edit, setEdit] = useState({ name: '', email: '', subjects_taught: '', status: true })

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

  async function create(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = { ...form }
      if (!body.subjects_taught) delete body.subjects_taught
      if (!body.password) delete body.password
      const res = await api('/api/v1/teachers', { method: 'POST', body })
      setNotice(`Added teacher ${res.teacher.name}`)
      setForm(EMPTY_FORM)
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function startEdit(t) {
    setEdit({ name: t.name, email: t.email, subjects_taught: t.subjects_taught || '', status: t.status })
    setEditing(t)
  }

  function setEditField(field, value) {
    setEdit((e) => ({ ...e, [field]: value }))
  }

  async function saveEdit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = { ...edit }
      if (!body.subjects_taught) body.subjects_taught = null
      await api(`/api/v1/teachers/${editing.teacher_id}`, { method: 'PUT', body })
      setNotice('Teacher updated')
      setEditing(null)
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

      <form className="form-panel" onSubmit={create}>
        <h2>Add a teacher</h2>
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
        </div>
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? 'Saving…' : 'Add teacher'}
        </button>
      </form>

      <div className="card">
        {loading ? (
          <p className="muted">Loading…</p>
        ) : rows.length === 0 ? (
          <p className="muted">No teachers found.</p>
        ) : (
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
                  <td>{t.name}</td>
                  <td>{t.email}</td>
                  <td>{t.subjects_taught || '—'}</td>
                  <td>{t.status ? 'Active' : 'Inactive'}</td>
                  <td>
                    <button className="btn btn-ghost" onClick={() => startEdit(t)}>
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {editing && (
        <form className="form-panel" onSubmit={saveEdit}>
          <div className="row space-between">
            <h2>Edit teacher</h2>
            <button className="btn" type="button" onClick={() => setEditing(null)}>
              Close
            </button>
          </div>
          <div className="grid2">
            <label>
              Full name
              <input
                value={edit.name}
                onChange={(e) => setEditField('name', e.target.value)}
                required
              />
            </label>
            <label>
              Email
              <input
                type="email"
                value={edit.email}
                onChange={(e) => setEditField('email', e.target.value)}
                required
              />
            </label>
            <label>
              Subjects taught
              <input
                value={edit.subjects_taught}
                onChange={(e) => setEditField('subjects_taught', e.target.value)}
                placeholder="e.g. Math, Physics"
              />
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={edit.status}
                onChange={(e) => setEditField('status', e.target.checked)}
              />
              Account active (un-tick to deactivate)
            </label>
          </div>
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      )}
    </div>
  )
}