const TOKEN_KEY = 'school_token'
const USER_KEY = 'school_user'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

export function saveAuth({ access_token, role, user_id, email }) {
  localStorage.setItem(TOKEN_KEY, access_token)
  localStorage.setItem(USER_KEY, JSON.stringify({ role, user_id, email }))
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export async function api(path, { method = 'GET', body } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  const res = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401) {
    clearAuth()
    window.location.href = '/login'
    throw new Error('Session expired. Please log in again.')
  }

  const text = await res.text()
  let data = null
  try {
    data = JSON.parse(text)
  } catch {
    data = { detail: text }
  }

  if (!res.ok) {
    if (typeof data?.detail === 'string') {
      throw new Error(data.detail)
    }
    if (Array.isArray(data?.detail)) {
      throw new Error(data.detail.map((d) => d.msg || JSON.stringify(d)).join('; '))
    }
    throw new Error(data?.message || `Request failed with status ${res.status}`)
  }
  return data
}