<script setup lang="ts">
function getQuoteText(quote: unknown): string {
  if (typeof quote === 'string') return quote
  if (quote && typeof quote === 'object') {
    const obj = quote as Record<string, unknown>
    if (typeof obj.text === 'string') return obj.text
    if (typeof obj.content === 'string') return obj.content
  }
  return ''
}

defineProps<{
  testimonials?: {
    headline?: string
    title?: string
    description?: string
    items?: Array<{
      quote: string
      user?: { name: string; description: string; avatar?: string | { src: string } }
    }>
  }
}>()
</script>

<template>
  <UPageSection
    v-if="testimonials"
    id="testimonials"
    :title="testimonials.title"
    :description="testimonials.description"
  >
    <UPageGrid class="grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <UPageCard
        v-for="(testimonial, index) in (testimonials.items || []).filter(t => getQuoteText(t.quote)).slice(0, 6)"
        :key="index"
        variant="subtle"
        :description="getQuoteText(testimonial.quote)"
        :ui="{ description: 'before:content-[open-quote] after:content-[close-quote]' }"
      >
        <template #footer>
          <UUser
            v-if="testimonial.user"
            :name="testimonial.user.name"
            :description="testimonial.user.description"
            :avatar="testimonial.user.avatar ? (typeof testimonial.user.avatar === 'string' ? { src: testimonial.user.avatar } : testimonial.user.avatar) : undefined"
            size="lg"
          />
        </template>
      </UPageCard>
    </UPageGrid>
  </UPageSection>
</template>
