export function connect(
    url: string,
    token: string,
    onMessage: (msg: unknown) => void,
): WebSocket {
    const ws = new WebSocket(`${url}?token=${token}`)

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data)
            onMessage(data)
        } catch {
            onMessage(event.data)
        }
    }

    return ws
}
