import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import Login from '../pages/Login.jsx'
import { getCachedBrand } from '../brand.js'

const mocks = vi.hoisted(() => ({
  login: vi.fn(),
}))

vi.mock('../auth.jsx', () => ({
  useAuth: () => ({
    login: mocks.login,
  }),
}))

function LocationDisplay() {
  const location = useLocation()
  return <div data-testid="location">{location.pathname}</div>
}

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <Login />
      <LocationDisplay />
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('Login page', () => {
  it('renders the branded school name and demo preview', () => {
    const brand = getCachedBrand()
    renderLogin()

    expect(screen.getByText(brand.name)).toBeInTheDocument()
    expect(screen.getByText('Demo preview')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Welcome back' })).toBeInTheDocument()
  })

  it('submits credentials and navigates by role', async () => {
    const user1 = userEvent.setup()
    mocks.login.mockResolvedValue('admin')

    renderLogin()
    await user1.type(screen.getByLabelText('Email'), 'admin@schoolsystem.com')
    await user1.type(screen.getByLabelText('Password'), 'demo-admin-password')
    await user1.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(mocks.login).toHaveBeenCalledWith('admin@schoolsystem.com', 'demo-admin-password'))
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/students'))
  })

  it('shows backend errors without navigating', async () => {
    const user1 = userEvent.setup()
    mocks.login.mockRejectedValue(new TypeError('bad credentials'))

    renderLogin()
    await user1.type(screen.getByLabelText('Email'), 'nope@x.com')
    await user1.type(screen.getByLabelText('Password'), 'wrong')
    await user1.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('bad credentials')).toBeInTheDocument()
    expect(screen.getByTestId('location')).toHaveTextContent('/login')
  })

  it('sends parents to the portal dashboard', async () => {
    const user1 = userEvent.setup()
    mocks.login.mockResolvedValue('parent')

    renderLogin()
    await user1.type(screen.getByLabelText('Email'), 'p@family.net')
    await user1.type(screen.getByLabelText('Password'), 'parent123')
    await user1.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/'))
  })
})