import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/account/',
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 6003,
    allowedHosts: ['jzchardware.cn', 'localhost', '127.0.0.1'],
    proxy: {
      '/api': {
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
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
    port: 6003,
    strictPort: true,
    allowedHosts: ['jzchardware.cn', 'localhost', '127.0.0.1']
  }
})
