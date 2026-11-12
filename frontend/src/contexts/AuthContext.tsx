import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
    id: string
    role: string
    email: string
}

interface AuthContextValue {
    user: User | null
    token: string | null
    login: (token: string, role: string, email: string, id: string) => void
    logout: () => void
    isAuthenticated: boolean
    isAdmin: boolean
    isCompany: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
    const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
    const [user, setUser] = useState<User | null>(() => {
        const stored = localStorage.getItem('user')
        return stored ? JSON.parse(stored) : null
    })

    function login(token: string, role: string, email: string, id: string) {
        const userData: User = { id, role, email }
        localStorage.setItem('token', token)
        localStorage.setItem('user', JSON.stringify(userData))
        setToken(token)
        setUser(userData)
    }

    function logout() {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        setToken(null)
        setUser(null)
    }

    const isAuthenticated = token !== null && user !== null
    const isAdmin = user?.role === 'admin'
    const isCompany = user?.role === 'company'

    return (
        <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated, isAdmin, isCompany }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth(): AuthContextValue {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth must be used within AuthProvider')
    return ctx
}
