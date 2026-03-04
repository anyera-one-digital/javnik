<script setup lang="ts">
import LandingHeroBlock from '~/components/LandingPage/LandingHeroBlock.vue'
import LandingCtaBlock from '~/components/LandingPage/LandingCtaBlock.vue'
import LandingAbout from '~/components/LandingPage/LandingAbout.vue'
import LandingAdvantages from '~/components/LandingPage/LandingAdvantages.vue'
import LandingSuccessStories from '~/components/LandingPage/LandingSuccessStories.vue'
import LandingPricingPlans from '~/components/LandingPage/LandingPricingPlans.vue'
import LandingFaqBlock from '~/components/LandingPage/LandingFaqBlock.vue'

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
  lazy: false
})

// Сохраняем данные в ref для стабильности
const pageData = ref(page.value)
watch(page, (newVal) => {
  if (newVal) {
    pageData.value = newVal
  }
}, { immediate: true })

const title = computed(() => pageData.value?.seo?.title || pageData.value?.title || '')
const description = computed(() => pageData.value?.seo?.description || pageData.value?.description || '')

useSeoMeta({
  titleTemplate: '',
  title,
  ogTitle: title,
  description,
  ogDescription: description
})
</script>

<template>
  <div v-if="pageData">
    <LandingHeroBlock
      v-if="pageData?.title"
      :title="pageData.title"
      :description="pageData.description"
    />

    <LandingAbout :sections="pageData.sections" />

    <LandingAdvantages :features="pageData.features" />

    <LandingSuccessStories :testimonials="pageData.testimonials" />

    <USeparator />

    <LandingPricingPlans :pricing="pageData.pricing" />

    <LandingFaqBlock :faq="pageData.faq" />

    <USeparator />

    <LandingCtaBlock
      v-if="pageData.cta"
      :cta="pageData.cta"
    />
  </div>
</template>
