<template>
  <UPageSection
    v-if="features"
    id="advantages"
    :title="features.title"
    :description="features.description"
  >
    <UPageGrid>
      <UPageCard
        v-for="(item, index) in features.items || []"
        :key="index"
        v-bind="item"
        spotlight
      />
    </UPageGrid>
  </UPageSection>
</template>

<script setup lang="ts">
defineProps<{
  features?: {
    headline?: string
    title?: string
    description?: string
    items?: Array<{ title: string; description: string; icon: string }>
  }
}>()
</script>
