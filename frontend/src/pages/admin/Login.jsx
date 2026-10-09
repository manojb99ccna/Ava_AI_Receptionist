import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { adminLogin } from '../../services/api.js'
import { getToken, saveSession } from '../../services/auth.js'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (getToken()) return <Navigate to="/admin" replace />

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { token, admin } = await adminLogin(username, password)
      saveSession(token, admin)
      navigate('/admin')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-vh-100 d-flex align-items-center justify-content-center bg-light px-3">
      <div className="card shadow-sm border-0 w-100" style={{ maxWidth: 400 }}>
        <div className="card-body p-4">
          <div className="text-center mb-4">
            <i className="bi bi-headset display-5 text-primary"></i>
            <h4 className="mt-2 mb-0">Admin Login</h4>
          </div>
          {error && <div className="alert alert-danger py-2">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label">Username</label>
              <input className="form-control" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
            </div>
            <div className="mb-4">
              <label className="form-label">Password</label>
              <input type="password" className="form-control" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <button className="btn btn-primary w-100" disabled={loading}>
              {loading && <span className="spinner-border spinner-border-sm me-2"></span>}
              Login
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
