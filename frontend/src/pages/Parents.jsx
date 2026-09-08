import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'

const EMPTY_FORM = { name: '', email: '', phone: '', password: '', student_ids: [] }

export default function Parents() {
  const [rows, setRows] = useState([])
  const [allStudents, setAllStudents] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState(EMPTY_FORM)
  const [busy, setBusy] = useState(false)
  const [detail, setDetail] = useState(null)
  const [linked, setLinked] = useState([])
  const [childMap, setChildMap] = useState({})
  const [formSearch, setFormSearch] = useState('')
  const [detailSearch, setDetailSearch] = useState('')
  const [edit, setEdit] = useState({ name: '', email: '', phone: '', status: true })

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [parentsData, studentsData] = await Promise.all([
        api('/api/v1/parents'),
        api('/api/v1/students?pageSize=100'),
      ])
      setRows(parentsData.data || [])
      setAllStudents(studentsData.data || [])
      const map = {}
      for (const p of parentsData.data || []) {
        map[p.parent_id] = []
      }
      setChildMap(map)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function loadChildren(parentId) {
    setError('')
    try {
      const res = await api(`/api/v1/parents/${parentId}/students`)
      setChildMap((m) => ({ ...m, [parentId]: (res.data || []).map((s) => s.student_id) }))
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    if (rows.length) rows.forEach((p) => loadChildren(p.parent_id))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows])

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  function toggleFormStudent(id) {
    setForm((f) => ({
      ...f,
      student_ids: f.student_ids.includes(id)
        ? f.student_ids.filter((sid) => sid !== id)
        : [...f.student_ids, id],
    }))
  }

  async function create(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = { ...form }
      if (!body.password) delete body.password
      const res = await api('/api/v1/parents', { method: 'POST', body })
      setNotice(`Added parent ${res.parent.name}`)
      setForm(EMPTY_FORM)
      setFormSearch('')
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function openDetail(p) {
    setError('')
    setDetailSearch('')
    setLinked(childMap[p.parent_id] || [])
    setEdit({ name: p.name, email: p.email, phone: p.phone, status: p.status })
    setDetail(p)
  }

  function toggleLinked(id) {
    setLinked((prev) => (prev.includes(id) ? prev.filter((sid) => sid !== id) : [...prev, id]))
  }

  function setEditField(field, value) {
    setEdit((e) => ({ ...e, [field]: value }))
  }

  async function saveAll(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await api(`/api/v1/parents/${detail.parent_id}`, {
        method: 'PUT',
        body: { name: edit.name, email: edit.email, phone: edit.phone, status: edit.status },
      })
      await api(`/api/v1/parents/${detail.parent_id}/students`, {
        method: 'PUT',
        body: { student_ids: linked },
      })
      setNotice('Parent updated')
      setChildMap((m) => ({ ...m, [detail.parent_id]: linked }))
      setDetail(null)
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const studentNames = (ids) =>
    ids.length === 0
      ? 'None'
      : ids
          .map((id) => allStudents.find((s) => s.student_id === id))
          .filter(Boolean)
          .map((s) => `${s.first_name} ${s.last_name}`)
          .join(', ')

  function filterStudents(term) {
    const t = term.trim().toLowerCase()
    return allStudents.filter((s) => {
      if (s.active === false) return false
      if (!t) return true
      return `${s.first_name} ${s.last_name}`.toLowerCase().includes(t)
    })
  }

  return (
    <div>
      <h1>Parents</h1>
      {notice && <div className="alert alert-ok">{notice}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <form className="form-panel" onSubmit={create}>
        <h2>Add a parent</h2>
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
            Phone
            <input
              value={form.phone}
              onChange={(e) => set('phone', e.target.value)}
              placeholder="e.g. 555-222-3333"
              required
            />
          </label>
          <label>
            Password (optional — lets them open the portal)
            <input
              type="password"
              value={form.password}
              onChange={(e) => set('password', e.target.value)}
              placeholder="At least 8 characters"
              minLength={form.password ? 8 : undefined}
            />
          </label>
        </div>
        <h3>Linked children</h3>
        {allStudents.length === 0 ? (
          <p className="muted">No students available yet — enroll students first.</p>
        ) : (
          <>
            <input
              className="search"
              placeholder="Search student name…"
              value={formSearch}
              onChange={(e) => setFormSearch(e.target.value)}
            />
            <div className="roster">
              {filterStudents(formSearch).length === 0 ? (
                <p className="muted">No students match your search.</p>
              ) : (
                filterStudents(formSearch).map((s) => (
                  <label key={s.student_id} className="check">
                    <input
                      type="checkbox"
                      checked={form.student_ids.includes(s.student_id)}
                      onChange={() => toggleFormStudent(s.student_id)}
                    />
                    {s.first_name} {s.last_name} ({s.grade_level})
                  </label>
                ))
              )}
            </div>
          </>
        )}
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? 'Saving…' : 'Add parent'}
        </button>
      </form>

      <div className="card">
        {loading ? (
          <p className="muted">Loading…</p>
        ) : rows.length === 0 ? (
          <p className="muted">No parents found.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Children</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.parent_id}>
                  <td>{p.name}</td>
                  <td>{p.email}</td>
                  <td>{p.phone}</td>
                  <td>{studentNames(childMap[p.parent_id] || [])}</td>
                  <td>{p.status ? 'Active' : 'Inactive'}</td>
                  <td>
                    <button className="btn btn-ghost" onClick={() => openDetail(p)}>
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {detail && (
        <form className="form-panel" onSubmit={saveAll}>
          <div className="row space-between">
            <h2>Edit parent</h2>
            <button className="btn" type="button" onClick={() => setDetail(null)}>
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
              Phone
              <input
                value={edit.phone}
                onChange={(e) => setEditField('phone', e.target.value)}
                placeholder="e.g. 555-222-3333"
                required
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
          <h3>Linked children</h3>
          <div className="roster">
            <input
              className="search"
              placeholder="Search student name…"
              value={detailSearch}
              onChange={(e) => setDetailSearch(e.target.value)}
            />
            {filterStudents(detailSearch).length === 0 ? (
              <p className="muted">No students match your search.</p>
            ) : (
              filterStudents(detailSearch).map((s) => (
                <label key={s.student_id} className="check">
                  <input
                    type="checkbox"
                    checked={linked.includes(s.student_id)}
                    onChange={() => toggleLinked(s.student_id)}
                  />
                  {s.first_name} {s.last_name} ({s.grade_level})
                </label>
              ))
            )}
          </div>
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      )}
    </div>
  )
}