// App-wide settings. Values come from frontend/.env
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8310'

export const CHAT_API_URL = `${API_URL}/api/chat`
