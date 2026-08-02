<script setup lang="ts">
import type { NuxtError } from '#app'

defineProps<{
  error: NuxtError
}>()

useSeoMeta({
  title: 'Страница не найдена',
  description: 'К сожалению, эта страница не найдена.'
})

useHead({
  htmlAttrs: {
    lang: 'ru'
  },
  link: [
    { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }
  ]
})
</script>

<template>
  <UApp>
    <UError :error="error" />
  </UApp>
</template>
