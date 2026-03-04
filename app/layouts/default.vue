<script setup lang="ts">
import AppHeader from '~/components/LandingPage/AppHeader.vue'
import AppFooter from '~/components/LandingPage/AppFooter.vue'

const route = useRoute()
const isLanding = computed(() => route.path === '/')
</script>

<template>
  <div :class="{ 'landing-page': isLanding }">
    <AppHeader />

    <UMain>
      <slot />
    </UMain>

    <AppFooter />
  </div>
</template>
