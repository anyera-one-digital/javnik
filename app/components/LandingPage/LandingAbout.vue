<script setup lang="ts">
import ImagePlaceholder from '~/components/LandingPage/ImagePlaceholder.vue'

defineProps<{
  sections?: Array<{
    id?: string
    title?: string
    description?: string
    orientation?: string
    reverse?: boolean
    image?: string
    features?: Array<{ name: string; description: string; icon: string }>
  }>
}>()
</script>

<template>
  <UPageSection
    v-for="(section, index) in sections"
    :key="index"
    :id="section.id"
    :title="section.title"
    :description="section.description"
    :orientation="section.orientation"
    :reverse="section.reverse"
    :features="section.features"
  >
    <img
      v-if="section.image"
      :src="section.image"
      :alt="section.title || ''"
      class="w-full rounded-lg object-cover aspect-video"
    >
    <ImagePlaceholder v-else />
  </UPageSection>
</template>
