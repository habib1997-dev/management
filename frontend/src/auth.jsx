import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { api, clearAuth, getStoredUser, getToken, saveAuth } from './api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser())
  const [token, setToken] = useState(getToken())

  const login = useCallback(async (email, password) => {
    const data = await api('/api/v1/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    saveAuth(data)
    setUser({
      role: data.role,
      user_id: data.user_id,
      email: data.email,
      teacher_id: data.teacher_id || null,
      parent_id: data.parent_id || null,
    })
    setToken(data.access_token)
    return data.role
  }, [])

  const logout = useCallback(() => {
    clearAuth()
    setUser(null)
    setToken(null)
  }, [])

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token),
      login,
      logout,
    }),
    [user, token, login, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}