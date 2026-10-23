import { useState, useEffect } from 'react'
import { getConversations, getConversationMessages } from '../../services/api.js'

export default function Conversations() {
  const [conversations, setConversations] = useState([])
  const [selectedConv, setSelectedConv] = useState(null)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadConversations()
  }, [])

  async function loadConversations() {
    try {
      setLoading(true)
      setError(null)
      const data = await getConversations()
      setConversations(data)
    } catch (err) {
      setError(err.message || 'Failed to load conversations.')
    } finally {
      setLoading(false)
    }
  }

  async function handleSelectConversation(conv) {
    setSelectedConv(conv)
    try {
      setLoadingMessages(true)
      const data = await getConversationMessages(conv.id)
      setMessages(data)
    } catch (err) {
      setMessages([])
    } finally {
      setLoadingMessages(false)
    }
  }

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="fw-bold mb-1">Chat Conversations</h3>
          <p className="text-muted small mb-0">Review past visitor interactions and message logs with Ava.</p>
        </div>
        <button className="btn btn-outline-dark btn-sm" onClick={loadConversations}>
          <i className="bi bi-arrow-clockwise me-1"></i>Refresh
        </button>
      </div>

      {error && (
        <div className="alert alert-danger py-2 small" role="alert">
          <i className="bi bi-exclamation-triangle me-1"></i>{error}
        </div>
      )}

      <div className="row g-4">
        {/* Conversations List */}
        <div className="col-md-5">
          <div className="card border-0 shadow-sm">
            <div className="card-header bg-white py-3">
              <h6 className="mb-0 fw-bold">Recent Sessions</h6>
            </div>
            <div className="card-body p-0" style={{ maxHeight: '600px', overflowY: 'auto' }}>
              {loading ? (
                <div className="text-center py-5">
                  <div className="spinner-border text-primary spinner-border-sm me-2" role="status"></div>
                  <span className="text-muted">Loading sessions...</span>
                </div>
              ) : conversations.length === 0 ? (
                <div className="text-center py-5 text-muted small">No conversation logs found.</div>
              ) : (
                <div className="list-group list-group-flush">
                  {conversations.map((conv) => (
                    <button
                      key={conv.id}
                      onClick={() => handleSelectConversation(conv)}
                      className={`list-group-item list-group-item-action p-3 text-start ${selectedConv?.id === conv.id ? 'active' : ''}`}
                    >
                      <div className="d-flex w-100 justify-content-between align-items-center mb-1">
                        <span className="fw-semibold small text-truncate" style={{ maxWidth: '180px' }}>
                          Session: {conv.session_id.substring(0, 10)}...
                        </span>
                        <span className={`badge ${selectedConv?.id === conv.id ? 'bg-light text-dark' : 'bg-secondary bg-opacity-10 text-secondary'}`}>
                          {conv.intent || 'general'}
                        </span>
                      </div>
                      <p className="mb-1 small text-muted text-truncate">
                        Step: {conv.current_step || 'Completed / None'}
                      </p>
                      <small className={selectedConv?.id === conv.id ? 'text-white-50' : 'text-muted'}>
                        {conv.updated_at ? new Date(conv.updated_at).toLocaleString() : ''}
                      </small>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Message Transcript Panel */}
        <div className="col-md-7">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-header bg-white py-3">
              <h6 className="mb-0 fw-bold">
                {selectedConv ? `Transcript for Session #${selectedConv.id}` : 'Select a Conversation'}
              </h6>
            </div>
            <div className="card-body d-flex flex-column" style={{ height: '540px', overflowY: 'auto', backgroundColor: '#f8f9fa' }}>
              {!selectedConv ? (
                <div className="text-center m-auto text-muted">
                  <i className="bi bi-chat-square-text display-4 mb-2 d-block"></i>
                  Click on a conversation session on the left to view the complete chat history.
                </div>
              ) : loadingMessages ? (
                <div className="text-center m-auto">
                  <div className="spinner-border text-primary spinner-border-sm me-2" role="status"></div>
                  <span className="text-muted">Loading messages...</span>
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center m-auto text-muted small">No messages recorded for this session.</div>
              ) : (
                <div className="d-flex flex-column gap-3">
                  {messages.map((msg) => {
                    const isAva = msg.sender === 'ava'
                    return (
                      <div key={msg.id} className={`d-flex ${isAva ? 'justify-content-start' : 'justify-content-end'}`}>
                        <div 
                          className={`p-3 rounded-3 shadow-sm small ${isAva ? 'bg-white text-dark border' : 'bg-primary text-white'}`}
                          style={{ maxWidth: '75%' }}
                        >
                          <div className="fw-bold mb-1 opacity-75 fs-8">
                            {isAva ? 'Ava AI' : 'Visitor'}
                          </div>
                          <div>{msg.message}</div>
                          <div className={`mt-1 fs-8 text-end ${isAva ? 'text-muted' : 'text-white-50'}`}>
                            {msg.created_at ? new Date(msg.created_at.replace('Z', '')).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}