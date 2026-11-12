import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import DeliveryTracker from '../components/DeliveryTracker'

interface Delivery {
    id: string
    status: string
    fee: number
    pickup_address: string
    destination_address: string
    created_at: string
}

interface NewDeliveryResponse {
    id: string
    fee: number
    platform_cut: number
    deliverer_cut: number
    status: string
}

const statusStyle: Record<string, React.CSSProperties> = {
    pending: { backgroundColor: '#fef08a', color: '#854d0e' },
    accepted: { backgroundColor: '#bfdbfe', color: '#1e40af' },
    picked_up: { backgroundColor: '#fed7aa', color: '#9a3412' },
    completed: { backgroundColor: '#bbf7d0', color: '#166534' },
    cancelled: { backgroundColor: '#fecaca', color: '#991b1b' },
}

function StatusBadge({ status }: { status: string }) {
    const base: React.CSSProperties = {
        padding: '2px 10px',
        borderRadius: '9999px',
        fontSize: '0.75rem',
        fontWeight: 600,
        display: 'inline-block',
        ...(statusStyle[status] ?? statusStyle['pending']),
    }
    return <span style={base}>{status}</span>
}

const TRACKABLE_STATUSES = ['accepted', 'picked_up']

export default function CompanyDashboard() {
    const { logout, user, token } = useAuth()
    const navigate = useNavigate()

    const [trackedDeliveryId, setTrackedDeliveryId] = useState<string | null>(null)

    // Balance
    const [balance, setBalance] = useState<number | null>(null)
    const [balanceLoading, setBalanceLoading] = useState(true)
    const [balanceError, setBalanceError] = useState('')

    // PIX top-up
    const [pixAmount, setPixAmount] = useState('')
    const [pixQr, setPixQr] = useState('')
    const [pixLoading, setPixLoading] = useState(false)
    const [pixError, setPixError] = useState('')

    // Card top-up
    const [cardAmount, setCardAmount] = useState('')
    const [cardToken, setCardToken] = useState('')
    const [cardLoading, setCardLoading] = useState(false)
    const [cardError, setCardError] = useState('')
    const [cardSuccess, setCardSuccess] = useState('')

    // New delivery form
    const [form, setForm] = useState({
        pickup_address: '',
        pickup_lat: '',
        pickup_lng: '',
        destination_address: '',
        destination_lat: '',
        destination_lng: '',
        city_id: '',
    })
    const [deliveryResult, setDeliveryResult] = useState<NewDeliveryResponse | null>(null)
    const [deliveryLoading, setDeliveryLoading] = useState(false)
    const [deliveryError, setDeliveryError] = useState('')

    // Delivery list
    const [deliveries, setDeliveries] = useState<Delivery[]>([])
    const [listLoading, setListLoading] = useState(true)
    const [listError, setListError] = useState('')

    async function fetchBalance() {
        setBalanceLoading(true)
        setBalanceError('')
        try {
            const res = await api.get('/api/v1/company/balance')
            setBalance(res.data.balance ?? res.data)
        } catch {
            setBalanceError('Erro ao carregar saldo.')
        } finally {
            setBalanceLoading(false)
        }
    }

    async function fetchDeliveries() {
        setListLoading(true)
        setListError('')
        try {
            const res = await api.get('/api/v1/company/deliveries')
            setDeliveries(res.data)
        } catch {
            setListError('Erro ao carregar entregas.')
        } finally {
            setListLoading(false)
        }
    }

    useEffect(() => {
        fetchBalance()
        fetchDeliveries()
    }, [])

    async function handlePixTopup(e: React.FormEvent) {
        e.preventDefault()
        setPixLoading(true)
        setPixError('')
        setPixQr('')
        try {
            const res = await api.post('/api/v1/company/balance/topup/pix', { amount: parseFloat(pixAmount) })
            setPixQr(res.data.qr_code ?? res.data.qr_code_string ?? JSON.stringify(res.data))
            setPixAmount('')
            fetchBalance()
        } catch (err: any) {
            setPixError(err.response?.data?.detail ?? 'Erro ao gerar PIX.')
        } finally {
            setPixLoading(false)
        }
    }

    async function handleCardTopup(e: React.FormEvent) {
        e.preventDefault()
        setCardLoading(true)
        setCardError('')
        setCardSuccess('')
        try {
            await api.post('/api/v1/company/balance/topup/card', {
                amount: parseFloat(cardAmount),
                card_token: cardToken,
            })
            setCardSuccess('Recarga via cartão realizada com sucesso!')
            setCardAmount('')
            setCardToken('')
            fetchBalance()
        } catch (err: any) {
            setCardError(err.response?.data?.detail ?? 'Erro ao processar cartão.')
        } finally {
            setCardLoading(false)
        }
    }

    function handleFormChange(e: React.ChangeEvent<HTMLInputElement>) {
        setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
    }

    async function handleNewDelivery(e: React.FormEvent) {
        e.preventDefault()
        setDeliveryLoading(true)
        setDeliveryError('')
        setDeliveryResult(null)
        try {
            const payload = {
                pickup_address: form.pickup_address,
                pickup_lat: parseFloat(form.pickup_lat),
                pickup_lng: parseFloat(form.pickup_lng),
                destination_address: form.destination_address,
                destination_lat: parseFloat(form.destination_lat),
                destination_lng: parseFloat(form.destination_lng),
                city_id: form.city_id,
            }
            const res = await api.post('/api/v1/company/deliveries', payload)
            setDeliveryResult(res.data)
            setForm({ pickup_address: '', pickup_lat: '', pickup_lng: '', destination_address: '', destination_lat: '', destination_lng: '', city_id: '' })
            fetchDeliveries()
            fetchBalance()
        } catch (err: any) {
            setDeliveryError(err.response?.data?.detail ?? 'Erro ao criar entrega.')
        } finally {
            setDeliveryLoading(false)
        }
    }

    function handleLogout() {
        logout()
        navigate('/login')
    }

    return (
        <div style={{ maxWidth: 960, margin: '0 auto', padding: '24px 16px', fontFamily: 'sans-serif' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
                <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Painel da Empresa</h1>
                <button onClick={handleLogout} style={{ padding: '8px 16px', cursor: 'pointer', borderRadius: 6, border: '1px solid #d1d5db', background: '#f9fafb' }}>
                    Sair
                </button>
            </div>

            {/* Balance Section */}
            <section style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 8, padding: 20, marginBottom: 24 }}>
                <h2 style={{ margin: '0 0 12px', fontSize: '1.1rem' }}>Saldo</h2>
                {balanceLoading && <p style={{ color: '#6b7280' }}>Carregando saldo...</p>}
                {balanceError && <p style={{ color: '#dc2626' }}>{balanceError}</p>}
                {balance !== null && !balanceLoading && (
                    <p style={{ fontSize: '1.75rem', fontWeight: 700, color: '#166534', margin: 0 }}>
                        R$ {balance.toFixed(2)}
                    </p>
                )}
            </section>

            {/* Top-up Forms */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
                {/* PIX */}
                <section style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 20 }}>
                    <h3 style={{ margin: '0 0 12px', fontSize: '1rem' }}>Recarga via PIX</h3>
                    <form onSubmit={handlePixTopup}>
                        <div style={{ marginBottom: 10 }}>
                            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: 4 }}>Valor (R$)</label>
                            <input
                                type="number"
                                min="0.01"
                                step="0.01"
                                bmit" disabled={pixLoading} style={{ padding: '8px 16px', borderRadius: 6, background: '#16a34a', color: '#fff', border: 'none', cursor: 'pointer', width: '100%' }}>
                            {pixLoading ? 'Gerando...' : 'Gerar QR Code PIX'}
                        </button>
                    </form>
                    {pixQr && (
                        <div style={{ marginTop: 12, background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 6, padding: 12 }}>
                            <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 6px' }}>QR Code PIX:</p>
                            <code style={{ wordBreak: 'break-all', fontSize: '0.75rem' }}>{pixQr}</code>
                        </div>
                    )}
                </section>

                {/* Card */}
                <section style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 20 }}>
                    <h3 style={{ margin: '0 0 12px', fontSize: '1rem' }}>Recarga via Cartão</h3>
                    <form onSubmit={handleCardTopup}>
                        <div style={{ marginBottom: 10 }}>
                            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: 4 }}>Valor (R$)</label>
                            <input
                                type="number"
                                min="0.01"
                                step="0.01"
                                value={cardAmount}
                                onChange={e => setCardAmount(e.target.value)}
                                required
                                style={{ width: '100%', padding: '8px', borderRadius: 6, border: '1px solid #d1d5db', boxSizing: 'border-box' }}
                            />
                        </div>
                        <div style={{ marginBottom: 10 }}>
                            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: 4 }}>Token do Cartão</label>
                            <input
                                type="text"
                                value={cardToken}
                                onChange={e => setCardToken(e.target.value)}
                                required
                                placeholder="tok_..."
                                style={{ width: '100%', padding: '8px', borderRadius: 6, border: '1px solid #d1d5db', boxSizing: 'border-box' }}
                            />
                        </div>
                        {cardError && <p style={{ color: '#dc2626', fontSize: '0.875rem' }}>{cardError}</p>}
                        {cardSuccess && <p style={{ color: '#16a34a', fontSize: '0.875rem' }}>{cardSuccess}</p>}
                        <button type="submit" disabled={cardLoading} style={{ padding: '8px 16px', borderRadius: 6, background: '#2563eb', color: '#fff', border: 'none', cursor: 'pointer', width: '100%' }}>
                            {cardLoading ? 'Processando...' : 'Pagar com Cartão'}
                        </button>
                    </form>
                </section>
            </div>

            {/* New Delivery Form */}
            <section style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 20, marginBottom: 24 }}>
                <h2 style={{ margin: '0 0 16px', fontSize: '1.1rem' }}>Nova Entrega</h2>
                <form onSubmit={handleNewDelivery}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                        {[
                            { name: 'pickup_address', label: 'Endereço de Coleta', type: 'text', colSpan: 2 },
                            { name: 'pickup_lat', label: 'Latitude Coleta', type: 'number' },
                            { name: 'pickup_lng', label: 'Longitude Coleta', type: 'number' },
                            { name: 'destination_address', label: 'Endereço de Destino', type: 'text', colSpan: 2 },
                            { name: 'destination_lat', label: 'Latitude Destino', type: 'number' },
                            { name: 'destination_lng', label: 'Longitude Destino', type: 'number' },
                            { name: 'city_id', label: 'ID da Cidade (UUID)', type: 'text', colSpan: 2 },
                        ].map(field => (
                            <div key={field.name} style={{ gridColumn: field.colSpan === 2 ? 'span 2' : undefined }}>
                                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: 4 }}>{field.label}</label>
                                <input
                                    type={field.type}
                                    name={field.name}
                                    value={form[field.name as keyof typeof form]}
                                    onChange={handleFormChange}
                                    required
                                    step={field.type === 'number' ? 'any' : undefined}
                                    style={{ width: '100%', padding: '8px', borderRadius: 6, border: '1px solid #d1d5db', boxSizing: 'border-box' }}
                                />
                            </div>
                        ))}
                    </div>
                    {deliveryError && <p style={{ color: '#dc2626', fontSize: '0.875rem', marginTop: 8 }}>{deliveryError}</p>}
                    <button type="submit" disabled={deliveryLoading} style={{ marginTop: 16, padding: '10px 24px', borderRadius: 6, background: '#7c3aed', color: '#fff', border: 'none', cursor: 'pointer' }}>
                        {deliveryLoading ? 'Criando...' : 'Criar Entrega'}
                    </button>
                </form>

                {deliveryResult && (
                    <div style={{ marginTop: 16, background: '#f5f3ff', border: '1px solid #ddd6fe', borderRadius: 6, padding: 12 }}>
                        <p style={{ margin: '0 0 4px', fontWeight: 600, color: '#5b21b6' }}>Entrega criada com sucesso!</p>
                        <p style={{ margin: '2px 0', fontSize: '0.875rem' }}>Taxa total: <strong>R$ {deliveryResult.fee?.toFixed(2)}</strong></p>
                        <p style={{ margin: '2px 0', fontSize: '0.875rem' }}>Plataforma: <strong>R$ {deliveryResult.platform_cut?.toFixed(2)}</strong></p>
                        <p style={{ margin: '2px 0', fontSize: '0.875rem' }}>Entregador: <strong>R$ {deliveryResult.deliverer_cut?.toFixed(2)}</strong></p>
                    </div>
                )}
            </section>

            {/* Delivery List */}
            <section style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 20 }}>
                <h2 style={{ margin: '0 0 16px', fontSize: '1.1rem' }}>Minhas Entregas</h2>
                {listLoading && <p style={{ color: '#6b7280' }}>Carregando entregas...</p>}
                {listError && <p style={{ color: '#dc2626' }}>{listError}</p>}
                {!listLoading && !listError && deliveries.length === 0 && (
                    <p style={{ color: '#6b7280' }}>Nenhuma entrega encontrada.</p>
                )}
                {!listLoading && deliveries.length > 0 && (
                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                            <thead>
                                <tr style={{ borderBottom: '2px solid #e5e7eb', textAlign: 'left' }}>
                                    <th style={{ padding: '8px 12px' }}>ID</th>
                                    <th style={{ padding: '8px 12px' }}>Status</th>
                                    <th style={{ padding: '8px 12px' }}>Taxa</th>
                                    <th style={{ padding: '8px 12px' }}>Coleta</th>
                                    <th style={{ padding: '8px 12px' }}>Destino</th>
                                    <th style={{ padding: '8px 12px' }}>Criado em</th>
                                    <th style={{ padding: '8px 12px' }}>Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                {deliveries.map(d => (
                                    <>
                                        <tr key={d.id} style={{ borderBottom: trackedDeliveryId === d.id ? 'none' : '1px solid #f3f4f6' }}>
                                            <td style={{ padding: '8px 12px', fontFamily: 'monospace', color: '#6b7280' }}>
                                                {d.id.slice(0, 8)}...
                                            </td>
                                            <td style={{ padding: '8px 12px' }}>
                                                <StatusBadge status={d.status} />
                                            </td>
                                            <td style={{ padding: '8px 12px' }}>R$ {d.fee?.toFixed(2)}</td>
                                            <td style={{ padding: '8px 12px', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                {d.pickup_address}
                                            </td>
                                            <td style={{ padding: '8px 12px', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                {d.destination_address}
                                            </td>
                                            <td style={{ padding: '8px 12px', whiteSpace: 'nowrap' }}>
                                                {new Date(d.created_at).toLocaleString('pt-BR')}
                                            </td>
                                            <td style={{ padding: '8px 12px' }}>
                                                {TRACKABLE_STATUSES.includes(d.status) && (
                                                    <button
                                                        onClick={() => setTrackedDeliveryId(trackedDeliveryId === d.id ? null : d.id)}
                                                        style={{
                                                            padding: '4px 12px',
                                                            borderRadius: 6,
                                                            border: '1px solid #2563eb',
                                                            background: trackedDeliveryId === d.id ? '#2563eb' : '#eff6ff',
                                                            color: trackedDeliveryId === d.id ? '#fff' : '#2563eb',
                                                            cursor: 'pointer',
                                                            fontSize: '0.75rem',
                                                            fontWeight: 600,
                                                        }}
                                                    >
                                                        {trackedDeliveryId === d.id ? 'Fechar' : 'Rastrear'}
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                        {trackedDeliveryId === d.id && user && token && (
                                            <tr key={`tracker-${d.id}`} style={{ borderBottom: '1px solid #f3f4f6' }}>
                                                <td colSpan={7} style={{ padding: '0 12px 12px' }}>
                                                    <DeliveryTracker
                                                        companyId={user.id}
                                                        deliveryId={d.id}
                                                        token={token}
                                                        onStatusChange={(status) => {
                                                            setDeliveries(prev =>
                                                                prev.map(item => item.id === d.id ? { ...item, status } : item)
                                                            )
                                                        }}
                                                    />
                                                </td>
                                            </tr>
                                        )}
                                    </>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>
        </div>
    )
}
