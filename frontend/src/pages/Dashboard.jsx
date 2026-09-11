import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Users, GraduationCap, BookOpen, HeartHandshake, CalendarCheck, ClipboardCheck, Baby, FileDown } from 'lucide-react'
import { useAuth } from '../auth.jsx'
import { api, downloadFile } from '../api.js'

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="stat-card">
      <span className="stat-icon">
        <Icon size={20} strokeWidth={2.1} />
      </span>
      <div>
        <div className="stat-num">{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [children, setChildren] = useState(null)
  const [reportKids, setReportKids] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    if (user?.role === 'admin') {
      ;(async () => {
        try {
          const [students, teachers, courses, parents] = await Promise.all([
            api('/api/v1/students?pageSize=1'),
            api('/api/v1/teachers'),
            api('/api/v1/courses'),
            api('/api/v1/parents'),
          ])
          if (!cancelled) {
            setStats([
              { icon: Users, label: 'Students', value: students.meta?.total ?? students.data?.length ?? 0 },
              { icon: GraduationCap, label: 'Teachers', value: teachers.meta?.total ?? teachers.data?.length ?? 0 },
              { icon: BookOpen, label: 'Courses', value: courses.meta?.total ?? courses.data?.length ?? 0 },
              { icon: HeartHandshake, label: 'Parents', value: parents.meta?.total ?? parents.data?.length ?? 0 },
            ])
          }
        } catch (err) {
          if (!cancelled) setError(err.message)
        }
      })()
    } else if (user?.role === 'parent' && user?.parent_id) {
      ;(async () => {
        try {
          const data = await api(`/api/v1/parents/${user.parent_id}/portal`)
          if (!cancelled) setChildren(data.parents?.[0]?.children?.length ?? 0)
        } catch (err) {
          if (!cancelled) setError(err.message)
        }
      })()
    }
    return () => {
      cancelled = true
    }
  }, [user])

  async function showReportPicker() {
    if (reportKids && reportKids.length > 1) {
      setReportKids(null)
      return
    }
    try {
      const data = await api(`/api/v1/parents/${user.parent_id}/portal`)
      const kids = data.parents?.[0]?.children || []
      if (kids.length === 1) {
        const child = kids[0]
        await downloadFile(
          `/api/v1/reports/portal/${child.student_id}`,
          `report_card_${child.last_name}_${child.first_name}.pdf`
        )
      } else {
        setReportKids(kids)
      }
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <div className="dash-hello">
        <h1>Welcome, {user?.email}</h1>
        <p className="sub">
          {user?.role === 'admin' && 'Here is what is happening across your school.'}
          {user?.role === 'teacher' && 'Mark attendance and record grades for your courses.'}
          {user?.role === 'parent' && 'Follow your children’s progress from one place.'}
        </p>
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      {user?.role === 'admin' && stats && (
        <div className="stat-grid">
          {stats.map((s) => (
            <StatCard key={s.label} {...s} />
          ))}
        </div>
      )}

      {user?.role === 'parent' && children !== null && (
        <div className="stat-grid">
          <StatCard icon={Baby} label="Children at school" value={children} />
        </div>
      )}

      <div className="quick-grid">
        {user?.role === 'admin' && (
          <>
            <div className="quick-card">
              <h3>Students</h3>
              <p className="muted" style={{ margin: 0, fontSize: 14 }}>
                Enroll new students, edit profiles, and download CSV exports.
              </p>
              <Link className="btn btn-primary" to="/students">
                Manage students
              </Link>
            </div>
            <div className="quick-card">
              <h3>Classes</h3>
              <p className="muted" style={{ margin: 0, fontSize: 14 }}>
                Create courses, assign teachers, and manage rosters.
              </p>
              <Link className="btn" to="/courses">
                Manage courses
              </Link>
            </div>
          </>
        )}

        {user?.role === 'teacher' && (
          <>
            <div className="quick-card">
              <h3>Attendance</h3>
              <p className="muted" style={{ margin: 0, fontSize: 14 }}>
                Record who is present, absent, late, or excused.
              </p>
              <Link className="btn btn-primary" to="/attendance">
                <CalendarCheck size={15} />
                Open attendance
              </Link>
            </div>
            <div className="quick-card">
              <h3>Grades</h3>
              <p className="muted" style={{ margin: 0, fontSize: 14 }}>
                Record quizzes, tests, homework, and final grades.
              </p>
              <Link className="btn" to="/grades">
                <ClipboardCheck size={15} />
                Open grades
              </Link>
            </div>
          </>
        )}

        {user?.role === 'parent' && (
          <div className="quick-card">
            <h3>My Children</h3>
            <p className="muted" style={{ margin: 0, fontSize: 14 }}>
              See attendance, grades, and download report cards.
            </p>
            <Link className="btn btn-primary" to="/portal">
              <Baby size={15} />
              Open portal
            </Link>
            {children > 0 && (
              <button className="btn" onClick={showReportPicker}>
                <FileDown size={15} />
                {reportKids && reportKids.length > 1 ? 'Close' : 'Download report card'}
              </button>
            )}
            {reportKids && reportKids.length > 1 && (
              <div className="report-child-picker">
                <p className="muted" style={{ margin: 0, fontSize: 13 }}>
                  Whose report card?
                </p>
                {reportKids.map((c) => (
                  <button
                    key={c.student_id}
                    className="btn"
                    style={{ marginRight: 8, marginTop: 6 }}
                    onClick={async () => {
                      try {
                        await downloadFile(
                          `/api/v1/reports/portal/${c.student_id}`,
                          `report_card_${c.last_name}_${c.first_name}.pdf`
                        )
                        setReportKids(null)
                      } catch (err) {
                        setError(err.message)
                      }
                    }}
                  >
                    {c.first_name} {c.last_name}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}