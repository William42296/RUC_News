import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { VantResolver } from '@vant/auto-import-resolver'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      vue(),
      // Vant 4 按需引入：模板中直接使用 <van-xxx>，无需手动 import
      Components({
        resolvers: [VantResolver()]
      })
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        // 开发环境跨域代理：/api 前缀 → 后端真实地址
        // 后端 Flask 路由不带 /api 前缀（如 /latest），此处剥离前缀
        '/api': {
          target: env.VITE_APP_API_TARGET || 'http://localhost:5000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    },
    build: {
      chunkSizeWarningLimit: 1500,
      rollupOptions: {
        output: {
          // 代码分割
          manualChunks: {
            'vue-vendor': ['vue', 'vue-router', 'pinia'],
            'vant': ['vant'],
            'utils': ['axios', 'dayjs', 'lodash-es']
          }
        }
      }
    }
  }
})
