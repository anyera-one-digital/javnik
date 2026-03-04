<template>
  <UPageSection
    v-if="faq"
    id="faq"
    :title="faq.title"
    :description="faq.description"
  >
    <UAccordion
      :items="faq.items || []"
      :unmount-on-hide="false"
      :default-value="['0']"
      type="multiple"
      class="max-w-3xl mx-auto"
      :ui="{
        trigger: 'text-base text-highlighted',
        body: 'text-base text-muted'
      }"
    />
  </UPageSection>
</template>

<script setup lang="ts">
defineProps<{
  faq?: {
    title?: string
    description?: string
    items?: Array<{ label: string; content: string }>
  }
}>()
</script>
