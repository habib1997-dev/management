import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../auth.jsx'
import App from '../App.jsx'

const mocks = vi.hoisted(() => ({
  api: vi.fn(),
  clearAuth: vi.fn(),
  downloadFile: vi.fn(),
  getStoredUser: vi.fn(() => null),
  getToken: vi.fn(() => null),
  saveAuth: vi.fn(),
}))

vi.mock('../api.js', () => mocks)

import { getStoredUser, getToken } from '../api.js'

function renderAt(path) {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </AuthProvider>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.api.mockResolvedValue({ data: [], meta: { total: 0 } })
  mocks.getStoredUser.mockReturnValue(null)
  mocks.getToken.mockReturnValue(null)
})

describe('App route guards', () => {
  it('redirects unauthenticated users to the login page', async () => {
    renderAt('/')
    expect(await screen.findByRole('heading', { name: 'Welcome back' })).toBeInTheDocument()
  })

  it('logs an admin into the dashboard', async () => {
    mocks.getStoredUser.mockReturnValue({ role: 'admin', user_id: 'u1', email: 'admin@schoolsystem.com' })
    mocks.getToken.mockReturnValue('tok')

    renderAt('/')
    expect(await screen.findByText('Welcome, admin@schoolsystem.com')).toBeInTheDocument()
  })

  it('keeps a non-admin off the admin-only students page', async () => {
    mocks.getStoredUser.mockReturnValue({ role: 'parent', user_id: 'u2', email: 'parent@family.net', parent_id: 'P1' })
    mocks.getToken.mockReturnValue('tok')
    mocks.api.mockResolvedValue({ parents: [{ children: [{ student_id: 's1' }] }] })

    renderAt('/students')
    expect(await screen.findByText('Welcome, parent@family.net')).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Students' })).not.toBeInTheDocument()
  })

  it('sends teachers to a working dashboard', async () => {
    mocks.getStoredUser.mockReturnValue({ role: 'teacher', user_id: 'u3', email: 't@school.com', teacher_id: 'T1' })
    mocks.getToken.mockReturnValue('tok')

    renderAt('/')
    expect(await screen.findByText('Welcome, t@school.com')).toBeInTheDocument()
  })

  it('falls back to login for unknown routes when logged out', async () => {
    renderAt('/nowhere')
    expect(await screen.findByRole('heading', { name: 'Welcome back' })).toBeInTheDocument()
  })

  it('hydrates auth state from stored credentials synchronously', async () => {
    mocks.getStoredUser.mockReturnValue({ role: 'admin', user_id: 'u1', email: 'admin@schoolsystem.com' })
    mocks.getToken.mockReturnValue('tok')

    renderAt('/')
    await waitFor(() => expect(getStoredUser).toHaveBeenCalled())
    expect(getToken).toHaveBeenCalled()
  })
})