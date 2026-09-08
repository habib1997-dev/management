import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'

const EMPTY_FORM = {
  first_name: '',
  last_name: '',
  date_of_birth: '',
  grade_level: '',
  email: '',
  phone: '',
  active: true,
}

export default function Students() {
  const [rows, setRows] = useState([])
  const [search, setSearch] = useState('')
  const [gradeLevel, setGradeLevel] = useState('')
  const [active, setActive] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState(EMPTY_FORM)
  const [editing, setEditing] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (gradeLevel) params.set('gradeLevel', gradeLevel)
    if (active !== '') params.set('active', active)
    try {
      const data = await api(`/api/v1/students?${params.toString()}`)
      setRows(data.data || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [search, gradeLevel, active])

  useEffect(() => {
    const t = setTimeout(load, 250)
    return () => clearTimeout(t)
  }, [load])

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  function resetForm() {
    setForm(EMPTY_FORM)
    setEditing(null)
  }

  async function enroll(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = { ...form }
      if (!body.email) delete body.email
      if (!body.phone) delete body.phone
      const res = await api('/api/v1/students', { method: 'POST', body })
      setNotice(`Enrolled ${res.student.first_name} ${res.student.last_name}`)
      resetForm()
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function startEdit(s) {
    setEditing(s)
    setForm({
      first_name: s.first_name,
      last_name: s.last_name,
      date_of_birth: s.date_of_birth ? s.date_of_birth.slice(0, 10) : '',
      grade_level: s.grade_level,
      email: s.email || '',
      phone: s.phone || '',
      active: s.active,
    })
  }

  async function saveEdit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = { ...form }
      delete body.date_of_birth
      delete body.grade_level
      if (!body.email) delete body.email
      if (!body.phone) delete body.phone
      await api(`/api/v1/students/${editing.student_id}`, { method: 'PUT', body })
      setNotice('Student updated')
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
      <h1>Students</h1>
      {notice && <div className="alert alert-ok">{notice}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <form className="form-panel" onSubmit={editing ? saveEdit : enroll}>
        <h2>{editing ? 'Edit student' : 'Enroll a new student'}</h2>
        <div className="grid2">
          <label>
            First name
            <input value={form.first_name} onChange={(e) => set('first_name', e.target.value)} required />
          </label>
          <label>
            Last name
            <input value={form.last_name} onChange={(e) => set('last_name', e.target.value)} required />
          </label>
          <label>
            Date of birth
            <input
              type="date"
              value={form.date_of_birth}
              onChange={(e) => set('date_of_birth', e.target.value)}
              disabled={Boolean(editing)}
              required
            />
          </label>
          <label>
            Grade level
            <input
              value={form.grade_level}
              onChange={(e) => set('grade_level', e.target.value)}
              placeholder="e.g. 9, K, O-Level"
              disabled={Boolean(editing)}
              required
            />
          </label>
          <label>
            Email
            <input type="email" value={form.email} onChange={(e) => set('email', e.target.value)} />
          </label>
          <label>
            Phone
            <input value={form.phone} onChange={(e) => set('phone', e.target.value)} />
          </label>
          {editing && (
            <label className="check">
              <input
                type="checkbox"
                checked={form.active}
                onChange={(e) => set('active', e.target.checked)}
              />
              Account active (un-tick to deactivate)
            </label>
          )}
        </div>
        <div className="row">
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? 'Saving…' : editing ? 'Save changes' : 'Enroll student'}
          </button>
          {editing && (
            <button className="btn" type="button" onClick={resetForm}>
              Cancel edit
            </button>
          )}
        </div>
      </form>

      <div className="card">
        <div className="filters">
          <input
            className="search"
            placeholder="Search by name / grade…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <input
            placeholder="Grade level filter"
            value={gradeLevel}
            onChange={(e) => setGradeLevel(e.target.value)}
          />
          <select value={active} onChange={(e) => setActive(e.target.value)}>
            <option value="">All statuses</option>
            <option value="true">Active only</option>
            <option value="false">Inactive only</option>
          </select>
        </div>
        {loading ? (
          <p className="muted">Loading…</p>
        ) : rows.length === 0 ? (
          <p className="muted">No students found.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Grade</th>
                <th>Enrolled</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((s) => (
                <tr key={s.student_id}>
                  <td>
                    {s.first_name} {s.last_name}
                  </td>
                  <td>{s.grade_level}</td>
                  <td>{s.enrollment_date}</td>
                  <td>{s.active ? 'Active' : 'Inactive'}</td>
                  <td>
                    <button className="btn btn-ghost" onClick={() => startEdit(s)}>
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}