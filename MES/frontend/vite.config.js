import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/mes/',
  plugins: [react()],
  server: {
    port: 7800,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8007',
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
    port: 7800,
    host: '0.0.0.0',
  }
})
