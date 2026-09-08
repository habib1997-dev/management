import { createContext, useContext, useState } from 'react'
import { api, clearAuth, getStoredUser, getToken, saveAuth } from './api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser())
  const [token, setToken] = useState(getToken())

  async function login(email, password) {
    const data = await api('/api/v1/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    saveAuth(data)
    setUser({ role: data.role, user_id: data.user_id, email: data.email })
    setToken(data.access_token)
    return data.role
  }

  function logout() {
    clearAuth()
    setUser(null)
    setToken(null)
  }

  const value = {
    user,
    token,
    isAuthenticated: Boolean(token),
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}