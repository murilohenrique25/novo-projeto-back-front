import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

// ─── Types ────────────────────────────────────────────────────────────────────

type RegStatus = 'pendente' | 'aprovado' | 'rejeitado'

interface Deliverer {
    id: string
    full_name: string
    cpf: string
    email: string
    phone: string
    city_id: string
    reg_status: RegStatus
}

interface Company {
    id: string
    legal_name: string
    cnpj: string
    email: string
    phone: string
    reg_status: RegStatus
    return(
        <span
            style = {{
            background: colors[status],
            color: '#fff',
            padding: '2px 10px',
            borderRadius: 12,
            fontSize: 12,
            fontWeight: 600,
            textTransform: 'capitalize',
        }}
        >
    { status }
        </span >
    )
}

function truncate(str: string, n = 12) {
    return str.length > n ? str.slice(0, n) + '…' : str
}

// ─── Tab: Entregadores ────────────────────────────────────────────────────────

function DeliverersTab() {
    const [deliverers, setDeliverers] = useState<Deliverer[]>([])
    const [filter, setFilter] = useState<RegStatus | ''>('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const fetchDeliverers = useCallback(async () => {
        setLoading(true)
        setError('')
        try {
            const params = filter ? { reg_status: filter } : {}
            const res = await api.get('/api/v1/admin/deliverers', { params })
            setDeliverers(res.data)
        } catch {
            setError('Erro ao carregar entregadores.')
        } finally {
            setLoading(false)
        }
    }, [filter])

    useEffect(() => { fetchDeliverers() }, [fetchDeliverers])

    async function approve(id: string) {
        try {
            await api.patch(`/api/v1/admin/deliverers/${id}/approve`)
            fetchDeliverers()
        } catch {
            alert('Erro ao aprovar entregador.')
        }
    }

    async function reject(id: string) {
        const reason = prompt('Motivo da rejeição:')
        if (reason === null) return
        try {
            await api.patch(`/api/v1/admin/deliverers/${id}/reject`, { reason })
            fetchDeliverers()
        } catch {
            alert('Erro ao rejeitar entregador.')
        }
    }

    async function remove(id: string) {
        if (!confirm('Excluir entregador?')) return
        try {
            await api.delete(`/api/v1/admin/deliverers/${id}`)
            fetchDeliverers()
        } catch {
            alert('Erro ao excluir entregador.')
        }
    }

    const filters: { label: string; value: RegStatus | '' }[] = [
        { label: 'Todos', value: '' },
        { label: 'Pendentes', value: 'pendente' },
        { label: 'Aprovados', value: 'aprovado' },
        { label: 'Rejeitados', value: 'rejeitado' },
    ]

    return (
        <div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                {filters.map((f) => (
                    <button
                        key={f.value}
                        onClick={() => setFilter(f.value)}
                        style={{
                            padding: '6px 14px',
                            borderRadius: 6,
                            border: 'none',
                            cursor: 'pointer',
                            background: filter === f.value ? '#6366f1' : '#e5e7eb',
                            color: filter === f.value ? '#fff' : '#374151',
                            fontWeight: 600,
                        }}
                    >
                        {f.label}
                    </button>
                ))}
            </div>

            {loading && <p>Carregando...</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}

            {!loading && !error && (
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                        <thead>
                            <tr style={{ background: '#f3f4f6' }}>
                                {['Nome', 'CPF', 'E-mail', 'Telefone', 'Cidade', 'Status', 'Ações'].map((h) => (
                                    <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontWeight: 700 }}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {deliverers.length === 0 && (
                                <tr><td colSpan={7} style={{ padding: 16, textAlign: 'center', color: '#9ca3af' }}>Nenhum entregador encontrado.</td></tr>
                            )}
                            {deliverers.map((d) => (
                                <tr key={d.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                                    <td style={{ padding: '10px 12px' }}>{d.full_name}</td>
                                    <td style={{ padding: '10px 12px' }}>{d.cpf}</td>
                                    <td style={{ padding: '10px 12px' }}>{d.email}</td>
                                    <td style={{ padding: '10px 12px' }}>{d.phone}</td>
                                    <td style={{ padding: '10px 12px' }} title={d.city_id}>{truncate(d.city_id)}</td>
                                    <td style={{ padding: '10px 12px' }}><StatusBadge status={d.reg_status} /></td>
                                    <td style={{ padding: '10px 12px', display: 'flex', gap: 6 }}>
                                        <ActionBtn label="Aprovar" color="#10b981" onClick={() => approve(d.id)} />
                                        <ActionBtn label="Rejeitar" color="#f59e0b" onClick={() => reject(d.id)} />
                                        <ActionBtn label="Excluir" color="#ef4444" onClick={() => remove(d.id)} />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}

// ─── Tab: Empresas ────────────────────────────────────────────────────────────

function CompaniesTab() {
    const [companies, setCompanies] = useState<Company[]>([])
    const [filter, setFilter] = useState<RegStatus | ''>('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const fetchCompanies = useCallback(async () => {
        setLoading(true)
        setError('')
        try {
            const params = filter ? { reg_status: filter } : {}
            const res = await api.get('/api/v1/admin/companies', { params })
            setCompanies(res.data)
        } catch {
            setError('Erro ao carregar empresas.')
        } finally {
            setLoading(false)
        }
    }, [filter])

    useEffect(() => { fetchCompanies() }, [fetchCompanies])

    async function approve(id: string) {
        try {
            await api.patch(`/api/v1/admin/companies/${id}/approve`)
            fetchCompanies()
        } catch {
            alert('Erro ao aprovar empresa.')
        }
    }

    async function reject(id: string) {
        const reason = prompt('Motivo da rejeição:')
        if (reason === null) return
        try {
            await api.patch(`/api/v1/admin/companies/${id}/reject`, { reason })
            fetchCompanies()
        } catch {
            alert('Erro ao rejeitar empresa.')
        }
    }

    async function remove(id: string) {
        if (!confirm('Excluir empresa?')) return
        try {
            await api.delete(`/api/v1/admin/companies/${id}`)
            fetchCompanies()
        } catch {
            alert('Erro ao excluir empresa.')
        }
    }

    const filters: { label: string; value: RegStatus | '' }[] = [
        { label: 'Todos', value: '' },
        { label: 'Pendentes', value: 'pendente' },
        { label: 'Aprovados', value: 'aprovado' },
        { label: 'Rejeitados', value: 'rejeitado' },
    ]

    return (
        <div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                {filters.map((f) => (
                    <button
                        key={f.value}
                        onClick={() => setFilter(f.value)}
                        style={{
                            padding: '6px 14px',
                            borderRadius: 6,
                            border: 'none',
                            cursor: 'pointer',
                            background: filter === f.value ? '#6366f1' : '#e5e7eb',
                            color: filter === f.value ? '#fff' : '#374151',
                            fontWeight: 600,
                        }}
                    >
                        {f.label}
                    </button>
                ))}
            </div>

            {loading && <p>Carregando...</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}

            {!loading && !error && (
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                        <thead>
                            <tr style={{ background: '#f3f4f6' }}>
                                {['Razão Social', 'CNPJ', 'E-mail', 'Telefone', 'Status', 'Saldo', 'Ações'].map((h) => (
                                    <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontWeight: 700 }}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {companies.length === 0 && (
                                <tr><td colSpan={7} style={{ padding: 16, textAlign: 'center', color: '#9ca3af' }}>Nenhuma empresa encontrada.</td></tr>
                            )}
                            {companies.map((c) => (
                                <tr key={c.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                                    <td style={{ padding: '10px 12px' }}>{c.legal_name}</td>
                                    <td style={{ padding: '10px 12px' }}>{c.cnpj}</td>
                                    <td style={{ padding: '10px 12px' }}>{c.email}</td>
                                    <td style={{ padding: '10px 12px' }}>{c.phone}</td>
                                    <td style={{ padding: '10px 12px' }}><StatusBadge status={c.reg_status} /></td>
                                    <td style={{ padding: '10px 12px' }}>R$ {c.balance.toFixed(2)}</td>
                                    <td style={{ padding: '10px 12px', display: 'flex', gap: 6 }}>
                                        <ActionBtn label="Aprovar" color="#10b981" onClick={() => approve(c.id)} />
                                        <ActionBtn label="Rejeitar" color="#f59e0b" onClick={() => reject(c.id)} />
                                        <ActionBtn label="Excluir" color="#ef4444" onClick={() => remove(c.id)} />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}

// ─── Tab: Configurações ───────────────────────────────────────────────────────

function SettingsTab() {
    const [settings, setSettings] = useState<PlatformSettings>({ platform_percentage: 0, deliverer_percentage: 0 })
    const [loading, setLoading] = useState(false)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState('')
    const [success, setSuccess] = useState('')

    useEffect(() => {
        setLoading(true)
        api.get('/api/v1/admin/settings')
            .then((res) => setSettings(res.data))
            .catch(() => setError('Erro ao carregar configurações.'))
            .finally(() => setLoading(false))
    }, [])

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault()
        setError('')
        setSuccess('')
        const sum = Number(settings.platform_percentage) + Number(settings.deliverer_percentage)
        if (Math.abs(sum - 100) > 0.001) {
            setError('A soma das porcentagens deve ser 100%.')
            return
        }
        setSaving(true)
        try {
            await api.put('/api/v1/admin/settings', settings)
            setSuccess('Configurações salvas com sucesso.')
        } catch {
            setError('Erro ao salvar configurações.')
        } finally {
            setSaving(false)
        }
    }

    if (loading) return <p>Carregando...</p>

    return (
        <form onSubmit={handleSubmit} style={{ maxWidth: 400 }}>
            <h3 style={{ marginBottom: 16 }}>Porcentagens Globais</h3>

            <label style={labelStyle}>
                Porcentagem da Plataforma (%)
                <input
                    type="number"
                    min={0}
                    max={100}
                    step={0.01}
                    value={settings.platform_percentage}
                    onChange={(e) => setSettings({ ...settings, platform_percentage: Number(e.target.value) })}
                    style={inputStyle}
                    required
                />
            </label>

            <label style={labelStyle}>
                Porcentagem do Entregador (%)
                <input
                    type="number"
                    min={0}
                    max={100}
                    step={0.01}
                    value={settings.deliverer_percentage}
                    onChange={(e) => setSettings({ ...settings, deliverer_percentage: Number(e.target.value) })}
                    style={inputStyle}
                    required
                />
            </label>

            <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 12 }}>
                Soma atual: {(Number(settings.platform_percentage) + Number(settings.deliverer_percentage)).toFixed(2)}%
            </p>

            {error && <p style={{ color: 'red', marginBottom: 8 }}>{error}</p>}
            {success && <p style={{ color: '#10b981', marginBottom: 8 }}>{success}</p>}

            <button type="submit" disabled={saving} style={primaryBtnStyle}>
                {saving ? 'Salvando...' : 'Salvar'}
            </button>
        </form>
    )
}

// ─── Tab: Taxas por Empresa ───────────────────────────────────────────────────

function RatesTab() {
    const [companyId, setCompanyId] = useState('')
    const [rates, setRates] = useState<DeliveryRate[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [editingId, setEditingId] = useState<string | null>(null)
    const [editForm, setEditForm] = useState<Omit<DeliveryRate, 'id'>>({ min_radius_km: 0, max_radius_km: 0, fee: 0 })
    const [newRate, setNewRate] = useState<Omit<DeliveryRate, 'id'>>({ min_radius_km: 0, max_radius_km: 0, fee: 0 })
    const [searched, setSearched] = useState(false)

    async function fetchRates() {
        if (!companyId.trim()) return
        setLoading(true)
        setError('')
        setSearched(true)
        try {
            const res = await api.get(`/api/v1/admin/companies/${companyId.trim()}/rates`)
            setRates(res.data)
        } catch {
            setError('Erro ao carregar taxas. Verifique o UUID da empresa.')
            setRates([])
        } finally {
            setLoading(false)
        }
    }

    async function addRate(e: React.FormEvent) {
        e.preventDefault()
        try {
            await api.post(`/api/v1/admin/companies/${companyId.trim()}/rates`, newRate)
            setNewRate({ min_radius_km: 0, max_radius_km: 0, fee: 0 })
            fetchRates()
        } catch {
            alert('Erro ao adicionar taxa.')
        }
    }

    async function saveEdit(id: string) {
        try {
            await api.put(`/api/v1/admin/companies/${companyId.trim()}/rates/${id}`, editForm)
            setEditingId(null)
            fetchRates()
        } catch {
            alert('Erro ao salvar taxa.')
        }
    }

    async function deleteRate(id: string) {
        if (!confirm('Excluir taxa?')) return
        try {
            await api.delete(`/api/v1/admin/companies/${companyId.trim()}/rates/${id}`)
            fetchRates()
        } catch {
            alert('Erro ao excluir taxa.')
        }
    }

    function startEdit(rate: DeliveryRate) {
        setEditingId(rate.id)
        setEditForm({ min_radius_km: rate.min_radius_km, max_radius_km: rate.max_radius_km, fee: rate.fee })
    }

    return (
        <div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 20, alignItems: 'flex-end' }}>
                <label style={{ ...labelStyle, marginBottom: 0, flex: 1 }}>
                    UUID da Empresa
                    <input
                        type="text"
                        value={companyId}
                        onChange={(e) => setCompanyId(e.target.value)}
                        placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                        style={inputStyle}
                    />
                </label>
                <button onClick={fetchRates} style={{ ...primaryBtnStyle, marginTop: 20 }}>Buscar</button>
            </div>

            {loading && <p>Carregando...</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}

            {searched && !loading && !error && (
                <>
                    <div style={{ overflowX: 'auto', marginBottom: 24 }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                            <thead>
                                <tr style={{ background: '#f3f4f6' }}>
                                    {['Raio Mín (km)', 'Raio Máx (km)', 'Taxa (R$)', 'Ações'].map((h) => (
                                        <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontWeight: 700 }}>{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {rates.length === 0 && (
                                    <tr><td colSpan={4} style={{ padding: 16, textAlign: 'center', color: '#9ca3af' }}>Nenhuma taxa cadastrada.</td></tr>
                                )}
                                {rates.map((r) => (
                                    <tr key={r.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                                        {editingId === r.id ? (
                                            <>
                                                <td style={{ padding: '8px 12px' }}>
                                                    <input type="number" value={editForm.min_radius_km} onChange={(e) => setEditForm({ ...editForm, min_radius_km: Number(e.target.value) })} style={{ ...inputStyle, marginBottom: 0 }} />
                                                </td>
                                                <td style={{ padding: '8px 12px' }}>
                                                    <input type="number" value={editForm.max_radius_km} onChange={(e) => setEditForm({ ...editForm, max_radius_km: Number(e.target.value) })} style={{ ...inputStyle, marginBottom: 0 }} />
                                                </td>
                                                <td style={{ padding: '8px 12px' }}>
                                                    <input type="number" step="0.01" value={editForm.fee} onChange={(e) => setEditForm({ ...editForm, fee: Number(e.target.value) })} style={{ ...inputStyle, marginBottom: 0 }} />
                                                </td>
                                                <td style={{ padding: '8px 12px', display: 'flex', gap: 6 }}>
                                                    <ActionBtn label="Salvar" color="#10b981" onClick={() => saveEdit(r.id)} />
                                                    <ActionBtn label="Cancelar" color="#6b7280" onClick={() => setEditingId(null)} />
                                                </td>
                                            </>
                                        ) : (
                                            <>
                                                <td style={{ padding: '10px 12px' }}>{r.min_radius_km}</td>
                                                <td style={{ padding: '10px 12px' }}>{r.max_radius_km}</td>
                                                <td style={{ padding: '10px 12px' }}>R$ {r.fee.toFixed(2)}</td>
                                                <td style={{ padding: '10px 12px', display: 'flex', gap: 6 }}>
                                                    <ActionBtn label="Editar" color="#6366f1" onClick={() => startEdit(r)} />
                                                    <ActionBtn label="Excluir" color="#ef4444" onClick={() => deleteRate(r.id)} />
                                                </td>
                                            </>
                                        )}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <h4 style={{ marginBottom: 12 }}>Adicionar Nova Taxa</h4>
                    <form onSubmit={addRate} style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                        <label style={{ ...labelStyle, marginBottom: 0 }}>
                            Raio Mín (km)
                            <input type="number" min={0} step={0.1} value={newRate.min_radius_km} onChange={(e) => setNewRate({ ...newRate, min_radius_km: Number(e.target.value) })} style={inputStyle} required />
                        </label>
                        <label style={{ ...labelStyle, marginBottom: 0 }}>
                            Raio Máx (km)
                            <input type="number" min={0} step={0.1} value={newRate.max_radius_km} onChange={(e) => setNewRate({ ...newRate, max_radius_km: Number(e.target.value) })} style={inputStyle} required />
                        </label>
                        <label style={{ ...labelStyle, marginBottom: 0 }}>
                            Taxa (R$)
                            <input type="number" min={0} step={0.01} value={newRate.fee} onChange={(e) => setNewRate({ ...newRate, fee: Number(e.target.value) })} style={inputStyle} required />
                        </label>
                        <button type="submit" style={{ ...primaryBtnStyle, marginTop: 20 }}>Adicionar</button>
                    </form>
                </>
            )}
        </div>
    )
}

// ─── Shared styles ────────────────────────────────────────────────────────────

const labelStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
    fontSize: 14,
    fontWeight: 600,
    color: '#374151',
    marginBottom: 14,
}

const inputStyle: React.CSSProperties = {
    padding: '8px 10px',
    borderRadius: 6,
    border: '1px solid #d1d5db',
    fontSize: 14,
    marginBottom: 4,
    width: '100%',
    boxSizing: 'border-box',
}

const primaryBtnStyle: React.CSSProperties = {
    padding: '8px 20px',
    background: '#6366f1',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: 14,
}

function ActionBtn({ label, color, onClick }: { label: string; color: string; onClick: () => void }) {
    return (
        <button
            onClick={onClick}
            style={{
                padding: '4px 10px',
                background: color,
                color: '#fff',
                border: 'none',
                borderRadius: 5,
                cursor: 'pointer',
                fontSize: 12,
                fontWeight: 600,
                whiteSpace: 'nowrap',
            }}
        >
            {label}
        </button>
    )
}

// ─── Main Component ───────────────────────────────────────────────────────────

type Tab = 'deliverers' | 'companies' | 'settings' | 'rates'

const TABS: { id: Tab; label: string }[] = [
    { id: 'deliverers', label: 'Entregadores' },
    { id: 'companies', label: 'Empresas' },
    { id: 'settings', label: 'Configurações' },
    { id: 'rates', label: 'Taxas por Empresa' },
]

export default function AdminDashboard() {
    const [activeTab, setActiveTab] = useState<Tab>('deliverers')
    const { logout } = useAuth()
    const navigate = useNavigate()

    function handleLogout() {
        logout()
        navigate('/login')
    }

    return (
        <div style={{ minHeight: '100vh', background: '#f9fafb', fontFamily: 'sans-serif' }}>
            {/* Header */}
            <header style={{ background: '#6366f1', color: '#fff', padding: '14px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Painel Super Admin</h1>
                <button
                    onClick={handleLogout}
                    style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: '#fff', padding: '6px 16px', borderRadius: 6, cursor: 'pointer', fontWeight: 600 }}
                >
                    Sair
                </button>
            </header>

            {/* Tabs */}
            <div style={{ background: '#fff', borderBottom: '1px solid #e5e7eb', padding: '0 24px', display: 'flex', gap: 0 }}>
                {TABS.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        style={{
                            padding: '14px 20px',
                            border: 'none',
                            background: 'none',
                            cursor: 'pointer',
                            fontWeight: 600,
                            fontSize: 14,
                            color: activeTab === tab.id ? '#6366f1' : '#6b7280',
                            borderBottom: activeTab === tab.id ? '2px solid #6366f1' : '2px solid transparent',
                        }}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Content */}
            <main style={{ padding: 24 }}>
                {activeTab === 'deliverers' && <DeliverersTab />}
                {activeTab === 'companies' && <CompaniesTab />}
                {activeTab === 'settings' && <SettingsTab />}
                {activeTab === 'rates' && <RatesTab />}
            </main>
        </div>
    )
}
