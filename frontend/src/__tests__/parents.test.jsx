import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Parents from '../pages/Parents.jsx'

const mocks = vi.hoisted(() => ({
  api: vi.fn(),
}))

vi.mock('../api.js', () => mocks)

const PARENT = { parent_id: 'P1', name: 'Maria Khan', email: 'maria@family.net', phone: '03001234567', status: true }
const STUDENT = { student_id: 's1', first_name: 'Ali', last_name: 'Khan', grade_level: '9', active: true }

function routeFor(path, init) {
  if (path === '/api/v1/parents' && !init) return { data: [PARENT] }
  if (path === '/api/v1/students?pageSize=15&active=true') return { data: [STUDENT] }
  if (path === '/api/v1/students?search=Ali&pageSize=15&active=true') return { data: [STUDENT] }
  if (path === '/api/v1/parents/P1/students' && !init) return { data: [STUDENT] }
  if (path === '/api/v1/parents/P1/students' && init?.method === 'PUT') return { data: [STUDENT] }
  if (path === '/api/v1/parents/P1' && init?.method === 'PUT') return { parent: PARENT }
  if (path === '/api/v1/parents' && init?.method === 'POST') return { parent: PARENT }
  return { data: [] }
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.api.mockImplementation(async (path, init) => routeFor(path, init))
})

describe('Parents page', () => {
  it('lists parents with their linked children', async () => {
    render(<Parents />)

    expect(await screen.findByText('Maria Khan')).toBeInTheDocument()
    expect(await screen.findByText('Ali Khan')).toBeInTheDocument()
    expect(screen.getByText('maria@family.net')).toBeInTheDocument()
    expect(screen.getByText('03001234567')).toBeInTheDocument()
  })

  it('shows None for a parent without children', async () => {
    mocks.api.mockImplementation(async (path, init) => {
      if (path === '/api/v1/parents' && !init) return { data: [{ ...PARENT, parent_id: 'P2', name: 'Sam Ali' }] }
      if (path === '/api/v1/parents/P2/students') return { data: [] }
      return { data: [] }
    })

    render(<Parents />)

    expect(await screen.findByText('Sam Ali')).toBeInTheDocument()
    expect(screen.getByText('None')).toBeInTheDocument()
  })

  it('adds a parent via POST without a password', async () => {
    const user1 = userEvent.setup()

    render(<Parents />)
    await user1.type(screen.getByLabelText('Full name'), 'Nadia Ali')
    await user1.type(screen.getByLabelText('Email'), 'nadia@family.net')
    await user1.type(screen.getByLabelText('Phone'), '01000000000')
    await user1.click(screen.getByRole('button', { name: 'Add parent' }))

    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith(
        '/api/v1/parents',
        expect.objectContaining({
          method: 'POST',
          body: expect.objectContaining({ name: 'Nadia Ali', email: 'nadia@family.net', phone: '01000000000' }),
        })
      )
    )
    expect(await screen.findByText('Added parent Maria Khan')).toBeInTheDocument()
  })

  it('edits a parent and saves profile plus linked children', async () => {
    const user1 = userEvent.setup()

    render(<Parents />)
    await screen.findByText('Maria Khan')
    await user1.click(screen.getByRole('button', { name: /edit/i }))

    expect(screen.getByRole('heading', { name: 'Edit parent' })).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Save changes' })).toBeEnabled())

    await user1.click(screen.getByRole('button', { name: 'Save changes' }))

    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith('/api/v1/parents/P1', expect.objectContaining({ method: 'PUT' }))
    )
    await waitFor(() =>
      expect(mocks.api).toHaveBeenCalledWith('/api/v1/parents/P1/students', expect.objectContaining({ method: 'PUT', body: { student_ids: ['s1'] } }))
    )
    expect(await screen.findByText('Parent updated')).toBeInTheDocument()
  })

  it('cancels an edit and restores the add form', async () => {
    const user1 = userEvent.setup()

    render(<Parents />)
    await screen.findByText('Maria Khan')
    await user1.click(screen.getByRole('button', { name: /edit/i }))
    expect(screen.getByRole('heading', { name: 'Edit parent' })).toBeInTheDocument()

    await user1.click(screen.getByRole('button', { name: 'Cancel edit' }))
    expect(screen.getByRole('heading', { name: 'Add a parent' })).toBeInTheDocument()
  })

  it('surfaces a load error', async () => {
    mocks.api.mockRejectedValueOnce(new TypeError('no backend'))

    render(<Parents />)

    expect(await screen.findByText('no backend')).toBeInTheDocument()
  })
})