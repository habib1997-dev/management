const TOKEN_KEY = 'school_token'
const USER_KEY = 'school_user'
const BASE = import.meta.env.BASE_URL || '/'
const LOGIN_PATH = `${BASE}login`

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

export function saveAuth({ access_token, role, user_id, email, teacher_id, parent_id }) {
  localStorage.setItem(TOKEN_KEY, access_token)
  localStorage.setItem(
    USER_KEY,
    JSON.stringify({ role, user_id, email, teacher_id: teacher_id || null, parent_id: parent_id || null })
  )
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
    // A failed login attempt (bad email/password) is NOT an expired session:
    // let the error bubble so the login form can show it without a reload.
    if (path !== '/api/v1/auth/login') {
      clearAuth()
      window.location.href = LOGIN_PATH
      throw new Error('Session expired. Please log in again.')
    }
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

export async function downloadFile(path, filename) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(path, { headers })

  if (res.status === 401) {
    clearAuth()
    window.location.href = LOGIN_PATH
    throw new Error('Session expired. Please log in again.')
  }
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`
    try {
      const j = await res.json()
      if (j?.detail) detail = j.detail
    } catch {
      /* keep default */
    }
    throw new Error(detail)
  }

  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}