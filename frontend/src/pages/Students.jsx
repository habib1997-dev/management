import { useCallback, useEffect, useState } from 'react'
import { Download, Pencil, ChevronLeft, ChevronRight } from 'lucide-react'
import { api, downloadFile } from '../api.js'
import Avatar from '../components/Avatar.jsx'

const EMPTY_FORM = {
  first_name: '',
  last_name: '',
  date_of_birth: '',
  grade_level: '',
  email: '',
  phone: '',
  active: true,
}

const PAGE_SIZE = 50

function submitLabel(busy, editing) {
  if (busy) return 'Saving…'
  if (editing) return 'Save changes'
  return 'Enroll student'
}

export default function Students() {
  const [rows, setRows] = useState([])
  const [search, setSearch] = useState('')
  const [gradeLevel, setGradeLevel] = useState('')
  const [active, setActive] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
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
    params.set('page', String(page))
    params.set('pageSize', String(PAGE_SIZE))
    try {
      const data = await api(`/api/v1/students?${params.toString()}`)
      setRows(data.data || [])
      setTotal(data.meta?.total || 0)
      setTotalPages(Math.max(1, Math.ceil((data.meta?.total || 0) / PAGE_SIZE)))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [search, gradeLevel, active, page])

  useEffect(() => {
    setPage(1)
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

  async function startEdit(s) {
    setEditing(s)
    setError('')
    let detail = s
    try {
      const res = await api(`/api/v1/students/${s.student_id}`)
      if (res?.student_id) detail = res
    } catch {
      // fall back to the list row (date field will then be empty)
    }
    setForm({
      first_name: detail.first_name,
      last_name: detail.last_name,
      date_of_birth: detail.date_of_birth ? detail.date_of_birth.slice(0, 10) : '',
      grade_level: detail.grade_level,
      email: detail.email || '',
      phone: detail.phone || '',
      active: detail.active,
    })
  }

  async function saveEdit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = { ...form }
      if (!body.email) delete body.email
      if (!body.phone) delete body.phone
      if (!body.date_of_birth) delete body.date_of_birth
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

  async function exportCsv(path, filename) {
    try {
      await downloadFile(path, filename)
    } catch (err) {
      setError(err.message)
    }
  }

  let listBody
  if (loading) {
    listBody = <p className="muted">Loading…</p>
  } else if (rows.length === 0) {
    listBody = <p className="muted">No students found.</p>
  } else {
    listBody = (
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Grade</th>
              <th>Enrolled</th>
              <th>Status</th>
              <th>Email</th>
              <th>Phone</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.student_id}>
                <td>
                  <div className="name-cell">
                    <Avatar name={`${s.first_name} ${s.last_name}`} />
                    {s.first_name} {s.last_name}
                  </div>
                </td>
                <td>{s.grade_level}</td>
                <td>{s.enrollment_date}</td>
                <td>
                  {s.active ? <span className="pill pill-ok">Active</span> : <span className="pill pill-off">Inactive</span>}
                </td>
                <td>{s.email || '—'}</td>
                <td>{s.phone || '—'}</td>
                <td>
                  <button className="btn btn-ghost" onClick={() => startEdit(s)}>
                    <Pencil size={13} />
                    Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <div>
      <div className="row space-between" style={{ marginTop: 0 }}>
        <h1>Students</h1>
        <div className="row-actions">
          <button className="btn" onClick={() => exportCsv('/api/v1/export/students.csv', 'students.csv')}>
            <Download size={14} />
            Download students CSV
          </button>
          <button className="btn" onClick={() => exportCsv('/api/v1/export/grades.csv', 'grades.csv')}>
            <Download size={14} />
            Download grades CSV
          </button>
        </div>
      </div>
      {notice && <div className="alert alert-ok">{notice}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <form className="form-panel" onSubmit={editing ? saveEdit : enroll}>
        <h2>{editing ? 'Edit student' : 'Enroll a new student'}</h2>
        <div className="grid2">
          <label>
            First name
            {' '}
            <input value={form.first_name} onChange={(e) => set('first_name', e.target.value)} required />
          </label>
          <label>
            Last name
            {' '}
            <input value={form.last_name} onChange={(e) => set('last_name', e.target.value)} required />
          </label>
          <label>
            Date of birth
            {' '}
            <input
              type="date"
              value={form.date_of_birth}
              onChange={(e) => set('date_of_birth', e.target.value)}
              required
            />
          </label>
          <label>
            Grade level
            {' '}
            <input
              value={form.grade_level}
              onChange={(e) => set('grade_level', e.target.value)}
              placeholder="e.g. 9, K, O-Level"
              required
            />
          </label>
          <label>
            Email
            {' '}
            <input type="email" value={form.email} onChange={(e) => set('email', e.target.value)} />
          </label>
          <label>
            Phone
            {' '}
            <input value={form.phone} onChange={(e) => set('phone', e.target.value)} />
          </label>
          {editing && (
            <label className="check">
              <input
                type="checkbox"
                checked={form.active}
                onChange={(e) => set('active', e.target.checked)}
              />
              {' '}
              Account active (un-tick to deactivate)
            </label>
          )}
        </div>
        <div className="row">
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {submitLabel(busy, editing)}
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
          <span className="muted">
            {total} student(s)
          </span>
        </div>
        {listBody}
        {total > PAGE_SIZE && (
          <div className="row pagination">
            <button className="btn" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1 || loading}>
              <ChevronLeft size={14} />
              Prev
            </button>
            <span className="muted">
              Page {page} of {totalPages}
            </span>
            <button className="btn" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages || loading}>
              Next
              <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}