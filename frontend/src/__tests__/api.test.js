import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  getToken,
  getStoredUser,
  saveAuth,
  clearAuth,
  api,
  downloadFile,
} from '../api.js'

beforeEach(() => {
  window.localStorage.clear()
  delete window.location.href
})

describe('token + user storage', () => {
  it('round-trips auth through localStorage', () => {
    expect(getToken()).toBeNull()
    expect(getStoredUser()).toBeNull()

    saveAuth({ access_token: 'tok-1', role: 'admin', user_id: 'u1', email: 'a@x.com' })

    expect(getToken()).toBe('tok-1')
    expect(getStoredUser()).toEqual({ role: 'admin', user_id: 'u1', email: 'a@x.com', teacher_id: null, parent_id: null })
  })

  it('keeps teacher/parent ids when present', () => {
    saveAuth({ access_token: 't', role: 'teacher', user_id: 'u2', email: 't@x.com', teacher_id: 'T1' })
    expect(getStoredUser().teacher_id).toBe('T1')
  })

  it('returns null for corrupt stored user JSON', () => {
    window.localStorage.setItem('school_user', '{oops')
    expect(getStoredUser()).toBeNull()
  })

  it('clears both keys', () => {
    saveAuth({ access_token: 't', role: 'parent', user_id: 'u3', email: 'p@x.com' })
    clearAuth()
    expect(getToken()).toBeNull()
    expect(getStoredUser()).toBeNull()
  })
})

describe('api()', () => {
  it('sends Bearer token from storage', async () => {
    saveAuth({ access_token: 'abc', role: 'admin', user_id: 'u', email: 'a@x.com' })
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"ok":true}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    const data = await api('/api/v1/things')
    expect(data).toEqual({ ok: true })
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/v1/things')
    expect(init.headers.Authorization).toBe('Bearer abc')
  })

  it('sends JSON body with content-type', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await api('/api/v1/x', { method: 'POST', body: { a: 1 } })
    const [, init] = fetchMock.mock.calls[0]
    expect(init.method).toBe('POST')
    expect(init.body).toBe('{"a":1}')
    expect(init.headers['Content-Type']).toBe('application/json')
  })

  it('does not attach auth when no token', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await api('/api/v1/x')
    const [, init] = fetchMock.mock.calls[0]
    expect(init.headers.Authorization).toBeUndefined()
  })

  it('parses string detail from error responses', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"detail":"nope"}', { status: 400 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(api('/api/v1/x')).rejects.toThrow('nope')
  })

  it('joins array detail messages', async () => {
    const body = JSON.stringify({ detail: [{ msg: 'field a broken' }, { msg: 'field b broken' }] })
    const fetchMock = vi.fn().mockResolvedValue(new Response(body, { status: 422 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(api('/api/v1/x')).rejects.toThrow('field a broken; field b broken')
  })

  it('falls back to message', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"message":"boom"}', { status: 500 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(api('/api/v1/x')).rejects.toThrow('boom')
  })

  it('falls back to a generic message', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 503 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(api('/api/v1/x')).rejects.toThrow('Request failed with status 503')
  })

  it('treats non-JSON success bodies as detail', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('plain text', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    const data = await api('/api/v1/x')
    expect(data).toEqual({ detail: 'plain text' })
  })

  it('clears session and redirects on 401 except for login', async () => {
    saveAuth({ access_token: 't', role: 'admin', user_id: 'u', email: 'a@x.com' })
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"detail":"expired"}', { status: 401 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(api('/api/v1/things')).rejects.toThrow('Session expired. Please log in again.')
    expect(getToken()).toBeNull()
    expect(window.location.href).toBe('/login')
  })

  it('does not hijack failed login attempts', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"detail":"bad credentials"}', { status: 401 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(api('/api/v1/auth/login', { method: 'POST', body: {} })).rejects.toThrow('bad credentials')
    expect(window.location.href).not.toBe('/login')
  })

  it('unwraps login data when 401-less success', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"access_token":"x","role":"admin"}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    const data = await api('/api/v1/auth/login', { method: 'POST', body: {} })
    expect(data.role).toBe('admin')
  })

  it('surfaces the type error detail shape', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"detail":"gone"}', { status: 404 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(api('/api/v1/none')).rejects.toThrow('gone')
  })
})

describe('downloadFile()', () => {
  function fakeBlobUrl() {
    let created = null
    const orig = URL.createObjectURL
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: vi.fn(() => {
        created = 'blob:fake'
        return created
      }),
    })
    URL.revokeObjectURL = vi.fn()
    return orig
  }

  it('downloads a blob and clicks a link', async () => {
    const orig = fakeBlobUrl()
    const blob = new Blob(['pdf'], { type: 'application/pdf' })
    const fetchMock = vi.fn().mockResolvedValue(new Response(blob, { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    await downloadFile('/api/v1/reports/portal/s1', 'report.pdf')

    expect(fetchMock).toHaveBeenCalled()
    expect(clickSpy).toHaveBeenCalled()

    orig
    URL.createObjectURL = orig
  })

  it('throws on 401 and clears auth', async () => {
    saveAuth({ access_token: 't', role: 'parent', user_id: 'u', email: 'p@x.com' })
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 401 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(downloadFile('/api/v1/reports/portal/s1', 'r.pdf')).rejects.toThrow('Session expired')
    expect(getToken()).toBeNull()
    expect(window.location.href).toBe('/login')
  })

  it('throws with backend detail on failure', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"detail":"no file"}', { status: 404 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(downloadFile('/a', 'a.pdf')).rejects.toThrow('no file')
  })
})