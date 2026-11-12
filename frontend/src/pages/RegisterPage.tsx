import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'

interface FormState {
    cnpj: string
    razaoSocial: string
    nomeFantasia: string
    endereco: string
    telefone: string
    email: string
    senha: string
}

export default function RegisterPage() {
    const [form, setForm] = useState<FormState>({
        cnpj: '',
        razaoSocial: '',
        nomeFantasia: '',
        endereco: '',
        telefone: '',
        email: '',
        senha: '',
    })
    const [loading, setLoading] = useState(false)
    const [success, setSuccess] = useState(false)
    const [error, setError] = useState<string | null>(null)

    function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
        const { name, value } = e.target
        setForm((prev) => ({ ...prev, [name]: value }))
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault()
        setError(null)
        setLoading(true)

        try {
            await api.post('/api/v1/auth/company/register', {
                cnpj: form.cnpj,
                razao_social: form.razaoSocial,
                nome_fantasia: form.nomeFantasia || undefined,
                endereco: form.endereco,
                telefone: form.telefone,
                email: form.email,
                senha: form.senha,
            })
            setSuccess(true)
        } catch (err: any) {
            const detail = err.response?.data?.detail
            if (typeof detail === 'string') {
                if (detail.includes('CNPJ') || detail.includes('cnpj')) {
                    setError('CNPJ já cadastrado no sistema.')
                } else if (detail.includes('email') || detail.includes('e-mail')) {
                    setError('E-mail já cadastrado no sistema.')
                } else {
                    setError(detail)
                }
            } else if (Array.isArray(detail)) {
                // Pydantic validation errors
                const messages = detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ')
                setError(`Erro de validação: ${messages}`)
            } else {
                setError('Erro ao enviar cadastro. Verifique os dados e tente novamente.')
            }
        } finally {
            setLoading(false)
        }
    }

    if (success) {
        return (
            <div style={{ maxWidth: 400, margin: '80px auto', padding: '0 16px', textAlign: 'center' }}>
                <div style={{ background: '#d4edda', border: '1px solid #28a745', borderRadius: 4, padding: 20, marginBottom: 16 }}>
                    <strong>Cadastro enviado! Aguarde aprovação.</strong>
                    <p style={{ margin: '8px 0 0' }}>Você receberá uma notificação quando seu cadastro for analisado.</p>
                </div>
                <Link to="/login">Voltar para o login</Link>
            </div>
        )
    }

    return (
        <div style={{ maxWidth: 480, margin: '60px auto', padding: '0 16px' }}>
            <h1>Cadastro de Empresa</h1>

            {error && (
                <div style={{ background: '#f8d7da', border: '1px solid #dc3545', borderRadius: 4, padding: 12, marginBottom: 16 }}>
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit}>
                <Field label="CNPJ *" id="cnpj" name="cnpj" value={form.cnpj} onChange={handleChange} required disabled={loading} placeholder="00.000.000/0000-00" />
                <Field label="Razão Social *" id="razaoSocial" name="razaoSocial" value={form.razaoSocial} onChange={handleChange} required disabled={loading} />
                <Field label="Nome Fantasia" id="nomeFantasia" name="nomeFantasia" value={form.nomeFantasia} onChange={handleChange} disabled={loading} />
                <Field label="Endereço *" id="endereco" name="endereco" value={form.endereco} onChange={handleChange} required disabled={loading} />
                <Field label="Telefone *" id="telefone" name="telefone" value={form.telefone} onChange={handleChange} required disabled={loading} placeholder="(00) 00000-0000" />
                <Field label="E-mail *" id="email" name="email" type="email" value={form.email} onChange={handleChange} required disabled={loading} />
                <Field label="Senha *" id="senha" name="senha" type="password" value={form.senha} onChange={handleChange} required disabled={loading} />

                <button
                    type="submit"
                    disabled={loading}
                    style={{ width: '100%', padding: '10px', marginTop: 8, cursor: loading ? 'not-allowed' : 'pointer' }}
                >
                    {loading ? 'Enviando...' : 'Cadastrar'}
                </button>
            </form>

            <p style={{ marginTop: 16, textAlign: 'center' }}>
                Já tem conta? <Link to="/login">Entrar</Link>
            </p>
        </div>
    )
}

interface FieldProps {
    label: string
    id: string
    name: string
    value: string
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
    required?: boolean
    disabled?: boolean
    type?: string
    placeholder?: string
}

function Field({ label, id, name, value, onChange, required, disabled, type = 'text', placeholder }: FieldProps) {
    return (
        <div style={{ marginBottom: 16 }}>
            <label htmlFor={id} style={{ display: 'block', marginBottom: 4 }}>{label}</label>
            <input
                id={id}
                name={name}
                type={type}
                value={value}
                onChange={onChange}
                required={required}
                disabled={disabled}
                placeholder={placeholder}
                style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
            />
        </div>
    )
}
