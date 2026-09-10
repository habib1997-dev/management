import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { Home, Users, GraduationCap, BookOpen, HeartHandshake, CalendarCheck, ClipboardCheck, Baby, LogOut } from 'lucide-react'
import { useAuth } from '../auth.jsx'
import { getCachedBrand } from '../brand.js'

const NAV = {
  admin: [
    { to: '/students', label: 'Students', icon: Users },
    { to: '/teachers', label: 'Teachers', icon: GraduationCap },
    { to: '/courses', label: 'Courses', icon: BookOpen },
    { to: '/parents', label: 'Parents', icon: HeartHandshake },
  ],
  teacher: [
    { to: '/attendance', label: 'Attendance', icon: CalendarCheck },
    { to: '/grades', label: 'Grades', icon: ClipboardCheck },
  ],
  parent: [{ to: '/portal', label: 'My Children', icon: Baby }],
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const brand = getCachedBrand()
  const items = NAV[user?.role] || []

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <img src={brand.logo_url} alt="" className="brand-logo" />
          <span>{brand.name}</span>
        </div>
        <nav>
          <span className="nav-section">Menu</span>
          <NavLink to="/" end>
            <Home size={16} strokeWidth={2.2} />
            Home
          </NavLink>
          {items.map((item) => {
            const Icon = item.icon
            return (
              <NavLink key={item.to} to={item.to}>
                <Icon size={16} strokeWidth={2.2} />
                {item.label}
              </NavLink>
            )
          })}
        </nav>
        <div className="sidebar-footer">
          <div className="who">
            <span className="who-name">{user?.email}</span>
            <span className="role-chip">{user?.role}</span>
          </div>
          <button className="btn btn-ghost" onClick={handleLogout}>
            <LogOut size={15} />
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