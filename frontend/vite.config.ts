import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  build: {
    rollupOptions: {
      external: [
        /\.test\.(ts|tsx)$/,
        /\/__tests__\//,
        /\/test\//,
        'vitest',
        '@testing-library/react',
        '@testing-library/jest-dom',
        '@testing-library/user-event'
      ]
    },
    sourcemap: false,
    minify: 'terser'
  }
})
