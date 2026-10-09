import { useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { getAdminMe } from '../services/api.js'
import { getToken } from '../services/auth.js'

export default function ProtectedRoute() {
  const [status, setStatus] = useState(getToken() ? 'checking' : 'denied')

  useEffect(() => {
    if (status !== 'checking') return
    getAdminMe()
      .then(() => setStatus('ok'))
      .catch(() => setStatus('denied'))
  }, [status])

  if (status === 'denied') return <Navigate to="/admin/login" replace />
  if (status === 'checking') {
    return (
      <div className="min-vh-100 d-flex align-items-center justify-content-center">
        <div className="spinner-border text-primary"></div>
      </div>
    )
  }
  return <Outlet />
}
