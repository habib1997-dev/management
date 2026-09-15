import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Teachers from '../pages/Teachers.jsx'

const mocks = vi.hoisted(() => ({
  api: vi.fn(),
}))

vi.mock('../api.js', () => mocks)

const TEACHER = {
  teacher_id: 't1',
  name: 'Ms Ayesha',
  email: 'ayesha@school.com',
  subjects_taught: 'Math',
  status: true,
}

function routeFor(path) {
  if (path === '/api/v1/teachers') return { data: [TEACHER] }
  return { data: [] }
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.api.mockImplementation(async (path) => routeFor(path))
})

describe('Teachers page', () => {
  it('lists teachers with their subjects and status', async () => {
    render(<Teachers />)

    expect(await screen.findByText('Ms Ayesha')).toBeInTheDocument()
    expect(screen.getByText('Math')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Teachers' })).toBeInTheDocument()
  })

  it('shows an empty state', async () => {
    mocks.api.mockResolvedValue({ data: [] })

    render(<Teachers />)

    expect(await screen.findByText('No teachers found.')).toBeInTheDocument()
  })

  it('adds a teacher via POST and drops empty optional fields', async () => {
    const user1 = userEvent.setup()
    mocks.api.mockImplementation(async (path, init) => {
      if (path === '/api/v1/teachers' && init?.method === 'POST') return { teacher: { name: 'Mr Bilal' } }
      return routeFor(path)
    })

    render(<Teachers />)
    await user1.type(screen.getByLabelText('Full name'), 'Mr Bilal')
    await user1.type(screen.getByLabelText('Email'), 'bilal@school.com')
    await user1.click(screen.getByRole('button', { name: 'Add teacher' }))

    await waitFor(() => expect(mocks.api).toHaveBeenCalledWith('/api/v1/teachers', expect.objectContaining({ method: 'POST' })))
    const postCall = mocks.api.mock.calls.find(([path, init]) => path === '/api/v1/teachers' && init?.method === 'POST')
    expect(postCall[1].body).toEqual({ name: 'Mr Bilal', email: 'bilal@school.com' })
    expect(await screen.findByText('Added teacher Mr Bilal')).toBeInTheDocument()
  })

  it('edits a teacher and deactivates them via PUT', async () => {
    const user1 = userEvent.setup()

    render(<Teachers />)
    await screen.findByText('Ms Ayesha')
    await user1.click(screen.getByRole('button', { name: /edit/i }))

    expect(screen.getByRole('heading', { name: 'Edit teacher' })).toBeInTheDocument()
    expect(screen.getByDisplayValue('Ms Ayesha')).toBeInTheDocument()

    await user1.click(screen.getByRole('checkbox'))
    await user1.click(screen.getByRole('button', { name: 'Save changes' }))

    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith(
        '/api/v1/teachers/t1',
        expect.objectContaining({
          method: 'PUT',
          body: expect.objectContaining({ name: 'Ms Ayesha', status: false, email: 'ayesha@school.com' }),
        })
      )
    )
    expect(await screen.findByText('Teacher updated')).toBeInTheDocument()
  })

  it('cancels an edit and restores the add form', async () => {
    const user1 = userEvent.setup()

    render(<Teachers />)
    await screen.findByText('Ms Ayesha')
    await user1.click(screen.getByRole('button', { name: /edit/i }))
    expect(screen.getByRole('heading', { name: 'Edit teacher' })).toBeInTheDocument()

    await user1.click(screen.getByRole('button', { name: 'Cancel edit' }))
    expect(screen.getByRole('heading', { name: 'Add a teacher' })).toBeInTheDocument()
  })

  it('surfaces load errors', async () => {
    mocks.api.mockRejectedValueOnce(new TypeError('no backend'))

    render(<Teachers />)

    expect(await screen.findByText('no backend')).toBeInTheDocument()
  })
})