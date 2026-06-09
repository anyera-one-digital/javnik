<script setup lang="ts">
const props = defineProps<{
  faq?: {
    title?: string
    description?: string
    items?: Array<{ label: string, content: string }>
  }
}>()

const accordionItems = computed(() =>
  (props.faq?.items || []).map((item, index) => ({
    label: item.label,
    content: item.content,
    value: String(index)
  }))
)
</script>

<template>
  <UPageSection
    v-if="faq"
    id="faq"
    :title="faq.title"
    :description="faq.description"
  >
    <template #body>
      <UAccordion
        v-if="accordionItems.length"
        :items="accordionItems"
        type="single"
        collapsible
        :unmount-on-hide="false"
        class="w-full max-w-3xl mx-auto"
        :ui="{
          root: 'flex flex-col w-full border-t border-default',
          item: 'flex flex-col w-full border-b border-default bg-transparent shadow-none',
          header: 'w-full',
          trigger: 'flex w-full items-center justify-between gap-4 py-4 text-left text-base text-highlighted',
          trailingIcon: 'shrink-0 size-5 text-muted',
          content: 'w-full',
          body: 'pb-4 text-base text-muted'
        }"
      />
    </template>
  </UPageSection>
</template>
