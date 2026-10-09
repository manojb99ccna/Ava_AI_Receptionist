const TOKEN_KEY = 'ava_admin_token'
const ADMIN_KEY = 'ava_admin'

export const getToken = () => localStorage.getItem(TOKEN_KEY)

export const getAdmin = () => JSON.parse(localStorage.getItem(ADMIN_KEY) || 'null')

export function saveSession(token, admin) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(ADMIN_KEY, JSON.stringify(admin))
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(ADMIN_KEY)
}
