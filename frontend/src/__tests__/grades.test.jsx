import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Grades from '../pages/Grades.jsx'

const mocks = vi.hoisted(() => ({
  api: vi.fn(),
}))

vi.mock('../api.js', () => mocks)

const ALI = { student_id: 's1', first_name: 'Ali', last_name: 'Khan', grade_level: '9', active: true }
const GRADE = {
  grade_id: 'g1',
  student_id: 's1',
  grade_value: 75,
  assignment_type: 'quiz',
  date_assigned: '2026-09-01',
  date_due: '2026-09-10',
  date_graded: '2026-09-11',
}

function routeFor(path, init) {
  if (path === '/api/v1/courses' && !init) return { data: [{ course_id: 'c1', name: 'Algebra' }] }
  if (path === '/api/v1/courses/c1/grades') return { data: [GRADE] }
  if (path === '/api/v1/courses/c1') return { course_id: 'c1', name: 'Algebra', students: [ALI] }
  if (path === '/api/v1/courses/c1/parents') return { data: [] }
  if (path === '/api/v1/grades' && init?.method === 'POST') return { grade: { grade_value: 88 } }
  if (path === '/api/v1/grades/g1' && init?.method === 'PUT') return { grade: { grade_value: 90 } }
  return { data: [] }
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.api.mockImplementation(async (path, init) => routeFor(path, init))
})

describe('Grades page', () => {
  it('shows the roster entry form and recorded grades', async () => {
    render(<Grades />)

    expect((await screen.findAllByText('Ali Khan')).length).toBeGreaterThan(0)
    expect(await screen.findByText('75')).toBeInTheDocument()
    expect(screen.getAllByText('quiz').length).toBeGreaterThan(0)
    expect(screen.getByText('2026-09-10')).toBeInTheDocument()
  })

  it('records a new grade via POST', async () => {
    const user1 = userEvent.setup()

    render(<Grades />)
    const gradeInput = (await screen.findAllByPlaceholderText('0–100'))[0]
    await user1.type(gradeInput, '88')
    await user1.click(screen.getByRole('button', { name: 'Record' }))

    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith(
        '/api/v1/grades',
        expect.objectContaining({
          method: 'POST',
          body: expect.objectContaining({
            student_id: 's1',
            course_id: 'c1',
            grade_value: 88,
            assignment_type: 'homework',
          }),
        })
      )
    )
    expect(await screen.findByText(/Grade 88 recorded for Ali Khan/)).toBeInTheDocument()
  })

  it('rejects a due date before the assigned date', async () => {
    const user1 = userEvent.setup()

    const view = render(<Grades />)
    const inputs = await screen.findAllByPlaceholderText('0–100')
    await user1.type(inputs[0], '50')

    const dates = view.container.querySelectorAll('input[type="date"]')
    fireEvent.change(dates[1], { target: { value: '2020-01-01' } })

    await user1.click(screen.getByRole('button', { name: 'Record' }))

    expect(await screen.findByText('Due date cannot be before the assigned date.')).toBeInTheDocument()
    expect(mocks.api).not.toHaveBeenCalledWith('/api/v1/grades', expect.anything())
  })

  it('edits an existing grade via PUT', async () => {
    const user1 = userEvent.setup()

    render(<Grades />)
    await screen.findByText('75')
    await user1.click(screen.getByRole('button', { name: /edit/i }))

    const editInputs = screen.getAllByPlaceholderText('0–100')
    const editGradeInput = editInputs[editInputs.length - 1]
    await user1.clear(editGradeInput)
    await user1.type(editGradeInput, '90')
    await user1.click(screen.getByRole('button', { name: /save/i }))

    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith(
        '/api/v1/grades/g1',
        expect.objectContaining({
          method: 'PUT',
          body: expect.objectContaining({ grade_value: 90, assignment_type: 'quiz' }),
        })
      )
    )
    expect(await screen.findByText(/Grade 90 saved for Ali Khan/)).toBeInTheDocument()
  })

  it('cancels an edit and restores the read-only row', async () => {
    const user1 = userEvent.setup()

    render(<Grades />)
    await screen.findByText('75')
    await user1.click(screen.getByRole('button', { name: /edit/i }))
    await user1.click(screen.getByRole('button', { name: /cancel/i }))

    expect(screen.queryByRole('button', { name: /save/i })).toBeNull()
    expect(screen.getAllByPlaceholderText('0–100')).toHaveLength(1)
  })

  it('shows an empty grades message', async () => {
    mocks.api.mockImplementation(async (path, init) => {
      if (path === '/api/v1/courses' && !init) return { data: [{ course_id: 'c1', name: 'Algebra' }] }
      if (path === '/api/v1/courses/c1/grades') return { data: [] }
      if (path === '/api/v1/courses/c1') return { course_id: 'c1', name: 'Algebra', students: [ALI] }
      return { data: [] }
    })

    render(<Grades />)

    expect(await screen.findByText('No grades recorded yet.')).toBeInTheDocument()
  })

  it('surfaces a load error', async () => {
    mocks.api.mockRejectedValueOnce(new TypeError('no backend'))

    render(<Grades />)

    expect(await screen.findByText('no backend')).toBeInTheDocument()
  })
})