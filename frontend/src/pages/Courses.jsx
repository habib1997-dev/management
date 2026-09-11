import { useCallback, useEffect, useState } from 'react'
import { BookOpen, Users, X } from 'lucide-react'
import { api } from '../api.js'

const coursePill = (status) => {
  if (status === 'active') return <span className="pill pill-ok">Active</span>
  if (status === 'full') return <span className="pill pill-warn">Full</span>
  return <span className="pill pill-off">{status || 'Inactive'}</span>
}

const EMPTY_FORM = {
  name: '',
  teacher_id: '',
  grade_level: '',
  semester: '',
  max_students: 30,
}

export default function Courses() {
  const [rows, setRows] = useState([])
  const [teachers, setTeachers] = useState([])
  const [picker, setPicker] = useState([])
  const [pickerBusy, setPickerBusy] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState(EMPTY_FORM)
  const [busy, setBusy] = useState(false)
  const [detail, setDetail] = useState(null)
  const [roster, setRoster] = useState([])
  const [newTeacherId, setNewTeacherId] = useState('')
  const [rosterSearch, setRosterSearch] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [courses, teachersData] = await Promise.all([
        api('/api/v1/courses'),
        api('/api/v1/teachers'),
      ])
      setRows(courses.data || [])
      setTeachers(teachersData.data || [])
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
      setPicker(data.data || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setPickerBusy(false)
    }
  }, [])

  useEffect(() => {
    if (!detail) return
    const t = setTimeout(() => searchStudents(rosterSearch), 250)
    return () => clearTimeout(t)
  }, [detail, rosterSearch, searchStudents])

  useEffect(() => {
    if (detail) searchStudents('')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detail])

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function create(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const res = await api('/api/v1/courses', { method: 'POST', body: { ...form } })
      setNotice(`Created course "${res.course.name}"`)
      setForm(EMPTY_FORM)
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function openDetail(courseId) {
    setError('')
    try {
      const course = await api(`/api/v1/courses/${courseId}`)
      setDetail(course)
      setRoster(course.students.map((s) => s.student_id))
      setNewTeacherId(course.teacher_id)
    } catch (err) {
      setError(err.message)
    }
  }

  function toggleStudent(id) {
    setRoster((prev) =>
      prev.includes(id) ? prev.filter((sid) => sid !== id) : [...prev, id]
    )
  }

  async function saveRoster() {
    setBusy(true)
    setError('')
    try {
      const course = await api(`/api/v1/courses/${detail.course_id}/students`, {
        method: 'PUT',
        body: { student_ids: roster },
      })
      setNotice('Course roster updated')
      setDetail(course)
      setRoster(course.students.map((s) => s.student_id))
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function changeTeacher() {
    setBusy(true)
    setError('')
    try {
      const body = { teacher_id: newTeacherId || null }
      const course = await api(`/api/v1/courses/${detail.course_id}`, {
        method: 'PUT',
        body,
      })
      setNotice('Course teacher updated')
      setDetail({ ...detail, teacher_id: course.course?.teacher_id })
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const teacherName = (id) => teachers.find((t) => t.teacher_id === id)?.name || '—'
  const activeTeachers = teachers.filter((t) => t.status !== false)

  function pickerStudents() {
    const byId = {}
    for (const s of detail?.students || []) byId[s.student_id] = s
    for (const s of picker) if (!byId[s.student_id]) byId[s.student_id] = s
    let list = Object.values(byId).filter((s) => s.active !== false)
    const term = rosterSearch.trim().toLowerCase()
    if (term) {
      list = list.filter((s) =>
        `${s.first_name} ${s.last_name}`.toLowerCase().includes(term)
      )
    }
    return list
  }

  return (
    <div>
      <h1>Courses</h1>
      {notice && <div className="alert alert-ok">{notice}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <form className="form-panel" onSubmit={create}>
        <h2>Create a course</h2>
        <div className="grid2">
          <label>
            Course name
            <input value={form.name} onChange={(e) => set('name', e.target.value)} required />
          </label>
          <label>
            Teacher
            <select
              value={form.teacher_id}
              onChange={(e) => set('teacher_id', e.target.value)}
              required
            >
              <option value="">Select a teacher…</option>
              {activeTeachers.map((t) => (
                <option key={t.teacher_id} value={t.teacher_id}>
                  {t.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Grade level
            <input
              value={form.grade_level}
              onChange={(e) => set('grade_level', e.target.value)}
              required
            />
          </label>
          <label>
            Semester
            <input
              value={form.semester}
              onChange={(e) => set('semester', e.target.value)}
              placeholder="e.g. Fall 2026"
              required
            />
          </label>
          <label>
            Max students
            <input
              type="number"
              min="1"
              max="500"
              value={form.max_students}
              onChange={(e) => set('max_students', Number(e.target.value))}
              required
            />
          </label>
        </div>
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? 'Saving…' : 'Create course'}
        </button>
      </form>

      <div className="card">
        {loading ? (
          <p className="muted">Loading…</p>
        ) : rows.length === 0 ? (
          <p className="muted">No courses found.</p>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Teacher</th>
                  <th>Grade</th>
                  <th>Semester</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.course_id}>
                  <td>
                    <div className="name-cell">
                      <span className="cell-icon">
                        <BookOpen size={15} />
                      </span>
                      {c.name}
                    </div>
                  </td>
                  <td>{teacherName(c.teacher_id)}</td>
                  <td>{c.grade_level}</td>
                  <td>{c.semester}</td>
                  <td>{coursePill(c.status)}</td>
                  <td>
                    <button className="btn btn-ghost" onClick={() => openDetail(c.course_id)}>
                      <Users size={13} />
                      Roster
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
      </div>

      {detail && (
        <div className="form-panel">
          <div className="row space-between">
            <h2>
              {detail.name} <span className="muted">— {detail.students.length} student(s)</span>
            </h2>
            <button className="btn" onClick={() => setDetail(null)}>
              <X size={14} />
              Close
            </button>
          </div>

          <div className="row">
            <label>
              Teacher
              <select
                value={newTeacherId}
                onChange={(e) => setNewTeacherId(e.target.value)}
              >
                {newTeacherId &&
                  activeTeachers.every((t) => t.teacher_id !== newTeacherId) && (
                    <option value={newTeacherId} disabled>
                      {teacherName(newTeacherId)} (deactivated — reassign to change)
                    </option>
                  )}
                {activeTeachers.map((t) => (
                  <option key={t.teacher_id} value={t.teacher_id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </label>
            <button className="btn" onClick={changeTeacher} disabled={busy}>
              Change teacher
            </button>
          </div>

          <h3>Enrolled students</h3>
          <input
            className="search"
            placeholder="Search student name…"
            value={rosterSearch}
            onChange={(e) => setRosterSearch(e.target.value)}
          />
          <div className="roster">
            {rosterSearch.trim() === '' ? (
              pickerStudents().length === 0 ? (
                <p className="muted">No students enrolled yet — type a name to add them.</p>
              ) : (
                <>
                  <p className="muted">Current roster — type to search the whole school.</p>
                  {pickerStudents().map((s) => (
                    <label key={s.student_id} className="check">
                      <input
                        type="checkbox"
                        checked={roster.includes(s.student_id)}
                        onChange={() => toggleStudent(s.student_id)}
                      />
                      {s.first_name} {s.last_name} ({s.grade_level})
                    </label>
                  ))}
                </>
              )
            ) : pickerBusy && picker.length === 0 ? (
              <p className="muted">Searching…</p>
            ) : pickerStudents().length === 0 ? (
              <p className="muted">No students match your search.</p>
            ) : (
              pickerStudents().map((s) => (
                <label key={s.student_id} className="check">
                  <input
                    type="checkbox"
                    checked={roster.includes(s.student_id)}
                    onChange={() => toggleStudent(s.student_id)}
                  />
                  {s.first_name} {s.last_name} ({s.grade_level})
                </label>
              ))
            )}
          </div>
          <button className="btn btn-primary" onClick={saveRoster} disabled={busy}>
            Save roster
          </button>
        </div>
      )}
    </div>
  )
}