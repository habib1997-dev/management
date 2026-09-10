import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'
import Avatar from '../components/Avatar.jsx'

const STATUS_OPTIONS = ['present', 'absent', 'late', 'excused']
const today = () => {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

export default function Attendance() {
  const [courses, setCourses] = useState([])
  const [courseId, setCourseId] = useState('')
  const [date, setDate] = useState(today())
  const [students, setStudents] = useState([])
  const [parents, setParents] = useState({})
  const [statuses, setStatuses] = useState({})
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const loadCourses = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api('/api/v1/courses')
      setCourses(data.data || [])
      if (data.data?.length) setCourseId((prev) => prev || data.data[0].course_id)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCourses()
  }, [loadCourses])

  useEffect(() => {
    if (!courseId) {
      setStudents([])
      setParents({})
      setStatuses({})
      return
    }
    let cancelled = false
    setLoading(true)
    setError('')
    ;(async () => {
      try {
        const [detail, existing, parentRows] = await Promise.all([
          api(`/api/v1/courses/${courseId}`),
          api(`/api/v1/attendance/${courseId}?date=${date}`),
          api(`/api/v1/courses/${courseId}/parents`),
        ])
        if (cancelled) return
        const roster = detail.students || []
        setStudents(roster)
        const parentMap = {}
        for (const row of parentRows.data || []) parentMap[row.student_id] = row.parents || []
        setParents(parentMap)
        const initial = {}
        for (const r of existing.data || []) initial[r.student_id] = r.status
        setStatuses(initial)
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [courseId, date])

  function setStatus(sid, value) {
    setStatuses((s) => ({ ...s, [sid]: value }))
  }

  async function save(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const records = students
        .filter((s) => statuses[s.student_id])
        .map((s) => ({ student_id: s.student_id, status: statuses[s.student_id] }))
      if (records.length === 0) {
        setNotice('Nothing to save yet — mark a status (or use "Mark all present").')
        setBusy(false)
        return
      }
      await api('/api/v1/attendance', {
        method: 'POST',
        body: { course_id: courseId, date, records },
      })
      setNotice(`Attendance recorded for ${date}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function markAllPresent() {
    setStatuses((s) => {
      const next = { ...s }
      for (const st of students) if (!next[st.student_id]) next[st.student_id] = 'present'
      return next
    })
  }

  return (
    <div>
      <h1>Attendance</h1>
      {notice && <div className="alert alert-ok">{notice}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <form className="form-panel" onSubmit={save}>
        <div className="grid2">
          <label>
            Course
            <select value={courseId} onChange={(e) => setCourseId(e.target.value)} required>
              <option value="">Select a course…</option>
              {courses.map((c) => (
                <option key={c.course_id} value={c.course_id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Date
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
          </label>
        </div>

        {loading ? (
          <p className="muted">Loading students…</p>
        ) : students.length === 0 ? (
          <p className="muted">No students in this course.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Student</th>
                <th>Parent contact</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.student_id}>
                  <td>
                    <div className="name-cell">
                      <Avatar name={`${s.first_name} ${s.last_name}`} />
                      {s.first_name} {s.last_name}
                    </div>
                  </td>
                  <td className="parent-contact">
                    {(parents[s.student_id] || []).length === 0 ? (
                      '—'
                    ) : (
                      parents[s.student_id].map((p) => (
                        <div key={p.parent_id} className="parent-line">
                          <span className="parent-name">{p.name}</span>
                          <span className="muted">
                            {p.phone}
                            {p.email ? ` · ${p.email}` : ''}
                          </span>
                        </div>
                      ))
                    )}
                  </td>
                  <td>
                    <select
                      value={statuses[s.student_id] || ''}
                      onChange={(e) => setStatus(s.student_id, e.target.value)}
                    >
                      <option value="">—</option>
                      {STATUS_OPTIONS.map((st) => (
                        <option key={st} value={st}>
                          {st}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <div className="row">
          <button className="btn btn-primary" type="submit" disabled={busy || students.length === 0}>
            {busy ? 'Saving…' : 'Save attendance'}
          </button>
          <button
            type="button"
            className="btn"
            onClick={markAllPresent}
            disabled={busy || students.length === 0}
          >
            Mark all present
          </button>
        </div>
      </form>
    </div>
  )
}
