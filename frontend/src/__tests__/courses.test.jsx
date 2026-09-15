import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Courses from '../pages/Courses.jsx'

const mocks = vi.hoisted(() => ({
  api: vi.fn(),
}))

vi.mock('../api.js', () => mocks)

const TEACHER = { teacher_id: 't1', name: 'Ms Ayesha', email: 'a@school.com', status: true }
const SECOND_TEACHER = { teacher_id: 't2', name: 'Mr Bilal', email: 'b@school.com', status: true }
const STUDENT = { student_id: 's1', first_name: 'Ali', last_name: 'Khan', grade_level: '9', active: true }
const COURSE = {
  course_id: 'c1',
  name: 'Algebra',
  status: 'active',
  grade_level: '9',
  semester: 'Fall 2026',
  teacher_id: 't1',
  students: [STUDENT],
}

function routeFor(path, init) {
  if (path === '/api/v1/courses' && !init) return { data: [COURSE] }
  if (path === '/api/v1/teachers') return { data: [TEACHER, SECOND_TEACHER] }
  if (path === '/api/v1/courses/c1' && init?.method === 'PUT') return { course: { teacher_id: 't2' } }
  if (path === '/api/v1/courses/c1/students' && init?.method === 'PUT') return { ...COURSE }
  if (path === '/api/v1/courses/c1') return COURSE
  if (path.startsWith('/api/v1/students?')) return { data: [STUDENT] }
  return { data: [] }
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.api.mockImplementation(async (path, init) => routeFor(path, init))
})

describe('Courses page', () => {
  it('lists courses with their teacher and status pill', async () => {
    render(<Courses />)

    expect(await screen.findByText('Algebra')).toBeInTheDocument()
    expect(screen.getAllByText('Ms Ayesha').length).toBeGreaterThan(0)
    expect(screen.getByText('Fall 2026')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('creates a course via POST', async () => {
    const user1 = userEvent.setup()
    mocks.api.mockImplementation(async (path, init) => {
      if (path === '/api/v1/courses' && init?.method === 'POST') return { course: { name: 'Physics' } }
      return routeFor(path, init)
    })

    render(<Courses />)
    await user1.type(screen.getByLabelText('Course name'), 'Physics')
    await user1.selectOptions(screen.getByLabelText('Teacher'), 't2')
    await user1.type(screen.getByLabelText('Grade level'), '10')
    await user1.type(screen.getByLabelText('Semester'), 'Spring 2027')
    await user1.click(screen.getByRole('button', { name: 'Create course' }))

    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith(
        '/api/v1/courses',
        expect.objectContaining({
          method: 'POST',
          body: expect.objectContaining({ name: 'Physics', teacher_id: 't2', grade_level: '10', semester: 'Spring 2027' }),
        })
      )
    )
    expect(await screen.findByText('Created course "Physics"')).toBeInTheDocument()
  })

  it('opens the roster panel and saves the roster', async () => {
    const user1 = userEvent.setup()

    render(<Courses />)
    await screen.findByText('Algebra')
    await user1.click(screen.getByRole('button', { name: /roster/i }))

    await screen.findByText('Enrolled students')
    expect(screen.getByText(/— 1 student/)).toBeInTheDocument()
    const checkbox = await screen.findByRole('checkbox')
    expect(checkbox).toBeChecked()

    await user1.click(screen.getByRole('button', { name: 'Save roster' }))

    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith(
        '/api/v1/courses/c1/students',
        expect.objectContaining({ method: 'PUT', body: { student_ids: ['s1'] } })
      )
    )
    expect(await screen.findByText('Course roster updated')).toBeInTheDocument()
  })

  it('can remove a student from the roster and save', async () => {
    const user1 = userEvent.setup()

    render(<Courses />)
    await screen.findByText('Algebra')
    await user1.click(screen.getByRole('button', { name: /roster/i }))
    const checkbox = await screen.findByRole('checkbox')
    await user1.click(checkbox)
    await waitFor(() => expect(checkbox).not.toBeChecked())

    await user1.click(screen.getByRole('button', { name: 'Save roster' }))
    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith('/api/v1/courses/c1/students', expect.objectContaining({ body: { student_ids: [] } }))
    )
  })

  it('changes the assigned teacher via PUT', async () => {
    const user1 = userEvent.setup()

    render(<Courses />)
    await screen.findByText('Algebra')
    await user1.click(screen.getByRole('button', { name: /roster/i }))
    await screen.findByText('Enrolled students')

    const teacherSelects = screen.getAllByLabelText('Teacher')
    await user1.selectOptions(teacherSelects[1], 't2')
    await user1.click(screen.getByRole('button', { name: 'Change teacher' }))

    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith('/api/v1/courses/c1', expect.objectContaining({ method: 'PUT', body: { teacher_id: 't2' } }))
    )
    expect(await screen.findByText('Course teacher updated')).toBeInTheDocument()
  })

  it('closes the detail panel', async () => {
    const user1 = userEvent.setup()

    render(<Courses />)
    await screen.findByText('Algebra')
    await user1.click(screen.getByRole('button', { name: /roster/i }))
    await screen.findByText('Enrolled students')

    await user1.click(screen.getByRole('button', { name: /close/i }))
    expect(screen.queryByText('Enrolled students')).not.toBeInTheDocument()
  })

  it('surfaces a load error', async () => {
    mocks.api.mockRejectedValueOnce(new TypeError('no backend'))

    render(<Courses />)

    expect(await screen.findByText('no backend')).toBeInTheDocument()
  })
})