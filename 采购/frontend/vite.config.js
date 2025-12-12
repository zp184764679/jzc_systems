// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/caigou/',
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5000,
    open: false,
    strictPort: false,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '61.145.212.28',
      'jzchardware.cn',
      '.jzchardware.cn', // 包括所有子域名
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false,
        cookieDomainRewrite: 'localhost',
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 5000,
    open: false,
    strictPort: false,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '61.145.212.28',
      'jzchardware.cn',
      '.jzchardware.cn', // 包括所有子域名
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false,
        cookieDomainRewrite: 'localhost',
      },
    },
  },
})
