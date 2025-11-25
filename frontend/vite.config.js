import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // 프론트에서 /backend 로 부르면 8081로 프록시 !!!!!!!!
      '/backend': {
        target: 'http://localhost:8081',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/backend/, ''),
      },
      '/uploads': {
        target: 'http://localhost:8081',
        changeOrigin: true,
      },
      // FastAPI 프록시 추가 (포트 8001)
      '/fastapi': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/fastapi/, ''),
      }
    },
  },
})
