import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'

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
  const [allStudents, setAllStudents] = useState([])
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
      const [courses, teachersData, studentsData] = await Promise.all([
        api('/api/v1/courses'),
        api('/api/v1/teachers'),
        api('/api/v1/students?pageSize=100'),
      ])
      setRows(courses.data || [])
      setTeachers(teachersData.data || [])
      setAllStudents(studentsData.data || [])
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
      body.teacher_id = body.teacher_id || null
      if (!body.teacher_id) {
        delete body.teacher_id
      }
      const res = await api('/api/v1/courses', { method: 'POST', body })
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
            <select value={form.teacher_id} onChange={(e) => set('teacher_id', e.target.value)}>
              <option value="">(unassigned)</option>
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
                  <td>{c.name}</td>
                  <td>{teacherName(c.teacher_id)}</td>
                  <td>{c.grade_level}</td>
                  <td>{c.semester}</td>
                  <td>{c.status}</td>
                  <td>
                    <button className="btn btn-ghost" onClick={() => openDetail(c.course_id)}>
                      Roster
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {detail && (
        <div className="form-panel">
          <div className="row space-between">
            <h2>
              {detail.name} <span className="muted">— {detail.students.length} student(s)</span>
            </h2>
            <button className="btn" onClick={() => setDetail(null)}>
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
                <option value="">(unassigned)</option>
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
          {allStudents.length === 0 ? (
            <p className="muted">No students available to roster.</p>
          ) : (
            <>
              <input
                className="search"
                placeholder="Search student name…"
                value={rosterSearch}
                onChange={(e) => setRosterSearch(e.target.value)}
              />
              <div className="roster">
                {filterStudents(rosterSearch).length === 0 ? (
                  <p className="muted">No students match your search.</p>
                ) : (
                  filterStudents(rosterSearch).map((s) => (
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
            </>
          )}
          <button className="btn btn-primary" onClick={saveRoster} disabled={busy}>
            Save roster
          </button>
        </div>
      )}
    </div>
  )
}