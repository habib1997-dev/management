import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Attendance from '../pages/Attendance.jsx'

const mocks = vi.hoisted(() => ({
  api: vi.fn(),
}))

vi.mock('../api.js', () => mocks)

const COURSE = { course_id: 'c1', name: 'Algebra', teacher_id: 't1', status: 'active' }
const ALI = { student_id: 's1', first_name: 'Ali', last_name: 'Khan', grade_level: '9', active: true }
const SARA = { student_id: 's2', first_name: 'Sara', last_name: 'Khan', grade_level: '9', active: true }

function routeFor(path) {
  if (path === '/api/v1/courses') return { data: [COURSE] }
  if (path === '/api/v1/courses/c1') return { course_id: 'c1', name: 'Algebra', students: [ALI, SARA] }
  if (path.startsWith('/api/v1/attendance/c1?')) return { data: [{ student_id: 's1', status: 'late' }] }
  if (path === '/api/v1/courses/c1/parents') return { data: [{ student_id: 's1', parents: [{ parent_id: 'p1', name: 'Maria Khan', phone: '0300', email: 'm@x.com' }] }] }
  if (path === '/api/v1/attendance') return { success: true }
  return { data: [] }
}

async function waitForRoster() {
  await screen.findByText('Ali Khan')
  return screen.getAllByRole('combobox')
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.api.mockImplementation(async (path) => routeFor(path))
})

describe('Attendance page', () => {
  it('loads the course roster and parent contacts', async () => {
    render(<Attendance />)

    expect(await screen.findByText('Ali Khan')).toBeInTheDocument()
    expect(screen.getByText('Sara Khan')).toBeInTheDocument()
    expect(await screen.findByText('Maria Khan')).toBeInTheDocument()
    expect(screen.getByText('0300 · m@x.com')).toBeInTheDocument()
  })

  it('pre-fills existing statuses and lets you change them', async () => {
    const user1 = userEvent.setup()

    render(<Attendance />)
    const selects = await waitForRoster()
    const statusSelect = selects[1]
    expect(statusSelect).toHaveValue('late')

    await user1.selectOptions(statusSelect, 'present')
    expect(statusSelect).toHaveValue('present')
  })

  it('marks all students present', async () => {
    const user1 = userEvent.setup()

    render(<Attendance />)
    const selects = await waitForRoster()

    await user1.click(screen.getByRole('button', { name: 'Mark all present' }))

    // Ali already had 'late' from existing records (kept), Sara gets present.
    expect(selects[1]).toHaveValue('late')
    expect(selects[2]).toHaveValue('present')
  })

  it('saves attendance for marked students via POST', async () => {
    const user1 = userEvent.setup()

    render(<Attendance />)
    await waitForRoster()
    await user1.click(screen.getByRole('button', { name: 'Mark all present' }))

    await user1.click(screen.getByRole('button', { name: 'Save attendance' }))

    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith(
        '/api/v1/attendance',
        expect.objectContaining({
          method: 'POST',
          body: expect.objectContaining({
            course_id: 'c1',
            records: expect.arrayContaining([
              { student_id: 's1', status: 'late' },
              { student_id: 's2', status: 'present' },
            ]),
          }),
        })
      )
    )
    expect(await screen.findByText(/Attendance recorded for/)).toBeInTheDocument()
  })

  it('flattens to only marked records', async () => {
    const user1 = userEvent.setup()

    render(<Attendance />)
    await screen.findByText('Ali Khan')
    const selects = screen.getAllByRole('combobox')
    await user1.selectOptions(selects[1], 'absent')

    await user1.click(screen.getByRole('button', { name: 'Save attendance' }))

    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith(
        '/api/v1/attendance',
        expect.objectContaining({ body: expect.objectContaining({ records: [{ student_id: 's1', status: 'absent' }] }) })
      )
    )
  })

  it('shows a hint when nothing is marked', async () => {
    const user1 = userEvent.setup()
    const noExisting = vi.fn(async (path) => {
      if (path === '/api/v1/courses') return { data: [COURSE] }
      if (path === '/api/v1/courses/c1') return { course_id: 'c1', name: 'Algebra', students: [ALI, SARA] }
      if (path.startsWith('/api/v1/attendance/c1?')) return { data: [] }
      if (path === '/api/v1/courses/c1/parents') return { data: [] }
      return { data: [] }
    })
    mocks.api.mockImplementation(noExisting)

    render(<Attendance />)
    await screen.findByText('Ali Khan')

    await user1.click(screen.getByRole('button', { name: 'Save attendance' }))

    expect(await screen.findByText(/Nothing to save yet/)).toBeInTheDocument()
  })

  it('shows an empty course message', async () => {
    mocks.api.mockImplementation(async (path) => {
      if (path === '/api/v1/courses') return { data: [COURSE] }
      if (path === '/api/v1/courses/c1') return { course_id: 'c1', name: 'Algebra', students: [] }
      return { data: [] }
    })

    render(<Attendance />)

    expect(await screen.findByText('No students in this course.')).toBeInTheDocument()
  })

  it('surfaces a load error', async () => {
    mocks.api.mockRejectedValueOnce(new TypeError('no backend'))

    render(<Attendance />)

    expect(await screen.findByText('no backend')).toBeInTheDocument()
  })
})