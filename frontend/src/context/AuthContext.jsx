import React, { createContext, useContext, useState, useEffect } from 'react'
import { apiService } from '../services/api'
import { useNavigate } from 'react-router-dom'

const AuthContext = createContext(null)

export const useAuth = () => useContext(AuthContext)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('chatx_user')) || null
    } catch {
      return null
    }
  })
  const [token, setToken] = useState(() => localStorage.getItem('chatx_token') || null)
  const navigate = useNavigate()

  useEffect(() => {
    // On load, verify token if present
    const verify = async () => {
      if (!token) return
      try {
        const res = await apiService.auth.getMe()
        setUser(res.data)
        localStorage.setItem('chatx_user', JSON.stringify(res.data))
      } catch (err) {
        // invalid token
        logout()
      }
    }
    verify()
  }, [])

  const register = async (payload) => {
    const res = await apiService.auth.register(payload)
    return res.data
  }

  const login = async ({ email, password }) => {
    const res = await apiService.auth.login({ 
      username_or_email: email, 
      password 
    })
    const data = res.data
    if (data && data.access_token) {
      localStorage.setItem('chatx_token', data.access_token)
      setToken(data.access_token)
      // fetch user
      const me = await apiService.auth.getMe()
      setUser(me.data)
      localStorage.setItem('chatx_user', JSON.stringify(me.data))
      navigate('/chat')
    }
    return data
  }

  const logout = () => {
    localStorage.removeItem('chatx_token')
    localStorage.removeItem('chatx_user')
    setUser(null)
    setToken(null)
    navigate('/login')
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  )
}
