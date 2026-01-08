import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import basicSsl from '@vitejs/plugin-basic-ssl'

const backend_client = 'http://127.0.0.1:8001'
export default defineConfig({
  plugins: [vue(), basicSsl()],
  define: {
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false,
    __VUE_OPTIONS_API__: true,
    __VUE_PROD_DEVTOOLS__: false,
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    https: true,
    proxy: {
      '/api': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/auth': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/dashboard': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/users': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/models': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/chat': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/contacts': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/web': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/roles': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/role-prompts': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/logs': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/diaries': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/albums': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/photos': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/skills': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/config': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/user': {
        target: backend_client,
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8001',
        ws: true,
        changeOrigin: true,
      },
    }
  },
  build: {
    // 代码分割优化
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue'],
        }
      }
    },
    // 压缩优化
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    // 减小chunk大小
    chunkSizeWarningLimit: 500
  },
  // 优化依赖预构建
  optimizeDeps: {
    include: ['vue']
  }
})
