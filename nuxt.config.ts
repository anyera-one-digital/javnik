// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/image',
    '@nuxt/ui',
    '@nuxt/content',
    '@vueuse/nuxt',
    'nuxt-og-image'
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
    // Публичная конфигурация для клиента (всегда localhost для браузера)
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
    }
  },

  css: ['~/assets/css/main.css'],

  routeRules: {
    '/api/**': {
      cors: true
    },
    '/docs': { redirect: '/docs/getting-started', prerender: false },
    // Публичные страницы сайта
    '/': { prerender: true },
    '/login': { prerender: false },
    '/signup': { prerender: false },
    '/pricing': { prerender: true },
    '/blog/**': { prerender: true },
    '/changelog/**': { prerender: true },
    '/docs/**': { prerender: true },
    // Публичный календарь (по username)
    '/booking/**': { ssr: false },
    // Защищенные страницы приложения (требуют авторизации)
    '/schedule': { ssr: false },
    '/dashboard': { ssr: false },
    '/customers': { ssr: false },
    '/services': { ssr: false },
    '/settings/**': { ssr: false },
    '/profile': { ssr: false },
    '/payment': { ssr: false }
  },

  compatibilityDate: '2024-07-11',

  nitro: {
    prerender: {
      routes: [
        '/'
      ],
      crawlLinks: true
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
      include: ['date-fns', '@unovis/vue', '@unovis/ts', 'vue']
    },
    resolve: {
      dedupe: ['vue', '@vue/runtime-core']
    },
    server: {
      hmr: {
        timeout: 120000 // 2 минуты вместо 60 секунд
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
