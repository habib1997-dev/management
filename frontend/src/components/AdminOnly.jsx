import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../auth.jsx'

export default function AdminOnly() {
  const { user } = useAuth()
  if (user?.role !== 'admin') return <Navigate to="/" replace />
  return <Outlet />
}