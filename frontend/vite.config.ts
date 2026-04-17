import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return
          }
          if (id.includes('react') || id.includes('react-router-dom')) {
            return 'react'
          }
          if (id.includes('recharts')) {
            return 'charts'
          }
          if (id.includes('@tanstack/react-query')) {
            return 'query'
          }
          if (id.includes('react-hook-form') || id.includes('@hookform/resolvers') || id.includes('/zod/')) {
            return 'forms'
          }
          return 'vendor'
        },
      },
    },
  },
})
