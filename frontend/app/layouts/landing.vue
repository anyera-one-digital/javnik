<script setup lang="ts">
import '@fontsource-variable/manrope/index.css'
import '~/assets/css/yavnik-landing.css'
import { YAVNIK_THEME_INIT_SCRIPT, useYavnikTheme } from '~/composables/useYavnikTheme'

const { initTheme, theme } = useYavnikTheme()

onMounted(() => {
  document.documentElement.classList.add('yavnik-landing')
  initTheme()
})

onBeforeUnmount(() => {
  document.documentElement.classList.remove('yavnik-landing')
})

useSeoMeta({
  title: 'Явьник — онлайн-запись для частных специалистов',
  titleTemplate: '%s',
  description: 'Личная страница, онлайн-расписание, напоминания и клиентская база — в одном спокойном сервисе.',
  ogTitle: 'Явьник — запись клиентов без переписки',
  ogDescription: 'Создайте страницу, откройте расписание и принимайте записи онлайн.',
  ogType: 'website',
  twitterCard: 'summary_large_image'
})


useHead({
  htmlAttrs: {
    class: 'yavnik-landing'
  },
  meta: [
    {
      key: 'theme-color',
      name: 'theme-color',
      content: () => (theme.value === 'dark' ? '#0d0d10' : '#f7f7f4')
    },
    { name: 'viewport', content: 'width=device-width, initial-scale=1, viewport-fit=cover' }
  ],
  link: [
    { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
    { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
    { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' }
  ],
  script: [
    {
      key: 'yavnik-theme-init',
      innerHTML: YAVNIK_THEME_INIT_SCRIPT,
      tagPriority: -30
    }
  ]
})
</script>

<template>
  <slot />
</template>
