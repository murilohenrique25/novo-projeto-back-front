import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import api from '../services/api'

type RegistrationStatus = 'pending' | 'rejected' | null

export default function LoginPage() {
    const { login } = useAuth()
    const navigate = useNavigate()

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [registrationStatus, setRegistrationStatus] = useState<RegistrationStatus>(null)

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault()
        setError(null)
        setRegistrationStatus(null)
        setLoading(true)

        const credentials = { email, password }

        try {
            // Try company login first
            try {
                const res = await api.post('/api/v1/auth/company/login', credentials)
                const { access_token, role, email: userEmail, id } = res.data
                login(access_token, role ?? 'company', userEmail ?? email, id)
                navigate('/dashboard')
                return
            } catch (companyErr: any) {
                const detail = companyErr.response?.data?.detail
                // If registration not approved, show status message instead of trying admin
                if (detail === 'REGISTRATION_NOT_APPROVED' || detail?.code === 'REGISTRATION_NOT_APPROVED') {
                    const status = companyErr.response?.data?.status
                    setRegistrationStatus(status === 'rejected' ? 'rejected' : 'pending')
                    return
                }
                // If it's a 401/403 for wrong credentials, don't try admin
                if (companyErr.response?.status === 401) {
                    throw companyErr
                }
                // Otherwise fall through to admin login
            }

            // Try admin login
            const res = await api.post('/api/v1/auth/admin/login', credentials)
            const { access_token, role, email: userEmail, id } = res.data
            login(access_token, role ?? 'admin', userEmail ?? email, id)
            navigate('/admin')
        } catch (err: any) {
            const detail = err.response?.data?.detail
            if (detail === 'REGISTRATION_NOT_APPROVED' || detail?.code === 'REGISTRATION_NOT_APPROVED') {
                const status = err.response?.data?.status
                setRegistrationStatus(status === 'rejected' ? 'rejected' : 'pending')
            } else if (err.response?.status === 401 || err.response?.status === 403) {
                setError('E-mail ou senha inválidos.')
            } else {
                setError('Erro ao conectar ao servidor. Tente novamente.')
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{ maxWidth: 400, margin: '80px auto', padding: '0 16px' }}>
            <h1>Entrar</h1>

            {registrationStatus === 'pending' && (
                <div style={{ background: '#fff3cd', border: '1px solid #ffc107', borderRadius: 4, padding: 12, marginBottom: 16 }}>
                    Seu cadastro está <strong>em análise</strong>. Aguarde a aprovação do administrador.
                </div>
            )}

            {registrationStatus === 'rejected' && (
                <div style={{ background: '#f8d7da', border: '1px solid #dc3545', borderRadius: 4, padding: 12, marginBottom: 16 }}>
                    Seu cadastro foi <strong>rejeitado</strong>. Entre em contato com o suporte para mais informações.
                </div>
            )}

            {error && (
                <div style={{ background: '#f8d7da', border: '1px solid #dc3545', borderRadius: 4, padding: 12, marginBottom: 16 }}>
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit}>
                <div style={{ marginBottom: 16 }}>
                    <label htmlFor="email" style={{ display: 'block', marginBottom: 4 }}>E-mail</label>
                    <input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        disabled={loading}
                        style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                    />
                </div>

                <div style={{ marginBottom: 24 }}>
                    <label htmlFor="password" style={{ display: 'block', marginBottom: 4 }}>Senha</label>
                    <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        disabled={loading}
                        style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                    />
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    style={{ width: '100%', padding: '10px', cursor: loading ? 'not-allowed' : 'pointer' }}
                >
                    {loading ? 'Entrando...' : 'Entrar'}
                </button>
            </form>

            <p style={{ marginTop: 16, textAlign: 'center' }}>
                Não tem conta? <Link to="/register">Cadastre sua empresa</Link>
            </p>
        </div>
    )
}
