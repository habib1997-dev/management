import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from '../pages/Dashboard.jsx'

const mocks = vi.hoisted(() => ({
  api: vi.fn(),
  downloadFile: vi.fn(),
}))

vi.mock('../api.js', () => mocks)

vi.mock('../auth.jsx', () => ({
  useAuth: () => mocks.authValue,
}))

function renderDashboard() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Dashboard />
    </MemoryRouter>
  )
}

const adminUser = { role: 'admin', user_id: 'u1', email: 'admin@schoolsystem.com' }

beforeEach(() => {
  vi.clearAllMocks()
  mocks.api.mockResolvedValue({ data: [], meta: { total: 0 } })
  mocks.downloadFile.mockResolvedValue(undefined)
  mocks.authValue = { user: adminUser }
})

describe('Dashboard', () => {
  it('greets an admin and renders stats from the API', async () => {
    mocks.api
      .mockResolvedValueOnce({ data: [{ id: 1 }], meta: { total: 42 } })
      .mockResolvedValueOnce({ data: [], meta: { total: 5 } })
      .mockResolvedValueOnce({ data: [], meta: { total: 8 } })
      .mockResolvedValueOnce({ data: [], meta: { total: 3 } })

    renderDashboard()

    expect(screen.getByText('Welcome, admin@schoolsystem.com')).toBeInTheDocument()
    expect(await screen.findByText('42')).toBeInTheDocument()
    expect(screen.getAllByText('Students').length).toBeGreaterThan(0)
    expect(screen.getByText('Manage students')).toBeInTheDocument()
    expect(mocks.api).toHaveBeenCalledTimes(4)
  })

  it('shows teacher quick links', () => {
    mocks.authValue = { user: { role: 'teacher', user_id: 'u2', email: 't@school.com' } }

    renderDashboard()

    expect(screen.getByText('Welcome, t@school.com')).toBeInTheDocument()
    expect(screen.getByText('Open attendance')).toBeInTheDocument()
    expect(screen.getByText('Open grades')).toBeInTheDocument()
  })

  it('surfaces API errors in an alert', async () => {
    mocks.api.mockRejectedValueOnce(new TypeError('boom'))

    renderDashboard()

    expect(await screen.findByText('boom')).toBeInTheDocument()
  })

  it('shows a parent child count from the portal', async () => {
    mocks.authValue = { user: { role: 'parent', user_id: 'u3', email: 'p@family.net', parent_id: 'P1' } }
    mocks.api.mockResolvedValue({ parents: [{ children: [{ student_id: 's1' }, { student_id: 's2' }] }] })

    renderDashboard()

    expect(screen.getByText('Welcome, p@family.net')).toBeInTheDocument()
    expect(await screen.findByText('2')).toBeInTheDocument()
    expect(screen.getByText('Open portal')).toBeInTheDocument()
  })

  it('downloads a single-child report card directly', async () => {
    mocks.authValue = { user: { role: 'parent', user_id: 'u3', email: 'p@family.net', parent_id: 'P1' } }
    const user1 = userEvent.setup()

    mocks.api.mockResolvedValue({ parents: [{ children: [{ student_id: 's1', first_name: 'Ali', last_name: 'Khan' }] }] })

    renderDashboard()
    expect(await screen.findByRole('button', { name: /download report card/i })).toBeInTheDocument()

    await user1.click(screen.getByRole('button', { name: /download report card/i }))

    expect(mocks.downloadFile).toHaveBeenCalledWith('/api/v1/reports/portal/s1', 'report_card_Khan_Ali.pdf')
  })

  it('opens a picker for parents with two children', async () => {
    mocks.authValue = { user: { role: 'parent', user_id: 'u3', email: 'p@family.net', parent_id: 'P1' } }
    const user1 = userEvent.setup()

    mocks.api.mockResolvedValue({
      parents: [
        {
          children: [
            { student_id: 's1', first_name: 'Ali', last_name: 'Khan' },
            { student_id: 's2', first_name: 'Sara', last_name: 'Khan' },
          ],
        },
      ],
    })

    renderDashboard()
    const btn = await screen.findByRole('button', { name: /download report card/i })
    await user1.click(btn)

    expect(screen.getByText('Whose report card?')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ali Khan' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sara Khan' })).toBeInTheDocument()
    expect(mocks.downloadFile).not.toHaveBeenCalled()
  })

  it('downloads the chosen child and closes the picker', async () => {
    mocks.authValue = { user: { role: 'parent', user_id: 'u3', email: 'p@family.net', parent_id: 'P1' } }
    const user1 = userEvent.setup()

    mocks.api.mockResolvedValue({
      parents: [
        {
          children: [
            { student_id: 's1', first_name: 'Ali', last_name: 'Khan' },
            { student_id: 's2', first_name: 'Sara', last_name: 'Khan' },
          ],
        },
      ],
    })

    renderDashboard()
    const btn = await screen.findByRole('button', { name: /download report card/i })
    await user1.click(btn)
    await user1.click(screen.getByRole('button', { name: 'Sara Khan' }))

    expect(mocks.downloadFile).toHaveBeenCalledWith('/api/v1/reports/portal/s2', 'report_card_Khan_Sara.pdf')
    await waitFor(() => expect(screen.queryByText('Whose report card?')).not.toBeInTheDocument())
  })
})