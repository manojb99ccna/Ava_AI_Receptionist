import { clearSession, getToken } from './auth.js'

const API_BASE = '/api'

async function request(path, options = {}) {
  const token = getToken()
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    if (res.status === 401 && token) clearSession()
    throw new Error(data.detail || `Request failed: ${res.status}`)
  }
  return data
}

export const getHealth = () => request('/health')

export const adminLogin = (username, password) =>
  request('/admin/login', { method: 'POST', body: JSON.stringify({ username, password }) })

export const getAdminMe = () => request('/admin/me')
