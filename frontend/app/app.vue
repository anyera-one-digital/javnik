<script setup lang="ts">
import { ru } from '@nuxt/ui/locale'

const colorMode = useColorMode()

const color = computed(() => colorMode.value === 'dark' ? '#1b1718' : 'white')

useHead({
  meta: [
    { charset: 'utf-8' },
    { name: 'viewport', content: 'width=device-width, initial-scale=1' },
    { key: 'theme-color', name: 'theme-color', content: color }
  ],
  link: [
    { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
    { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
    { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' }
  ],
  htmlAttrs: {
    lang: 'ru'
  }
})

useSeoMeta({
  titleTemplate: '%s — Явьник',
  twitterCard: 'summary_large_image'
})
</script>

<template>
  <UApp :locale="ru">
    <NuxtLoadingIndicator />

    <NuxtLayout>
      <NuxtPage :page-key="route => route.path" />
    </NuxtLayout>
  </UApp>
</template>
