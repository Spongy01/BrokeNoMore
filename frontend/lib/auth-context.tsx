'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useRouter } from 'next/navigation'

interface AuthUser {
  email: string
}

interface AuthContextType {
  token: string | null
  user: AuthUser | null
  login: (token: string, email: string) => void
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<AuthUser | null>(null)
  const router = useRouter()

  useEffect(() => {
    const stored = localStorage.getItem('brokenomore_token')
    const email = localStorage.getItem('brokenomore_email')
    if (stored && email) {
      setToken(stored)
      setUser({ email })
    }
  }, [])

  function login(token: string, email: string) {
    localStorage.setItem('brokenomore_token', token)
    localStorage.setItem('brokenomore_email', email)
    document.cookie = `brokenomore_token=${token}; path=/; max-age=3600; SameSite=Lax`
    setToken(token)
    setUser({ email })
  }

  async function logout() {
    localStorage.removeItem('brokenomore_token')
    localStorage.removeItem('brokenomore_email')
    document.cookie = 'brokenomore_token=; path=/; max-age=0'
    setToken(null)
    setUser(null)
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/auth/logout`, {
        method: 'POST',
      })
    } catch {
      // stateless JWT — safe to ignore
    }
    router.push('/login')
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
