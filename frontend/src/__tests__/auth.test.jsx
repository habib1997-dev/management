import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from '../auth.jsx'

const mocks = vi.hoisted(() => ({
  api: vi.fn(),
  clearAuth: vi.fn(),
  getStoredUser: vi.fn(() => null),
  getToken: vi.fn(() => null),
  saveAuth: vi.fn(),
}))

vi.mock('../api.js', () => mocks)

import { api, saveAuth, clearAuth, getStoredUser, getToken } from '../api.js'

function Probe() {
  const { user, token, isAuthenticated, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="user">{user ? user.email : 'none'}</span>
      <span data-testid="token">{token || 'none'}</span>
      <span data-testid="authed">{isAuthenticated ? 'yes' : 'no'}</span>
      <button
        onClick={() => {
          login('a@x.com', 'pw').catch(() => {})
        }}
      >
        login
      </button>
      <button onClick={logout}>logout</button>
    </div>
  )
}

function renderProbe() {
  return render(
    <AuthProvider>
      <Probe />
    </AuthProvider>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.getStoredUser.mockReturnValue(null)
  mocks.getToken.mockReturnValue(null)
})

describe('AuthProvider', () => {
  it('starts logged out with no stored session', () => {
    renderProbe()
    expect(screen.getByTestId('user')).toHaveTextContent('none')
    expect(screen.getByTestId('token')).toHaveTextContent('none')
    expect(screen.getByTestId('authed')).toHaveTextContent('no')
  })

  it('hydrates from a stored session', async () => {
    mocks.getStoredUser.mockReturnValue({ role: 'admin', user_id: 'u1', email: 'a@x.com' })
    mocks.getToken.mockReturnValue('tok')

    renderProbe()
    await waitFor(() => expect(screen.getByTestId('authed')).toHaveTextContent('yes'))
    expect(screen.getByTestId('user')).toHaveTextContent('a@x.com')
  })

  it('login stores auth and flips state', async () => {
    const user1 = userEvent.setup()
    mocks.api.mockResolvedValue({
      access_token: 'tok1',
      role: 'teacher',
      user_id: 'u2',
      email: 't@x.com',
      teacher_id: 'T7',
    })

    renderProbe()
    await user1.click(screen.getByText('login'))

    await waitFor(() => expect(screen.getByTestId('authed')).toHaveTextContent('yes'))
    expect(saveAuth).toHaveBeenCalledWith(expect.objectContaining({ access_token: 'tok1', role: 'teacher' }))
    expect(screen.getByTestId('user')).toHaveTextContent('t@x.com')
    expect(screen.getByTestId('token')).toHaveTextContent('tok1')
    expect(mocks.api).toHaveBeenCalledWith('/api/v1/auth/login', { method: 'POST', body: { email: 'a@x.com', password: 'pw' } })
  })

  it('login rejects with the backend error', async () => {
    const user1 = userEvent.setup()
    mocks.api.mockRejectedValue(new TypeError('bad credentials'))

    renderProbe()
    await user1.click(screen.getByText('login'))

    await waitFor(() => expect(mocks.api).toHaveBeenCalled())
    expect(screen.getByTestId('authed')).toHaveTextContent('no')
  })

  it('logout clears auth state', async () => {
    const user1 = userEvent.setup()
    mocks.getStoredUser.mockReturnValue({ role: 'admin', user_id: 'u1', email: 'a@x.com' })
    mocks.getToken.mockReturnValue('tok')

    renderProbe()
    await waitFor(() => expect(screen.getByTestId('authed')).toHaveTextContent('yes'))

    await user1.click(screen.getByText('logout'))

    expect(clearAuth).toHaveBeenCalled()
    await waitFor(() => expect(screen.getByTestId('authed')).toHaveTextContent('no'))
  })

  it('useAuth throws outside the provider', () => {
    expect(() => render(<Probe />)).toThrow('useAuth must be used inside AuthProvider')
  })

  it('makes getStoredUser/getToken available to callers', () => {
    renderProbe()
    expect(getStoredUser).toBeTypeOf('function')
    expect(getToken).toBeTypeOf('function')
  })
})