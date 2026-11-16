
import { useEffect, useRef, useState } from 'react'
import { CHAT_API_URL } from '../config.js'

const WELCOME = {
  from: 'ava',
  text: 'Hi, I am Ava. How can I help you today?',
}

export default function Chatbox() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [sessionId, setSessionId] = useState(null)

  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open, sending])

  // -------------------------------------------------------
  // COMMON API REQUEST
  // -------------------------------------------------------

  async function sendChatRequest(payload, userDisplayText = null) {
    if (sending) return

    if (userDisplayText) {
      setMessages((prev) => [
        ...prev,
        { from: 'user', text: userDisplayText },
      ])
    }

    setSending(true)

    try {
      const res = await fetch(CHAT_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...payload,
          ...(sessionId && { session_id: sessionId }),
        }),
      })

      if (!res.ok) {
        throw new Error(`Request failed: ${res.status}`)
      }

      const data = await res.json()

      if (data.session_id) {
        setSessionId(data.session_id)
      }

      setMessages((prev) => [
        ...prev,
        {
          from: 'ava',
          text: data.reply,
          ui_action: data.ui_action || null,
          data: data.data || null,
        },
      ])
    } catch (error) {
      console.error('Chat error:', error)

      setMessages((prev) => [
        ...prev,
        {
          from: 'ava',
          text: 'Sorry, I could not reach the server. Please try again.',
        },
      ])
    } finally {
      setSending(false)
    }
  }

  // -------------------------------------------------------
  // NORMAL MESSAGE
  // -------------------------------------------------------

  async function handleSend(e) {
    e.preventDefault()

    const text = input.trim()

    if (!text || sending) return

    setInput('')

    await sendChatRequest(
      { message: text },
      text
    )
  }

  // -------------------------------------------------------
  // DATE SELECTION
  // -------------------------------------------------------

  async function handleDateSelect(selectedDate) {
    if (sending) return

    const formattedDate = new Date(
      `${selectedDate}T00:00:00`
    ).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })

    await sendChatRequest(
      {
        message: '',
        action: 'select_date',
        selected_date: selectedDate,
      },
      formattedDate
    )
  }

  // -------------------------------------------------------
  // TIME SELECTION
  // -------------------------------------------------------

  async function handleTimeSelect(selectedDate, selectedTime, label) {
    if (sending) return

    await sendChatRequest(
      {
        message: '',
        action: 'select_time',
        selected_date: selectedDate,
        selected_time: selectedTime,
      },
      label
    )
  }

  // -------------------------------------------------------
  // RENDER
  // -------------------------------------------------------

  return (
    <div
      className="position-fixed bottom-0 end-0 p-3"
      style={{ zIndex: 1050 }}
    >
      {open && (
        <div
          className="card border-0 shadow d-flex flex-column mb-3"
          style={{
            width: 'min(360px, calc(100vw - 32px))',
            height: 'min(560px, calc(100vh - 120px))',
          }}
        >
          {/* HEADER */}

          <div className="card-header bg-primary text-white d-flex align-items-center">
            <i className="bi bi-robot fs-4 me-2"></i>

            <div className="flex-grow-1">
              <div className="fw-semibold">Ava</div>
              <small className="text-white-50">
                AI Receptionist
              </small>
            </div>

            <button
              type="button"
              className="btn-close btn-close-white"
              onClick={() => setOpen(false)}
            ></button>
          </div>

          {/* CHAT MESSAGES */}

          <div className="card-body overflow-auto flex-grow-1 bg-light">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`d-flex flex-column mb-3 ${
                  m.from === 'user'
                    ? 'align-items-end'
                    : 'align-items-start'
                }`}
              >
                {/* MESSAGE */}

                <div
                  className={`px-3 py-2 rounded-3 small ${
                    m.from === 'user'
                      ? 'bg-primary text-white'
                      : 'bg-white border'
                  }`}
                  style={{
                    maxWidth: '85%',
                    whiteSpace: 'pre-line',
                  }}
                >
                  {m.text}
                </div>

                {/* DATE BUTTONS */}

                {m.from === 'ava' &&
                  m.ui_action === 'select_date' &&
                  m.data?.dates && (
                    <div className="mt-2 w-100">
                      <div className="small fw-semibold mb-2">
                        Select a date
                      </div>

                      <div className="d-flex flex-wrap gap-2">
                        {m.data.dates.map((item) => (
                          <button
                            key={item.date}
                            type="button"
                            disabled={sending || item.disabled}
                            onClick={() =>
                              handleDateSelect(item.date)
                            }
                            className={`btn btn-sm ${
                              item.disabled
                                ? 'btn-outline-secondary'
                                : 'btn-outline-primary'
                            }`}
                            style={{
                              minWidth: '95px',
                              opacity: item.disabled ? 0.5 : 1,
                            }}
                          >
                            <div className="fw-semibold">
                              {item.label}
                            </div>

                            <small>
                              {item.is_open
                                ? item.day
                                : 'Closed'}
                            </small>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                {/* TIME BUTTONS */}

                {m.from === 'ava' &&
                  m.ui_action === 'select_time' &&
                  m.data?.slots && (
                    <div className="mt-2 w-100">
                      <div className="small fw-semibold mb-2">
                        Available times
                      </div>

                      <div className="d-flex flex-wrap gap-2">
                        {m.data.slots.map((slot) => (
                          <button
                            key={slot.time}
                            type="button"
                            disabled={
                              sending ||
                              slot.disabled ||
                              !slot.available
                            }
                            onClick={() =>
                              handleTimeSelect(
                                m.data.date,
                                slot.time,
                                slot.label
                              )
                            }
                            className={`btn btn-sm ${
                              slot.available
                                ? 'btn-outline-primary'
                                : 'btn-outline-secondary'
                            }`}
                            style={{
                              minWidth: '90px',
                              opacity: slot.available ? 1 : 0.5,
                            }}
                          >
                            {slot.label}
                            {!slot.available && (
                              <span className="d-block">
                                <small>Booked</small>
                              </span>
                            )}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
              </div>
            ))}

            {/* TYPING INDICATOR */}

            {sending && (
              <div className="d-flex mb-3">
                <div className="px-3 py-2 rounded-3 small bg-white border text-muted">
                  Ava is typing...
                </div>
              </div>
            )}

            <div ref={endRef}></div>
          </div>

          {/* INPUT */}

          <div className="card-footer bg-white">
            <form
              className="input-group"
              onSubmit={handleSend}
            >
              <input
                className="form-control"
                placeholder="Type a message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={sending}
                autoFocus
              />

              <button
                className="btn btn-primary"
                type="submit"
                disabled={sending || !input.trim()}
              >
                <i className="bi bi-send"></i>
              </button>
            </form>
          </div>
        </div>
      )}

      {/* CHAT TOGGLE */}

      <div className="text-end">
        <button
          type="button"
          className="btn btn-primary rounded-circle shadow"
          style={{
            width: 60,
            height: 60,
          }}
          onClick={() => setOpen(!open)}
        >
          <i
            className={`bi ${
              open ? 'bi-x-lg' : 'bi-chat-dots-fill'
            } fs-4`}
          ></i>
        </button>
      </div>
    </div>
  )
}