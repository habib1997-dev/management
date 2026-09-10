import { useCallback, useEffect, useState } from 'react'
import { Download } from 'lucide-react'
import { api, downloadFile } from '../api.js'
import { useAuth } from '../auth.jsx'
import Avatar from '../components/Avatar.jsx'

const statusPill = (status) => {
  if (status === 'present') return <span className="pill pill-ok">Present</span>
  if (status === 'excused') return <span className="pill pill-warn">Excused</span>
  if (status === 'late') return <span className="pill pill-warn">Late</span>
  return <span className="pill pill-off">Absent</span>
}

export default function Portal() {
  const { user } = useAuth()
  const [parent, setParent] = useState(null)
  const [children, setChildren] = useState([])
  const [loading, setLoading] = useState(false)
  const [busyId, setBusyId] = useState(null)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    if (!user?.parent_id) return
    setLoading(true)
    setError('')
    try {
      const data = await api(`/api/v1/parents/${user.parent_id}/portal`)
      const p = data.parents?.[0]
      setParent(p || null)
      setChildren(p?.children || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [user?.parent_id])

  useEffect(() => {
    load()
  }, [load])

  async function downloadReport(child) {
    setBusyId(child.student_id)
    setError('')
    try {
      const filename = `report_card_${child.last_name}_${child.first_name}.pdf`
      await downloadFile(`/api/v1/reports/portal/${child.student_id}`, filename)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div>
      <h1>Parent Portal</h1>
      {error && <div className="alert alert-error">{error}</div>}
      {loading ? (
        <p className="muted">Loading…</p>
      ) : !parent ? (
        <div className="card">
          <p className="muted">
            No children are linked to your account yet. Contact the school office if you expected to
            see someone here.
          </p>
        </div>
      ) : (
        <>
          <div className="card">
            <p>
              <strong>{parent.name}</strong>
            </p>
            <p className="muted">{parent.email}</p>
          </div>
          {children.map((child) => (
            <div className="card" key={child.student_id}>
              <div className="row space-between">
                <div className="child-hero">
                  <Avatar name={`${child.first_name} ${child.last_name}`} />
                  <h2 style={{ margin: 0 }}>
                    {child.first_name} {child.last_name}
                    {child.grade_level ? ` · ${child.grade_level}` : ''}
                  </h2>
                </div>
                <button className="btn btn-ghost" onClick={() => downloadReport(child)} disabled={busyId === child.student_id}>
                  <Download size={14} />
                  {busyId === child.student_id ? 'Preparing…' : 'Download report card (PDF)'}
                </button>
              </div>

              <h3>Attendance</h3>
              {child.attendance.length === 0 ? (
                <p className="muted">No attendance records yet.</p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Course</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {child.attendance.map((a) => (
                      <tr key={a.attendance_id}>
                        <td>{a.date}</td>
                        <td>{a.course_name || '—'}</td>
                        <td>{statusPill(a.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              <h3>Grades</h3>
              {child.grades.length === 0 ? (
                <p className="muted">No grades recorded yet.</p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Course</th>
                      <th>Type</th>
                      <th>Grade</th>
                      <th>Due</th>
                    </tr>
                  </thead>
                  <tbody>
                    {child.grades.map((g) => (
                      <tr key={g.grade_id}>
                        <td>{g.course_name || '—'}</td>
                        <td>{g.assignment_type || '—'}</td>
                        <td>
                          <span className="pill pill-score">{g.grade_value}</span>
                        </td>
                        <td>{g.date_due}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          ))}
        </>
      )}
    </div>
  )
}
