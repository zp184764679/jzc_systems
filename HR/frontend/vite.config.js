import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/hr/',
  plugins: [react()],
  server: {
    port: 6002,
    host: '0.0.0.0',
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '61.145.212.28',
      'jzchardware.cn',
      '.jzchardware.cn',
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      }
    }
  },
  preview: {
    port: 6002,
    host: '0.0.0.0',
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '61.145.212.28',
      'jzchardware.cn',
      '.jzchardware.cn',
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      }
    }
  }
})
