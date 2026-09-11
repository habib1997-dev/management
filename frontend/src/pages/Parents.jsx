import { useCallback, useEffect, useState } from 'react'
import { Pencil } from 'lucide-react'
import { api } from '../api.js'
import Avatar from '../components/Avatar.jsx'

const EMPTY_FORM = {
  name: '',
  email: '',
  phone: '',
  password: '',
  status: true,
  student_ids: [],
}

export default function Parents() {
  const [rows, setRows] = useState([])
  const [formResults, setFormResults] = useState([])
  const [pickerBusy, setPickerBusy] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState(EMPTY_FORM)
  const [busy, setBusy] = useState(false)
  const [editing, setEditing] = useState(null)
  const [childMap, setChildMap] = useState({})
  const [childrenReady, setChildrenReady] = useState({})
  const [formSearch, setFormSearch] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const parentsData = await api('/api/v1/parents')
      setRows(parentsData.data || [])
      setChildMap({})
      setChildrenReady({})
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const searchStudents = useCallback(async (term) => {
    setPickerBusy(true)
    try {
      const params = new URLSearchParams()
      if (term) params.set('search', term)
      params.set('pageSize', '15')
      params.set('active', 'true')
      const data = await api(`/api/v1/students?${params.toString()}`)
      setFormResults(data.data || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setPickerBusy(false)
    }
  }, [])

  useEffect(() => {
    const t = setTimeout(() => searchStudents(formSearch), 250)
    return () => clearTimeout(t)
  }, [formSearch, searchStudents])

  async function loadChildren(parentId) {
    setError('')
    try {
      const res = await api(`/api/v1/parents/${parentId}/students`)
      setChildMap((m) => ({ ...m, [parentId]: res.data || [] }))
      setChildrenReady((r) => ({ ...r, [parentId]: true }))
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    if (rows.length) rows.forEach((p) => loadChildren(p.parent_id))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows])

  // Keep the edit form's child selection in sync once the children arrive
  // (the children list is the source of truth for what is currently linked).
  useEffect(() => {
    if (!editing) return
    const kids = childMap[editing.parent_id]
    if (!kids) return
    setForm((f) => ({ ...f, student_ids: kids.map((s) => s.student_id) }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [childMap, editing])

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  function resetForm() {
    setForm(EMPTY_FORM)
    setEditing(null)
    setFormSearch('')
    setFormResults([])
  }

  function toggleStudent(id) {
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
      delete body.status
      const res = await api('/api/v1/parents', { method: 'POST', body })
      setNotice(`Added parent ${res.parent.name}`)
      resetForm()
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function startEdit(p) {
    setError('')
    setFormSearch('')
    setFormResults([])
    setForm({
      name: p.name,
      email: p.email,
      phone: p.phone,
      password: '',
      status: p.status,
      student_ids: (childMap[p.parent_id] || []).map((s) => s.student_id),
    })
    setEditing(p)
  }

  async function saveEdit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = {
        name: form.name,
        email: form.email,
        phone: form.phone,
        status: form.status,
      }
      if (form.password) body.password = form.password
      await api(`/api/v1/parents/${editing.parent_id}`, { method: 'PUT', body })
      await api(`/api/v1/parents/${editing.parent_id}/students`, {
        method: 'PUT',
        body: { student_ids: form.student_ids },
      })
      setNotice('Parent updated')
      resetForm()
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const studentNames = (objs) =>
    !objs || objs.length === 0
      ? 'None'
      : objs
          .map((s) => `${s.first_name} ${s.last_name}`)
          .join(', ')

  function pickerStudents() {
    const byId = {}
    if (editing) {
      for (const s of childMap[editing.parent_id] || []) byId[s.student_id] = s
    }
    for (const s of formResults) if (!byId[s.student_id]) byId[s.student_id] = s
    let list = Object.values(byId).filter((s) => s.active !== false)
    const term = formSearch.trim().toLowerCase()
    if (term) {
      list = list.filter((s) =>
        `${s.first_name} ${s.last_name}`.toLowerCase().includes(term)
      )
    }
    return list
  }

  return (
    <div>
      <h1>Parents</h1>
      {notice && <div className="alert alert-ok">{notice}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <form className="form-panel" onSubmit={editing ? saveEdit : create}>
        <h2>{editing ? 'Edit parent' : 'Add a parent'}</h2>
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
              Password (optional — lets them open the portal)
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
        <h3>Linked children</h3>
        <input
          className="search"
          placeholder="Search student name…"
          value={formSearch}
          onChange={(e) => setFormSearch(e.target.value)}
        />
        <div className="roster">
          {formSearch.trim() === '' ? (
            pickerStudents().length === 0 ? (
              <p className="muted">No linked children yet — type a student's name to attach them.</p>
            ) : (
              <>
                <p className="muted">Currently linked children — type to search the whole school.</p>
                {pickerStudents().map((s) => (
                  <label key={s.student_id} className="check">
                    <input
                      type="checkbox"
                      checked={form.student_ids.includes(s.student_id)}
                      onChange={() => toggleStudent(s.student_id)}
                    />
                    {s.first_name} {s.last_name} ({s.grade_level})
                  </label>
                ))}
              </>
            )
          ) : pickerBusy && pickerStudents().length === 0 ? (
            <p className="muted">Searching…</p>
          ) : pickerStudents().length === 0 ? (
            <p className="muted">No students match your search.</p>
          ) : (
            pickerStudents().map((s) => (
              <label key={s.student_id} className="check">
                <input
                  type="checkbox"
                  checked={form.student_ids.includes(s.student_id)}
                  onChange={() => toggleStudent(s.student_id)}
                />
                {s.first_name} {s.last_name} ({s.grade_level})
              </label>
            ))
          )}
        </div>
        <div className="row">
          <button
            className="btn btn-primary"
            type="submit"
            disabled={busy || (editing && !childrenReady[editing.parent_id])}
          >
            {busy ? 'Saving…' : editing ? 'Save changes' : 'Add parent'}
          </button>
          {editing && (
            <button className="btn" type="button" onClick={resetForm}>
              Cancel edit
            </button>
          )}
        </div>
        {editing && !childrenReady[editing.parent_id] && (
          <p className="muted">Loading this parent's linked children — saving is enabled once loaded.</p>
        )}
      </form>

      <div className="card">
        {loading ? (
          <p className="muted">Loading…</p>
        ) : rows.length === 0 ? (
          <p className="muted">No parents found.</p>
        ) : (
          <div className="table-scroll">
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
                  <td>
                    <div className="name-cell">
                      <Avatar name={p.name} />
                      {p.name}
                    </div>
                  </td>
                  <td>{p.email}</td>
                  <td>{p.phone}</td>
                  <td>{studentNames(childMap[p.parent_id] || [])}</td>
                  <td>{p.status ? <span className="pill pill-ok">Active</span> : <span className="pill pill-off">Inactive</span>}</td>
                  <td>
                    <button className="btn btn-ghost" onClick={() => startEdit(p)}>
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