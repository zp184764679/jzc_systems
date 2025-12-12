import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/scm/',
  plugins: [react()],
  server: {
    port: 7000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8005',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 7000,
    host: '0.0.0.0',
  },
})
