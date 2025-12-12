import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/crm/',
  plugins: [react()],
  server: {
    port: 6004,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 6004,
    host: '0.0.0.0',
  },
})
