import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  // API_TARGET: where the dev proxy forwards /api/* requests.
  // Set in .env.local (git-ignored) to override without touching committed files.
  const apiTarget = env.API_TARGET || 'http://10.149.204.137:8013'

  return {
    plugins: [react(), tailwindcss()],
    base: '/assets/sowaan_cloud/onboarding/',
    build: {
      outDir: path.resolve(__dirname, '../sowaan_cloud/public/onboarding'),
      emptyOutDir: true,
      manifest: true,
    },
    server: {
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  }
})
