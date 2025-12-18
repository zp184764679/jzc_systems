import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/docs/',
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 6200,
    proxy: {
      '/strapi-api': {
        target: 'http://localhost:1337',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/strapi-api/, '/api')
      },
      '/portal-api': {
        target: 'http://localhost:3002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/portal-api/, '/api')
      }
    }
  },
  preview: {
    host: '0.0.0.0',
    port: 6200
  }
})
