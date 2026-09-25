import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Backend default from Backend/config.py (HOST=0.0.0.0, PORT=8000).
// Override with BACKEND_ORIGIN when running the API elsewhere.
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ?? 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // The frontend calls /api/... ; the backend serves routes at the root
      // (e.g. /risk/calculate), so the prefix is stripped on the way through.
      '/api': {
        target: BACKEND_ORIGIN,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
