import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/',
  server: {
    host: '0.0.0.0',
    port: 3001,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'jzchardware.cn',
      '.jzchardware.cn',
      '192.168.5.49'
    ]
  },
  preview: {
    host: '0.0.0.0',
    port: 3001,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'jzchardware.cn',
      '.jzchardware.cn',
      '192.168.5.49'
    ]
  },
})
