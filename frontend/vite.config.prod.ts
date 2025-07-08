import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'
import compression from 'vite-plugin-compression'

// Production configuration with CDN optimization
export default defineConfig({
  plugins: [
    react(),
    // Gzip compression
    compression({
      algorithm: 'gzip',
      ext: '.gz',
    }),
    // Brotli compression
    compression({
      algorithm: 'brotliCompress',
      ext: '.br',
    }),
    // Bundle analyzer (optional)
    process.env.ANALYZE && visualizer({
      open: true,
      filename: 'dist/bundle-analysis.html',
    })
  ].filter(Boolean),
  
  // Use CDN URL in production
  base: process.env.CDN_URL || '/',
  
  build: {
    // Output directory
    outDir: 'dist',
    
    // Generate source maps for error tracking
    sourcemap: true,
    
    // Minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    
    // Chunk size warnings
    chunkSizeWarningLimit: 1000,
    
    // Rollup options
    rollupOptions: {
      output: {
        // Consistent file naming for better caching
        entryFileNames: 'assets/js/[name].[hash].js',
        chunkFileNames: 'assets/js/[name].[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          const ext = info[info.length - 1]
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `assets/images/[name].[hash][extname]`
          } else if (/woff|woff2|eot|ttf|otf/i.test(ext)) {
            return `assets/fonts/[name].[hash][extname]`
          } else if (/css/i.test(ext)) {
            return `assets/css/[name].[hash][extname]`
          }
          return `assets/[name].[hash][extname]`
        },
        
        // Manual chunks for better caching
        manualChunks: {
          // Vendor chunks
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@headlessui/react', 'lucide-react'],
          'utils-vendor': ['axios', 'date-fns', 'clsx'],
          'i18n-vendor': ['i18next', 'react-i18next', 'i18next-browser-languagedetector'],
          
          // Application chunks
          'auth': [
            './src/components/Auth/LoginForm.tsx',
            './src/components/Auth/RegisterForm.tsx',
            './src/components/Auth/TwoFactorSetup.tsx',
            './src/store/authStore.ts'
          ],
          'dashboard': [
            './src/pages/Dashboard.tsx',
            './src/components/Dashboard/StatsCard.tsx',
            './src/components/Analytics/AnalyticsDashboard.tsx'
          ],
          'payment': [
            './src/components/Payment/CheckoutForm.tsx',
            './src/components/Payment/BillingDashboard.tsx',
            './src/services/paymentService.ts'
          ]
        }
      },
      
      // External dependencies (if using CDN for libraries)
      external: [],
    },
    
    // CSS code splitting
    cssCodeSplit: true,
    
    // Asset inlining threshold (4kb)
    assetsInlineLimit: 4096,
    
    // Target modern browsers
    target: 'es2020',
    
    // Report compressed size
    reportCompressedSize: true,
  },
  
  // Optimization
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'axios',
      'i18next',
      'react-i18next'
    ],
  },
  
  // Server options for preview
  preview: {
    port: 4173,
    strictPort: true,
    host: true,
  },
  
  // Define global constants
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    __BUILD_DATE__: JSON.stringify(new Date().toISOString()),
    __COMMIT_HASH__: JSON.stringify(process.env.GITHUB_SHA || 'development'),
  },
})