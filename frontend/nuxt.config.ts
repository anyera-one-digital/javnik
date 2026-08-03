// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/image',
    '@nuxt/ui',
    '@nuxt/content',
    '@vueuse/nuxt'
  ],

  components: [
    { path: '~/components/yavnik-landing', pathPrefix: false, priority: 10 },
    { path: '~/components/yavnik-landing/ui', pathPrefix: false, priority: 10 },
    '~/components'
  ],

  devtools: {
    enabled: true
  },

  devServer: {
    port: 4000,
    host: '0.0.0.0'
  },

  runtimeConfig: {
    // Приватная конфигурация для сервера (может использовать backend:8000 внутри Docker)
    apiBase: process.env.API_BASE_URL || 'http://localhost:8000',
    // Публичная конфигурация для клиента (браузер)
    // Для production: пустая строка (относительные пути)
    // Для development: http://localhost:8000
    public: {
      // Пустая строка = относительные /api/** через nginx (не дублировать /api в base)
      apiBase: process.env.NUXT_PUBLIC_API_BASE_URL ?? ''
    }
  },

  css: ['~/assets/css/main.css'],

  routeRules: {
    '/api/**': {
      cors: true
    },
    // Публичные страницы сайта (без prerender — иначе устаревший HTML ломает гидрацию)
    '/': { ssr: true },
    '/login': { prerender: false },
    '/signup': { prerender: false },
    // Публичный календарь (по username)
    '/booking/**': { ssr: false },
    // Защищенные страницы приложения (требуют авторизации)
    '/schedule': { ssr: false },
    '/dashboard': { ssr: false },
    '/customers': { ssr: false },
    '/services': { ssr: false },
    '/settings': { redirect: '/settings/general' },
    '/settings/**': { ssr: false },
    '/profile': { ssr: false },
    '/payment': { ssr: false },
    '/payment/**': { ssr: false }
  },

  compatibilityDate: '2024-07-11',

  nitro: {
    prerender: {
      routes: [
        '/'
      ],
      crawlLinks: false,
      failOnError: false
    }
  },

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  },

  vite: {
    optimizeDeps: {
      include: ['date-fns', '@unovis/vue', '@unovis/ts', 'vue', 'gsap', 'reka-ui']
    },
    resolve: {
      dedupe: ['vue', '@vue/runtime-core']
    },
    server: {
      watch: {
        // Docker Desktop на macOS часто шлёт ложные fs-events → лишние HMR/рыки UI
        usePolling: false,
        ignored: ['**/node_modules/**', '**/.git/**']
      },
      hmr: {
        // Доступ через nginx :8765 — клиент должен ходить на тот же порт
        clientPort: 8765,
        protocol: 'ws',
        timeout: 120000
      }
    }
  },

  // Отключаем автоматическую загрузку шрифтов из внешних источников
  fonts: {
    providers: {
      fontsource: false,
      fontshare: false
    }
  },

  // Экспериментальные настройки для SSR
  experimental: {
    payloadExtraction: false
  }
})
