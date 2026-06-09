<script setup lang="ts">
import LandingHeroBlock from '~/components/LandingPage/LandingHeroBlock.vue'
import LandingFaqBlock from '~/components/LandingPage/LandingFaqBlock.vue'

definePageMeta({
  ssr: true
})

// Сначала пробуем загрузить из админки (Django API), иначе — из Nuxt Content
const { data: page } = await useAsyncData('index', async () => {
  const fromApi = await $fetch<Record<string, unknown> | null>('/api/landing/index')
  if (fromApi && Object.keys(fromApi).length > 0) {
    return fromApi
  }
  return queryCollection('index').first()
}, {
  default: () => null,
  server: true,
  lazy: false,
  getCachedData(key, nuxtApp) {
    if (nuxtApp.isHydrating && nuxtApp.payload.data[key]) {
      return nuxtApp.payload.data[key]
    }
    return undefined
  }
})

const title = computed(() => page.value?.seo?.title || page.value?.title || '')
const description = computed(() => page.value?.seo?.description || page.value?.description || '')

useSeoMeta({
  titleTemplate: '',
  title,
  ogTitle: title,
  description,
  ogDescription: description
})
</script>

<template>
  <div v-if="page">
    <LandingHeroBlock
      v-if="page.title"
      :title="page.title"
      :description="page.description"
    />

    <USeparator />

    <LandingFaqBlock :faq="page.faq" />
  </div>
</template>
