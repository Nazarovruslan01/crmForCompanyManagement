import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiProxy = {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    // Tell Django this request arrived via HTTPS (mimics nginx X-Forwarded-Proto header)
    // so SECURE_SSL_REDIRECT doesn't redirect the dev proxy to HTTPS
    headers: {
      'X-Forwarded-Proto': 'https',
    },
  },
}

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: apiProxy,
  },
  preview: {
    proxy: apiProxy,
  },
})
