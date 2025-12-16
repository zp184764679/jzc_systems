import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/shm/',
  plugins: [react()],
  server: {
    port: 7500,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
      '/portal-api': {
        target: 'http://localhost:3002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/portal-api/, '/api')
      }
    }
  },
  preview: {
    port: 7500,
    host: '0.0.0.0',
  }
})
