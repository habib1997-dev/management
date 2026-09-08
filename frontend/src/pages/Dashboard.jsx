import { useAuth } from '../auth.jsx'

export default function Dashboard() {
  const { user } = useAuth()
  return (
    <div>
      <h1>Welcome, {user?.email}</h1>
      <div className="card">
        <p>
          You are signed in as <strong>{user?.role}</strong>.
        </p>
        {user?.role === 'admin' && (
          <p className="muted">
            Use the menu on the left to manage students, teachers, courses, and parents.
          </p>
        )}
        {user?.role === 'teacher' && (
          <p className="muted">
            Teacher tools (attendance &amp; grades) are coming in the next release.
          </p>
        )}
        {user?.role === 'parent' && (
          <p className="muted">
            The parent portal (your children&apos;s grades and attendance) is coming in the
            next release.
          </p>
        )}
      </div>
    </div>
  )
}