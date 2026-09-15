import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Portal from '../pages/Portal.jsx'

const mocks = vi.hoisted(() => ({
  api: vi.fn(),
  downloadFile: vi.fn(),
}))

vi.mock('../auth.jsx', () => ({
  useAuth: () => ({ user: mocks.user }),
}))

vi.mock('../api.js', () => mocks)

const CHILD = {
  student_id: 's1',
  first_name: 'Ali',
  last_name: 'Khan',
  grade_level: '9',
  attendance: [{ attendance_id: 'a1', date: '2026-09-01', course_name: 'Algebra', status: 'late' }],
  grades: [{ grade_id: 'g1', course_name: 'Algebra', assignment_type: 'quiz', grade_value: 88, date_due: '2026-09-10' }],
}

const PORTAL_PARENT = { parent_id: 'P1', name: 'Maria Khan', email: 'maria@family.net', children: [CHILD] }

beforeEach(() => {
  vi.clearAllMocks()
  mocks.user = { role: 'parent', user_id: 'u1', email: 'maria@family.net', parent_id: 'P1' }
  mocks.api.mockResolvedValue({ parents: [PORTAL_PARENT] })
  mocks.downloadFile.mockResolvedValue(undefined)
})

describe('Parent Portal page', () => {
  it('renders the parent header and child attendance + grades', async () => {
    render(<Portal />)

    expect(await screen.findByText('Maria Khan')).toBeInTheDocument()
    expect(screen.getByText('maria@family.net')).toBeInTheDocument()
    expect(await screen.findByText(/Ali Khan/)).toBeInTheDocument()
    expect(screen.getAllByText('Algebra').length).toBeGreaterThan(0)
    expect(screen.getByText('Late')).toBeInTheDocument()
    expect(screen.getByText('88')).toBeInTheDocument()
    expect(mocks.api).toHaveBeenCalledWith('/api/v1/parents/P1/portal')
  })

  it('shows a message when no children are linked', async () => {
    mocks.api.mockResolvedValue({ parents: [] })

    render(<Portal />)

    expect(await screen.findByText(/No children are linked to your account yet/)).toBeInTheDocument()
  })

  it('shows empty attendance and grades placeholders per child', async () => {
    mocks.api.mockResolvedValue({
      parents: [{ ...PORTAL_PARENT, children: [{ ...CHILD, attendance: [], grades: [] }] }],
    })

    render(<Portal />)

    expect(await screen.findByText('No attendance records yet.')).toBeInTheDocument()
    expect(screen.getByText('No grades recorded yet.')).toBeInTheDocument()
  })

  it('downloads a report card PDF', async () => {
    const user1 = userEvent.setup()

    render(<Portal />)
    await screen.findByText(/Ali Khan/)

    await user1.click(screen.getByRole('button', { name: /download report card/i }))

    await waitFor(() =>
      expect(mocks.downloadFile).toHaveBeenCalledWith('/api/v1/reports/portal/s1', 'report_card_Khan_Ali.pdf')
    )
  })

  it('reports download errors', async () => {
    const user1 = userEvent.setup()
    mocks.downloadFile.mockRejectedValueOnce(new TypeError('pdf failed'))

    render(<Portal />)
    await screen.findByText(/Ali Khan/)

    await user1.click(screen.getByRole('button', { name: /download report card/i }))

    expect(await screen.findByText('pdf failed')).toBeInTheDocument()
  })

  it('does nothing without a parent id', async () => {
    mocks.user = { role: 'parent', email: 'x@y.net' }

    render(<Portal />)

    expect(mocks.api).not.toHaveBeenCalled()
  })

  it('surfaces a load error', async () => {
    mocks.api.mockRejectedValueOnce(new TypeError('no backend'))

    render(<Portal />)

    expect(await screen.findByText('no backend')).toBeInTheDocument()
  })
})