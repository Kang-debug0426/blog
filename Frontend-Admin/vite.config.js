import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
// import vueDevTools from 'vite-plugin-vue-devtools'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import Icons from 'unplugin-icons/vite'
import IconsResolver from 'unplugin-icons/resolver'

// https://vite.dev/config/
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5922',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  plugins: [
    vue(),
    // vueDevTools(),
    // Element Plus 自动导入
    AutoImport({
      resolvers: [
        ElementPlusResolver(),
        IconsResolver({
          prefix: 'Icon',
          enabledCollections: ['ep']
        })
      ]
    }),
    // 组件自动导入
    Components({
      resolvers: [
        ElementPlusResolver(),
        IconsResolver({
          enabledCollections: ['ep']
        })
      ]
    }),
    // 图标
    Icons({
      autoInstall: true,
      compiler: 'vue3'
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // 移除 console
        drop_debugger: true, // 移除 debugger
        pure_funcs: ['console.log']
      },
      format: {
        comments: false // 移除注释
      }
    },
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Vite 内部模块（含 __vitePreload 预加载助手）统一并入 vendor：
          // 该助手被入口静态引用，若落进 md-editor 这类懒加载分包，入口就会被迫预加载整个编辑器
          if (id.includes('node_modules/vite') || id.includes('\0vite') || id.includes('preload-helper')) {
            return 'vendor'
          }
          if (id.includes('node_modules')) {
            if (id.includes('element-plus')) {
              return 'element'
            }
            if (id.includes('echarts') || id.includes('zrender')) {
              return 'echarts'
            }
            if (
              id.includes('md-editor-v3') ||
              id.includes('@codemirror') ||
              id.includes('codemirror') ||
              id.includes('highlight.js')
            ) {
              return 'md-editor'
            }
            return 'vendor'
          }
        },
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    }
  }
})
