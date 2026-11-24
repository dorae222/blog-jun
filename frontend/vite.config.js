import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

/**
 * 모드별 개발 서버. 운영 빌드(`vite build`, mode=production)는 어느 분기도 타지 않는다.
 *
 * - 기본(`npm run dev`): 예전 그대로 :3000, /api → VITE_PROXY_TARGET 또는 localhost:8000
 *   예: VITE_PROXY_TARGET=https://blog.dorae222.com npm run dev
 * - workspace(`npm run dev:workspace`): 127.0.0.1:5180, /api·/media → 로컬 blog-api(127.0.0.1:18000)
 * - mock(`npm run dev:mock`): 127.0.0.1:5180, 백엔드 없이 dev/mock-api.js 가 /api를 대신 받는다
 * 로컬 전용 모드는 127.0.0.1에만 붙는다(외부 노출 금지).
 */
export default defineConfig(async ({ mode }) => {
  const local = mode === 'workspace' || mode === 'mock'
  const API_TARGET = process.env.VITE_PROXY_TARGET
    || (mode === 'workspace' ? 'http://127.0.0.1:18000' : 'http://localhost:8000')

  const plugins = [react(), tailwindcss()]
  if (mode === 'mock') {
    const { default: mockApi } = await import('./dev/mock-api.js')
    plugins.push(mockApi())
  }

  const proxy = {
    '/api': { target: API_TARGET, changeOrigin: true },
    '/media': { target: API_TARGET, changeOrigin: true },
  }

  return {
    plugins,
    server: local
      ? { host: '127.0.0.1', port: 5180, strictPort: true, proxy: mode === 'mock' ? undefined : proxy }
      : { port: 3000, proxy },
  }
})
