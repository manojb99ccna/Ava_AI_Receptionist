import { useEffect, useRef, useState } from 'react'
import { CHAT_API_URL } from '../config.js'

const WELCOME = { from: 'ava', text: 'Hi, I am Ava. How can I help you today?' }

export default function Chatbox() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open, sending])

  async function handleSend(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return
    setInput('')
    setMessages((prev) => [...prev, { from: 'user', text }])
    setSending(true)

    try {
      const res = await fetch(CHAT_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      })
      if (!res.ok) throw new Error(`Request failed: ${res.status}`)
      const data = await res.json()
      setMessages((prev) => [...prev, { from: 'ava', text: data.reply }])
    } catch {
      setMessages((prev) => [...prev, { from: 'ava', text: 'Sorry, I could not reach the server. Please try again.' }])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="position-fixed bottom-0 end-0 p-3" style={{ zIndex: 1050 }}>
      {open && (
        <div
          className="card border-0 shadow d-flex flex-column mb-3"
          style={{ width: 'min(360px, calc(100vw - 32px))', height: 'min(480px, calc(100vh - 120px))' }}
        >
          <div className="card-header bg-primary text-white d-flex align-items-center">
            <i className="bi bi-robot fs-4 me-2"></i>
            <div className="flex-grow-1">
              <div className="fw-semibold">Ava</div>
              <small className="text-white-50">AI Receptionist</small>
            </div>
            <button type="button" className="btn-close btn-close-white" onClick={() => setOpen(false)}></button>
          </div>

          <div className="card-body overflow-auto flex-grow-1 bg-light">
            {messages.map((m, i) => (
              <div key={i} className={`d-flex mb-3 ${m.from === 'user' ? 'justify-content-end' : ''}`}>
                <div
                  className={`px-3 py-2 rounded-3 small ${m.from === 'user' ? 'bg-primary text-white' : 'bg-white border'}`}
                  style={{ maxWidth: '80%' }}
                >
                  {m.text}
                </div>
              </div>
            ))}
            {sending && (
              <div className="d-flex mb-3">
                <div className="px-3 py-2 rounded-3 small bg-white border text-muted">Ava is typing...</div>
              </div>
            )}
            <div ref={endRef}></div>
          </div>

          <div className="card-footer bg-white">
            <form className="input-group" onSubmit={handleSend}>
              <input
                className="form-control"
                placeholder="Type a message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                autoFocus
              />
              <button className="btn btn-primary" type="submit" disabled={sending || !input.trim()}>
                <i className="bi bi-send"></i>
              </button>
            </form>
          </div>
        </div>
      )}

      <div className="text-end">
        <button
          type="button"
          className="btn btn-primary rounded-circle shadow"
          style={{ width: 60, height: 60 }}
          onClick={() => setOpen(!open)}
        >
          <i className={`bi ${open ? 'bi-x-lg' : 'bi-chat-dots-fill'} fs-4`}></i>
        </button>
      </div>
    </div>
  )
}
