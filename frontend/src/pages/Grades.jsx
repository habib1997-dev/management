import { useCallback, useEffect, useState } from 'react'
import { Pencil, Save, X } from 'lucide-react'
import { api } from '../api.js'
import Avatar from '../components/Avatar.jsx'

const ASSIGNMENT_TYPES = ['quiz', 'test', 'homework', 'final']
const today = () => {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}
const blankEntry = (overrides = {}) => ({
  grade_value: '',
  assignment_type: 'homework',
  date_assigned: today(),
  date_due: today(),
  ...overrides,
})

export default function Grades() {
  const [courses, setCourses] = useState([])
  const [courseId, setCourseId] = useState('')
  const [students, setStudents] = useState([])
  const [parents, setParents] = useState({})
  const [recorded, setRecorded] = useState([])
  const [addEntries, setAddEntries] = useState({})
  const [editingId, setEditingId] = useState(null)
  const [editDraft, setEditDraft] = useState(null)
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
      setRecorded([])
      setAddEntries({})
      return
    }
    let cancelled = false
    setLoading(true)
    setError('')
    ;(async () => {
      try {
        const [detail, grades, parentRows] = await Promise.all([
          api(`/api/v1/courses/${courseId}`),
          api(`/api/v1/courses/${courseId}/grades`),
          api(`/api/v1/courses/${courseId}/parents`),
        ])
        if (cancelled) return
        const roster = detail.students || []
        setStudents(roster)
        const parentMap = {}
        for (const row of parentRows.data || []) parentMap[row.student_id] = row.parents || []
        setParents(parentMap)
        setRecorded(grades.data || [])
        const empty = {}
        for (const s of roster) empty[s.student_id] = blankEntry()
        setAddEntries(empty)
        setEditingId(null)
        setEditDraft(null)
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [courseId])

  const reloadGrades = useCallback(async () => {
    if (!courseId) return
    try {
      const grades = await api(`/api/v1/courses/${courseId}/grades`)
      setRecorded(grades.data || [])
    } catch (err) {
      setError(err.message)
    }
  }, [courseId])

  function setAddField(sid, field, value) {
    setAddEntries((e) => ({ ...e, [sid]: { ...(e[sid] || blankEntry()), [field]: value } }))
  }

  async function addGrade(s) {
    setBusy(true)
    setError('')
    setNotice('')
    const ent = addEntries[s.student_id] || blankEntry()
    const date_assigned = ent.date_assigned || today()
    const date_due = ent.date_due || today()
    if (date_due < date_assigned) {
      setError('Due date cannot be before the assigned date.')
      setBusy(false)
      return
    }
    const body = {
      student_id: s.student_id,
      course_id: courseId,
      grade_value: Number(ent.grade_value),
      assignment_type: ent.assignment_type || 'homework',
      date_assigned,
      date_due,
    }
    try {
      const res = await api('/api/v1/grades', { method: 'POST', body })
      setNotice(`Grade ${res.grade.grade_value} recorded for ${s.first_name} ${s.last_name}`)
      setAddEntries((e) => ({ ...e, [s.student_id]: blankEntry() }))
      await reloadGrades()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function startEdit(g) {
    setEditingId(g.grade_id)
    setEditDraft({
      grade_value: String(g.grade_value),
      assignment_type: g.assignment_type || 'homework',
      date_assigned: g.date_assigned,
      date_due: g.date_due,
    })
  }

  function cancelEdit() {
    setEditingId(null)
    setEditDraft(null)
  }

  function editField(field, value) {
    setEditDraft((d) => ({ ...d, [field]: value }))
  }

  function studentName(g) {
    const s = students.find((x) => x.student_id === g.student_id)
    return s ? `${s.first_name} ${s.last_name}` : g.student_id
  }

  async function saveEdit(g) {
    if (!editDraft) return
    setBusy(true)
    setError('')
    setNotice('')
    const date_assigned = editDraft.date_assigned || today()
    const date_due = editDraft.date_due || today()
    if (date_due < date_assigned) {
      setError('Due date cannot be before the assigned date.')
      setBusy(false)
      return
    }
    const body = {
      grade_value: Number(editDraft.grade_value),
      assignment_type: editDraft.assignment_type || 'homework',
      date_assigned,
      date_due,
    }
    try {
      const res = await api(`/api/v1/grades/${g.grade_id}`, { method: 'PUT', body })
      setNotice(`Grade ${res.grade.grade_value} saved for ${studentName(g)}`)
      cancelEdit()
      await reloadGrades()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function typeSelect(value, onChange) {
    return (
      <select value={value} onChange={onChange}>
        {ASSIGNMENT_TYPES.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>
    )
  }

  let gradeFormBody
  if (loading) {
    gradeFormBody = <p className="muted">Loading…</p>
  } else if (students.length === 0) {
    gradeFormBody = <p className="muted">No students in this course.</p>
  } else {
    gradeFormBody = (
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Student</th>
              <th>Parent contact</th>
              <th>Grade (0–100)</th>
              <th>Type</th>
              <th>Assigned</th>
            <th>Due</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {students.map((s) => {
            const ent = addEntries[s.student_id] || blankEntry()
            return (
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
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="0.5"
                    value={ent.grade_value}
                    onChange={(e) => setAddField(s.student_id, 'grade_value', e.target.value)}
                    placeholder="0–100"
                  />
                </td>
                <td>{typeSelect(ent.assignment_type, (e) => setAddField(s.student_id, 'assignment_type', e.target.value))}</td>
                <td>
                  <input type="date" value={ent.date_assigned} onChange={(e) => setAddField(s.student_id, 'date_assigned', e.target.value)} />
                </td>
                <td>
                  <input type="date" value={ent.date_due} onChange={(e) => setAddField(s.student_id, 'date_due', e.target.value)} />
                </td>
                <td>
                  <button className="btn btn-ghost" onClick={() => addGrade(s)} disabled={busy || !ent.grade_value}>
                    Record
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      </div>
    )
  }

  let recordedBody
  if (loading) {
    recordedBody = <p className="muted">Loading…</p>
  } else if (recorded.length === 0) {
    recordedBody = <p className="muted">No grades recorded yet.</p>
  } else {
    recordedBody = (
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Student</th>
              <th>Grade</th>
              <th>Type</th>
              <th>Assigned</th>
              <th>Due</th>
              <th>Graded</th>
              <th />
            </tr>
          </thead>
        <tbody>
          {recorded.map((g) =>
            editingId === g.grade_id ? (
              <tr key={g.grade_id}>
                <td>
                  <div className="name-cell">
                    <Avatar name={studentName(g)} />
                    {studentName(g)}
                  </div>
                </td>
                <td>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="0.5"
                    value={editDraft?.grade_value || ''}
                    onChange={(e) => editField('grade_value', e.target.value)}
                    placeholder="0–100"
                  />
                </td>
                <td>{typeSelect(editDraft?.assignment_type || 'homework', (e) => editField('assignment_type', e.target.value))}</td>
                <td>
                  <input type="date" value={editDraft?.date_assigned || ''} onChange={(e) => editField('date_assigned', e.target.value)} />
                </td>
                <td>
                  <input type="date" value={editDraft?.date_due || ''} onChange={(e) => editField('date_due', e.target.value)} />
                </td>
                <td>{g.date_graded}</td>
                <td>
                  <button className="btn btn-ghost" onClick={() => saveEdit(g)} disabled={busy || !editDraft?.grade_value}>
                    <Save size={13} />
                    Save
                  </button>{' '}
                  <button className="btn btn-ghost" onClick={cancelEdit}>
                    <X size={13} />
                    Cancel
                  </button>
                </td>
              </tr>
            ) : (
              <tr key={g.grade_id}>
                <td>
                  <div className="name-cell">
                    <Avatar name={studentName(g)} />
                    {studentName(g)}
                  </div>
                </td>
                <td>
                  <span className="pill pill-score">{g.grade_value}</span>
                </td>
                <td>{g.assignment_type || '—'}</td>
                <td>{g.date_assigned}</td>
                <td>{g.date_due}</td>
                <td>{g.date_graded}</td>
                <td>
                  <button className="btn btn-ghost" onClick={() => startEdit(g)} disabled={busy}>
                    <Pencil size={13} />
                    Edit
                  </button>
                </td>
              </tr>
            )
          )}
        </tbody>
      </table>
      </div>
    )
  }

  return (
    <div>
      <h1>Grades</h1>
      {notice && <div className="alert alert-ok">{notice}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <div className="form-panel">
        <label>
          Course
          {' '}
          <select value={courseId} onChange={(e) => setCourseId(e.target.value)} required>
            <option value="">Select a course…</option>
            {courses.map((c) => (
              <option key={c.course_id} value={c.course_id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="form-panel">
        <h2>Record a new grade</h2>
        {gradeFormBody}
      </div>

      <div className="card">
        <h2>Recorded grades for this course</h2>
        {recordedBody}
      </div>
    </div>
  )
}