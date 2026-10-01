import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, getToken, setToken, type User } from './api'

interface Ctx { user: User | null; loading: boolean; login: (token: string) => Promise<User | null>; logout: () => void; refresh: () => Promise<User | null> }
const AuthCtx = createContext<Ctx>(null!)
export const useAuth = () => useContext(AuthCtx)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(!!getToken())

  const refresh = useCallback(async () => {
    if (!getToken()) { setUser(null); setLoading(false); return null }
    try { const { data } = await api.get<User>('/auth/me'); setUser(data); return data }
    catch { setToken(null); setUser(null); return null }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const login = async (token: string) => { setToken(token); return refresh() }
  const logout = () => { setToken(null); setUser(null); window.location.href = '/' }

  return <AuthCtx.Provider value={{ user, loading, login, logout, refresh }}>{children}</AuthCtx.Provider>
}

/** Where should a signed-in user land? */
export function nextRoute(u: User) {
  if (!u.has_completed_assessment) return '/welcome'
  if (!u.has_completed_availability) return '/schedule'
  return '/dashboard'
}
