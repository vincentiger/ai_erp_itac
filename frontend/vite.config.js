// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  base: '/ai/', // 部署在 https://127.0.0.1:81/ai/
  build: {
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '127.0.0.1',
    port: 5174,
    strictPort: true,
    proxy: {
      '/ai/api': {
        target: 'http://127.0.0.1:8080', // 確保後端 API 端口是 8080
        changeOrigin: true,
        secure: false,
      },
      '/ai/socket.io': {
        target: 'http://127.0.0.1:8080', // WebSocket 代理
        ws: true,
        changeOrigin: true,
        secure: false,
      },
    },
  },
})



