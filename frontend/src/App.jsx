import { Navigate, Route, Routes } from 'react-router-dom'
import RequireAuth from './components/RequireAuth.jsx'
import Layout from './components/Layout.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Students from './pages/Students.jsx'
import Teachers from './pages/Teachers.jsx'
import Courses from './pages/Courses.jsx'
import Parents from './pages/Parents.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/students" element={<Students />} />
          <Route path="/teachers" element={<Teachers />} />
          <Route path="/courses" element={<Courses />} />
          <Route path="/parents" element={<Parents />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}