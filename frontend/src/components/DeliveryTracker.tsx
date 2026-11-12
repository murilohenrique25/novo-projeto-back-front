import { useEffect, useRef, useState } from 'react'

interface LocationData {
    lat: number
    lng: number
    timestamp: string
}

interface DeliveryTrackerProps {
    companyId: string
    deliveryId: string
    token: string
    onStatusChange?: (status: string) => void
}

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected'

const connectionColors: Record<ConnectionStatus, string> = {
    connecting: '#fef08a',
    connected: '#bbf7d0',
    disconnected: '#fecaca',
}

const connectionLabels: Record<ConnectionStatus, string> = {
    connecting: 'Conectando...',
    connected: 'Conectado',
    disconnected: 'Desconectado',
}

const statusStyle: Record<string, React.CSSProperties> = {
    accepted: { backgroundColor: '#bfdbfe', color: '#1e40af' },
    picked_up: { backgroundColor: '#fed7aa', color: '#9a3412' },
    completed: { backgroundColor: '#bbf7d0', color: '#166534' },
    cancelled: { backgroundColor: '#fecaca', color: '#991b1b' },
}

export default function DeliveryTracker({ companyId, deliveryId, token, onStatusChange }: DeliveryTrackerProps) {
    const [location, setLocation] = useState<LocationData | null>(null)
    const [deliveryStatus, setDeliveryStatus] = useState<string | null>(null)
    const [connStatus, setConnStatus] = useState<ConnectionStatus>('connecting')
    const wsRef = useRef<WebSocket | null>(null)

    useEffect(() => {
        const url = `ws://localhost:8000/ws/company/${companyId}/delivery/${deliveryId}?token=${token}`
        const ws = new WebSocket(url)
        wsRef.current = ws

        ws.onopen = () => setConnStatus('connected')

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                if (data.type === 'location_update') {
                    setLocation({ lat: data.lat, lng: data.lng, timestamp: data.timestamp })
                } else if (data.type === 'delivery_status') {
                    setDeliveryStatus(data.status)
                    onStatusChange?.(data.status)
                }
            } catch {
                // ignore malformed messages
            }
        }

        ws.onclose = () => setConnStatus('disconnected')
        ws.onerror = () => setConnStatus('disconnected')

        return () => {
            ws.close()
        }
    }, [companyId, deliveryId, token])

    const badgeStyle: React.CSSProperties = {
        padding: '2px 10px',
        borderRadius: '9999px',
        fontSize: '0.75rem',
        fontWeight: 600,
        display: 'inline-block',
        ...(deliveryStatus ? (statusStyle[deliveryStatus] ?? {}) : {}),
    }

    const connBadgeStyle: React.CSSProperties = {
        padding: '2px 10px',
        borderRadius: '9999px',
        fontSize: '0.75rem',
        fontWeight: 600,
        display: 'inline-block',
        backgroundColor: connectionColors[connStatus],
        color: '#374151',
    }

    return (
        <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, background: '#f9fafb', marginTop: 8 }}>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12, flexWrap: 'wrap' }}>
                <span style={connBadgeStyle}>{connectionLabels[connStatus]}</span>
                {deliveryStatus && (
                    <span style={badgeStyle}>{deliveryStatus}</span>
                )}
            </div>

            {location ? (
                <div style={{ fontSize: '0.875rem', color: '#374151' }}>
                    <p style={{ margin: '0 0 4px' }}>
                        <strong>Localização:</strong>{' '}
                        <a
                            href={`https://maps.google.com/?q=${location.lat},${location.lng}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: '#2563eb' }}
                        >
                            {location.lat.toFixed(6)}, {location.lng.toFixed(6)}
                        </a>
                    </p>
                    <p style={{ margin: 0, color: '#6b7280', fontSize: '0.75rem' }}>
                        Atualizado em: {new Date(location.timestamp).toLocaleString('pt-BR')}
                    </p>
                </div>
            ) : (
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#6b7280' }}>
                    Aguardando localização do entregador...
                </p>
            )}
        </div>
    )
}
