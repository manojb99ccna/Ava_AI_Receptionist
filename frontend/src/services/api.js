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

// --- ADMIN LEADS API ---
export const getLeads = () => request('/admin/leads')

// --- ADMIN FAQS API ---
export const getFaqs = () => request('/admin/faqs')
export const createFaq = (faqData) => request('/admin/faqs', { method: 'POST', body: JSON.stringify(faqData) })
export const updateFaq = (id, faqData) => request(`/admin/faqs/${id}`, { method: 'PUT', body: JSON.stringify(faqData) })
export const deleteFaq = (id) => request(`/admin/faqs/${id}`, { method: 'DELETE' })

// --- ADMIN CONVERSATIONS API ---
export const getConversations = () => request('/admin/conversations')
export const getConversationMessages = (id) => request(`/admin/conversations/${id}/messages`)