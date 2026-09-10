import { createContext, useContext, useEffect, useState } from 'react'
import {
  clearAuthSession,
  getMe,
  getStoredToken,
  getStoredUser,
  login as apiLogin,
  register as apiRegister,
  setAuthSession,
} from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser())
  const [loading, setLoading] = useState(!!getStoredToken())

  useEffect(() => {
    const token = getStoredToken()
    if (!token) {
      setLoading(false)
      return
    }
    getMe()
      .then((res) => {
        setUser(res.data)
        setAuthSession(token, res.data)
      })
      .catch(() => {
        clearAuthSession()
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = async (username, password) => {
    const res = await apiLogin(username, password)
    setAuthSession(res.data.access_token, res.data.user)
    setUser(res.data.user)
    return res.data.user
  }

  const register = async ({ email, username, password }) => {
    await apiRegister({ email, username, password })
    return login(username, password)
  }

  const logout = () => {
    clearAuthSession()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
