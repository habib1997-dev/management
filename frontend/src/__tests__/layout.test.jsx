import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Layout from '../components/Layout.jsx'
import { getCachedBrand } from '../brand.js'

const mocks = vi.hoisted(() => ({
  logout: vi.fn(),
}))

vi.mock('../auth.jsx', () => ({
  useAuth: () => mocks.authValue,
}))

function renderLayout() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Layout />
    </MemoryRouter>
  )
}

const adminUser = { role: 'admin', user_id: 'u1', email: 'admin@schoolsystem.com' }

beforeEach(() => {
  vi.clearAllMocks()
  mocks.authValue = { user: adminUser, logout: mocks.logout }
})

describe('Layout', () => {
  it('shows the brand block and the admin menu', () => {
    renderLayout()

    const brand = getCachedBrand()
    expect(screen.getByText(brand.name)).toBeInTheDocument()
    for (const label of ['Students', 'Teachers', 'Courses', 'Parents']) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
    expect(screen.queryByText('Attendance')).not.toBeInTheDocument()
    expect(screen.queryByText('My Children')).not.toBeInTheDocument()
  })

  it('shows teacher navigation for teachers', () => {
    mocks.authValue = { user: { role: 'teacher', user_id: 'u2', email: 't@school.com' }, logout: mocks.logout }
    renderLayout()

    expect(screen.getByText('Attendance')).toBeInTheDocument()
    expect(screen.getByText('Grades')).toBeInTheDocument()
    expect(screen.queryByText('Students')).not.toBeInTheDocument()
  })

  it('shows the parent menu for parents', () => {
    mocks.authValue = { user: { role: 'parent', user_id: 'u3', email: 'p@family.net' }, logout: mocks.logout }
    renderLayout()

    expect(screen.getByText('My Children')).toBeInTheDocument()
    expect(screen.queryByText('Students')).not.toBeInTheDocument()
  })

  it('logs out through the footer button', async () => {
    const user1 = userEvent.setup()
    renderLayout()

    await user1.click(screen.getByRole('button', { name: /log out/i }))
    expect(mocks.logout).toHaveBeenCalled()
  })

  it('shows the current user email and role chip', () => {
    renderLayout()
    expect(screen.getByText('admin@schoolsystem.com')).toBeInTheDocument()
    expect(screen.getByText('admin')).toBeInTheDocument()
  })

  it('renders children via Outlet', () => {
    mocks.authValue = { user: adminUser, logout: mocks.logout }
    render(
      <MemoryRouter initialEntries={['/']}>
        <Layout />
      </MemoryRouter>
    )
    expect(screen.getByText('admin@schoolsystem.com')).toBeInTheDocument()
  })
})