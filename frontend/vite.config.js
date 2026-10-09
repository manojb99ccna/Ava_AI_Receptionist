import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Polling is needed for hot reload on Docker Desktop (Windows bind mounts)
    watch: { usePolling: true },
    proxy: {
      '/api': process.env.API_TARGET || 'http://localhost:8000',
    },
  },
})
