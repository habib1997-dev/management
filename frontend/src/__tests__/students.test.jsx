import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Students from '../pages/Students.jsx'

const mocks = vi.hoisted(() => ({
  api: vi.fn(),
  downloadFile: vi.fn(),
}))

vi.mock('../api.js', () => mocks)

const ALI = {
  student_id: 's1',
  first_name: 'Ali',
  last_name: 'Khan',
  grade_level: '9',
  date_of_birth: '2010-04-02',
  email: 'ali@x.com',
  phone: '03001234567',
  active: true,
  enrollment_date: '2026-01-05',
}

function listResponse(rows, total) {
  return { data: rows, meta: { total } }
}

function renderStudents() {
  return render(<Students />)
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.api.mockResolvedValue(listResponse([], 0))
  mocks.downloadFile.mockResolvedValue(undefined)
})

describe('Students page', () => {
  it('shows an empty state when there are no students', async () => {
    renderStudents()
    expect(screen.getByRole('heading', { name: 'Students' })).toBeInTheDocument()
    expect(await screen.findByText('No students found.')).toBeInTheDocument()
    expect(screen.getByText('0 student(s)')).toBeInTheDocument()
  })

  it('renders the student list and totals', async () => {
    mocks.api.mockResolvedValue(listResponse([ALI], 1))

    renderStudents()

    expect(await screen.findByText('Ali Khan')).toBeInTheDocument()
    expect(screen.getByText('9')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByText('ali@x.com')).toBeInTheDocument()
    expect(screen.getByText('03001234567')).toBeInTheDocument()
    expect(screen.getByText('1 student(s)')).toBeInTheDocument()
  })

  it('refetches with the search term after typing', async () => {
    const user1 = userEvent.setup()
    mocks.api.mockResolvedValue(listResponse([ALI], 1))

    renderStudents()
    await screen.findByText('Ali Khan')

    await user1.type(screen.getByPlaceholderText('Search by name / grade…'), 'Ali')

    await waitFor(() => expect(mocks.api).toHaveBeenCalledWith(expect.stringContaining('search=Ali')))
  })

  it('enrolls a student via POST and clears the form', async () => {
    const user1 = userEvent.setup()
    mocks.api.mockResolvedValue({ student: { first_name: 'Sara', last_name: 'Khan' } })

    renderStudents()

    await user1.type(screen.getByLabelText('First name'), 'Sara')
    await user1.type(screen.getByLabelText('Last name'), 'Khan')
    await user1.type(screen.getByLabelText('Date of birth'), '2011-06-01')
    await user1.type(screen.getByLabelText('Grade level'), '10')
    await user1.click(screen.getByRole('button', { name: 'Enroll student' }))

    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith(
        '/api/v1/students',
        expect.objectContaining({
          method: 'POST',
          body: expect.objectContaining({ first_name: 'Sara', last_name: 'Khan', grade_level: '10' }),
        })
      )
    )
    expect(await screen.findByText('Enrolled Sara Khan')).toBeInTheDocument()
  })

  it('drops empty email/phone from the enroll body', async () => {
    const user1 = userEvent.setup()
    mocks.api.mockResolvedValue({ student: { first_name: 'Sara', last_name: 'Khan' } })

    renderStudents()
    await user1.type(screen.getByLabelText('First name'), 'Sara')
    await user1.type(screen.getByLabelText('Last name'), 'Khan')
    await user1.type(screen.getByLabelText('Date of birth'), '2011-06-01')
    await user1.type(screen.getByLabelText('Grade level'), '10')
    await user1.click(screen.getByRole('button', { name: 'Enroll student' }))

    const postCall = await waitFor(() => {
      const call = mocks.api.mock.calls.find(([path, init]) => path === '/api/v1/students' && init?.method === 'POST')
      expect(call).toBeTruthy()
      return call
    })
    expect(postCall[1].body).not.toContain('email')
    expect(postCall[1].body).not.toContain('phone')
  })

  it('opens the edit panel and saves changes via PUT', async () => {
    const user1 = userEvent.setup()
    mocks.api
      .mockResolvedValueOnce(listResponse([ALI], 1))
      .mockResolvedValueOnce(ALI)
      .mockResolvedValueOnce({ student: ALI })

    renderStudents()

    await screen.findByText('Ali Khan')
    await user1.click(screen.getByRole('button', { name: /edit/i }))

    expect(await screen.findByRole('heading', { name: 'Edit student' })).toBeInTheDocument()
    expect(screen.getByDisplayValue('Ali')).toBeInTheDocument()
    expect(screen.getByDisplayValue('9')).toBeInTheDocument()

    await user1.click(screen.getByRole('button', { name: 'Save changes' }))

    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith(
        '/api/v1/students/s1',
        expect.objectContaining({ method: 'PUT', body: expect.objectContaining({ first_name: 'Ali' }) })
      )
    )
    expect(await screen.findByText('Student updated')).toBeInTheDocument()
  })

  it('cancels an edit and restores the enroll form', async () => {
    const user1 = userEvent.setup()
    mocks.api.mockResolvedValueOnce(listResponse([ALI], 1)).mockResolvedValueOnce(ALI)

    renderStudents()
    await screen.findByText('Ali Khan')
    await user1.click(screen.getByRole('button', { name: /edit/i }))
    expect(await screen.findByRole('heading', { name: 'Edit student' })).toBeInTheDocument()

    await user1.click(screen.getByRole('button', { name: 'Cancel edit' }))
    expect(screen.getByRole('heading', { name: 'Enroll a new student' })).toBeInTheDocument()
  })

  it('downloads CSV exports', async () => {
    const user1 = userEvent.setup()
    renderStudents()

    await user1.click(screen.getByRole('button', { name: /download students csv/i }))
    await user1.click(screen.getByRole('button', { name: /download grades csv/i }))

    expect(mocks.downloadFile).toHaveBeenCalledWith('/api/v1/export/students.csv', 'students.csv')
    expect(mocks.downloadFile).toHaveBeenCalledWith('/api/v1/export/grades.csv', 'grades.csv')
  })

  it('shows pagination only when the list exceeds the page size', async () => {
    const many = Array.from({ length: 60 }, (_, i) => ({
      ...ALI,
      student_id: `s${i}`,
      first_name: `Student`,
    }))
    mocks.api.mockResolvedValue(listResponse(many, 60))

    renderStudents()

    expect(await screen.findByText('Page 1 of 2')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /prev/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /next/i })).toBeEnabled()
  })

  it('surfaces fetch errors in the alerts', async () => {
    mocks.api.mockRejectedValueOnce(new TypeError('no backend'))

    renderStudents()

    expect(await screen.findByText('no backend')).toBeInTheDocument()
  })
})