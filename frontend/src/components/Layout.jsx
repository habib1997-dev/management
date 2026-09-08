import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'

const NAV = {
  admin: [
    { to: '/students', label: 'Students' },
    { to: '/teachers', label: 'Teachers' },
    { to: '/courses', label: 'Courses' },
    { to: '/parents', label: 'Parents' },
  ],
  teacher: [],
  parent: [],
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const items = NAV[user?.role] || []

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">School System</div>
        <nav>
          <NavLink to="/" end>
            Home
          </NavLink>
          {items.map((item) => (
            <NavLink key={item.to} to={item.to}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="who">
            {user?.email}
            <span className="role-chip">{user?.role}</span>
          </div>
          <button className="btn btn-ghost" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}